import os
# Force le backend Qt 'offscreen' pour favoriser l'exécution en environnement headless (CI)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from pytestqt.qt_compat import qt_api
from pytestqt.qtbot import QtBot
from pytestqt.exceptions import TimeoutError as QtTimeoutError

# Ajustez les imports en fonction de la structure de votre projet
# Il est possible que vous deviez ajouter DialogueGenerator au PYTHONPATH ou ajuster les imports relatifs
try:
    # Mode package (python -m DialogueGenerator.main_app)
    from DialogueGenerator.main_app import MainWindow # main_app n'exporte pas directement MainWindow, mais l'utilise
    from DialogueGenerator.ui.main_window import MainWindow as ActualMainWindow # On importe la classe directement
    from DialogueGenerator.context_builder import ContextBuilder
    from DialogueGenerator.ui.left_selection_panel import LeftSelectionPanel
    from DialogueGenerator.ui.details_panel import DetailsPanel
    # from DialogueGenerator.config_manager import ConfigManager # Module, pas une classe à instancier comme ça
    from DialogueGenerator import config_manager # Importer le module
except ImportError:
    # Tentative d'import relatif si exécuté comme partie d'un package non installé
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__)) # DialogueGenerator/tests
    dialogue_generator_dir = os.path.dirname(current_dir) # DialogueGenerator
    project_root = os.path.dirname(dialogue_generator_dir) # Notion_Scrapper
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    if dialogue_generator_dir not in sys.path:
        sys.path.insert(0, dialogue_generator_dir)

    from DialogueGenerator.ui.main_window import MainWindow as ActualMainWindow
    from DialogueGenerator.context_builder import ContextBuilder
    from DialogueGenerator.ui.left_selection_panel import LeftSelectionPanel
    from DialogueGenerator.ui.details_panel import DetailsPanel
    from DialogueGenerator import config_manager

@pytest.fixture
def app(qtbot: QtBot, monkeypatch):
    """Crée et retourne l'instance principale de l'application."""
    
    # S'assurer que config_manager utilise les bons chemins si nécessaire
    # Pour ces tests, on suppose que les fichiers de config par défaut sont présents et valides
    # Si les tests modifiaient la config, il faudrait mocker config_manager ou utiliser des fichiers temporaires.
    # Ici, context_config.json et ui_settings.json sont lus par les modules eux-mêmes.

    # Similaire à main_app.py
    context_builder_instance = ContextBuilder() # Utilise config_manager en interne
    # Il faut s'assurer que les chemins dans context_config.json pointent vers des fichiers GDD valides pour le test.
    # Par exemple, si les chemins sont relatifs, ils doivent l'être par rapport à la racine du projet.
    # config.txt (lu par config_manager) doit être à la racine de Notion_Scrapper.
    
    # Pour que context_builder.load_gdd_files() fonctionne, il faut s'assurer que
    # les chemins dans DialogueGenerator/context_config.json sont corrects
    # et que les fichiers GDD existent.
    # Vérifions si la config principale (config.txt) est bien à la racine du projet
    # pour que config_manager.get_project_root() fonctionne correctement.
    
    # Monkeypatch get_config_file_path pour pointer vers le fichier config.txt à la racine
    # de Notion_Scrapper si le test est lancé depuis un autre répertoire.
    # Cela assure que config_manager.PROFILE_CONFIG_PATH est correct.
    # Si pytest est lancé depuis Notion_Scrapper, ceci n'est pas strictement nécessaire.
    # project_root_path = Path(project_root) # project_root est défini dans le bloc ImportError
    # monkeypatch.setattr(config_manager, 'get_config_file_path', lambda: project_root_path / 'config.txt')


    # Assurez-vous que les fichiers de configuration référencés par context_config.json sont disponibles
    # et que context_config.json lui-même est au bon endroit.
    # Par défaut: DialogueGenerator/context_config.json
    # Ce fichier est lu par ContextBuilder.
    try:
        context_builder_instance.load_gdd_files()
    except FileNotFoundError as e:
        pytest.fail(f"Un fichier GDD n'a pas été trouvé lors du chargement. Vérifiez context_config.json et les chemins. Erreur: {e}")
    except Exception as e:
        pytest.fail(f"Erreur lors du chargement des fichiers GDD par ContextBuilder: {e}")

    main_window = ActualMainWindow(context_builder=context_builder_instance)
    qtbot.addWidget(main_window)
    main_window.show()
    # Pas besoin d'attendre isActiveWindow en mode offscreen ; on passe directement

    # Attendre que les listes soient peuplées (si asynchrone ou post-init)
    # LeftSelectionPanel.populate_all_lists est appelé dans MainWindow.load_initial_data
    # qui est appelé dans MainWindow.__init__
    # On peut ajouter un waitUntil pour s'assurer que les listes sont remplies.
    left_panel = main_window.findChild(LeftSelectionPanel)
    assert left_panel is not None, "LeftSelectionPanel n'a pas été trouvé."
    
    def lists_are_ready():
        # Vérifie au moins une liste, en supposant que les autres suivent
        # ou que populate_all_lists est atomique pour le chargement GDD.
        # On vérifie "characters" car c'est une catégorie principale.
        char_list = left_panel.lists.get("characters")
        return char_list is not None and char_list.count() > 0

    try:
        qtbot.waitUntil(lists_are_ready, timeout=10000) # Augmenter le timeout si les fichiers GDD sont gros
    except QtTimeoutError:
        pytest.fail("Les listes dans LeftSelectionPanel n'ont pas été peuplées dans le délai imparti.")

    return main_window

