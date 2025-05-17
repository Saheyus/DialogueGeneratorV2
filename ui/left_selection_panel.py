from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QCheckBox, QHBoxLayout, QScrollArea, QFrame, QGroupBox)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPalette, QColor
import logging
from functools import partial

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

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(10)

        self.list_widgets = {}
        self.filter_edits = {}
        self.section_labels = {}
        self.category_data_callables = {} 
        self.category_singular_names = {} 
        self.category_name_key_priorities = {} 
        # self.checkbox_groups = {} # Retiré car non utilisé et source de confusion

        # Define categories and their properties
        # (category_key, display_label, item_names_callable_name_on_context_builder, 
        #  category_data_ATTRIBUTE_name_on_context_builder, singular_name, name_key_priority_list_for_details)
        self.categories_definition = [
            ("characters", "Characters:", "get_characters_names", "characters", "Character", ["Nom"]),
            ("locations", "Locations:", "get_locations_names", "locations", "Location", ["Nom"]),
            ("items", "Items:", "get_items_names", "items", "Item", ["Nom"]),
            ("species", "Species:", "get_species_names", "species", "Species", ["Nom"]),
            ("communities", "Communities:", "get_communities_names", "communities", "Community", ["Nom"]),
            ("dialogues_examples", "Dialogue Examples:", "get_dialogue_examples_titles", "dialogues_examples", "Dialogue Example", ["Nom", "Titre", "ID"])
        ]

        for cat_key, label_text, names_callable_name, data_attribute_name, singular_name, name_keys in self.categories_definition:
            self._create_section_widget(cat_key, label_text, names_callable_name, data_attribute_name, singular_name, name_keys)

        self.setMinimumWidth(300)
        self.setMaximumWidth(400)

        logger.info("LeftSelectionPanel initialized with all sections.")

    def _create_section_widget(self, category_key_name: str, section_label_text: str, 
                                 item_names_callable_name: str, category_data_attribute_name: str, # Renamed for clarity
                                 category_singular_name: str, name_key_priority: list):
        """Creates a labeled section with a filter, and a list widget for a category."""
        label = QLabel(section_label_text)
        filter_edit = QLineEdit()
        filter_edit.setPlaceholderText(f"Filter {section_label_text.lower().replace(':', '')}...")
        list_widget = QListWidget()
        list_widget.setObjectName(f"{category_key_name}_list")

        self.section_labels[category_key_name] = label
        self.filter_edits[category_key_name] = filter_edit
        self.list_widgets[category_key_name] = list_widget
        # Store the attribute from context_builder that holds the full data for the category
        self.category_data_callables[category_key_name] = getattr(self.context_builder, category_data_attribute_name, []) # Default to empty list if not found
        self.category_singular_names[category_key_name] = category_singular_name
        self.category_name_key_priorities[category_key_name] = name_key_priority # Stored but not directly used by LeftPanel signal

        list_widget.itemClicked.connect(
            lambda item_widget, key=category_key_name: # item_widget is QListWidgetItem
            self.item_clicked_for_details.emit(
                key, 
                item_widget.text(), 
                self.category_data_callables[key], # REMOVED parentheses, as it's now the list itself
                self.category_singular_names[key]
            )
        )
        
        list_widget.itemChanged.connect(self._on_list_item_check_changed_internal)

        self.main_layout.addWidget(label)
        self.main_layout.addWidget(filter_edit)
        self.main_layout.addWidget(list_widget)
        logger.debug(f"Section for '{category_key_name}' created.")

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
            
        checked_items_settings = settings.get("checked_items", {})
        for category_key, items_to_check in checked_items_settings.items():
            if category_key in self.list_widgets:
                self._set_checked_list_items(self.list_widgets[category_key], items_to_check)
        
        logger.info("LeftSelectionPanel: Settings loaded.")
        self.context_selection_changed.emit() # Emit to update context based on loaded checked items
        
    def _get_checked_items_from_list(self, list_widget: QListWidget) -> list[str]:
        """Helper to get checked items from a specific QListWidget."""
        checked = []
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            if item and item.checkState() == Qt.Checked:
                checked.append(item.text())
        return checked

    def _set_checked_list_items(self, list_widget: QListWidget, items_to_check: list[str]):
        """Helper to set checked items for a specific QListWidget, blocking itemChanged signal."""
        list_widget.blockSignals(True)
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            if item:
                item.setCheckState(Qt.Checked if item.text() in items_to_check else Qt.Unchecked)
        list_widget.blockSignals(False)

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

    # --- Old Slot Handlers (to be removed or refactored if not used) ---
    # def _on_filter_list_item_changed(self, item: QListWidgetItem) -> None:
    #     logger.debug(f"LeftSelectionPanel: Item '{item.text()}' check state changed in list {item.listWidget().objectName()}.")
    #     self.context_selection_changed.emit() 