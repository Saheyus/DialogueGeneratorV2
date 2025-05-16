# DialogueGenerator/context_builder.py
import json
from pathlib import Path
import logging
import re
import os

try:
    import tiktoken
except ImportError:
    tiktoken = None

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
        self.macro_structure = {}
        self.micro_structure = {}
        self.dialogues_examples = []
        self.vision_data = None
        self.quests = []
        self.context_config = self._load_context_config(config_file_path)

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
            "structure_macro": {"attr": "macro_structure", "key": "structure_macro", "type": dict},
            "structure_micro": {"attr": "micro_structure", "key": "structure_micro", "type": dict},
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
        Extrait les informations d'un élément en fonction du type, du niveau de priorité,
        et de la configuration chargée dans self.context_config.
        Les kwargs peuvent contenir des indicateurs conditionnels comme `include_dialogue_type`.
        """
        if not element_data or not self.context_config:
            return ""

        type_config = self.context_config.get(element_type)
        if not type_config:
            logger.debug(f"Aucune configuration de contexte trouvée pour le type: {element_type}")
            return ""

        level_config = type_config.get(str(level))
        if not level_config or not isinstance(level_config, list):
            logger.debug(f"Aucune configuration de niveau {level} trouvée ou invalide pour le type: {element_type}")
            return ""

        parts = []
        for field_desc in level_config:
            if not isinstance(field_desc, dict):
                continue

            condition_flag_name = field_desc.get("condition_flag")
            if condition_flag_name and not kwargs.get(condition_flag_name, True):
                continue # La condition pour inclure ce champ n'est pas remplie

            main_path = field_desc.get("path")
            if not main_path:
                continue

            value = self._extract_from_dict(element_data, main_path)

            fallback_path = field_desc.get("fallback_path")
            if (value == "N/A" or not value) and fallback_path:
                value = self._extract_from_dict(element_data, fallback_path)
            
            # Gestion de condition_path_not_exists (pour afficher un champ seulement si un autre n'existe pas)
            # Ceci est une logique un peu plus spécifique demandée pour le champ "Fonctionnement de base" de l'item.
            # On pourrait la généraliser si besoin.
            cond_path_not_exists = field_desc.get("condition_path_not_exists")
            if cond_path_not_exists:
                check_val = self._extract_from_dict(element_data, cond_path_not_exists)
                if check_val and check_val != "N/A":
                    continue # Le champ conditionnel existe, donc on saute ce champ

            if value and value != "N/A":
                label = field_desc.get("label", main_path.split('.')[-1]) # Utilise la dernière partie du path comme label par défaut
                text_value = str(value)

                if field_desc.get("is_list", False):
                    max_list_items = field_desc.get("list_max_items", 5)
                    text_value = self._format_list(value, max_items=max_list_items)
                else:
                    truncate_len = field_desc.get("truncate", -1)
                    if truncate_len > 0 and len(text_value) > truncate_len:
                        text_value = text_value[:truncate_len] + "..."
                
                parts.append(f"{label}: {text_value}")
        
        return "\n".join(filter(None, parts)) + ("\n" if parts else "")

    def build_context(self, selected_elements: dict[str, list[str]], scene_instruction: str, max_tokens: int = 16000, include_dialogue_type: bool = True) -> str:
        context_parts = []
        current_tokens = 0

        if scene_instruction:
            instruction_tokens = self._count_tokens(scene_instruction)
            if current_tokens + instruction_tokens <= max_tokens:
                context_parts.append(f"### Instruction de Scène\n{scene_instruction}\n")
                current_tokens += instruction_tokens
            else:
                logger.warning("L'instruction de scène est trop longue pour être incluse avec le budget de tokens actuel.")
        
        element_order = ["characters", "locations", "items", "species", "communities", "quests", "dialogues_examples"]

        for element_type in element_order:
            if element_type in selected_elements:
                if not selected_elements[element_type]:
                    continue

                type_header = f"### {element_type.capitalize()}\n"
                type_header_tokens = self._count_tokens(type_header)
                if current_tokens + type_header_tokens > max_tokens:
                    break 
                
                context_parts.append(type_header)
                current_tokens += type_header_tokens

                for name in selected_elements[element_type]:
                    details = None
                    # Utilisation des méthodes get_..._details_by_name existantes
                    if element_type == "characters": details = self.get_character_details_by_name(name)
                    elif element_type == "locations": details = self.get_location_details_by_name(name)
                    elif element_type == "items": details = self.get_item_details_by_name(name)
                    elif element_type == "species": details = self.get_species_details_by_name(name)
                    elif element_type == "communities": details = self.get_community_details_by_name(name)
                    elif element_type == "quests": details = self.get_quest_details_by_name(name)
                    elif element_type == "dialogues_examples": details = self.get_dialogue_example_details_by_title(name)
                    
                    if details:
                        for level in [1, 2, 3]:
                            singular_type = element_type[:-1] if element_type.endswith("s") and element_type != "species" else element_type
                            if element_type == "dialogues_examples": singular_type = "dialogue_example"
                            
                            # Passer les indicateurs conditionnels à _get_prioritized_info
                            conditional_flags = {"include_dialogue_type": include_dialogue_type}
                            info_str = self._get_prioritized_info(details, singular_type, level, **conditional_flags)
                            
                            if not info_str: continue
                            info_tokens = self._count_tokens(info_str)
                            
                            if current_tokens + info_tokens <= max_tokens:
                                context_parts.append(info_str)
                                current_tokens += info_tokens
                            else:
                                logger.info(f"Token limit reached for {element_type} '{name}' at priority level {level}. Skipping further details for this item.")
                                break 
                    if current_tokens >= max_tokens: break 
            if current_tokens >= max_tokens: break 

        if self.vision_data and (current_tokens + self._count_tokens("### Vision du Monde\n") < max_tokens):
            # Utiliser la config pour extraire la vision si elle est définie, sinon fallback
            vision_summary_from_config = ""
            if self.context_config.get("vision") and self.context_config["vision"].get("1"):
                 # Supposons une structure simple pour la vision dans config: [{"path": "Resume", "label": "Vision du Monde", "truncate": 1000}]
                field_desc_vision = self.context_config["vision"]["1"][0]
                raw_vision_summary = self._extract_from_dict(self.vision_data, field_desc_vision.get("path", "Resume"))
                if raw_vision_summary and raw_vision_summary != "N/A":
                    truncate_len_vision = field_desc_vision.get("truncate", 1000)
                    label_vision = field_desc_vision.get("label", "Vision du Monde")
                    if truncate_len_vision > 0 and len(raw_vision_summary) > truncate_len_vision:
                        raw_vision_summary = raw_vision_summary[:truncate_len_vision] + "..."
                    vision_summary_from_config = f"### {label_vision}\n{raw_vision_summary}\n"
            else: # Fallback à l'ancienne méthode si pas de config pour la vision
                vision_summary = self.vision_data.get("Resume", "") 
                if vision_summary:
                    vision_summary_from_config = f"### Vision du Monde\n{vision_summary[:1000]}\n" 

            if vision_summary_from_config:
                vision_tokens = self._count_tokens(vision_summary_from_config)
                if current_tokens + vision_tokens <= max_tokens:
                    context_parts.append(vision_summary_from_config)
                    current_tokens += vision_tokens
        
        logger.info(f"Contexte construit avec {current_tokens} tokens (approx).")
        return "\n".join(context_parts)

    def get_regions(self) -> list[str]:
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
                    for word_or_phrase in potential_related_names_from_text(relations_text, all_char_names):
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

def potential_related_names_from_text(text: str, known_character_names: list[str]) -> set[str]:
    if not text or not isinstance(text, str):
        return set()
    found_names = set()
    for known_name in known_character_names:
        if re.search(r"\b" + re.escape(known_name) + r"\b", text):
            found_names.add(known_name)
    return found_names 