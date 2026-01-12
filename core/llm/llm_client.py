# DialogueGenerator/llm_client.py
import asyncio
import logging
import os
import time
from abc import ABC, abstractmethod
from openai import AsyncOpenAI, APIError, NOT_GIVEN
import json # Ajout pour charger la config
from pathlib import Path # Ajout pour le chemin de la config
from typing import List, Optional, Type, TypeVar, Union, Dict, Any, Callable, Coroutine # Ajout de Dict, Any, Callable, Coroutine
from pydantic import BaseModel, ValidationError # Ajout de ValidationError
import pydantic
import inspect # Ajout pour l'inspection de la signature
from constants import ModelNames # Ajout pour vérifier les modèles sans température

logger = logging.getLogger(__name__)

# Chemin vers le fichier de configuration LLM
LLM_CONFIG_PATH = Path(__file__).resolve().parent / "llm_config.json"

class ILLMClient(ABC):
    """Interface pour les clients LLM."""
    @abstractmethod
    async def generate_variants(self, prompt: str, k: int, response_model: Optional[Type[BaseModel]] = None, previous_dialogue_context: Optional[List[Dict[str, Any]]] = None, user_system_prompt_override: Optional[str] = None) -> List[Union[str, BaseModel]]:
        """
        Génère k variantes de texte à partir du prompt donné.

        Args:
            prompt (str): Le prompt à envoyer au LLM.
            k (int): Le nombre de variantes à générer.
            response_model (Optional[Type[BaseModel]]): Le modèle Pydantic attendu pour la sortie structurée.
            previous_dialogue_context (Optional[List[Dict[str, Any]]]): Contexte de dialogue précédent.
            user_system_prompt_override (Optional[str]): Pour surcharger le system prompt.

        Returns:
            list[Union[str, BaseModel]]: Une liste de k éléments, chaque élément étant une variante ou une instance de response_model.
        """
        pass

    @abstractmethod
    def get_max_tokens(self) -> int:
        """Retourne le nombre maximum de tokens que le modèle peut gérer pour un prompt."""
        pass

    async def close(self):
        if hasattr(self, 'client') and hasattr(self.client, 'close'): # Vérifier si le client existe et a une méthode close
            if inspect.iscoroutinefunction(self.client.close):
                await self.client.close()
            else:
                self.client.close() # Pour les clients synchrones si jamais ils sont utilisés dans l'interface
        pass

class DummyLLMClient(ILLMClient):
    def __init__(self, delay_seconds: float = 0.0):
        super().__init__()
        self.delay_seconds = delay_seconds
        logger.info(f"DummyLLMClient initialisé avec un délai de {self.delay_seconds}s par variante.")

    async def generate_variants(self, prompt: str, k: int, response_model: Optional[Type[BaseModel]] = None, previous_dialogue_context: Optional[List[Dict[str, Any]]] = None, user_system_prompt_override: Optional[str] = None) -> List[Union[str, BaseModel]]:
        logger.info(f"DummyLLMClient (délai={self.delay_seconds}s): Début de la génération de {k} variante(s). response_model: {response_model.__name__ if response_model else 'None'}")
        variants = []
        for i in range(k):
            if self.delay_seconds > 0:
                await asyncio.sleep(self.delay_seconds)
            
            if response_model:
                # Cas spécial pour UnityDialogueGenerationResponse
                if response_model.__name__ == "UnityDialogueGenerationResponse":
                    dummy_data = {
                        "title": "Dialogue de test généré par DummyLLMClient",
                        "node": {
                            "line": "Texte de test généré par DummyLLMClient pour Unity JSON.",
                            "choices": [
                                {
                                    "text": "Choix de test 1"
                                },
                                {
                                    "text": "Choix de test 2"
                                }
                            ]
                        }
                    }
                else:
                    # Pour les autres modèles (Interaction, etc.)
                    dummy_data: Dict[str, Any] = {
                        "interaction_id": f"dummy_id_{i+1}",
                        "title": f"Dummy Title {i+1}",
                    }
                    if hasattr(response_model, "model_fields"):
                        phase_idx = 1
                        while f"phase_{phase_idx}" in response_model.model_fields:
                            field_info = response_model.model_fields[f"phase_{phase_idx}"]
                            field_type_name = str(field_info.annotation)
                            if "DialogueLineElement" in field_type_name: 
                                 dummy_data[f"phase_{phase_idx}"] = {"element_type": "dialogue_line", "speaker":"DummyPNJ", "text":f"Ligne PNJ phase {phase_idx} var {i+1}"}
                            elif "PlayerChoicesBlockElement" in field_type_name:
                                 dummy_data[f"phase_{phase_idx}"] = {"element_type": "player_choices_block", "choices":[{"text":f"Choix {c_idx+1}", "next_interaction_id":f"next_dummy_{i+1}_{phase_idx}_{c_idx+1}"} for c_idx in range(2)]}
                            phase_idx += 1
                
                try:
                    parsed_dummy = response_model.model_validate(dummy_data) 
                    variants.append(parsed_dummy)
                    logger.info(f"DummyLLMClient: Variante structurée {i+1} (simulée) générée pour {response_model.__name__}.")
                except ValidationError as e_dummy_parse:
                    logger.warning(f"DummyLLMClient: Erreur de validation Pydantic factice {response_model.__name__} pour la variante {i+1}: {e_dummy_parse}. Retour d'un dict brut: {dummy_data}")
                    variants.append(dummy_data) 
                except Exception as e_generic_dummy:
                    logger.error(f"DummyLLMClient: Erreur générique lors de la simulation de variante structurée: {e_generic_dummy}")
                    variants.append(f"// Erreur Dummy LLM: {e_generic_dummy}")
            else:
                # DummyLLMClient : génération de variante factice (structured output ou texte)
                variant_text = f"Variante {i+1} générée par DummyLLMClient (mode test)"
                variants.append(variant_text)
                logger.info(f"DummyLLMClient: Variante {i+1} générée (mode test).")
        return variants

    def get_max_tokens(self) -> int:
        return 16000

