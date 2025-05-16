# DialogueGenerator/main_app.py
import sys
from PySide6.QtWidgets import QApplication

from context_builder import ContextBuilder
from ui.main_window import MainWindow

def main():
    """Point d'entrée principal de l'application Dialogue Generator."""
    app = QApplication(sys.argv)
    
    print("Initialisation du ContextBuilder...")
    context_builder = ContextBuilder()
    # Utiliser les chemins par défaut qui sont relatifs à l'emplacement de context_builder.py
    # Étant donné que main_app.py est dans le même dossier que context_builder.py,
    # les chemins relatifs ../GDD et ../import devraient fonctionner correctement.
    context_builder.load_gdd_files() 
    print("ContextBuilder initialisé.")

    print("Initialisation de la MainWindow...")
    window = MainWindow(context_builder=context_builder)
    window.show() # La méthode show() est héritée de QMainWindow
    print("MainWindow affichée.")

    sys.exit(app.exec())

if __name__ == '__main__':
    main() 