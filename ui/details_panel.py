from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTreeView, QAbstractItemView, QHeaderView, QTextEdit, QScrollArea, QSizePolicy)
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt, Slot
import logging
from pathlib import Path

import config_manager

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
        
        self.content_layout.addStretch(1) # Pushes content to the top if it's short
        
        self.current_category_key = None
        self.current_item_text = None
        
        logger.info("DetailsPanel initialized.")

    @Slot(str, str, list, str)
    def update_details(self, category_key: str, item_text: str, category_data: list, category_singular_name: str):
        logger.info(f"DetailsPanel received item: '{item_text}' from category '{category_key}'. Singular: '{category_singular_name}'. Data items: {len(category_data) if category_data else 'None'}")
        self.current_category_key = category_key
        self.current_item_text = item_text

        self.title_label.setText(f"Details: {category_singular_name} - {item_text}")
        self.details_text_edit.clear()
        self.details_text_edit.setVisible(True)
        self.default_label.setVisible(False)

        if category_key == "existing_yarn_files": # Handle Yarn files
            # For yarn files, item_text is the full path (as sent by LeftSelectionPanel)
            # category_data[0] also contains this full path.
            yarn_file_path_str = item_text 
            if not yarn_file_path_str:
                logger.warning("Yarn file path is empty.")
                self.details_text_edit.setPlainText("Error: Yarn file path is missing.")
                return

            yarn_file_path = Path(yarn_file_path_str)
            self.title_label.setText(f"Content: {yarn_file_path.name}") # Show file name in title
            logger.info(f"Displaying content for Yarn file: {yarn_file_path}")
            content = config_manager.read_yarn_file_content(yarn_file_path)
            if content is not None:
                self.details_text_edit.setPlainText(content)
            else:
                self.details_text_edit.setPlainText(f"Error: Could not read content from {yarn_file_path.name}.")
            
        elif category_data: # Handle GDD items
            found_item_details = None
            primary_name_key_used = "Unknown"

            # Iterate through known name keys for the category to find the item
            # This assumes item_text corresponds to one of the name_keys values.
            # The category_config in LeftSelectionPanel should define these.
            # We might need a more robust way to get these keys if not passed directly.
            # For now, we search by matching item_text, common for display names.
            
            # Simplified search: find the dict in category_data that matches item_text in a common key
            # A more robust approach would be to pass the exact item_dict or its index.
            for item_dict in category_data:
                if isinstance(item_dict, dict):
                    # Check common keys or the display name (item_text)
                    if item_dict.get("Nom") == item_text or \
                       item_dict.get("Titre") == item_text or \
                       item_dict.get("ID") == item_text or \
                       item_dict.get(category_singular_name) == item_text: # Fallback to singular name as key
                        found_item_details = item_dict
                        break
                    # Check if any value in the dict matches item_text (broader search)
                    for val in item_dict.values():
                        if str(val) == item_text:
                            found_item_details = item_dict
                            break
                    if found_item_details: break
            
            if found_item_details:
                details_str = f"Category: {category_singular_name}\nItem: {item_text}\n--- Details ---\n"
                for key, value in found_item_details.items():
                    details_str += f"{key}: {value}\n"
                self.details_text_edit.setPlainText(details_str)
            else:
                self.details_text_edit.setPlainText(f"Details for '{item_text}' in '{category_key}' not found or data structure mismatch.")
                logger.warning(f"Could not find item details for '{item_text}' in '{category_key}' using common keys.")
        else:
            self.details_text_edit.setPlainText(f"No detailed data available for '{item_text}' in '{category_key}'.")
            logger.warning(f"No category_data provided for '{item_text}' in '{category_key}'.")

    def clear_details(self):
        logger.info("Clearing DetailsPanel.")
        self.title_label.setText("Details")
        self.details_text_edit.clear()
        self.details_text_edit.setVisible(False)
        self.default_label.setVisible(True)
        self.current_category_key = None
        self.current_item_text = None 