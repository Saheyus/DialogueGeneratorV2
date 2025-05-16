# DialogueGenerator/context_builder.py
import json
from pathlib import Path
import logging

# Configuration du logging pour ce module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ContextBuilder:
    def __init__(self):
        self.gdd_data = {} # Peut-être pour GDD_Full.json si besoin plus tard
        self.characters = []
        self.locations = []
        self.items = []
        self.species = []
        self.communities = []
        self.narrative_structures = [] # Pourrait être un dict si la structure est unique
        self.macro_structure = {}      # Probablement un dict unique
        self.micro_structure = {}      # Probablement un dict unique
        self.dialogues_examples = []
        # Plus de structures de données pour d'autres catégories
        self.vision_data = None # Pour charger Vision.json

    def load_gdd_files(self, gdd_base_path_str="../GDD", import_base_path_str="../import"):
        """
        Charge les fichiers JSON du GDD depuis les chemins spécifiés.
        Se concentre sur les fichiers non-Mini dans GDD/categories/
        et charge également Vision.json depuis import/Bible_Narrative/
        """
        gdd_base_path = Path(gdd_base_path_str)
        categories_path = gdd_base_path / "categories"
        import_base_path = Path(import_base_path_str)

        logger.info(f"Début du chargement des données du GDD depuis {categories_path} et {import_base_path}.")

        # Charger Vision.json (Bible Narrative)
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
            # Pour les listes d'entités, la clé dans le JSON est le nom du fichier (ex: "personnages")
            "personnages": {"attr": "characters", "key": "personnages", "type": list},
            "lieux": {"attr": "locations", "key": "lieux", "type": list},
            "objets": {"attr": "items", "key": "objets", "type": list},
            "especes": {"attr": "species", "key": "especes", "type": list},
            "communautes": {"attr": "communities", "key": "communautes", "type": list},
            "dialogues": {"attr": "dialogues_examples", "key": "dialogues", "type": list},
            "structure_narrative": {"attr": "narrative_structures", "key": "structure_narrative", "type": list}, 
            # Pour les fichiers qui sont un objet unique (après "Vision"), la clé peut être le nom du fichier ou une clé spécifique
            # La logique actuelle tente de prendre l'objet entier si la clé principale n'est pas trouvée mais que le type est dict.
            "structure_macro": {"attr": "macro_structure", "key": "structure_macro", "type": list}, 
            "structure_micro": {"attr": "micro_structure", "key": "structure_micro", "type": list}, 
        }

        for file_key, load_config in categories_to_load.items():
            attribute_name = load_config["attr"]
            json_main_key = load_config["key"]
            expected_type = load_config["type"]
            
            file_path = categories_path / f"{file_key}.json"
            default_value = [] if expected_type == list else {}
            setattr(self, attribute_name, default_value) # Initialiser avec la valeur par défaut

            if file_path.exists() and file_path.is_file():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    data_to_set = None
                    if isinstance(data, dict) and json_main_key in data:
                        data_to_set = data[json_main_key]
                    elif isinstance(data, dict) and expected_type == dict: # Pour les structures uniques comme Macro/Micro
                        data_to_set = data
                    elif isinstance(data, list) and expected_type == list: # Cas où le JSON est directement une liste
                         data_to_set = data
                    
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
        """Retourne une liste des noms des personnages."""
        if not self.characters: return []
        return [char.get("Nom") for char in self.characters if isinstance(char, dict) and char.get("Nom")]

    def get_locations_names(self):
        """Retourne une liste des noms des lieux."""
        if not self.locations: return []
        return [loc.get("Nom") for loc in self.locations if isinstance(loc, dict) and loc.get("Nom")]

    def get_items_names(self):
        """Retourne une liste des noms des objets."""
        if not self.items: return []
        return [item.get("Nom") for item in self.items if isinstance(item, dict) and item.get("Nom")]

    def get_species_names(self):
        """Retourne une liste des noms des espèces."""
        if not self.species: return []
        return [s.get("Nom") for s in self.species if isinstance(s, dict) and s.get("Nom")]

    def get_communities_names(self):
        """Retourne une liste des noms des communautés."""
        if not self.communities: return []
        return [c.get("Nom") for c in self.communities if isinstance(c, dict) and c.get("Nom")]

    # Pour les structures (narrative, macro, micro), il est peut-être plus pertinent
    # de retourner l'objet/la liste d'objets directement plutôt qu'une liste de noms.
    def get_narrative_structures(self):
        return self.narrative_structures

    def get_macro_structure(self):
        # Si c'est une liste qui contient généralement un seul gros dictionnaire
        return self.macro_structure[0] if self.macro_structure and isinstance(self.macro_structure, list) else None

    def get_micro_structure(self):
        # Si c'est une liste qui contient généralement un seul gros dictionnaire
        return self.micro_structure[0] if self.micro_structure and isinstance(self.micro_structure, list) else None
        
    def get_dialogue_examples_titles(self):
        """Retourne une liste des titres/identifiants des exemples de dialogues."""
        if not self.dialogues_examples: return []
        # Supposons que les dialogues ont un champ "Titre" ou "ID" ou "Nom"
        return [d.get("Nom") or d.get("Titre") or d.get("ID") for d in self.dialogues_examples if isinstance(d, dict)]