class OpenAIClient(ILLMClient):
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None, usage_service: Optional[Any] = None, request_id: Optional[str] = None, endpoint: Optional[str] = None, reasoning_callback: Optional[Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]] = None):
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Clé API OpenAI non fournie ou non trouvée dans les variables d'environnement.")
        
        self.client = AsyncOpenAI(api_key=api_key)
        
        self.llm_config = config if config is not None else {}
        self.model_name = self.llm_config.get("default_model", "gpt-5.2")
        self.temperature = self.llm_config.get("temperature", 0.7)
        self.max_tokens = self.llm_config.get("max_tokens", 1500)
        self.reasoning_effort = self.llm_config.get("reasoning_effort", None)  # none, low, medium, high, xhigh
        self.reasoning_summary = self.llm_config.get("reasoning_summary", None)  # None, "auto", "detailed"
        
        self.system_prompt_template = self.llm_config.get(
            "system_prompt_template", 
            "Tu es un assistant expert en écriture de dialogues pour jeux de rôle (RPG)."
        )
        
        # Service de tracking (optionnel)
        self.usage_service = usage_service
        self.request_id = request_id or "unknown"
        self.endpoint = endpoint or "unknown"
        
        # Callback pour streaming du reasoning trace (optionnel)
        self.reasoning_callback = reasoning_callback
        self.reasoning_trace: Optional[Dict[str, Any]] = None
        
        # Initialiser retry et circuit breaker (optionnel, peut ne pas être disponible dans tous les contextes)
        self._retry_with_backoff = None
        self._circuit_breaker = None
        try:
            from api.utils.retry import retry_with_backoff
            from api.utils.circuit_breaker import get_llm_circuit_breaker
            self._retry_with_backoff = retry_with_backoff
            self._circuit_breaker = get_llm_circuit_breaker()
            if self._circuit_breaker:
                logger.info("Circuit breaker LLM activé")
            if self._retry_with_backoff:
                logger.info("Retry avec exponential backoff activé pour les appels LLM")
        except (ImportError, AttributeError):
            # Si les modules ne sont pas disponibles (ex: tests, imports circulaires), continuer sans retry/circuit breaker
            logger.debug("Modules retry/circuit_breaker non disponibles. Continuation sans protection.")
        
        logger.info(f"OpenAIClient initialisé avec le modèle: {self.model_name}, API Key présente: {'Oui' if api_key else 'Non'}.")
        logger.info(f"System prompt template utilisé: '{self.system_prompt_template}'")

    @classmethod
    def load_llm_config(cls) -> dict:
        """Charge la configuration depuis llm_config.json."""
        try:
            with open(LLM_CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Fichier de configuration LLM introuvable: {LLM_CONFIG_PATH}")
            return {}
        except json.JSONDecodeError:
            logger.error(f"Erreur de décodage JSON dans {LLM_CONFIG_PATH}")
            return {}
        except Exception as e:
            logger.error(f"Erreur inattendue lors du chargement de {LLM_CONFIG_PATH}: {e}")
            return {}

    async def generate_variants(
        self,
        prompt: str,
        k: int = 1,
        response_model: Optional[Type[BaseModel]] = None,
        previous_dialogue_context: Optional[List[Dict[str, Any]]] = None,
        user_system_prompt_override: Optional[str] = None
    ) -> List[Union[BaseModel, str]]:
        
        generated_results = []
        
        system_message_content = user_system_prompt_override if user_system_prompt_override else self.system_prompt_template
        if response_model:
            system_message_content += " Tu DOIS utiliser la fonction 'generate_interaction' pour formater ta réponse."

        messages = [{"role": "system", "content": system_message_content}]
        if previous_dialogue_context:
            messages.extend(previous_dialogue_context)
        messages.append({"role": "user", "content": prompt})

        logger.debug(f"Messages envoyés au LLM (avant tool): {messages}")

        tool_definition = None
        tool_definition_responses = None
        tool_choice_option = NOT_GIVEN

        if response_model:
            model_schema_for_tool = response_model.model_json_schema()
            
            function_parameters = {
                "type": "object",
                "properties": model_schema_for_tool.get("properties", {}),
                "required": model_schema_for_tool.get("required", []),
            }
            if "$defs" in model_schema_for_tool:
                function_parameters["$defs"] = model_schema_for_tool["$defs"]

            model_schema_for_tool["additionalProperties"] = False

            tool_definition = {
                "type": "function",
                "function": {
                    "name": "generate_interaction",
                    "description": "Génère une interaction de dialogue structurée.",
                    "parameters": model_schema_for_tool
                }
            }
            # Responses API attend un format "tools" différent (name au top-level, pas sous "function")
            tool_definition_responses = {
                "type": "function",
                "name": "generate_interaction",
                "description": "Génère une interaction de dialogue structurée.",
                "parameters": model_schema_for_tool,
            }
            tool_choice_option = {"type": "function", "function": {"name": "generate_interaction"}}
            logger.info(f"Utilisation du structured output avec le modèle: {response_model.__name__}")
            # Note: Tous les modèles GPT-5 supportent le structured output selon la documentation OpenAI
            # Les logs détaillés permettront de comparer les réponses entre modèles
            logger.info(f"Configuration structured output pour {self.model_name}: tool_definition présent, tool_choice forcé")
            logger.debug(f"Schéma de la fonction 'generate_interaction' envoyé à OpenAI: \n{json.dumps(model_schema_for_tool, indent=2, ensure_ascii=False)}")
            logger.debug(f"Messages complets envoyés à OpenAI (avec tool): \n{json.dumps(messages, indent=2, ensure_ascii=False)}")


        for i in range(k):
            start_time = time.time()
            success = False
            error_message = None
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            
            try:
                logger.info(f"Début de la génération de la variante {i+1}/{k} pour le prompt.")
                
                # Choix API OpenAI:
                # - GPT-5.2 / GPT-5.2-pro: utiliser Responses API (supporte reasoning.effort)
                # - Autres modèles: Chat Completions API (historique)
                use_responses_api = bool(self.model_name and self.model_name.startswith("gpt-5.2"))

                # Paramètres pour Chat Completions (legacy)
                chat_params: Dict[str, Any] = {
                    "model": self.model_name,
                    "messages": messages,
                    "n": 1,
                    "tools": [tool_definition] if tool_definition else NOT_GIVEN,
                    "tool_choice": tool_choice_option,
                }

                # Paramètres pour Responses API (nouvelle norme)
                responses_params: Dict[str, Any] = {
                    "model": self.model_name,
                    "input": messages,
                    "tools": [tool_definition_responses] if tool_definition_responses else NOT_GIVEN,
                }
                if tool_definition:
                    # Forcer l'appel du tool de structured output côté Responses
                    responses_params["tool_choice"] = {
                        "type": "allowed_tools",
                        "mode": "required",
                        "tools": [{"type": "function", "name": "generate_interaction"}],
                    }

                # Gestion tokens: Chat completions utilise max_completion_tokens / max_tokens,
                # Responses utilise max_output_tokens.
                if self.model_name and "gpt-5" in self.model_name:
                    # Les modèles "thinking" (mini, nano) peuvent nécessiter plus de tokens (reasoning + output).
                    # Note: mini/nano restent sur Chat Completions dans ce code.
                    if self.model_name and ("gpt-5-mini" in self.model_name or "gpt-5-nano" in self.model_name):
                        if self.max_tokens >= 10000:
                            max_completion_tokens = self.max_tokens
                        else:
                            max_completion_tokens = 10000
                        chat_params["max_completion_tokens"] = max_completion_tokens
                        logger.info(f"Modèle thinking détecté ({self.model_name}), utilisation de max_completion_tokens={max_completion_tokens}")
                    else:
                        chat_params["max_completion_tokens"] = self.max_tokens
                    # Responses API: max_output_tokens
                    responses_params["max_output_tokens"] = self.max_tokens
                else:
                    chat_params["max_tokens"] = self.max_tokens
                    responses_params["max_output_tokens"] = self.max_tokens

                # Reasoning effort et summary: uniquement via Responses API
                if use_responses_api:
                    reasoning_config = {}
                    if self.reasoning_effort is not None:
                        reasoning_config["effort"] = self.reasoning_effort
                        # Activer automatiquement summary="detailed" si un effort est défini et que summary n'est pas explicitement désactivé
                        # "detailed" fournit un résumé plus complet que "auto" selon la doc OpenAI
                        if self.reasoning_summary is None:
                            reasoning_config["summary"] = "detailed"
                        elif self.reasoning_summary is not None:
                            reasoning_config["summary"] = self.reasoning_summary
                    elif self.reasoning_summary is not None:
                        # Si seulement summary est défini (sans effort)
                        reasoning_config["summary"] = self.reasoning_summary
                    
                    if reasoning_config:
                        responses_params["reasoning"] = reasoning_config
                        logger.info(
                            f"Utilisation de reasoning pour {self.model_name} (Responses API): "
                            f"effort={self.reasoning_effort}, summary={reasoning_config.get('summary', 'None')}"
                        )

                # Temperature: Chat Completions OK; Responses API uniquement si reasoning.effort == "none" (ou non spécifié)
                if self.model_name and self.model_name not in ModelNames.MODELS_WITHOUT_CUSTOM_TEMPERATURE:
                    chat_params["temperature"] = self.temperature
                    if use_responses_api and (self.reasoning_effort in (None, "none")):
                        responses_params["temperature"] = self.temperature
                    elif use_responses_api and (self.reasoning_effort not in (None, "none")):
                        logger.debug(
                            f"Temperature omise (Responses API) car reasoning_effort='{self.reasoning_effort}' "
                            f"(temperature supportée uniquement avec reasoning.effort='none')."
                        )
                elif self.model_name and self.model_name in ModelNames.MODELS_WITHOUT_CUSTOM_TEMPERATURE:
                    logger.debug(f"Le modèle {self.model_name} ne supporte pas le paramètre temperature. Il sera omis de la requête API.")

                # Logger les paramètres API (sans prompt complet) pour debug
                if use_responses_api:
                    safe_params = {k: v for k, v in responses_params.items() if k not in ("input",)}
                    logger.info(f"Paramètres API (Responses) pour {self.model_name}: {json.dumps(safe_params, indent=2, ensure_ascii=False)}")
                else:
                    safe_params = {k: v for k, v in chat_params.items() if k not in ("messages",)}
                    logger.info(f"Paramètres API (ChatCompletions) pour {self.model_name}: {json.dumps(safe_params, indent=2, ensure_ascii=False)}")
                
                async def _make_api_call():
                    try:
                        if use_responses_api:
                            result = await self.client.responses.create(**responses_params)
                        else:
                            result = await self.client.chat.completions.create(**chat_params)
                        return result
                    except Exception as api_error:
                        raise
                
                # Appliquer retry et circuit breaker si disponibles
                # Le retry doit envelopper le circuit breaker
                if self._retry_with_backoff and self._circuit_breaker:
                    # Les deux sont disponibles: retry enveloppe circuit breaker
                    async def _make_api_call_with_circuit_breaker():
                        return await self._circuit_breaker.call_async(_make_api_call)
                    response = await self._retry_with_backoff(_make_api_call_with_circuit_breaker)
                elif self._circuit_breaker:
                    # Circuit breaker seul
                    response = await self._circuit_breaker.call_async(_make_api_call)
                elif self._retry_with_backoff:
                    # Retry seul
                    response = await self._retry_with_backoff(_make_api_call)
                else:
                    # Pas de protection
                    response = await _make_api_call()
                
                # Extraire les métriques d'utilisation
                if hasattr(response, 'usage') and response.usage:
                    # Chat Completions
                    if hasattr(response.usage, "prompt_tokens"):
                        prompt_tokens = response.usage.prompt_tokens or 0
                        completion_tokens = response.usage.completion_tokens or 0
                        total_tokens = response.usage.total_tokens or 0
                    # Responses
                    elif hasattr(response.usage, "input_tokens"):
                        prompt_tokens = getattr(response.usage, "input_tokens", 0) or 0
                        completion_tokens = getattr(response.usage, "output_tokens", 0) or 0
                        total_tokens = prompt_tokens + completion_tokens

                try:
                    logger.info(
                        f"Réponse BRUTE de l'API OpenAI reçue pour la variante {i+1} "
                        f"(modèle: {self.model_name}, api={'responses' if use_responses_api else 'chat_completions'}):\n"
                        f"{response.model_dump_json(indent=2)}"
                    )
                except Exception:
                    logger.info(
                        f"Réponse reçue (non sérialisable) pour la variante {i+1} "
                        f"(modèle: {self.model_name}, api={'responses' if use_responses_api else 'chat_completions'})."
                    )

                # --- Extraction et affichage de la phase réflexive (reasoning trace) ---
                if use_responses_api:
                    reasoning_data = getattr(response, "reasoning", None)
                    if reasoning_data:
                        try:
                            
                            # Essayer d'accéder aux différents champs du reasoning
                            reasoning_effort = getattr(reasoning_data, "effort", None)
                            reasoning_summary = getattr(reasoning_data, "summary", None)
                            reasoning_items = getattr(reasoning_data, "items", None)
                            
                            # Construire un dictionnaire avec le reasoning trace
                            reasoning_trace_dict = {
                                "effort": reasoning_effort,
                                "summary": reasoning_summary,
                                "items": None,
                                "items_count": len(reasoning_items) if reasoning_items else 0
                            }
                            
                            # Convertir les items en dict si disponibles
                            if reasoning_items:
                                try:
                                    reasoning_trace_dict["items"] = [
                                        item.model_dump() if hasattr(item, 'model_dump') else str(item)
                                        for item in reasoning_items
                                    ]
                                except Exception:
                                    reasoning_trace_dict["items"] = [str(item) for item in reasoning_items]
                            
                            # Stocker le reasoning trace dans l'instance
                            self.reasoning_trace = reasoning_trace_dict
                            
                            # Appeler le callback si fourni pour streaming
                            if self.reasoning_callback:
                                try:
                                    await self.reasoning_callback(reasoning_trace_dict)
                                except Exception as callback_error:
                                    logger.warning(f"Erreur lors de l'appel du callback reasoning: {callback_error}")
                            
                            logger.info(
                                f"\n{'='*80}\n"
                                f"PHASE RÉFLEXIVE (Reasoning Trace) - Variante {i+1}\n"
                                f"{'='*80}\n"
                                f"Effort: {reasoning_effort}\n"
                                f"Summary: {reasoning_summary}\n"
                            )
                            
                            if reasoning_items:
                                logger.info(f"Nombre d'étapes de raisonnement: {len(reasoning_items)}")
                                for idx, item in enumerate(reasoning_items[:10], 1):  # Limiter à 10 pour éviter les logs trop longs
                                    try:
                                        item_str = json.dumps(item.model_dump() if hasattr(item, 'model_dump') else str(item), indent=2, ensure_ascii=False)
                                        logger.info(f"Étape {idx}:\n{item_str}")
                                    except Exception:
                                        logger.info(f"Étape {idx}: {str(item)[:500]}")
                                
                                if len(reasoning_items) > 10:
                                    logger.info(f"... ({len(reasoning_items) - 10} étapes supplémentaires)")
                            
                            # Afficher le reasoning complet en JSON si disponible
                            try:
                                reasoning_json = reasoning_data.model_dump_json(indent=2) if hasattr(reasoning_data, 'model_dump_json') else json.dumps(reasoning_data, indent=2, ensure_ascii=False, default=str)
                                logger.debug(f"Reasoning trace complet (JSON):\n{reasoning_json}")
                            except Exception:
                                pass
                            
                            logger.info(f"{'='*80}\n")
                        except Exception as reasoning_error:
                            logger.warning(f"Erreur lors de l'extraction du reasoning trace: {reasoning_error}")
                            # Fallback: essayer d'afficher le reasoning brut
                            try:
                                logger.info(f"Reasoning trace (brut): {str(reasoning_data)[:1000]}")
                            except Exception:
                                pass
                    else:
                        logger.debug(f"Aucun reasoning trace disponible pour la variante {i+1} (reasoning_effort={self.reasoning_effort})")
                        self.reasoning_trace = None

                # --- Parsing: Responses API ---
                if use_responses_api:
                    # Debug: types d'items output
                    output_items = getattr(response, "output", None) or []
                    output_types = [getattr(it, "type", None) for it in output_items]

                    # Extraire le reasoning trace depuis output (le vrai contenu, pas response.reasoning qui est juste la config)
                    reasoning_content_item = None
                    for item in output_items:
                        if getattr(item, "type", None) == "reasoning":
                            reasoning_content_item = item
                            break
                    
                    if reasoning_content_item:
                        try:
                            # Extraire le contenu du reasoning depuis l'item
                            # Le résumé peut être une liste d'objets ou une chaîne
                            summary_raw = getattr(reasoning_content_item, "summary", None)
                            reasoning_summary_text = None
                            
                            if isinstance(summary_raw, list):
                                # Selon la doc OpenAI, summary est un tableau de chaînes de caractères
                                # Joindre avec des retours à la ligne pour une meilleure lisibilité
                                parts = []
                                for part in summary_raw:
                                    if isinstance(part, str):
                                        parts.append(part)
                                    elif hasattr(part, "text"):
                                        parts.append(str(part.text))
                                    elif isinstance(part, dict) and "text" in part:
                                        parts.append(str(part["text"]))
                                    else:
                                        # Fallback: convertir en string
                                        parts.append(str(part))
                                reasoning_summary_text = "\n".join(parts) if parts else None
                            elif isinstance(summary_raw, str):
                                reasoning_summary_text = summary_raw
                            
                            # Fallback sur content ou text si summary est toujours vide
                            if not reasoning_summary_text:
                                reasoning_summary_text = getattr(reasoning_content_item, "text", None) or getattr(reasoning_content_item, "content", None)
                            
                            # Mettre à jour le reasoning_trace avec le vrai contenu
                            if self.reasoning_trace:
                                # Remplacer le summary par le vrai texte si disponible
                                if reasoning_summary_text and reasoning_summary_text != "detailed":
                                    self.reasoning_trace["summary"] = reasoning_summary_text
                                
                                # Essayer d'extraire des items structurés si disponibles
                                reasoning_items_content = getattr(reasoning_content_item, "items", None)
                                if reasoning_items_content:
                                    try:
                                        self.reasoning_trace["items"] = [
                                            item.model_dump() if hasattr(item, 'model_dump') else str(item)
                                            for item in reasoning_items_content
                                        ]
                                        self.reasoning_trace["items_count"] = len(reasoning_items_content)
                                    except Exception:
                                        self.reasoning_trace["items"] = [str(item) for item in reasoning_items_content]
                                        self.reasoning_trace["items_count"] = len(reasoning_items_content)
                                
                                logger.info(f"Reasoning trace extrait depuis output: summary présent={bool(self.reasoning_trace.get('summary'))}, items présents={bool(self.reasoning_trace.get('items'))}")
                        except Exception as e:
                            logger.warning(f"Erreur lors de l'extraction du reasoning depuis output: {e}")

                    function_args_raw: Optional[str] = None
                    function_name: Optional[str] = None
                    for item in output_items:
                        item_type = getattr(item, "type", None)
                        if item_type in ("function_call", "tool_call", "function"):
                            name = getattr(item, "name", None)
                            args = getattr(item, "arguments", None)
                            # Certains SDK encapsulent sous item.function
                            if name is None and getattr(item, "function", None) is not None:
                                name = getattr(item.function, "name", None)
                                args = getattr(item.function, "arguments", None)
                            if name:
                                function_name = name
                            if name == "generate_interaction" and args:
                                function_args_raw = args
                                break

                    if response_model and function_args_raw:
                        logger.debug(f"Arguments bruts de la fonction reçus (Responses API): {function_args_raw}")
                        try:
                            parsed_output = response_model.model_validate_json(function_args_raw)
                            generated_results.append(parsed_output)
                            logger.info(f"Variante {i+1} générée et validée avec succès (structured, Responses API).")
                            success = True
                        except Exception as e:
                            logger.error(f"Erreur de validation Pydantic pour la variante {i+1} (Responses API): {e}")
                            logger.error(f"Données JSON qui ont échoué à la validation (Responses API): {function_args_raw}")
                            generated_results.append(f"Erreur de validation: {e} - Données: {function_args_raw}")
                            error_message = f"Validation error: {e}"
                    elif response_model and not function_args_raw:
                        # Cas critique: response_model requis mais aucun tool call attendu trouvé
                        text_output = getattr(response, "output_text", None)
                        text_preview = (text_output or "")[:500]
                        error_msg = (
                            f"Le modèle {self.model_name} n'a pas retourné de structured output (function_call) alors qu'un response_model était requis (Responses API). "
                            f"Outil appelé: {function_name}. "
                            f"Réponse texte (premiers 500 caractères): {text_preview}"
                        )
                        logger.error(error_msg)
                        generated_results.append(f"Erreur: {error_msg}")
                        error_message = "Structured output not received from Responses API"
                        success = False
                    else:
                        # Texte simple
                        text_output = getattr(response, "output_text", "") or ""
                        text_output = text_output.strip()
                        if text_output:
                            generated_results.append(text_output)
                            logger.info(f"Variante {i+1} générée avec succès (texte simple, Responses API).")
                            success = True
                        else:
                            error_msg = f"Réponse vide ou inattendue pour la variante {i+1} (Responses API)"
                            generated_results.append(f"Erreur: {error_msg}")
                            error_message = error_msg
                            success = False

                # --- Parsing: Chat Completions API ---
                else:
                    # Logger spécifiquement les tool_calls pour comparaison
                    if response.choices and response.choices[0].message:
                        has_tool_calls = hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls
                        has_content = hasattr(response.choices[0].message, 'content') and response.choices[0].message.content
                        finish_reason = getattr(response.choices[0], 'finish_reason', 'unknown')
                        logger.info(f"Analyse réponse {self.model_name}: tool_calls={bool(has_tool_calls)}, content={bool(has_content)}, finish_reason={finish_reason}")

                    if response_model and response.choices[0].message.tool_calls:
                        tool_call = response.choices[0].message.tool_calls[0]
                        if tool_call.function.name == "generate_interaction":
                            function_args_raw = tool_call.function.arguments
                            logger.debug(f"Arguments bruts de la fonction reçus: {function_args_raw}")
                            try:
                                parsed_output = response_model.model_validate_json(function_args_raw)
                                generated_results.append(parsed_output)
                                logger.info(f"Variante {i+1} générée et validée avec succès (structured).")
                                success = True
                            except Exception as e:
                                logger.error(f"Erreur de validation Pydantic pour la variante {i+1}: {e}")
                                logger.error(f"Données JSON qui ont échoué à la validation: {function_args_raw}")
                                generated_results.append(f"Erreur de validation: {e} - Données: {function_args_raw}")
                                error_message = f"Validation error: {e}"
                        else:
                            logger.warning(f"Outil inattendu appelé: {tool_call.function.name}")
                            generated_results.append(f"Erreur: Outil inattendu {tool_call.function.name}")
                            error_message = f"Unexpected tool: {tool_call.function.name}"

                    elif response_model and response.choices and response.choices[0].message and response.choices[0].message.content:
                        # Cas critique: response_model requis mais le modèle a retourné du texte au lieu de tool_calls
                        text_output = response.choices[0].message.content.strip()
                        finish_reason = response.choices[0].finish_reason if hasattr(response.choices[0], 'finish_reason') else "unknown"
                        
                        error_msg = (
                            f"Le modèle {self.model_name} n'a pas retourné de structured output (tool_calls) alors qu'un response_model était requis. "
                            f"Finish reason: {finish_reason}. "
                            f"Le modèle a retourné du texte à la place. "
                            f"Cela peut indiquer que le modèle ne supporte pas correctement le structured output (function calling). "
                            f"Essayez d'utiliser un modèle différent comme 'gpt-5.2'. "
                            f"Réponse reçue (premiers 500 caractères): {text_output[:500]}"
                        )
                        logger.error(error_msg)
                        generated_results.append(f"Erreur: {error_msg}")
                        error_message = f"Structured output not supported by {self.model_name}: model returned text instead of tool_calls"
                        success = False

                    elif response.choices and response.choices[0].message and response.choices[0].message.content:
                        text_output = response.choices[0].message.content.strip()
                        generated_results.append(text_output)
                        logger.info(f"Variante {i+1} générée avec succès (texte simple).")
                        success = True
                    else:
                        logger.warning(f"Aucun contenu ou appel de fonction dans la réponse pour la variante {i+1}.")
                        finish_reason = response.choices[0].finish_reason if (response.choices and response.choices[0] and hasattr(response.choices[0], 'finish_reason')) else "unknown"
                        error_msg = f"Réponse vide ou inattendue pour la variante {i+1} (finish_reason: {finish_reason})"
                        if response_model:
                            error_msg += f". Structured output (response_model) était requis mais non reçu du modèle {self.model_name}."
                        generated_results.append(f"Erreur: {error_msg}")
                        error_message = error_msg
            
            except APIError as e:
                logger.error(f"Erreur API OpenAI lors de la génération de la variante {i+1}: {e}")
                generated_results.append(f"Erreur API: {e}")
                error_message = str(e)
            except Exception as e:
                logger.error(f"Erreur inattendue lors de la génération de la variante {i+1}: {e}", exc_info=True)
                generated_results.append(f"Erreur: {e}")
                error_message = str(e)
            finally:
                # Calculer la durée
                duration_ms = int((time.time() - start_time) * 1000)
                
                # Enregistrer l'utilisation si le service est disponible
                if self.usage_service:
                    try:
                        self.usage_service.track_usage(
                            request_id=self.request_id,
                            model_name=self.model_name,
                            prompt_tokens=prompt_tokens,
                            completion_tokens=completion_tokens,
                            total_tokens=total_tokens,
                            duration_ms=duration_ms,
                            success=success,
                            endpoint=self.endpoint,
                            k_variants=k,
                            error_message=error_message
                        )
                    except Exception as tracking_error:
                        # Ne pas faire échouer l'appel LLM si le tracking échoue
                        logger.error(f"Erreur lors du tracking de l'usage LLM: {tracking_error}", exc_info=True)
        
        return generated_results

    def get_max_tokens(self) -> int:
        model_lower = self.model_name.lower()
        if "gpt-5.2" in model_lower:
            return 128000  # GPT-5.2 et ses variantes (mini, nano, thinking) supportent 128k tokens
        else:
            logger.warning(f"Modèle OpenAI inconnu ou non listé pour get_max_tokens: {self.model_name}. Retourne 4096 par défaut.")
            return 4096 

    async def close(self):
        if self.client:
            await self.client.close()

async def main_test():
    # build_interaction_model_from_structure supprimé - système obsolète
    
    # Configurer le logging pour voir les messages DEBUG de ce module et des modules Pydantic/OpenAI si nécessaire
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Récupérer la clé API depuis les variables d'environnement
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Erreur: La variable d'environnement OPENAI_API_KEY n'est pas définie.")
        return

    # Charger la configuration LLM (pourrait être passé à OpenAIClient)
    client_config = OpenAIClient.load_llm_config()
    openai_client = OpenAIClient(api_key=api_key, config=client_config)

    # --- Test 1: Génération de texte simple ---
    # ... (test texte simple inchangé)

    # --- Test 2: Génération structurée avec Pydantic dynamique ---
    # build_interaction_model_from_structure supprimé - système obsolète
    # DynamicTestModel supprimé - système obsolète
    
    openai_prompt_structured = (
        "Contexte: Le joueur (Seigneuresse Uresaïr) rencontre Akthar-Neth Amatru, l'Exégète, dans le Coeur du Léviathan. "
        "C'est leur première rencontre. Akthar-Neth est un être ancien et sage, gardien du savoir du Léviathan. "
        "Uresaïr est là pour chercher des réponses sur des visions mystérieuses qui la hantent.\n"
        "Objectif de la scène: Akthar-Neth accueille Uresaïr et lui demande la raison de sa venue. Uresaïr doit pouvoir choisir entre deux raisons principales." 
        "Ton attendu: Génère une ligne pour Akthar-Neth, suivie d'un bloc de deux choix pour Uresaïr."
    )
    
    print(f"\n--- Envoi du prompt STRUCTURÉ (système obsolète) à {openai_client.model_name} --- ")
    # Note: Le system_prompt_template est déjà dans openai_client. Il sera combiné avec "Tu DOIS utiliser la fonction..."
    print(f"USER: {openai_prompt_structured}")
    print("--------------------------------------------------")

    # Test de génération structurée supprimé - système obsolète (DynamicTestModel)
    # openai_variants_structured = await openai_client.generate_variants(openai_prompt_structured, 1, response_model=DynamicTestModel)
    print(f"\n--- Test de génération structurée supprimé (système obsolète) --- ")
    # Code de test supprimé - système obsolète

    await openai_client.close()

if __name__ == "__main__":
    asyncio.run(main_test()) 
