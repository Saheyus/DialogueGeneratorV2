"""Permet de lancer le module DialogueGenerator directement avec `python -m DialogueGenerator`."""

import sys
import os

# Assurer la gestion correcte des imports, similaire à main_app.py
# Si lancé avec `python -m DialogueGenerator`, `.` est DialogueGenerator.
# Les imports relatifs dans main_app devraient fonctionner.

try:
    from .main_app import main
except ImportError:
    # Ce fallback est moins probable ici si lancé avec -m,
    # mais par cohérence avec les règles d'import du projet.
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) # Notion_Scrapper
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    
    # Tenter à nouveau l'import qui devrait maintenant fonctionner si PROJECT_ROOT est la clé
    from main_app import main

if __name__ == "__main__":
    main() 