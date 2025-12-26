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
                        "nodes": [
                            {
                                "line": "Texte de test généré par DummyLLMClient pour Unity JSON.",
                                "choices": [
                                    {
                                        "text": "Choix de test",
                                        "targetNode": ""
                                    }
                                ]
                            }
                        ]
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
                # Format texte libre au lieu de Yarn (Yarn n'est plus utilisé)
                variant_text = f"Texte de dialogue variante {i+1} généré par DummyLLMClient.\n\nLe personnage A dit : \"Bonjour, je suis une variante de test.\"\n\nLe personnage B répond : \"Moi aussi, c'est pour tester le système sans format Yarn.\""
                variants.append(variant_text)
                logger.info(f"DummyLLMClient: Variante textuelle {i+1} générée (format texte libre, pas Yarn).")
        return variants

    def get_max_tokens(self) -> int:
        return 16000

class OpenAIClient(ILLMClient):
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Clé API OpenAI non fournie ou non trouvée dans les variables d'environnement.")
        
        self.client = AsyncOpenAI(api_key=api_key)
        
        self.llm_config = config if config is not None else {}
        self.model_name = self.llm_config.get("default_model", "gpt-4o")
        self.temperature = self.llm_config.get("temperature", 0.7)
        self.max_tokens = self.llm_config.get("max_tokens", 1500)
        
        self.system_prompt_template = self.llm_config.get(
            "system_prompt_template", 
            "Tu es un assistant expert en écriture de dialogues pour jeux de rôle (RPG)."
        )
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
            logger.debug(f"Schéma de la fonction 'generate_interaction' envoyé à OpenAI: \n{json.dumps(model_schema_for_tool, indent=2, ensure_ascii=False)}")
            logger.debug(f"Messages complets envoyés à OpenAI (avec tool): \n{json.dumps(messages, indent=2, ensure_ascii=False)}")


        for i in range(k):
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
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    n=1,
                    tools=[tool_definition] if tool_definition else NOT_GIVEN,
                    tool_choice=tool_choice_option,
                )
                logger.info(f"Réponse BRUTE de l'API OpenAI reçue pour la variante {i+1}:\n{response.model_dump_json(indent=2)}")

                if response_model and response.choices[0].message.tool_calls:
                    tool_call = response.choices[0].message.tool_calls[0]
                    if tool_call.function.name == "generate_interaction":
                        function_args_raw = tool_call.function.arguments
                        logger.debug(f"Arguments bruts de la fonction reçus: {function_args_raw}")
                        try:
                            parsed_output = response_model.model_validate_json(function_args_raw)
                            generated_results.append(parsed_output)
                            logger.info(f"Variante {i+1} générée et validée avec succès (structured).")
                        except Exception as e:
                            logger.error(f"Erreur de validation Pydantic pour la variante {i+1}: {e}")
                            logger.error(f"Données JSON qui ont échoué à la validation: {function_args_raw}")
                            generated_results.append(f"Erreur de validation: {e} - Données: {function_args_raw}")
                    else:
                        logger.warning(f"Outil inattendu appelé: {tool_call.function.name}")
                        generated_results.append(f"Erreur: Outil inattendu {tool_call.function.name}")

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
                else:
                    logger.warning(f"Aucun contenu ou appel de fonction dans la réponse pour la variante {i+1}.")
                    generated_results.append(f"Erreur: Réponse vide ou inattendue pour la variante {i+1}")
            
            except APIError as e:
                logger.error(f"Erreur API OpenAI lors de la génération de la variante {i+1}: {e}")
                generated_results.append(f"Erreur API: {e}")
            except Exception as e:
                logger.error(f"Erreur inattendue lors de la génération de la variante {i+1}: {e}", exc_info=True)
                generated_results.append(f"Erreur: {e}")
        
        return generated_results

    def get_max_tokens(self) -> int:
        model_lower = self.model_name.lower()
        if "gpt-4o-mini" in model_lower or "gpt-4o" in model_lower:
            return 128000 
        elif "gpt-4-turbo" in model_lower:
            return 128000
        elif "gpt-4" in model_lower: # Inclut gpt-4, gpt-4-0613 etc.
            return 8192
        elif "gpt-3.5-turbo" in model_lower: # Inclut gpt-3.5-turbo, gpt-3.5-turbo-16k etc.
            # Les modèles 3.5 peuvent avoir 4k, 8k, ou 16k. On prend 16k comme une approximation safe pour le prompt total.
            # La limite de complétion est gérée séparément par self.max_tokens.
            return 16385 
        elif "text-davinci" in model_lower: # Modèles plus anciens, moins probables mais pour référence
            return 4096 # Ou 4097 selon les sources, mais 4096 est plus sûr pour le calcul prompt+completion
        else:
            logger.warning(f"Modèle OpenAI inconnu ou non listé pour get_max_tokens: {self.model_name}. Retourne 4096 par défaut.")
            return 4096 

    async def close(self):
        if self.client:
            await self.client.close()

async def main_test():
    from models.dialogue_structure.dynamic_interaction_schema import build_interaction_model_from_structure, DialogueLineElement, PlayerChoicesBlockElement
    
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
    structure_pnj_pj = ["PNJ", "PJ"]
    DynamicTestModel = build_interaction_model_from_structure(structure_pnj_pj)
    
    openai_prompt_structured = (
        "Contexte: Le joueur (Seigneuresse Uresaïr) rencontre Akthar-Neth Amatru, l'Exégète, dans le Coeur du Léviathan. "
        "C'est leur première rencontre. Akthar-Neth est un être ancien et sage, gardien du savoir du Léviathan. "
        "Uresaïr est là pour chercher des réponses sur des visions mystérieuses qui la hantent.\n"
        "Objectif de la scène: Akthar-Neth accueille Uresaïr et lui demande la raison de sa venue. Uresaïr doit pouvoir choisir entre deux raisons principales." 
        "Ton attendu: Génère une ligne pour Akthar-Neth, suivie d'un bloc de deux choix pour Uresaïr."
    )
    
    print(f"\n--- Envoi du prompt STRUCTURÉ (pour {DynamicTestModel.__name__}) à {openai_client.model_name} --- ")
    # Note: Le system_prompt_template est déjà dans openai_client. Il sera combiné avec "Tu DOIS utiliser la fonction..."
    print(f"USER: {openai_prompt_structured}")
    print("--------------------------------------------------")

    openai_variants_structured = await openai_client.generate_variants(openai_prompt_structured, 1, response_model=DynamicTestModel)
    print(f"\n--- Variants STRUCTURÉS ({DynamicTestModel.__name__}) de l'OpenAIClient ({openai_client.model_name}) --- ")
    if openai_variants_structured:
        for i, v_struct in enumerate(openai_variants_structured):
            print(f"Variante {i+1}:")
            if isinstance(v_struct, BaseModel):
                print(v_struct.model_dump_json(indent=2))
                # Essayons aussi de valider l'ordre si c'est une instance du modèle attendu
                from models.dialogue_structure.dynamic_interaction_schema import validate_interaction_elements_order
                if validate_interaction_elements_order(v_struct, structure_pnj_pj):
                    print("Validation de l'ordre des éléments réussie.")
                else:
                    print("ÉCHEC de la validation de l'ordre des éléments.")
            else:
                print(str(v_struct)) # Afficher l'erreur ou le texte brut
            print("---")
    else:
        print("Aucune variante structurée n'a été générée.")

    await openai_client.close()

if __name__ == "__main__":
    asyncio.run(main_test()) 
