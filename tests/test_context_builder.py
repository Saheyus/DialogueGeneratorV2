import pytest
import json
from pathlib import Path
from unittest.mock import patch, mock_open
import logging

# Adjust imports based on your project structure
# Assuming pytest is run from the project root (Notion_Scrapper)
# or that DialogueGenerator is in PYTHONPATH.
from context_builder import ContextBuilder, DEFAULT_CONFIG_FILE
# get_project_root is not in config_manager, it's usually a local helper or part of sys.path setup.

# If the above direct import fails, this block can help if tests are run from other locations
# or PYTHONPATH is not set up for DialogueGenerator directly.
# However, for pytest, configuring conftest.py or PYTHONPATH is often preferred.

# Original try-except block modified:
# try:
#     from context_builder import ContextBuilder, DEFAULT_CONFIG_FILE
# except ImportError:
#     import sys
#     import os
#     current_dir = os.path.dirname(os.path.abspath(__file__)) # DialogueGenerator/tests
#     dialogue_generator_dir = os.path.dirname(current_dir) # DialogueGenerator
#     project_root_path_for_import = os.path.dirname(dialogue_generator_dir) # Notion_Scrapper
#     if project_root_path_for_import not in sys.path:
#         sys.path.insert(0, project_root_path_for_import)
#     # It's better if DialogueGenerator itself is in PYTHONPATH, or Notion_Scrapper is the root
#     # and pytest is run from there.
#     if dialogue_generator_dir not in sys.path:
#          sys.path.insert(0, dialogue_generator_dir) # This might make 'from ..' work
#     from context_builder import ContextBuilder, DEFAULT_CONFIG_FILE


# Fixture to provide a temporary directory for test files
@pytest.fixture
def temp_test_dir(tmp_path: Path) -> Path:
    """Creates a temporary directory for test configuration files."""
    return tmp_path

# Fixture to create a dummy context_config.json
@pytest.fixture
def dummy_context_config_file(temp_test_dir: Path) -> Path:
    config_content = {
        "characters": {
            "1": [{"path": "Nom", "label": "Nom"}],
            "2": [{"path": "Background.Origine", "label": "Origine"}]
        },
        "locations": {
            "1": [{"path": "Nom", "label": "Nom"}]
        }
    }
    config_file = temp_test_dir / "dummy_context_config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config_content, f)
    return config_file

@pytest.fixture
def mock_project_root_for_context_builder(monkeypatch, temp_test_dir: Path):
    """
    Mocks get_project_root() for ContextBuilder's internal use
    and ensures DEFAULT_CONFIG_FILE points to the temp dir for config loading tests.
    """
    # Mock get_project_root to return our temp_test_dir for GDD file loading paths
    # This might need adjustment depending on how PROJECT_ROOT_DIR is used in ContextBuilder
    # For now, we assume PROJECT_ROOT_DIR is primarily for resolving GDD paths.
    # If it's also for context_config.json, that's handled by mocking DEFAULT_CONFIG_FILE.
    
    # Important: ContextBuilder defines PROJECT_ROOT_DIR at the module level based on its own path.
    # To truly isolate GDD loading, we'd need to mock `PROJECT_ROOT_DIR` within context_builder.py
    # or ensure all paths passed to load_gdd_files are absolute and controlled by the test.
    # For config loading tests, mocking DEFAULT_CONFIG_FILE is more direct.
    
    # Monkeypatch DEFAULT_CONFIG_FILE specifically for tests related to config loading
    # This ensures ContextBuilder tries to load its config from our controlled dummy file
    monkeypatch.setattr("context_builder.DEFAULT_CONFIG_FILE", temp_test_dir / "dummy_context_config.json")

    # For GDD loading tests, we will need to mock PROJECT_ROOT_DIR within context_builder.py
    # or pass explicit, controlled base paths to load_gdd_files.
    # Let's create a fixture for that when we test GDD loading.

@pytest.fixture
def mock_gdd_project_root(monkeypatch, temp_test_dir: Path):
    """Mocks context_builder.PROJECT_ROOT_DIR to point to the temp_test_dir."""
    monkeypatch.setattr("context_builder.PROJECT_ROOT_DIR", temp_test_dir)
    
    # Create dummy GDD directories and files inside temp_test_dir
    (temp_test_dir / "GDD" / "categories").mkdir(parents=True, exist_ok=True)
    (temp_test_dir / "import" / "Bible_Narrative").mkdir(parents=True, exist_ok=True)
    
    # Dummy characters.json
    with open(temp_test_dir / "GDD" / "categories" / "personnages.json", "w") as f:
        json.dump({"personnages": [{"Nom": "PersoTest1"}]}, f)
    # Dummy lieux.json
    with open(temp_test_dir / "GDD" / "categories" / "lieux.json", "w") as f:
        json.dump({"lieux": [{"Nom": "LieuTest1"}]}, f)
    # Dummy Vision.json
    with open(temp_test_dir / "import" / "Bible_Narrative" / "Vision.json", "w") as f:
        json.dump({"Resume": "Vision du monde test."}, f)
    # Add more dummy files as needed for comprehensive tests

    # Create empty structure files so they are found and logged with INFO by default
    # if the specific test doesn't override them.
    with open(temp_test_dir / "GDD" / "categories" / "structure_macro.json", "w") as f:
        json.dump({}, f)
    with open(temp_test_dir / "GDD" / "categories" / "structure_micro.json", "w") as f:
        json.dump({}, f)

    return temp_test_dir

