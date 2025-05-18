import unittest
from unittest.mock import patch, mock_open, MagicMock
import json
import os
from pathlib import Path

# Ajuster le sys.path pour permettre l'import de DialogueGenerator
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from DialogueGenerator import config_manager
from DialogueGenerator.config_manager import UI_SETTINGS_FILE, load_ui_settings, save_ui_settings # Importer pour patcher directement

class TestConfigManager(unittest.TestCase):

    def setUp(self):
        self.settings_backup = None
        if UI_SETTINGS_FILE.exists():
            with open(UI_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                self.settings_backup = f.read()
            UI_SETTINGS_FILE.unlink() # Supprimer pour commencer propre

    def tearDown(self):
        if self.settings_backup:
            with open(UI_SETTINGS_FILE, 'w', encoding='utf-8') as f:
                f.write(self.settings_backup)
        elif UI_SETTINGS_FILE.exists():
            UI_SETTINGS_FILE.unlink()

    @patch(f'{config_manager.__name__}.save_ui_settings') # Mocker save_ui_settings directement
    @patch(f'{config_manager.__name__}.load_ui_settings') # Mocker load_ui_settings directement
    def test_set_unity_dialogues_path_new_file(self, mock_load_ui_settings, mock_save_ui_settings):
        """Teste la définition du chemin quand ui_settings.json n'existe pas ou est vide."""
        mock_load_ui_settings.return_value = {}  # Simule un fichier non existant ou vide
        
        test_path = "C:/test/path"
        # Path.is_dir est utilisé par set_unity_dialogues_path pour un warning, mais n'affecte pas le retour/sauvegarde
        with patch('pathlib.Path.is_dir', return_value=True): 
            result = config_manager.set_unity_dialogues_path(test_path)
        
        self.assertTrue(result)
        mock_load_ui_settings.assert_called_once()
        mock_save_ui_settings.assert_called_once_with({"unity_dialogues_path": test_path})

    @patch(f'{config_manager.__name__}.save_ui_settings')
    @patch(f'{config_manager.__name__}.load_ui_settings')
    def test_set_unity_dialogues_path_existing_file(self, mock_load_ui_settings, mock_save_ui_settings):
        """Teste la définition du chemin quand ui_settings.json existe déjà."""
        existing_settings = {"other_key": "other_value"}
        mock_load_ui_settings.return_value = existing_settings
        
        test_path = "D:/another/path"
        with patch('pathlib.Path.is_dir', return_value=True):
            result = config_manager.set_unity_dialogues_path(test_path)
        
        self.assertTrue(result)
        mock_load_ui_settings.assert_called_once()
        expected_settings_to_save = {"other_key": "other_value", "unity_dialogues_path": test_path}
        mock_save_ui_settings.assert_called_once_with(expected_settings_to_save)

    @patch(f'{config_manager.__name__}.save_ui_settings')
    @patch(f'{config_manager.__name__}.load_ui_settings')
    @patch('pathlib.Path.is_dir', return_value=False) # Simule que le chemin n'est pas un dir
    def test_set_unity_dialogues_path_invalid_path_is_not_dir(self, mock_is_dir, mock_load_ui_settings, mock_save_ui_settings):
        """Teste la définition avec un chemin qui n'est pas un répertoire."""
        mock_load_ui_settings.return_value = {}
        test_path = "C:/not_a_dir"
        
        result = config_manager.set_unity_dialogues_path(test_path)
        self.assertTrue(result) # La fonction set est permissive, logue un warning.
        mock_load_ui_settings.assert_called_once()
        mock_save_ui_settings.assert_called_once_with({"unity_dialogues_path": test_path})

    # Les tests pour get_unity_dialogues_path restent globalement les mêmes,
    # mais on va s'assurer qu'ils mockent load_ui_settings au lieu de open/json.load directement
    # pour être cohérents avec la structure de config_manager.

    @patch('os.access')
    @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.exists')
    @patch(f'{config_manager.__name__}.load_ui_settings')
    def test_get_unity_dialogues_path_success(self, mock_load_ui_settings, mock_path_exists, mock_is_dir, mock_os_access):
        """Teste la récupération d'un chemin valide et existant."""
        test_path_str = "E:/valid/path"
        mock_load_ui_settings.return_value = {"unity_dialogues_path": test_path_str}
        mock_path_exists.return_value = True
        mock_is_dir.return_value = True
        mock_os_access.side_effect = [True, True] # W_OK, R_OK

        retrieved_path = config_manager.get_unity_dialogues_path()
        self.assertIsNotNone(retrieved_path)
        self.assertEqual(retrieved_path, Path(test_path_str))
        mock_load_ui_settings.assert_called_once()
        mock_os_access.assert_any_call(Path(test_path_str), os.W_OK)
        mock_os_access.assert_any_call(Path(test_path_str), os.R_OK)

    @patch(f'{config_manager.__name__}.load_ui_settings')
    def test_get_unity_dialogues_path_not_configured(self, mock_load_ui_settings):
        """Teste la récupération quand le chemin n'est pas dans les settings."""
        mock_load_ui_settings.return_value = {"other_key": "value"} # Pas de clé 'unity_dialogues_path'
        retrieved_path = config_manager.get_unity_dialogues_path()
        self.assertIsNone(retrieved_path)
        mock_load_ui_settings.assert_called_once()

    @patch('pathlib.Path.exists', return_value=False) # Le chemin n'existe pas
    @patch(f'{config_manager.__name__}.load_ui_settings')
    def test_get_unity_dialogues_path_not_exists(self, mock_load_ui_settings, mock_path_exists):
        """Teste la récupération quand le chemin configuré n'existe pas."""
        mock_load_ui_settings.return_value = {"unity_dialogues_path": "F:/non_existent_path"}
        retrieved_path = config_manager.get_unity_dialogues_path()
        self.assertIsNone(retrieved_path)
        mock_load_ui_settings.assert_called_once()

    @patch('pathlib.Path.is_dir', return_value=False) # N'est pas un répertoire
    @patch('pathlib.Path.exists', return_value=True)
    @patch(f'{config_manager.__name__}.load_ui_settings')
    def test_get_unity_dialogues_path_not_a_directory(self, mock_load_ui_settings, mock_path_exists, mock_is_dir):
        """Teste la récupération quand le chemin n'est pas un dossier."""
        mock_load_ui_settings.return_value = {"unity_dialogues_path": "G:/not_a_dir_file.txt"}
        retrieved_path = config_manager.get_unity_dialogues_path()
        self.assertIsNone(retrieved_path)
        mock_load_ui_settings.assert_called_once()

    @patch('os.access', side_effect=[False]) # Non accessible en écriture
    @patch('pathlib.Path.is_dir', return_value=True)
    @patch('pathlib.Path.exists', return_value=True)
    @patch(f'{config_manager.__name__}.load_ui_settings')
    def test_get_unity_dialogues_path_not_writable(self, mock_load_ui_settings, mock_path_exists, mock_is_dir, mock_os_access):
        """Teste la récupération quand le chemin n'est pas accessible en écriture."""
        test_path_str = "H:/not_writable"
        mock_load_ui_settings.return_value = {"unity_dialogues_path": test_path_str}
        retrieved_path = config_manager.get_unity_dialogues_path()
        self.assertIsNone(retrieved_path)
        mock_load_ui_settings.assert_called_once()
        mock_os_access.assert_called_once_with(Path(test_path_str), os.W_OK)
        
    @patch('os.access', side_effect=[True, False]) # Accessible en écriture, mais pas en lecture
    @patch('pathlib.Path.is_dir', return_value=True)
    @patch('pathlib.Path.exists', return_value=True)
    @patch(f'{config_manager.__name__}.load_ui_settings')
    def test_get_unity_dialogues_path_not_readable(self, mock_load_ui_settings, mock_path_exists, mock_is_dir, mock_os_access):
        """Teste la récupération quand le chemin n'est pas accessible en lecture."""
        test_path_str = "I:/not_readable"
        mock_load_ui_settings.return_value = {"unity_dialogues_path": test_path_str}
        retrieved_path = config_manager.get_unity_dialogues_path()
        self.assertIsNone(retrieved_path)
        mock_load_ui_settings.assert_called_once()
        mock_os_access.assert_any_call(Path(test_path_str), os.W_OK)
        mock_os_access.assert_any_call(Path(test_path_str), os.R_OK)

if __name__ == '__main__':
    unittest.main() 