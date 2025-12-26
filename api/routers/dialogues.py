"""Router pour la génération de dialogues."""
import logging
from typing import Annotated
from fastapi import APIRouter, Depends, Request, status
from api.schemas.dialogue import (
    GenerateDialogueVariantsRequest,
    GenerateInteractionVariantsRequest,
    GenerateDialogueVariantsResponse,
    DialogueVariantResponse,
    EstimateTokensRequest,
    EstimateTokensResponse
)
from api.schemas.interaction import InteractionResponse
from api.dependencies import (
    get_dialogue_generation_service,
    get_interaction_service,
    get_request_id
)
from api.exceptions import InternalServerException, ValidationException, NotFoundException, OpenAIException
from services.dialogue_generation_service import DialogueGenerationService
from services.interaction_service import InteractionService
from llm_client import ILLMClient
from models.dialogue_structure.interaction import Interaction
from models.dialogue_structure.dialogue_elements import PlayerChoicesBlockElement

logger = logging.getLogger(__name__)

router = APIRouter()


def _transform_openai_error(error: Exception, request_id: str) -> OpenAIException:
    """Transforme une erreur OpenAI en exception API standardisée.
    
    Args:
        error: L'exception OpenAI.
        request_id: ID de la requête.
        
    Returns:
        OpenAIException avec code et message appropriés.
    """
    error_str = str(error).lower()
    error_type = type(error).__name__
    
    # Détecter le type d'erreur OpenAI
    if "rate limit" in error_str or "429" in error_str:
        return OpenAIException(
            code="OPENAI_RATE_LIMIT",
            message="Limite de taux OpenAI atteinte. Veuillez réessayer plus tard.",
            details={"error_type": error_type, "error_message": str(error)},
            request_id=request_id
        )
    elif "timeout" in error_str or "timed out" in error_str:
        return OpenAIException(
            code="OPENAI_TIMEOUT",
            message="Délai d'attente OpenAI dépassé. Veuillez réessayer.",
            details={"error_type": error_type, "error_message": str(error)},
            request_id=request_id
        )
    elif "invalid" in error_str or "400" in error_str:
        return OpenAIException(
            code="OPENAI_INVALID_REQUEST",
            message="Requête invalide vers OpenAI. Vérifiez les paramètres.",
            details={"error_type": error_type, "error_message": str(error)},
            request_id=request_id
        )
    else:
        # Erreur générique OpenAI
        return OpenAIException(
            code="OPENAI_ERROR",
            message="Erreur lors de l'appel à OpenAI",
            details={"error_type": error_type, "error_message": str(error)},
            request_id=request_id
        )


@router.post(
    "/generate/variants",
    response_model=GenerateDialogueVariantsResponse,
    status_code=status.HTTP_200_OK
)
async def generate_dialogue_variants(
    request_data: GenerateDialogueVariantsRequest,
    request: Request,
    dialogue_service: Annotated[DialogueGenerationService, Depends(get_dialogue_generation_service)],
    request_id: Annotated[str, Depends(get_request_id)]
) -> GenerateDialogueVariantsResponse:
    """Génère des variantes de dialogue texte.
    
    Args:
        request_data: Données de la requête de génération.
        request: La requête HTTP.
        dialogue_service: Service de génération injecté.
        request_id: ID de la requête.
        
    Returns:
        Réponse contenant les variantes générées.
        
    Raises:
        InternalServerException: Si la génération échoue.
    """
    try:
        # Créer le client LLM via la factory
        from api.dependencies import get_config_service
        config_service = get_config_service()
        from factories.llm_factory import LLMClientFactory
        llm_config = config_service.get_llm_config()
        available_models = config_service.get_available_llm_models()
        llm_client = LLMClientFactory.create_client(
            model_id=request_data.llm_model_identifier,
            config=llm_config,
            available_models=available_models
        )
        
        # Convertir ContextSelection en dict pour le service (avec préfixes underscore)
        context_selections_dict = request_data.context_selections.to_service_dict()
        
        # Appeler le service de génération
        variants, prompt_used, estimated_tokens = await dialogue_service.generate_dialogue_variants(
            llm_client=llm_client,
            k_variants=request_data.k_variants,
            max_context_tokens_for_context_builder=request_data.max_context_tokens,
            structured_output=request_data.structured_output,
            user_instructions=request_data.user_instructions,
            system_prompt_override=request_data.system_prompt_override,
            context_selections=context_selections_dict,
            current_llm_model_identifier=request_data.llm_model_identifier
        )
        
        if variants is None:
            raise InternalServerException(
                message="Échec de la génération de variantes",
                request_id=request_id
            )
        
        # Convertir en format de réponse
        variant_responses = [
            DialogueVariantResponse(
                id=variant.get("id", f"variant-{i}"),
                title=variant.get("title", f"Variante {i+1}"),
                content=variant.get("content", ""),
                is_new=variant.get("is_new", True)
            )
            for i, variant in enumerate(variants)
        ]
        
        return GenerateDialogueVariantsResponse(
            variants=variant_responses,
            prompt_used=prompt_used,
            estimated_tokens=estimated_tokens or 0
        )
        
    except Exception as e:
        # Vérifier si c'est une erreur OpenAI
        from openai import APIError
        if isinstance(e, APIError):
            logger.error(f"Erreur OpenAI lors de la génération de variantes (request_id: {request_id}): {e}")
            raise _transform_openai_error(e, request_id)
        
        logger.exception(f"Erreur lors de la génération de variantes (request_id: {request_id})")
        raise InternalServerException(
            message="Erreur lors de la génération de variantes",
            details={"error": str(e)},
            request_id=request_id
        )


