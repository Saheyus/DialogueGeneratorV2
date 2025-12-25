import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QTextEdit, QLabel, QPushButton, 
    QListWidgetItem, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, Slot
from typing import Optional, List
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor, QPalette

# MODIFIED: Changed to direct import from services
from services.interaction_service import InteractionService
from services.configuration_service import ConfigurationService
from context_builder import ContextBuilder
# from ...services.context_builder import ContextBuilder # MODIFIED: Commenté pour éviter confusion avec le précédent

# MODIFIED: Changed to direct import from models
from models.dialogue_structure.interaction import Interaction

import logging
logger = logging.getLogger(__name__)

from constants import UIText, FilePaths, Defaults

class PreviousDialogueSelectorWidget(QWidget):
    """Widget pour sélectionner une interaction précédente comme contexte."""
    
    # Signal émis lorsqu'une interaction est sélectionnée pour être utilisée comme contexte
    # Passe l'ID de l'interaction et la liste des interactions du chemin
    previous_interaction_context_selected = Signal(str, list)

    def __init__(self, interaction_service: InteractionService, context_builder: ContextBuilder, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._interaction_service = interaction_service
        self._context_builder = context_builder
        self._current_selected_interaction_id: Optional[str] = None
        self._current_path_interactions: List[Interaction] = []

        self._init_ui()
        self.populate_interactions_list()

    def _init_ui(self) -> None:
        """Initialise l'interface utilisateur du widget."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Liste des interactions existantes
        self.interactions_list_widget = QListWidget()
        self.interactions_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.interactions_list_widget.itemSelectionChanged.connect(self._on_interaction_selection_changed)
        main_layout.addWidget(QLabel("Interactions Existantes:"))
        main_layout.addWidget(self.interactions_list_widget)

        # Affichage du chemin de dialogue
        self.path_display_text_edit = QTextEdit()
        self.path_display_text_edit.setReadOnly(True)
        self.path_display_text_edit.setPlaceholderText("Sélectionnez une interaction pour voir son chemin de dialogue.")
        main_layout.addWidget(QLabel("Chemin de Dialogue (vers l'interaction sélectionnée):"))
        main_layout.addWidget(self.path_display_text_edit)
        self.path_display_text_edit.setFixedHeight(100) # Hauteur fixe pour commencer

        # Bouton pour utiliser l'interaction sélectionnée
        self.use_context_button = QPushButton("Utiliser comme Contexte de Départ")
        self.use_context_button.setEnabled(False) # Désactivé par défaut
        self.use_context_button.clicked.connect(self._on_use_context_button_clicked)
        main_layout.addWidget(self.use_context_button)

        # Ajout du QTextEdit pour l'aperçu du contexte formaté
        self.context_preview_text_edit = QTextEdit()
        self.context_preview_text_edit.setReadOnly(True)
        self.context_preview_text_edit.setPlaceholderText("Aperçu du contexte formaté pour le LLM.")
        self.context_preview_text_edit.setStyleSheet("font-family: monospace; background: #f8f8f8;")
        main_layout.addWidget(QLabel("Aperçu du contexte injecté dans le LLM :"))
        main_layout.addWidget(self.context_preview_text_edit)
        self.context_preview_text_edit.setFixedHeight(140)

    def populate_interactions_list(self) -> None:
        """Peuple la liste avec les interactions existantes."""
        self.interactions_list_widget.clear()
        try:
            interactions = self._interaction_service.get_all()
            if not interactions:
                self.interactions_list_widget.addItem(UIText.NO_INTERACTION_FOUND)
                self.interactions_list_widget.setEnabled(False)
                return
            
            self.interactions_list_widget.setEnabled(True)
            for interaction in sorted(interactions, key=lambda i: i.title or i.interaction_id):
                display_text = f"{interaction.title or '(Sans titre)'} (ID: {interaction.interaction_id[:8]}...)"
                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, interaction.interaction_id)
                # Ajout case à cocher, décochée par défaut
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
                # Ne pas désactiver l'item !
                self.interactions_list_widget.addItem(item)
        except Exception as e:
            logger.error(f"Erreur lors du peuplement de la liste des interactions: {e}", exc_info=True)
            self.interactions_list_widget.addItem("Erreur lors du chargement des interactions.")
            self.interactions_list_widget.setEnabled(False)

    @Slot()
    def _on_interaction_selection_changed(self) -> None:
        """Appelé lorsqu'une interaction est sélectionnée dans la liste."""
        selected_items = self.interactions_list_widget.selectedItems()
        if not selected_items:
            self._current_selected_interaction_id = None
            self._current_path_interactions = []
            self.path_display_text_edit.setPlaceholderText("Sélectionnez une interaction pour voir son chemin.")
            self.path_display_text_edit.clear()
            self.use_context_button.setEnabled(False)
            self._update_context_preview()
            self._update_checkboxes([])
            return

        selected_item = selected_items[0]
        interaction_id = selected_item.data(Qt.ItemDataRole.UserRole)
        if not interaction_id or not isinstance(interaction_id, str):
             logger.warning(f"ID d'interaction non valide ou non trouvé pour l'item: {selected_item.text()}")
             self._current_selected_interaction_id = None
             self._current_path_interactions = []
             self.path_display_text_edit.clear()
             self.path_display_text_edit.setPlaceholderText("Erreur: ID d'interaction invalide.")
             self.use_context_button.setEnabled(False)
             self._update_context_preview()
             self._update_checkboxes([])
             return

        self._current_selected_interaction_id = interaction_id
        logger.info(f"Interaction sélectionnée: {self._current_selected_interaction_id}")

        try:
            self._current_path_interactions = self._interaction_service.get_dialogue_path(interaction_id)
            if self._current_path_interactions:
                path_texts = []
                for i, inter in enumerate(self._current_path_interactions):
                    text = f"{i+1}. {inter.title or '(Sans titre)'} (ID: {inter.interaction_id[:8]}...)"
                    # Si ce n'est pas la première interaction, essayer de trouver le choix qui y a mené
                    if i > 0:
                        prev_inter = self._current_path_interactions[i-1]
                        choice_text = self._interaction_service.get_choice_text_for_transition(prev_inter.interaction_id, inter.interaction_id)
                        if choice_text:
                            text += f"\n    ↳ Choix: \"{choice_text}\""
                    path_texts.append(text)
                self.path_display_text_edit.setText("\n".join(path_texts))
                self.use_context_button.setEnabled(True)
            else:
                self.path_display_text_edit.setText(UIText.NO_PATH_FOUND.format(interaction_id=interaction_id))
                self.use_context_button.setEnabled(False)
            # Met à jour les cases à cocher
            path_ids = [inter.interaction_id for inter in self._current_path_interactions]
            self._update_checkboxes(path_ids)
            self._update_context_preview()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du chemin de dialogue pour {interaction_id}: {e}", exc_info=True)
            self.path_display_text_edit.setText(f"Erreur lors de la récupération du chemin pour {interaction_id}.")
            self.use_context_button.setEnabled(False)
            self._update_checkboxes([])
            self._update_context_preview()

    @Slot()
    def _on_use_context_button_clicked(self) -> None:
        """Appelé lorsque le bouton 'Utiliser comme Contexte' est cliqué."""
        if self._current_selected_interaction_id and self._current_path_interactions:
            logger.info(f"Émission du signal previous_interaction_context_selected pour l'ID: {self._current_selected_interaction_id}")
            self.previous_interaction_context_selected.emit(self._current_selected_interaction_id, self._current_path_interactions)
        else:
            logger.warning("Tentative d'utiliser un contexte sans ID ou chemin sélectionné.")

    def refresh_list(self):
        """Rafraîchit la liste des interactions."""
        current_selection_id = self._current_selected_interaction_id
        self.populate_interactions_list()
        if current_selection_id:
            for i in range(self.interactions_list_widget.count()):
                item = self.interactions_list_widget.item(i)
                if item and item.data(Qt.ItemDataRole.UserRole) == current_selection_id:
                    item.setSelected(True)
                    self.interactions_list_widget.scrollToItem(item)
                    break
            else:
                # L'ID précédemment sélectionné n'existe plus, réinitialiser
                self._current_selected_interaction_id = None
                self._current_path_interactions = []
                self.path_display_text_edit.clear()
                self.path_display_text_edit.setPlaceholderText("Sélectionnez une interaction pour voir son chemin.")
                self.use_context_button.setEnabled(False)
                self._update_checkboxes([])
                self._update_context_preview()

    def _update_checkboxes(self, checked_ids: list[str]):
        for i in range(self.interactions_list_widget.count()):
            item = self.interactions_list_widget.item(i)
            item_id = item.data(Qt.ItemDataRole.UserRole)
            if item_id in checked_ids:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)

    def _update_context_preview(self):
        if not self._current_path_interactions:
            self.context_preview_text_edit.clear()
            self.context_preview_text_edit.setPlaceholderText("Aperçu du contexte formaté pour le LLM.")
            return
        # Utilise le formateur du ContextBuilder (3 interactions max, 512 tokens max pour l'aperçu)
        try:
            # On simule l'appel comme dans ContextBuilder.build_context
            old_prev = self._context_builder.previous_dialogue_context
            self._context_builder.previous_dialogue_context = self._current_path_interactions
            preview = self._context_builder._format_previous_dialogue_for_context(512)
            self.context_preview_text_edit.setPlainText(preview)
            self._context_builder.previous_dialogue_context = old_prev
        except Exception as e:
            self.context_preview_text_edit.setPlainText(f"[Erreur lors du formatage du contexte : {e}]")


