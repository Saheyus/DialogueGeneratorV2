import sys
import uuid
from typing import Optional, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTextEdit, QFormLayout, QGroupBox, 
    QScrollArea, QSplitter, QFrame, QTabWidget, QMessageBox, QDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QCursor

# --- Gestion des imports robustes ---
try:
    # Import absolu (cas normal application)
    from models.dialogue_structure.interaction import Interaction
    from models.dialogue_structure.dialogue_elements import (
        DialogueLineElement, PlayerChoicesBlockElement, CommandElement, PlayerChoiceOption
    )
    from services.interaction_service import InteractionService
except ImportError:
    try:
        # Import relatif (cas test ou module)
        from ...models.dialogue_structure.interaction import Interaction
        from ...models.dialogue_structure.dialogue_elements import (
            DialogueLineElement, PlayerChoicesBlockElement, CommandElement, PlayerChoiceOption
        )
        from ...services.interaction_service import InteractionService
    except ImportError:
        # Fallback pour exécution directe isolée
        import os
        from pathlib import Path
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir.parent.parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        from models.dialogue_structure.interaction import Interaction
        from models.dialogue_structure.dialogue_elements import (
            DialogueLineElement, PlayerChoicesBlockElement, CommandElement, PlayerChoiceOption
        )
        from services.interaction_service import InteractionService

# Import du nouveau widget de sélection de personnages
from .character_selector_widget import CharacterSelectorWidget


class DialogueLineWidget(QWidget):
    """Widget pour l'édition d'une ligne de dialogue."""
    
    line_changed = Signal(int, DialogueLineElement)  # Index, Nouvelle ligne
    line_deleted = Signal(int)  # Index
    
    def __init__(self, line: DialogueLineElement, index: int, character_names: List[str] = None, parent=None):
        super().__init__(parent)
        self.line = line
        self.index = index
        self.character_names = character_names or []
        self._init_ui()
    
    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Forme : [Speaker] Text
        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 0, 0, 0)
        
        # Utiliser le widget de sélection de personnages avec les noms fournis
        self.speaker_edit = CharacterSelectorWidget(self.character_names)
        self.speaker_edit.setText(self.line.speaker)
        self.speaker_edit.setPlaceholderText("Personnage")
        self.speaker_edit.textChanged.connect(self._on_speaker_changed)
        
        self.text_edit = QTextEdit(self.line.text)
        self.text_edit.setPlaceholderText("Texte du dialogue")
        self.text_edit.textChanged.connect(self._on_text_changed)
        self.text_edit.setMaximumHeight(100)
        
        form_layout.addRow("Personnage:", self.speaker_edit)
        form_layout.addRow("Texte:", self.text_edit)
        
        layout.addLayout(form_layout, 1)
        
        # Boutons
        buttons_layout = QVBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(2)
        
        delete_button = QPushButton("Supprimer")
        delete_button.clicked.connect(self._on_delete_clicked)
        
        buttons_layout.addWidget(delete_button)
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
    
    def _on_speaker_changed(self):
        self.line.speaker = self.speaker_edit.text()
        self.line_changed.emit(self.index, self.line)
    
    def _on_text_changed(self):
        self.line.text = self.text_edit.toPlainText()
        self.line_changed.emit(self.index, self.line)
    
    def _on_delete_clicked(self):
        self.line_deleted.emit(self.index)


