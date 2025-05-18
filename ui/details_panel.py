from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTreeView, QAbstractItemView, QHeaderView, QTextEdit, QScrollArea, QSizePolicy, QGroupBox)
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt, Slot
import logging
from pathlib import Path
from typing import Optional

from .. import yarn_parser
from .. import config_manager

logger = logging.getLogger(__name__)

class DetailsPanel(QWidget):
    """Manages the UI elements for displaying detailed information of a selected GDD item."""

    def __init__(self, parent=None):
        """Initializes the DetailsPanel.

        Args:
            parent: The parent widget.
        """
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(8)

        self.title_label = QLabel("Details")
        font = self.title_label.font()
        font.setPointSize(14)
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.title_label)

        # Use a QScrollArea to make the content scrollable if it's too long
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.main_layout.addWidget(self.scroll_area)

        self.scroll_content_widget = QWidget() # Widget to hold the actual content
        self.scroll_area.setWidget(self.scroll_content_widget)
        
        self.content_layout = QVBoxLayout(self.scroll_content_widget) # Layout for the scrollable content
        self.content_layout.setContentsMargins(0,0,0,0)
        self.content_layout.setSpacing(6)
        
        # Default message / placeholder
        self.default_label = QLabel("Select an item from the left panel to see its details here, or a Yarn file to see its content.")
        self.default_label.setWordWrap(True)
        self.default_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.default_label)

        self.details_text_edit = QTextEdit()
        self.details_text_edit.setReadOnly(True)
        self.details_text_edit.setVisible(False) # Initially hidden
        self.details_text_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth) # Optional: improve readability
        self.content_layout.addWidget(self.details_text_edit)
        
        self.current_category_key = None
        self.current_item_text = None
        
        # --- Widgets for Yarn File Display ---
        self.yarn_display_group = QGroupBox("Yarn File Content") # GroupBox for Yarn content
        self.yarn_display_layout = QVBoxLayout()

        # TreeView for Yarn nodes
        self.yarn_nodes_tree_view = QTreeView()
        self.yarn_nodes_tree_view.setHeaderHidden(True)
        self.yarn_nodes_model = QStandardItemModel()
        self.yarn_nodes_tree_view.setModel(self.yarn_nodes_model)
        self.yarn_nodes_tree_view.setFixedHeight(200) # Initial fixed height, can be adjusted
        self.yarn_nodes_tree_view.selectionModel().selectionChanged.connect(self._on_yarn_node_selected)

        # TextEdit for selected Yarn node body
        self.yarn_node_body_text_edit = QTextEdit()
        self.yarn_node_body_text_edit.setReadOnly(True) # For now, just display

        self.yarn_display_layout.addWidget(QLabel("Nodes:"))
        self.yarn_display_layout.addWidget(self.yarn_nodes_tree_view)
        self.yarn_display_layout.addWidget(QLabel("Node Body:"))
        self.yarn_display_layout.addWidget(self.yarn_node_body_text_edit)
        self.yarn_display_group.setLayout(self.yarn_display_layout)
        # --- End of Widgets for Yarn File Display ---

        # Add placeholder initially, hide others
        self.main_layout.addWidget(self.default_label)
        self.main_layout.addWidget(self.scroll_area)
        self.main_layout.addWidget(self.yarn_display_group) # Add the new group to the main layout

        self.scroll_area.setVisible(False)
        self.yarn_display_group.setVisible(False) # Initially hidden
        self.default_label.setVisible(True)
        
        self.current_gdd_data = None
        self.current_yarn_nodes: list[yarn_parser.YarnNode] = [] # To store parsed nodes

        logger.info("DetailsPanel initialized.")

    @Slot(str, str, list, str)
    def update_details(self, category_key: str, item_name_or_path: str, category_data: list, category_singular_name: str):
        """Updates the panel to show details for the selected item or Yarn file content.

        Args:
            category_key: The category of the item (e.g., "characters", "existing_yarn_files").
            item_name_or_path: The name of the GDD item or the full path to the Yarn file.
            category_data: The full data for the GDD category, or a list containing the path for Yarn files.
            category_singular_name: The singular display name for the category.
        """
        logger.info(f"DetailsPanel received item: '{item_name_or_path}' from category '{category_key}'. Singular: '{category_singular_name}'. Data items: {len(category_data)}")
        self.current_gdd_data = None # Reset GDD data
        self.current_yarn_nodes = [] # Reset Yarn nodes
        self.yarn_nodes_model.clear()
        self.yarn_node_body_text_edit.clear()

        if category_key == "existing_yarn_files":
            self.scroll_area.setVisible(False)
            self.default_label.setVisible(False)
            self.yarn_display_group.setVisible(True)
            
            yarn_file_path_str = item_name_or_path # item_name_or_path is the full path for yarn files
            yarn_file_path = Path(yarn_file_path_str)
            logger.info(f"Displaying content for Yarn file: {yarn_file_path}")

            if yarn_file_path.is_file():
                self.current_yarn_nodes = yarn_parser.parse_yarn_file(yarn_file_path)
                self.yarn_nodes_model.clear() # Clear previous model items
                if self.current_yarn_nodes:
                    for node in self.current_yarn_nodes:
                        item = QStandardItem(node.title if node.title else "Untitled Node")
                        item.setData(node, Qt.ItemDataRole.UserRole) # Store the whole node object
                        item.setEditable(False)
                        self.yarn_nodes_model.appendRow(item)
                    self.yarn_nodes_tree_view.expandAll() # Optional: expand all nodes
                    if self.yarn_nodes_model.rowCount() > 0: # Select the first node by default
                        first_node_index = self.yarn_nodes_model.index(0,0)
                        self.yarn_nodes_tree_view.setCurrentIndex(first_node_index)
                        # _on_yarn_node_selected will be called automatically by selectionChanged
                else:
                    self.yarn_node_body_text_edit.setText(f"No nodes found or error parsing: {yarn_file_path.name}")
            else:
                self.yarn_node_body_text_edit.setText(f"Yarn file not found: {yarn_file_path}")
            self.yarn_display_group.setTitle(f"Yarn File: {yarn_file_path.name}")

        elif category_key and item_name_or_path: # Handle GDD items
            self.yarn_display_group.setVisible(False)
            self.default_label.setVisible(False)
            self.scroll_area.setVisible(True)
            self.details_text_edit.setVisible(True)
            self.default_label.setVisible(False)
            
            self.current_gdd_data = category_data
            selected_item_data = self._find_gdd_item_data(item_name_or_path, category_key, category_data)

            if selected_item_data:
                details_text = f"Category: {category_singular_name}\n"
                details_text += f"Item: {item_name_or_path}\n"
                details_text += "--- Details ---\n"
                for key, value in selected_item_data.items():
                    details_text += f"{key}: {value}\n"
                self.details_text_edit.setText(details_text)
            else:
                self.details_text_edit.setText(f"Details for '{item_name_or_path}' not found in category '{category_key}'.")
            
        else:
            self.scroll_area.setVisible(False)
            self.yarn_display_group.setVisible(False)
            self.details_text_edit.setVisible(False)
            self.default_label.setVisible(True)
            self.details_text_edit.clear() # Clear text edit if no valid item/category

    def _find_gdd_item_data(self, item_name_to_find: str, category_key: str, category_data_list: list) -> Optional[dict]:
        """Finds the specific GDD item's dictionary from the category data list.

        Args:
            item_name_to_find: The name of the item to find.
            category_key: The category of the item.
            category_data_list: The full data for the GDD category.

        Returns:
            The dictionary for the found item, or None if not found.
        """
        # This logic assumes item_name_to_find is unique enough or that the first match is desired.
        # It also assumes that the name is primarily in a "Nom" or "Name" or "Titre" or "ID" field.
        # This could be made more robust by using the name_keys from LeftSelectionPanel if accessible.
        potential_name_keys = ["Nom", "Name", "Titre", "ID", "id", "title"] # Common keys
        if hasattr(self.parent(), 'left_panel') and hasattr(self.parent().left_panel, 'category_item_name_keys'):
            # Try to get more specific keys from LeftSelectionPanel if possible
            # This creates a dependency, consider passing name_keys if this becomes an issue.
            specific_keys = self.parent().left_panel.category_item_name_keys.get(category_key)
            if specific_keys:
                potential_name_keys = specific_keys + [k for k in potential_name_keys if k not in specific_keys]
        
        for item_dict in category_data_list:
            if isinstance(item_dict, dict):
                for key_to_check in potential_name_keys:
                    value_in_dict = item_dict.get(key_to_check)
                    if value_in_dict is not None and str(value_in_dict) == item_name_to_find:
                        return item_dict
        logger.warning(f"Could not find GDD item '{item_name_to_find}' in category '{category_key}' using keys: {potential_name_keys}")
        return None

    @Slot()
    def _on_yarn_node_selected(self):
        """Called when a node is selected in the yarn_nodes_tree_view."""
        selected_indexes = self.yarn_nodes_tree_view.selectedIndexes()
        if not selected_indexes:
            self.yarn_node_body_text_edit.clear()
            return

        selected_index = selected_indexes[0]
        node_item = self.yarn_nodes_model.itemFromIndex(selected_index)
        if node_item:
            node_data: Optional[yarn_parser.YarnNode] = node_item.data(Qt.ItemDataRole.UserRole)
            if node_data:
                self.yarn_node_body_text_edit.setText(node_data.body)
                logger.debug(f"Displaying body for Yarn node: {node_data.title}")
            else:
                self.yarn_node_body_text_edit.setText("[Error: Could not retrieve node data]")
        else:
            self.yarn_node_body_text_edit.clear()

    def clear_details(self):
        """Clears all detail views and shows the placeholder."""
        self.details_text_edit.clear()
        self.yarn_nodes_model.clear()
        self.yarn_node_body_text_edit.clear()
        
        self.scroll_area.setVisible(False)
        self.yarn_display_group.setVisible(False)
        self.default_label.setVisible(True)
        logger.info("DetailsPanel cleared.")
        self.current_gdd_data = None
        self.current_yarn_nodes = [] 