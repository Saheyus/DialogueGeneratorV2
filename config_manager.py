import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# MODIFIÉ: Constantes UI_SETTINGS_FILE et DEFAULT_UNITY_DIALOGUES_PATH supprimées.
# Elles sont maintenant dans ConfigurationService.

# MODIFIÉ: Fonctions load_ui_settings, save_ui_settings, get_unity_dialogues_path, set_unity_dialogues_path supprimées.
# Leur logique est maintenant dans ConfigurationService.

def list_yarn_files(dialogues_base_path: Path, recursive: bool = False) -> List[Path]:
    """
    Lists .yarn files in the specified Unity dialogues path.

    Args:
        dialogues_base_path (Path): The base path to search for .yarn files.
        recursive (bool): If True, searches recursively in subdirectories.
                          Defaults to False (searches only in the root of dialogues_base_path).

    Returns:
        List[Path]: A list of Path objects for each .yarn file found.
    """
    if not dialogues_base_path or not dialogues_base_path.is_dir():
        # MODIFIÉ: Utiliser logger au lieu de print pour les erreurs/warnings.
        logger.error(f"Cannot list .yarn files, path is invalid or not a directory: {dialogues_base_path}")
        return []

    pattern = "*.yarn"
    if recursive:
        pattern = "**/*.yarn" 
    
    try:
        yarn_files = list(dialogues_base_path.glob(pattern))
        return yarn_files
    except Exception as e:
        logger.error(f"Error listing .yarn files in {dialogues_base_path}: {e}")
        return []

def read_yarn_file_content(file_path: Path) -> Optional[str]:
    """
    Reads the content of a specified .yarn file.

    Args:
        file_path (Path): The Path object pointing to the .yarn file.

    Returns:
        Optional[str]: The content of the file as a string, or None if an error occurs.
    """
    if not file_path or not file_path.is_file():
        logger.error(f"Cannot read file, path is invalid or not a file: {file_path}")
        return None
    
    try:
        content = file_path.read_text(encoding="utf-8")
        return content
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None

if __name__ == "__main__":
    # Le bloc __main__ ici référençait les fonctions supprimées.
    # Il doit être supprimé ou adapté pour tester list_yarn_files/read_yarn_file_content si besoin.
    # Pour l'instant, je le commente pour éviter les erreurs.
    pass
    # print(f"Config manager - Ce module contient maintenant des utilitaires de fichiers Yarn.")
    # # Exemple de test pour list_yarn_files (nécessite un chemin valide)
    # # test_path = Path("./some_test_yarn_directory") # Créez ce répertoire avec des fichiers .yarn pour tester
    # # if test_path.is_dir():
    # #     print(f"\n--- Testing list_yarn_files (non-recursive) in {test_path} ---")
    # #     yarn_files_in_root = list_yarn_files(test_path, recursive=False)
    # #     # ... (suite des tests comme avant)
    # # else:
    # #     print(f"Pour tester list_yarn_files, créez un dossier de test: {test_path}") 