class PlayerChoiceWidget(QWidget):
    """Widget pour l'édition d'un choix individuel du joueur."""
    
    choice_changed = Signal(int, PlayerChoiceOption)  # Index, Choix modifié
    choice_deleted = Signal(int)  # Index
    
    def __init__(self, choice: PlayerChoiceOption, index: int, parent=None):
        super().__init__(parent)
        self.choice = choice
        self.index = index
        self._init_ui()
    
    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Texte du choix
        self.text_edit = QLineEdit(self.choice.text)
        self.text_edit.setPlaceholderText("Texte du choix")
        self.text_edit.textChanged.connect(self._on_text_changed)
        
        # ID de la prochaine interaction
        self.next_id_edit = QLineEdit(self.choice.next_interaction_id or "")
        self.next_id_edit.setPlaceholderText("ID de la prochaine interaction")
        self.next_id_edit.textChanged.connect(self._on_next_id_changed)
        
        layout.addWidget(self.text_edit, 2)
        layout.addWidget(self.next_id_edit, 1)
        
        # Bouton de suppression
        delete_button = QPushButton("X")
        delete_button.setMaximumWidth(30)
        delete_button.clicked.connect(self._on_delete_clicked)
        
        layout.addWidget(delete_button)
    
    def _on_text_changed(self):
        self.choice.text = self.text_edit.text()
        self.choice_changed.emit(self.index, self.choice)
    
    def _on_next_id_changed(self):
        self.choice.next_interaction_id = self.next_id_edit.text() or None
        self.choice_changed.emit(self.index, self.choice)
    
    def _on_delete_clicked(self):
        self.choice_deleted.emit(self.index)


class PlayerChoicesBlockWidget(QWidget):
    """Widget pour l'édition d'un bloc de choix du joueur."""
    
    block_changed = Signal(int, PlayerChoicesBlockElement)  # Index, Bloc modifié
    block_deleted = Signal(int)  # Index
    
    def __init__(self, block: PlayerChoicesBlockElement, index: int, parent=None):
        super().__init__(parent)
        self.block = block
        self.index = index
        self.choice_widgets = []
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Titre du bloc
        title_layout = QHBoxLayout()
        title_label = QLabel(f"Bloc de choix #{self.index + 1}")
        title_label.setStyleSheet("font-weight: bold;")
        
        delete_button = QPushButton("Supprimer bloc")
        delete_button.clicked.connect(self._on_delete_clicked)
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(delete_button)
        
        layout.addLayout(title_layout)
        
        # Liste des choix
        self.choices_layout = QVBoxLayout()
        self.choices_layout.setSpacing(5)
        
        # Charger les choix existants
        for i, choice in enumerate(self.block.choices):
            self._add_choice_widget(choice, i)
        
        # Bouton pour ajouter un choix
        add_choice_button = QPushButton("Ajouter un choix")
        add_choice_button.clicked.connect(self._add_choice)
        
        layout.addLayout(self.choices_layout)
        layout.addWidget(add_choice_button)
        
        # Séparateur
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
    
    def _add_choice(self):
        """Ajoute un nouveau choix au bloc."""
        new_choice = PlayerChoiceOption("", None)
        self.block.choices.append(new_choice)
        self._add_choice_widget(new_choice, len(self.choice_widgets))
        self.block_changed.emit(self.index, self.block)
    
    def _add_choice_widget(self, choice: PlayerChoiceOption, index: int):
        """Ajoute un widget pour éditer un choix existant."""
        choice_widget = PlayerChoiceWidget(choice, index)
        choice_widget.choice_changed.connect(self._on_choice_changed)
        choice_widget.choice_deleted.connect(self._on_choice_deleted)
        
        self.choices_layout.addWidget(choice_widget)
        self.choice_widgets.append(choice_widget)
    
    def _on_choice_changed(self, index: int, choice: PlayerChoiceOption):
        """Gère le changement d'un choix."""
        if index < len(self.block.choices):
            self.block.choices[index] = choice
            self.block_changed.emit(self.index, self.block)
    
    def _on_choice_deleted(self, index: int):
        """Supprime un choix."""
        if index < len(self.block.choices):
            self.block.choices.pop(index)
            
            widget = self.choice_widgets.pop(index)
            widget.deleteLater()
            
            # Mettre à jour les indices des widgets restants
            for i, widget in enumerate(self.choice_widgets):
                widget.index = i
            
            self.block_changed.emit(self.index, self.block)
    
    def _on_delete_clicked(self):
        """Supprime le bloc entier."""
        self.block_deleted.emit(self.index)