# Pour des tests rapides
if __name__ == '__main__':
    cb = ContextBuilder()
    cb.load_gdd_files()

    print(f"\n--- Personnages ({len(cb.characters)}) ---")
    for name in cb.get_characters_names()[:2]: print(f"  {name}")

    print(f"\n--- Lieux ({len(cb.locations)}) ---")
    for name in cb.get_locations_names()[:2]: print(f"  {name}")

    print(f"\n--- Objets ({len(cb.items)}) ---")
    for name in cb.get_items_names()[:2]: print(f"  {name}")

    print(f"\n--- Espèces ({len(cb.species)}) ---")
    for name in cb.get_species_names()[:2]: print(f"  {name}")

    print(f"\n--- Communautés ({len(cb.communities)}) ---")
    for name in cb.get_communities_names()[:2]: print(f"  {name}")
    
    print(f"\n--- Dialogues Exemples ({len(cb.dialogues_examples)}) ---")
    for name in cb.get_dialogue_examples_titles()[:2]: print(f"  {name}")

    print(f"\n--- Structure Narrative ({len(cb.get_narrative_structures()) if isinstance(cb.get_narrative_structures(), list) else 'Objet unique non chargé comme liste'}) ---")
    # Afficher un aperçu si c'est une liste
    if isinstance(cb.get_narrative_structures(), list) and cb.get_narrative_structures():
        for item in cb.get_narrative_structures()[:1]: # Affiche le premier item/partie
            print(f"  Premier élément (clés): {list(item.keys()) if isinstance(item, dict) else item}")
    elif cb.get_narrative_structures(): # Si c'est un dict non vide (ne devrait plus arriver)
         print(f"  Clés principales: {list(cb.get_narrative_structures().keys())}")


    macro_struct = cb.get_macro_structure()
    print(f"\n--- Structure Macro ({'Chargée' if macro_struct else 'Non chargée ou vide'}) ---")
    if macro_struct: print(f"  Clés: {list(macro_struct.keys())}")

    micro_struct = cb.get_micro_structure()
    print(f"\n--- Structure Micro ({'Chargée' if micro_struct else 'Non chargée ou vide'}) ---")
    if micro_struct: print(f"  Clés: {list(micro_struct.keys())}")
    
    if cb.vision_data:
        print(f"\n--- Vision Data ---")
        print(f"  Clés dans Vision: {list(cb.vision_data.keys())}")
        if "Nom" in cb.vision_data: print(f"  Nom Vision: {cb.vision_data['Nom']}") 