# DialogueGenerator/context_builder.py
import json
from pathlib import Path
import logging
import re
import os
from typing import List, Optional, Dict
import traceback

try:
    import tiktoken
except ImportError:
    tiktoken = None

from models.dialogue_structure.interaction import Interaction
from models.dialogue_structure.dialogue_elements import DialogueLineElement, PlayerChoicesBlockElement, PlayerChoiceOption

logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') # Déjà configuré dans main_app

CONTEXT_BUILDER_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT_DIR = CONTEXT_BUILDER_DIR.parent
DEFAULT_CONFIG_FILE = CONTEXT_BUILDER_DIR / "context_config.json"

class ContextBuilder:
    def __init__(self, config_file_path: Path = DEFAULT_CONFIG_FILE):
        self.gdd_data = {}
        self.characters = []
        self.locations = []
        self.items = []
        self.species = []
        self.communities = []
        self.narrative_structures = []
        self.macro_structure = []
        self.micro_structure = []
        self.dialogues_examples = []
        self.vision_data = None
        self.quests = []
        self.context_config = self._load_context_config(config_file_path)
        self.previous_dialogue_context: Optional[List[Interaction]] = None

        if tiktoken:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        else:
            self.tokenizer = None
            logger.warning("tiktoken n'est pas installé. La gestion précise du nombre de tokens sera désactivée.")

    def _load_context_config(self, config_file: Path) -> dict:
        """Charge la configuration de priorisation depuis un fichier JSON."""
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                logger.info(f"Configuration de contexte chargée depuis {config_file}")
                return config
            except json.JSONDecodeError as e:
                logger.error(f"Erreur de décodage JSON pour le fichier de configuration {config_file}: {e}")
            except Exception as e:
                logger.error(f"Erreur inattendue lors du chargement de {config_file}: {e}")
        else:
            logger.warning(f"Fichier de configuration {config_file} non trouvé. Utilisation d'une configuration vide.")
        return {} # Retourne un dict vide si le chargement échoue ou si le fichier n'existe pas

    def _count_tokens(self, text: str) -> int:
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            return len(text.split())

    def load_gdd_files(self): # Suppression des arguments gdd_base_path_str et import_base_path_str
        """
        Charge les fichiers JSON du GDD depuis les chemins relatifs au projet.
        Se concentre sur les fichiers non-Mini dans GDD/categories/
        et charge également Vision.json depuis import/Bible_Narrative/
        """
        gdd_base_path = PROJECT_ROOT_DIR / "GDD"
        categories_path = gdd_base_path / "categories"
        import_base_path = PROJECT_ROOT_DIR / "import"

        logger.info(f"Début du chargement des données du GDD depuis {categories_path} et {import_base_path}.")

        vision_file_path = import_base_path / "Bible_Narrative" / "Vision.json"
        if vision_file_path.exists() and vision_file_path.is_file():
            try:
                with open(vision_file_path, "r", encoding="utf-8") as f:
                    self.vision_data = json.load(f)
                logger.info(f"Fichier {vision_file_path.name} chargé avec succès.")
            except json.JSONDecodeError as e:
                logger.error(f"Erreur de décodage JSON pour {vision_file_path.name}: {e}")
            except Exception as e:
                logger.error(f"Erreur inattendue lors du chargement de {vision_file_path.name}: {e}")
        else:
            logger.warning(f"Fichier {vision_file_path.name} non trouvé ou n'est pas un fichier.")

        categories_to_load = {
            "personnages": {"attr": "characters", "key": "personnages", "type": list},
            "lieux": {"attr": "locations", "key": "lieux", "type": list},
            "objets": {"attr": "items", "key": "objets", "type": list},
            "especes": {"attr": "species", "key": "especes", "type": list},
            "communautes": {"attr": "communities", "key": "communautes", "type": list},
            "dialogues": {"attr": "dialogues_examples", "key": "dialogues", "type": list},
            "structure_narrative": {"attr": "narrative_structures", "key": "structure_narrative", "type": list}, 
            "structure_macro": {"attr": "macro_structure", "key": "structure_macro", "type": list},
            "structure_micro": {"attr": "micro_structure", "key": "structure_micro", "type": list},
            "quetes": {"attr": "quests", "key": "quetes", "type": list}
        }

        for file_key, load_config_item in categories_to_load.items():
            attribute_name = load_config_item["attr"]
            json_main_key = load_config_item["key"]
            expected_type = load_config_item["type"]
            
            file_path = categories_path / f"{file_key}.json"
            default_value = [] if expected_type == list else {}
            setattr(self, attribute_name, default_value)

            if file_path.exists() and file_path.is_file():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    data_to_set = None
                    if isinstance(data, dict) and json_main_key in data:
                        data_to_set = data[json_main_key]
                    elif isinstance(data, dict) and expected_type == dict:
                        data_to_set = data
                    elif isinstance(data, list) and expected_type == list:
                         data_to_set = data
                    elif file_key in ["structure_macro", "structure_micro"] and isinstance(data, dict):
                        setattr(self, attribute_name, data)
                        logger.info(f"Fichier {file_path.name} chargé comme objet unique.")
                        continue
                    
                    if data_to_set is not None:
                        if isinstance(data_to_set, expected_type):
                            setattr(self, attribute_name, data_to_set)
                            count = len(data_to_set) if expected_type == list else 1
                            logger.info(f"Fichier {file_path.name} chargé. {count} élément(s) pour '{json_main_key}'.")
                        else:
                            logger.warning(f"Type de données inattendu pour {json_main_key} dans {file_path.name}. Attendu {expected_type}, obtenu {type(data_to_set)}.")
                    else:
                        logger.warning(f"Contenu inattendu dans {file_path.name}. Clé '{json_main_key}' non trouvée ou format non géré.")

                except json.JSONDecodeError as e:
                    logger.error(f"Erreur de décodage JSON pour {file_path.name}: {e}")
                except Exception as e:
                    logger.error(f"Erreur inattendue lors du chargement de {file_path.name}: {e}")
            else:
                logger.warning(f"Fichier {file_path.name} non trouvé dans {categories_path}. L'attribut '{attribute_name}' restera à sa valeur par défaut.")
        
        logger.info("Chargement des fichiers GDD terminé.")

    def get_characters_names(self):
        if not self.characters: return []
        return [char.get("Nom") for char in self.characters if isinstance(char, dict) and char.get("Nom")]

    def get_locations_names(self):
        if not self.locations: return []
        return [loc.get("Nom") for loc in self.locations if isinstance(loc, dict) and loc.get("Nom")]

    def get_items_names(self):
        if not self.items: return []
        return [item.get("Nom") for item in self.items if isinstance(item, dict) and item.get("Nom")]

    def get_species_names(self):
        if not self.species: return []
        return [s.get("Nom") for s in self.species if isinstance(s, dict) and s.get("Nom")]

    def get_communities_names(self):
        if not self.communities: return []
        return [c.get("Nom") for c in self.communities if isinstance(c, dict) and c.get("Nom")]

    def get_quests_names(self):
        if not hasattr(self, 'quests') or not self.quests: return []
        return [q.get("Nom") for q in self.quests if isinstance(q, dict) and q.get("Nom")]

    def get_narrative_structures(self):
        return self.narrative_structures

    def get_macro_structure(self):
        return self.macro_structure[0] if self.macro_structure and isinstance(self.macro_structure, list) and self.macro_structure else self.macro_structure if isinstance(self.macro_structure, dict) else None

    def get_micro_structure(self):
        return self.micro_structure[0] if self.micro_structure and isinstance(self.micro_structure, list) and self.micro_structure else self.micro_structure if isinstance(self.micro_structure, dict) else None
        
    def get_dialogue_examples_titles(self):
        if not self.dialogues_examples: return []
        return [d.get("Nom") or d.get("Titre") or d.get("ID") for d in self.dialogues_examples if isinstance(d, dict)]

    def _get_element_details_by_name(self, element_name: str, element_list: list, name_keys=None) -> dict | None:
        if name_keys is None:
            name_keys = ["Nom"]
        if not element_list or not element_name:
            return None
        for element_data in element_list:
            if isinstance(element_data, dict):
                for key in name_keys:
                    if element_data.get(key) == element_name:
                        return element_data
        logger.warning(f"Élément '{element_name}' non trouvé dans la liste fournie avec les clés {name_keys}.")
        return None

    def get_character_details_by_name(self, name: str) -> dict | None:
        return self._get_element_details_by_name(name, self.characters)

    def get_location_details_by_name(self, name: str) -> dict | None:
        return self._get_element_details_by_name(name, self.locations)

    def get_item_details_by_name(self, name: str) -> dict | None:
        return self._get_element_details_by_name(name, self.items)

    def get_species_details_by_name(self, name: str) -> dict | None:
        return self._get_element_details_by_name(name, self.species)

    def get_community_details_by_name(self, name: str) -> dict | None:
        return self._get_element_details_by_name(name, self.communities)

    def get_dialogue_example_details_by_title(self, title: str) -> dict | None:
        return self._get_element_details_by_name(title, self.dialogues_examples, name_keys=["Nom", "Titre", "ID"])

    def get_quest_details_by_name(self, name: str) -> dict | None:
        if not hasattr(self, 'quests'): return None
        return self._get_element_details_by_name(name, self.quests)

    def set_previous_dialogue_context(self, path_interactions: Optional[List[Interaction]]) -> None:
        """Définit le contexte du dialogue précédent à utiliser pour la prochaine génération."""
        if path_interactions:
            logger.info(f"[LOG DEBUG] ContextBuilder: Contexte de dialogue précédent défini avec {len(path_interactions)} interaction(s). Stack: {''.join(traceback.format_stack(limit=5))}")
            self.previous_dialogue_context = path_interactions
        else:
            logger.info(f"[LOG DEBUG] ContextBuilder: Contexte de dialogue précédent réinitialisé (None). Stack: {''.join(traceback.format_stack(limit=5))}")
            self.previous_dialogue_context = None

    def _format_previous_dialogue_for_context(self, max_tokens_for_history: int) -> str:
        """Formate le dialogue précédent stocké pour l'inclure dans le contexte LLM."""
        logger.info(f"[LOG DEBUG] Appel à _format_previous_dialogue_for_context. previous_dialogue_context présent: {self.previous_dialogue_context is not None} (len={len(self.previous_dialogue_context) if self.previous_dialogue_context else 0})")
        if not self.previous_dialogue_context:
            return ""

        history_accumulator = []  # Utiliser un accumulateur temporaire
        current_tokens_content = 0  # Tokens pour le contenu réel de l'historique

        delimiter_start = "--- DIALOGUES PRECEDENTS ---"
        delimiter_end = "--- FIN DES DIALOGUES PRECEDENTS ---"
        
        tokens_for_delimiters_structure = self._count_tokens(delimiter_start) + self._count_tokens(delimiter_end) + self._count_tokens("\n") * 2
        available_tokens_for_content = max_tokens_for_history - tokens_for_delimiters_structure
        
        if available_tokens_for_content <= 0:
            logger.warning(f"ContextBuilder: Pas assez de tokens ({max_tokens_for_history}) alloués pour l'historique.")
            return ""

        interactions_to_include = self.previous_dialogue_context[-3:]

        for i, interaction in enumerate(interactions_to_include):
            interaction_parts = []
            interaction_title = interaction.title or f"Interaction ID: {interaction.interaction_id[:8]}..."
            # En-tête plus concis
            interaction_header = f"  Précédent ({i + 1}/{len(interactions_to_include)}): {interaction_title!r}"
            interaction_parts.append(interaction_header)
            
            for element in interaction.elements:
                if isinstance(element, DialogueLineElement):
                    char_name = element.speaker or "Narrateur"
                    # Indentation pour les lignes de dialogue
                    line = f"    {char_name}: {element.text}"
                    interaction_parts.append(line)
                elif isinstance(element, PlayerChoicesBlockElement):
                    # Indentation pour le bloc de choix
                    interaction_parts.append("    Joueur (Choix):")
                    for choice_idx, choice_option in enumerate(element.choices):
                        # Indentation pour chaque choix
                        choice_line = f"      - Choix {choice_idx + 1}: {choice_option.text} (-> {choice_option.next_interaction_id or 'N/A'})"
                        interaction_parts.append(choice_line)
            
            interaction_str = "\n".join(interaction_parts)
            
            tokens_for_current_interaction_segment = self._count_tokens(interaction_str)
            if history_accumulator:  
                tokens_for_current_interaction_segment += self._count_tokens("\n") # Pour le saut de ligne entre interactions

            if current_tokens_content + tokens_for_current_interaction_segment <= available_tokens_for_content:
                history_accumulator.append(interaction_str)
                current_tokens_content += tokens_for_current_interaction_segment
            else:
                logger.warning(f"ContextBuilder: Limite de tokens ({available_tokens_for_content} pour contenu) atteinte. Interaction {interaction_title!r} et suivantes non incluses.")
                break
        
        if not history_accumulator:
            logger.info("ContextBuilder: Aucun contenu d'historique de dialogue n'a pu être formaté.")
            return ""
        
        # Un seul saut de ligne entre les interactions dans l'accumulateur
        final_history_content_str = "\n".join(history_accumulator) 
        # Sauts de ligne clairs autour des délimiteurs
        return f"{delimiter_start}\n\n{final_history_content_str}\n\n{delimiter_end}"

    def _format_list(self, data_list, max_items=5) -> str:
        if not isinstance(data_list, list):
            if isinstance(data_list, str):
                data_list = [item.strip() for item in data_list.split(',') if item.strip()]
            else:
                return str(data_list)
        if not data_list: return "N/A"
        if len(data_list) > max_items:
            return ", ".join(data_list[:max_items]) + f", et {len(data_list) - max_items} autre(s)"
        return ", ".join(data_list)

    def _extract_from_dict(self, data: dict, path: str, default="N/A"):
        keys = path.split('.')
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    def _get_prioritized_info(self, element_data: dict, element_type: str, level: int, **kwargs) -> str:
        """
        Extrait et formate les informations d'un élément en fonction de sa priorité et du niveau de détail.
        MODIFIÉ : Ignore la troncature et les limites de liste pour retourner les données complètes.
        """
        details = []
        config_for_type = self.context_config.get(element_type.lower(), {})
        
        # Pour l'instant, on prend toutes les infos définies jusqu'au level demandé, sans tronquer.
        # On pourrait aussi simplement prendre toutes les clés de element_data si on veut tout.
        # Mais pour garder une certaine structure issue de la config :
        fields_to_extract = []
        for l in range(1, level + 1):
            fields_to_extract.extend(config_for_type.get(str(l), []))

        if not fields_to_extract and element_data: # Si la config est vide pour ce type/level, mais qu'on a des données
            logger.info(f"Aucune configuration de champ pour {element_type} au niveau {level}, tentative de formatage direct des données.")
            for key, value in element_data.items():
                if isinstance(value, list):
                    formatted_list = ", ".join(map(str, value))
                    details.append(f"{key.replace('_', ' ').capitalize()}: {formatted_list}")
                elif isinstance(value, dict):
                    # Pour les dictionnaires imbriqués, on pourrait les aplatir ou les formater spécifiquement.
                    # Pour l'instant, on les convertit en string simple.
                    details.append(f"{key.replace('_', ' ').capitalize()}: {json.dumps(value, ensure_ascii=False)}")
                elif value is not None:
                    details.append(f"{key.replace('_', ' ').capitalize()}: {str(value)}")
            return "\n".join(details)

        processed_paths = set()

        for field_config in fields_to_extract:
            path = field_config.get("path")
            if not path or path in processed_paths:
                continue
            processed_paths.add(path)

            label = field_config.get("label", path.split('.')[-1].replace('_', ' ').capitalize())
            condition_flag = field_config.get("condition_flag")
            condition_path_not_exists = field_config.get("condition_path_not_exists")

            if condition_flag and not kwargs.get(condition_flag, False):
                continue

            if condition_path_not_exists:
                value_for_condition_check = self._extract_from_dict(element_data, condition_path_not_exists, None)
                if value_for_condition_check is not None:
                    continue

            value = self._extract_from_dict(element_data, path)
            fallback_path = field_config.get("fallback_path")
            if (value is None or value == "N/A" or (isinstance(value, list) and not value)) and fallback_path:
                value = self._extract_from_dict(element_data, fallback_path)
            
            if value is None or value == "N/A" or (isinstance(value, list) and not value):
                continue

            if isinstance(value, list):
                # Si c'est une liste, on joint tous les éléments.
                # Si les éléments sont des dictionnaires, on les convertit en chaînes (par exemple, leurs 'Nom').
                formatted_list_items = []
                for item in value: # Ne plus utiliser list_max_items
                    if isinstance(item, dict):
                        # Essayer de trouver un champ 'Nom' ou 'Titre' ou prendre une représentation str
                        name = item.get("Nom", item.get("Titre", str(item)))
                        formatted_list_items.append(str(name))
                    else:
                        formatted_list_items.append(str(item))
                if formatted_list_items:
                    details.append(f"{label}: {', '.join(formatted_list_items)}")
            elif isinstance(value, dict):
                # Pour les dictionnaires, on pourrait vouloir une représentation plus détaillée.
                # Pour l'instant, on prend une conversion simple en string, ou on cherche une clé spécifique.
                # Cela pourrait être amélioré pour extraire des sous-clés pertinentes.
                display_value = value.get("Nom", value.get("Résumé", json.dumps(value, ensure_ascii=False, indent=2)))
                details.append(f"{label}: {display_value}")
            else:
                # text_value = str(value)
                # if truncate_length != -1 and len(text_value) > truncate_length:
                #     text_value = text_value[:truncate_length] + "... (extrait)"
                # details.append(f"{label}: {text_value}")
                details.append(f"{label}: {str(value)}") # Ne plus tronquer

        return "\n".join(details)

    def build_context(self, selected_elements: dict[str, list[str]], scene_instruction: str, max_tokens: int = 70000, include_dialogue_type: bool = True) -> str:
        """
        Construit un résumé contextuel basé sur les éléments sélectionnés et une instruction de scène,
        en ignorant toute limite de tokens (plus de troncature ni de refus d'ajout).
        """
        logger.info(f"Début de la construction du contexte avec max_tokens={max_tokens}.")
        logger.info(f"Éléments sélectionnés: {selected_elements}")
        
        context_parts = []
        # total_tokens = 0  # Plus utilisé
        level = 3  # Détail maximal
        
        # Contexte du dialogue précédent (si disponible)
        previous_dialogue_formatted = self._format_previous_dialogue_for_context(max_tokens)
        if previous_dialogue_formatted:
            context_parts.append(previous_dialogue_formatted)
            logger.info(f"Historique du dialogue précédent ajouté au contexte.")
        
        # Ajouter l'objectif de la scène juste après l'historique
        if scene_instruction and scene_instruction.strip():
            context_parts.append("\n--- OBJECTIF DE LA SCÈNE (Instruction Utilisateur) ---\n" + scene_instruction.strip())
        
        # Informations sur le GDD (personnages, lieux, etc.)
        element_categories_order = ["characters", "species", "communities", "locations", "items", "quests"]
        prioritized_elements_for_context = {}
        for category_key in element_categories_order:
            if category_key in selected_elements:
                prioritized_elements_for_context[category_key] = selected_elements[category_key]
        for category_key in selected_elements:
            if category_key not in prioritized_elements_for_context:
                prioritized_elements_for_context[category_key] = selected_elements[category_key]
        
        gdd_context_parts = []
        for category_key, names_list in prioritized_elements_for_context.items():
            # Ajout log détaillé sur le type de chaque valeur
            logger.debug(f"[build_context] Catégorie '{category_key}': type(names_list)={type(names_list)}, valeur={names_list}")
            if not isinstance(names_list, list):
                logger.warning(f"[build_context] Clé '{category_key}' ignorée car sa valeur n'est pas une liste (type={type(names_list)}). Valeur: {names_list}")
                continue
            if not names_list:
                continue
            category_title = category_key.replace('_', ' ').capitalize()
            gdd_context_parts.append(f"\n--- {category_title.upper()} ---")
            for name in names_list:
                element_data = None
                if category_key == "characters": element_data = self.get_character_details_by_name(name)
                elif category_key == "locations": element_data = self.get_location_details_by_name(name)
                elif category_key == "items": element_data = self.get_item_details_by_name(name)
                elif category_key == "species": element_data = self.get_species_details_by_name(name)
                elif category_key == "communities": element_data = self.get_community_details_by_name(name)
                elif category_key == "quests": element_data = self.get_quest_details_by_name(name)
                if element_data:
                    info_str = self._get_prioritized_info(element_data, category_key, level, include_dialogue_type=include_dialogue_type)
                    gdd_context_parts.append(info_str)
                else:
                    logger.warning(f"Aucune donnée trouvée pour l'élément '{name}' dans la catégorie '{category_key}'.")
        if gdd_context_parts:
            context_parts.extend(gdd_context_parts)
        
        # Construction finale du résumé
        context_summary = "\n".join(context_parts).strip()
        final_tokens = self._count_tokens(context_summary)
        logger.info(f"Résumé du contexte construit. Total tokens (après assemblage GDD et historique): {final_tokens}")
        if final_tokens > max_tokens:
            logger.warning(f"ATTENTION : Le contexte final ({final_tokens} tokens) dépasse la limite max_tokens ({max_tokens}). Le contenu sera tronqué.")
            # Troncature effective : découper le texte pour ne garder que max_tokens tokens
            # Utilise tiktoken si dispo, sinon découpe naïve sur les mots
            try:
                enc = tiktoken.get_encoding("cl100k_base")
                tokens = enc.encode(context_summary)
                truncated_tokens = tokens[:max_tokens]
                truncated_text = enc.decode(truncated_tokens)
            except Exception:
                # Fallback naïf : découpe sur les mots
                words = context_summary.split()
                truncated_text = " ".join(words[:max_tokens])
            context_summary = truncated_text + "\n... (contexte tronqué)"
        return context_summary

    def get_regions(self) -> list[str]:
        """Retourne une liste de noms de régions uniques à partir des données de localisation."""
        if not self.locations: return []
        return [loc.get("Nom") for loc in self.locations 
                if isinstance(loc, dict) and loc.get("Nom") and loc.get("Catégorie") == "Région"]

    def get_sub_locations(self, region_name: str) -> list[str]:
        if not self.locations or not region_name: return []
        region_details = self.get_location_details_by_name(region_name)
        if not region_details or region_details.get("Catégorie") != "Région":
            logger.warning(f"'{region_name}' n'est pas une région valide ou n'a pas été trouvée.")
            return []
        
        sub_locations_str = region_details.get("Contient")
        if isinstance(sub_locations_str, str) and sub_locations_str:
            return [name.strip() for name in sub_locations_str.split(',') if name.strip()]
        return []

    def _extract_linked_names(self, text_field: str | None, known_names_list: list[str]) -> set[str]:
        linked_found = set()
        if not text_field or not isinstance(text_field, str):
            return linked_found
        potential_names = [name.strip() for name in text_field.split(',') if name.strip()]
        for pname in potential_names:
            if pname in known_names_list:
                linked_found.add(pname)
        return linked_found

    def get_linked_elements(self, character_name: str | None = None, location_names: list[str] | None = None) -> dict[str, set[str]]:
        linked_elements: dict[str, set[str]] = {
            "characters": set(), "locations": set(), "items": set(),
            "species": set(), "communities": set(), "quests": set()
        }
        all_char_names = self.get_characters_names()
        all_loc_names = self.get_locations_names()
        all_item_names = self.get_items_names()
        all_species_names = self.get_species_names()
        all_comm_names = self.get_communities_names()
        all_quest_names = self.get_quests_names()

        if character_name:
            char_details = self.get_character_details_by_name(character_name)
            if char_details:
                linked_elements["items"].update(self._extract_linked_names(char_details.get("Détient"), all_item_names))
                linked_elements["species"].update(self._extract_linked_names(char_details.get("Espèce"), all_species_names))
                linked_elements["communities"].update(self._extract_linked_names(char_details.get("Communautés"), all_comm_names))
                linked_elements["locations"].update(self._extract_linked_names(char_details.get("Lieux de vie"), all_loc_names))
                relations_text = self._extract_from_dict(char_details, 'Background.Relations')
                if relations_text and isinstance(relations_text, str):
                    for word_or_phrase in self.potential_related_names_from_text(relations_text, all_char_names):
                         if word_or_phrase != character_name:
                            linked_elements["characters"].add(word_or_phrase)

        if location_names:
            for loc_name in location_names:
                loc_details = self.get_location_details_by_name(loc_name)
                if loc_details:
                    linked_elements["characters"].update(self._extract_linked_names(loc_details.get("Personnages présents"), all_char_names))
                    linked_elements["communities"].update(self._extract_linked_names(loc_details.get("Communautés présentes"), all_comm_names))
                    linked_elements["species"].update(self._extract_linked_names(loc_details.get("Faunes & Flores présentes"), all_species_names))
                    linked_elements["locations"].update(self._extract_linked_names(loc_details.get("Contient"), all_loc_names))
                    linked_elements["locations"].update(self._extract_linked_names(loc_details.get("Contenu par"), all_loc_names))

        if character_name: linked_elements["characters"].discard(character_name)
        if location_names: 
            for loc_name in location_names:
                linked_elements["locations"].discard(loc_name)
        return linked_elements

    @staticmethod
    def potential_related_names_from_text(text: str, known_character_names: list[str]) -> set[str]:
        if not text or not isinstance(text, str):
            return set()
        found_names = set()
        for known_name in known_character_names:
            if re.search(r"\b" + re.escape(known_name) + r"\b", text):
                found_names.add(known_name)
        return found_names