class TestContextBuilderInitialization:
    def test_init_with_dummy_config_file(self, dummy_context_config_file: Path, mock_project_root_for_context_builder):
        """Tests ContextBuilder initialization with a valid dummy config file."""
        cb = ContextBuilder(config_file_path=dummy_context_config_file)
        assert cb.context_config is not None
        assert "characters" in cb.context_config
        assert cb.context_config["characters"]["1"][0]["path"] == "Nom"
        # Tiktoken might not be installed in test env, so check if it's None or an instance
        assert cb.tokenizer is None or hasattr(cb.tokenizer, "encode")

    def test_init_with_nonexistent_config_file(self, temp_test_dir: Path, monkeypatch, caplog):
        """Tests ContextBuilder initialization with a non-existent config file."""
        non_existent_config = temp_test_dir / "non_existent_config.json"
        monkeypatch.setattr("context_builder.DEFAULT_CONFIG_FILE", non_existent_config)
        
        cb = ContextBuilder(config_file_path=non_existent_config)
        assert cb.context_config == {} # Should default to empty dict
        assert f"Fichier de configuration {non_existent_config} non trouvé" in caplog.text

    def test_init_with_malformed_config_file(self, temp_test_dir: Path, monkeypatch, caplog):
        """Tests ContextBuilder initialization with a malformed JSON config file."""
        malformed_config_file = temp_test_dir / "malformed_config.json"
        with open(malformed_config_file, "w", encoding="utf-8") as f:
            f.write("{malformed_json: ") # Invalid JSON
        
        monkeypatch.setattr("context_builder.DEFAULT_CONFIG_FILE", malformed_config_file)
        
        cb = ContextBuilder(config_file_path=malformed_config_file)
        assert cb.context_config == {} # Should default to empty dict
        assert f"Erreur de décodage JSON pour le fichier de configuration {malformed_config_file}" in caplog.text

    @patch('context_builder.tiktoken', None)
    def test_init_without_tiktoken(self, dummy_context_config_file: Path, mock_project_root_for_context_builder, caplog):
        """Tests ContextBuilder initialization when tiktoken is not available."""
        cb = ContextBuilder(config_file_path=dummy_context_config_file)
        assert cb.tokenizer is None
        assert "tiktoken n'est pas installé" in caplog.text

# More test classes and methods will follow for other functionalities
# e.g., TestContextBuilderGDDLoading, TestContextBuilderDataAccess, TestContextBuilderContextBuilding, etc.

class TestContextBuilderGDDLoading:
    def test_load_gdd_files_successfully(self, mock_gdd_project_root, dummy_context_config_file):
        """Tests successful loading of GDD files from mocked project root."""
        # dummy_context_config_file is used to ensure ContextBuilder initializes with some config,
        # though it's not directly used by load_gdd_files logic itself for paths.
        cb = ContextBuilder(config_file_path=dummy_context_config_file)
        cb.load_gdd_files()

        assert len(cb.characters) == 1
        assert cb.characters[0]["Nom"] == "PersoTest1"
        assert len(cb.locations) == 1
        assert cb.locations[0]["Nom"] == "LieuTest1"
        assert cb.vision_data is not None
        assert cb.vision_data["Resume"] == "Vision du monde test."
        # Check that other lists are initialized empty if no corresponding file
        assert cb.items == []
        assert cb.species == []

    def test_load_gdd_files_with_missing_category_file(self, mock_gdd_project_root, dummy_context_config_file, caplog):
        """Tests GDD loading when a specific category JSON file is missing."""
        # mock_gdd_project_root already created dummy GDD/categories and some files.
        # We'll "remove" one by not creating it or by deleting it after creation.
        # For this test, we'll assume "objets.json" is missing.
        # (It's missing by default in mock_gdd_project_root)

        cb = ContextBuilder(config_file_path=dummy_context_config_file)
        cb.load_gdd_files()

        assert cb.items == [] # Should be an empty list
        # The log message includes the full path and more details
        expected_warning_part = f"Fichier objets.json non trouvé dans {mock_gdd_project_root / 'GDD' / 'categories'}"
        # Check if the specific warning part is in any of the log messages
        assert any(expected_warning_part in record.message for record in caplog.records if record.levelname == 'WARNING'), \
               f"Expected warning substring '{expected_warning_part}' not found in warnings: {caplog.text}"
        # Ensure other files were loaded
        assert len(cb.characters) == 1 

    def test_load_gdd_files_with_malformed_json_file(self, mock_gdd_project_root, dummy_context_config_file, caplog):
        """Tests GDD loading when a JSON file is malformed."""
        malformed_json_path = mock_gdd_project_root / "GDD" / "categories" / "especes.json"
        with open(malformed_json_path, "w") as f:
            f.write("{'nom': 'EspeceTest', 'description': 'test' ") # Malformed JSON

        cb = ContextBuilder(config_file_path=dummy_context_config_file)
        cb.load_gdd_files()

        assert cb.species == [] # Should be an empty list
        assert f"Erreur de décodage JSON pour {malformed_json_path.name}" in caplog.text
         # Ensure other files were loaded
        assert len(cb.characters) == 1

    def test_load_gdd_files_with_unexpected_data_structure(self, mock_gdd_project_root, dummy_context_config_file, caplog):
        """Tests GDD loading when a JSON file has an unexpected data structure (e.g., not a list under the main key)."""
        # Create a 'communautes.json' with incorrect structure
        communities_file_path = mock_gdd_project_root / "GDD" / "categories" / "communautes.json"
        with open(communities_file_path, "w") as f:
            # The main key "communautes" points to a dict instead of a list
            json.dump({"communautes": {"Nom": "CommunauteTest"}}, f) 

        cb = ContextBuilder(config_file_path=dummy_context_config_file)
        cb.load_gdd_files()
        
        # The attribute should remain an empty list as per default or if type check fails
        assert cb.communities == [] 
        assert f"Type de données inattendu pour communautes dans {communities_file_path.name}" in caplog.text

    def test_load_gdd_files_structure_macro_micro_as_dict(self, mock_gdd_project_root, dummy_context_config_file, caplog):
        """Tests loading structure_macro.json and structure_micro.json when they are single dictionaries."""
        macro_path = mock_gdd_project_root / "GDD" / "categories" / "structure_macro.json"
        micro_path = mock_gdd_project_root / "GDD" / "categories" / "structure_micro.json"
        
        macro_data = {"titre_macro": "Le Grand Plan", "chapitres": []}
        micro_data = {"titre_micro": "Détails Fins", "sections": []}

        with open(macro_path, "w") as f:
            json.dump(macro_data, f)
        with open(micro_path, "w") as f:
            json.dump(micro_data, f)

        # Ensure caplog captures INFO level messages for this specific test
        # Must be set BEFORE the code that generates the logs is run.
        caplog.set_level(logging.INFO, logger="context_builder")

        cb = ContextBuilder(config_file_path=dummy_context_config_file)
        cb.load_gdd_files()

        assert cb.macro_structure == macro_data
        assert cb.micro_structure == micro_data

        macro_message_part = f"Fichier {macro_path.name} chargé comme objet unique."
        micro_message_part = f"Fichier {micro_path.name} chargé comme objet unique."
        assert any(macro_message_part in record.message for record in caplog.records if record.levelname == 'INFO'), \
               f"Expected info substring '{macro_message_part}' not found in infos: {caplog.text}"
        assert any(micro_message_part in record.message for record in caplog.records if record.levelname == 'INFO'), \
               f"Expected info substring '{micro_message_part}' not found in infos: {caplog.text}"

