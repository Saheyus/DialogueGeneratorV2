from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QProgressBar, QStyle, QGroupBox)
from PySide6.QtCore import Signal, QSize, Qt
from ui.utils import get_icon_path # Correction de l'import

class TokenEstimationActionsWidget(QWidget):
    refresh_token_clicked = Signal()
    generate_dialogue_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        # Utiliser un QGroupBox comme conteneur principal si on veut un titre "Actions"
        # ou directement un QVBoxLayout si le titre est géré par le parent.
        # Pour l'instant, je vais supposer que le titre "Actions" est souhaité ici.
        self.group_box = QGroupBox("Actions")
        main_layout = QVBoxLayout(self.group_box) # Le layout principal du widget est celui du groupbox

        # --- Estimation Tokens --- 
        estimation_h_layout = QHBoxLayout()
        self.token_estimation_label = QLabel("Estimation tokens (contexte/prompt): N/A")
        self.token_estimation_label.setToolTip("Estimation du nombre de tokens basé sur le contexte sélectionné et les instructions.")
        estimation_h_layout.addWidget(self.token_estimation_label)
        estimation_h_layout.addStretch()
        self.refresh_token_button = QPushButton()
        self.refresh_token_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        self.refresh_token_button.setToolTip("Rafraîchir l'estimation des tokens")
        self.refresh_token_button.clicked.connect(self.refresh_token_clicked.emit)
        self.refresh_token_button.setFixedSize(QSize(28,28))
        estimation_h_layout.addWidget(self.refresh_token_button)
        main_layout.addLayout(estimation_h_layout)

        # --- Barre de Progression --- 
        self.generation_progress_bar = QProgressBar()
        self.generation_progress_bar.setVisible(False) 
        main_layout.addWidget(self.generation_progress_bar)

        # --- Bouton Générer --- 
        self.generate_dialogue_button = QPushButton("Générer Dialogues")
        self.generate_dialogue_button.setIcon(get_icon_path("robot.png"))
        self.generate_dialogue_button.setToolTip("Lance la génération des dialogues avec les paramètres actuels (F5).")
        self.generate_dialogue_button.clicked.connect(self.generate_dialogue_clicked.emit) 
        self.generate_dialogue_button.setStyleSheet("font-weight: bold; padding: 5px;")
        main_layout.addWidget(self.generate_dialogue_button)

        # Le layout du widget lui-même doit être défini pour que le group_box s'affiche correctement
        outer_layout = QVBoxLayout(self)
        outer_layout.addWidget(self.group_box)
        outer_layout.setContentsMargins(0,0,0,0) # Pour s'intégrer au mieux dans le parent
        self.setLayout(outer_layout)

    def set_token_estimation_text(self, text: str):
        self.token_estimation_label.setText(text)

    def set_progress_bar_visibility(self, visible: bool):
        self.generation_progress_bar.setVisible(visible)

    def set_progress_bar_indeterminate(self, indeterminate: bool = True):
        if indeterminate:
            self.generation_progress_bar.setRange(0,0)
        else:
            self.generation_progress_bar.setRange(0,100) # Ou une autre valeur max si connue
    
    def set_progress_bar_value(self, value: int):
        self.generation_progress_bar.setValue(value)

    def set_generate_button_enabled(self, enabled: bool):
        self.generate_dialogue_button.setEnabled(enabled) 
