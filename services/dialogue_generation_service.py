import logging
import json
import re
from typing import Optional, Any, Tuple, List, Dict, Union

try:
    from ..context_builder import ContextBuilder
    from ..prompt_engine import PromptEngine
    from ..llm_client import ILLMClient # Utiliser l'interface
    from ..models.dialogue_structure.interaction import Interaction
    from ..models.dialogue_structure.dialogue_elements import (
        DialogueLineElement, PlayerChoicesBlockElement, CommandElement, PlayerChoiceOption
    )
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

logger = logging.getLogger(__name__)

class DialogueGenerationService:
    def __init__(self, context_builder: ContextBuilder, prompt_engine: PromptEngine):
        self.context_builder = context_builder
        self.prompt_engine = prompt_engine

    async def generate_dialogue_variants(
        self,
        llm_client: ILLMClient, # Le client LLM est passé à chaque appel
        k_variants: int,
        max_context_tokens_for_context_builder: int, # Renommé pour clarté
        structured_output: bool,
        user_instructions: str, # C'est le user_specific_goal pour PromptEngine
        system_prompt_override: Optional[str],
        context_selections: Dict[str, Any], # Utilisé par ContextBuilder pour générer context_summary
        # Les paramètres suivants sont extraits de context_selections ou sont implicites
        # pour construire scene_protagonists et scene_location pour PromptEngine
        current_llm_model_identifier: Optional[str] # Pour info, pas directement utilisé ici car le client est déjà configuré
    ) -> Tuple[Optional[List[str]], Optional[str], Optional[int]]:
        """
        Génère des variantes de dialogue en utilisant le client LLM.
        """ # Docstring abrégée pour la concision du diff
        logger.info(f"Début de la génération de dialogue via DialogueGenerationService. Modèle: {current_llm_model_identifier}")
        
        full_prompt = None # S'assurer qu'il est défini en cas d'erreur précoce
        estimated_tokens = 0

        try:
            # 1. Construire le contexte avec ContextBuilder
            # Note: user_instructions est aussi passé à context_builder comme scene_instruction.
            context_summary = self.context_builder.build_context(
                selected_elements=context_selections, 
                scene_instruction=user_instructions, # L'instruction utilisateur peut aussi guider le ContextBuilder
                max_tokens=max_context_tokens_for_context_builder
            )
            if context_summary is None: # Si build_context retourne None (par exemple, si context_selections est vide et que c'est géré ainsi)
                context_summary = "" # Assurer une chaîne vide au lieu de None pour PromptEngine
                logger.warning("ContextBuilder a retourné None pour le résumé du contexte. Utilisation d'une chaîne vide.")

            # 2. Extraire les informations de scène pour PromptEngine depuis context_selections
            # Les clés exactes dépendent de ce que _get_current_context_selections() de MainWindow retourne.
            # On suppose qu'il y a des clés comme 'personnage_a', 'personnage_b', 'lieu', 'sous_lieu'.
            # Ces clés doivent correspondre à celles utilisées dans le dictionnaire retourné par 
            # MainWindow._get_current_context_selections() et SceneSelectionWidget.get_selected()
            
            # Tentative d'extraction des noms de personnages et lieux depuis context_selections
            # Normalement, SceneSelectionWidget s'occupe de la sélection directe de ceux-ci.
            # context_selections est un dict avec des listes d'objets GDD, PAS les sélections directes des comboboxes.
            # IL FAUT AJOUTER les personnages A/B et le lieu/sous-lieu comme arguments séparés 
            # ou les passer dans un dictionnaire dédié si on ne veut pas modifier la signature de generate_dialogue_variants.
            
            # Pour l'instant, on les suppose absents de context_selections et on les passe à None
            # Ceci est une simplification et pourrait nécessiter un ajustement de l'appelant (GenerationPanelBase)
            # pour passer char_a_name, char_b_name, scene_region_name, scene_sub_location_name séparément.
            # OU, mieux, les inclure dans context_selections AVEC des clés spécifiques.
            
            # Solution actuelle: on attend de l'appelant (GenerationPanelBase) qu'il peuple context_selections
            # avec des clés spécifiques pour les protagonistes et le lieu, par exemple :
            # context_selections["_scene_protagonists"] = {"personnage_a": "NomA", ...}
            # context_selections["_scene_location"] = {"lieu": "NomLieu", ...}
            
            scene_protagonists_dict = context_selections.pop("_scene_protagonists", None)
            scene_location_dict = context_selections.pop("_scene_location", None)

            # 3. Construire le prompt final avec PromptEngine
            # Surcharger le prompt système si un override est fourni
            original_system_prompt = None
            if system_prompt_override is not None and self.prompt_engine.system_prompt_template != system_prompt_override:
                original_system_prompt = self.prompt_engine.system_prompt_template
                self.prompt_engine.system_prompt_template = system_prompt_override
                logger.info("Utilisation d'un system_prompt_override.")

            full_prompt, estimated_tokens = self.prompt_engine.build_prompt(
                user_specific_goal=user_instructions, # C'est l'instruction utilisateur principale
                scene_protagonists=scene_protagonists_dict,
                scene_location=scene_location_dict,
                context_summary=context_summary,  # Le contexte généré par ContextBuilder
                generation_params={"structured_output": structured_output} # Exemple de param de génération
            )

            if original_system_prompt is not None: # Restaurer l'original s'il a été surchargé
                self.prompt_engine.system_prompt_template = original_system_prompt

            if not full_prompt:
                logger.error("DialogueGenerationService: Impossible de construire le prompt final avec PromptEngine.")
                return None, None, None

            logger.info(f"Prompt final construit ({estimated_tokens} tokens estimés). Appel de llm_client.generate_variants (k={k_variants}).")
            if structured_output:
                logger.info("Sortie structurée (JSON) demandée au LLM (via le prompt).")

            # 4. Appeler le client LLM
            # L'argument structured_output a été retiré car non géré par l'interface ILLMClient
            # La demande de sortie structurée est gérée au niveau du prompt.
            variants = await llm_client.generate_variants(full_prompt, k_variants)

            if variants:
                logger.info(f"{len(variants)} variante(s) reçue(s) du LLM.")
                return variants, full_prompt, estimated_tokens
            else:
                logger.warning("DialogueGenerationService: Le LLM n'a retourné aucune variante.")
                return [], full_prompt, estimated_tokens

        except Exception as e:
            logger.exception("DialogueGenerationService: Erreur majeure lors de la génération de dialogue")
            return None, full_prompt, estimated_tokens # Retourne le prompt s'il a pu être généré, pour debug 

    async def generate_interaction_variants(
        self,
        llm_client: ILLMClient,
        k_variants: int = 1,
        max_context_tokens_for_context_builder: int = 4000,
        user_instructions: str = "",
        system_prompt_override: Optional[str] = None,
        context_selections: Optional[Dict[str, Any]] = None,
        current_llm_model_identifier: Optional[str] = None
    ) -> Tuple[Optional[List[Interaction]], Optional[str], Optional[int]]:
        """
        Génère des variantes d'interactions structurées en utilisant le client LLM.
        
        Cette méthode est similaire à generate_dialogue_variants, mais elle est spécifiquement
        conçue pour générer des objets Interaction structurés plutôt que du texte brut.
        
        Args:
            llm_client: Le client LLM à utiliser
            k_variants: Nombre de variantes à générer
            max_context_tokens_for_context_builder: Limite de tokens pour le contexte
            user_instructions: Instructions de l'utilisateur pour la génération
            system_prompt_override: Prompt système personnalisé (optionnel)
            context_selections: Sélections de contexte (personnages, lieux, etc.)
            current_llm_model_identifier: Identifiant du modèle LLM (pour debug)
            
        Returns:
            Tuple contenant:
            - Liste d'objets Interaction générés
            - Prompt complet utilisé
            - Nombre estimé de tokens
        """
        logger.info(f"Début de la génération d'interactions structurées. Modèle: {current_llm_model_identifier}")
        
        if context_selections is None:
            context_selections = {}
            
        full_prompt = None
        estimated_tokens = 0
        
        try:
            # 1. Construire le contexte
            context_summary = self.context_builder.build_context(
                selected_elements=context_selections,
                scene_instruction=user_instructions,
                max_tokens=max_context_tokens_for_context_builder
            )
            if context_summary is None:
                context_summary = ""
                logger.warning("ContextBuilder a retourné None pour le résumé du contexte. Utilisation d'une chaîne vide.")
                
            # 2. Extraire les informations de scène
            scene_protagonists_dict = context_selections.pop("_scene_protagonists", None)
            scene_location_dict = context_selections.pop("_scene_location", None)
            
            # 3. Construire le prompt avec le format JSON pour Interaction
            original_system_prompt = None
            if system_prompt_override is not None and self.prompt_engine.system_prompt_template != system_prompt_override:
                original_system_prompt = self.prompt_engine.system_prompt_template
                self.prompt_engine.system_prompt_template = system_prompt_override
                logger.info("Utilisation d'un system_prompt_override pour la génération d'interactions.")
                
            # Utiliser le paramètre generate_interaction pour utiliser le prompt spécifique aux interactions
            generation_params = {"generate_interaction": True}
            
            full_prompt, estimated_tokens = self.prompt_engine.build_prompt(
                user_specific_goal=user_instructions,
                scene_protagonists=scene_protagonists_dict,
                scene_location=scene_location_dict,
                context_summary=context_summary,
                generation_params=generation_params
            )
            
            if original_system_prompt is not None:
                self.prompt_engine.system_prompt_template = original_system_prompt
                
            if not full_prompt:
                logger.error("Impossible de construire le prompt pour la génération d'interactions.")
                return None, None, None
                
            logger.info(f"Prompt final pour interactions construit ({estimated_tokens} tokens). Appel de llm_client.generate_variants (k={k_variants}).")
            
            # 4. Appeler le LLM
            raw_variants = await llm_client.generate_variants(full_prompt, k_variants)
            
            if not raw_variants:
                logger.warning("Le LLM n'a retourné aucune variante d'interaction.")
                return [], full_prompt, estimated_tokens
                
            # 5. Parser les réponses JSON en objets Interaction
            interaction_variants = []
            for i, raw_variant in enumerate(raw_variants):
                try:
                    interaction = self._parse_llm_response_to_interaction(raw_variant)
                    if interaction:
                        interaction_variants.append(interaction)
                    else:
                        logger.warning(f"La variante {i+1} n'a pas pu être convertie en Interaction.")
                except Exception as e:
                    logger.exception(f"Erreur lors du parsing de la variante {i+1}: {str(e)}")
            
            logger.info(f"{len(interaction_variants)}/{len(raw_variants)} variantes d'interaction générées avec succès.")
            return interaction_variants, full_prompt, estimated_tokens
            
        except Exception as e:
            logger.exception("Erreur majeure lors de la génération d'interactions structurées")
            return None, full_prompt, estimated_tokens
            
    def _parse_llm_response_to_interaction(self, response_text: str) -> Optional[Interaction]:
        """
        Parse la réponse du LLM pour extraire et créer un objet Interaction.
        
        Args:
            response_text: Réponse textuelle du LLM contenant la structure JSON
            
        Returns:
            Un objet Interaction si le parsing réussit, None sinon
        """
        try:
            # Nettoyer la réponse pour extraire le JSON
            # Rechercher des délimiteurs de code JSON
            json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', response_text, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(1)
            else:
                # Si pas de délimiteurs, essayer de prendre tout le texte
                json_str = response_text.strip()
                
            # Parser le JSON
            interaction_data = json.loads(json_str)
            
            # Créer l'Interaction à partir des données JSON
            interaction_id = interaction_data.get("interaction_id", "")
            title = interaction_data.get("title", "")
            header_tags = interaction_data.get("header_tags", [])
            header_commands = interaction_data.get("header_commands", [])
            next_interaction_id_if_no_choices = interaction_data.get("next_interaction_id_if_no_choices")
            
            # Créer l'objet Interaction
            interaction = Interaction(
                interaction_id=interaction_id,
                title=title,
                header_tags=header_tags,
                header_commands=header_commands,
                next_interaction_id_if_no_choices=next_interaction_id_if_no_choices
            )
            
            # Ajouter les éléments
            for element_data in interaction_data.get("elements", []):
                element_type = element_data.get("element_type")
                
                if element_type == "dialogue_line":
                    element = DialogueLineElement(
                        text=element_data.get("text", ""),
                        speaker=element_data.get("speaker"),
                        tags=element_data.get("tags", []),
                        pre_line_commands=element_data.get("pre_line_commands", []),
                        post_line_commands=element_data.get("post_line_commands", [])
                    )
                    interaction.elements.append(element)
                    
                elif element_type == "command":
                    element = CommandElement(
                        command_string=element_data.get("command_string", "")
                    )
                    interaction.elements.append(element)
                    
                elif element_type == "player_choices_block":
                    choices_block = PlayerChoicesBlockElement()
                    
                    for choice_data in element_data.get("choices", []):
                        choice = PlayerChoiceOption(
                            text=choice_data.get("text", ""),
                            next_interaction_id=choice_data.get("next_interaction_id", ""),
                            condition=choice_data.get("condition"),
                            actions=choice_data.get("actions", []),
                            tags=choice_data.get("tags", [])
                        )
                        choices_block.choices.append(choice)
                        
                    interaction.elements.append(choices_block)
            
            return interaction
            
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de décodage JSON: {str(e)}")
            logger.debug(f"Réponse problématique: {response_text}")
            return None
        except Exception as e:
            logger.exception(f"Erreur inattendue lors du parsing de l'interaction: {str(e)}")
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
        
        Args:
            raw_response: La réponse textuelle du LLM
            
        Returns:
            L'objet Interaction créé ou None en cas d'échec
        """
        try:
            # Nettoyer la réponse pour extraire seulement le JSON
            json_str = self._extract_json_from_text(raw_response)
            if not json_str:
                logger.error("Impossible d'extraire du JSON de la réponse.")
                return None
                
            data = json.loads(json_str)
            
            # Vérifier si nous avons les éléments essentiels
            if not isinstance(data, dict):
                logger.error(f"Les données extraites ne sont pas un dictionnaire: {type(data)}")
                return None
                
            # S'assurer que nous avons un titre
            if "title" not in data and "interaction_id" in data:
                # Générer un titre basé sur l'ID si absent
                data["title"] = f"Interaction {data['interaction_id'][:8]}"
            elif "title" not in data:
                # Générer un titre basé sur le contenu
                first_dialogue = self._find_first_dialogue_text(data)
                if first_dialogue:
                    data["title"] = first_dialogue[:30] + "..." if len(first_dialogue) > 30 else first_dialogue
                else:
                    data["title"] = "Nouvelle interaction"
            
            # Créer l'objet Interaction
            interaction = Interaction.from_dict(data)
            logger.info(f"Interaction créée avec succès. ID: {interaction.interaction_id}, titre: {interaction.title}")
            return interaction
            
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de décodage JSON: {e}")
            logger.debug(f"Contenu qui a causé l'erreur: {raw_response[:200]}...")
            return None
        except Exception as e:
            logger.exception(f"Erreur lors de l'analyse de la réponse d'interaction: {e}")
            return None
            
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
        except:
            pass
        return None 