def test_app_opens(app: ActualMainWindow):
    """Vérifie que la fenêtre principale de l'application s'ouvre."""
    assert app.isVisible()
    assert app.windowTitle() == "DialogueGenerator IA - Context Builder" # Corrigé selon main_window.py

def test_lists_are_populated(app: ActualMainWindow, qtbot: QtBot):
    """Vérifie que les listes dans LeftSelectionPanel sont peuplées."""
    left_panel = app.findChild(LeftSelectionPanel)
    assert left_panel is not None, "LeftSelectionPanel n'a pas été trouvé."

    # Les listes sont stockées dans un dictionnaire `lists`
    assert left_panel.lists["characters"].count() > 0, "La liste des personnages est vide."
    assert left_panel.lists["locations"].count() > 0, "La liste des lieux est vide."
    assert left_panel.lists["items"].count() > 0, "La liste des objets est vide."
    # D'autres listes peuvent être testées au besoin.


def test_details_panel_updates_on_click(app: ActualMainWindow, qtbot: QtBot):
    """Vérifie que le DetailsPanel se met à jour après un clic sur un item."""
    left_panel = app.findChild(LeftSelectionPanel)
    details_panel = app.findChild(DetailsPanel)

    assert left_panel is not None, "LeftSelectionPanel n'a pas été trouvé."
    assert details_panel is not None, "DetailsPanel n'a pas été trouvé."

    character_list_widget = left_panel.lists.get("characters")
    assert character_list_widget is not None, "La QListWidget pour 'characters' n'a pas été trouvée."

    if character_list_widget.count() == 0:
        pytest.skip("La liste des personnages est vide, impossible de tester le clic.")
        return

    # Cliquer sur le premier item de la liste des personnages
    # Les items peuvent être des QListWidgetItem ou des QWidget (CheckableListItemWidget)
    # On doit obtenir le QListWidgetItem pour visualItemRect
    
    # Tentative de clic sur le premier item, qu'il soit un widget wrapper ou un QListWidgetItem simple
    # En général, LeftSelectionPanel utilise CheckableListItemWidget qui sont mis via setItemWidget.
    # Donc, item(0) retourne le QListWidgetItem, et list.itemWidget(list.item(0)) retourne le widget personnalisé.
    
    list_item = character_list_widget.item(0) # Ceci est le QListWidgetItem
    assert list_item is not None, "Le premier QListWidgetItem de la liste des personnages est None."

    # On clique sur le viewport de la QListWidget aux coordonnées de l'item.
    rect = character_list_widget.visualItemRect(list_item)
    qtbot.mouseClick(character_list_widget.viewport(), qt_api.QtCore.Qt.MouseButton.LeftButton, pos=rect.center())
    
    def check_details_populated():
        # La méthode update_details dans DetailsPanel rend details_text_edit visible
        # et le remplit, ou remplit le groupe yarn.
        # Pour un personnage, c'est details_text_edit qui doit être visible et non vide.
        assert details_panel.details_text_edit.isVisible(), "details_text_edit devrait être visible après clic sur personnage."
        assert details_panel.details_text_edit.toPlainText() != "", "DetailsPanel (details_text_edit) est vide après le clic sur un personnage."
        # On peut aussi vérifier que la section Yarn est cachée
        assert not details_panel.yarn_display_group.isVisible(), "yarn_display_group ne devrait pas être visible pour un personnage."
        return True

    try:
        qtbot.waitUntil(check_details_populated, timeout=5000)
    except QtTimeoutError:
        # Pour aider au débogage si ça échoue :
        print(f"Debug Info: details_panel.details_text_edit.isVisible() = {details_panel.details_text_edit.isVisible()}")
        print(f"Debug Info: details_panel.details_text_edit.toPlainText() = '{details_panel.details_text_edit.toPlainText()}'")
        print(f"Debug Info: details_panel.yarn_display_group.isVisible() = {details_panel.yarn_display_group.isVisible()}")
        current_item_text = list_item.text() # Ou le texte du widget si c'est un CheckableListItemWidget
        if character_list_widget.itemWidget(list_item):
             current_item_text = character_list_widget.itemWidget(list_item).text_label.text()
        print(f"Debug Info: Clic simulé sur l'item: {current_item_text}")
        pytest.fail("Le DetailsPanel n'a pas été peuplé correctement après le clic sur un personnage dans le délai imparti.")

