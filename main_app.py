# DialogueGenerator/main_app.py
import sys
from PySide6.QtWidgets import QApplication
import logging # Added for logging configuration

from context_builder import ContextBuilder
from ui.main_window import MainWindow

def main():
    """Point d'entrée principal de l'application Dialogue Generator."""
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[logging.StreamHandler(sys.stdout)]) # Ensure logs go to stdout
    
    logger = logging.getLogger(__name__) # Get a logger for this module

    app = QApplication(sys.argv)
    
    logger.info("Initialisation du ContextBuilder...") # Changed from print
    context_builder = ContextBuilder()
    # Utiliser les chemins par défaut qui sont relatifs à l'emplacement de context_builder.py
    # Étant donné que main_app.py est dans le même dossier que context_builder.py,
    # les chemins relatifs ../GDD et ../import devraient fonctionner correctement.
    context_builder.load_gdd_files() 
    logger.info("ContextBuilder initialisé.") # Changed from print

    logger.info("Initialisation de la MainWindow...") # Changed from print
    window = MainWindow(context_builder=context_builder)
    window.show() # La méthode show() est héritée de QMainWindow
    logger.info("MainWindow affichée.") # Changed from print

    sys.exit(app.exec())

if __name__ == '__main__':
    main() 