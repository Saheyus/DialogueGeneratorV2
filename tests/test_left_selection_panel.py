import pytest
import os

# Force le backend Qt 'offscreen' pour favoriser l'exécution en environnement headless (CI)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QListWidget, QApplication
from pytestqt.qt_compat import qt_api
from pytestqt.qtbot import QtBot
from pytestqt.exceptions import TimeoutError as QtTimeoutError


# Ajustez les imports en fonction de la structure de votre projet
try:
    from DialogueGenerator.ui.left_selection_panel import LeftSelectionPanel, CheckableListItemWidget
    from DialogueGenerator.context_builder import ContextBuilder # Pour mocker ou dummifier
except ImportError:
    import sys
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dialogue_generator_dir = os.path.dirname(script_dir) # DialogueGenerator
    project_root = os.path.dirname(dialogue_generator_dir) # Notion_Scrapper
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    if dialogue_generator_dir not in sys.path:
        sys.path.insert(0, dialogue_generator_dir)
    
    from DialogueGenerator.ui.left_selection_panel import LeftSelectionPanel, CheckableListItemWidget
    from DialogueGenerator.context_builder import ContextBuilder

# Mocks / Dummies
class DummyContextBuilder:
    def __init__(self):
        self.characters = [{"Nom": "Alice"}, {"Nom": "Bob"}, {"Nom": "Charlie"}]
        self.locations = [{"Nom": "Forest"}, {"Nom": "Cave"}]
        self.items = [{"Nom": "Sword"}, {"Nom": "Shield"}]
        self.species = []
        self.communities = []
        # ... ajoutez d'autres attributs de catégorie si LeftSelectionPanel les attend à l'init

    def get_unity_dialogues_path(self):
        return None # Pas pertinent pour ces tests
    
    def list_yarn_files(self, path, recursive):
        return [] # Pas pertinent

@pytest.fixture
def app_instance(qtbot): # Renommé pour éviter conflit avec test_app_launch
    """Crée une instance de QApplication si nécessaire."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app

@pytest.fixture
def left_panel(qtbot, app_instance):
    """Crée et retourne une instance de LeftSelectionPanel pour les tests."""
    dummy_context_builder = DummyContextBuilder()
    panel = LeftSelectionPanel(context_builder=dummy_context_builder)
    qtbot.addWidget(panel)
    # populate_all_lists est appelé dans __init__ via _setup_ui_elements et _create_category_group
    # mais les listes sont vides car DummyContextBuilder.characters etc. ne sont pas "chargés" comme des fichiers.
    # Nous allons manuellement peupler une liste pour le test de _set_checked_list_items.
    return panel

def test_set_checked_list_items(left_panel: LeftSelectionPanel, qtbot: QtBot):
    """Teste la méthode _set_checked_list_items."""
    category_to_test = "characters" # Doit correspondre à une clé dans left_panel.lists
    list_widget = left_panel.lists.get(category_to_test)

    assert list_widget is not None, f"La QListWidget pour la catégorie '{category_to_test}' n'a pas été trouvée."

    # Vider la liste au cas où elle aurait été peuplée par l'initialisation de LeftSelectionPanel
    list_widget.clear()

    # Peupler manuellement la QListWidget avec des CheckableListItemWidget pour le test
    item_names = ["Alice", "Bob", "Charlie", "Diana"]
    for name in item_names:
        item_widget = CheckableListItemWidget(name, parent=list_widget)
        q_list_item = qt_api.QtWidgets.QListWidgetItem(list_widget) # Utiliser qt_api pour QListWidgetItem
        q_list_item.setSizeHint(item_widget.sizeHint())
        list_widget.addItem(q_list_item)
        list_widget.setItemWidget(q_list_item, item_widget)
    
    assert list_widget.count() == len(item_names), "Le peuplement manuel de la liste a échoué."

    # Cas 1: Cocher "Alice" et "Charlie"
    items_to_check1 = ["Alice", "Charlie"]
    left_panel._set_checked_list_items(list_widget, items_to_check1)

    checked_after_set1 = []
    for i in range(list_widget.count()):
        q_item = list_widget.item(i)
        widget = list_widget.itemWidget(q_item)
        if widget.checkbox.isChecked():
            checked_after_set1.append(widget.text_label.text())
    
    assert sorted(checked_after_set1) == sorted(items_to_check1), "Cas 1: Les items cochés ne correspondent pas."

    # Cas 2: Cocher uniquement "Bob", les autres doivent être décochés
    items_to_check2 = ["Bob"]
    left_panel._set_checked_list_items(list_widget, items_to_check2)

    checked_after_set2 = []
    for i in range(list_widget.count()):
        q_item = list_widget.item(i)
        widget = list_widget.itemWidget(q_item)
        if widget.checkbox.isChecked():
            checked_after_set2.append(widget.text_label.text())
            
    assert sorted(checked_after_set2) == sorted(items_to_check2), "Cas 2: La mise à jour des items cochés a échoué."

    # Cas 3: Cocher un item non existant et un existant
    items_to_check3 = ["Alice", "Zorro"]
    left_panel._set_checked_list_items(list_widget, items_to_check3)
    
    checked_after_set3 = []
    for i in range(list_widget.count()):
        q_item = list_widget.item(i)
        widget = list_widget.itemWidget(q_item)
        if widget.checkbox.isChecked():
            checked_after_set3.append(widget.text_label.text())
            
    assert sorted(checked_after_set3) == sorted(["Alice"]), "Cas 3: Devrait cocher Alice et ignorer Zorro."

    # Cas 4: Liste vide pour tout décocher
    items_to_check_empty = []
    left_panel._set_checked_list_items(list_widget, items_to_check_empty)
    
    checked_after_set_empty = []
    for i in range(list_widget.count()):
        q_item = list_widget.item(i)
        widget = list_widget.itemWidget(q_item)
        if widget.checkbox.isChecked():
            checked_after_set_empty.append(widget.text_label.text())
            
    assert not checked_after_set_empty, "Cas 4: La liste vide aurait dû tout décocher." 