# Pour exécuter ces tests:
# 1. Assurez-vous que pytest et pytest-qt sont installés.
# 2. Naviguez vers le dossier Notion_Scrapper (racine du projet) dans votre terminal.
# 3. Exécutez: pytest DialogueGenerator/tests/test_app_launch.py
#
# Notes importantes pour que les tests fonctionnent:
# - Les chemins vers context_config.json (dans DialogueGenerator) et config.txt (à la racine de Notion_Scrapper)
#   doivent être corrects et les fichiers accessibles.
# - Les fichiers JSON pointés par context_config.json (GDD, import, etc.) doivent exister et être accessibles.
#   Leurs chemins dans context_config.json sont relatifs à la racine du projet (Notion_Scrapper).
# - La logique de chargement des données dans `ConfigManager` et `ContextBuilder` doit fonctionner correctement.
# - Les noms des widgets et des clés de catégorie doivent correspondre.
# - Il est crucial que l'environnement d'exécution des tests (PYTHONPATH) permette les imports.
#   Lancer pytest depuis la racine du projet (Notion_Scrapper) est recommandé.
# - Assurez-vous que les fichiers GDD JSON ne sont pas vides pour les catégories testées.
#   Si, par exemple, `GDD/categories/characters.json` est vide, le test `test_lists_are_populated` pour les personnages échouera.
#   Et `test_details_panel_updates_on_click` sera skippé.
# - Les tests supposent que les fichiers de configuration du GDD (pointés par context_config.json)
#   contiennent des données pour les catégories "characters", "locations", "items", "species", "communities".
#   Sinon, les assertions sur `count() > 0` échoueront.

# Ajout pour clarifier l'import de ActualMainWindow vs MainWindow de main_app
# Dans main_app.py, MainWindow est la classe de ui.main_window, pas le module lui-même.
# Le test doit importer et utiliser la classe directement.
# from DialogueGenerator.ui.main_window import MainWindow as ActualMainWindow # Déjà fait plus haut.
# ... (le reste du fichier est identique)
# Dans la fixture app :
# main_window = ActualMainWindow(context_builder=context_builder_instance) # Déjà corrigé plus haut.
# Dans les type hints des tests :
# def test_app_opens(app: ActualMainWindow): # Déjà corrigé plus haut.
# def test_lists_are_populated(app: ActualMainWindow, qtbot: QtBot): # Déjà corrigé plus haut.
# def test_details_panel_updates_on_click(app: ActualMainWindow, qtbot: QtBot): # Déjà corrigé plus haut.

# Ajout pour clarifier l'import de ActualMainWindow vs MainWindow de main_app
# Dans main_app.py, MainWindow est la classe de ui.main_window, pas le module lui-même.
# Le test doit importer et utiliser la classe directement.
# from DialogueGenerator.ui.main_window import MainWindow as ActualMainWindow # Déjà fait plus haut.
# ... (le reste du fichier est identique)
# Dans la fixture app :
# main_window = ActualMainWindow(context_builder=context_builder_instance) # Déjà corrigé plus haut.
# Dans les type hints des tests :
# def test_app_opens(app: ActualMainWindow): # Déjà corrigé plus haut.
# def test_lists_are_populated(app: ActualMainWindow, qtbot: QtBot): # Déjà corrigé plus haut.
# def test_details_panel_updates_on_click(app: ActualMainWindow, qtbot: QtBot): # Déjà corrigé plus haut. 