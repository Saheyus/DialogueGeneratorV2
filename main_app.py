# DialogueGenerator/main_app.py
"""
⚠️ DÉPRÉCIÉ : Cette interface desktop PySide6 est dépréciée.

Utiliser l'interface web React à la place :
    npm run dev

Cette interface est maintenue uniquement pour compatibilité mais ne doit plus être utilisée.
"""
import sys
import logging
import os
import warnings
from pathlib import Path
from datetime import datetime
# from PySide6.QtWidgets import QApplication # Remplacé par QAsyncApplication
from PySide6.QtWidgets import QApplication, QMessageBox
from qasync import QEventLoop
from constants import UIText, FilePaths, Defaults

# -------------------------------------------------------------
# Gestion des imports selon le mode d'exécution
# -------------------------------------------------------------
# 1. Exécution recommandée :
#       python -m DialogueGenerator.main_app
#    -> Les imports relatifs fonctionnent.
# 2. Exécution directe :
#       python DialogueGenerator/main_app.py
#    -> self-package inconnu, les imports relatifs échouent.
#
# Le bloc try/except ci-dessous assure la compatibilité :
#   • tente d'abord l'import relatif (cas 1)
#   • en cas d'échec, ajoute le dossier parent du package au PYTHONPATH
#     puis fait un import absolu (cas 2)
# -------------------------------------------------------------

# Simplification pour imports absolus directs, en supposant que DialogueGenerator est dans PYTHONPATH
from context_builder import ContextBuilder
from ui.main_window import MainWindow

def _is_debug_enabled() -> bool:
    """Return True when debug logging should be enabled (via environment variable)."""
    value = os.getenv("DIALOGUEGEN_DEBUG", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def configure_logging(debug: bool) -> None:
    """Configure root logging (file + console) exactly once for the application."""
    logs_dir = Path(os.path.dirname(__file__)).resolve().parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_filename = logs_dir / (datetime.now().strftime("%Y-%m-%d") + ".log")

    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(str(log_filename), encoding="utf-8"),
            logging.StreamHandler(),
        ],
        # Ensure this config actually applies even if something configured logging earlier.
        force=True,
    )

def main():
    configure_logging(debug=_is_debug_enabled())
    logger = logging.getLogger(__name__) # Obtenir un logger spécifique au module

    # ⚠️ Avertissement de dépréciation
    deprecation_warning = (
        "⚠️ DÉPRÉCIÉ : L'interface desktop PySide6 est dépréciée.\n\n"
        "Utiliser l'interface web React à la place :\n"
        "  npm run dev\n\n"
        "Cette interface est maintenue uniquement pour compatibilité."
    )
    warnings.warn(deprecation_warning, DeprecationWarning, stacklevel=2)
    logger.warning("⚠️ DÉPRÉCIÉ : Interface desktop PySide6 dépréciée. Utiliser 'npm run dev' pour l'interface web.")

    logger.info("Démarrage de l'application DialogueGenerator...")
    app = QApplication(sys.argv)  # Création de l'application Qt standard
    
    # Afficher un message box d'avertissement (une seule fois au démarrage)
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle("Interface Dépréciée")
    msg.setText("⚠️ Interface Desktop Dépréciée")
    msg.setInformativeText(
        "Cette interface desktop PySide6 est dépréciée.\n\n"
        "Utiliser l'interface web React à la place :\n"
        "  npm run dev\n\n"
        "L'application continuera de fonctionner mais cette interface n'est plus maintenue activement."
    )
    msg.setStandardButtons(QMessageBox.Ok)
    msg.exec()

    logger.info("Initialisation du ContextBuilder...")
    context_builder_instance = ContextBuilder()
    logger.info("Chargement des fichiers GDD par ContextBuilder...")
    context_builder_instance.load_gdd_files()
    logger.info("ContextBuilder initialisé et fichiers GDD chargés.")

    logger.info("Initialisation de la MainWindow...")
    main_application_window = MainWindow(context_builder_instance)
    main_application_window.show()
    logger.info("MainWindow affichée.")

    # Intégration de asyncio avec Qt via qasync
    loop = QEventLoop(app)
    import asyncio as _asyncio
    _asyncio.set_event_loop(loop)

    # Lancement de la boucle d'évènements intégrée Qt + asyncio
    with loop:
        logger.info("Entrée dans la boucle d'événements principale (loop.run_forever()).")
        loop.run_forever()
        logger.info("Sortie de la boucle d'événements principale (loop.run_forever()).")

    logger.info("Application terminée.")
    sys.exit(0)

if __name__ == "__main__":
    main() 