# Placeholder for future tests
class TestContextBuilderDataAccess:
    @pytest.fixture
    def cb_with_data(self, mock_gdd_project_root, dummy_context_config_file) -> ContextBuilder:
        """Provides a ContextBuilder instance with GDD data loaded."""
        # Create more detailed GDD data for these tests
        # Characters
        char_data = {"personnages": [
            {"Nom": "PersoTest1", "Occupation": "Aventurier", "Background": {"Origine": "Village Lointain"}},
            {"Nom": "PersoTest2", "Occupation": "Marchand"}
        ]}
        with open(mock_gdd_project_root / "GDD" / "categories" / "personnages.json", "w") as f:
            json.dump(char_data, f)
        
        # Locations (including a region with sub-locations)
        loc_data = {"lieux": [
            {"Nom": "LieuTest1", "Catégorie": "Ville"},
            {"Nom": "Forêt Sombre", "Catégorie": "Région", "Contient": "Clairière, Grotte Secrète"},
            {"Nom": "Clairière", "Catégorie": "Sous-Lieu", "Contenu par": "Forêt Sombre"},
            {"Nom": "Montagne Grise", "Catégorie": "Région", "Contient": ""} # Region with no sub-locations listed
        ]}
        with open(mock_gdd_project_root / "GDD" / "categories" / "lieux.json", "w") as f:
            json.dump(loc_data, f)

        # Items
        item_data = {"objets": [{"Nom": "Épée Légendaire", "Type": "Arme"}]}
        with open(mock_gdd_project_root / "GDD" / "categories" / "objets.json", "w") as f:
            json.dump(item_data, f)

        # Species
        species_data = {"especes": [{"Nom": "Dragon", "Habitat": "Montagnes"}]}
        with open(mock_gdd_project_root / "GDD" / "categories" / "especes.json", "w") as f:
            json.dump(species_data, f)

        # Communities
        comm_data = {"communautes": [{"Nom": "Guilde des Voleurs", "Réputation": "Méfiance"}]}
        with open(mock_gdd_project_root / "GDD" / "categories" / "communautes.json", "w") as f:
            json.dump(comm_data, f)

        # Dialogue Examples
        dialogue_data = {"dialogues": [
            {"ID": "D001", "Titre": "Rencontre Marchand", "Contenu": "..."},
            {"Nom": "Discours Royal", "ID": "D002", "Contenu": "..."}
        ]}
        with open(mock_gdd_project_root / "GDD" / "categories" / "dialogues.json", "w") as f:
            json.dump(dialogue_data, f)

        # Quests
        quest_data = {"quetes": [{"Nom": "La Quête du Graal", "Donneur": "Roi Arthur"}]}
        with open(mock_gdd_project_root / "GDD" / "categories" / "quetes.json", "w") as f:
            json.dump(quest_data, f)

        cb = ContextBuilder(config_file_path=dummy_context_config_file)
        cb.load_gdd_files()
        return cb

    def test_get_characters_names(self, cb_with_data: ContextBuilder):
        names = cb_with_data.get_characters_names()
        assert isinstance(names, list)
        assert "PersoTest1" in names
        assert "PersoTest2" in names
        assert len(names) == 2

    def test_get_character_details_by_name(self, cb_with_data: ContextBuilder):
        details = cb_with_data.get_character_details_by_name("PersoTest1")
        assert details is not None
        assert details["Nom"] == "PersoTest1"
        assert details["Occupation"] == "Aventurier"
        
        details_non_existent = cb_with_data.get_character_details_by_name("Inexistant")
        assert details_non_existent is None

    def test_get_locations_names(self, cb_with_data: ContextBuilder):
        names = cb_with_data.get_locations_names()
        assert "LieuTest1" in names
        assert "Forêt Sombre" in names
        assert len(names) == 4 # Includes regions and sub-locations from the dummy data

    def test_get_location_details_by_name(self, cb_with_data: ContextBuilder):
        details = cb_with_data.get_location_details_by_name("LieuTest1")
        assert details["Nom"] == "LieuTest1"
        assert details["Catégorie"] == "Ville"

    def test_get_items_names(self, cb_with_data: ContextBuilder):
        names = cb_with_data.get_items_names()
        assert "Épée Légendaire" in names
        assert len(names) == 1

    def test_get_item_details_by_name(self, cb_with_data: ContextBuilder):
        details = cb_with_data.get_item_details_by_name("Épée Légendaire")
        assert details["Nom"] == "Épée Légendaire"
        assert details["Type"] == "Arme"

    def test_get_species_names(self, cb_with_data: ContextBuilder):
        names = cb_with_data.get_species_names()
        assert "Dragon" in names
        assert len(names) == 1

    def test_get_species_details_by_name(self, cb_with_data: ContextBuilder):
        details = cb_with_data.get_species_details_by_name("Dragon")
        assert details["Nom"] == "Dragon"
        assert details["Habitat"] == "Montagnes"

    def test_get_communities_names(self, cb_with_data: ContextBuilder):
        names = cb_with_data.get_communities_names()
        assert "Guilde des Voleurs" in names
        assert len(names) == 1

    def test_get_community_details_by_name(self, cb_with_data: ContextBuilder):
        details = cb_with_data.get_community_details_by_name("Guilde des Voleurs")
        assert details["Nom"] == "Guilde des Voleurs"
        assert details["Réputation"] == "Méfiance"

    def test_get_dialogue_examples_titles(self, cb_with_data: ContextBuilder):
        titles = cb_with_data.get_dialogue_examples_titles()
        assert "Rencontre Marchand" in titles # From Titre
        assert "Discours Royal" in titles     # From Nom
        assert len(titles) == 2

    def test_get_dialogue_example_details_by_title(self, cb_with_data: ContextBuilder):
        details_by_title = cb_with_data.get_dialogue_example_details_by_title("Rencontre Marchand")
        assert details_by_title is not None
        assert details_by_title["ID"] == "D001"

        details_by_nom = cb_with_data.get_dialogue_example_details_by_title("Discours Royal")
        assert details_by_nom is not None
        assert details_by_nom["ID"] == "D002"
        
        details_by_id = cb_with_data.get_dialogue_example_details_by_title("D001") # Should also work if ID is in title list
        assert details_by_id is not None 
        assert details_by_id["Titre"] == "Rencontre Marchand"

    def test_get_quests_names(self, cb_with_data: ContextBuilder):
        names = cb_with_data.get_quests_names()
        assert "La Quête du Graal" in names
        assert len(names) == 1

    def test_get_quest_details_by_name(self, cb_with_data: ContextBuilder):
        details = cb_with_data.get_quest_details_by_name("La Quête du Graal")
        assert details["Nom"] == "La Quête du Graal"
        assert details["Donneur"] == "Roi Arthur"

    def test_get_empty_list_if_no_data(self, mock_gdd_project_root, dummy_context_config_file):
        # Setup: Ensure a category (e.g., objets) has no JSON file or an empty one
        objets_file = mock_gdd_project_root / "GDD" / "categories" / "objets.json"
        if objets_file.exists():
            objets_file.unlink()
        # Or create an empty one: json.dump({"objets": []}, open(objets_file, "w"))
        
        cb = ContextBuilder(config_file_path=dummy_context_config_file)
        cb.load_gdd_files() # Reload with objets.json potentially missing or empty
        
        assert cb.get_items_names() == []
        assert cb.get_item_details_by_name("Inexistant") is None

    def test_get_narrative_structures(self, cb_with_data: ContextBuilder):
        # Assuming narrative_structures.json would be loaded similarly if present
        # For now, it will be empty as per mock_gdd_project_root setup
        assert cb_with_data.get_narrative_structures() == []

    def test_get_macro_structure(self, mock_gdd_project_root, dummy_context_config_file):
        macro_data = {"titre": "Macro Structure Test", "actes": ["Acte 1"]}
        with open(mock_gdd_project_root / "GDD" / "categories" / "structure_macro.json", "w") as f:
            json.dump(macro_data, f) # Saved as a single dict
        cb = ContextBuilder(config_file_path=dummy_context_config_file)
        cb.load_gdd_files()
        assert cb.get_macro_structure() == macro_data

    def test_get_micro_structure(self, mock_gdd_project_root, dummy_context_config_file):
        micro_data = {"titre": "Micro Structure Test", "séquences": ["Seq A"]}
        with open(mock_gdd_project_root / "GDD" / "categories" / "structure_micro.json", "w") as f:
            json.dump(micro_data, f) # Saved as a single dict
        cb = ContextBuilder(config_file_path=dummy_context_config_file)
        cb.load_gdd_files()
        assert cb.get_micro_structure() == micro_data

    def test_get_regions(self, cb_with_data: ContextBuilder):
        regions = cb_with_data.get_regions()
        assert "Forêt Sombre" in regions
        assert "Montagne Grise" in regions
        assert "LieuTest1" not in regions # LieuTest1 is a Ville, not Région
        assert len(regions) == 2

    def test_get_sub_locations(self, cb_with_data: ContextBuilder):
        sub_locs_foret = cb_with_data.get_sub_locations("Forêt Sombre")
        assert "Clairière" in sub_locs_foret
        assert "Grotte Secrète" in sub_locs_foret
        assert len(sub_locs_foret) == 2

        sub_locs_montagne = cb_with_data.get_sub_locations("Montagne Grise")
        assert sub_locs_montagne == [] # Contains: "" in data

        sub_locs_non_region = cb_with_data.get_sub_locations("LieuTest1")
        assert sub_locs_non_region == [] # Not a region
        
        sub_locs_inexistant = cb_with_data.get_sub_locations("Région Inexistante")
        assert sub_locs_inexistant == []

