import logging
import json
import re
from typing import Optional, Any, Tuple, List, Dict, Union
import uuid
from abc import ABC, abstractmethod
import asyncio

try:
    from ..context_builder import ContextBuilder
    from ..prompt_engine import PromptEngine
    from ..llm_client import ILLMClient # Utiliser l'interface
    from ..models.dialogue_structure.interaction import Interaction
    from ..models.dialogue_structure.dialogue_elements import (
        DialogueLineElement, PlayerChoicesBlockElement, CommandElement, PlayerChoiceOption
    )
    from ..services.interaction_service import InteractionService
except ImportError:
    # Support pour exécution directe ou tests unitaires hors contexte de package complet
    import sys
    from pathlib import Path
    current_dir = Path(__file__).resolve().parent.parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    from DialogueGenerator.context_builder import ContextBuilder
    from DialogueGenerator.prompt_engine import PromptEngine
    from DialogueGenerator.llm_client import ILLMClient
    from DialogueGenerator.models.dialogue_structure.interaction import Interaction
    from DialogueGenerator.models.dialogue_structure.dialogue_elements import (
        DialogueLineElement, PlayerChoicesBlockElement, CommandElement, PlayerChoiceOption
    )
    from DialogueGenerator.services.interaction_service import InteractionService

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

    @abstractmethod
    async def generate_interaction_variants(self,
                                            llm_client: ILLMClient,
                                            k_variants: int,
                                            max_context_tokens_for_context_builder: int,
                                            user_instructions: str, # Notamment la structure du dialogue
                                            system_prompt_override: Optional[str],
                                            context_selections: Dict[str, Any],
                                            current_llm_model_identifier: str
                                            ) -> Tuple[Optional[List[Interaction]], Optional[str], Optional[int]]:
        pass

