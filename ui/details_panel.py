from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTreeView, QAbstractItemView, QHeaderView, QTextEdit, QScrollArea, QSizePolicy, QGroupBox)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QFont
from PySide6.QtCore import Qt, Slot
import logging
from pathlib import Path
from typing import Optional

import json
from config_manager import read_json_file_content

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
        self.default_label = QLabel("Select an item from the left panel to see its details here, or a JSON file to see its content.")
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
        
        # --- Widgets for JSON File Display ---
        self.json_display_group = QGroupBox("JSON File Content") # GroupBox for JSON content
        self.json_display_layout = QVBoxLayout()

        # TextEdit for JSON content (formatted)
        self.json_content_text_edit = QTextEdit()
        self.json_content_text_edit.setReadOnly(True)
        # Use monospace font for JSON
        font = QFont("Consolas", 10)
        if not font.exactMatch():
            font = QFont("Courier", 10)
        self.json_content_text_edit.setFont(font)

        self.json_display_layout.addWidget(self.json_content_text_edit)
        self.json_display_group.setLayout(self.json_display_layout)
        # --- End of Widgets for JSON File Display ---

        # Add placeholder initially, hide others
        self.main_layout.addWidget(self.default_label)
        self.main_layout.addWidget(self.scroll_area)
        self.main_layout.addWidget(self.json_display_group) # Add the new group to the main layout

        self.scroll_area.setVisible(False)
        self.json_display_group.setVisible(False) # Initially hidden
        self.default_label.setVisible(True)
        
        self.current_gdd_data = None

        logger.info("DetailsPanel initialized.")

    @Slot(str, str, list, str)
    def update_details(self, category_key: str, item_name_or_path: str, category_data: list, category_singular_name: str):
        """Updates the panel to show details for the selected item or JSON file content.

        Args:
            category_key: The category of the item (e.g., "characters", "existing_json_files").
            item_name_or_path: The name of the GDD item or the full path to the JSON file.
            category_data: The full data for the GDD category, or a list containing the path for JSON files.
            category_singular_name: The singular display name for the category.
        """
        logger.info(f"DetailsPanel received item: '{item_name_or_path}' from category '{category_key}'. Singular: '{category_singular_name}'. Data items: {len(category_data)}")
        self.current_gdd_data = None # Reset GDD data

        if category_key == "existing_json_files":
            self.scroll_area.setVisible(False)
            self.default_label.setVisible(False)
            self.json_display_group.setVisible(True)
            
            json_file_path_str = item_name_or_path # item_name_or_path is the full path for JSON files
            json_file_path = Path(json_file_path_str)
            logger.info(f"Displaying content for JSON file: {json_file_path}")

            if json_file_path.is_file():
                json_content = read_json_file_content(json_file_path)
                if json_content:
                    try:
                        # Parse and pretty-print JSON
                        json_data = json.loads(json_content)
                        formatted_json = json.dumps(json_data, indent=2, ensure_ascii=False)
                        self.json_content_text_edit.setText(formatted_json)
                    except json.JSONDecodeError as e:
                        self.json_content_text_edit.setText(f"Erreur de parsing JSON:\n{e}\n\nContenu brut:\n{json_content}")
                else:
                    self.json_content_text_edit.setText(f"Impossible de lire le fichier JSON: {json_file_path}")
            else:
                self.json_content_text_edit.setText(f"Fichier JSON non trouvé: {json_file_path}")
            self.json_display_group.setTitle(f"JSON File: {json_file_path.name}")

        elif category_key and item_name_or_path: # Handle GDD items
            self.json_display_group.setVisible(False)
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
            self.json_display_group.setVisible(False)
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

    def clear_details(self):
        """Clears all detail views and shows the placeholder."""
        self.details_text_edit.clear()
        self.json_content_text_edit.clear()
        
        self.scroll_area.setVisible(False)
        self.json_display_group.setVisible(False)
        self.default_label.setVisible(True)
        logger.info("DetailsPanel cleared.")
        self.current_gdd_data = None 