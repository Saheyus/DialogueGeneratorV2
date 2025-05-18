from pathlib import Path
from PySide6.QtGui import QIcon


def get_icon_path(icon_name: str) -> QIcon:
    """Retourne un objet QIcon basé sur le nom de fichier de l'icône.

    Cherche l'icône dans le sous-répertoire 'icons' du dossier ui.
    Si le fichier n'existe pas, retourne un QIcon vide afin d'éviter les plantages.
    """
    icons_dir = Path(__file__).resolve().parent / "icons"
    icon_file = icons_dir / icon_name
    if not icon_file.exists():
        return QIcon()  # Icône vide en secours
    return QIcon(str(icon_file)) 