class CommandWidget(QWidget):
    """Widget pour l'édition d'une commande."""
    
    command_changed = Signal(int, CommandElement)  # Index, Commande modifiée
    command_deleted = Signal(int)  # Index
    
    def __init__(self, command: CommandElement, index: int, parent=None):
        super().__init__(parent)
        self.command = command
        self.index = index
        self._init_ui()
    
    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Texte de la commande
        self.command_edit = QLineEdit(self.command.command_string)
        self.command_edit.setPlaceholderText("Commande (ex: wait(2), set_mood(personnage, content))")
        self.command_edit.textChanged.connect(self._on_command_changed)
        
        layout.addWidget(self.command_edit, 1)
        
        # Bouton de suppression
        delete_button = QPushButton("X")
        delete_button.setMaximumWidth(30)
        delete_button.clicked.connect(self._on_delete_clicked)
        
        layout.addWidget(delete_button)
    
    def _on_command_changed(self):
        self.command.command_string = self.command_edit.text()
        self.command_changed.emit(self.index, self.command)
    
    def _on_delete_clicked(self):
        self.command_deleted.emit(self.index)


class InteractionEditorWidget(QWidget):
    """Widget d'édition des détails d'une interaction.
    
    Permet de modifier:
    - Les informations générales (titre, ID)
    - Les lignes de dialogue
    - Les commandes
    - Les choix du joueur et leurs conséquences
    """
    
    interaction_changed = Signal(Interaction)  # Émis quand l'interaction est modifiée
    interaction_saved = Signal()  # Signal émis après sauvegarde
    
    def __init__(self, interaction_service: InteractionService, context_builder=None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setMinimumHeight(500)  # Hauteur minimale augmentée pour un confort maximal
        self.interaction_service = interaction_service
        self.context_builder = context_builder
        self.character_names = []
        if self.context_builder:
            self.character_names = self.context_builder.get_characters_names()
        
        self.current_interaction: Optional[Interaction] = None
        self.dialogue_line_widgets = []  # Liste des widgets de lignes de dialogue
        self.player_choices_block_widgets = []  # Liste des widgets de blocs de choix
        self.command_widgets = []  # Liste des widgets de commandes
        
        self._init_ui()
    
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Titre du widget
        title_label = QLabel("Éditeur d'interaction")
        title_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(title_label)
        
        # Widget de défilement pour tout le contenu
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        main_layout.addWidget(scroll_area)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_area.setWidget(scroll_content)
        
        # --- Section Informations Générales ---
        general_group = QGroupBox("Informations générales")
        general_layout = QFormLayout(general_group)
        
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Titre de l'interaction")
        self.title_edit.textChanged.connect(self._on_title_changed)
        
        self.id_label = QLabel()
        self.id_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.id_label.setStyleSheet("font-family: monospace;")
        
        general_layout.addRow("Titre:", self.title_edit)
        general_layout.addRow("ID:", self.id_label)
        
        scroll_layout.addWidget(general_group)
        
        # --- Section Éléments de l'Interaction ---
        elements_tabs = QTabWidget()
        
        # Onglet Lignes de Dialogue
        self.dialogue_lines_widget = QWidget()
        dialogue_lines_layout = QVBoxLayout(self.dialogue_lines_widget)
        
        # Liste des lignes de dialogue
        dialogue_lines_group = QGroupBox("Lignes de dialogue")
        dialogue_lines_group_layout = QVBoxLayout(dialogue_lines_group)
        
        # Tableau des lignes de dialogue
        self.dialogue_lines_layout = QVBoxLayout()
        self.dialogue_lines_layout.setSpacing(5)
        
        # Bouton pour ajouter une ligne de dialogue
        add_dialogue_line_button = QPushButton("Ajouter une ligne de dialogue")
        add_dialogue_line_button.clicked.connect(self._add_dialogue_line)
        
        dialogue_lines_group_layout.addLayout(self.dialogue_lines_layout)
        dialogue_lines_group_layout.addWidget(add_dialogue_line_button)
        
        dialogue_lines_layout.addWidget(dialogue_lines_group)
        dialogue_lines_layout.addStretch()
        
        # Onglet Choix du Joueur
        self.player_choices_widget = QWidget()
        player_choices_layout = QVBoxLayout(self.player_choices_widget)
        
        # Liste des blocs de choix
        player_choices_group = QGroupBox("Choix du joueur")
        player_choices_group_layout = QVBoxLayout(player_choices_group)
        
        # Tableau des blocs de choix
        self.player_choices_layout = QVBoxLayout()
        self.player_choices_layout.setSpacing(5)
        
        # Bouton pour ajouter un bloc de choix
        add_player_choices_button = QPushButton("Ajouter un bloc de choix")
        add_player_choices_button.clicked.connect(self._add_player_choices_block)
        
        player_choices_group_layout.addLayout(self.player_choices_layout)
        player_choices_group_layout.addWidget(add_player_choices_button)
        
        player_choices_layout.addWidget(player_choices_group)
        player_choices_layout.addStretch()
        
        # Onglet Commandes
        self.commands_widget = QWidget()
        commands_layout = QVBoxLayout(self.commands_widget)
        
        # Liste des commandes
        commands_group = QGroupBox("Commandes")
        commands_group_layout = QVBoxLayout(commands_group)
        
        # Tableau des commandes
        self.commands_layout = QVBoxLayout()
        self.commands_layout.setSpacing(5)
        
        # Bouton pour ajouter une commande
        add_command_button = QPushButton("Ajouter une commande")
        add_command_button.clicked.connect(self._add_command)
        
        commands_group_layout.addLayout(self.commands_layout)
        commands_group_layout.addWidget(add_command_button)
        
        commands_layout.addWidget(commands_group)
        commands_layout.addStretch()
        
        elements_tabs.addTab(self.dialogue_lines_widget, "Dialogues")
        elements_tabs.addTab(self.player_choices_widget, "Choix joueur")
        elements_tabs.addTab(self.commands_widget, "Commandes")
        
        scroll_layout.addWidget(elements_tabs)
        
        # --- Section Boutons d'actions ---
        buttons_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Enregistrer")
        self.save_button.clicked.connect(self._on_save_clicked)
        
        self.revert_button = QPushButton("Annuler")
        self.revert_button.clicked.connect(self._on_revert_clicked)
        
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.revert_button)
        
        scroll_layout.addLayout(buttons_layout)
        
        # Désactiver les contrôles par défaut
        self._update_ui_state(False)
    
    def set_interaction(self, interaction: Optional[Interaction]):
        """Charge une interaction dans l'éditeur."""
        print(f"[DEBUG] InteractionEditorWidget.set_interaction() appelé avec interaction={interaction}")
        self._clear_ui()
        self.current_interaction = interaction
        
        if interaction:
            print(f"[DEBUG] Chargement de l'interaction: id={interaction.interaction_id}, titre={getattr(interaction, 'title', 'N/A')}")
            self.id_label.setText(str(interaction.interaction_id))
            self.title_edit.setText(getattr(interaction, 'title', ""))
            self._load_dialogue_lines()
            self._load_player_choices_blocks()
            self._load_commands()
            self._update_ui_state(True)  # Toujours activer l'éditeur si interaction
        else:
            print(f"[DEBUG] Effacement de l'éditeur (interaction=None)")
            self._update_ui_state(False)
    
    def _clear_ui(self):
        """Efface tous les widgets dynamiques."""
        # Effacer les lignes de dialogue
        for widget in self.dialogue_line_widgets:
            widget.deleteLater()
        self.dialogue_line_widgets = []
        
        # Effacer les blocs de choix
        for widget in self.player_choices_block_widgets:
            widget.deleteLater()
        self.player_choices_block_widgets = []
        
        # Effacer les commandes
        for widget in self.command_widgets:
            widget.deleteLater()
        self.command_widgets = []
        
        # Effacer les champs
        self.id_label.setText("")
        self.title_edit.setText("")
    
    def _load_dialogue_lines(self):
        """Charge les lignes de dialogue de l'interaction."""
        if not self.current_interaction:
            return
        
        # Trouver toutes les lignes de dialogue dans l'interaction
        dialogue_lines = [elem for elem in self.current_interaction.elements if isinstance(elem, DialogueLineElement)]
        
        # Ajouter un widget pour chaque ligne
        for i, line in enumerate(dialogue_lines):
            self._add_dialogue_line_widget(line, i)
    
    def _load_player_choices_blocks(self):
        """Charge les blocs de choix du joueur de l'interaction."""
        if not self.current_interaction:
            return
        
        # Trouver tous les blocs de choix dans l'interaction
        choices_blocks = [elem for elem in self.current_interaction.elements if isinstance(elem, PlayerChoicesBlockElement)]
        
        # Ajouter un widget pour chaque bloc
        for i, block in enumerate(choices_blocks):
            self._add_player_choices_block_widget(block, i)
    
    def _load_commands(self):
        """Charge les commandes de l'interaction."""
        if not self.current_interaction:
            return
        
        # Trouver toutes les commandes dans l'interaction
        commands = [elem for elem in self.current_interaction.elements if isinstance(elem, CommandElement)]
        
        # Ajouter un widget pour chaque commande
        for i, command in enumerate(commands):
            self._add_command_widget(command, i)
    
    def _update_ui_state(self, enabled: bool):
        """Met à jour l'état d'activation des contrôles."""
        self.title_edit.setEnabled(enabled)
        self.save_button.setEnabled(enabled)
        self.revert_button.setEnabled(enabled)
        # TODO: Activer/désactiver les autres contrôles
    
    def _on_title_changed(self, new_title: str):
        """Gère le changement de titre."""
        if self.current_interaction:
            self.current_interaction.title = new_title
    
    def _on_save_clicked(self):
        """Enregistre les modifications de l'interaction."""
        if not self.current_interaction:
            return
        
        try:
            self.interaction_service.save(self.current_interaction)
            self.interaction_changed.emit(self.current_interaction)
            self.interaction_saved.emit()  # Émettre le signal après sauvegarde
            QMessageBox.information(self, "Sauvegarde", "Les modifications ont été enregistrées avec succès.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde : {str(e)}")
    
    def _on_revert_clicked(self):
        """Annule les modifications en rechargeant l'interaction depuis le service."""
        if not self.current_interaction:
            return
        
        # Demander confirmation
        confirm = QMessageBox.question(
            self, "Confirmer l'annulation", 
            "Voulez-vous vraiment annuler toutes les modifications ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            # Recharger l'interaction depuis le service
            reloaded_interaction = self.interaction_service.get_by_id(str(self.current_interaction.interaction_id))
            if reloaded_interaction:
                self.set_interaction(reloaded_interaction)
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de recharger l'interaction.")
    
    def _add_dialogue_line(self):
        """Ajoute une nouvelle ligne de dialogue à l'interaction."""
        if not self.current_interaction:
            return
        
        # Créer une nouvelle ligne de dialogue
        new_line = DialogueLineElement("", "")
        
        # Ajouter la ligne à l'interaction
        self.current_interaction.elements.append(new_line)
        
        # Ajouter le widget pour éditer la ligne
        self._add_dialogue_line_widget(new_line, len(self.dialogue_line_widgets))
        
        # Émettre le signal de changement
        self.interaction_changed.emit(self.current_interaction)
    
    def _add_dialogue_line_widget(self, line: DialogueLineElement, index: int):
        """Ajoute un widget pour éditer une ligne de dialogue existante."""
        dialogue_line_widget = DialogueLineWidget(line, index, self.character_names)
        dialogue_line_widget.line_changed.connect(self._on_dialogue_line_changed)
        dialogue_line_widget.line_deleted.connect(self._on_dialogue_line_deleted)
        
        self.dialogue_lines_layout.addWidget(dialogue_line_widget)
        self.dialogue_line_widgets.append(dialogue_line_widget)
    
    def _on_dialogue_line_changed(self, index: int, line: DialogueLineElement):
        """Gère le changement d'une ligne de dialogue."""
        if not self.current_interaction:
            return
        
        # Mettre à jour la ligne dans l'interaction
        dialogue_elements = [elem for elem in self.current_interaction.elements if isinstance(elem, DialogueLineElement)]
        if index < len(dialogue_elements):
            # Trouver l'index réel dans la liste des éléments
            elements = self.current_interaction.elements
            element_indices = [i for i, elem in enumerate(elements) if isinstance(elem, DialogueLineElement)]
            if index < len(element_indices):
                real_index = element_indices[index]
                self.current_interaction.elements[real_index] = line
        
        # Pas besoin d'émettre le signal car le widget de ligne émet déjà son propre signal
    
    def _on_dialogue_line_deleted(self, index: int):
        """Supprime une ligne de dialogue."""
        if not self.current_interaction:
            return
        
        # Trouver la ligne à supprimer
        dialogue_elements = [elem for elem in self.current_interaction.elements if isinstance(elem, DialogueLineElement)]
        if index < len(dialogue_elements):
            # Trouver l'index réel dans la liste des éléments
            elements = self.current_interaction.elements
            element_indices = [i for i, elem in enumerate(elements) if isinstance(elem, DialogueLineElement)]
            if index < len(element_indices):
                real_index = element_indices[index]
                # Supprimer la ligne de l'interaction
                self.current_interaction.elements.pop(real_index)
                
                # Supprimer le widget
                if index < len(self.dialogue_line_widgets):
                    widget = self.dialogue_line_widgets.pop(index)
                    widget.deleteLater()
                
                # Mettre à jour les indices des widgets restants
                for i, widget in enumerate(self.dialogue_line_widgets):
                    widget.index = i
                
                # Émettre le signal de changement
                self.interaction_changed.emit(self.current_interaction)
    
    def _add_player_choices_block(self):
        """Ajoute un nouveau bloc de choix à l'interaction."""
        if not self.current_interaction:
            return
        
        # Créer un nouveau bloc de choix
        new_block = PlayerChoicesBlockElement()
        
        # Ajouter le bloc à l'interaction
        self.current_interaction.elements.append(new_block)
        
        # Ajouter le widget pour éditer le bloc
        self._add_player_choices_block_widget(new_block, len(self.player_choices_block_widgets))
        
        # Émettre le signal de changement
        self.interaction_changed.emit(self.current_interaction)
    
    def _add_player_choices_block_widget(self, block: PlayerChoicesBlockElement, index: int):
        """Ajoute un widget pour éditer un bloc de choix existant."""
        block_widget = PlayerChoicesBlockWidget(block, index)
        block_widget.block_changed.connect(self._on_player_choices_block_changed)
        block_widget.block_deleted.connect(self._on_player_choices_block_deleted)
        
        self.player_choices_layout.addWidget(block_widget)
        self.player_choices_block_widgets.append(block_widget)
    
    def _on_player_choices_block_changed(self, index: int, block: PlayerChoicesBlockElement):
        """Gère le changement d'un bloc de choix."""
        if not self.current_interaction:
            return
        
        # Mettre à jour le bloc dans l'interaction
        choices_blocks = [elem for elem in self.current_interaction.elements if isinstance(elem, PlayerChoicesBlockElement)]
        if index < len(choices_blocks):
            # Trouver l'index réel dans la liste des éléments
            elements = self.current_interaction.elements
            element_indices = [i for i, elem in enumerate(elements) if isinstance(elem, PlayerChoicesBlockElement)]
            if index < len(element_indices):
                real_index = element_indices[index]
                self.current_interaction.elements[real_index] = block
        
        # Pas besoin d'émettre le signal car le widget de bloc émet déjà son propre signal
    
    def _on_player_choices_block_deleted(self, index: int):
        """Supprime un bloc de choix."""
        if not self.current_interaction:
            return
        
        # Trouver le bloc à supprimer
        choices_blocks = [elem for elem in self.current_interaction.elements if isinstance(elem, PlayerChoicesBlockElement)]
        if index < len(choices_blocks):
            # Trouver l'index réel dans la liste des éléments
            elements = self.current_interaction.elements
            element_indices = [i for i, elem in enumerate(elements) if isinstance(elem, PlayerChoicesBlockElement)]
            if index < len(element_indices):
                real_index = element_indices[index]
                # Supprimer le bloc de l'interaction
                self.current_interaction.elements.pop(real_index)
                
                # Supprimer le widget
                if index < len(self.player_choices_block_widgets):
                    widget = self.player_choices_block_widgets.pop(index)
                    widget.deleteLater()
                
                # Mettre à jour les indices des widgets restants
                for i, widget in enumerate(self.player_choices_block_widgets):
                    widget.index = i
                
                # Émettre le signal de changement
                self.interaction_changed.emit(self.current_interaction)
    
    def _add_command(self):
        """Ajoute une nouvelle commande à l'interaction."""
        if not self.current_interaction:
            return
        
        # Créer une nouvelle commande
        new_command = CommandElement("")
        
        # Ajouter la commande à l'interaction
        self.current_interaction.elements.append(new_command)
        
        # Ajouter le widget pour éditer la commande
        self._add_command_widget(new_command, len(self.command_widgets))
        
        # Émettre le signal de changement
        self.interaction_changed.emit(self.current_interaction)
    
    def _add_command_widget(self, command: CommandElement, index: int):
        """Ajoute un widget pour éditer une commande existante."""
        command_widget = CommandWidget(command, index)
        command_widget.command_changed.connect(self._on_command_changed)
        command_widget.command_deleted.connect(self._on_command_deleted)
        
        self.commands_layout.addWidget(command_widget)
        self.command_widgets.append(command_widget)
    
    def _on_command_changed(self, index: int, command: CommandElement):
        """Gère le changement d'une commande."""
        if not self.current_interaction:
            return
        
        # Mettre à jour la commande dans l'interaction
        commands = [elem for elem in self.current_interaction.elements if isinstance(elem, CommandElement)]
        if index < len(commands):
            # Trouver l'index réel dans la liste des éléments
            elements = self.current_interaction.elements
            element_indices = [i for i, elem in enumerate(elements) if isinstance(elem, CommandElement)]
            if index < len(element_indices):
                real_index = element_indices[index]
                self.current_interaction.elements[real_index] = command
        
        # Pas besoin d'émettre le signal car le widget de commande émet déjà son propre signal
    
    def _on_command_deleted(self, index: int):
        """Supprime une commande."""
        if not self.current_interaction:
            return
        
        # Trouver la commande à supprimer
        commands = [elem for elem in self.current_interaction.elements if isinstance(elem, CommandElement)]
        if index < len(commands):
            # Trouver l'index réel dans la liste des éléments
            elements = self.current_interaction.elements
            element_indices = [i for i, elem in enumerate(elements) if isinstance(elem, CommandElement)]
            if index < len(element_indices):
                real_index = element_indices[index]
                # Supprimer la commande de l'interaction
                self.current_interaction.elements.pop(real_index)
                
                # Supprimer le widget
                if index < len(self.command_widgets):
                    widget = self.command_widgets.pop(index)
                    widget.deleteLater()
                
                # Mettre à jour les indices des widgets restants
                for i, widget in enumerate(self.command_widgets):
                    widget.index = i
                
                # Émettre le signal de changement
                self.interaction_changed.emit(self.current_interaction)


# Pour tester le widget isolément (si besoin)
if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Créer un service d'interaction de test
    from services.repositories import InMemoryInteractionRepository
    repo = InMemoryInteractionRepository()
    service = InteractionService(repo)
    
    # Créer une interaction de test
    test_interaction = Interaction(str(uuid.uuid4()))
    test_interaction.title = "Interaction de test"
    test_interaction.elements.append(DialogueLineElement("Personnage", "Bonjour, monde !"))
    test_interaction.elements.append(CommandElement("wait(2)"))
    
    choices_block = PlayerChoicesBlockElement()
    choices_block.add_choice(PlayerChoiceOption("Saluer", "node_salutation"))
    choices_block.add_choice(PlayerChoiceOption("Ignorer", "node_ignorer"))
    test_interaction.elements.append(choices_block)
    
    service.save(test_interaction)
    
    # Créer et afficher le widget
    widget = InteractionEditorWidget(service)
    widget.set_interaction(test_interaction)
    widget.show()
    
    sys.exit(app.exec()) 