from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal, Slot
import logging
import uuid
from typing import Optional

from .interaction_sequence_widget import InteractionSequenceWidget
from .interaction_editor_widget import InteractionEditorWidget
from services.interaction_service import InteractionService
from models.dialogue_structure.interaction import Interaction

logger = logging.getLogger(__name__)

class InteractionsTabWidget(QWidget):
    interaction_selected_in_tab = Signal(uuid.UUID) 
    sequence_changed_in_tab = Signal()
    edit_interaction_requested_in_tab = Signal(uuid.UUID)
    interaction_changed_in_tab = Signal(Interaction)

    def __init__(self, interaction_service: InteractionService, parent=None):
        super().__init__(parent)
        self.interaction_service = interaction_service
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)

        self.interaction_sequence_widget = InteractionSequenceWidget(
            interaction_service=self.interaction_service
        )
        layout.addWidget(self.interaction_sequence_widget)

        self.interaction_editor_widget = InteractionEditorWidget(
            interaction_service=self.interaction_service
        )
        layout.addWidget(self.interaction_editor_widget)
        layout.addStretch(1)
        
        self.interaction_sequence_widget.interaction_selected.connect(self._handle_interaction_selected_from_sequence)
        self.interaction_sequence_widget.sequence_changed.connect(self.sequence_changed_in_tab.emit)
        self.interaction_sequence_widget.interaction_selected.connect(self.edit_interaction_requested_in_tab.emit) 
        self.interaction_editor_widget.interaction_changed.connect(self._handle_interaction_changed_from_editor)

    @Slot(uuid.UUID)
    def _handle_interaction_selected_from_sequence(self, interaction_id: Optional[uuid.UUID]):
        logger.debug(f"InteractionsTabWidget: Interaction {interaction_id} sélectionnée dans la séquence.")
        interaction = self.interaction_service.get_by_id(str(interaction_id)) if interaction_id else None
        self.interaction_editor_widget.set_interaction(interaction)
        if interaction_id:
            self.interaction_selected_in_tab.emit(interaction_id)
        else:
            # Émettre un signal avec None ou un UUID vide si nécessaire, ou ne rien émettre.
            # Pour l'instant, on n'émet que si un ID valide est présent.
            pass 

    @Slot(Interaction)
    def _handle_interaction_changed_from_editor(self, interaction: Interaction):
        logger.debug(f"InteractionsTabWidget: Interaction {interaction.interaction_id} modifiée dans l'éditeur.")
        self.interaction_sequence_widget.refresh_list() 
        self.interaction_changed_in_tab.emit(interaction)
        
    def get_current_selected_interaction_id(self) -> Optional[uuid.UUID]:
        return self.interaction_sequence_widget.get_current_selected_id()

    def refresh_sequence_list(self, select_id: Optional[str] = None):
        self.interaction_sequence_widget.refresh_list(select_id=select_id)

    def display_interaction_in_editor(self, interaction: Optional[Interaction]):
        self.interaction_editor_widget.set_interaction(interaction)

    def clear_editor(self):
        self.interaction_editor_widget.clear_fields() 