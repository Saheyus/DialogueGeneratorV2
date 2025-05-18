# DialogueGenerator/main_app.py
import sys
import logging
from pathlib import Path
# from PySide6.QtWidgets import QApplication # Remplacé par QAsyncApplication
from PySide6.QtWidgets import QApplication
from qasync import QEventLoop

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

try:
    # Mode package (python -m DialogueGenerator.main_app)
    from .context_builder import ContextBuilder
    from .ui.main_window import MainWindow
except ImportError:  # Lancement direct du script
    SCRIPT_DIR = Path(__file__).resolve().parent
    PROJECT_ROOT = SCRIPT_DIR.parent
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))  # Prioritaire

    # Import absolu une fois le path préparé
    from DialogueGenerator.context_builder import ContextBuilder
    from DialogueGenerator.ui.main_window import MainWindow

def main():
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[logging.StreamHandler()])

    logger = logging.getLogger(__name__) # Obtenir un logger spécifique au module

    logger.info("Démarrage de l'application DialogueGenerator...")
    app = QApplication(sys.argv)  # Création de l'application Qt standard

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