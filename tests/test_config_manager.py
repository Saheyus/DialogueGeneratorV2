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

import config_manager
from config_manager import UI_SETTINGS_FILE, load_ui_settings, save_ui_settings

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

    @patch(f'{config_manager.__name__}.save_ui_settings')
    @patch(f'{config_manager.__name__}.load_ui_settings')
    def test_set_unity_dialogues_path_new_file(self, mock_load_ui_settings, mock_save_ui_settings):
        """Teste la définition du chemin quand ui_settings.json n'existe pas ou est vide."""
        mock_load_ui_settings.return_value = {}
        
        test_path = "C:/test/path"
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
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.is_dir', return_value=False)
    def test_set_unity_dialogues_path_creates_directory(self, mock_is_dir, mock_mkdir, mock_load_ui_settings, mock_save_ui_settings):
        """Teste la création de répertoire quand le chemin n'existe pas."""
        mock_load_ui_settings.return_value = {}
        test_path = "C:/new_dir"
        
        result = config_manager.set_unity_dialogues_path(test_path)
        self.assertTrue(result)
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_save_ui_settings.assert_called_once_with({"unity_dialogues_path": test_path})

    # Tests pour la nouvelle implémentation de get_unity_dialogues_path qui utilise ui_settings.json + validation
    @patch('os.access')
    @patch('pathlib.Path.is_dir', return_value=True)
    @patch('pathlib.Path.exists', return_value=True)
    @patch(f'{config_manager.__name__}.load_ui_settings')
    def test_get_unity_dialogues_path_from_settings_success(self, mock_load_ui_settings, mock_exists, mock_is_dir, mock_os_access):
        """Teste la récupération du chemin depuis ui_settings.json avec validation complète."""
        test_path_str = "E:/valid/path"
        mock_load_ui_settings.return_value = {"unity_dialogues_path": test_path_str}
        mock_os_access.side_effect = [True, True]  # W_OK, R_OK
        
        retrieved_path = config_manager.get_unity_dialogues_path()
        
        self.assertIsNotNone(retrieved_path)
        self.assertEqual(retrieved_path, Path(test_path_str))
        mock_load_ui_settings.assert_called_once()
        mock_os_access.assert_any_call(Path(test_path_str), os.W_OK)
        mock_os_access.assert_any_call(Path(test_path_str), os.R_OK)

    @patch('os.access')
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.is_dir', return_value=True)
    @patch('pathlib.Path.exists', return_value=False)
    @patch(f'{config_manager.__name__}.load_ui_settings')
    def test_get_unity_dialogues_path_creates_configured_directory(self, mock_load_ui_settings, mock_exists, mock_is_dir, mock_mkdir, mock_os_access):
        """Teste la création du répertoire configuré s'il n'existe pas."""
        test_path_str = "E:/new/path"
        mock_load_ui_settings.return_value = {"unity_dialogues_path": test_path_str}
        mock_os_access.side_effect = [True, True]  # W_OK, R_OK après création
        
        retrieved_path = config_manager.get_unity_dialogues_path()
        
        self.assertIsNotNone(retrieved_path)
        self.assertEqual(retrieved_path, Path(test_path_str))
        mock_load_ui_settings.assert_called_once()

    @patch('os.access')
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.is_dir', return_value=True)
    @patch('pathlib.Path.exists', return_value=False)
    @patch(f'{config_manager.__name__}.load_ui_settings')
    @patch(f'{config_manager.__name__}.DEFAULT_UNITY_DIALOGUES_PATH')
    def test_get_unity_dialogues_path_uses_default_when_not_configured(self, mock_default_path, mock_load_ui_settings, mock_exists, mock_is_dir, mock_mkdir, mock_os_access):
        """Teste l'utilisation du chemin par défaut quand non configuré."""
        mock_load_ui_settings.return_value = {}  # Pas de unity_dialogues_path
        mock_default_path.exists.return_value = False
        mock_default_path.is_dir.return_value = True
        mock_os_access.side_effect = [True, True]  # W_OK, R_OK
        
        with patch.object(config_manager, 'DEFAULT_UNITY_DIALOGUES_PATH', mock_default_path):
            retrieved_path = config_manager.get_unity_dialogues_path()
        
        self.assertEqual(retrieved_path, mock_default_path)
        mock_load_ui_settings.assert_called_once()
        mock_default_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch('os.access', side_effect=[False, True])  # Pas d'écriture, mais lecture OK
    @patch('pathlib.Path.is_dir', return_value=True)
    @patch('pathlib.Path.exists', return_value=True)
    @patch(f'{config_manager.__name__}.load_ui_settings')
    def test_get_unity_dialogues_path_no_write_access(self, mock_load_ui_settings, mock_exists, mock_is_dir, mock_os_access):
        """Teste le rejet quand pas d'accès en écriture."""
        test_path_str = "E:/readonly/path"
        mock_load_ui_settings.return_value = {"unity_dialogues_path": test_path_str}
        
        retrieved_path = config_manager.get_unity_dialogues_path()
        
        self.assertIsNone(retrieved_path)
        mock_load_ui_settings.assert_called_once()

    @patch('os.access', side_effect=[True, False])  # Écriture OK, mais pas de lecture
    @patch('pathlib.Path.is_dir', return_value=True)
    @patch('pathlib.Path.exists', return_value=True)
    @patch(f'{config_manager.__name__}.load_ui_settings')
    def test_get_unity_dialogues_path_no_read_access(self, mock_load_ui_settings, mock_exists, mock_is_dir, mock_os_access):
        """Teste le rejet quand pas d'accès en lecture."""
        test_path_str = "E:/writeonly/path"
        mock_load_ui_settings.return_value = {"unity_dialogues_path": test_path_str}
        
        retrieved_path = config_manager.get_unity_dialogues_path()
        
        self.assertIsNone(retrieved_path)
        mock_load_ui_settings.assert_called_once()

    @patch('pathlib.Path.is_dir', return_value=False)
    @patch('pathlib.Path.exists', return_value=True)
    @patch(f'{config_manager.__name__}.load_ui_settings')
    def test_get_unity_dialogues_path_not_directory(self, mock_load_ui_settings, mock_exists, mock_is_dir):
        """Teste le rejet quand le chemin existe mais n'est pas un répertoire."""
        test_path_str = "E:/file.txt"
        mock_load_ui_settings.return_value = {"unity_dialogues_path": test_path_str}
        
        retrieved_path = config_manager.get_unity_dialogues_path()
        
        self.assertIsNone(retrieved_path)
        mock_load_ui_settings.assert_called_once()

    @patch('pathlib.Path.mkdir', side_effect=OSError("Permission denied"))
    @patch('pathlib.Path.exists', return_value=False)
    @patch(f'{config_manager.__name__}.load_ui_settings')
    def test_get_unity_dialogues_path_creation_fails(self, mock_load_ui_settings, mock_exists, mock_mkdir):
        """Teste le cas où la création du répertoire échoue."""
        test_path_str = "E:/cannot/create"
        mock_load_ui_settings.return_value = {"unity_dialogues_path": test_path_str}
        
        retrieved_path = config_manager.get_unity_dialogues_path()
        
        self.assertIsNone(retrieved_path)
        mock_load_ui_settings.assert_called_once()

if __name__ == '__main__':
    unittest.main() 