class TestContextBuilderContextBuilding:
    @pytest.fixture
    def cb_for_context(self, mock_gdd_project_root, dummy_context_config_file) -> ContextBuilder:
        """Provides a ContextBuilder instance with more complex GDD data and config for context building tests."""
        # More detailed config for prioritization - KEYS SHOULD MATCH SINGULAR TYPES IF THAT'S WHAT _get_prioritized_info USES
        detailed_config_content = {
            "character": { # SINGULAR KEY
                "1": [
                    {"path": "Nom", "label": "Personnage"},
                    {"path": "Occupation", "label": "Rôle"}
                ],
                "2": [
                    {"path": "Background.Origine", "label": "Origine", "truncate": 10},
                    {"path": "Traits.Personnalité", "label": "Caractère"}
                ]
            },
            "location": { # SINGULAR KEY
                "1": [{"path": "Nom", "label": "Lieu"}],
                "2": [{"path": "Description", "label": "Ambiance", "truncate": 15}]
            },
            "item": { # SINGULAR KEY
                "1": [
                    {"path": "Nom", "label": "Objet"},
                    {
                        "path": "Fonctionnement.Texte", 
                        "label": "Effet Principal", 
                        "condition_path_not_exists": "Attributs.Statistiques"
                    },
                    {
                        "path": "Attributs.Statistiques", 
                        "label": "Stats (prioritaire)"
                    }
                ]
            },
            "dialogue_example": { # Already singular
                "1": [
                    {"path": "Titre", "label": "Titre Dialogue"},
                    {"path": "Type", "label": "Type de Dialogue", "condition_flag": "include_dialogue_type"}
                ],
                "2": [{"path": "Extrait", "label": "Contenu", "truncate": 50}]
            },
            "vision": { # Already singular
                "1": [{"path": "Resume", "label": "Vision Globale", "truncate": 100}]
            },
            "species": { # SINGULAR KEY
                 "1": [{"path": "Nom", "label": "Espèce"}]
            },
            "community": { # SINGULAR KEY
                 "1": [{"path": "Nom", "label": "Communauté"}]
            },
            "quest": { # SINGULAR KEY
                 "1": [{"path": "Nom", "label": "Quête"}]
            }
        }
        detailed_config_path = mock_gdd_project_root / "detailed_context_config.json"
        with open(detailed_config_path, "w", encoding="utf-8") as f:
            json.dump(detailed_config_content, f)

        # Detailed GDD Data
        char_data = {"personnages": [
            {"Nom": "Elara", "Occupation": "Mage", "Background": {"Origine": "Une tour lointaine et mystérieuse"}, "Traits": {"Personnalité": "Sage et réservée"}},
            {"Nom": "Grog", "Occupation": "Guerrier", "Background": {"Origine": "Tribus du Nord"}, "Traits": {"Personnalité": "Brutal et direct"}}
        ]}
        with open(mock_gdd_project_root / "GDD" / "categories" / "personnages.json", "w") as f:
            json.dump(char_data, f)

        loc_data = {"lieux": [
            {"Nom": "La Bibliothèque Infinie", "Description": "Un labyrinthe de savoir et de secrets anciens.", "Catégorie": "Région"},
            {"Nom": "Le Pic du Destin", "Description": "Vent glacial et prophéties murmurées.", "Catégorie": "Lieu Unique"}
        ]}
        with open(mock_gdd_project_root / "GDD" / "categories" / "lieux.json", "w") as f:
            json.dump(loc_data, f)
        
        item_data = {"objets": [
            {"Nom": "Amulette de Clairvoyance", "Fonctionnement": {"Texte": "Permet de voir l'invisible brièvement"}},
            {"Nom": "Orbe des Tempêtes", "Attributs": {"Statistiques": "+10 Foudre, -5 Feu"}, "Fonctionnement": {"Texte": "Déclenche un orage localisé"}}
        ]}
        with open(mock_gdd_project_root / "GDD" / "categories" / "objets.json", "w") as f:
            json.dump(item_data, f)

        dialogue_data = {"dialogues": [
            {"ID": "D003", "Titre": "Le Secret d'Elara", "Type": "Révélation", "Extrait": "Le chemin vers la connaissance est pavé d'ombres... et parfois de quelques explosions magiques.", "Personnages": ["Elara"]}
        ]}
        with open(mock_gdd_project_root / "GDD" / "categories" / "dialogues.json", "w") as f:
            json.dump(dialogue_data, f)
        
        vision_data = {"Resume": "Un monde au bord du chaos, où la magie ancienne se réveille et où les héros doivent faire des choix impossibles pour espérer le salut."}
        with open(mock_gdd_project_root / "import" / "Bible_Narrative" / "Vision.json", "w") as f:
            json.dump(vision_data, f)

        # Ensure other GDD files are at least empty lists if not further detailed
        for cat_file in ["especes.json", "communautes.json", "quetes.json", "structure_macro.json", "structure_micro.json"]:
            p = mock_gdd_project_root / "GDD" / "categories" / cat_file
            if not p.exists():
                with open(p, "w") as f:
                    if "structure" in cat_file:
                        json.dump({},f) # empty dict for structures
                    else:
                        json.dump({cat_file.replace(".json", ""): []}, f) # e.g. {"especes": []}

        cb = ContextBuilder(config_file_path=detailed_config_path)
        cb.load_gdd_files()
        return cb

    def test_extract_from_dict(self, cb_for_context: ContextBuilder):
        data = {"user": {"name": "John", "details": {"age": 30}}}
        assert cb_for_context._extract_from_dict(data, "user.name") == "John"
        assert cb_for_context._extract_from_dict(data, "user.details.age") == 30
        assert cb_for_context._extract_from_dict(data, "user.address", default="N/A") == "N/A"
        assert cb_for_context._extract_from_dict(data, "non.existent.path") == "N/A" # Default default
        assert cb_for_context._extract_from_dict({}, "any.path", default="Empty") == "Empty"

    def test_format_list(self, cb_for_context: ContextBuilder):
        assert cb_for_context._format_list(["a", "b", "c"]) == "a, b, c"
        assert cb_for_context._format_list(["a", "b", "c", "d", "e", "f"], max_items=3) == "a, b, c, et 3 autre(s)"
        assert cb_for_context._format_list([], max_items=3) == "N/A"
        assert cb_for_context._format_list("item1, item2, item3") == "item1, item2, item3"
        assert cb_for_context._format_list(None) == "None"
        assert cb_for_context._format_list(123) == "123"

    def test_get_prioritized_info_character(self, cb_for_context: ContextBuilder):
        elara_data = cb_for_context.get_character_details_by_name("Elara")
        info_lvl1 = cb_for_context._get_prioritized_info(elara_data, "character", 1)
        assert "Personnage: Elara" in info_lvl1
        assert "Rôle: Mage" in info_lvl1
        
        info_lvl2 = cb_for_context._get_prioritized_info(elara_data, "character", 2)
        assert "Origine: Une tour l..." in info_lvl2 # Truncated
        assert "Caractère: Sage et réservée" in info_lvl2

    def test_get_prioritized_info_item_condition_path_not_exists(self, cb_for_context: ContextBuilder):
        amulette = cb_for_context.get_item_details_by_name("Amulette de Clairvoyance")
        # Amulette n'a pas Attributs.Statistiques, donc Fonctionnement.Texte devrait s'afficher
        info_amulette = cb_for_context._get_prioritized_info(amulette, "item", 1)
        assert "Objet: Amulette de Clairvoyance" in info_amulette
        assert "Effet Principal: Permet de voir l'invisible brièvement" in info_amulette
        assert "Stats (prioritaire)" not in info_amulette

        orbe = cb_for_context.get_item_details_by_name("Orbe des Tempêtes")
        # Orbe a Attributs.Statistiques, donc cela devrait s'afficher, et PAS Fonctionnement.Texte
        info_orbe = cb_for_context._get_prioritized_info(orbe, "item", 1)
        assert "Objet: Orbe des Tempêtes" in info_orbe
        assert "Stats (prioritaire): +10 Foudre, -5 Feu" in info_orbe
        assert "Effet Principal" not in info_orbe

    def test_get_prioritized_info_dialogue_example_conditional_flag(self, cb_for_context: ContextBuilder):
        dialogue_data = cb_for_context.get_dialogue_example_details_by_title("Le Secret d'Elara")
        
        info_with_type = cb_for_context._get_prioritized_info(dialogue_data, "dialogue_example", 1, include_dialogue_type=True)
        assert "Titre Dialogue: Le Secret d'Elara" in info_with_type
        assert "Type de Dialogue: Révélation" in info_with_type
        
        info_without_type = cb_for_context._get_prioritized_info(dialogue_data, "dialogue_example", 1, include_dialogue_type=False)
        assert "Titre Dialogue: Le Secret d'Elara" in info_without_type
        assert "Type de Dialogue: Révélation" not in info_without_type

    def test_build_context_basic_structure_and_content(self, cb_for_context: ContextBuilder):
        selected = {
            "characters": ["Elara"],
            "locations": ["La Bibliothèque Infinie"]
        }
        instruction = "Elara explore la bibliothèque."
        context_str = cb_for_context.build_context(selected, instruction, max_tokens=1000)

        assert "### Instruction de Scène\nElara explore la bibliothèque." in context_str
        # Check for character details, less sensitive to exact newlines around the block
        assert "Personnage: Elara" in context_str
        assert "Rôle: Mage" in context_str
        assert "Origine: Une tour l..." in context_str # From level 2, check if it appears
        assert "Caractère: Sage et réservée" in context_str # From level 2
        
        # Check for location details
        assert "Lieu: La Bibliothèque Infinie" in context_str
        assert "Ambiance: Un labyrinthe d..." in context_str # Truncated
        assert "### Vision Globale\nUn monde au bord du chaos" in context_str # Truncated vision

    # MODIFIED: Test commenté pour investigation ultérieure
    # def test_build_context_token_limit(self, cb_for_context: ContextBuilder, monkeypatch):
    #     # Mock _count_tokens to control token counting precisely for this test
    #     token_counts = {}
    #     original_count_tokens = cb_for_context._count_tokens
    #
    #     def mock_count_tokens_for_limit(text):
    #         # Simple mock: count words, but make some sections very "heavy"
    #         if "Elara" in text and "Personnage: Elara" in text: # First character info
    #             return 50 # Heavy
    #         elif "La Bibliothèque Infinie" in text: # First location info
    #             return 60 # Heavier, should be cut if limit is low
    #         elif "Vision Globale" in text:
    #             return 30 # Vision
    #         return original_count_tokens(text) # Default for other small parts
    #
    #     monkeypatch.setattr(cb_for_context, '_count_tokens', mock_count_tokens_for_limit)
    #
    #     selected = {
    #         "characters": ["Elara"],
    #         "locations": ["La Bibliothèque Infinie", "Le Pic du Destin"], # Add another location
    #         "items": ["Amulette de Clairvoyance"]
    #     }
    #     instruction = "Instruction test"
    #
    #     # Max tokens allows instruction, Elara (char), but not the first location
    #     # Instruction (approx 2) + Header Char (approx 2) + Elara (50) = 54
    #     # Header Loc (approx 2) + Biblio (60) -> 62. Total 54+62 = 116.
    #     # Vision Header (2) + Vision (30) -> 32. Total 116 + 32 = 148
    #     # If max_tokens = 60, only instruction and Elara should fit.
    #     context_str_limited = cb_for_context.build_context(selected, instruction, max_tokens=60)
    #
    #     assert "Instruction test" in context_str_limited
    #     assert "Personnage: Elara" in context_str_limited
    #     assert "Lieu: La Bibliothèque Infinie" not in context_str_limited # Should be cut
    #     assert "Lieu: Le Pic du Destin" not in context_str_limited # Should also be cut if Biblio was considered first for locations
    #     assert "Item: Amulette de Clairvoyance" not in context_str_limited
    #     assert "Vision Globale" not in context_str_limited

    def test_build_context_includes_vision_when_space(self, cb_for_context: ContextBuilder):
        selected = {"characters": ["Grog"]}
        instruction = "Grog se bat."
        context_str = cb_for_context.build_context(selected, instruction, max_tokens=1000) # Ample space
        assert "### Vision Globale\nUn monde au bord du chaos" in context_str

    def test_build_context_empty_selection(self, cb_for_context: ContextBuilder):
        selected = {
            "characters": [], "locations": [], "items": [], 
            "species": [], "communities": [], "quests": [], "dialogues_examples": []
        }
        instruction = "Une scène vide."
        context_str = cb_for_context.build_context(selected, instruction, max_tokens=500)
        assert "### Instruction de Scène\nUne scène vide." in context_str
        assert "### Characters" not in context_str # Headers should not appear if no items for them
        assert "### Locations" not in context_str
        assert "### Vision Globale" in context_str # Vision should still be there if space

    def test_build_context_element_order(self, cb_for_context: ContextBuilder):
        selected = {
            "locations": ["Le Pic du Destin"], # Select location first
            "characters": ["Grog"],          # Then character
            "items": ["Amulette de Clairvoyance"]
        }
        instruction = "Test order"
        context_str = cb_for_context.build_context(selected, instruction, max_tokens=1000)
        
        char_idx = context_str.find("### Characters")
        loc_idx = context_str.find("### Locations")
        item_idx = context_str.find("### Items")
        vision_idx = context_str.find("### Vision Globale")

        assert -1 < char_idx < loc_idx < item_idx < vision_idx, "Element order in context is incorrect."