if __name__ == '__main__':
    # Configuration du logging pour les tests en standalone
    if not logger.hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    cb = ContextBuilder()
    cb.load_gdd_files()

    print(f"\n--- Personnages ({len(cb.characters)}) ---")
    for name in cb.get_characters_names()[:2]: print(f"  {name}")
    print(f"\n--- Lieux ({len(cb.locations)}) ---")
    for name in cb.get_locations_names()[:2]: print(f"  {name}")
    # ... (autres prints de test)

    if cb.vision_data:
        print(f"\n--- Vision Data ---")
        print(f"  Clés dans Vision: {list(cb.vision_data.keys())}")

    if tiktoken and cb.characters and cb.locations:
        print("\n--- Test build_context avec config --- ")
        selected_test_elements = {
            "characters": cb.get_characters_names()[:1], 
            "locations": cb.get_locations_names()[:1],
            "items": cb.get_items_names()[:1]
        }
        test_instruction = "Le personnage A doit convaincre le personnage B."
        context = cb.build_context(selected_test_elements, test_instruction, max_tokens=8000, include_dialogue_type=True)
        print(f"\nContexte Généré (avec config, Dialogue Type, limite 8000 tokens):\nNombre de tokens: {cb._count_tokens(context)}\n{context}")

        context_no_dt = cb.build_context(selected_test_elements, test_instruction, max_tokens=8000, include_dialogue_type=False)
        print(f"\nContexte Généré (avec config, SANS Dialogue Type, limite 8000 tokens):\nNombre de tokens: {cb._count_tokens(context_no_dt)}\n{context_no_dt}")
    else:
        print("\nSkipping build_context test: tiktoken non dispo ou pas assez de données de test.") 