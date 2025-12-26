from PySide6.QtCore import Qt
import logging
logger = logging.getLogger(__name__)

def handle_uncheck_all_items(panel):
    """
    Handler pour décocher tous les items de toutes les catégories du LeftSelectionPanel.
    Fonctionne pour les widgets custom et natifs. Émet context_selection_changed si nécessaire.
    """
    something_changed = False
    for cat_key, list_widget in (panel.lists if hasattr(panel, 'lists') else panel.list_widgets).items():
        if hasattr(panel, 'json_files_category_key') and cat_key == getattr(panel, 'json_files_category_key', None):
            continue
        list_widget.blockSignals(True)
        try:
            for i in range(list_widget.count()):
                q_item = list_widget.item(i)
                item_widget = list_widget.itemWidget(q_item) if list_widget.itemWidget(q_item) else None
                if item_widget and hasattr(item_widget, "checkbox") and item_widget.checkbox.isChecked():
                    item_widget.checkbox.setChecked(False)
                    something_changed = True
                elif q_item and q_item.checkState() == Qt.Checked:
                    q_item.setCheckState(Qt.Unchecked)
                    something_changed = True
        finally:
            list_widget.blockSignals(False)
    if something_changed:
        panel.context_selection_changed.emit()


def handle_set_checked_items_by_name(panel, item_names_to_check):
    """
    Handler pour cocher les items dont le nom est dans item_names_to_check dans toutes les catégories.
    Fonctionne pour les widgets custom et natifs. Émet context_selection_changed si nécessaire.
    """
    if not item_names_to_check:
        return
    items_to_check_set = set(item_names_to_check)
    something_changed = False
    for cat_key, list_widget in (panel.lists if hasattr(panel, 'lists') else panel.list_widgets).items():
        if hasattr(panel, 'json_files_category_key') and cat_key == getattr(panel, 'json_files_category_key', None):
            continue
        list_widget.blockSignals(True)
        try:
            for i in range(list_widget.count()):
                q_item = list_widget.item(i)
                item_widget = list_widget.itemWidget(q_item) if list_widget.itemWidget(q_item) else None
                if item_widget and hasattr(item_widget, "checkbox"):
                    should_be_checked = item_widget.text_label.text() in items_to_check_set
                    if item_widget.checkbox.isChecked() != should_be_checked:
                        item_widget.checkbox.setChecked(should_be_checked)
                        something_changed = True
                elif q_item:
                    should_be_checked = q_item.text() in items_to_check_set
                    if q_item.checkState() != (Qt.Checked if should_be_checked else Qt.Unchecked):
                        q_item.setCheckState(Qt.Checked if should_be_checked else Qt.Unchecked)
                        something_changed = True
        finally:
            list_widget.blockSignals(False)
    if something_changed:
        panel.context_selection_changed.emit() 