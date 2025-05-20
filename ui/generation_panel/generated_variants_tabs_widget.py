from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QPlainTextEdit, 
                               QSizePolicy, QScrollArea, QMessageBox, QPushButton, QHBoxLayout, QStyle, QTextEdit)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QKeySequence
import logging

logger = logging.getLogger(__name__)

class GeneratedVariantsTabsWidget(QTabWidget):
    validate_variant_requested = Signal(str, str) # tab_name, content
    save_all_variants_requested = Signal(list) # list of (tab_name, content)
    regenerate_variant_requested = Signal(str) # tab_name (variant_id)
    # Peut-être d'autres signaux utiles plus tard

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabsClosable(False) # Les onglets de prompt et variantes ne sont pas fermables par défaut
        self.setMovable(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_tab_context_menu)

    def _show_tab_context_menu(self, position):
        index = self.tabBar().tabAt(position)
        if index == -1:
            return

        menu = QMenu(self)
        tab_text = self.tabText(index)

        # Action pour régénérer (si c'est un onglet de variante)
        if tab_text.startswith("Variante"):
            regenerate_action = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload), f"Régénérer {tab_text}", self)
            regenerate_action.triggered.connect(lambda: self._handle_regenerate_variant(tab_text))
            menu.addAction(regenerate_action)
            menu.addSeparator()

        # Action pour valider (si c'est un onglet de variante)
        if tab_text.startswith("Variante"):
            validate_action = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton), f"Valider {tab_text}", self)
            validate_action.triggered.connect(lambda: self._handle_validate_variant(index))
            menu.addAction(validate_action)
        
        # Action pour sauvegarder toutes les variantes visibles (si au moins une variante existe)
        has_variants = any(self.tabText(i).startswith("Variante") for i in range(self.count()))
        if has_variants:
            save_all_action = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton), "Sauvegarder toutes les variantes...", self)
            save_all_action.triggered.connect(self._handle_save_all_variants)
            menu.addAction(save_all_action)

        if menu.actions(): # Seulement afficher si des actions sont disponibles
            menu.exec(self.tabBar().mapToGlobal(position))

    def _handle_regenerate_variant(self, tab_name: str):
        variant_id = tab_name # Pour l'instant, le nom de l'onglet est l'ID
        logger.info(f"Demande de régénération pour la variante : {variant_id}")
        self.regenerate_variant_requested.emit(variant_id)

    def _handle_validate_variant(self, tab_index: int):
        widget = self.widget(tab_index)
        if isinstance(widget, QScrollArea) and isinstance(widget.widget(), QPlainTextEdit):
            content = widget.widget().toPlainText()
            tab_name = self.tabText(tab_index)
            logger.info(f"Validation demandée pour l'onglet: {tab_name}")
            self.validate_variant_requested.emit(tab_name, content)
        else:
            logger.warning(f"Impossible de valider l'onglet {self.tabText(tab_index)}, contenu non accessible.")
            
    def _handle_save_all_variants(self):
        variants_data = []
        for i in range(self.count()):
            tab_name = self.tabText(i)
            if tab_name.startswith("Variante"):
                widget = self.widget(i)
                if isinstance(widget, QScrollArea) and isinstance(widget.widget(), QPlainTextEdit):
                    content = widget.widget().toPlainText()
                    variants_data.append({"title": tab_name, "content": content})
        if variants_data:
            logger.info(f"Demande de sauvegarde pour {len(variants_data)} variantes.")
            self.save_all_variants_requested.emit(variants_data)
        else:
            QMessageBox.information(self, "Sauvegarde", "Aucune variante à sauvegarder.")


    def update_or_add_tab(self, tab_name: str, content: str, set_current: bool = True) -> int:
        for i in range(self.count()):
            if self.tabText(i) == tab_name:
                widget = self.widget(i)
                if isinstance(widget, QScrollArea):
                    text_edit = widget.widget()
                    if isinstance(text_edit, QPlainTextEdit):
                        text_edit.setPlainText(content)
                        if set_current:
                            self.setCurrentIndex(i)
                        logger.debug(f"Onglet '{tab_name}' mis à jour à l'index {i}.")
                        return i
                # Si le widget n'est pas ce qu'on attend, on le remplace (cas rare)
                logger.warning(f"Widget inattendu pour l'onglet '{tab_name}', remplacement.")
                self.removeTab(i)
                break 
        
        # Si l'onglet n'existe pas, on le crée
        text_edit = QPlainTextEdit()
        text_edit.setPlainText(content)
        text_edit.setReadOnly(True) # Par défaut, les onglets sont en lecture seule
        
        # Amélioration pour la lisibilité et la sélection
        text_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        font = text_edit.font()
        font.setPointSize(10) # Ajuster la taille de la police si nécessaire
        text_edit.setFont(font)
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(text_edit)
        scroll_area.setWidgetResizable(True)
        
        index = self.addTab(scroll_area, tab_name)
        if set_current:
            self.setCurrentIndex(index)
        logger.debug(f"Onglet '{tab_name}' ajouté à l'index {index}.")
        return index

    def get_tab_content(self, tab_name: str) -> str | None:
        for i in range(self.count()):
            if self.tabText(i) == tab_name:
                widget = self.widget(i)
                if isinstance(widget, QScrollArea) and isinstance(widget.widget(), QPlainTextEdit):
                    return widget.widget().toPlainText()
        return None

    def remove_variant_tabs(self):
        indices_to_remove = []
        for i in range(self.count()):
            # Ne pas supprimer l'onglet "Prompt Estimé"
            if self.tabText(i).startswith("Variante"):
                indices_to_remove.append(i)
        
        # Supprimer en ordre décroissant pour éviter les problèmes d'index
        for i in sorted(indices_to_remove, reverse=True):
            logger.debug(f"Suppression de l'onglet de variante: {self.tabText(i)}")
            self.removeTab(i)

    def get_all_variants_content(self) -> list[dict]:
        variants = []
        for i in range(self.count()):
            tab_name = self.tabText(i)
            if tab_name.startswith("Variante"):
                content = self.get_tab_content(tab_name)
                if content:
                    variants.append({"title": tab_name, "content": content})
        return variants

    def make_tab_editable(self, tab_name: str, editable: bool = True):
        for i in range(self.count()):
            if self.tabText(i) == tab_name:
                widget = self.widget(i)
                if isinstance(widget, QScrollArea) and isinstance(widget.widget(), QPlainTextEdit):
                    widget.widget().setReadOnly(not editable)
                    logger.info(f"Onglet '{tab_name}' rendu {'éditable' if editable else 'non éditable'}.")
                    if editable:
                         widget.widget().setFocus() # Donner le focus si rendu éditable
                    return
        logger.warning(f"Tentative de rendre éditable l'onglet '{tab_name}' non trouvé.") 