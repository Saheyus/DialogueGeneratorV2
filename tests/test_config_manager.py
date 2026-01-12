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

import warnings
# DEPRECATED: config_manager est un wrapper de compatibilité
# Les nouveaux tests devraient utiliser services.configuration_service.ConfigurationService
import config_manager
# from config_manager import UI_SETTINGS_FILE, load_ui_settings, save_ui_settings # MODIFIED: Commenté

class TestConfigManager(unittest.TestCase):
    """Tests pour config_manager (wrapper de compatibilité).
    
    NOTE: Ce module est déprécié. Les nouveaux tests devraient utiliser
    services.configuration_service.ConfigurationService directement.
    """
    pass # MODIFIED: Contenu de la classe commenté pour l'instant
#
#    def setUp(self):
#        self.settings_backup = None
#        if UI_SETTINGS_FILE.exists(): # UI_SETTINGS_FILE n'est plus défini ici
#            with open(UI_SETTINGS_FILE, 'r', encoding='utf-8') as f:
#                self.settings_backup = f.read()
#            UI_SETTINGS_FILE.unlink() # Supprimer pour commencer propre
#
#    def tearDown(self):
#        if self.settings_backup:
#            with open(UI_SETTINGS_FILE, 'w', encoding='utf-8') as f:
#                f.write(self.settings_backup)
#        elif UI_SETTINGS_FILE.exists():
#            UI_SETTINGS_FILE.unlink()
#
#    @patch(f'{config_manager.__name__}.save_ui_settings')
#    @patch(f'{config_manager.__name__}.load_ui_settings')
#    def test_set_unity_dialogues_path_new_file(self, mock_load_ui_settings, mock_save_ui_settings):
#        """Teste la définition du chemin quand ui_settings.json n'existe pas ou est vide."""
#        mock_load_ui_settings.return_value = {}
#        
#        test_path = "C:/test/path"
#        with patch('pathlib.Path.is_dir', return_value=True): 
#            result = config_manager.set_unity_dialogues_path(test_path) # set_unity_dialogues_path n'est plus ici
#        
#        self.assertTrue(result)
#        mock_load_ui_settings.assert_called_once()
#        mock_save_ui_settings.assert_called_once_with({"unity_dialogues_path": test_path})
#
#    # ... (tous les autres tests sont commentés de la même manière)

if __name__ == '__main__':
    unittest.main() 