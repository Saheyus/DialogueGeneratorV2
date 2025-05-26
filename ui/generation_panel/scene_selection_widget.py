from PySide6.QtWidgets import (QWidget, QGroupBox, QGridLayout, QLabel, QComboBox, QPushButton, QStyle, QVBoxLayout)
from PySide6.QtCore import Qt, Signal, QSize, QSignalBlocker
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
        self._init_ui()

    def _init_ui(self):
        self.group_box = QGroupBox("Scène Principale")
        
        grid_layout = QGridLayout(self.group_box)
        row = 0

        grid_layout.addWidget(QLabel("Personnage A:"), row, 0)
        self.character_a_combo = QComboBox()
        self.character_a_combo.setToolTip("Sélectionnez le premier personnage principal de la scène.")
        self.character_a_combo.currentTextChanged.connect(self.character_a_changed.emit)
        grid_layout.addWidget(self.character_a_combo, row, 1)
        row += 1

        grid_layout.addWidget(QLabel("Personnage B:"), row, 0)
        self.character_b_combo = QComboBox()
        self.character_b_combo.setToolTip("Sélectionnez le second personnage principal de la scène (optionnel).")
        self.character_b_combo.currentTextChanged.connect(self.character_b_changed.emit)
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
        self.scene_region_combo.currentTextChanged.connect(self._on_scene_region_changed_internal)
        grid_layout.addWidget(self.scene_region_combo, row, 1, 1, 2)
        row += 1

        grid_layout.addWidget(QLabel("Sous-Lieu (optionnel):"), row, 0)
        self.scene_sub_location_combo = QComboBox()
        self.scene_sub_location_combo.setToolTip("Sélectionnez le sous-lieu plus spécifique (si applicable).")
        self.scene_sub_location_combo.currentTextChanged.connect(self.scene_sub_location_changed.emit)
        grid_layout.addWidget(self.scene_sub_location_combo, row, 1, 1, 2)
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.group_box)
        self.setLayout(main_layout)
        
        # Initialiser avec des valeurs par défaut sans émettre de signaux initiaux inutiles
        # Les combos sont vides au début, _update_sub_locations_for_region s'en chargera
        self._update_sub_locations_for_region(UIText.NONE_FEM, is_initial_call=True)

    def populate_character_combos(self, character_names: list):
        logger.debug(f"Peuplement combos personnages avec: {character_names}")
        blocker_a = QSignalBlocker(self.character_a_combo)
        blocker_b = QSignalBlocker(self.character_b_combo)
        
        prev_char_a = self.character_a_combo.currentText()
        prev_char_b = self.character_b_combo.currentText()
        
        self.character_a_combo.clear()
        self.character_b_combo.clear()
        
        all_chars_with_none = [UIText.NONE] + sorted(list(set(character_names)))
        self.character_a_combo.addItems(all_chars_with_none)
        self.character_b_combo.addItems(all_chars_with_none)
        
        self.character_a_combo.setCurrentText(prev_char_a if prev_char_a in all_chars_with_none else UIText.NONE)
        self.character_b_combo.setCurrentText(prev_char_b if prev_char_b in all_chars_with_none else UIText.NONE)
            
        del blocker_a
        del blocker_b

        final_char_a = self.character_a_combo.currentText()
        final_char_b = self.character_b_combo.currentText()

        if final_char_a != prev_char_a:
             self.character_a_changed.emit(final_char_a)
        if final_char_b != prev_char_b:
             self.character_b_changed.emit(final_char_b)
        logger.debug("Combos personnages peuplés.")

    def populate_scene_combos(self, region_names: list):
        logger.debug(f"Peuplement combo régions avec: {region_names}")
        blocker_region = QSignalBlocker(self.scene_region_combo)
        
        prev_region = self.scene_region_combo.currentText() or UIText.NONE_FEM # Gérer le cas initial où c'est vide

        self.scene_region_combo.clear()
        all_regions_with_none = [UIText.NONE_FEM] + sorted(list(set(region_names)))
        self.scene_region_combo.addItems(all_regions_with_none)
        
        selected_region = prev_region if prev_region in all_regions_with_none else UIText.NONE_FEM
        self.scene_region_combo.setCurrentText(selected_region)
        del blocker_region
        if selected_region != UIText.NONE_FEM or prev_region != UIText.NONE_FEM:
            self.scene_region_changed.emit(selected_region)
        self._update_sub_locations_for_region(selected_region, known_regions=set(region_names), is_initial_call=(not prev_region or prev_region == UIText.NONE_FEM) and selected_region == UIText.NONE_FEM)
        self.scene_sub_location_changed.emit(self.scene_sub_location_combo.currentText())
        logger.debug("Combo régions peuplé.")

    def _on_scene_region_changed_internal(self, region_name: str):
        logger.debug(f"Changement de région interne: {region_name}")
        self.scene_region_changed.emit(region_name)
        self._update_sub_locations_for_region(region_name, is_initial_call=False)
        self.scene_sub_location_changed.emit(self.scene_sub_location_combo.currentText())

    def _update_sub_locations_for_region(self, region_name: str, stored_sub_location: Optional[str] = None, known_regions=None, is_initial_call: bool = False):
        logger.debug(f"Update sub-locs pour région: '{region_name}'. Stored: '{stored_sub_location}', InitialCall: {is_initial_call}")
        blocker_sub = QSignalBlocker(self.scene_sub_location_combo)
        prev_sub_loc = self.scene_sub_location_combo.currentText() or UIText.NO_SELECTION
        self.scene_sub_location_combo.clear()
        items_to_add = []
        is_enabled = False
        default_selection_for_sub = UIText.NO_SELECTION
        if known_regions is None:
            known_regions = set(self.context_builder.get_regions())
        known_regions.discard(UIText.NONE_FEM)
        if region_name and region_name != UIText.NONE_FEM and region_name != UIText.NO_SELECTION and region_name in known_regions:
            try:
                sub_locations = sorted(list(set(self.context_builder.get_sub_locations(region_name))))
                if not sub_locations:
                    items_to_add = [UIText.NONE_SUBLOCATION]
                    default_selection_for_sub = UIText.NONE_SUBLOCATION
                else:
                    items_to_add = [UIText.ALL] + sub_locations
                    default_selection_for_sub = UIText.ALL
                is_enabled = True if sub_locations else False
            except Exception as e:
                logger.error(f"Erreur récup sous-lieux pour {region_name}: {e}", exc_info=True)
                items_to_add = [UIText.ERROR_PREFIX + "Err. Charg."]
                default_selection_for_sub = items_to_add[0]
                is_enabled = False # Erreur, donc désactivé
        else: 
            items_to_add = [UIText.NO_SELECTION]
            default_selection_for_sub = UIText.NO_SELECTION
            is_enabled = False
        self.scene_sub_location_combo.addItems(items_to_add)
        self.scene_sub_location_combo.setEnabled(is_enabled)
        sub_location_to_set = default_selection_for_sub
        if stored_sub_location and stored_sub_location in items_to_add:
            sub_location_to_set = stored_sub_location
        self.scene_sub_location_combo.setCurrentText(sub_location_to_set)
        del blocker_sub
        final_sub_loc = self.scene_sub_location_combo.currentText()
        if final_sub_loc != prev_sub_loc or is_initial_call:
            logger.debug(f"Émission scene_sub_location_changed: '{final_sub_loc}' (prev: '{prev_sub_loc}', initial: {is_initial_call})")
            self.scene_sub_location_changed.emit(final_sub_loc)
        logger.debug(f"Combo sous-lieux màj. Sélectionné: '{final_sub_loc}'")

    def _perform_swap_and_emit(self):
        logger.debug("Swap personnages.")
        blocker_a = QSignalBlocker(self.character_a_combo)
        blocker_b = QSignalBlocker(self.character_b_combo)
        
        prev_a = self.character_a_combo.currentText()
        prev_b = self.character_b_combo.currentText()

        self.character_a_combo.setCurrentText(prev_b)
        self.character_b_combo.setCurrentText(prev_a)
        
        del blocker_a
        del blocker_b
        
        # Émettre seulement si les valeurs ont effectivement changé
        if self.character_a_combo.currentText() != prev_a:
            self.character_a_changed.emit(self.character_a_combo.currentText())
        if self.character_b_combo.currentText() != prev_b:
            self.character_b_changed.emit(self.character_b_combo.currentText())
        logger.debug("Swap terminé.")

    def get_selected_scene_info(self) -> dict:
        return {
            "character_a": self.character_a_combo.currentText(),
            "character_b": self.character_b_combo.currentText(),
            "scene_region": self.scene_region_combo.currentText(),
            "scene_sub_location": self.scene_sub_location_combo.currentText(),
        }

    def load_selection(self, scene_info: dict):
        logger.debug(f"Chargement sélection: {scene_info}")
        
        prev_char_a = self.character_a_combo.currentText()
        prev_char_b = self.character_b_combo.currentText()
        prev_region = self.scene_region_combo.currentText()
        prev_sub_loc = self.scene_sub_location_combo.currentText()

        blocker_char_a = QSignalBlocker(self.character_a_combo)
        blocker_char_b = QSignalBlocker(self.character_b_combo)
        blocker_region = QSignalBlocker(self.scene_region_combo)
        blocker_sub_loc = QSignalBlocker(self.scene_sub_location_combo)

        char_a_val = scene_info.get("character_a", UIText.NONE)
        char_b_val = scene_info.get("character_b", UIText.NONE)
        region_val = scene_info.get("scene_region", UIText.NONE_FEM)
        sub_loc_val = scene_info.get("scene_sub_location") # Peut être None

        self.character_a_combo.setCurrentText(char_a_val)
        self.character_b_combo.setCurrentText(char_b_val)
        self.scene_region_combo.setCurrentText(region_val)
        # Récupérer la liste des régions connues depuis le combo
        known_regions = set(self.scene_region_combo.itemText(i) for i in range(self.scene_region_combo.count()))
        self._update_sub_locations_for_region(region_val, stored_sub_location=sub_loc_val, known_regions=known_regions, is_initial_call=True)
        del blocker_char_a
        del blocker_char_b
        del blocker_region
        del blocker_sub_loc
        # Forcer l'émission des signaux même si Qt ne le fait pas
        self.character_a_changed.emit(self.character_a_combo.currentText())
        self.character_b_changed.emit(self.character_b_combo.currentText())
        self.scene_region_changed.emit(self.scene_region_combo.currentText())
        self.scene_sub_location_changed.emit(self.scene_sub_location_combo.currentText())
        logger.debug("Sélection chargée.") 