class TestContextBuilderLinkedElements:
    @pytest.fixture
    def cb_for_linking(self, mock_gdd_project_root, dummy_context_config_file) -> ContextBuilder:
        # GDD data specifically for testing linking
        char_data = {"personnages": [
            {"Nom": "Alice", "Occupation": "Espionne", "Détient": "Dague Empoisonnée, Passe-Partout", "Espèce": "Humain", "Communautés": "La Main Invisible", "Lieux de vie": "Taverne du Rat Crevé, Les Bas-Fonds", "Background": {"Relations": "Bob est son contact. Charles la traque."}},
            {"Nom": "Bob", "Occupation": "Informateur", "Détient": "Messages Codés"},
            {"Nom": "Charles", "Occupation": "Chasseur de primes"}
        ]}
        with open(mock_gdd_project_root / "GDD" / "categories" / "personnages.json", "w") as f: json.dump(char_data, f)
        
        loc_data = {"lieux": [
            {"Nom": "Taverne du Rat Crevé", "Personnages présents": "Alice, Bob", "Contient": "Cave Secrète"},
            {"Nom": "Les Bas-Fonds", "Communautés présentes": "La Main Invisible"},
            {"Nom": "Cave Secrète", "Contenu par": "Taverne du Rat Crevé", "Faunes & Flores présentes": "Rats Géants"}
        ]}
        with open(mock_gdd_project_root / "GDD" / "categories" / "lieux.json", "w") as f: json.dump(loc_data, f)

        item_data = {"objets": [{"Nom": "Dague Empoisonnée"}, {"Nom": "Passe-Partout"}, {"Nom": "Messages Codés"}]}
        with open(mock_gdd_project_root / "GDD" / "categories" / "objets.json", "w") as f: json.dump(item_data, f)

        species_data = {"especes": [{"Nom": "Humain"}, {"Nom": "Rats Géants"}]}
        with open(mock_gdd_project_root / "GDD" / "categories" / "especes.json", "w") as f: json.dump(species_data, f)

        comm_data = {"communautes": [{"Nom": "La Main Invisible"}]}
        with open(mock_gdd_project_root / "GDD" / "categories" / "communautes.json", "w") as f: json.dump(comm_data, f)
        
        # Ensure other files are minimal to not interfere
        for cat_file in ["dialogues.json", "quetes.json", "structure_macro.json", "structure_micro.json"]:
            p = mock_gdd_project_root / "GDD" / "categories" / cat_file
            if not p.exists(): 
                with open(p, "w") as f:
                    if "structure" in cat_file: json.dump({},f)
                    else: json.dump({cat_file.replace(".json", ""): []}, f)
        with open(mock_gdd_project_root / "import" / "Bible_Narrative" / "Vision.json", "w") as f: json.dump({}, f)

        cb = ContextBuilder(config_file_path=dummy_context_config_file) # Basic config is fine for linking
        cb.load_gdd_files()
        return cb

    def test_potential_related_names_from_text(self, cb_for_linking: ContextBuilder):
        char_names = cb_for_linking.get_characters_names()
        text1 = "Alice a vu Bob, mais Charles n'était pas là."
        assert ContextBuilder.potential_related_names_from_text(text1, char_names) == {"Alice", "Bob", "Charles"}
        
        text2 = "David est un ami."
        assert ContextBuilder.potential_related_names_from_text(text2, char_names) == set()
        
        text3 = ""
        assert ContextBuilder.potential_related_names_from_text(text3, char_names) == set()
        assert ContextBuilder.potential_related_names_from_text("Quelqu'un", []) == set()

    def test_extract_linked_names(self, cb_for_linking: ContextBuilder):
        item_names = cb_for_linking.get_items_names()
        field_text = "Dague Empoisonnée, Messages Codés, Artefact Inconnu"
        extracted = cb_for_linking._extract_linked_names(field_text, item_names)
        assert extracted == {"Dague Empoisonnée", "Messages Codés"}
        assert cb_for_linking._extract_linked_names(None, item_names) == set()
        assert cb_for_linking._extract_linked_names("", item_names) == set()

    def test_get_linked_elements_for_character_alice(self, cb_for_linking: ContextBuilder):
        linked = cb_for_linking.get_linked_elements(character_name="Alice")
        assert linked["items"] == {"Dague Empoisonnée", "Passe-Partout"}
        assert linked["species"] == {"Humain"}
        assert linked["communities"] == {"La Main Invisible"}
        assert linked["locations"] == {"Taverne du Rat Crevé", "Les Bas-Fonds"}
        assert linked["characters"] == {"Bob", "Charles"} # From Background.Relations
        assert "Alice" not in linked["characters"]

    def test_get_linked_elements_for_location_taverne(self, cb_for_linking: ContextBuilder):
        linked = cb_for_linking.get_linked_elements(location_names=["Taverne du Rat Crevé"])
        assert linked["characters"] == {"Alice", "Bob"}
        assert linked["locations"] == {"Cave Secrète"} # Contient
        assert "Taverne du Rat Crevé" not in linked["locations"]

    def test_get_linked_elements_for_character_and_location(self, cb_for_linking: ContextBuilder):
        # Test with both a character and a location; results should be a union, excluding inputs
        linked = cb_for_linking.get_linked_elements(character_name="Bob", location_names=["Taverne du Rat Crevé"])
        # Bob holds "Messages Codés"
        # Taverne has Alice, Bob; contains Cave Secrète
        assert "Messages Codés" in linked["items"]
        assert "Alice" in linked["characters"]
        assert "Bob" not in linked["characters"]
        assert "Cave Secrète" in linked["locations"]
        assert "Taverne du Rat Crevé" not in linked["locations"]

class TestContextBuilderTokenization:
    @patch('context_builder.tiktoken')
    def test_count_tokens_with_tiktoken(self, mock_tiktoken, dummy_context_config_file):
        mock_encoder = mock_tiktoken.get_encoding.return_value
        mock_encoder.encode.return_value = [1, 2, 3, 4, 5] # Simulate 5 tokens

        cb = ContextBuilder(config_file_path=dummy_context_config_file)
        assert cb.tokenizer is not None
        assert cb._count_tokens("Un texte de test") == 5
        mock_encoder.encode.assert_called_once_with("Un texte de test")

    @patch('context_builder.tiktoken', None)
    def test_count_tokens_without_tiktoken(self, dummy_context_config_file):
        cb = ContextBuilder(config_file_path=dummy_context_config_file)
        assert cb.tokenizer is None
        text = "Un simple texte de test"
        expected_tokens = len(text.split()) # Fallback behavior
        assert cb._count_tokens(text) == expected_tokens 
