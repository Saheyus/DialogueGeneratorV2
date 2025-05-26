from PySide6.QtWidgets import (QWidget, QGroupBox, QGridLayout, QLabel, QComboBox, QPushButton, QStyle, QVBoxLayout)
from PySide6.QtCore import Qt, Signal, QSize
import logging
from constants import UIText, FilePaths, Defaults
from typing import Optional

logger = logging.getLogger(__name__)

class SceneSelectionWidget(QWidget):
    character_a_changed = Signal(str)
    character_b_changed = Signal(str)
    scene_region_changed = Signal(str)
    scene_sub_location_changed = Signal(str)

    def __init__(self, context_builder, parent=None):
        super().__init__(parent)
        self.context_builder = context_builder
        self._is_populating = False # Flag to prevent signals during population
        self._init_ui()

    def _init_ui(self):
        self.group_box = QGroupBox("Scène Principale")
        
        grid_layout = QGridLayout(self.group_box)
        row = 0

        grid_layout.addWidget(QLabel("Personnage A:"), row, 0)
        self.character_a_combo = QComboBox()
        self.character_a_combo.setToolTip("Sélectionnez le premier personnage principal de la scène.")
        self.character_a_combo.currentTextChanged.connect(self._on_character_a_changed)
        grid_layout.addWidget(self.character_a_combo, row, 1)
        row += 1

        grid_layout.addWidget(QLabel("Personnage B:"), row, 0)
        self.character_b_combo = QComboBox()
        self.character_b_combo.setToolTip("Sélectionnez le second personnage principal de la scène (optionnel).")
        self.character_b_combo.currentTextChanged.connect(self._on_character_b_changed)
        grid_layout.addWidget(self.character_b_combo, row, 1)
        row += 1

        self.swap_characters_button = QPushButton()
        self.swap_characters_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ToolBarHorizontalExtensionButton))
        self.swap_characters_button.setToolTip("Échanger Personnage A et Personnage B")
        self.swap_characters_button.setFixedSize(QSize(28, 28))
        self.swap_characters_button.clicked.connect(self._perform_swap_and_emit)
        grid_layout.addWidget(self.swap_characters_button, 0, 2, 2, 1, Qt.AlignmentFlag.AlignCenter)

        grid_layout.addWidget(QLabel("Région de la Scène:"), row, 0)
        self.scene_region_combo = QComboBox()
        self.scene_region_combo.setToolTip("Sélectionnez la région où se déroule la scène.")
        self.scene_region_combo.currentTextChanged.connect(self._on_scene_region_changed_internal_and_emit)
        grid_layout.addWidget(self.scene_region_combo, row, 1, 1, 2)
        row += 1

        grid_layout.addWidget(QLabel("Sous-Lieu (optionnel):"), row, 0)
        self.scene_sub_location_combo = QComboBox()
        self.scene_sub_location_combo.setToolTip("Sélectionnez le sous-lieu plus spécifique (si applicable).")
        self.scene_sub_location_combo.currentTextChanged.connect(self._on_scene_sub_location_changed)
        grid_layout.addWidget(self.scene_sub_location_combo, row, 1, 1, 2)
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.group_box)
        self.setLayout(main_layout)

    def _on_character_a_changed(self, text: str):
        if not self._is_populating:
            self.character_a_changed.emit(text)

    def _on_character_b_changed(self, text: str):
        if not self._is_populating:
            self.character_b_changed.emit(text)

    def _on_scene_sub_location_changed(self, text: str):
        if not self._is_populating:
            self.scene_sub_location_changed.emit(text)
            
    def populate_character_combos(self, character_names: list):
        logger.debug(f"Peuplement des combos personnages avec: {character_names}")
        self._is_populating = True
        
        current_char_a = self.character_a_combo.currentText()
        current_char_b = self.character_b_combo.currentText()
        
        self.character_a_combo.clear()
        self.character_b_combo.clear()
        
        all_chars_with_none = [UIText.NONE] + sorted(list(set(character_names))) # Ensure unique and sorted
        self.character_a_combo.addItems(all_chars_with_none)
        self.character_b_combo.addItems(all_chars_with_none)
        
        self.character_a_combo.setCurrentText(current_char_a if current_char_a in all_chars_with_none else UIText.NONE)
        self.character_b_combo.setCurrentText(current_char_b if current_char_b in all_chars_with_none else UIText.NONE)
            
        self._is_populating = False
        # Emit initial state if different from default (NONE)
        if self.character_a_combo.currentText() != UIText.NONE:
             self.character_a_changed.emit(self.character_a_combo.currentText())
        if self.character_b_combo.currentText() != UIText.NONE:
             self.character_b_changed.emit(self.character_b_combo.currentText())
        logger.debug("Combos personnages peuplés.")

    def populate_scene_combos(self, region_names: list):
        logger.debug(f"Peuplement combo régions avec: {region_names}")
        self._is_populating = True
        
        current_region = self.scene_region_combo.currentText()
        self.scene_region_combo.clear()
        all_regions_with_none = [UIText.NONE_FEM] + sorted(list(set(region_names))) # Ensure unique and sorted
        self.scene_region_combo.addItems(all_regions_with_none)
        
        selected_region = current_region if current_region in all_regions_with_none else UIText.NONE_FEM
        self.scene_region_combo.setCurrentText(selected_region)
        
        self._is_populating = False # Allow _on_scene_region_changed_internal_and_emit to emit
        self._update_sub_locations_for_region(selected_region, is_initial_population=True) # Update sub-locations based on new region list
        if selected_region != UIText.NONE_FEM: # Emit if not default
            self.scene_region_changed.emit(selected_region)


        logger.debug("Combo régions peuplé.")

    def _on_scene_region_changed_internal_and_emit(self, region_name: str):
        if self._is_populating:
            return
        logger.debug(f"Changement de région détecté: {region_name}")
        self._update_sub_locations_for_region(region_name)
        self.scene_region_changed.emit(region_name) # Emit external signal

    def _update_sub_locations_for_region(self, region_name: str, stored_sub_location: Optional[str] = None, is_initial_population: bool = False):
        logger.debug(f"Mise à jour des sous-lieux pour la région: {region_name}. Stored sub_loc: {stored_sub_location}")
        self._is_populating = True # Block sub_location_changed during this internal update
        
        previous_sub_location = self.scene_sub_location_combo.currentText()
        self.scene_sub_location_combo.clear()
        
        items_to_add = [UIText.NO_SELECTION] # Default if no region or error
        is_enabled = False
        
        if region_name and region_name != UIText.NONE_FEM and region_name != UIText.NO_SELECTION:
            try:
                sub_locations = sorted(list(set(self.context_builder.get_sub_locations(region_name)))) # Ensure unique
                if not sub_locations:
                    items_to_add = [UIText.NONE_SUBLOCATION]
                else:
                    items_to_add = [UIText.ALL] + sub_locations
                is_enabled = True
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des sous-lieux pour {region_name}: {e}", exc_info=True)
                items_to_add = [UIText.ERROR_PREFIX + "Err. Charg."]
        
        self.scene_sub_location_combo.addItems(items_to_add)
        self.scene_sub_location_combo.setEnabled(is_enabled)
        
        # Determine sub-location to set
        sub_location_to_set = items_to_add[0] # Default to first item (e.g., NO_SELECTION, NONE_SUBLOCATION, ALL)
        if stored_sub_location and stored_sub_location in items_to_add:
            sub_location_to_set = stored_sub_location
        elif not stored_sub_location and previous_sub_location in items_to_add : # try to keep previous if still valid and no specific one is asked
            sub_location_to_set = previous_sub_location

        self.scene_sub_location_combo.setCurrentText(sub_location_to_set)
        self._is_populating = False

        # Emit signal if the sub-location actually changed or if it's an initial population causing an update
        current_text = self.scene_sub_location_combo.currentText()
        if current_text != previous_sub_location or is_initial_population :
             self.scene_sub_location_changed.emit(current_text)
        logger.debug(f"Combo sous-lieux mis à jour. Sélectionné: {current_text}")


    def _perform_swap_and_emit(self):
        logger.debug("Swap des personnages.")
        self._is_populating = True # Block signals from individual combo changes
        
        current_a_text = self.character_a_combo.currentText()
        current_b_text = self.character_b_combo.currentText()

        self.character_a_combo.setCurrentText(current_b_text)
        self.character_b_combo.setCurrentText(current_a_text)
        
        self._is_populating = False
        
        self.character_a_changed.emit(self.character_a_combo.currentText())
        self.character_b_changed.emit(self.character_b_combo.currentText())
        logger.debug("Swap terminé et signaux émis.")

    def get_selected_scene_info(self) -> dict:
        return {
            "character_a": self.character_a_combo.currentText(),
            "character_b": self.character_b_combo.currentText(),
            "scene_region": self.scene_region_combo.currentText(),
            "scene_sub_location": self.scene_sub_location_combo.currentText(),
        }

    def load_selection(self, scene_info: dict):
        logger.debug(f"Chargement de la sélection dans SceneSelectionWidget: {scene_info}")
        self._is_populating = True

        char_a = scene_info.get("character_a", UIText.NONE)
        char_b = scene_info.get("character_b", UIText.NONE)
        region = scene_info.get("scene_region", UIText.NONE_FEM)
        sub_location = scene_info.get("scene_sub_location", UIText.ALL) # Default to ALL if region has sublocations

        # Set characters first
        self.character_a_combo.setCurrentText(char_a)
        self.character_b_combo.setCurrentText(char_b)
        
        # Set region - this will trigger _on_scene_region_changed_internal_and_emit -> _update_sub_locations_for_region
        # We pass the target sub_location to _update_sub_locations_for_region via setCurrentText of scene_region_combo
        # No, that's not right. _update_sub_locations_for_region needs it directly.

        # Block signals from region combo while we manually manage sub-location update
        self.scene_region_combo.blockSignals(True)
        self.scene_region_combo.setCurrentText(region)
        self.scene_region_combo.blockSignals(False)
        
        # Now update sub-locations based on the loaded region, trying to set the loaded sub_location
        self._update_sub_locations_for_region(region, stored_sub_location=sub_location, is_initial_population=True)

        self._is_populating = False
        
        # Emit signals for the final loaded state, so GenerationPanel can update tokens etc.
        self.character_a_changed.emit(self.character_a_combo.currentText())
        self.character_b_changed.emit(self.character_b_combo.currentText())
        self.scene_region_changed.emit(self.scene_region_combo.currentText())
        # scene_sub_location_changed is already emitted by _update_sub_locations_for_region if needed
        
        logger.debug("Sélection chargée dans SceneSelectionWidget.") 