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
    EstimateTokensResponse,
    GenerateUnityDialogueRequest,
    GenerateUnityDialogueResponse
)
from api.schemas.interaction import InteractionResponse
from api.dependencies import (
    get_dialogue_generation_service,
    get_interaction_service,
    get_request_id,
    get_prompt_engine
)
from prompt_engine import PromptEngine
from api.exceptions import InternalServerException, ValidationException, NotFoundException, OpenAIException
from services.dialogue_generation_service import DialogueGenerationService
from services.interaction_service import InteractionService
from services.unity_dialogue_generation_service import UnityDialogueGenerationService
from services.skill_catalog_service import SkillCatalogService
from services.json_renderer.unity_json_renderer import UnityJsonRenderer
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
        logger.info(f"Tentative de création du client LLM pour model_id: {request_data.llm_model_identifier}")
        logger.debug(f"Available models: {available_models}")
        llm_client = LLMClientFactory.create_client(
            model_id=request_data.llm_model_identifier,
            config=llm_config,
            available_models=available_models
        )
        from llm_client import DummyLLMClient, OpenAIClient
        is_dummy_client = isinstance(llm_client, DummyLLMClient)
        is_openai_client = isinstance(llm_client, OpenAIClient)
        if is_dummy_client:
            logger.warning(f"ATTENTION: DummyLLMClient utilisé au lieu d'OpenAI pour model_id: {request_data.llm_model_identifier}")
        if is_openai_client:
            logger.info(f"OpenAIClient créé avec succès - model_name: {getattr(llm_client, 'model_name', 'N/A')}, has_client: {hasattr(llm_client, 'client')}")
        
        logger.info(f"Client LLM créé: {type(llm_client).__name__}, is_dummy: {is_dummy_client}, is_openai: {is_openai_client}")
        
        # Convertir ContextSelection en dict pour le service (avec préfixes underscore)
        context_selections_dict = request_data.context_selections.to_service_dict()
        logger.info(f"Context selections reçus - characters: {context_selections_dict.get('characters', [])}, locations: {context_selections_dict.get('locations', [])}, items: {context_selections_dict.get('items', [])}")
        logger.debug(f"Context selections complet: {context_selections_dict}")
        
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
        
        # Ajouter un avertissement si DummyLLMClient a été utilisé
        warning_message = None
        if is_dummy_client:
            warning_message = (
                f"⚠️ Mode test activé (DummyLLMClient). "
                f"Vérifiez que la clé API OpenAI ({llm_config.get('api_key_env_var', 'OPENAI_API_KEY')}) est configurée dans les variables d'environnement."
            )
            logger.warning(warning_message)
        
        return GenerateDialogueVariantsResponse(
            variants=variant_responses,
            prompt_used=prompt_used,
            estimated_tokens=estimated_tokens or 0,
            warning=warning_message
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
        logger.info(f"Tentative de création du client LLM pour model_id: {request_data.llm_model_identifier}")
        logger.debug(f"Available models: {available_models}")
        llm_client = LLMClientFactory.create_client(
            model_id=request_data.llm_model_identifier,
            config=llm_config,
            available_models=available_models
        )
        from llm_client import DummyLLMClient, OpenAIClient
        is_dummy_client = isinstance(llm_client, DummyLLMClient)
        is_openai_client = isinstance(llm_client, OpenAIClient)
        if is_dummy_client:
            logger.warning(f"ATTENTION: DummyLLMClient utilisé au lieu d'OpenAI pour model_id: {request_data.llm_model_identifier}")
        if is_openai_client:
            logger.info(f"OpenAIClient créé avec succès - model_name: {getattr(llm_client, 'model_name', 'N/A')}, has_client: {hasattr(llm_client, 'client')}")
        
        logger.info(f"Client LLM créé: {type(llm_client).__name__}, is_dummy: {is_dummy_client}, is_openai: {is_openai_client}")
        
        # Convertir ContextSelection en dict pour le service (avec préfixes underscore)
        context_selections_dict = request_data.context_selections.to_service_dict()
        logger.info(f"Context selections reçus - characters: {context_selections_dict.get('characters', [])}, locations: {context_selections_dict.get('locations', [])}, items: {context_selections_dict.get('items', [])}")
        logger.debug(f"Context selections complet: {context_selections_dict}")
        
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
        
        # S'assurer que context_text n'est jamais None
        if context_text is None:
            context_text = ""
        
        context_tokens = context_builder._count_tokens(context_text)
        
        # Estimer le prompt complet
        prompt_engine = dialogue_service.prompt_engine
        original_system_prompt = None
        
        # Appliquer le system_prompt_override s'il est fourni
        if request_data.system_prompt_override is not None and prompt_engine.system_prompt_template != request_data.system_prompt_override:
            original_system_prompt = prompt_engine.system_prompt_template
            prompt_engine.system_prompt_template = request_data.system_prompt_override
            logger.info(f"System prompt temporarily set for estimation: '{request_data.system_prompt_override[:100]}...'")
        
        try:
            # Extraire les informations de scène pour PromptEngine depuis context_selections
            scene_protagonists_dict = context_selections_dict.pop("_scene_protagonists", {})
            scene_location_dict = context_selections_dict.pop("_scene_location", {})
            
            # Extraire generation_settings si présent
            generation_settings = context_selections_dict.pop("generation_settings", {})
            dialogue_structure = generation_settings.get("dialogue_structure", []) if generation_settings else []
            
            generation_params_for_prompt_build = {}
            if dialogue_structure:
                # Convertir la structure en description narrative pour le prompt
                generation_params_for_prompt_build["dialogue_structure_narrative"] = "Structure: " + " → ".join(dialogue_structure)
            
            full_prompt, total_tokens = prompt_engine.build_prompt(
                context_summary=context_text,
                user_specific_goal=request_data.user_instructions,
                scene_protagonists=scene_protagonists_dict if scene_protagonists_dict else None,
                scene_location=scene_location_dict if scene_location_dict else None,
                generation_params=generation_params_for_prompt_build if generation_params_for_prompt_build else None
            )
        finally:
            # Restaurer le system prompt original si on l'a modifié
            if original_system_prompt is not None:
                prompt_engine.system_prompt_template = original_system_prompt
        
        return EstimateTokensResponse(
            context_tokens=context_tokens,
            total_estimated_tokens=total_tokens,
            estimated_prompt=full_prompt
        )
        
    except Exception as e:
        logger.exception(f"Erreur lors de l'estimation de tokens (request_id: {request_id})")
        raise InternalServerException(
            message="Erreur lors de l'estimation de tokens",
            details={"error": str(e)},
            request_id=request_id
        )


@router.post(
    "/generate/unity-dialogue",
    response_model=GenerateUnityDialogueResponse,
    status_code=status.HTTP_200_OK
)
async def generate_unity_dialogue(
    request_data: GenerateUnityDialogueRequest,
    request: Request,
    dialogue_service: Annotated[DialogueGenerationService, Depends(get_dialogue_generation_service)],
    prompt_engine: Annotated[PromptEngine, Depends(get_prompt_engine)],
    request_id: Annotated[str, Depends(get_request_id)]
) -> GenerateUnityDialogueResponse:
    """Génère un nœud de dialogue au format Unity JSON.
    
    Args:
        request_data: Données de la requête de génération.
        request: La requête HTTP.
        dialogue_service: Service de génération injecté (pour ContextBuilder).
        prompt_engine: PromptEngine injecté.
        request_id: ID de la requête.
        
    Returns:
        Réponse contenant le JSON Unity généré.
        
    Raises:
        ValidationException: Si aucun personnage n'est sélectionné.
        InternalServerException: Si la génération échoue.
    """
    try:
        # 1. Valider qu'au moins un personnage est sélectionné
        if not request_data.context_selections.characters or len(request_data.context_selections.characters) == 0:
            raise ValidationException(
                message="Au moins un personnage doit être sélectionné pour générer un dialogue",
                details={"field": "context_selections.characters"},
                request_id=request_id
            )
        
        # 2. Extraire le PNJ interlocuteur
        npc_speaker_id = request_data.npc_speaker_id
        if not npc_speaker_id:
            # Utiliser le premier personnage sélectionné
            npc_speaker_id = request_data.context_selections.characters[0]
            logger.info(f"PNJ interlocuteur non spécifié, utilisation du premier personnage: {npc_speaker_id}")
        else:
            # Vérifier que le PNJ sélectionné est dans la liste des personnages
            if npc_speaker_id not in request_data.context_selections.characters:
                logger.warning(
                    f"PNJ interlocuteur '{npc_speaker_id}' n'est pas dans la liste des personnages sélectionnés. "
                    f"Utilisation quand même."
                )
        
        # 3. Charger le catalogue des compétences
        skill_service = SkillCatalogService()
        try:
            skills_list = skill_service.load_skills()
            logger.info(f"Chargement réussi: {len(skills_list)} compétences disponibles")
        except Exception as e:
            logger.warning(f"Impossible de charger le catalogue des compétences: {e}. Continuation sans liste de compétences.")
            skills_list = []
        
        # 4. Construire le contexte GDD
        context_builder = dialogue_service.context_builder
        context_selections_dict = request_data.context_selections.to_service_dict()
        
        context_summary, context_tokens = context_builder.build_context(
            max_tokens=request_data.max_context_tokens,
            **context_selections_dict
        )
        
        # Extraire le lieu de la scène
        scene_location = None
        if request_data.context_selections.scene_location:
            scene_location = request_data.context_selections.scene_location
        
        # 5. Construire le prompt Unity
        prompt, prompt_tokens = prompt_engine.build_unity_dialogue_prompt(
            user_instructions=request_data.user_instructions,
            npc_speaker_id=npc_speaker_id,
            player_character_id="URESAIR",  # Seigneuresse Uresaïr par défaut
            skills_list=skills_list,
            context_summary=context_summary,
            scene_location=scene_location
        )
        
        estimated_tokens = context_tokens + prompt_tokens
        
        # 6. Créer le client LLM
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
        
        from llm_client import DummyLLMClient, OpenAIClient
        is_dummy_client = isinstance(llm_client, DummyLLMClient)
        warning = None
        if is_dummy_client:
            warning = "ATTENTION: DummyLLMClient utilisé au lieu d'OpenAI"
            logger.warning(warning)
        
        # 7. Générer le nœud via Structured Output
        unity_service = UnityDialogueGenerationService()
        generation_response = await unity_service.generate_dialogue_node(
            llm_client=llm_client,
            prompt=prompt,
            system_prompt_override=request_data.system_prompt_override
        )
        
        # 8. Enrichir avec IDs
        enriched_nodes = unity_service.enrich_with_ids(
            content=generation_response,
            start_id="START"
        )
        
        # 9. Normaliser et rendre en JSON
        renderer = UnityJsonRenderer()
        json_content = renderer.render_unity_nodes(
            nodes=enriched_nodes,
            normalize=True
        )
        
        logger.info(f"Génération Unity JSON réussie: {len(enriched_nodes)} nœud(s)")
        
        return GenerateUnityDialogueResponse(
            json_content=json_content,
            prompt_used=prompt,
            estimated_tokens=estimated_tokens,
            warning=warning
        )
        
    except ValidationException:
        raise
    except Exception as e:
        logger.exception(f"Erreur lors de la génération Unity JSON (request_id: {request_id})")
        raise InternalServerException(
            message="Erreur lors de la génération du dialogue Unity JSON",
            details={"error": str(e)},
            request_id=request_id
        )

