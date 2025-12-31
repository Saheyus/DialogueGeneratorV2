# DialogueGenerator/llm_client.py
import asyncio
import logging
import os
import time
from abc import ABC, abstractmethod
from openai import AsyncOpenAI, APIError, NOT_GIVEN
import json # Ajout pour charger la config
from pathlib import Path # Ajout pour le chemin de la config
from typing import List, Optional, Type, TypeVar, Union, Dict, Any # Ajout de Dict, Any
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
                # #region agent log
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "A",
                    "location": "llm_client.py:90",
                    "message": "DummyLLMClient génération variante texte",
                    "data": {"variant_index": i+1, "k_variants": k, "response_model": None},
                    "timestamp": int(time.time() * 1000)
                }
                try:
                    with open(r"f:\Projets\Notion_Scrapper\DialogueGenerator\.cursor\debug.log", "a", encoding="utf-8") as log_file:
                        log_file.write(json.dumps(log_data) + "\n")
                except: pass
                # #endregion
                # DummyLLMClient : génération de variante factice (structured output ou texte)
                variant_text = f"Variante {i+1} générée par DummyLLMClient (mode test)"
                variants.append(variant_text)
                logger.info(f"DummyLLMClient: Variante {i+1} générée (mode test).")
        return variants

    def get_max_tokens(self) -> int:
        return 16000

class OpenAIClient(ILLMClient):
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None, usage_service: Optional[Any] = None, request_id: Optional[str] = None, endpoint: Optional[str] = None):
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Clé API OpenAI non fournie ou non trouvée dans les variables d'environnement.")
        
        self.client = AsyncOpenAI(api_key=api_key)
        
        self.llm_config = config if config is not None else {}
        self.model_name = self.llm_config.get("default_model", "gpt-5.2")
        self.temperature = self.llm_config.get("temperature", 0.7)
        self.max_tokens = self.llm_config.get("max_tokens", 1500)
        
        self.system_prompt_template = self.llm_config.get(
            "system_prompt_template", 
            "Tu es un assistant expert en écriture de dialogues pour jeux de rôle (RPG)."
        )
        
        # Service de tracking (optionnel)
        self.usage_service = usage_service
        self.request_id = request_id or "unknown"
        self.endpoint = endpoint or "unknown"
        
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
                # #region agent log
                log_data = {
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "B",
                    "location": "llm_client.py:190",
                    "message": "OpenAIClient génération variante - messages envoyés",
                    "data": {
                        "variant_index": i+1,
                        "system_message_preview": messages[0]["content"][:200] if messages else None,
                        "user_message_preview": messages[-1]["content"][:200] if messages else None,
                        "has_response_model": response_model is not None
                    },
                    "timestamp": int(time.time() * 1000)
                }
                try:
                    with open(r"f:\Projets\Notion_Scrapper\DialogueGenerator\.cursor\debug.log", "a", encoding="utf-8") as log_file:
                        log_file.write(json.dumps(log_data) + "\n")
                except: pass
                # #endregion
                
                # Créer une fonction wrapper pour l'appel API avec retry et circuit breaker
                # Certains modèles (comme gpt-5.2) nécessitent max_completion_tokens au lieu de max_tokens
                # Certains modèles (gpt-5-mini, gpt-5-nano) ne supportent pas le paramètre temperature
                api_params = {
                    "model": self.model_name,
                    "messages": messages,
                    "n": 1,
                    "tools": [tool_definition] if tool_definition else NOT_GIVEN,
                    "tool_choice": tool_choice_option,
                }
                
                # Ajouter temperature seulement si le modèle le supporte
                if self.model_name and self.model_name not in ModelNames.MODELS_WITHOUT_CUSTOM_TEMPERATURE:
                    api_params["temperature"] = self.temperature
                elif self.model_name and self.model_name in ModelNames.MODELS_WITHOUT_CUSTOM_TEMPERATURE:
                    logger.debug(f"Le modèle {self.model_name} ne supporte pas le paramètre temperature. Il sera omis de la requête API.")
                
                # Utiliser max_completion_tokens pour les modèles récents (gpt-5.x), max_tokens pour les anciens
                if self.model_name and "gpt-5" in self.model_name:
                    # Les modèles "thinking" (mini, nano) nécessitent plus de tokens car ils utilisent des reasoning_tokens
                    # avant de générer la réponse finale
                    if self.model_name and ("gpt-5-mini" in self.model_name or "gpt-5-nano" in self.model_name):
                        # Augmenter la limite pour les modèles thinking (reasoning + output)
                        # Si max_tokens a été explicitement défini (par l'utilisateur), l'utiliser, sinon utiliser 10k par défaut
                        if self.max_tokens >= 10000:
                            # L'utilisateur a déjà défini une valeur élevée, l'utiliser
                            max_completion_tokens = self.max_tokens
                        else:
                            # Utiliser 10k par défaut pour les modèles thinking
                            max_completion_tokens = 10000
                        api_params["max_completion_tokens"] = max_completion_tokens
                        logger.info(f"Modèle thinking détecté ({self.model_name}), utilisation de max_completion_tokens={max_completion_tokens}")
                    else:
                        api_params["max_completion_tokens"] = self.max_tokens
                else:
                    api_params["max_tokens"] = self.max_tokens
                
                # Logger les paramètres API pour comparaison entre modèles
                logger.info(f"Paramètres API pour {self.model_name}: {json.dumps({k: v for k, v in api_params.items() if k != 'messages'}, indent=2, ensure_ascii=False)}")
                
                async def _make_api_call():
                    return await self.client.chat.completions.create(**api_params)
                
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
                    prompt_tokens = response.usage.prompt_tokens or 0
                    completion_tokens = response.usage.completion_tokens or 0
                    total_tokens = response.usage.total_tokens or 0
                
                logger.info(f"Réponse BRUTE de l'API OpenAI reçue pour la variante {i+1} (modèle: {self.model_name}):\n{response.model_dump_json(indent=2)}")
                
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
                    # #region agent log
                    log_data = {
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "B",
                        "location": "llm_client.py:221",
                        "message": "OpenAIClient réponse texte reçue",
                        "data": {
                            "variant_index": i+1,
                            "output_preview": text_output[:300],
                            "contains_yarn_title": "---title:" in text_output,
                            "contains_yarn_separator": "===" in text_output
                        },
                        "timestamp": int(time.time() * 1000)
                    }
                    try:
                        with open(r"f:\Projets\Notion_Scrapper\DialogueGenerator\.cursor\debug.log", "a", encoding="utf-8") as log_file:
                            log_file.write(json.dumps(log_data) + "\n")
                    except: pass
                    # #endregion
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
