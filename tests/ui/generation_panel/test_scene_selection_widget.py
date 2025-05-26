import pytest
from unittest.mock import Mock, call
from PySide6.QtCore import QSignalBlocker

from ui.generation_panel.scene_selection_widget import SceneSelectionWidget
from constants import UIText

@pytest.fixture
def mock_context_builder(mocker):
    builder = Mock()
    builder.get_characters_names = Mock(return_value=["Alice", "Bob", "Charlie"])
    builder.get_regions = Mock(return_value=["Forest", "City", "Mountain"])
    
    sub_locations_map = {
        "Forest": ["Dark Woods", "Sunny Meadow"],
        "City": ["Main Street", "Old Quarter"],
        "Mountain": ["Peak", "Cave"]
    }
    builder.get_sub_locations = Mock(side_effect=lambda region_name: sub_locations_map.get(region_name, []))
    return builder

@pytest.fixture
def widget(qtbot, mock_context_builder):
    # Crée le widget sans parent pour les tests unitaires de base
    # Si des interactions plus complexes avec la boucle d'événements Qt sont nécessaires,
    # qtbot.addWidget peut être utilisé, mais pour l'instant, une instanciation directe suffit.
    w = SceneSelectionWidget(context_builder=mock_context_builder)
    # qtbot.addWidget(w) # Décommenter si des tests d'interaction UI plus poussés sont ajoutés
    return w

def test_scene_selection_widget_initialization(widget, mock_context_builder):
    """Test basic initialization and that combos are initially empty or have default text but no data."""
    assert widget is not None
    assert widget.character_a_combo.count() == 0 # Avant peuplement
    assert widget.character_b_combo.count() == 0 # Avant peuplement
    assert widget.scene_region_combo.count() == 0 # Avant peuplement
    assert widget.scene_sub_location_combo.count() == 1 # Devrait avoir UIText.NO_SELECTION

def test_populate_character_combos(widget, mock_context_builder):
    widget.populate_character_combos(mock_context_builder.get_characters_names())
    
    expected_chars = [UIText.NONE] + sorted(["Alice", "Bob", "Charlie"])
    assert widget.character_a_combo.count() == len(expected_chars)
    assert widget.character_b_combo.count() == len(expected_chars)
    for i, char_name in enumerate(expected_chars):
        assert widget.character_a_combo.itemText(i) == char_name
        assert widget.character_b_combo.itemText(i) == char_name
    
    # Test signal emission on population if a value was already set (and different from default)
    # This requires a more complex setup or direct call to setCurrentText then populate
    # For now, we assume populate sets default if nothing was there.

def test_swap_characters(widget, mock_context_builder, qtbot):
    widget.populate_character_combos(mock_context_builder.get_characters_names())
    widget.character_a_combo.setCurrentText("Alice")
    widget.character_b_combo.setCurrentText("Bob")

    mock_signal_a = Mock()
    mock_signal_b = Mock()
    widget.character_a_changed.connect(mock_signal_a)
    widget.character_b_changed.connect(mock_signal_b)

    with qtbot.waitSignals([widget.character_a_changed, widget.character_b_changed], timeout=100, order="strict"):
        widget.swap_characters_button.click()

    assert widget.character_a_combo.currentText() == "Bob"
    assert widget.character_b_combo.currentText() == "Alice"
    mock_signal_a.assert_called_with("Bob")
    mock_signal_b.assert_called_with("Alice")

def test_edge_case_empty_context_data(widget, mock_context_builder, qtbot):
    """Test behavior when context builder returns empty lists."""
    mock_context_builder.get_characters_names = Mock(return_value=[])
    mock_context_builder.get_regions = Mock(return_value=[])
    mock_context_builder.get_sub_locations = Mock(return_value=[])

    widget.populate_character_combos([])
    assert widget.character_a_combo.count() == 1 # UIText.NONE
    assert widget.character_a_combo.currentText() == UIText.NONE
    
    widget.populate_scene_combos([])
    assert widget.scene_region_combo.count() == 1 # UIText.NONE_FEM
    assert widget.scene_region_combo.currentText() == UIText.NONE_FEM
    assert widget.scene_sub_location_combo.currentText() == UIText.NO_SELECTION # Due to NONE_FEM region

    # Test load_selection with empty data scenario
    selection = {
        "character_a": "NonExistent", # Should default to NONE
        "character_b": "NonExistent2",# Should default to NONE
        "scene_region": "NonExistentRegion", # Should default to NONE_FEM
        "scene_sub_location": "NonExistentSub" # Should default to NO_SELECTION
    }
    widget.load_selection(selection)
    retrieved = widget.get_selected_scene_info()
    assert retrieved["character_a"] == UIText.NONE
    assert retrieved["character_b"] == UIText.NONE
    assert retrieved["scene_region"] == UIText.NONE_FEM
    assert retrieved["scene_sub_location"] == UIText.NO_SELECTION 