if __name__ == '__main__':
    # Pour tester ce widget isolément
    from PySide6.QtWidgets import QApplication
    from ...services.repositories import InMemoryInteractionRepository
    from ...models.dialogue_structure.dialogue_elements import DialogueLineElement, PlayerChoicesBlockElement, PlayerChoiceOption

    app = QApplication(sys.argv)

    # Créer un mock d'InteractionService avec quelques données
    mock_repo = InMemoryInteractionRepository()
    service = InteractionService(mock_repo)

    # Créer des interactions de test
    inter1 = service.create_interaction(title="Introduction", prefix="intro")
    inter1.elements.append(DialogueLineElement(text="Bonjour."))
    inter1.next_interaction_id_if_no_choices = "scene1_start"
    service.save(inter1)

    inter2 = service.create_interaction(title="Début Scène 1", interaction_id="scene1_start")
    inter2.elements.append(DialogueLineElement(text="Que voulez-vous faire ?"))
    inter2.elements.append(PlayerChoicesBlockElement(choices=[
        PlayerChoiceOption(text="Explorer la grotte", next_interaction_id="scene1_grotte"),
        PlayerChoiceOption(text="Parler au garde", next_interaction_id="scene1_garde")
    ]))
    service.save(inter2)

    inter3_grotte = service.create_interaction(title="Dans la grotte", interaction_id="scene1_grotte")
    inter3_grotte.elements.append(DialogueLineElement(text="La grotte est sombre."))
    service.save(inter3_grotte)

    inter3_garde = service.create_interaction(title="Discussion Garde", interaction_id="scene1_garde")
    inter3_garde.elements.append(DialogueLineElement(text="Le garde vous ignore."))
    service.save(inter3_garde)

    widget = PreviousDialogueSelectorWidget(service)
    
    def handle_context_selected(interaction_id, path_interactions):
        print(f"---- CONTEXTE SÉLECTIONNÉ FINALEMENT ----")
        print(f"ID Interaction finale: {interaction_id}")
        print(f"Chemin ({len(path_interactions)} interactions):")
        for i, p_inter in enumerate(path_interactions):
            print(f"  {i+1}. {p_inter.title} (ID: {p_inter.interaction_id})")

    widget.previous_interaction_context_selected.connect(handle_context_selected)
    widget.setWindowTitle("Test PreviousDialogueSelectorWidget")
    widget.setMinimumSize(400, 500)
    widget.show()

    sys.exit(app.exec()) 