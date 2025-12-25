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
    get_request_id
)
from api.exceptions import InternalServerException, ValidationException
from services.dialogue_generation_service import DialogueGenerationService
from llm_client import ILLMClient
from models.dialogue_structure.interaction import Interaction

logger = logging.getLogger(__name__)

router = APIRouter()


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
    request_id: Annotated[str, Depends(get_request_id)]
) -> list[InteractionResponse]:
    """Génère des interactions structurées.
    
    Args:
        request_data: Données de la requête de génération.
        request: La requête HTTP.
        dialogue_service: Service de génération injecté.
        request_id: ID de la requête.
        
    Returns:
        Liste des interactions générées.
        
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
        interactions, prompt_used, estimated_tokens = await dialogue_service.generate_interaction_variants(
            llm_client=llm_client,
            k_variants=request_data.k_variants,
            max_context_tokens_for_context_builder=request_data.max_context_tokens,
            user_instructions=request_data.user_instructions,
            system_prompt_override=request_data.system_prompt_override,
            context_selections=context_selections_dict,
            current_llm_model_identifier=request_data.llm_model_identifier
        )
        
        if interactions is None:
            raise InternalServerException(
                message="Échec de la génération d'interactions",
                request_id=request_id
            )
        
        # Convertir en format de réponse
        return [InteractionResponse.from_model(interaction) for interaction in interactions]
        
    except Exception as e:
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

