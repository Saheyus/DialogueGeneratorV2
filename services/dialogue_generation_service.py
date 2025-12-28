import logging
import json
import re
from typing import Optional, Any, Tuple, List, Dict, Union, Type
from pydantic import BaseModel
import uuid
from abc import ABC, abstractmethod
import asyncio

try:
    from ..context_builder import ContextBuilder
    from ..prompt_engine import PromptEngine
    from ..llm_client import ILLMClient # Utiliser l'interface
except ImportError:
    # Support pour exécution directe ou tests unitaires hors contexte de package complet
    import sys
    from pathlib import Path
    current_dir = Path(__file__).resolve().parent.parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    from context_builder import ContextBuilder
    from prompt_engine import PromptEngine
    from llm_client import ILLMClient

logger = logging.getLogger(__name__)

class IDialogueGenerationService(ABC):
    @abstractmethod
    async def generate_dialogue_variants(self, 
                                         llm_client: ILLMClient, 
                                         k_variants: int, 
                                         max_context_tokens_for_context_builder: int, 
                                         structured_output: bool, 
                                         user_instructions: str, 
                                         system_prompt_override: Optional[str], 
                                         context_selections: Dict[str, Any], 
                                         current_llm_model_identifier: str
                                         ) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str], Optional[int]]:
        pass

    # generate_interaction_variants supprimé - système obsolète remplacé par Unity JSON

    @abstractmethod
    async def generate_structured_object_variants(self,
                                               llm_client: ILLMClient,
                                               k_variants: int,
                                               max_context_tokens_for_context_builder: int,
                                               user_instructions: str,
                                               system_prompt_override: Optional[str],
                                               context_selections: Dict[str, Any], # Doit contenir _scene_protagonists, _scene_location
                                               dialogue_structure_description: str, # Description de la structure pour le prompt
                                               target_response_model: Type[BaseModel], # Le modèle Pydantic pour la réponse LLM
                                               current_llm_model_identifier: str # Pour logging ou logique spécifique au modèle
                                               ) -> Tuple[Optional[List[BaseModel]], Optional[str], Optional[int]]:
        pass

