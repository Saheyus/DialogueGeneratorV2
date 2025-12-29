"""Router pour la génération de dialogues."""
import logging
import re
import json
from pathlib import Path
from typing import Annotated
from fastapi import APIRouter, Depends, Request, status
from api.schemas.dialogue import (
    GenerateDialogueVariantsRequest,
    GenerateDialogueVariantsResponse,
    DialogueVariantResponse,
    EstimateTokensRequest,
    EstimateTokensResponse,
    GenerateUnityDialogueRequest,
    GenerateUnityDialogueResponse,
    ExportUnityDialogueRequest,
    ExportUnityDialogueResponse
)
from api.dependencies import (
    get_dialogue_generation_service,
    get_request_id,
    get_prompt_engine,
    get_config_service
)
from prompt_engine import PromptEngine
from api.exceptions import InternalServerException, ValidationException, NotFoundException, OpenAIException
from services.dialogue_generation_service import DialogueGenerationService
from services.unity_dialogue_generation_service import UnityDialogueGenerationService
from services.skill_catalog_service import SkillCatalogService
from services.trait_catalog_service import TraitCatalogService
from services.json_renderer.unity_json_renderer import UnityJsonRenderer
from services.configuration_service import ConfigurationService
from llm_client import ILLMClient

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


# NOTE: L'endpoint /generate/interactions a été supprimé. Utiliser /generate/unity-dialogue à la place.


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
        # Extraire _element_modes si présent
        element_modes = context_selections_dict.pop("_element_modes", None)
        
        # Utiliser build_context_with_custom_fields si field_configs est fourni
        if request_data.field_configs and hasattr(context_builder, 'build_context_with_custom_fields'):
            context_text = context_builder.build_context_with_custom_fields(
                selected_elements=context_selections_dict,
                scene_instruction=request_data.user_instructions,
                field_configs=request_data.field_configs,
                organization_mode=request_data.organization_mode or "default",
                max_tokens=request_data.max_context_tokens,
                element_modes=element_modes
            )
        else:
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
        
        # 4. Charger le catalogue des traits
        trait_service = TraitCatalogService()
        try:
            traits_data = trait_service.load_traits()
            traits_list = trait_service.get_trait_labels()
            logger.info(f"Chargement réussi: {len(traits_list)} traits disponibles")
        except Exception as e:
            logger.warning(f"Impossible de charger le catalogue des traits: {e}. Continuation sans liste de traits.")
            traits_list = []
        
        # 5. Construire le contexte GDD
        context_builder = dialogue_service.context_builder
        context_selections_dict = request_data.context_selections.to_service_dict()
        
        # Extraire _element_modes si présent
        element_modes = context_selections_dict.pop("_element_modes", None)
        
        # Si un preview de dialogue précédent est fourni, le définir dans le context builder
        if request_data.previous_dialogue_preview:
            context_builder.set_previous_dialogue_context(request_data.previous_dialogue_preview)
        
        # Pour l'instant, utiliser build_context standard (sans field_configs)
        # TODO: Ajouter support pour field_configs dans generate_unity_dialogue si nécessaire
        context_summary = context_builder.build_context(
            selected_elements=context_selections_dict,
            scene_instruction=request_data.user_instructions,
            max_tokens=request_data.max_context_tokens
        )
        context_tokens = context_builder._count_tokens(context_summary)
        
        # Extraire le lieu de la scène
        scene_location = None
        if request_data.context_selections.scene_location:
            scene_location = request_data.context_selections.scene_location
        
        # 6. Construire le prompt Unity
        prompt, prompt_tokens = prompt_engine.build_unity_dialogue_prompt(
            user_instructions=request_data.user_instructions,
            npc_speaker_id=npc_speaker_id,
            player_character_id="URESAIR",  # Seigneuresse Uresaïr par défaut
            skills_list=skills_list,
            traits_list=traits_list,
            context_summary=context_summary,
            scene_location=scene_location,
            max_choices=request_data.max_choices,
            narrative_tags=request_data.narrative_tags,
            author_profile=request_data.author_profile,
            vocabulary_min_importance=request_data.vocabulary_min_importance,
            include_narrative_guides=request_data.include_narrative_guides
        )
        
        estimated_tokens = context_tokens + prompt_tokens
        
        # 7. Créer le client LLM
        from api.dependencies import get_config_service, create_llm_usage_service
        config_service = get_config_service()
        usage_service = create_llm_usage_service()
        from factories.llm_factory import LLMClientFactory
        llm_config = config_service.get_llm_config()
        available_models = config_service.get_available_llm_models()
        
        llm_client = LLMClientFactory.create_client(
            model_id=request_data.llm_model_identifier,
            config=llm_config,
            available_models=available_models,
            usage_service=usage_service,
            request_id=request_id,
            endpoint="generate/unity-dialogue"
        )
        
        from llm_client import DummyLLMClient, OpenAIClient
        is_dummy_client = isinstance(llm_client, DummyLLMClient)
        warning = None
        if is_dummy_client:
            warning = "ATTENTION: DummyLLMClient utilisé au lieu d'OpenAI"
            logger.warning(warning)
        
        # 8. Générer le nœud via Structured Output
        unity_service = UnityDialogueGenerationService()
        generation_response = await unity_service.generate_dialogue_node(
            llm_client=llm_client,
            prompt=prompt,
            system_prompt_override=request_data.system_prompt_override,
            max_choices=request_data.max_choices
        )
        
        # 9. Enrichir avec IDs
        enriched_nodes = unity_service.enrich_with_ids(
            content=generation_response,
            start_id="START"
        )
        
        # 10. Normaliser et rendre en JSON
        renderer = UnityJsonRenderer()
        json_content = renderer.render_unity_nodes(
            nodes=enriched_nodes,
            normalize=True
        )
        
        # 10.1 Validation optionnelle contre le schéma Unity (si activée)
        from api.config.validation_config import get_validation_config
        from api.config.security_config import get_security_config
        from api.utils.unity_schema_validator import validate_unity_json
        import json
        
        validation_config = get_validation_config()
        security_config = get_security_config()
        
        if validation_config.should_validate_unity_schema(security_config):
            try:
                json_data = json.loads(json_content)
                is_valid, schema_errors = validate_unity_json(json_data)
                
                if not is_valid:
                    error_msg = f"Validation Unity Schema échouée ({len(schema_errors)} erreur(s)): " + "; ".join(schema_errors[:3])
                    if security_config.is_development:
                        logger.warning(error_msg)
                    else:
                        logger.error(error_msg)
                    # Note: On ne bloque pas l'export, juste un warning/error dans les logs
            except Exception as e:
                logger.warning(f"Erreur lors de la validation Unity Schema (non bloquante): {e}")
        
        # 11. Extraire le titre depuis la réponse de génération
        dialogue_title = generation_response.title if hasattr(generation_response, 'title') and generation_response.title else None
        
        logger.info(f"Génération Unity JSON réussie: {len(enriched_nodes)} nœud(s), titre: {dialogue_title}")
        
        return GenerateUnityDialogueResponse(
            json_content=json_content,
            title=dialogue_title,
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


@router.post(
    "/unity/export",
    response_model=ExportUnityDialogueResponse,
    status_code=status.HTTP_200_OK
)
async def export_unity_dialogue(
    request_data: ExportUnityDialogueRequest,
    request: Request,
    config_service: Annotated[ConfigurationService, Depends(get_config_service)],
    request_id: Annotated[str, Depends(get_request_id)]
) -> ExportUnityDialogueResponse:
    """Exporte un dialogue Unity JSON vers un fichier.
    
    Args:
        request_data: Données de la requête d'export (JSON, titre, nom de fichier).
        request: La requête HTTP.
        config_service: Service de configuration injecté.
        request_id: ID de la requête.
        
    Returns:
        Réponse contenant le chemin du fichier créé.
        
    Raises:
        ValidationException: Si le chemin Unity n'est pas configuré ou si le JSON est invalide.
        InternalServerException: Si l'écriture du fichier échoue.
    """
    try:
        # 1. Récupérer le chemin Unity configuré
        unity_path = config_service.get_unity_dialogues_path()
        if not unity_path:
            raise ValidationException(
                message="Le chemin Unity dialogues n'est pas configuré. Configurez-le dans les paramètres.",
                details={"field": "unity_dialogues_path"},
                request_id=request_id
            )
        
        unity_dir = Path(unity_path)
        
        # Créer le dossier s'il n'existe pas
        unity_dir.mkdir(parents=True, exist_ok=True)
        
        # 2. Valider que le JSON est valide
        try:
            json_data = json.loads(request_data.json_content)
            if not isinstance(json_data, list):
                raise ValidationException(
                    message="Le JSON Unity doit être un tableau de nœuds",
                    details={"json_content": "Doit être un tableau []"},
                    request_id=request_id
                )
        except json.JSONDecodeError as e:
            raise ValidationException(
                message="Le JSON fourni n'est pas valide",
                details={"json_content": f"Erreur JSON: {str(e)}"},
                request_id=request_id
            )
        
        # 3. Générer le nom de fichier
        if request_data.filename:
            # Utiliser le nom fourni (sans extension)
            filename = request_data.filename
        else:
            # Générer un slug à partir du titre
            # Convertir en minuscules, remplacer espaces et caractères spéciaux par underscores
            slug = re.sub(r'[^\w\s-]', '', request_data.title.lower())
            slug = re.sub(r'[-\s]+', '_', slug)
            filename = slug[:100]  # Limiter la longueur
        
        # Ajouter l'extension .json si pas présente
        if not filename.endswith('.json'):
            filename += '.json'
        
        file_path = unity_dir / filename
        
        # 4. Écrire le fichier JSON (pretty-print avec 2 espaces)
        json_content_formatted = json.dumps(json_data, indent=2, ensure_ascii=False)
        file_path.write_text(json_content_formatted, encoding='utf-8')
        
        logger.info(f"Dialogue Unity exporté: {file_path} (request_id: {request_id})")
        
        return ExportUnityDialogueResponse(
            file_path=str(file_path.absolute()),
            filename=filename,
            success=True
        )
        
    except ValidationException:
        raise
    except Exception as e:
        logger.exception(f"Erreur lors de l'export Unity JSON (request_id: {request_id})")
        raise InternalServerException(
            message="Erreur lors de l'export du dialogue Unity JSON",
            details={"error": str(e)},
            request_id=request_id
        )

