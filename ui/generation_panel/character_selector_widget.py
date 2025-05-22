from typing import List, Optional
from PySide6.QtWidgets import QWidget, QHBoxLayout, QCompleter, QLineEdit
from PySide6.QtCore import Signal, Qt

class CharacterSelectorWidget(QLineEdit):
    """Widget de sélection de personnage avec recherche et autocomplétion."""
    
    character_selected = Signal(str)  # Émis quand un personnage est sélectionné
    
    def __init__(self, character_names: List[str] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.character_names = character_names or []
        self._init_ui()
        
    def _init_ui(self):
        self.setPlaceholderText("Rechercher un personnage...")
        
        # Configurer l'autocomplétion
        self._setup_completer()
        
        # Connecter les signaux
        self.textChanged.connect(self._on_text_changed)
        self.returnPressed.connect(self._on_return_pressed)
        
    def _setup_completer(self):
        self.completer = QCompleter(self.character_names)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.setCompleter(self.completer)
        
    def update_character_names(self, character_names: List[str]):
        """Met à jour la liste des noms de personnages pour l'autocomplétion."""
        self.character_names = character_names
        self.completer.setModel(None)  # Détacher le modèle actuel
        self.completer = QCompleter(self.character_names)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.setCompleter(self.completer)
        
    def _on_text_changed(self, text: str):
        """Gère les changements dans le texte saisi."""
        # Si le texte correspond exactement à un nom de personnage, émettre le signal
        if text in self.character_names:
            self.character_selected.emit(text)
            
    def _on_return_pressed(self):
        """Gère l'appui sur la touche Entrée."""
        # Émettre le signal avec le texte actuel, même s'il ne correspond pas exactement
        text = self.text()
        if text:
            self.character_selected.emit(text)
            
    def get_character(self) -> str:
        """Retourne le personnage sélectionné."""
        return self.text()
        
    def set_character(self, character: str):
        """Définit le personnage sélectionné."""
        self.setText(character) 