from PySide6.QtWidgets import (QWidget, QGroupBox, QGridLayout, QLabel, QComboBox, QPushButton, QStyle)
from PySide6.QtCore import Qt, Signal, QSize
import logging
from constants import UIText, FilePaths, Defaults

logger = logging.getLogger(__name__)

class SceneSelectionWidget(QWidget):
    character_a_changed = Signal(str)
    character_b_changed = Signal(str)
    scene_region_changed = Signal(str)
    scene_sub_location_changed = Signal(str)
    swap_characters_clicked = Signal()

    def __init__(self, context_builder, parent=None):
        super().__init__(parent)
        self.context_builder = context_builder
        self._init_ui()

    def _init_ui(self):
        self.group_box = QGroupBox("Scène Principale", self)
        self.layout = QGridLayout(self.group_box)
        row = 0
        self.layout.addWidget(QLabel("Personnage A:"), row, 0)
        self.character_a_combo = QComboBox()
        self.character_a_combo.setToolTip("Sélectionnez le premier personnage principal de la scène.")
        self.character_a_combo.currentTextChanged.connect(self.character_a_changed.emit)
        self.layout.addWidget(self.character_a_combo, row, 1)
        row += 1

        self.layout.addWidget(QLabel("Personnage B:"), row, 0)
        self.character_b_combo = QComboBox()
        self.character_b_combo.setToolTip("Sélectionnez le second personnage principal de la scène (optionnel).")
        self.character_b_combo.currentTextChanged.connect(self.character_b_changed.emit)
        self.layout.addWidget(self.character_b_combo, row, 1)
        row += 1

        self.swap_characters_button = QPushButton()
        self.swap_characters_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ToolBarHorizontalExtensionButton))
        self.swap_characters_button.setToolTip("Échanger Personnage A et Personnage B")
        self.swap_characters_button.setFixedSize(QSize(28, 28))
        self.swap_characters_button.clicked.connect(self.swap_characters_clicked.emit)
        self.layout.addWidget(self.swap_characters_button, 0, 2, 2, 1, Qt.AlignmentFlag.AlignCenter)

        self.layout.addWidget(QLabel("Région de la Scène:"), row, 0)
        self.scene_region_combo = QComboBox()
        self.scene_region_combo.setToolTip("Sélectionnez la région où se déroule la scène.")
        self.scene_region_combo.currentTextChanged.connect(self._on_scene_region_changed_internal)
        self.scene_region_combo.currentTextChanged.connect(self.scene_region_changed.emit)
        self.layout.addWidget(self.scene_region_combo, row, 1, 1, 2)
        row += 1

        self.layout.addWidget(QLabel("Sous-Lieu (optionnel):"), row, 0)
        self.scene_sub_location_combo = QComboBox()
        self.scene_sub_location_combo.setToolTip("Sélectionnez le sous-lieu plus spécifique (si applicable).")
        self.scene_sub_location_combo.currentTextChanged.connect(self.scene_sub_location_changed.emit)
        self.layout.addWidget(self.scene_sub_location_combo, row, 1, 1, 2)
        row += 1

        self.setLayout(self.layout)

    def populate_characters(self, character_names: list):
        logger.debug(f"Peuplement des personnages avec: {character_names}")
        self.character_a_combo.blockSignals(True)
        self.character_b_combo.blockSignals(True)
        
        current_char_a = self.character_a_combo.currentText()
        current_char_b = self.character_b_combo.currentText()
        
        self.character_a_combo.clear()
        self.character_b_combo.clear()
        
        all_chars_with_none = [UIText.NONE] + sorted(character_names)
        self.character_a_combo.addItems(all_chars_with_none)
        self.character_b_combo.addItems(all_chars_with_none)
        
        if current_char_a in all_chars_with_none:
            self.character_a_combo.setCurrentText(current_char_a)
        if current_char_b in all_chars_with_none:
            self.character_b_combo.setCurrentText(current_char_b)
            
        self.character_a_combo.blockSignals(False)
        self.character_b_combo.blockSignals(False)
        logger.debug("Combobox des personnages peuplées.")

    def populate_regions(self, region_names: list):
        logger.debug(f"Peuplement des régions avec: {region_names}")
        self.scene_region_combo.blockSignals(True)
        current_region = self.scene_region_combo.currentText()
        self.scene_region_combo.clear()
        all_regions_with_none = [UIText.NONE_FEM] + sorted(region_names)
        self.scene_region_combo.addItems(all_regions_with_none)
        if current_region in all_regions_with_none:
            self.scene_region_combo.setCurrentText(current_region)
        else:
             self._on_scene_region_changed_internal(self.scene_region_combo.currentText())

        self.scene_region_combo.blockSignals(False)
        if self.scene_region_combo.currentText() == current_region :
            self._on_scene_region_changed_internal(current_region) 
        logger.debug("Combobox des régions peuplée.")

    def _on_scene_region_changed_internal(self, region_name: str):
        logger.debug(f"Changement de région détecté (interne): {region_name}")
        self.scene_sub_location_combo.blockSignals(True)
        current_sub_location = self.scene_sub_location_combo.currentText()
        self.scene_sub_location_combo.clear()
        
        sub_locations_with_none = [UIText.NO_SELECTION]
        
        if region_name and region_name != UIText.NONE_FEM and region_name != UIText.NO_SELECTION:
            try:
                sub_locations = sorted(self.context_builder.get_sub_locations(region_name))
                if not sub_locations:
                    logger.info(f"Aucun sous-lieu trouvé pour la région : {region_name}")
                    sub_locations_with_none = [UIText.NONE_SUBLOCATION]
                else:
                    sub_locations_with_none = [UIText.ALL] + sub_locations
                self.scene_sub_location_combo.setEnabled(True)
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des sous-lieux pour la région {region_name}: {e}", exc_info=True)
                sub_locations_with_none = ["(Erreur de chargement)"]
                self.scene_sub_location_combo.setEnabled(False)
        else:
            self.scene_sub_location_combo.setEnabled(False)

        self.scene_sub_location_combo.addItems(sub_locations_with_none)
        if current_sub_location in sub_locations_with_none:
            self.scene_sub_location_combo.setCurrentText(current_sub_location)
        
        self.scene_sub_location_combo.blockSignals(False)
        logger.debug(f"Combobox des sous-lieux mis à jour pour la région: {region_name}")

    def swap_characters(self):
        logger.debug("Personnages A et B échangés.")
        current_a_index = self.character_a_combo.currentIndex()
        current_b_index = self.character_b_combo.currentIndex()
        self.character_a_combo.setCurrentIndex(current_b_index)
        self.character_b_combo.setCurrentIndex(current_a_index)

    def set_characters(self, characters):
        self.character_a_combo.blockSignals(True)
        self.character_b_combo.blockSignals(True)
        self.character_a_combo.clear()
        self.character_b_combo.clear()
        self.character_a_combo.addItems([UIText.NONE] + characters)
        self.character_b_combo.addItems([UIText.NONE] + characters)
        self.character_a_combo.blockSignals(False)
        self.character_b_combo.blockSignals(False)

    def set_regions(self, regions):
        self.scene_region_combo.blockSignals(True)
        self.scene_region_combo.clear()
        self.scene_region_combo.addItem(UIText.NONE_FEM)
        self.scene_region_combo.addItems(regions)
        self.scene_region_combo.blockSignals(False)

    def set_sub_locations(self, sub_locations):
        self.scene_sub_location_combo.blockSignals(True)
        self.scene_sub_location_combo.clear()
        if not sub_locations:
            self.scene_sub_location_combo.addItem(UIText.NONE_SUBLOCATION)
        else:
            self.scene_sub_location_combo.addItems([UIText.ALL] + sub_locations)
            self.scene_sub_location_combo.setEnabled(True)
        self.scene_sub_location_combo.blockSignals(False)

    def get_selected(self):
        return {
            "character_a": self.character_a_combo.currentText(),
            "character_b": self.character_b_combo.currentText(),
            "scene_region": self.scene_region_combo.currentText(),
            "scene_sub_location": self.scene_sub_location_combo.currentText(),
        }

    def set_selected(self, character_a, character_b, scene_region, scene_sub_location):
        logger.debug(f"SceneSelectionWidget.set_selected appelé avec : A='{character_a}', B='{character_b}', Region='{scene_region}', SubL='{scene_sub_location}'")
        self.character_a_combo.blockSignals(True)
        self.character_b_combo.blockSignals(True)
        self.scene_region_combo.blockSignals(True)
        self.scene_sub_location_combo.blockSignals(True)

        self.character_a_combo.setCurrentText(character_a or UIText.NONE)
        self.character_b_combo.setCurrentText(character_b or UIText.NONE)
        
        new_region_text = scene_region or UIText.NONE_FEM
        region_changed = self.scene_region_combo.currentText() != new_region_text
        self.scene_region_combo.setCurrentText(new_region_text)
        if region_changed :
             self._on_scene_region_changed_internal(new_region_text)
        
        self.scene_sub_location_combo.setCurrentText(scene_sub_location or UIText.ALL)

        self.character_a_combo.blockSignals(False)
        self.character_b_combo.blockSignals(False)
        self.scene_region_combo.blockSignals(False)
        self.scene_sub_location_combo.blockSignals(False)
        logger.debug("Sélections du SceneSelectionWidget mises à jour.") 