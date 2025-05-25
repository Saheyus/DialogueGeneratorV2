import sys
import uuid
from typing import Optional, List

"""
Widget pour afficher et manipuler une séquence d'interactions.

Gère:
- L'affichage de la liste des interactions
- La sélection d'une interaction (émission du signal interaction_selected)
- L'ajout, la suppression et la réorganisation des interactions
- Le chargement depuis et la sauvegarde vers le service d'interactions

Notes techniques:
- Le signal interaction_selected utilise un type 'object' pour pouvoir accepter à la fois des UUID et des identifiants string
- Les méthodes _add_interaction_to_list_widget et refresh_list gèrent les identifiants qui ne sont pas des UUID valides
- Toutes les exceptions sont attrapées pour éviter des crashs de l'UI
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QListWidgetItem, QMessageBox, QAbstractItemView, QLabel, QMenu
)
from PySide6.QtCore import Signal, Qt, Slot
from PySide6.QtGui import QAction, QDropEvent, QDragEnterEvent, QDragMoveEvent

# --- Correction des imports robustes pour InteractionService et Interaction ---
try:
    # Import absolu (cas normal application)
    from services.interaction_service import InteractionService
except ImportError:
    try:
        # Import relatif (cas test ou module)
        from ...services.interaction_service import InteractionService
    except ImportError:
        # Fallback pour exécution directe isolée
        import os
        from pathlib import Path
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir.parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        try:
            from services.interaction_service import InteractionService
        except ImportError as e:
            raise ImportError("Impossible d'importer InteractionService. Vérifiez l'arborescence des packages et les __init__.py.") from e

# Import absolu unique pour Interaction
from models.dialogue_structure.interaction import Interaction

class InteractionSequenceWidget(QWidget):
    interaction_selected = Signal(object)  # Émis avec l'ID de l'interaction sélectionnée (UUID ou str)
    sequence_changed = Signal()  # Émis si la séquence est modifiée (ajout, suppression, réorganisation)

    def __init__(self, interaction_service: InteractionService, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.interaction_service = interaction_service
        self._init_ui()
        self._load_interactions()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0) # Pas de marges pour mieux s'intégrer

        # Titre du widget
        title_label = QLabel("Séquence d'Interactions")
        title_label.setStyleSheet("font-weight: bold;") # Optionnel: mettre en gras
        layout.addWidget(title_label)

        self.interaction_list_widget = QListWidget()
        self.interaction_list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.interaction_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.interaction_list_widget.setStyleSheet("""
            QListWidget::item { 
                padding: 5px; 
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #d0e4f8;
                color: black; /* Assurer la lisibilité du texte sélectionné */
            }
        """)
        layout.addWidget(self.interaction_list_widget)

        # Boutons d'action
        buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("Ajouter")
        self.remove_button = QPushButton("Supprimer")

        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.remove_button)
        layout.addLayout(buttons_layout)

        # Connexions
        self.add_button.clicked.connect(self._on_add_interaction)
        self.remove_button.clicked.connect(self._on_remove_interaction)
        self.interaction_list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        self.interaction_list_widget.model().rowsMoved.connect(self._on_rows_moved)

        # Menu contextuel
        self.interaction_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.interaction_list_widget.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, position):
        context_menu = QMenu(self)
        edit_action = QAction("Éditer", self)
        remove_action = QAction("Supprimer", self)
        
        context_menu.addAction(edit_action)
        context_menu.addAction(remove_action)
        
        edit_action.triggered.connect(self._on_edit_interaction_button_clicked)
        remove_action.triggered.connect(self._on_remove_interaction)
        
        # Désactiver les actions si aucun item n'est sélectionné
        selected_item = self.interaction_list_widget.currentItem()
        edit_action.setEnabled(selected_item is not None)
        remove_action.setEnabled(selected_item is not None)
        
        context_menu.exec(self.interaction_list_widget.mapToGlobal(position))

    def _load_interactions(self):
        self.interaction_list_widget.clear()
        # Forcer la relecture depuis le disque
        repo_type = type(self.interaction_service._repo).__name__
        print(f"Chargement des interactions depuis le service, type de repository: {repo_type}")
        if hasattr(self.interaction_service._repo, 'storage_dir'):
            print(f"Dossier de stockage: {self.interaction_service._repo.storage_dir}")
        interactions = self.interaction_service.get_all()  # get_all() lit les fichiers à jour
        print(f"Nombre d'interactions chargées: {len(interactions)}")
        for interaction in interactions:
            print(f"Interaction: {interaction.interaction_id}, titre: {getattr(interaction, 'title', '<sans titre>')}")
            self._add_interaction_to_list_widget(interaction)
        self._update_buttons_state()

    def _add_interaction_to_list_widget(self, interaction: Interaction):
        item_text = interaction.title if hasattr(interaction, 'title') and interaction.title else f"Interaction Sans Titre ({str(interaction.interaction_id)[:8]})"
        item = QListWidgetItem(item_text)
        
        # Stockage de l'ID brut (non UUID) dans l'item
        interaction_id_str = str(interaction.interaction_id)
        print(f"[DEBUG] _add_interaction_to_list_widget: item='{item_text}', ID={interaction_id_str}")
        
        # Tenter de convertir en UUID si possible, sinon stocker l'ID brut
        try:
            # Vérifier si l'ID est un UUID valide
            if len(interaction_id_str) == 36 and interaction_id_str.count('-') == 4:
                uuid_obj = uuid.UUID(interaction_id_str)
                item.setData(Qt.ItemDataRole.UserRole, uuid_obj)
            else:
                # Si ce n'est pas un UUID standard, stocker l'ID brut
                item.setData(Qt.ItemDataRole.UserRole, interaction_id_str)
        except ValueError:
            # En cas d'erreur (format non valide), stocker l'ID brut
            item.setData(Qt.ItemDataRole.UserRole, interaction_id_str)
        
        self.interaction_list_widget.addItem(item)

    @Slot()
    def _on_add_interaction(self):
        new_id = str(uuid.uuid4()) 
        new_interaction_obj = Interaction(interaction_id=new_id)
        new_interaction_obj.title = "Nouvelle Interaction" 
        self.interaction_service.save(new_interaction_obj)
        
        self._add_interaction_to_list_widget(new_interaction_obj)
        self.interaction_list_widget.setCurrentRow(self.interaction_list_widget.count() - 1)
        self.sequence_changed.emit()
        self.interaction_selected.emit(uuid.UUID(new_interaction_obj.interaction_id))
        self._update_buttons_state()

    @Slot()
    def _on_remove_interaction(self):
        current_item = self.interaction_list_widget.currentItem()
        if current_item:
            interaction_id = current_item.data(Qt.ItemDataRole.UserRole)
            if interaction_id:
                confirm = QMessageBox.question(self, "Confirmer Suppression", 
                                             f"Voulez-vous vraiment supprimer l'interaction '{current_item.text()}' ?",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if confirm == QMessageBox.StandardButton.Yes:
                    self.interaction_service.delete(str(interaction_id))
                    self.interaction_list_widget.takeItem(self.interaction_list_widget.row(current_item))
                    self.sequence_changed.emit()
                    # Émettre un signal qu'aucune interaction n'est sélectionnée après suppression
                    if self.interaction_list_widget.count() == 0:
                        self.interaction_selected.emit(None)
                    elif self.interaction_list_widget.currentItem():
                        selected_id = self.interaction_list_widget.currentItem().data(Qt.ItemDataRole.UserRole)
                        self.interaction_selected.emit(selected_id)
                    else: # Si le dernier item a été enlevé et qu'il n'y a plus de sélection courante
                        self.interaction_selected.emit(None)
        self._update_buttons_state()

    @Slot()
    def _on_selection_changed(self):
        current_item = self.interaction_list_widget.currentItem()
        print(f"[DEBUG] _on_selection_changed appelé, current_item={current_item}")
        if current_item:
            interaction_id = current_item.data(Qt.ItemDataRole.UserRole)
            print(f"[DEBUG] Émission interaction_selected avec interaction_id={interaction_id}, type={type(interaction_id)}")
            self.interaction_selected.emit(interaction_id)
        else:
            print(f"[DEBUG] Émission interaction_selected avec None car aucun item sélectionné")
            self.interaction_selected.emit(None)
        self._update_buttons_state()

    @Slot(uuid.UUID)
    def _on_edit_interaction_button_clicked(self):
        current_item = self.interaction_list_widget.currentItem()
        if current_item:
            interaction_id = current_item.data(Qt.ItemDataRole.UserRole)
            if interaction_id:
                self.interaction_selected.emit(interaction_id)
        else:
            QMessageBox.information(self, "Aucune Sélection", "Veuillez sélectionner une interaction à éditer.")

    def _on_rows_moved(self, parent, start, end, destination, row):
        # Mettre à jour l'ordre dans le service si nécessaire
        # Ceci est un peu plus complexe car il faut mapper les positions de la QListWidget
        # à l'ordre réel dans le service.
        # Pour l'instant, on émet juste que la séquence a changé.
        # Une implémentation plus robuste mettrait à jour l'ordre dans interaction_service.
        ordered_ids = []
        for i in range(self.interaction_list_widget.count()):
            item = self.interaction_list_widget.item(i)
            ordered_ids.append(item.data(Qt.ItemDataRole.UserRole))
        
        self.interaction_service.reorder_interactions(ordered_ids)
        self.sequence_changed.emit()
        # Potentiellement émettre un signal avec la nouvelle sélection si elle change
        current_item = self.interaction_list_widget.currentItem()
        if current_item:
            self.interaction_selected.emit(current_item.data(Qt.ItemDataRole.UserRole))
        else:
            self.interaction_selected.emit(None)
        self._update_buttons_state()

    def _update_buttons_state(self):
        has_selection = self.interaction_list_widget.currentItem() is not None
        self.remove_button.setEnabled(has_selection)

    def get_selected_interaction_id(self) -> Optional[uuid.UUID]:
        current_item = self.interaction_list_widget.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None

    def refresh_list(self, select_id: Optional[str] = None):
        """Rafraîchit la liste des interactions à partir du service.
        
        Args:
            select_id: Optionnel, ID de l'interaction à sélectionner après rafraîchissement
        """
        try:
            # Sauvegarder l'état actuel de la sélection si aucun ID spécifique n'est fourni
            current_selected_id = None
            if select_id is None and self.interaction_list_widget.currentItem() is not None:
                current_row = self.interaction_list_widget.currentRow()
                if 0 <= current_row < self.interaction_list_widget.count():
                    current_selected_id = str(self.interaction_list_widget.item(current_row).data(Qt.ItemDataRole.UserRole))
                    
            # Obtenir le type du repository pour le logging
            repo_type = type(self.interaction_service._repo).__name__
            print(f"Rafraîchissement de la liste d'interactions depuis {repo_type}")
            
            # Afficher le dossier de stockage si c'est un FileInteractionRepository
            if hasattr(self.interaction_service._repo, 'storage_dir'):
                print(f"Dossier de stockage: {self.interaction_service._repo.storage_dir}")
                
            # Obtenir toutes les interactions à jour
            self.interaction_list_widget.clear()
            self.interactions = self.interaction_service.get_all()
            print(f"Nombre d'interactions chargées: {len(self.interactions)}")
            
            # Construire la liste
            self.interaction_ids = []
            for interaction in self.interactions:
                title_display = interaction.title if hasattr(interaction, 'title') and interaction.title else str(interaction.interaction_id)
                item = QListWidgetItem(title_display)
                
                # S'assurer que l'ID est bien associé à l'item
                interaction_id_str = str(interaction.interaction_id)
                self.interaction_ids.append(interaction_id_str)
                
                # Tenter de convertir en UUID si possible, sinon stocker l'ID brut
                try:
                    # Vérifier si l'ID est un UUID valide
                    if len(interaction_id_str) == 36 and interaction_id_str.count('-') == 4:
                        uuid_obj = uuid.UUID(interaction_id_str)
                        item.setData(Qt.ItemDataRole.UserRole, uuid_obj)
                    else:
                        # Si ce n'est pas un UUID standard, stocker l'ID brut
                        item.setData(Qt.ItemDataRole.UserRole, interaction_id_str)
                except ValueError:
                    # En cas d'erreur (format non valide), stocker l'ID brut
                    item.setData(Qt.ItemDataRole.UserRole, interaction_id_str)
                
                print(f"[DEBUG] Ajout item '{title_display}' avec ID={interaction_id_str}")
                self.interaction_list_widget.addItem(item)
            
            # Sélectionner l'interaction spécifiée ou restaurer la sélection précédente
            target_id = select_id or current_selected_id
            if target_id and target_id in self.interaction_ids:
                target_index = self.interaction_ids.index(target_id)
                self.interaction_list_widget.setCurrentRow(target_index)
                print(f"Interaction sélectionnée après rafraîchissement: {target_id}")
            elif self.interaction_list_widget.count() > 0:
                # Par défaut, sélectionner la première interaction si la liste n'est pas vide
                self.interaction_list_widget.setCurrentRow(0)
                
            # Signaler que la séquence a changé
            self.sequence_changed.emit()
            
        except Exception as e:
            print(f"Erreur lors du rafraîchissement de la liste d'interactions: {e}")
            # Ne pas interrompre l'UI en cas d'erreur

    # --- Méthodes pour gérer le Drag and Drop (simplifié) ---
    # QListWidget gère déjà beaucoup en interne avec InternalMove
    # Mais on pourrait vouloir surcharger pour plus de contrôle ou de validation.

    # def dragEnterEvent(self, event: QDragEnterEvent):
    #     if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist'): # Vérifier si ce sont des items de la liste
    #         event.acceptProposedAction()
    #     else:
    #         super().dragEnterEvent(event)

    # def dragMoveEvent(self, event: QDragMoveEvent):
    #     super().dragMoveEvent(event) # Laisser QListWidget gérer le feedback visuel

    # def dropEvent(self, event: QDropEvent):
    #     # La logique de déplacement est gérée par QListWidget avec InternalMove
    #     # Le signal model().rowsMoved sera émis, que nous capturons déjà.
    #     super().dropEvent(event) 
    #     # self.sequence_changed.emit() # Déjà émis par _on_rows_moved

# Pour tester le widget isolément (si besoin)
if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    import sys

    # Créer un service d'interaction en mémoire pour le test
    class InMemoryInteractionRepository:
        def __init__(self):
            self.interactions = {}
            self.order = []

        def get_all(self) -> List[Interaction]:
            return [self.interactions[id] for id in self.order if id in self.interactions]

        def get_by_id(self, interaction_id: uuid.UUID) -> Optional[Interaction]:
            return self.interactions.get(interaction_id)

        def add(self, interaction: Interaction) -> Interaction:
            self.interactions[interaction.id] = interaction
            if interaction.id not in self.order:
                self.order.append(interaction.id)
            return interaction

        def update(self, interaction: Interaction) -> Optional[Interaction]:
            if interaction.id in self.interactions:
                self.interactions[interaction.id] = interaction
                return interaction
            return None

        def delete(self, interaction_id: uuid.UUID) -> bool:
            if interaction_id in self.interactions:
                del self.interactions[interaction_id]
                if interaction_id in self.order:
                    self.order.remove(interaction_id)
                return True
            return False
        
        def reorder(self, ordered_ids: List[uuid.UUID]):
            # S'assurer que tous les IDs sont valides et uniques
            valid_ids = [id_ for id_ in ordered_ids if id_ in self.interactions]
            # S'assurer qu'il n'y a pas de doublons et que tous les IDs existants sont présents
            if len(set(valid_ids)) == len(valid_ids) and set(valid_ids) == set(self.order):
                self.order = valid_ids
            else:
                # Gérer l'erreur ou resynchroniser
                print("Error in reordering: ID mismatch or duplicates.")
                # Pour la simplicité, on ne change rien si les IDs ne correspondent pas parfaitement
                pass

    app = QApplication(sys.argv)
    # Créer une instance du service et du repository factice
    repo = InMemoryInteractionRepository()
    interaction_service_instance = InteractionService(repo)

    # Ajouter quelques interactions de test
    interaction_service_instance.create_interaction(title="Saluer le joueur")
    interaction_service_instance.create_interaction(title="Proposer une quête")
    interaction_service_instance.create_interaction(title="Dire au revoir")

    widget = InteractionSequenceWidget(interaction_service_instance)
    widget.setWindowTitle("Test Interaction Sequence Widget")
    widget.resize(400, 300)
    widget.show()

    @Slot(uuid.UUID)
    def on_interaction_selected_test(interaction_id):
        if interaction_id:
            print(f"[TEST SLOT] Interaction sélectionnée: {interaction_id}")
            interaction = interaction_service_instance.get_interaction(interaction_id)
            if interaction: print(f"          Titre: {interaction.title}")
        else:
            print("[TEST SLOT] Aucune interaction sélectionnée")

    @Slot()
    def on_sequence_changed_test():
        print("[TEST SLOT] Séquence modifiée. Nouvel ordre:")
        for i, interaction in enumerate(interaction_service_instance.get_all_interactions()):
            print(f"  {i+1}. {interaction.title} ({interaction.id})")
            
    sys.exit(app.exec()) 
