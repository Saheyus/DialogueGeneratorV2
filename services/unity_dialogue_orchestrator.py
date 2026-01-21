"""Orchestrateur pour génération Unity Dialogue (REST + SSE streaming).

Ce service encapsule toute la logique de génération Unity Dialogue,
permettant de l'utiliser à la fois pour l'endpoint REST et le streaming SSE.
"""
import logging
import asyncio
from typing import AsyncGenerator, Callable, Dict, Any, Optional
from dataclasses import dataclass

from services.dialogue_generation_service import DialogueGenerationService
from core.prompt.prompt_engine import PromptEngine, PromptInput, BuiltPrompt
from services.skill_catalog_service import SkillCatalogService
from services.trait_catalog_service import TraitCatalogService
from services.configuration_service import ConfigurationService
from services.llm_usage_service import LLMUsageService
from services.unity_dialogue_generation_service import UnityDialogueGenerationService
from services.json_renderer.unity_json_renderer import UnityJsonRenderer
from api.schemas.dialogue import GenerateUnityDialogueRequest, GenerateUnityDialogueResponse
from api.exceptions import InternalServerException, ValidationException
from factories.llm_factory import LLMClientFactory

logger = logging.getLogger(__name__)


@dataclass
class GenerationEvent:
    """Événement de génération pour SSE streaming."""
    type: str  # 'step', 'metadata', 'complete', 'error'
    data: Dict[str, Any]


