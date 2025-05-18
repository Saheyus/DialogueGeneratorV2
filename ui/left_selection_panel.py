from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QCheckBox, QHBoxLayout, QScrollArea, QFrame, QGroupBox, QPushButton, QSizePolicy, QSpacerItem, QAbstractItemView, QTabWidget)
from PySide6.QtCore import Qt, Signal, Slot, QSortFilterProxyModel, QRegularExpression, QTimer
from PySide6.QtGui import QPalette, QColor
import logging
from functools import partial
from pathlib import Path
from .. import config_manager

logger = logging.getLogger(__name__)

class LeftSelectionPanel(QWidget):
    """Manages the UI elements for selecting context items (characters, locations, etc.).

    This panel contains filterable lists for each category of GDD elements.
    It emits signals when selections change or items are clicked for detail view.
    """
    # Emits: category_key (str), item_text (str), category_data (list), category_singular_name (str)
    item_clicked_for_details: Signal = Signal(str, str, list, str) 
    context_selection_changed: Signal = Signal() # Émis lorsque l'état coché d'un item change
    # selection_changed: Signal = Signal(list) # List of selected item names - Redondant avec context_selection_changed si ce dernier est bien utilisé
    # item_focused: Signal = Signal(str, str) # item_name, category_key - Semble non utilisé, à vérifier

    def __init__(self, context_builder, parent=None):
        """Initializes the LeftSelectionPanel.

        Args:
            context_builder: Instance of ContextBuilder to access GDD data.
            parent: The parent widget.
        """
        super().__init__(parent)
        self.context_builder = context_builder
        self.filters = {}
        self.lists = {}
        self.filter_edits = {}
        self.category_data_map = {}
        self.category_display_names = {}
        self.category_item_name_keys = {}
        self.category_name_key_priorities = {}
        self.details_panel_instance = None # Ajout pour stocker la référence

        # Define categories to be displayed, their data keys, display names, and primary name keys
        self.categories_config = [
            {"key": "characters", "attr": "characters", "display_name": "Characters", "singular_name": "Character", "name_keys": ["Nom"]},
            {"key": "locations", "attr": "locations", "display_name": "Locations", "singular_name": "Location", "name_keys": ["Nom"]},
            {"key": "items", "attr": "items", "display_name": "Items", "singular_name": "Item", "name_keys": ["Nom"]},
            {"key": "species", "attr": "species", "display_name": "Species", "singular_name": "Species", "name_keys": ["Nom"]},
            {"key": "communities", "attr": "communities", "display_name": "Communities", "singular_name": "Community", "name_keys": ["Nom"]},
            # 'dialogues_examples' retiré pour éviter le doublon avec Yarn Files
        ]
        # Add a new static category for existing Yarn files
        self.yarn_files_category_key = "existing_yarn_files"
        self.yarn_files_display_name = "Yarn Files (Project)"
        self.yarn_files_singular_name = "Yarn File"

        self.gdd_data_loaded = False # Flag to track if GDD data has been loaded

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0,0,0,0) # Ajuster les marges pour le QTabWidget
        self.main_layout.setSpacing(0) # Ajuster l'espacement pour le QTabWidget

        self._setup_ui_elements()
        self._connect_signals()

        # Placeholder for Yarn files data (will be paths)
        self.category_data_map[self.yarn_files_category_key] = [] 

    def _setup_ui_elements(self):
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget, 1)

        # --- Onglet de Sélection ---
        selection_tab_widget = QWidget()
        self.selection_layout = QVBoxLayout(selection_tab_widget) # Renommé pour clarté
        self.selection_layout.setContentsMargins(5, 5, 5, 5)
        self.selection_layout.setSpacing(2)

        # Create UI for GDD categories
        for category_config in self.categories_config:
            cat_key = category_config["key"]
            self.category_display_names[cat_key] = category_config["display_name"]
            self.category_item_name_keys[cat_key] = category_config["name_keys"]
            
            group_box, list_widget, filter_edit = self._create_category_group(
                category_config["display_name"]
            )
            self.lists[cat_key] = list_widget
            self.filter_edits[cat_key] = filter_edit
            self.selection_layout.addWidget(group_box)

        # Add a separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        self.selection_layout.addWidget(separator)

        # Create UI for Existing Yarn Files
        yarn_group_box, yarn_list_widget, yarn_filter_edit = self._create_category_group(
            self.yarn_files_display_name,
            is_yarn_file_list=True # Differentiate for click handling if needed
        )
        self.lists[self.yarn_files_category_key] = yarn_list_widget
        self.filter_edits[self.yarn_files_category_key] = yarn_filter_edit
        self.selection_layout.addWidget(yarn_group_box)
        self.category_display_names[self.yarn_files_category_key] = self.yarn_files_display_name
        # For yarn files, the "name key" is implicitly the file path or name

        self.selection_layout.addStretch(1) # Add stretch to push everything up
        
        self.tab_widget.addTab(selection_tab_widget, "Sélection")

    def add_details_panel_as_tab(self, details_panel: QWidget):
        """Ajoute le panneau de détails comme un onglet."""
        if hasattr(self, 'tab_widget'):
            self.tab_widget.addTab(details_panel, "Détails")
            self.details_panel_instance = details_panel # Stocker la référence
            logger.info("DetailsPanel ajouté comme onglet dans LeftSelectionPanel.")
        else:
            logger.error("tab_widget non trouvé dans LeftSelectionPanel, impossible d'ajouter l'onglet Détails.")

    def _create_category_group(self, title: str, is_yarn_file_list: bool = False):
        group_box = QGroupBox(title)
        group_box.setStyleSheet("QGroupBox { font-weight: bold; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 3px 5px; }")
        group_layout = QVBoxLayout(group_box)
        group_layout.setContentsMargins(3,3,3,3)
        group_layout.setSpacing(3)

        filter_edit = QLineEdit()
        filter_edit.setPlaceholderText(f"Filter {title}...")
        group_layout.addWidget(filter_edit)

        list_widget = QListWidget()
        list_widget.setStyleSheet("QListWidget::item { padding: 2px; }")
        list_widget.setSpacing(1)  # Réduit l'espacement entre les items
        
        if is_yarn_file_list:
            list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection) # Single selection for yarn files
            list_widget.itemClicked.connect(
                lambda item, lw=list_widget: self._on_yarn_file_item_clicked(lw.itemWidget(item) if lw.itemWidget(item) else item)
            )
        else:
            list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection) # Explicitly set for GDD
            # Connect for GDD items - this lambda needs to be specific to the category
            list_widget.itemClicked.connect(
                lambda item, lw=list_widget, cat_title=title: self._on_gdd_list_item_clicked(lw.itemWidget(item) if lw.itemWidget(item) else item, cat_title)
            )

        group_layout.addWidget(list_widget)
        return group_box, list_widget, filter_edit

    def _on_gdd_list_item_clicked(self, item_widget_or_list_item: QWidget | QListWidgetItem, category_title: str):
        # Find category_key from category_title
        category_key = None
        for key, name in self.category_display_names.items():
            if name == category_title:
                category_key = key
                break
        
        if not category_key or category_key == self.yarn_files_category_key:
            logger.debug(f"GDD item click ignored or category_key not found for title: {category_title}")
            return

        item_text = ""
        is_checkbox_item = False
        if isinstance(item_widget_or_list_item, QWidget) and hasattr(item_widget_or_list_item, 'text_label'): # Assuming CheckableListItemWidget
            item_text = item_widget_or_list_item.text_label.text()
            is_checkbox_item = True
        elif isinstance(item_widget_or_list_item, QListWidgetItem):
            item_text = item_widget_or_list_item.text()
        else:
            logger.warning("Clicked item is of an unexpected type.")
            return

        logger.debug(f"GDD Item clicked: '{item_text}' in category '{category_key}' (Title: '{category_title}')")
        category_data = self.category_data_map.get(category_key, [])
        singular_name = self._get_singular_name_for_category_key(category_key)
        self.item_clicked_for_details.emit(category_key, item_text, category_data, singular_name)

        if self.details_panel_instance and hasattr(self.tab_widget, 'setCurrentWidget'):
            self.tab_widget.setCurrentWidget(self.details_panel_instance)
            logger.debug(f"Onglet 'Détails' activé après clic sur item GDD '{item_text}'.")

    def _on_yarn_file_item_clicked(self, item_widget_or_list_item: QWidget | QListWidgetItem):
        item_text = ""
        if isinstance(item_widget_or_list_item, QWidget) and hasattr(item_widget_or_list_item, 'text_label'):
            item_text = item_widget_or_list_item.text_label.text() 
        elif isinstance(item_widget_or_list_item, QListWidgetItem):
            item_text = item_widget_or_list_item.text()
        else:
            logger.warning("Clicked yarn file item is of an unexpected type.")
            return

        logger.info(f"Yarn file selected: {item_text}")
        # The item_text here will be the relative path of the yarn file.
        # We need the full path to read it.
        dialogues_base_path = config_manager.get_unity_dialogues_path()
        if dialogues_base_path:
            full_path = dialogues_base_path / item_text
            # Emit a signal or call a method on MainWindow/DetailsPanel to show content
            # For now, let's just emit item_clicked_for_details with special handling
            # The 'category_data' for yarn files will be the full path string
            self.item_clicked_for_details.emit(self.yarn_files_category_key, str(full_path), [str(full_path)], self.yarn_files_singular_name)
            if self.details_panel_instance and hasattr(self.tab_widget, 'setCurrentWidget'):
                self.tab_widget.setCurrentWidget(self.details_panel_instance)
                logger.debug(f"Onglet 'Détails' activé après clic sur fichier Yarn '{item_text}'.")
        else:
            logger.warning("Unity dialogues path not configured, cannot get full path for yarn file.")

    def populate_all_lists(self):
        logger.info("Populating all GDD lists in LeftSelectionPanel...")
        self.gdd_data_loaded = False # Reset flag at the beginning

        if not self.context_builder:
            logger.warning("LeftSelectionPanel: self.context_builder is None. Cannot populate GDD lists.")
            # Populate with placeholder messages
            for cat_key in self.lists:
                if cat_key != self.yarn_files_category_key:
                    list_widget = self.lists.get(cat_key)
                    if list_widget:
                        list_widget.clear()
                        list_widget.addItem(QListWidgetItem("(ContextBuilder not available)"))
            self.populate_yarn_files_list() # Attempt to populate yarn files even if GDD fails
            return

        logger.info(f"  LeftSelectionPanel: self.context_builder exists. Checking direct attributes for GDD data.")

        for category_config in self.categories_config:
            cat_key = category_config["key"]
            attr_name = category_config.get("attr", cat_key)
            name_keys = self.category_item_name_keys.get(cat_key, ["Nom"])
            
            logger.info(f"Processing GDD category: '{cat_key}' (attr: '{attr_name}', name_keys: {name_keys})")
            items_data = getattr(self.context_builder, attr_name, [])
            self.category_data_map[cat_key] = items_data
            logger.info(f"  Category '{cat_key}': Found {len(items_data)} raw items from context_builder attribute '{attr_name}'.")
            
            display_items = []
            if isinstance(items_data, list):
                if not items_data: # Si la liste items_data est vide
                    logger.info(f"  Category '{cat_key}': Raw items list is empty for attr '{attr_name}'.")
                for idx, item_dict in enumerate(items_data):
                    if isinstance(item_dict, dict):
                        item_display_name = "Unknown Item (error in name key)"
                        for name_key in name_keys:
                            if name_key in item_dict and item_dict[name_key] is not None and str(item_dict[name_key]).strip() != "":
                                item_display_name = str(item_dict[name_key])
                                break
                        display_items.append(item_display_name)
                    elif isinstance(item_dict, str):
                        display_items.append(item_dict)
                    else:
                        logger.warning(f"    Item {idx} in '{cat_key}' is not a dict or str: {type(item_dict)}. Value: {item_dict}")
            elif items_data is None:
                 logger.warning(f"  Category '{cat_key}': items_data is None for attr '{attr_name}'. This shouldn't happen with .get default.")
            else:
                logger.warning(f"  Data for category '{cat_key}' attribute '{attr_name}' is not a list (it's {type(items_data)}). Value: {items_data}")

            logger.info(f"  Category '{cat_key}': Generated {len(display_items)} display items.")
            if not display_items and items_data: 
                 logger.warning(f"  Category '{cat_key}': No display items generated despite having {len(items_data)} raw items. Check name_keys ({name_keys}) and data structure of items.")

            # Call _populate_list_widget. The restore_checked_states parameter is removed from _populate_list_widget.
            if cat_key in self.lists:
                 self._populate_list_widget(self.lists[cat_key], display_items, cat_key)
            else:
                 logger.error(f"List widget for category key '{cat_key}' not found in self.lists.")

        # If context_builder is available, we consider data potentially loaded and ready for settings restoration attempt.
        if self.context_builder:
            self.gdd_data_loaded = True
            logger.info("LeftSelectionPanel: Finished processing GDD categories. gdd_data_loaded set to True as ContextBuilder is present.")
        
        logger.info("All GDD lists processing finished.")
        self.populate_yarn_files_list()

    def populate_yarn_files_list(self):
        logger.info("Populating existing Yarn files list...")
        list_widget = self.lists.get(self.yarn_files_category_key)
        if not list_widget:
            logger.error("Yarn files list widget not found.")
            return

        dialogues_path = config_manager.get_unity_dialogues_path()
        if not dialogues_path:
            logger.warning("Unity dialogues path not configured. Cannot list Yarn files.")
            list_widget.clear()
            list_widget.addItem(QListWidgetItem("Unity dialogues path not configured."))
            return

        yarn_files = config_manager.list_yarn_files(dialogues_path, recursive=True)
        self.category_data_map[self.yarn_files_category_key] = yarn_files # Store Path objects

        display_items = []
        for file_path in yarn_files:
            # Display relative path from the dialogues_path for brevity
            try:
                relative_path = file_path.relative_to(dialogues_path)
                display_items.append(str(relative_path))
            except ValueError:
                # Should not happen if list_yarn_files works correctly from dialogues_path
                display_items.append(file_path.name) 
        
        # Using _populate_list_widget directly for non-checkable items
        # It expects a category_key for checkbox state loading/saving, which is not applicable here.
        # So, we adapt or do it manually.
        list_widget.clear()
        if not display_items:
            list_widget.addItem(QListWidgetItem("(No .yarn files found)"))
        else:
            for item_text in display_items:
                q_list_item = QListWidgetItem(item_text)
                list_widget.addItem(q_list_item)
        logger.info(f"Populated Yarn files list with {len(display_items)} items.")

    def _populate_list_widget(self, list_widget: QListWidget, items: list[str], category_key: str): # restore_checked_states param removed
        current_filter_text = ""
        # Ensure filter_edit for the category_key exists before accessing its text
        if category_key in self.filter_edits:
            current_filter_text = self.filter_edits[category_key].text()
        
        list_widget.clear()

        if not items:
            list_widget.addItem(QListWidgetItem("(No items for this category or filter)"))
            return

        # No restoration logic here. This is handled by load_settings -> _set_checked_list_items

        for item_text in items:
            if current_filter_text and current_filter_text.lower() not in item_text.lower():
                continue
            
            item_widget = CheckableListItemWidget(item_text, parent=list_widget)
            # Checkbox state is not set here. It will be set by _set_checked_list_items via load_settings.
            
            # Connect the checkbox's stateChanged signal
            # item_widget is newly created, so no need to disconnect first.
            item_widget.checkbox.stateChanged.connect(lambda: self.context_selection_changed.emit())

            q_list_item = QListWidgetItem(list_widget) 
            q_list_item.setSizeHint(item_widget.sizeHint())
            list_widget.addItem(q_list_item) 
            list_widget.setItemWidget(q_list_item, item_widget)

    def _connect_signals(self):
        for cat_key, filter_edit in self.filter_edits.items():
            # Pass the correct list_widget and category_key to the lambda
            list_widget = self.lists[cat_key]
            # Check if the category is for yarn files to connect to the correct handler
            if cat_key == self.yarn_files_category_key:
                 filter_edit.textChanged.connect(
                    lambda text, lw=list_widget, ck=cat_key: self._filter_yarn_list(lw, ck, text)
                )
            else:
                filter_edit.textChanged.connect(
                    lambda text, lw=list_widget, ck=cat_key: self._filter_gdd_list(lw, ck, text)
                )
    
    def _filter_gdd_list(self, list_widget_to_filter: QListWidget, category_key: str, filter_text: str):
        """Filters the GDD items in the specified list widget based on filter_text."""
        items_data = self.category_data_map.get(category_key, [])
        name_keys = self.category_item_name_keys.get(category_key, ["Nom"])
        display_items = []
        # This logic is similar to initial population but without checkboxes for filtering only strings
        if isinstance(items_data, list):
            for item_dict in items_data:
                if isinstance(item_dict, dict):
                    item_display_name = "Unknown Item"
                    for name_key in name_keys:
                        if name_key in item_dict and item_dict[name_key]:
                            item_display_name = str(item_dict[name_key])
                            break
                    if filter_text.lower() in item_display_name.lower():
                        display_items.append(item_display_name)
                elif isinstance(item_dict, str):
                    if filter_text.lower() in item_dict.lower():
                        display_items.append(item_dict)
        
        # Temporarily disconnect stateChanged to avoid mass signals during repopulation
        for i in range(list_widget_to_filter.count()):
            item = list_widget_to_filter.item(i)
            widget = list_widget_to_filter.itemWidget(item)
            if widget and hasattr(widget, 'checkbox'):
                try:
                    # Tenter de déconnecter un slot spécifique si possible, sinon ignorer.
                    # Ceci est plus sûr que disconnect() seul.
                    widget.checkbox.stateChanged.disconnect(self.context_selection_changed.emit)
                except (TypeError, RuntimeError): 
                    pass 
        
        list_widget_to_filter.clear()
        if not display_items:
            list_widget_to_filter.addItem(QListWidgetItem("(No matching items)"))
        else:
            for item_text in display_items:
                item_widget = CheckableListItemWidget(item_text, parent=list_widget_to_filter)
                item_widget.checkbox.stateChanged.connect(lambda: self.context_selection_changed.emit())
                q_list_item = QListWidgetItem(list_widget_to_filter)
                q_list_item.setSizeHint(item_widget.sizeHint())
                list_widget_to_filter.addItem(q_list_item)
                list_widget_to_filter.setItemWidget(q_list_item, item_widget)
        self.context_selection_changed.emit() # Emit once after filtering

    def _filter_yarn_list(self, list_widget_to_filter: QListWidget, category_key: str, filter_text: str):
        """Filters the Yarn file list (simple string list) based on filter_text."""
        yarn_paths = self.category_data_map.get(category_key, []) # List of Path objects
        dialogues_base_path = config_manager.get_unity_dialogues_path() # For making paths relative

        list_widget_to_filter.clear()
        
        found_match = False
        for file_path_obj in yarn_paths:
            # Display relative path for consistency
            display_text = str(file_path_obj.relative_to(dialogues_base_path)) if dialogues_base_path and dialogues_base_path in file_path_obj.parents else file_path_obj.name
            if filter_text.lower() in display_text.lower():
                q_list_item = QListWidgetItem(display_text)
                list_widget_to_filter.addItem(q_list_item)
                found_match = True
        
        if not found_match:
            list_widget_to_filter.addItem(QListWidgetItem("(No matching .yarn files)"))

    def get_settings(self) -> dict:
        """Gets the current settings for the LeftSelectionPanel."""
        checked_items = {}
        for cat_key, list_widget in self.lists.items():
            if cat_key == self.yarn_files_category_key: # Skip yarn files for checked items
                continue
            checked_items[cat_key] = []
            for i in range(list_widget.count()):
                q_list_item = list_widget.item(i)
                item_widget = list_widget.itemWidget(q_list_item)
                if item_widget and hasattr(item_widget, 'checkbox') and item_widget.checkbox.isChecked():
                    checked_items[cat_key].append(item_widget.text_label.text())
        
        filters_text = {cat_key: edit.text() for cat_key, edit in self.filter_edits.items()}
        
        return {
            "filters": filters_text,
            "checked_items": checked_items
        }

    def load_settings(self, settings: dict):
        logger.info(f"LeftSelectionPanel: Loading settings. Current gdd_data_loaded: {self.gdd_data_loaded}")
        filters = settings.get("filters", {})
        for cat_key, filter_edit in self.filter_edits.items():
            if cat_key in filters:
                current_filter_text = filters[cat_key]
                is_blocked = filter_edit.signalsBlocked()
                filter_edit.blockSignals(True)
                filter_edit.setText(current_filter_text)
                filter_edit.blockSignals(is_blocked)

        if self.gdd_data_loaded:
            checked_items_by_category = settings.get("checked_items", {})
            logger.info(f"LeftSelectionPanel: gdd_data_loaded is True. Attempting to restore checked items: {checked_items_by_category}")
            for cat_key, items_to_check in checked_items_by_category.items():
                if cat_key in self.lists:
                    list_widget = self.lists[cat_key]
                    logger.debug(f"Restoring {len(items_to_check)} checked items for category '{cat_key}'.")
                    self._set_checked_list_items(list_widget, items_to_check)
                else:
                    logger.warning(f"Category '{cat_key}' not found in lists during load_settings for checked items.")
            if any(checked_items_by_category.values()):
                 self.context_selection_changed.emit()
        else:
            logger.warning("LeftSelectionPanel: gdd_data_loaded is False. Skipping restoration of checked items.")
        logger.info("LeftSelectionPanel settings loaded.")

    def _get_singular_name_for_category_key(self, category_key: str) -> str:
        """Helper to get the singular display name for a category key."""
        if category_key == self.yarn_files_category_key:
            return self.yarn_files_singular_name
        for config in self.categories_config:
            if config["key"] == category_key:
                return config.get("singular_name", category_key.capitalize())
        return category_key.capitalize() # Fallback

    # ---------------------------------------------------------------------
    # Méthodes utilitaires utilisées par GenerationPanel (sélection rapide)
    # ---------------------------------------------------------------------

    @Slot(list)
    def set_checked_items_by_name(self, item_names_to_check: list[str]) -> None:
        """Coche les éléments dont le nom est présent dans la liste fournie.

        Args:
            item_names_to_check: Liste des noms à cocher dans toutes les catégories.
        """
        if not item_names_to_check:
            return

        items_to_check_set = set(item_names_to_check)
        something_changed: bool = False

        for cat_key, list_widget in self.lists.items():
            if cat_key == self.yarn_files_category_key:  # Pas de checkbox pour les fichiers yarn
                continue

            list_widget.blockSignals(True)
            try:
                for i in range(list_widget.count()):
                    q_item = list_widget.item(i)
                    item_widget = list_widget.itemWidget(q_item)
                    if item_widget and hasattr(item_widget, "checkbox"):
                        should_be_checked = item_widget.text_label.text() in items_to_check_set
                        if item_widget.checkbox.isChecked() != should_be_checked:
                            item_widget.checkbox.setChecked(should_be_checked)
                            something_changed = True
            finally:
                list_widget.blockSignals(False)

        if something_changed:
            self.context_selection_changed.emit()

    @Slot()
    def uncheck_all_items(self) -> None:
        """Décoche tous les items de toutes les catégories."""
        something_changed = False
        for cat_key, list_widget in self.lists.items():
            if cat_key == self.yarn_files_category_key:
                continue
            list_widget.blockSignals(True)
            try:
                for i in range(list_widget.count()):
                    q_item = list_widget.item(i)
                    item_widget = list_widget.itemWidget(q_item)
                    if item_widget and hasattr(item_widget, "checkbox") and item_widget.checkbox.isChecked():
                        item_widget.checkbox.setChecked(False)
                        something_changed = True
            finally:
                list_widget.blockSignals(False)

        if something_changed:
            self.context_selection_changed.emit()

    def get_all_selected_item_names(self) -> list[str]:
        """Retourne la liste plate des noms d'items actuellement cochés."""
        selected: list[str] = []
        for cat_key, list_widget in self.lists.items():
            if cat_key == self.yarn_files_category_key:
                continue
            for i in range(list_widget.count()):
                q_item = list_widget.item(i)
                item_widget = list_widget.itemWidget(q_item)
                if item_widget and hasattr(item_widget, "checkbox") and item_widget.checkbox.isChecked():
                    selected.append(item_widget.text_label.text())
        return selected

    # Utility method to be part of the class
    def _set_checked_list_items(self, list_widget: QListWidget, items_to_check: list[str]):
        """Helper to set checked items for a specific QListWidget, blocking itemChanged signal."""
        # This is the definition from the global scope, now indented to be part of the class
        list_widget.blockSignals(True)
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            # GDD lists use custom widgets, Yarn list does not (or might in future)
            widget_item = list_widget.itemWidget(item)
            if widget_item and hasattr(widget_item, 'checkbox') and hasattr(widget_item, 'text_label'): # CheckableListItemWidget
                if widget_item.text_label.text() in items_to_check:
                    widget_item.checkbox.setChecked(True)
                else:
                    widget_item.checkbox.setChecked(False)
            elif item: # For simple QListWidgetItems (like Yarn files if they were checkable)
                 # This branch might not be used if Yarn files are not checkable or use a different mechanism
                if item.text() in items_to_check:
                    item.setCheckState(Qt.Checked)
                else:
                    item.setCheckState(Qt.Unchecked)
        list_widget.blockSignals(False)