@router.post(
    "/generate/interactions",
    response_model=list[InteractionResponse],
    status_code=status.HTTP_200_OK
)
async def generate_interaction_variants(
    request_data: GenerateInteractionVariantsRequest,
    request: Request,
    dialogue_service: Annotated[DialogueGenerationService, Depends(get_dialogue_generation_service)],
    interaction_service: Annotated[InteractionService, Depends(get_interaction_service)],
    request_id: Annotated[str, Depends(get_request_id)]
) -> list[InteractionResponse]:
    """Génère des interactions structurées.
    
    Args:
        request_data: Données de la requête de génération.
        request: La requête HTTP.
        dialogue_service: Service de génération injecté.
        interaction_service: Service d'interactions injecté.
        request_id: ID de la requête.
        
    Returns:
        Liste des interactions générées.
        
    Raises:
        InternalServerException: Si la génération échoue.
        NotFoundException: Si previous_interaction_id est fourni mais l'interaction n'existe pas.
    """
    try:
        # Gérer la continuité narrative si previous_interaction_id est fourni
        if request_data.previous_interaction_id:
            if not interaction_service.exists(request_data.previous_interaction_id):
                raise NotFoundException(
                    resource_type="Interaction",
                    resource_id=request_data.previous_interaction_id,
                    request_id=request_id
                )
            
            # Récupérer le chemin complet (tous les parents jusqu'à la racine)
            path_interactions = interaction_service.get_dialogue_path(request_data.previous_interaction_id)
            
            # Définir le contexte de dialogue précédent dans le ContextBuilder
            context_builder = dialogue_service.context_builder
            context_builder.set_previous_dialogue_context(path_interactions)
        
        # Créer le client LLM via la factory
        from api.dependencies import get_config_service
        config_service = get_config_service()
        from factories.llm_factory import LLMClientFactory
        llm_config = config_service.get_llm_config()
        available_models = config_service.get_available_llm_models()
        llm_client = LLMClientFactory.create_client(
            model_id=request_data.llm_model_identifier,
            config=llm_config,
            available_models=available_models
        )
        
        # Convertir ContextSelection en dict pour le service (avec préfixes underscore)
        context_selections_dict = request_data.context_selections.to_service_dict()
        
        # Appeler le service de génération
        interactions, prompt_used, estimated_tokens = await dialogue_service.generate_interaction_variants(
            llm_client=llm_client,
            k_variants=request_data.k_variants,
            max_context_tokens_for_context_builder=request_data.max_context_tokens,
            user_instructions=request_data.user_instructions,
            system_prompt_override=request_data.system_prompt_override,
            context_selections=context_selections_dict,
            current_llm_model_identifier=request_data.llm_model_identifier
        )
        
        if interactions is None or len(interactions) == 0:
            raise InternalServerException(
                message="Échec de la génération d'interactions",
                request_id=request_id
            )
        
        # Valider les références dans les interactions générées
        # Collecter tous les IDs des interactions générées
        generated_ids = {interaction.interaction_id for interaction in interactions}
        valid_ids = set(generated_ids)
        
        # Ajouter les IDs existants dans le système (pour références vers interactions existantes)
        all_existing = interaction_service.get_all()
        for existing_interaction in all_existing:
            valid_ids.add(existing_interaction.interaction_id)
        
        # Valider chaque interaction générée
        validated_interactions = []
        validation_errors = []
        
        for interaction in interactions:
            try:
                # Collecter tous les IDs référencés dans cette interaction
                referenced_ids = []
                if interaction.next_interaction_id_if_no_choices:
                    referenced_ids.append(interaction.next_interaction_id_if_no_choices)
                
                for element in interaction.elements:
                    if isinstance(element, PlayerChoicesBlockElement):
                        for choice in element.choices:
                            if choice.next_interaction_id:
                                referenced_ids.append(choice.next_interaction_id)
                
                # Vérifier que tous les IDs référencés existent (dans les interactions générées OU existantes)
                invalid_refs = [ref_id for ref_id in referenced_ids if ref_id not in valid_ids]
                
                if invalid_refs:
                    logger.warning(
                        f"Interaction générée '{interaction.interaction_id}' a des références cassées: {invalid_refs} "
                        f"(request_id: {request_id})"
                    )
                    # Option: supprimer les références cassées plutôt que de rejeter l'interaction
                    # Pour l'instant, on log juste un warning et on garde l'interaction
                    validation_errors.append({
                        "interaction_id": interaction.interaction_id,
                        "invalid_references": invalid_refs
                    })
                
                validated_interactions.append(interaction)
                
            except Exception as e:
                logger.error(
                    f"Erreur lors de la validation de l'interaction générée '{interaction.interaction_id}': {e} "
                    f"(request_id: {request_id})"
                )
                validation_errors.append({
                    "interaction_id": interaction.interaction_id,
                    "error": str(e)
                })
                # On continue avec les autres interactions même si une échoue
        
        # Si toutes les interactions ont échoué, lever une exception
        if len(validated_interactions) == 0:
            raise InternalServerException(
                message="Aucune interaction valide générée",
                details={"errors": validation_errors},
                request_id=request_id
            )
        
        # Si certaines interactions ont échoué, logger un warning mais retourner les valides
        if validation_errors:
            logger.warning(
                f"Génération partielle: {len(validated_interactions)}/{len(interactions)} interactions valides, "
                f"{len(validation_errors)} erreurs (request_id: {request_id})"
            )
        
        # Convertir en format de réponse
        return [InteractionResponse.from_model(interaction) for interaction in validated_interactions]
        
    except NotFoundException:
        # Re-propager NotFoundException (déjà gérée)
        raise
    except Exception as e:
        # Vérifier si c'est une erreur OpenAI
        from openai import APIError
        if isinstance(e, APIError):
            logger.error(f"Erreur OpenAI lors de la génération d'interactions (request_id: {request_id}): {e}")
            raise _transform_openai_error(e, request_id)
        
        logger.exception(f"Erreur lors de la génération d'interactions (request_id: {request_id})")
        raise InternalServerException(
            message="Erreur lors de la génération d'interactions",
            details={"error": str(e)},
            request_id=request_id
        )


