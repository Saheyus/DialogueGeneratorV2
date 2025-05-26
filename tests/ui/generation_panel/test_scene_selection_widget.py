import pytest
from unittest.mock import Mock, call
from PySide6.QtCore import SignalBlocker

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

def test_populate_scene_combos_and_sub_locations(widget, mock_context_builder, qtbot):
    mock_signal_region = Mock()
    mock_signal_sub_location = Mock()
    widget.scene_region_changed.connect(mock_signal_region)
    widget.scene_sub_location_changed.connect(mock_signal_sub_location)

    widget.populate_scene_combos(mock_context_builder.get_regions())
    
    expected_regions = [UIText.NONE_FEM] + sorted(["Forest", "City", "Mountain"])
    assert widget.scene_region_combo.count() == len(expected_regions)
    for i, region_name in enumerate(expected_regions):
        assert widget.scene_region_combo.itemText(i) == region_name

    # Initial sub-location should be NO_SELECTION as region is NONE_FEM
    assert widget.scene_sub_location_combo.currentText() == UIText.NO_SELECTION
    mock_signal_region.assert_not_called() # Should not emit for default UIText.NONE_FEM population
    # Sub-location might emit NO_SELECTION if it changed from an undefined state or during initial population logic
    qtbot.waitSignal(widget.scene_sub_location_changed, timeout=100, raising=False) # Allow signal to process

    # Change region to "Forest"
    with qtbot.waitSignals([widget.scene_region_changed, widget.scene_sub_location_changed], timeout=200, order="strict"):
        widget.scene_region_combo.setCurrentText("Forest")

    mock_context_builder.get_sub_locations.assert_called_with("Forest")
    expected_sub_forest = [UIText.ALL] + sorted(["Dark Woods", "Sunny Meadow"])
    assert widget.scene_sub_location_combo.count() == len(expected_sub_forest)
    for i, sub_loc_name in enumerate(expected_sub_forest):
        assert widget.scene_sub_location_combo.itemText(i) == sub_loc_name
    assert widget.scene_sub_location_combo.currentText() == UIText.ALL # Default after population for a valid region
    
    mock_signal_region.assert_called_with("Forest")
    mock_signal_sub_location.assert_called_with(UIText.ALL) # Or the first sub-location

    # Change to a region with no sub-locations (mocked if necessary, or add to map)
    mock_context_builder.get_sub_locations = Mock(side_effect=lambda region_name: {"Desert": []}.get(region_name, []))
    widget.populate_scene_combos(["Desert"]) # Re-populate to include Desert

    with qtbot.waitSignals([widget.scene_region_changed, widget.scene_sub_location_changed], timeout=200, order="strict"):
         widget.scene_region_combo.setCurrentText("Desert")
    
    assert widget.scene_sub_location_combo.currentText() == UIText.NONE_SUBLOCATION
    mock_signal_region.assert_called_with("Desert")
    mock_signal_sub_location.assert_called_with(UIText.NONE_SUBLOCATION)

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

def test_get_and_load_selected_scene_info(widget, mock_context_builder, qtbot):
    widget.populate_character_combos(mock_context_builder.get_characters_names())
    widget.populate_scene_combos(mock_context_builder.get_regions())

    initial_selection = {
        "character_a": "Alice",
        "character_b": "Bob",
        "scene_region": "Forest",
        "scene_sub_location": "Dark Woods" 
    }

    mock_signal_char_a = Mock()
    mock_signal_char_b = Mock()
    mock_signal_region = Mock()
    mock_signal_sub_loc = Mock()

    # Temporarily block signals to avoid emissions from setCurrentText before load_selection call
    # This simulates a clean load.
    # Note: load_selection itself has an _is_populating flag, but this ensures
    # the state is exactly as we set it before calling load_selection.
    
    # Connect after initial population and before setting specific values for the test
    widget.character_a_changed.connect(mock_signal_char_a)
    widget.character_b_changed.connect(mock_signal_char_b)
    widget.scene_region_changed.connect(mock_signal_region)
    widget.scene_sub_location_changed.connect(mock_signal_sub_loc)

    # Wrap signal waiting around the load_selection call
    # Signals are now emitted at the END of load_selection if values changed
    with qtbot.waitSignals([widget.character_a_changed, widget.character_b_changed, widget.scene_region_changed, widget.scene_sub_location_changed], timeout=300, order="strict", check_params_cbs=[
        lambda s: s == initial_selection["character_a"],
        lambda s: s == initial_selection["character_b"],
        lambda s: s == initial_selection["scene_region"],
        lambda s: s == initial_selection["scene_sub_location"],
    ]):
        widget.load_selection(initial_selection)


    # Verify combo box values
    assert widget.character_a_combo.currentText() == initial_selection["character_a"]
    assert widget.character_b_combo.currentText() == initial_selection["character_b"]
    assert widget.scene_region_combo.currentText() == initial_selection["scene_region"]
    # _update_sub_locations_for_region in load_selection should correctly set this
    assert widget.scene_sub_location_combo.currentText() == initial_selection["scene_sub_location"] 

    # Verify signals were called with the correct parameters
    mock_signal_char_a.assert_called_with(initial_selection["character_a"])
    mock_signal_char_b.assert_called_with(initial_selection["character_b"])
    mock_signal_region.assert_called_with(initial_selection["scene_region"])
    mock_signal_sub_loc.assert_called_with(initial_selection["scene_sub_location"])
    
    # Verify get_selected_scene_info
    retrieved_selection = widget.get_selected_scene_info()
    assert retrieved_selection == initial_selection

    # Test loading with some None values or defaults
    default_like_selection = {
        "character_a": UIText.NONE,
        "character_b": UIText.NONE,
        "scene_region": UIText.NONE_FEM,
        "scene_sub_location": UIText.NO_SELECTION # This will be the default for NONE_FEM region
    }
    
    # Reset mocks
    mock_signal_char_a.reset_mock()
    mock_signal_char_b.reset_mock()
    mock_signal_region.reset_mock()
    mock_signal_sub_loc.reset_mock()

    # Expect only sub_location to emit if chars and region are already default
    # Or all if they changed from non-default to default.
    # The signal emission logic in load_selection should handle this.
    
    # First set a non-default state to ensure load_selection causes changes
    widget.character_a_combo.setCurrentText("Alice")
    widget.character_b_combo.setCurrentText("Bob")
    widget.scene_region_combo.setCurrentText("City") # This will auto-select sub-location to ALL
    # Reset mocks again after this setup
    mock_signal_char_a.reset_mock()
    mock_signal_char_b.reset_mock()
    mock_signal_region.reset_mock()
    mock_signal_sub_loc.reset_mock()
    
    qtbot.wait(50) # Allow signals from previous setCurrentText to clear if any race

    with qtbot.waitSignals([
        widget.character_a_changed, widget.character_b_changed, 
        widget.scene_region_changed, widget.scene_sub_location_changed
    ], timeout=300, order="strict"):
        widget.load_selection(default_like_selection)

    assert widget.character_a_combo.currentText() == UIText.NONE
    assert widget.character_b_combo.currentText() == UIText.NONE
    assert widget.scene_region_combo.currentText() == UIText.NONE_FEM
    assert widget.scene_sub_location_combo.currentText() == UIText.NO_SELECTION

    mock_signal_char_a.assert_called_with(UIText.NONE)
    mock_signal_char_b.assert_called_with(UIText.NONE)
    mock_signal_region.assert_called_with(UIText.NONE_FEM)
    mock_signal_sub_loc.assert_called_with(UIText.NO_SELECTION)


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