class CheckableListItemWidget(QWidget):
    """Custom widget for items in QListWidget, with a checkbox and a label."""
    def __init__(self, text: str, parent: QListWidget = None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)

        self.checkbox = QCheckBox()
        self.text_label = QLabel(text)
        self.text_label.setWordWrap(False)
        self.text_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.layout.addWidget(self.checkbox)
        self.layout.addWidget(self.text_label)
        self.layout.setStretchFactor(self.text_label, 1)
        self.layout.setStretchFactor(self.checkbox, 0)

        self.setLayout(self.layout)

    def _filter_list_widget_internal(self, category_key: str, filter_text: str):
        """Filters items in a specific QListWidget based on input text."""
        list_widget_to_filter = self.list_widgets.get(category_key)
        label_to_update = self.section_labels.get(category_key)
        
        if not list_widget_to_filter or not label_to_update:
            logger.warning(f"Could not find list_widget or label for category '{category_key}' in _filter_list_widget_internal")
            return
        
        original_label_text_content = ""
        # Find original label text from categories_definition to avoid count in count
        for cat_def in self.categories_definition:
            if cat_def[0] == category_key:
                original_label_text_content = cat_def[1]
                break

        num_visible_items = 0
        for i in range(list_widget_to_filter.count()):
            list_item = list_widget_to_filter.item(i)
            if list_item:
                is_hidden_by_filter = filter_text.lower() not in list_item.text().lower()
                list_item.setHidden(is_hidden_by_filter)
                if not is_hidden_by_filter:
                    num_visible_items += 1
        total_items_count = list_widget_to_filter.count()
        label_to_update.setText(f"{original_label_text_content} ({num_visible_items}/{total_items_count})")

    def _populate_list_widget_internal(self, category_key: str):
        """Populates a specific QListWidget with data and configures items to be checkable."""
        list_widget_to_populate = self.list_widgets.get(category_key)
        label_to_update = self.section_labels.get(category_key)
        item_names_callable_name = None
        original_label_text_content = ""

        for cat_def in self.categories_definition:
            if cat_def[0] == category_key:
                item_names_callable_name = cat_def[2] # This is the name of the method on context_builder
                original_label_text_content = cat_def[1] # This is the display label
                break
        
        if not list_widget_to_populate or not label_to_update or not item_names_callable_name:
            logger.error(f"Missing widget/label/callable_name for category '{category_key}' in _populate_list_widget_internal")
            return

        name_extraction_func = getattr(self.context_builder, item_names_callable_name, lambda: [])

        # Block itemChanged signal during population
        list_widget_to_populate.blockSignals(True)

        list_widget_to_populate.clear()
        item_names = []
        valid_item_names = [] 
        if self.context_builder and callable(name_extraction_func): 
            item_names = name_extraction_func()
        
        if item_names:
            valid_item_names = [str(name) for name in item_names if name is not None]
            for name_string in sorted(valid_item_names): # Sort items alphabetically
                list_item = QListWidgetItem(name_string)
                list_item.setFlags(list_item.flags() | Qt.ItemIsUserCheckable)
                list_item.setCheckState(Qt.Unchecked)
                list_widget_to_populate.addItem(list_item)
            label_to_update.setText(f"{original_label_text_content} ({len(valid_item_names)}/{len(valid_item_names)})")
        else:
            list_widget_to_populate.addItem(QListWidgetItem("(No items)")) # Changed for clarity
            label_to_update.setText(f"{original_label_text_content} (0/0)")
        
        if list_widget_to_populate.count() > 0:
            list_widget_to_populate.setCurrentItem(None)
        
        list_widget_to_populate.blockSignals(False) # Unblock signals

    def populate_all_lists(self):
        """Populates all the lists in this panel with initial data from context_builder."""
        logger.info("LeftSelectionPanel: Populating all lists...")
        if not self.context_builder:
            logger.warning("Context builder not available in LeftSelectionPanel, cannot populate lists.")
            return
            
        for cat_key, _, _, _, _, _ in self.categories_definition:
            self._populate_list_widget_internal(cat_key)
            # Connect filter for this category after populating and creating the filter_edit
            if cat_key in self.filter_edits and cat_key in self.list_widgets:
                 self.filter_edits[cat_key].textChanged.connect(partial(self._filter_list_widget_internal, cat_key))

        # self.context_selection_changed.emit() # Emit once after all lists are populated and settings potentially loaded
        logger.info("LeftSelectionPanel: All lists populated and filters connected.")

    def get_all_checked_items(self) -> dict[str, list[str]]:
        """Returns a dictionary of all checked items, categorized."""
        all_checked = {}
        for category_key, list_widget in self.list_widgets.items():
            all_checked[category_key] = self._get_checked_items_from_list(list_widget)
        return all_checked

    def set_checked_items_for_category(self, category_key: str, items_to_check: list[str]):
        """Sets the checked items for a specific category and emits context_selection_changed.

        Args:
            category_key: The key of the category (e.g., "locations", "characters").
            items_to_check: A list of item names (str) that should be checked in that category.
                           Items not in this list will be unchecked.
        """
        list_widget = self.list_widgets.get(category_key)
        if list_widget:
            logger.info(f"LeftSelectionPanel: Setting checked items for '{category_key}': {items_to_check}")
            self._set_checked_list_items(list_widget, items_to_check)
            self.context_selection_changed.emit() # Notify that context might have changed
        else:
            logger.warning(f"LeftSelectionPanel: Category key '{category_key}' not found in list_widgets when trying to set checked items.")

    def get_settings(self) -> dict:
        """Returns the current UI settings of this panel (filters, checked items)."""
        settings = {
            "filters": {},
            "checked_items": self.get_all_checked_items() # Use the helper method
        }
        for category_key, filter_edit in self.filter_edits.items():
            settings["filters"][category_key] = filter_edit.text()
        return settings

    def load_settings(self, settings: dict):
        """Loads UI settings into this panel's widgets."""
        if not settings:
            logger.info("LeftSelectionPanel: No settings provided to load.")
            return
            
        logger.info(f"LeftSelectionPanel: Attempting to load settings: {settings}")
        filter_settings = settings.get("filters", {})
        for category_key, filter_text in filter_settings.items():
            if category_key in self.filter_edits:
                self.filter_edits[category_key].blockSignals(True)
                self.filter_edits[category_key].setText(filter_text)
                self.filter_edits[category_key].blockSignals(False)
                if filter_text: # Apply filter if text was loaded
                    self._filter_list_widget_internal(category_key, filter_text)
            
        # Restore checked items only if gdd_data_loaded is true,
        # and if MainWindow's option to restore selections is enabled (implicitly handled by MainWindow calling this)
        if self.gdd_data_loaded:
            checked_items_by_category = settings.get("checked_items", {})
            logger.info(f"LeftSelectionPanel: gdd_data_loaded is True. Attempting to restore checked items: {checked_items_by_category}")
            for cat_key, items_to_check in checked_items_by_category.items():
                if cat_key in self.lists:
                    list_widget = self.lists[cat_key]
                    logger.debug(f"Restoring {len(items_to_check)} checked items for category '{cat_key}'.")
                    self._set_checked_list_items(list_widget, items_to_check)
                else:
                    logger.warning(f"Category '{cat_key}' not found in lists during load_settings for checked items.")
            # After restoring, emit context_selection_changed if any items were actually checked
            # This can be done more robustly by checking if any QListWidgetItem isChecked()
            # or if _set_checked_list_items made any changes.
            # For now, let's assume if checked_items_by_category is not empty, a change might have occurred.
            if any(checked_items_by_category.values()):
                 self.context_selection_changed.emit() # Emit to update dependent UI like token count
        else:
            logger.warning("LeftSelectionPanel: gdd_data_loaded is False. Skipping restoration of checked items.")
            # If data isn't loaded, we should not attempt to check items that don't exist.
            # We also need to ensure lists are cleared of any "(Loading...)" messages if populate_all_lists
            # didn't run or failed before this. However, populate_all_lists should handle clearing.

        logger.info("LeftSelectionPanel settings loaded.")

    def _get_checked_items_from_list(self, list_widget: QListWidget) -> list[str]:
        """Helper to get checked items from a specific QListWidget."""
        checked = []
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            if item and item.checkState() == Qt.Checked:
                checked.append(item.text())
        return checked

    def _on_list_item_check_changed_internal(self, item: QListWidgetItem):
        """Called when a list item's check state changes. Emits context_selection_changed signal."""
        logger.debug(f"LeftSelectionPanel: Item '{item.text()}' check state changed in list {item.listWidget().objectName()}.")
        self.context_selection_changed.emit()

    def _on_list_item_clicked_internal(self, list_widget_object_name: str, item_text: str):
        """Called when an item in any list is clicked. Emits a signal for details view."""
        logger.debug(f"LeftSelectionPanel: Item '{item_text}' from list '{list_widget_object_name}' clicked for details.")
        self.item_clicked_for_details.emit(list_widget_object_name, item_text) 

    def get_selected_items_by_category(self) -> dict[str, list[str]]:
        """Returns a dictionary of selected (checked) items, keyed by category."""
        selected_by_category: dict[str, list[str]] = {cat: [] for cat in self.category_keys}
        for category_key, checkboxes in self.checkbox_groups.items():
            for item_name, checkbox in checkboxes.items():
                if checkbox.isChecked():
                    selected_by_category[category_key].append(item_name)
        return selected_by_category

    def get_all_selected_item_names(self) -> list[str]:
        """Returns a flat list of all selected (checked) item names across all categories."""
        all_selected: list[str] = []
        for _category_key, list_widget in self.list_widgets.items():
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                if item and item.checkState() == Qt.Checked:
                    all_selected.append(item.text())
        return all_selected

    @Slot(list, bool)
    def clear_and_set_selected_items(self, item_names: list[str], silent: bool = False) -> None:
        """
        Clears all current selections and checks items specified in item_names.
        If silent is True, context_selection_changed signal is not emitted.
        Otherwise, context_selection_changed is emitted once after all changes if any state changed.
        """
        # logger.debug(f"LeftSelectionPanel: clear_and_set_selected_items called with {item_names}, silent={silent}")
        something_changed = False
        for list_widget in self.list_widgets.values():
            list_widget.blockSignals(True) # Bloquer les signaux du QListWidget pendant la modification
            try:
                # Uncheck all existing items in this list_widget
                for i in range(list_widget.count()):
                    item = list_widget.item(i)
                    if item and item.checkState() == Qt.Checked:
                        item.setCheckState(Qt.Unchecked)
                        something_changed = True
                
                # Check the new items relevant to this list_widget
                # (Nous ne savons pas à quelle catégorie appartiennent les item_names ici directement)
                # Donc, nous cochons ceux qui sont présents dans item_names et présents dans la liste actuelle.
                item_names_set = set(item_names)
                for i in range(list_widget.count()):
                    item = list_widget.item(i)
                    if item and item.text() in item_names_set:
                        if item.checkState() != Qt.Checked:
                            item.setCheckState(Qt.Checked)
                            something_changed = True
            finally:
                list_widget.blockSignals(False)

        if something_changed and not silent:
            self.context_selection_changed.emit()
            # logger.debug(f"LeftSelectionPanel: clear_and_set_selected_items finished, emitted context_selection_changed.")

    @Slot()
    def uncheck_all_items(self) -> None:
        """Unchecks all items in all category lists and emits context_selection_changed if any state changed."""
        # logger.debug("LeftSelectionPanel: uncheck_all_items called.")
        something_changed = False
        for list_widget in self.list_widgets.values():
            list_widget.blockSignals(True)
            try:
                for i in range(list_widget.count()):
                    item = list_widget.item(i)
                    if item and item.checkState() == Qt.Checked:
                        item.setCheckState(Qt.Unchecked)
                        something_changed = True
            finally:
                list_widget.blockSignals(False)
        
        if something_changed:
            self.context_selection_changed.emit()
            # logger.debug("LeftSelectionPanel: uncheck_all_items finished, emitted context_selection_changed.")

    @Slot(list)
    def set_checked_items_by_name(self, item_names_to_check: list[str]) -> None:
        """
        Sets the checked state of items based on item_names_to_check across all categories.
        Items in the list will be checked, others will be unchecked.
        Emits context_selection_changed signal once after all changes if any state changed.
        """
        # logger.debug(f"LeftSelectionPanel: set_checked_items_by_name called with {len(item_names_to_check)} items: {item_names_to_check}")
        something_changed = False
        items_to_check_set = set(item_names_to_check)

        for list_widget in self.list_widgets.values():
            list_widget.blockSignals(True)
            try:
                for i in range(list_widget.count()):
                    item = list_widget.item(i)
                    if item:
                        should_be_checked = item.text() in items_to_check_set
                        if item.checkState() != (Qt.Checked if should_be_checked else Qt.Unchecked):
                            item.setCheckState(Qt.Checked if should_be_checked else Qt.Unchecked)
                            something_changed = True
            finally:
                list_widget.blockSignals(False)

        if something_changed:
            self.context_selection_changed.emit()
            # logger.debug(f"LeftSelectionPanel: set_checked_items_by_name finished, emitted context_selection_changed.")

    # --- Old Slot Handlers (commentés et potentiellement à supprimer s'ils ne sont plus utilisés nulle part) ---
    # def _on_filter_list_item_changed(self, item: QListWidgetItem) -> None:
    #     logger.debug(f"LeftSelectionPanel: Item '{item.text()}' check state changed in list {item.listWidget().objectName()}.")
    #     self.context_selection_changed.emit() 