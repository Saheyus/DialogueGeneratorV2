from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QPlainTextEdit, 
                               QLabel, QPushButton, QHBoxLayout, QStyle)
from PySide6.QtCore import Signal, Qt
from typing import Optional

class InstructionsWidget(QWidget):
    user_instructions_changed = Signal()
    system_prompt_changed = Signal()
    restore_default_system_prompt_clicked = Signal()
    settings_changed = Signal() # Generic signal

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_loading_settings = False
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0) # Pour s'intégrer sans marges additionnelles

        self.instructions_tabs = QTabWidget()
        main_layout.addWidget(self.instructions_tabs)

        # Onglet 1: Instructions de Scène
        scene_instructions_widget = QWidget()
        scene_instructions_layout = QVBoxLayout(scene_instructions_widget)
        self.user_instructions_textedit = QPlainTextEdit()
        self.user_instructions_textedit.setPlaceholderText(
            "Ex: Bob doit annoncer à Alice qu'il part à l'aventure. Ton désiré: Héroïque. Inclure une condition sur la compétence 'Charisme' de Bob."
        )
        self.user_instructions_textedit.setToolTip("Décrivez le but de la scène, le ton, les points clés à aborder, ou toute autre instruction spécifique pour l'IA.")
        self.user_instructions_textedit.textChanged.connect(self._on_user_instructions_changed)
        scene_instructions_layout.addWidget(self.user_instructions_textedit)
        self.instructions_tabs.addTab(scene_instructions_widget, "Instructions de Scène")

        # Onglet 2: Instructions Système LLM
        system_prompt_widget = QWidget()
        system_prompt_layout = QVBoxLayout(system_prompt_widget)
        
        system_prompt_header_layout = QHBoxLayout()
        system_prompt_header_layout.addWidget(QLabel("Prompt Système Principal:"))
        system_prompt_header_layout.addStretch()
        self.restore_default_system_prompt_button = QPushButton("Restaurer Défaut")
        self.restore_default_system_prompt_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogResetButton))
        self.restore_default_system_prompt_button.setToolTip("Restaure le prompt système par défaut de l'application.")
        self.restore_default_system_prompt_button.clicked.connect(self.restore_default_system_prompt_clicked.emit)
        system_prompt_header_layout.addWidget(self.restore_default_system_prompt_button)
        system_prompt_layout.addLayout(system_prompt_header_layout)

        self.system_prompt_textedit = QPlainTextEdit()
        self.system_prompt_textedit.setToolTip("Modifiez le prompt système principal envoyé au LLM. Ce prompt guide le comportement général de l'IA.")
        self.system_prompt_textedit.textChanged.connect(self._on_system_prompt_changed)
        system_prompt_layout.addWidget(self.system_prompt_textedit)
        self.instructions_tabs.addTab(system_prompt_widget, "Instructions Système LLM")
        
        self.setLayout(main_layout)

    def _on_user_instructions_changed(self):
        self.user_instructions_changed.emit()
        if not self._is_loading_settings: self.settings_changed.emit()

    def _on_system_prompt_changed(self):
        self.system_prompt_changed.emit()
        if not self._is_loading_settings: self.settings_changed.emit()

    def get_settings(self) -> dict:
        return {
            "user_instructions": self.user_instructions_textedit.toPlainText(),
            "system_prompt": self.system_prompt_textedit.toPlainText(),
        }

    def load_settings(self, settings: dict, default_user_instructions: str = "", default_system_prompt: Optional[str] = None):
        self._is_loading_settings = True
        self.user_instructions_textedit.setPlainText(settings.get("user_instructions", default_user_instructions))
        
        system_prompt_to_load = settings.get("system_prompt", default_system_prompt)
        if system_prompt_to_load is not None:
            self.system_prompt_textedit.setPlainText(system_prompt_to_load)
        # Si default_system_prompt est None et qu'il n'y a rien dans settings, on ne change pas le texte actuel
        # (qui pourrait être le placeholder ou un texte par défaut déjà mis par un autre mécanisme comme restore_default).
        # Si default_system_prompt est une chaîne vide, cela effacera le texte.

        self._is_loading_settings = False

    def set_system_prompt_text(self, text: str):
        self.system_prompt_textedit.setPlainText(text)

    def get_user_instructions_text(self) -> str:
        return self.user_instructions_textedit.toPlainText()

    def get_system_prompt_text(self) -> str:
        return self.system_prompt_textedit.toPlainText() 