@router.post(
    "/estimate-tokens",
    response_model=EstimateTokensResponse,
    status_code=status.HTTP_200_OK
)
async def estimate_tokens(
    request_data: EstimateTokensRequest,
    request: Request,
    dialogue_service: Annotated[DialogueGenerationService, Depends(get_dialogue_generation_service)],
    request_id: Annotated[str, Depends(get_request_id)]
) -> EstimateTokensResponse:
    """Estime le nombre de tokens pour un contexte donné.
    
    Args:
        request_data: Données de la requête d'estimation.
        request: La requête HTTP.
        dialogue_service: Service de génération injecté.
        request_id: ID de la requête.
        
    Returns:
        Estimation du nombre de tokens.
    """
    try:
        # Convertir ContextSelection en dict pour le service (avec préfixes underscore)
        context_selections_dict = request_data.context_selections.to_service_dict()
        
        # Construire le contexte via le service
        context_builder = dialogue_service.context_builder
        context_text = context_builder.build_context(
            selected_elements=context_selections_dict,
            scene_instruction=request_data.user_instructions,
            max_tokens=request_data.max_context_tokens
        )
        
        context_tokens = context_builder._count_tokens(context_text)
        
        # Estimer le prompt complet
        prompt_engine = dialogue_service.prompt_engine
        full_prompt, total_tokens = prompt_engine.build_prompt(
            context_summary=context_text,
            user_specific_goal=request_data.user_instructions
        )
        
        return EstimateTokensResponse(
            context_tokens=context_tokens,
            total_estimated_tokens=total_tokens
        )
        
    except Exception as e:
        logger.exception(f"Erreur lors de l'estimation de tokens (request_id: {request_id})")
        raise InternalServerException(
            message="Erreur lors de l'estimation de tokens",
            details={"error": str(e)},
            request_id=request_id
        )

