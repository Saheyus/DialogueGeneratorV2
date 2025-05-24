# DialogueGenerator/llm_client.py
import asyncio
import logging
import os
from abc import ABC, abstractmethod
from openai import AsyncOpenAI
import json # Ajout pour charger la config
from pathlib import Path # Ajout pour le chemin de la config
from typing import List, Optional, Type, TypeVar, Union # Ajout de Type, TypeVar, Union
from pydantic import BaseModel # Ajout de BaseModel pour le typage

logger = logging.getLogger(__name__)

# Chemin vers le fichier de configuration LLM
LLM_CONFIG_PATH = Path(__file__).resolve().parent / "llm_config.json"

class ILLMClient(ABC):
    """Interface pour les clients LLM."""
    @abstractmethod
    async def generate_variants(self, prompt: str, k: int, response_model: Optional[Type[BaseModel]] = None) -> List[Union[str, BaseModel]]:
        """
        Génère k variantes de texte à partir du prompt donné.

        Args:
            prompt (str): Le prompt à envoyer au LLM.
            k (int): Le nombre de variantes à générer.
            response_model (Optional[Type[BaseModel]]): Le modèle Pydantic attendu pour la sortie structurée.

        Returns:
            list[Union[str, BaseModel]]: Une liste de k éléments, chaque élément étant une variante ou une instance de response_model.
        """
        pass

    @abstractmethod
    def get_max_tokens(self) -> int:
        """Retourne le nombre maximum de tokens que le modèle peut gérer pour un prompt."""
        pass

    async def close(self):
        # Implementation of close method
        pass

class DummyLLMClient(ILLMClient):
    def __init__(self, delay_seconds: float = 0.0):
        super().__init__()
        self.delay_seconds = delay_seconds
        logger.info(f"DummyLLMClient initialisé avec un délai de {self.delay_seconds}s par variante.")

    async def generate_variants(self, prompt: str, k: int, response_model: Optional[Type[BaseModel]] = None) -> List[Union[str, BaseModel]]:
        logger.info(f"DummyLLMClient (délai={self.delay_seconds}s): Début de la génération de {k} variante(s). response_model: {response_model}")
        variants = []
        for i in range(k):
            if self.delay_seconds > 0:
                await asyncio.sleep(self.delay_seconds)
            
            if response_model:
                # Simuler une sortie structurée si un modèle est demandé
                # Pour un vrai test, il faudrait instancier response_model avec des données factices
                # Ici, on retourne juste un dict simple pour l'exemple
                dummy_structured_output = {
                    "title": f"Dummy Structured Title {i+1}",
                    "description": f"Dummy description for variant {i+1}. Prompt: {prompt[:30]}...",
                    "items": [f"item_dummy_{j}" for j in range(k)]
                }
                try:
                    # Essayer de valider/créer une instance du modèle Pydantic
                    # Cela suppose que le modèle Pydantic peut être instancié à partir du dict
                    # En réalité, il faudrait un constructeur ou .model_validate()
                    # Pour l'instant, on retourne le dict, ce qui n'est pas idéal mais simule la structure
                    # Pour un test plus poussé, il faudrait créer des instances réelles de response_model
                    parsed_dummy = response_model.model_validate(dummy_structured_output) 
                    variants.append(parsed_dummy)
                    logger.info(f"DummyLLMClient: Variante structurée {i+1} (simulée) générée.")
                except Exception as e_dummy_parse:
                    logger.warning(f"DummyLLMClient: Erreur de validation du modèle Pydantic factice pour la variante {i+1}: {e_dummy_parse}. Retour d'un dict brut.")
                    # En cas d'échec de validation avec le modèle (ex: champs manquants/incorrects dans dummy_structured_output)
                    # on retourne un dict brut pour ne pas planter, mais ce n'est pas une instance du modèle.
                    variants.append(dummy_structured_output) # Ce ne sera pas de type BaseModel

            else:
                variant_text = f"""---title: TitreDummy_Variant{i+1}_{k}
tags: tag_dummy
character_a: PersonnageA_Dummy
character_b: PersonnageB_Dummy
scene: Scene_Dummy
---
// Ceci est le corps de la variante {i+1} générée par DummyLLMClient.
// Prompt reçu : {prompt[:50]}...
<<ligne_de_dialogue_dummy_{i+1}>>
===
"""
            variants.append(variant_text)
            logger.info(f"DummyLLMClient (délai={self.delay_seconds}s): Variante {i+1} générée.")
        logger.info(f"DummyLLMClient (délai={self.delay_seconds}s): Génération de {k} variante(s) terminée.")
        return variants

    def get_max_tokens(self) -> int:
        return 16000 # Valeur arbitraire pour le client factice

    async def close(self):
        # Implementation of close method
        pass

