from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTreeView, QAbstractItemView, QHeaderView)
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt
import logging

logger = logging.getLogger(__name__)

class DetailsPanel(QWidget):
    """Manages the UI elements for displaying detailed information of a selected GDD item."""

    def __init__(self, parent=None):
        """Initializes the DetailsPanel.

        Args:
            parent: The parent widget.
        """
        super().__init__(parent)

        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.details_view_label = QLabel("Item Details")
        self.details_view_label.setStyleSheet("font-weight: bold; padding-bottom: 5px;")
        layout.addWidget(self.details_view_label)

        self.details_tree_model = QStandardItemModel()
        self.details_tree_model.setHorizontalHeaderLabels(["Property", "Value"])

        self.details_view = QTreeView()
        self.details_view.setModel(self.details_tree_model)
        self.details_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.details_view.setAlternatingRowColors(True)
        self.details_view.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.details_view.header().setStretchLastSection(True)
        layout.addWidget(self.details_view)

    def display_details(self, item_data: dict | None, category_singular_name: str, item_name: str):
        """Populates the QTreeView with the details of the selected item.

        Args:
            item_data: A dictionary containing the data of the item to display.
                       If None, the tree view is cleared and a message is shown.
            category_singular_name: The singular name of the category (e.g., 'Character').
            item_name: The name of the item being displayed.
        """
        self.details_tree_model.clear()
        self.details_tree_model.setHorizontalHeaderLabels(["Property", "Value"]) # Ensure headers are always present
        self.details_view_label.setText(f"{category_singular_name} Details: {item_name}")

        if item_data is None:
            logger.warning(f"No data provided to display for {category_singular_name}: {item_name}")
            root_item = self.details_tree_model.invisibleRootItem()
            placeholder_item = QStandardItem(f"Details not found or no data for {item_name}.")
            placeholder_item.setEditable(False)
            root_item.appendRow([placeholder_item, QStandardItem("")]) # Add empty item for second column
            return

        if not isinstance(item_data, dict):
            logger.error(f"Invalid item_data type for {item_name}: {type(item_data)}. Expected dict.")
            root_item = self.details_tree_model.invisibleRootItem()
            error_item = QStandardItem(f"Invalid data format for {item_name}.")
            error_item.setEditable(False)
            root_item.appendRow([error_item, QStandardItem("")])
            return

        self._populate_tree_recursively(self.details_tree_model.invisibleRootItem(), item_data)
        self.details_view.expandAll() 
        if self.details_tree_model.rowCount() > 0 and self.details_tree_model.columnCount() > 0:
            first_item_index = self.details_tree_model.index(0, 0)
            if first_item_index.isValid():
                self.details_view.scrollTo(first_item_index, QAbstractItemView.ScrollHint.PositionAtTop)

    def _populate_tree_recursively(self, parent_item: QStandardItem, data_node):
        """Recursively populates the QTreeView model with dictionary data."""
        if isinstance(data_node, dict):
            for key, value in data_node.items():
                key_item = QStandardItem(str(key))
                key_item.setEditable(False)
                if isinstance(value, (dict, list)):
                    parent_item.appendRow([key_item, QStandardItem("")]) # No value in second column for parent
                    self._populate_tree_recursively(key_item, value)
                else:
                    value_item = QStandardItem(str(value))
                    value_item.setEditable(False)
                    parent_item.appendRow([key_item, value_item])
        elif isinstance(data_node, list):
            for index, item in enumerate(data_node):
                index_item = QStandardItem(f"[{index}]")
                index_item.setEditable(False)
                if isinstance(item, (dict, list)):
                    parent_item.appendRow([index_item, QStandardItem("")])
                    self._populate_tree_recursively(index_item, item)
                else:
                    value_item = QStandardItem(str(item))
                    value_item.setEditable(False)
                    parent_item.appendRow([index_item, value_item])
        else:
            # This case should ideally not be reached if called from display_details 
            # with a dict, but as a fallback for direct calls or complex structures:
            value_item = QStandardItem(str(data_node))
            value_item.setEditable(False)
            parent_item.appendRow([value_item, QStandardItem("")]) 