from PySide6.QtWidgets import (QWidget, QGroupBox, QGridLayout, QLabel, QComboBox, QPushButton, QStyle)
from PySide6.QtCore import Qt, Signal, QSize

class SceneSelectionWidget(QWidget):
    character_a_changed = Signal(str)
    character_b_changed = Signal(str)
    scene_region_changed = Signal(str)
    scene_sub_location_changed = Signal(str)
    swap_characters_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.group_box = QGroupBox("Contexte Principal de la Scène", self)
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

    def set_characters(self, characters):
        self.character_a_combo.blockSignals(True)
        self.character_b_combo.blockSignals(True)
        self.character_a_combo.clear()
        self.character_b_combo.clear()
        self.character_a_combo.addItems(["(Aucun)"] + characters)
        self.character_b_combo.addItems(["(Aucun)"] + characters)
        self.character_a_combo.blockSignals(False)
        self.character_b_combo.blockSignals(False)

    def set_regions(self, regions):
        self.scene_region_combo.blockSignals(True)
        self.scene_region_combo.clear()
        self.scene_region_combo.addItem("(Aucune)")
        self.scene_region_combo.addItems(regions)
        self.scene_region_combo.blockSignals(False)

    def set_sub_locations(self, sub_locations):
        self.scene_sub_location_combo.blockSignals(True)
        self.scene_sub_location_combo.clear()
        if not sub_locations:
            self.scene_sub_location_combo.addItem("(Aucun sous-lieu)")
        else:
            self.scene_sub_location_combo.addItems(["(Tous / Non spécifié)"] + sub_locations)
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
        self.character_a_combo.setCurrentText(character_a or "")
        self.character_b_combo.setCurrentText(character_b or "")
        self.scene_region_combo.setCurrentText(scene_region or "")
        self.scene_sub_location_combo.setCurrentText(scene_sub_location or "") 