class OpenAIClient(ILLMClient):
    def __init__(self, model_identifier: str, api_key_env_var: str = "OPENAI_API_KEY"):
        """
        Initialise le client OpenAI.

        Args:
            model_identifier (str): L'identifiant du modèle OpenAI à utiliser (ex: "gpt-4o").
            api_key_env_var (str): Le nom de la variable d'environnement contenant la clé API OpenAI.
        """
        self.api_key = os.getenv(api_key_env_var)
        if not self.api_key:
            logger.error(f"La variable d'environnement {api_key_env_var} n'est pas définie.")
            # Pour l'instant, on logue l'erreur et on continue, mais les appels échoueront.
            # Il serait préférable de lever une exception ici pour une gestion d'erreur plus robuste.
            # raise ValueError(f"{api_key_env_var} non configurée.")
        
        self.model = model_identifier
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None
        logger.info(f"OpenAIClient initialisé pour le modèle: {self.model}. Clé API chargée depuis {api_key_env_var}: {'Oui' if self.api_key else 'Non'}")

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

    async def generate_variants(self, prompt: str, k: int, response_model: Optional[Type[BaseModel]] = None) -> List[Union[str, BaseModel]]:
        if not self.client:
            error_msg = "OpenAIClient n'a pas pu être initialisé (clé API manquante ou autre erreur)."
            logger.error(error_msg)
            # Retourner une liste d'erreurs de type str, ou lever une exception
            if response_model: # Si un modèle est attendu, il faut théoriquement retourner une liste de ce type
                               # Mais en cas d'erreur fondamentale, un str est plus informatif ici.
                return [f"Erreur: {error_msg}"] * k # Ou des instances d'un modèle d'erreur Pydantic
            return [f"Erreur: {error_msg}"] * k

        variants = []
        logger.info(f"OpenAIClient: Envoi de la requête pour {k} variante(s) au modèle {self.model}. Mode structuré: {bool(response_model)}.")
        try:
            tasks = []
            for _ in range(k):
                if response_model:
                    # Utilisation de la méthode .parse() pour la sortie structurée
                    # Note: La méthode .parse() ne prend pas de paramètre 'n' pour plusieurs choix.
                    # Donc, si k > 1 avec response_model, on fait k appels .parse().
                    # Chaque appel à .parse() garantit une sortie conforme au response_model.
                    tasks.append(
                        self.client.beta.chat.completions.parse(
                            model=self.model,
                            messages=[
                                {"role": "system", "content": "Tu es un assistant expert en génération de données structurées au format JSON spécifié."},
                                {"role": "user", "content": prompt}
                            ],
                            response_format=response_model,
                            temperature=0.7, # Peut être ajusté
                        )
                    )
                else:
                    # Logique existante pour la sortie textuelle
                    tasks.append(
                        self.client.chat.completions.create(
                            model=self.model,
                            messages=[
                                {"role": "system", "content": "Tu es un assistant expert en écriture de dialogues pour jeux de rôle (RPG) au format Yarn Spinner."},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.7, # Un peu de créativité
                        )
                    )
            
            responses = await asyncio.gather(*tasks)
            
            for i, response in enumerate(responses):
                if response_model:
                    # MODIFIÉ: Extraire l'objet Pydantic de la réponse ParsedChatCompletion
                    parsed_object: Optional[BaseModel] = None
                    if response.choices and response.choices[0].message and response.choices[0].message.parsed:
                        parsed_object = response.choices[0].message.parsed
                    else:
                        # Gérer le cas où la structure attendue n'est pas trouvée
                        logger.error("OpenAIClient: Impossible d'extraire l'objet parsé de la réponse ParsedChatCompletion.")
                        # Retourner une erreur ou une chaîne vide, selon la gestion d'erreur souhaitée
                        # Pour l'instant, on propage None, ce qui sera traité comme une erreur par GenerationPanel
                        pass 

                    if k == 1:
                        if parsed_object:
                            variants.append(parsed_object)
                            logger.info(f"OpenAIClient: Variante structurée 1/1 reçue et parsée.")
                        else:
                            # Ajouter une chaîne d'erreur si le parsing a échoué en amont
                            variants.append("// Erreur: OpenAI n'a pas retourné un objet structuré valide après parsing.")
                    else:
                        if parsed_object:
                            logger.warning(f"OpenAIClient: .parse() a retourné un seul objet structuré, mais k={k} était demandé. Retour de la même instance {k} fois.")
                            for _ in range(k):
                                variants.append(parsed_object) 
                            logger.info(f"OpenAIClient: Variante structurée (dupliquée {k} fois) reçue et parsée.")
                        else:
                            error_message = "// Erreur: OpenAI n'a pas retourné un objet structuré valide après parsing (pour k > 1)."
                            for _ in range(k):
                                variants.append(error_message)
                else:
                    # Logique existante pour la réponse textuelle (response_or_parsed_item est ici un objet ChatCompletion)
                    if response.choices and response.choices[0].message and response.choices[0].message.content:
                        variants.append(response.choices[0].message.content.strip())
                        logger.info(f"OpenAIClient: Variante textuelle {i+1}/{k} reçue.")
            
            logger.info(f"OpenAIClient: {len(variants)} variante(s) reçue(s) avec succès.")

        except Exception as e:
            logger.error(f"OpenAIClient: Erreur lors de l'appel à l'API OpenAI: {e}", exc_info=True) # Ajout de exc_info
            # Renvoyer des messages d'erreur pour chaque variante attendue
            error_content = f"// Erreur lors de la génération OpenAI: {str(e)}"
            if response_model:
                 # En cas d'erreur avec response_model, on ne peut pas garantir le type.
                 # On retourne une liste de chaînes d'erreur.
                 # Idéalement, on pourrait avoir un modèle Pydantic d'erreur et retourner des instances de cela.
                 variants = [error_content] * k
            else:
                variants = [error_content] * k
        
        return variants

    def get_max_tokens(self) -> int:
        # Ces valeurs peuvent dépendre du modèle spécifique.
        # Pour gpt-4o-mini, la fenêtre de contexte est de 128K tokens.
        # Pour gpt-3.5-turbo, c'est souvent 4k ou 16k selon la version.
        # Retournons une valeur "générale" pour l'instant, ou adaptons selon self.model.
        if "gpt-4o-mini" in self.model:
            return 128000 # Fenêtre de contexte totale
        elif "gpt-4" in self.model: # inclut gpt-4, gpt-4-turbo, etc.
            return 128000
        elif "gpt-3.5-turbo-16k" in self.model:
            return 16384
        elif "gpt-3.5-turbo" in self.model:
            return 4096
        else:
            return 4096 # Par défaut pour les autres modèles gpt-3.5 ou inconnus

# Pour des tests rapides (nécessite que OPENAI_API_KEY soit définie dans l'environnement)
async def main_test():
    logging.basicConfig(level=logging.INFO)
    
    # Charger la configuration LLM pour le test
    llm_config = OpenAIClient.load_llm_config()
    default_model = llm_config.get("default_model_identifier", "gpt-4o") # Changé pour gpt-4o pour tester structured output
    api_key_var = llm_config.get("api_key_env_var", "OPENAI_API_KEY")

    # --- Test Dummy ---
    dummy_client = DummyLLMClient(delay_seconds=0.1)
    dummy_prompt = "Instructions pour le dummy..."
    dummy_variants_text = await dummy_client.generate_variants(dummy_prompt, 1) # Test texte
    print("\n--- Variant texte du DummyLLMClient ---")
    print(f"Variante 1:\n{dummy_variants_text[0]}\n")

    # Définition d'un modèle Pydantic simple pour le test du dummy structuré
    class DummyTestModel(BaseModel):
        title: str
        description: str
        items: List[str]

    dummy_variants_structured = await dummy_client.generate_variants(dummy_prompt, 1, response_model=DummyTestModel)
    print("\n--- Variant structuré (simulé) du DummyLLMClient ---")
    if dummy_variants_structured and isinstance(dummy_variants_structured[0], DummyTestModel):
        print(f"Variante 1 (type {type(dummy_variants_structured[0])}):\n{dummy_variants_structured[0].model_dump_json(indent=2)}\n")
    elif dummy_variants_structured: # Si c'est un dict brut (erreur de validation)
        print(f"Variante 1 (type {type(dummy_variants_structured[0])} - validation échouée):\n{dummy_variants_structured[0]}\n")
    else:
        print("Aucune variante structurée (simulée) retournée par le dummy.")

    # --- Test OpenAI ---
    openai_client = OpenAIClient(model_identifier=default_model, api_key_env_var=api_key_var)
    if not openai_client.api_key:
        print(f"{api_key_var} n'est pas configurée. Le test OpenAI sera sauté.")
        await dummy_client.close()
        return

    from prompt_engine import PromptEngine
    from DialogueGenerator.models.dialogue_structure.interaction import Interaction # MODIFIÉ: Import de Interaction

    engine = PromptEngine() # Utilisation du PromptEngine par défaut pour l'instant
    
    # Test OpenAI - Sortie Textuelle (ancienne méthode)
    test_user_goal_text = "Donne-moi une description de la taverne du Crâne Fêlé."
    openai_prompt_text, _ = engine.build_prompt(user_specific_goal=test_user_goal_text) # Contexte minimal
    
    print(f"\n--- Envoi du prompt TEXTUEL suivant à {openai_client.model} ---")
    print(openai_prompt_text)
    print("--------------------------------------------------")
    openai_variants_text = await openai_client.generate_variants(openai_prompt_text, 1)
    print(f"\n--- Variants TEXTUELS de l'OpenAIClient ({openai_client.model}) ---")
    if openai_variants_text and isinstance(openai_variants_text[0], str):
        print(f"Variante 1:\n{openai_variants_text[0]}\n")
    else:
        print(f"Réponse inattendue pour variante textuelle: {openai_variants_text}")

    # Test OpenAI - Sortie Structurée (nouvelle méthode avec Interaction)
    # Il faut un prompt qui guide le LLM vers la structure attendue, même avec .parse()
    # .parse() garantit la forme, mais un bon prompt garantit le contenu pertinent.
    # Pour Interaction, le system_prompt de PromptEngine est déjà conçu pour cela.
    # On va simuler un appel qui demanderait une Interaction complète.
    test_user_goal_structured = "Génère une interaction simple où Bob demande une bière à Alice dans la Taverne du Crâne Fêlé. Alice répond et lui sert."
    
    # Le PromptEngine doit être configuré pour générer le prompt pour une Interaction
    # (ce qui est déjà le cas si generation_params={'generate_interaction': True} est passé)
    openai_prompt_structured, _ = engine.build_prompt(
        user_specific_goal=test_user_goal_structured,
        scene_protagonists={"personnage_a": "Bob", "personnage_b": "Alice"},
        scene_location={"lieu": "Taverne du Crâne Fêlé"},
        context_summary="Bob est un aventurier assoiffé. Alice est la tenancière.",
        generation_params={"generate_interaction": True} # Pour utiliser le system_prompt d'interaction
    )

    print(f"\n--- Envoi du prompt STRUCTURÉ (pour Interaction) suivant à {openai_client.model} ---")
    print(openai_prompt_structured)
    print("--------------------------------------------------")

    # Appel avec le modèle Pydantic Interaction
    # k=1 car .parse() ne gère pas plusieurs choix directement, il faut boucler si k > 1.
    openai_variants_structured = await openai_client.generate_variants(openai_prompt_structured, 1, response_model=Interaction)
    print(f"\n--- Variants STRUCTURÉS (Interaction) de l'OpenAIClient ({openai_client.model}) ---")
    if openai_variants_structured:
        for i, v_struct in enumerate(openai_variants_structured):
            if isinstance(v_struct, Interaction):
                print(f"Variante Structurée {i+1} (type {type(v_struct)}):")
                print(v_struct.model_dump_json(indent=2))
            elif isinstance(v_struct, str): # Cas d'erreur retourné comme string
                print(f"Variante Structurée {i+1} (Erreur):\n{v_struct}")
            else:
                print(f"Variante Structurée {i+1} (type {type(v_struct)} inattendu):\n{v_struct}")
        print("\n")
    else:
        print("Aucune variante structurée (Interaction) retournée.")
    
    await dummy_client.close()
    await openai_client.close() # S'assurer que le client OpenAI est fermé

if __name__ == '__main__':
    # Pour exécuter le test async : python -m DialogueGenerator.llm_client 
    # (si vous êtes dans le dossier parent Notion_Scrapper)
    # ou simplement `python llm_client.py` si vous êtes dans `DialogueGenerator`
    asyncio.run(main_test()) 