class UnityDialogueOrchestrator:
    """Orchestrateur pour génération Unity Dialogue (REST + SSE).
    
    Encapsule toute la logique de génération Unity Dialogue, permettant
    de l'utiliser à la fois pour l'endpoint REST et le streaming SSE.
    """
    
    def __init__(
        self,
        dialogue_service: DialogueGenerationService,
        prompt_engine: PromptEngine,
        skill_service: SkillCatalogService,
        trait_service: TraitCatalogService,
        config_service: ConfigurationService,
        usage_service: LLMUsageService,
        request_id: str
    ):
        """Initialise l'orchestrateur avec toutes les dépendances.
        
        Args:
            dialogue_service: Service de génération de dialogue.
            prompt_engine: Moteur de construction de prompts.
            skill_service: Service de catalogue des compétences.
            trait_service: Service de catalogue des traits.
            config_service: Service de configuration.
            usage_service: Service de tracking usage LLM.
            request_id: ID de la requête pour logging.
        """
        self.dialogue_service = dialogue_service
        self.prompt_engine = prompt_engine
        self.skill_service = skill_service
        self.trait_service = trait_service
        self.config_service = config_service
        self.usage_service = usage_service
        self.request_id = request_id
    
    async def generate_with_events(
        self,
        request_data: GenerateUnityDialogueRequest,
        check_cancelled: Callable[[], bool]
    ) -> AsyncGenerator[GenerationEvent, None]:
        """Génère avec yield d'événements SSE.
        
        Args:
            request_data: Paramètres de génération Unity Dialogue.
            check_cancelled: Fonction pour vérifier si la génération a été annulée.
            
        Yields:
            GenerationEvent: Événements de progression (step, metadata, complete, error).
        """
        try:
            # Étape 1: Prompting
            yield GenerationEvent(type='step', data={'step': 'Prompting'})
            
            if check_cancelled():
                yield GenerationEvent(type='error', data={'message': 'Génération annulée', 'code': 'cancelled'})
                return
            
            # 1. Convertir ContextSelection en dict
            context_selections_dict = request_data.context_selections.to_service_dict()
            all_characters = context_selections_dict.get('characters', [])
            if not all_characters:
                raise ValidationException(
                    message="Au moins un personnage doit être sélectionné",
                    request_id=self.request_id
                )
            
            # 2. Déterminer le PNJ interlocuteur
            npc_speaker_id = request_data.npc_speaker_id or all_characters[0]
            
            # 3. Charger catalogues (services injectés)
            skills_list = []
            try:
                skills_list = self.skill_service.load_skills()
            except Exception as e:
                logger.warning(
                    f"Erreur lors du chargement des compétences (request_id: {self.request_id}): {e}",
                    exc_info=True
                )
                # Continuer avec une liste vide si le chargement échoue
            
            traits_list = []
            try:
                traits_list = self.trait_service.get_trait_labels()
            except Exception as e:
                logger.warning(
                    f"Erreur lors du chargement des traits (request_id: {self.request_id}): {e}",
                    exc_info=True
                )
                # Continuer avec une liste vide si le chargement échoue
            
            # 4. Construire le contexte GDD (JSON obligatoire, plus de fallback)
            context_builder = self.dialogue_service.context_builder
            if request_data.previous_dialogue_preview:
                context_builder.set_previous_dialogue_context(request_data.previous_dialogue_preview)
            
            structured_context = context_builder.build_context_json(
                selected_elements=context_selections_dict,
                scene_instruction=request_data.user_instructions,
                field_configs=None,
                organization_mode="narrative",
                max_tokens=request_data.max_context_tokens,
                include_dialogue_type=True,
                element_modes=context_selections_dict.get("_element_modes")
            )
            # Sérialiser en texte pour le LLM
            context_summary = context_builder._context_serializer.serialize_to_text(structured_context)
            
            # 5. Construire le prompt Unity via le builder unique
            prompt_input = PromptInput(
                user_instructions=request_data.user_instructions,
                npc_speaker_id=npc_speaker_id,
                player_character_id="URESAIR",
                skills_list=skills_list,
                traits_list=traits_list,
                context_summary=context_summary,
                structured_context=structured_context,
                scene_location=request_data.context_selections.scene_location,
                max_choices=request_data.max_choices,
                choices_mode=request_data.choices_mode,
                narrative_tags=request_data.narrative_tags,
                author_profile=request_data.author_profile,
                vocabulary_config=request_data.vocabulary_config,
                include_narrative_guides=request_data.include_narrative_guides,
                in_game_flags=request_data.in_game_flags
            )
            
            built = self.prompt_engine.build_prompt(prompt_input)
            prompt = built.raw_prompt
            prompt_hash = built.prompt_hash
            estimated_tokens = built.token_count
            
            # Étape 2: Generating
            yield GenerationEvent(type='step', data={'step': 'Generating'})
            
            if check_cancelled():
                yield GenerationEvent(type='error', data={'message': 'Génération annulée', 'code': 'cancelled'})
                return
            
            # 6. Créer le client LLM
            llm_client = LLMClientFactory.create_client(
                model_id=request_data.llm_model_identifier,
                config=self.config_service.get_llm_config(),
                available_models=self.config_service.get_available_llm_models(),
                usage_service=self.usage_service,
                request_id=self.request_id,
                endpoint="generate/unity-dialogue"
            )
            
            if request_data.max_completion_tokens is not None:
                llm_client.max_tokens = request_data.max_completion_tokens
            
            # Configurer le reasoning effort si fourni (uniquement pour GPT-5.2)
            if request_data.reasoning_effort is not None:
                llm_client.reasoning_effort = request_data.reasoning_effort
            
            # 7. Générer via Structured Output
            # #region agent log
            import json
            try:
                with open('f:\\Projets\\Notion_Scrapper\\DialogueGenerator\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"id": f"log_{int(__import__('time').time() * 1000)}_before_generate", "timestamp": int(__import__('time').time() * 1000), "location": "unity_dialogue_orchestrator.py:generate_with_events:before_generate", "message": "About to call generate_dialogue_node", "data": {"request_id": self.request_id, "job_id": getattr(self, 'job_id', None)}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "F"}) + '\n')
            except: pass
            # #endregion
            unity_service = UnityDialogueGenerationService()
            generation_response = await unity_service.generate_dialogue_node(
                llm_client=llm_client,
                prompt=prompt,
                system_prompt_override=request_data.system_prompt_override,
                max_choices=request_data.max_choices
            )
            # #region agent log
            try:
                with open('f:\\Projets\\Notion_Scrapper\\DialogueGenerator\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"id": f"log_{int(__import__('time').time() * 1000)}_after_generate", "timestamp": int(__import__('time').time() * 1000), "location": "unity_dialogue_orchestrator.py:generate_with_events:after_generate", "message": "generate_dialogue_node completed", "data": {"request_id": self.request_id, "has_response": bool(generation_response)}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "F"}) + '\n')
            except: pass
            # #endregion
            
            # Streaming simulé du contenu généré (caractère par caractère)
            stream_text = self._build_stream_text(generation_response)
            if stream_text:
                async for chunk_event in self._stream_text(stream_text, check_cancelled):
                    yield chunk_event
            
            if check_cancelled():
                yield GenerationEvent(type='error', data={'message': 'Génération annulée', 'code': 'cancelled'})
                return
            
            # 8. Enrichir et normaliser
            # FIX: Envoyer 'Validating' APRÈS l'enrichissement pour que l'utilisateur voie la validation en cours
            # (Les opérations synchrones peuvent bloquer le générateur async, donc on envoie l'événement après)
            enriched_nodes = unity_service.enrich_with_ids(content=generation_response, start_id="START")
            renderer = UnityJsonRenderer()
            json_content = renderer.render_unity_nodes(nodes=enriched_nodes, normalize=True)
            
            # Étape 3: Validating (après enrichissement pour garantir l'ordre d'envoi)
            yield GenerationEvent(type='step', data={'step': 'Validating'})
            
            if check_cancelled():
                yield GenerationEvent(type='error', data={'message': 'Génération annulée', 'code': 'cancelled'})
                return
            
            # 9. Extraire le titre
            dialogue_title = generation_response.title if hasattr(generation_response, 'title') else None
            
            # Convertir structured_prompt en dict pour la réponse
            structured_prompt_dict = None
            if built.structured_prompt:
                try:
                    structured_prompt_dict = built.structured_prompt.model_dump()
                except Exception as e:
                    logger.warning(f"Erreur lors de la conversion du structured_prompt en dict: {e}")
            
            # Extraire le reasoning trace du client LLM si disponible
            reasoning_trace = getattr(llm_client, 'reasoning_trace', None)
            
            # Calculer le coût (si disponible)
            cost = 0.0
            if hasattr(llm_client, 'last_call_cost'):
                cost = llm_client.last_call_cost or 0.0
            elif hasattr(self.usage_service, 'get_last_call_cost'):
                cost = self.usage_service.get_last_call_cost() or 0.0
            
            # Metadata
            yield GenerationEvent(type='metadata', data={
                'tokens': estimated_tokens,
                'cost': cost
            })
            
            # Étape 4: Complete
            result = GenerateUnityDialogueResponse(
                json_content=json_content,
                title=dialogue_title,
                raw_prompt=prompt,
                prompt_hash=prompt_hash,
                estimated_tokens=estimated_tokens,
                warning=getattr(llm_client, 'warning', None),
                structured_prompt=structured_prompt_dict,
                reasoning_trace=reasoning_trace
            )
            
            yield GenerationEvent(type='complete', data={'result': result.model_dump(mode='json')})
            
        except ValidationException:
            # Re-raise ValidationException sans modification
            raise
        except Exception as e:
            logger.exception(f"Erreur génération Unity (request_id: {self.request_id}): {e}")
            yield GenerationEvent(type='error', data={'message': str(e)})
    
    def _build_stream_text(self, generation_response: Any) -> str:
        """Construit un texte lisible à streamer depuis la réponse Unity."""
        # #region agent log
        import json
        try:
            with open('f:\\Projets\\Notion_Scrapper\\DialogueGenerator\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"id": f"log_{int(__import__('time').time() * 1000)}_build_start", "timestamp": int(__import__('time').time() * 1000), "location": "unity_dialogue_orchestrator.py:_build_stream_text:entry", "message": "Building stream text from generation_response", "data": {"has_node": hasattr(generation_response, 'node')}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "B"}) + '\n')
        except: pass
        # #endregion
        node = getattr(generation_response, 'node', None)
        if not node:
            return ''
        
        parts = []
        speaker = getattr(node, 'speaker', None)
        line = getattr(node, 'line', None)
        # #region agent log
        try:
            with open('f:\\Projets\\Notion_Scrapper\\DialogueGenerator\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"id": f"log_{int(__import__('time').time() * 1000)}_extracted", "timestamp": int(__import__('time').time() * 1000), "location": "unity_dialogue_orchestrator.py:_build_stream_text:extracted", "message": "Extracted speaker and line", "data": {"speaker": str(speaker)[:100] if speaker else None, "line": str(line)[:100] if line else None, "speaker_type": type(speaker).__name__, "line_type": type(line).__name__}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "B"}) + '\n')
        except: pass
        # #endregion
        if line:
            if speaker:
                parts.append(f"{speaker}: {line}")
            else:
                parts.append(line)
        
        choices = getattr(node, 'choices', None)
        if choices:
            # #region agent log
            try:
                with open('f:\\Projets\\Notion_Scrapper\\DialogueGenerator\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"id": f"log_{int(__import__('time').time() * 1000)}_choices_count", "timestamp": int(__import__('time').time() * 1000), "location": "unity_dialogue_orchestrator.py:_build_stream_text:choices_start", "message": "Processing choices", "data": {"choices_count": len(choices) if choices else 0}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "B"}) + '\n')
            except: pass
            # #endregion
            for idx, choice in enumerate(choices, 1):
                text = getattr(choice, 'text', None)
                # #region agent log
                try:
                    with open('f:\\Projets\\Notion_Scrapper\\DialogueGenerator\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                        f.write(json.dumps({"id": f"log_{int(__import__('time').time() * 1000)}_choice_{idx}", "timestamp": int(__import__('time').time() * 1000), "location": "unity_dialogue_orchestrator.py:_build_stream_text:choice", "message": f"Processing choice {idx}", "data": {"choice_text": str(text) if text else None, "choice_text_length": len(str(text)) if text else 0, "choice_text_type": type(text).__name__ if text else None}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "B"}) + '\n')
                except: pass
                # #endregion
                if text:
                    parts.append(f"{idx}. {text}")
        
        result = "\n".join(parts).strip()
        # #region agent log
        try:
            with open('f:\\Projets\\Notion_Scrapper\\DialogueGenerator\\.cursor\\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"id": f"log_{int(__import__('time').time() * 1000)}_build_result", "timestamp": int(__import__('time').time() * 1000), "location": "unity_dialogue_orchestrator.py:_build_stream_text:result", "message": "Built stream text result", "data": {"result_length": len(result), "result_preview": result[:500], "result_suffix": result[-500:] if len(result) > 500 else result, "parts_count": len(parts)}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "B"}) + '\n')
        except: pass
        # #endregion
        return result
    
    async def _stream_text(
        self,
        text: str,
        check_cancelled: Callable[[], bool],
        delay_seconds: float = 0.01
    ) -> AsyncGenerator[GenerationEvent, None]:
        """Stream le texte caractère par caractère avec séquence pour garantir l'ordre.
        
        TCP garantit l'ordre des chunks, mais pour être absolument sûr et gérer
        les cas de buffering, on ajoute un numéro de séquence. Le frontend
        peut réordonner si nécessaire (normalement pas nécessaire avec TCP).
        
        Le flush explicite dans StreamingResponse + headers corrects devraient
        garantir que les chunks arrivent dans l'ordre sans buffering.
        """
        for seq, char in enumerate(text):
            if check_cancelled():
                yield GenerationEvent(type='error', data={'message': 'Génération annulée', 'code': 'cancelled'})
                return
            yield GenerationEvent(type='chunk', data={'content': char, 'sequence': seq})
            await asyncio.sleep(delay_seconds)
    
    async def generate(
        self,
        request_data: GenerateUnityDialogueRequest
    ) -> GenerateUnityDialogueResponse:
        """Génère sans streaming (usage REST).
        
        Args:
            request_data: Paramètres de génération Unity Dialogue.
            
        Returns:
            GenerateUnityDialogueResponse: Réponse avec dialogue Unity JSON.
            
        Raises:
            ValidationException: Si validation échoue.
            InternalServerException: Si génération échoue.
        """
        result = None
        error_message = None
        
        async for event in self.generate_with_events(request_data, lambda: False):
            if event.type == 'complete':
                result = GenerateUnityDialogueResponse(**event.data['result'])
            elif event.type == 'error':
                error_message = event.data['message']
        
        if result is None:
            if error_message:
                raise InternalServerException(message=error_message, request_id=self.request_id)
            else:
                raise InternalServerException(
                    message="Génération échouée sans résultat",
                    request_id=self.request_id
                )
        
        return result