class DialogueGenerationService(IDialogueGenerationService):
    def __init__(self, context_builder: ContextBuilder, prompt_engine: PromptEngine, interaction_service: InteractionService):
        """
        Initialise le service de génération de dialogues.
        
        Args:
            context_builder: Composant qui construit le contexte basé sur les sélections utilisateur
            prompt_engine: Composant qui construit les prompts pour le LLM
            interaction_service: Service pour gérer les interactions (optionnel)
        """
        self.context_builder = context_builder
        self.prompt_engine = prompt_engine
        self.interaction_service = interaction_service
        
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

        try:
            context_summary_text = self._build_context_summary(
                context_selections, user_instructions, max_context_tokens_for_context_builder
            )

            if system_prompt_override is not None and self.prompt_engine.system_prompt_template != system_prompt_override:
                original_system_prompt = self.prompt_engine.system_prompt_template
                self.prompt_engine.system_prompt_template = system_prompt_override
                logger.info(f"System prompt temporarily set for TEXT: '{system_prompt_override[:100]}...'" ) 

            generation_params_for_prompt_build = {
                "structured_generation_request": structured_output,
                "generate_interaction": False 
            }
            final_prompt_str, estimated_tokens = self.prompt_engine.build_prompt(
                context_summary=context_summary_text,
                user_specific_goal=user_instructions,
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

    async def generate_interaction_variants(self,
                                            llm_client: ILLMClient,
                                            k_variants: int,
                                            max_context_tokens_for_context_builder: int,
                                            user_instructions: str, # Devrait inclure la description de la structure
                                            system_prompt_override: Optional[str],
                                            context_selections: Dict[str, Any],
                                            current_llm_model_identifier: str
                                            ) -> Tuple[Optional[List[Interaction]], Optional[str], Optional[int]]:
        logger.info(f"Service: Starting INTERACTION generation. Model: {current_llm_model_identifier}, K: {k_variants}")
        original_system_prompt = None
        final_prompt_str = None
        estimated_tokens = 0
        interactions_output: Optional[List[Interaction]] = []

        try:
            # context_selections déjà enrichi avec _scene_protagonists, _scene_location, generate_interaction=True
            # et generation_settings.dialogue_structure par GenerationPanel
            context_summary_text = self._build_context_summary(
                context_selections, user_instructions, max_context_tokens_for_context_builder
            )

            if system_prompt_override is not None and self.prompt_engine.system_prompt_template != system_prompt_override:
                original_system_prompt = self.prompt_engine.system_prompt_template
                self.prompt_engine.system_prompt_template = system_prompt_override
                logger.info(f"System prompt temporarily set for INTERACTION: '{system_prompt_override[:100]}...'" )
            
            dialogue_structure_description = context_selections.get("generation_settings", {}).get("dialogue_structure", "")

            generation_params_for_prompt_build = {
                "structured_generation_request": True, 
                "generate_interaction": True,
                "dialogue_structure_description": dialogue_structure_description
            }

            final_prompt_str, estimated_tokens = self.prompt_engine.build_prompt(
                context_summary=context_summary_text,
                user_specific_goal=user_instructions, 
                generation_params=generation_params_for_prompt_build
            )
            logger.info(f"Final prompt for INTERACTION built. Estimated tokens: {estimated_tokens}. Length: {len(final_prompt_str)} chars.")

            if not final_prompt_str:
                logger.error("Failed to build prompt string (empty) for INTERACTION.")
                self._restore_prompt_on_error(original_system_prompt)
                return None, "Error: Prompt could not be built for INTERACTION.", 0

            if not llm_client:
                logger.error("LLM client is None, cannot generate INTERACTION variants.")
                self._restore_prompt_on_error(original_system_prompt)
                return None, final_prompt_str, estimated_tokens

            logger.debug(f"Calling LLM to generate {k_variants} INTERACTION variants (raw JSON strings).")
            llm_raw_json_variants = await llm_client.generate_variants(prompt=final_prompt_str, k=k_variants)

            if llm_raw_json_variants:
                interactions_output = []
                for i, raw_json_interaction_str in enumerate(llm_raw_json_variants):
                    try:
                        interaction_obj = self.interaction_service.parse_llm_output_to_interaction(raw_json_interaction_str)
                        if interaction_obj:
                            # Titre temporaire, pourrait être amélioré ou généré par le LLM
                            interaction_obj.title = f"Generated Interaction {i+1} (ID: ...{str(interaction_obj.interaction_id)[-6:]})"
                            interactions_output.append(interaction_obj)
                        else:
                            logger.warning(f"Failed to parse LLM output to Interaction for variant {i+1}. Output: {raw_json_interaction_str[:150]}...")
                    except Exception as parse_err:
                        logger.error(f"Error parsing LLM variant {i+1} into Interaction: {parse_err}. Raw: {raw_json_interaction_str[:250]}...")
                logger.info(f"LLM generated and parsed {len(interactions_output)} INTERACTION objects from {len(llm_raw_json_variants)} raw outputs.")
            else:
                logger.warning("LLM returned no INTERACTION variants (raw JSON strings).")
                interactions_output = []

            self._restore_prompt_on_error(original_system_prompt) # Restore even on success
            return interactions_output, final_prompt_str, estimated_tokens

        except Exception as e:
            logger.exception("Error during INTERACTION generation in DialogueGenerationService:")
            self._restore_prompt_on_error(original_system_prompt)
            return None, final_prompt_str if final_prompt_str else "Error during INTERACTION generation.", estimated_tokens

    def _build_context_summary(self, context_selections: Dict[str, Any], user_instructions: str, max_tokens: int) -> str:
        # Cette méthode encapsule la logique de construction du résumé du contexte.
        # Elle utilise context_selections qui devrait contenir _scene_protagonists et _scene_location si applicables.
        # user_instructions est passé à build_context comme scene_instruction.
        
        # Note: La construction de `scene_instruction` à partir de `_scene_protagonists` et `_scene_location`
        # a été retirée d'ici car `GenerationPanel` prépare déjà `context_selections` avec ces informations.
        # Le `ContextBuilder.build_context` doit utiliser `scene_instruction` (qui est `user_instructions` ici)
        # et les `selected_elements` (qui est `context_selections` ici) pour former le contexte.
        
        context_summary_text = self.context_builder.build_context(
            selected_elements=context_selections, 
            scene_instruction=user_instructions, 
            max_tokens=max_tokens,
        )
        logger.debug(f"Context summary built by service: {len(context_summary_text)} chars, first 100: {context_summary_text[:100]}")
        return context_summary_text

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

    def _parse_llm_response_to_interaction(self, response_text: str) -> Optional[Interaction]:
        """
        Parse la réponse du LLM pour extraire et créer un objet Interaction.
        Utilise interaction_service pour s'assurer que l'ID est robuste.
        """
        try:
            json_str = self._extract_json_from_text(response_text)
            if not json_str:
                logger.error("Impossible d'extraire du JSON de la réponse pour _parse_llm_response_to_interaction.")
                return None
                
            interaction_data = json.loads(json_str) # Renommé de data à interaction_data pour clarté

            # Récupérer le titre ou en générer un à partir du contenu
            title = interaction_data.get("title", "")
            if not title:
                first_dialogue = self._find_first_dialogue_text(interaction_data)
                if first_dialogue:
                    title = first_dialogue[:30] + "..." if len(first_dialogue) > 30 else first_dialogue
                else:
                    title = "Nouvelle interaction"
                interaction_data["title"] = title  # Mettre à jour le titre dans les données
            
            # Traitement de l'ID d'interaction
            current_interaction_id = interaction_data.get("interaction_id", "")
            # prefix = None # Le préfixe n'est plus utilisé ici pour garantir un ID UUID pur
            
            final_interaction_id = current_interaction_id

            if self.interaction_service:
                if not current_interaction_id or not self._is_valid_id(current_interaction_id):
                    # On ne dérive plus le préfixe du titre ici pour obtenir un UUID pur.
                    # Si un préfixe était désiré, il devrait être géré plus haut ou passé différemment.
                    final_interaction_id = self.interaction_service.generate_interaction_id(prefix=None)
                    logger.info(f"Généré nouvel ID UUID pur via _parse_llm: {final_interaction_id} (ancien: '{current_interaction_id}', titre: '{title}')")
                else:
                    logger.info(f"Utilisation de l'ID existant valide via _parse_llm: {current_interaction_id}")
            else:
                # Sans service d'interaction, on garde l'ID fourni ou on génère un ID basique
                if not current_interaction_id:
                    if title:
                        cleaned_title = re.sub(r'[^a-zA-Z0-9]', '_', title.lower())
                        final_interaction_id = cleaned_title[:50]
                    else:
                        import time
                        final_interaction_id = f"interaction_{int(time.time())}"
                    logger.warning(f"Généré ID basique (non-robuste) via _parse_llm: {final_interaction_id} - InteractionService non disponible")
            
            # Mettre à jour l'ID dans le dictionnaire avant de créer l'objet
            interaction_data["interaction_id"] = final_interaction_id
            
            # Créer l'objet Interaction en utilisant Interaction.from_dict pour la cohérence
            # si tous les champs nécessaires sont dans interaction_data et au bon format.
            # Sinon, continuer avec l'instanciation manuelle.
            # Pour l'instant, on s'assure que `from_dict` est utilisé si possible, sinon construction manuelle.
            
            # Assurons-nous que les éléments sont bien parsés et ajoutés.
            # L'implémentation précédente de _parse_llm_response_to_interaction construisait l'objet Interaction
            # et ajoutait les éléments manuellement. Il faut conserver cette logique si from_dict ne gère pas tout.
            # Interaction.from_dict DEVRAIT gérer la création des éléments si le JSON est structuré correctement.

            # Option 1: Utiliser from_dict si la structure de interaction_data correspond parfaitement
            # return Interaction.from_dict(interaction_data) 
            
            # Option 2: Construction manuelle (comme c'était fait avant, mais avec le nouvel ID)
            # Cela garantit que la logique de gestion des éléments est préservée.
            new_interaction = Interaction(
                interaction_id=final_interaction_id, # Utilise l'ID finalisé
                title=interaction_data.get("title", ""), # Utilise le titre mis à jour
                header_tags=interaction_data.get("header_tags", []),
                header_commands=interaction_data.get("header_commands", []),
                next_interaction_id_if_no_choices=interaction_data.get("next_interaction_id_if_no_choices")
            )
            
            for element_data in interaction_data.get("elements", []):
                element_type = element_data.get("element_type")
                element = None
                if element_type == "dialogue_line":
                    element = DialogueLineElement.model_validate(element_data)
                elif element_type == "command":
                    element = CommandElement.model_validate(element_data)
                elif element_type == "player_choices_block":
                    element = PlayerChoicesBlockElement.model_validate(element_data)
                
                if element:
                    new_interaction.elements.append(element)
                else:
                    logger.warning(f"Type d'élément inconnu ou données invalides dans _parse_llm: {element_type}")

            logger.info(f"Interaction (re)parsée avec ID: {new_interaction.interaction_id}, Titre: {new_interaction.title}")
            return new_interaction
            
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de décodage JSON dans _parse_llm: {str(e)}. Réponse: {response_text[:200]}...")
            return None
        except Exception as e:
            logger.exception(f"Erreur inattendue dans _parse_llm: {str(e)}")
            return None

    def _is_valid_id(self, interaction_id: str) -> bool:
        """
        Vérifie si un ID d'interaction est dans un format valide/robuste.
        
        Args:
            interaction_id: L'ID à vérifier
            
        Returns:
            True si l'ID est au format UUID ou prefix_UUID, False sinon
        """
        # Format UUID standard
        try:
            uuid.UUID(interaction_id)
            return True
        except ValueError:
            pass
        
        # Format prefix_UUID
        if '_' in interaction_id:
            parts = interaction_id.split('_')
            if len(parts) >= 2:
                try:
                    # Essayer de parser la dernière partie comme UUID
                    uuid.UUID(parts[-1])
                    return True
                except ValueError:
                    pass
        
        return False

    def _find_first_dialogue_text(self, data: Dict) -> Optional[str]:
        """
        Trouve le premier texte de dialogue dans les données pour générer un titre.
        
        Args:
            data: Les données de l'interaction
            
        Returns:
            Le premier texte de dialogue trouvé ou None
        """
        try:
            if "elements" in data:
                for element in data["elements"]:
                    if element.get("element_type") == "dialogue_line" and "text" in element:
                        return element["text"]
        except Exception as e:
            logger.warning(f"Erreur dans _find_first_dialogue_text: {e}")
            pass
        return None 

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

        try:
            # 1. Construire le contexte avec ContextBuilder
            # Note: user_instructions est aussi passé à context_builder comme scene_instruction.
            context_summary = self.context_builder.build_context(
                selected_elements=context_selections, 
                scene_instruction=user_instructions,
                max_tokens=max_context_tokens
            )
            if context_summary is None:
                context_summary = "" # Assurer une chaîne vide
                logger.warning("ContextBuilder a retourné None pour le résumé du contexte. Utilisation d'une chaîne vide.")

            # 2. Extraire les informations de scène pour PromptEngine depuis context_selections
            scene_protagonists_dict = context_selections.pop("_scene_protagonists", {}) # Utiliser {} comme défaut
            scene_location_dict = context_selections.pop("_scene_location", {}) # Utiliser {} comme défaut

            # 3. Construire le prompt final avec PromptEngine
            original_system_prompt = None
            if system_prompt_override is not None and self.prompt_engine.system_prompt_template != system_prompt_override:
                original_system_prompt = self.prompt_engine.system_prompt_template
                self.prompt_engine.system_prompt_template = system_prompt_override
                logger.info("Utilisation d'un system_prompt_override pour la prévisualisation.")

            # Déterminer si nous générons une interaction structurée
            generate_interaction = structured_output and context_selections.get("generate_interaction", False)
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

    def parse_interaction_response(self, raw_response: str) -> Optional[Interaction]:
        """
        Analyse la réponse du LLM pour créer un objet Interaction.
        NOTE: Cette méthode contient une logique similaire à _parse_llm_response_to_interaction.
        Elle devrait être révisée ou supprimée si _parse_llm_response_to_interaction est la méthode principale.
        Pour l'instant, on la laisse pour ne pas casser d'éventuels appels existants non identifiés,
        mais la logique robuste d'ID est maintenant dans _parse_llm_response_to_interaction.
        """
        try:
            # Nettoyer la réponse pour extraire seulement le JSON
            json_str = self._extract_json_from_text(raw_response)
            if not json_str:
                logger.error("Impossible d'extraire du JSON de la réponse.")
                return None
                
            data = json.loads(json_str)
            
            if not isinstance(data, dict):
                logger.error(f"Les données extraites ne sont pas un dictionnaire: {type(data)}")
                return None
                
            # ID et Titre gérés comme dans _parse_llm_response_to_interaction (simplifié ici)
            title = data.get("title", "")
            if not title:
                first_dialogue = self._find_first_dialogue_text(data)
                title = (first_dialogue[:30] + "..." if len(first_dialogue) > 30 else first_dialogue) if first_dialogue else "Nouvelle interaction"
                data["title"] = title

            interaction_id = data.get("interaction_id", "")
            if not interaction_id: # Générer un ID basique si absent
                interaction_id = title.lower().replace(" ", "_")[:30] + f"_{uuid.uuid4().hex[:6]}"
                data["interaction_id"] = interaction_id

            # MODIFIÉ: Utilisation de model_validate pour créer l'instance d'Interaction
            # Cela suppose que la structure de `data` correspond au modèle Interaction Pydantic
            # y compris la gestion des `elements` par discrimination.
            return Interaction.model_validate(data)
            
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de décodage JSON dans parse_interaction_response: {str(e)}. Réponse: {raw_response[:200]}...")
            return None
        except Exception as e:
            logger.exception(f"Erreur inattendue dans parse_interaction_response: {str(e)}")
            return None 