class DialogueGenerationService(IDialogueGenerationService):
    def __init__(self, context_builder: ContextBuilder, prompt_engine: PromptEngine):
        """
        Initialise le service de génération de dialogues.
        
        Args:
            context_builder: Composant qui construit le contexte basé sur les sélections utilisateur
            prompt_engine: Composant qui construit les prompts pour le LLM
        """
        self.context_builder = context_builder
        self.prompt_engine = prompt_engine
        
        # Initialisation du logger
        self.logger = logging.getLogger(__name__)
        logger.info("DialogueGenerationService initialized.")

    async def generate_dialogue_variants(self, 
                                         llm_client: ILLMClient, 
                                         k_variants: int, 
                                         max_context_tokens_for_context_builder: int, 
                                         structured_output: bool,
                                         user_instructions: str, 
                                         system_prompt_override: Optional[str], 
                                         context_selections: Dict[str, Any],
                                         current_llm_model_identifier: str
                                         ) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str], Optional[int]]:
        logger.info(f"Service: Starting TEXT dialogue generation. Model: {current_llm_model_identifier}, K: {k_variants}")
        original_system_prompt = None
        final_prompt_str = None
        estimated_tokens = 0
        variants_output: Optional[List[Dict[str, Any]]] = []
        # Copie pour pouvoir utiliser .pop() sans affecter l'original en dehors de cette portée
        current_context_selections = context_selections.copy()

        try:
            context_summary_text = self._build_context_summary(
                current_context_selections, user_instructions, max_context_tokens_for_context_builder # Utilise la copie
            )

            if system_prompt_override is not None and self.prompt_engine.system_prompt_template != system_prompt_override:
                original_system_prompt = self.prompt_engine.system_prompt_template
                self.prompt_engine.system_prompt_template = system_prompt_override
                logger.info(f"System prompt temporarily set for TEXT: '{system_prompt_override[:100]}...'" ) 

            # Extraire les informations de scène pour PromptEngine depuis context_selections
            scene_protagonists_dict = current_context_selections.pop("_scene_protagonists", {})
            scene_location_dict = current_context_selections.pop("_scene_location", {})

            generation_params_for_prompt_build = {
                "structured_generation_request": structured_output,
                "generate_interaction": False 
            }
            final_prompt_str, estimated_tokens = self.prompt_engine.build_prompt(
                context_summary=context_summary_text,
                user_specific_goal=user_instructions,
                scene_protagonists=scene_protagonists_dict,
                scene_location=scene_location_dict,
                generation_params=generation_params_for_prompt_build
            )
            logger.info(f"Final prompt for TEXT dialogue built. Estimated tokens: {estimated_tokens}. Length: {len(final_prompt_str)} chars.")
            
            if not final_prompt_str:
                logger.error("Failed to build prompt string (empty) for TEXT dialogue.")
                self._restore_prompt_on_error(original_system_prompt)
                return None, "Error: Prompt could not be built.", 0

            if not llm_client:
                logger.error("LLM client is None, cannot generate TEXT variants.")
                self._restore_prompt_on_error(original_system_prompt)
                return None, final_prompt_str, estimated_tokens

            logger.debug(f"Calling LLM to generate {k_variants} TEXT variants.")
            llm_raw_variants = await llm_client.generate_variants(prompt=final_prompt_str, k=k_variants)
            
            if llm_raw_variants:
                variants_output = []
                for i, variant_text in enumerate(llm_raw_variants):
                    variants_output.append({
                        "id": str(asyncio.get_event_loop().time()) + f"-txt-{i}",
                        "title": f"Variante Texte {i+1}",
                        "content": variant_text,
                        "is_new": True 
                    })
                logger.info(f"LLM generated {len(variants_output)} TEXT variants.")
            else:
                logger.warning("LLM returned no TEXT variants.")
                variants_output = []

            self._restore_prompt_on_error(original_system_prompt) # Restore even on success
            return variants_output, final_prompt_str, estimated_tokens

        except Exception as e:
            logger.exception("Error during TEXT dialogue generation in DialogueGenerationService:")
            self._restore_prompt_on_error(original_system_prompt)
            return None, final_prompt_str if final_prompt_str else "Error during TEXT generation.", estimated_tokens

    # generate_interaction_variants supprimé - système obsolète remplacé par Unity JSON

    def _build_context_summary(self, context_selections: Dict[str, Any], user_instructions: str, max_tokens: int, no_limit: bool = False, field_configs: Optional[Dict[str, List[str]]] = None, organization_mode: Optional[str] = None) -> str:
        """
        Construit le résumé contextuel à partir des sélections et instructions utilisateur.
        Si no_limit est True, max_tokens est ignoré (valeur très haute transmise).
        
        Args:
            context_selections: Sélections de contexte GDD.
            user_instructions: Instructions utilisateur.
            max_tokens: Nombre maximum de tokens.
            no_limit: Si True, ignore la limite de tokens.
            field_configs: Configuration des champs à inclure (optionnel).
            organization_mode: Mode d'organisation du contexte (optionnel).
        """
        if no_limit:
            max_tokens = 999999
        # Log pour déboguer les personnages sélectionnés
        logger.debug(f"[_build_context_summary] context_selections reçu: {context_selections}")
        logger.debug(f"[_build_context_summary] characters dans context_selections: {context_selections.get('characters', [])}")
        
        # Utiliser build_context_with_custom_fields si field_configs est fourni
        if field_configs and hasattr(self.context_builder, 'build_context_with_custom_fields'):
            return self.context_builder.build_context_with_custom_fields(
                selected_elements=context_selections,
                scene_instruction=user_instructions,
                field_configs=field_configs,
                organization_mode=organization_mode or "default",
                max_tokens=max_tokens
            )
        else:
            return self.context_builder.build_context(context_selections, user_instructions, max_tokens=max_tokens)

    def _restore_prompt_on_error(self, original_system_prompt: Optional[str]):
        if original_system_prompt is not None:
            if hasattr(self.prompt_engine, 'system_prompt_template') and self.prompt_engine.system_prompt_template != original_system_prompt:
                self.prompt_engine.system_prompt_template = original_system_prompt
                logger.info("Original system prompt restored after operation or error.")
            elif not hasattr(self.prompt_engine, 'system_prompt_template'):
                 logger.warning("PromptEngine does not have system_prompt_template attribute during error recovery.")
        # else: logger.debug("No original system prompt to restore or no override was made.")

    def _extract_json_from_text(self, text: str) -> Optional[str]:
        """Extracts a JSON string from a text that might contain markdown code blocks.

        Args:
            text: The input text.

        Returns:
            The extracted JSON string, or None if not found.
        """
        # Regex to find JSON within markdown-style code blocks (```json ... ``` or ``` ... ```)
        # It captures the content within the innermost curly braces assuming it's the JSON object.
        match = re.search(r'```(?:json)?\s*({.*?})\s*```', text, re.DOTALL)
        if match:
            return match.group(1)
        
        # If no markdown block is found, try to find a JSON object directly
        # This is a simplified regex, might need to be more robust depending on expected LLM output
        match = re.search(r'({.*?})', text, re.DOTALL)
        if match:
            return match.group(1)
            
        return None

    # _parse_llm_response_to_interaction supprimé - système obsolète
    # _is_valid_id supprimé - système obsolète
    # _find_first_dialogue_text supprimé - système obsolète 

    def prepare_generation_preview(
        self,
        user_instructions: str,
        system_prompt_override: Optional[str],
        context_selections: Dict[str, Any], 
        max_context_tokens: int,
        structured_output: bool # Ajouté pour correspondre à la logique de build_prompt
    ) -> Tuple[Optional[str], int, Optional[str]]:
        """
        Prépare le contexte, construit le prompt final et estime les tokens SANS appeler le LLM.
        Utilisé pour mettre à jour l'UI avec une estimation avant la génération réelle.

        Retourne:
            Tuple (full_prompt, estimated_tokens, context_summary)
        """
        logger.debug("Début de prepare_generation_preview.")
        full_prompt: Optional[str] = None
        estimated_tokens: int = 0
        context_summary: Optional[str] = None # Initialisation
        # Copie pour pouvoir utiliser .pop() sans affecter l'original en dehors de cette portée
        current_context_selections = context_selections.copy()

        try:
            # 1. Construire le contexte avec ContextBuilder
            # Note: user_instructions est aussi passé à context_builder comme scene_instruction.
            context_summary = self.context_builder.build_context(
                selected_elements=current_context_selections, 
                scene_instruction=user_instructions,
                max_tokens=max_context_tokens
            )
            if context_summary is None:
                context_summary = "" # Assurer une chaîne vide
                logger.warning("ContextBuilder a retourné None pour le résumé du contexte. Utilisation d'une chaîne vide.")

            # 2. Extraire les informations de scène pour PromptEngine depuis current_context_selections
            scene_protagonists_dict = current_context_selections.pop("_scene_protagonists", {}) # Utiliser {} comme défaut
            scene_location_dict = current_context_selections.pop("_scene_location", {}) # Utiliser {} comme défaut

            # 3. Construire le prompt final avec PromptEngine
            original_system_prompt = None
            if system_prompt_override is not None and self.prompt_engine.system_prompt_template != system_prompt_override:
                original_system_prompt = self.prompt_engine.system_prompt_template
                self.prompt_engine.system_prompt_template = system_prompt_override
                logger.info("Utilisation d'un system_prompt_override pour la prévisualisation.")

            # Déterminer si nous générons une interaction structurée
            generate_interaction = structured_output and current_context_selections.get("generate_interaction", False)
            generation_params = {
                "structured_output": structured_output,
                "generate_interaction": generate_interaction
            }

            full_prompt, estimated_tokens = self.prompt_engine.build_prompt(
                user_specific_goal=user_instructions,
                scene_protagonists=scene_protagonists_dict,
                scene_location=scene_location_dict,
                context_summary=context_summary,
                generation_params=generation_params
            )

            if original_system_prompt is not None: # Restaurer l'original s'il a été surchargé
                self.prompt_engine.system_prompt_template = original_system_prompt

            if not full_prompt:
                logger.error("Impossible de construire le prompt final pour la prévisualisation.")
                return None, 0, context_summary

            logger.debug(f"Prévisualisation du prompt construite ({estimated_tokens} tokens estimés).")
            return full_prompt, estimated_tokens, context_summary

        except Exception as e:
            logger.exception("Erreur majeure lors de la préparation de la prévisualisation du dialogue.")
            return full_prompt, estimated_tokens, context_summary # Retourne ce qui a pu être généré 

    # parse_interaction_response supprimé - système obsolète 

    async def generate_structured_object_variants(self,
                                               llm_client: ILLMClient,
                                               k_variants: int,
                                               max_context_tokens_for_context_builder: int,
                                               user_instructions: str,
                                               system_prompt_override: Optional[str],
                                               context_selections: Dict[str, Any], # Doit contenir _scene_protagonists, _scene_location
                                               dialogue_structure_description: str, # Description de la structure pour le prompt
                                               target_response_model: Type[BaseModel], # Le modèle Pydantic pour la réponse LLM
                                               current_llm_model_identifier: str # Pour logging ou logique spécifique au modèle
                                               ) -> Tuple[Optional[List[BaseModel]], Optional[str], Optional[int]]:
        """
        Génère des variantes de dialogue structurées directement en objets Pydantic.
        Utilise un target_response_model pour que le LLM retourne des objets conformes.
        """
        logger.info(f"Service: Starting STRUCTURED OBJECT generation. Model: {current_llm_model_identifier}, K: {k_variants}, TargetModel: {target_response_model.__name__}")
        original_system_prompt = None
        final_prompt_str = None
        estimated_tokens = 0
        structured_objects_output: Optional[List[BaseModel]] = []
        
        # Copie pour pouvoir utiliser .pop() sans affecter l'original en dehors de cette portée
        current_context_selections = context_selections.copy()

        try:
            context_summary_text = self._build_context_summary(
                current_context_selections, user_instructions, max_context_tokens_for_context_builder # Utilise la copie
            )

            if system_prompt_override is not None and self.prompt_engine.system_prompt_template != system_prompt_override:
                original_system_prompt = self.prompt_engine.system_prompt_template
                self.prompt_engine.system_prompt_template = system_prompt_override
                logger.info(f"System prompt temporarily set for STRUCTURED OBJECT: '{system_prompt_override[:100]}...'")

            # Extraire les informations de scène pour PromptEngine depuis context_selections
            scene_protagonists_dict = current_context_selections.pop("_scene_protagonists", {})
            scene_location_dict = current_context_selections.pop("_scene_location", {})
            
            generation_params_for_prompt_build = {
                "structured_generation_request": True, # Indique une demande de sortie structurée
                "dialogue_structure_description": dialogue_structure_description
            }

            final_prompt_str, estimated_tokens = self.prompt_engine.build_prompt(
                context_summary=context_summary_text,
                user_specific_goal=user_instructions,
                scene_protagonists=scene_protagonists_dict,
                scene_location=scene_location_dict,
                generation_params=generation_params_for_prompt_build
            )
            logger.info(f"Final prompt for STRUCTURED OBJECT built. Estimated tokens: {estimated_tokens}. Length: {len(final_prompt_str)} chars.")

            if not final_prompt_str:
                logger.error("Failed to build prompt string (empty) for STRUCTURED OBJECT.")
                self._restore_prompt_on_error(original_system_prompt)
                return None, "Error: Prompt could not be built for STRUCTURED OBJECT.", 0

            if not llm_client:
                logger.error("LLM client is None, cannot generate STRUCTURED OBJECT variants.")
                self._restore_prompt_on_error(original_system_prompt)
                return None, final_prompt_str, estimated_tokens

            logger.debug(f"Calling LLM to generate {k_variants} STRUCTURED OBJECT variants using response_model: {target_response_model.__name__}.")
            
            # Appel LLM avec le response_model
            llm_pydantic_variants = await llm_client.generate_variants(
                prompt=final_prompt_str, 
                k=k_variants, 
                response_model=target_response_model # C'est la différence clé
            )
            
            if llm_pydantic_variants:
                structured_objects_output = llm_pydantic_variants # Directement les objets Pydantic
                logger.info(f"LLM generated {len(structured_objects_output)} STRUCTURED OBJECT variants.")
            else:
                logger.warning("LLM returned no STRUCTURED OBJECT variants.")
                structured_objects_output = []

            self._restore_prompt_on_error(original_system_prompt) # Restore even on success
            return structured_objects_output, final_prompt_str, estimated_tokens

        except Exception as e:
            logger.exception("Error during STRUCTURED OBJECT generation in DialogueGenerationService:")
            self._restore_prompt_on_error(original_system_prompt)
            return None, final_prompt_str if final_prompt_str else "Error during STRUCTURED OBJECT generation.", estimated_tokens
