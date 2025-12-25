from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QPlainTextEdit, 
                               QSizePolicy, QScrollArea, QMessageBox, QPushButton, QHBoxLayout, QStyle, QTextEdit, QMenu)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QKeySequence
import logging
import json
from typing import List, Dict, Union, Optional, Any

try:
    from models.dialogue_structure.interaction import Interaction
except ImportError:
    # Fallback pour le support d'exécution isolée
    import sys
    from pathlib import Path
    current_dir = Path(__file__).resolve().parent.parent.parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    from models.dialogue_structure.interaction import Interaction

logger = logging.getLogger(__name__)

class GeneratedVariantsTabsWidget(QTabWidget):
    """Widget d'affichage des variantes générées dans des onglets."""
    
    validate_variant_requested = Signal(str, str) # tab_name, content
    validate_interaction_requested = Signal(str, Interaction) # tab_name, interaction
    save_all_variants_requested = Signal(list) # list of {title: str, content: str}
    save_all_interactions_requested = Signal(list) # list of (tab_name, interaction)
    regenerate_variant_requested = Signal(str) # variant_id

    def __init__(self, parent=None):
        super().__init__(parent)
        print(f"[DEBUG] Constructeur GeneratedVariantsTabsWidget instancié: self={self} @ {id(self)}")
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self._on_tab_close_requested)
        self.setMovable(True)
        
        self.stored_contents = {}  # Pour stocker le contenu texte de chaque onglet
        self.stored_interactions = {}  # Pour stocker les interactions
        
        # Menu contextuel
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_tab_context_menu)

        # Actions communes
        self.save_all_action = QAction("Sauvegarder toutes les variantes", self)
        self.save_all_action.triggered.connect(self._on_save_all_triggered)
        
    def _show_tab_context_menu(self, pos):
        tab_index = self.tabBar().tabAt(pos)
        if tab_index == -1:
            return
            
        tab_name = self.tabText(tab_index)

        menu = QMenu(self)
        
        # Actions pour cet onglet spécifique
        validate_action = QAction(f"Valider '{tab_name}'", self)
        validate_action.triggered.connect(lambda: self._on_validate_variant_triggered(tab_name))
        
        regenerate_action = QAction(f"Régénérer '{tab_name}'", self)
        regenerate_action.triggered.connect(lambda: self._on_regenerate_variant_triggered(tab_name))
        
        close_action = QAction(f"Fermer '{tab_name}'", self)
        close_action.triggered.connect(lambda: self._on_tab_close_requested(tab_index))
        
        menu.addAction(validate_action)
        menu.addAction(regenerate_action)
        menu.addAction(close_action)
        menu.addSeparator()
        menu.addAction(self.save_all_action)
        
        menu.exec_(self.mapToGlobal(pos))
        
    def clear_all_tabs(self):
        """Supprime tous les onglets."""
        self.clear()
        self.stored_contents.clear()
        self.stored_interactions.clear()
        
    def add_variant_tab(self, tab_name: str, content: str, structured_data: Optional[Dict] = None):
        """Ajoute un nouvel onglet pour une variante générée."""
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        
        content_area = QTextEdit()
        # --- Amélioration UX ---
        # Si structured_data est fourni et peut être converti en Interaction, on affiche joliment
        if structured_data:
            try:
                interaction = Interaction.model_validate(structured_data)
                self.stored_interactions[tab_name] = interaction
                logger.info(f"Interaction créée pour l'onglet '{tab_name}' (affichage formaté)")
                formatted_text = self._format_interaction_for_display(interaction)
                content_area.setPlainText(formatted_text)
            except Exception as e:
                logger.error(f"Erreur lors de la conversion des données en Interaction: {str(e)}")
                # Fallback: affichage JSON
                content_area.setPlainText(json.dumps(structured_data, indent=2, ensure_ascii=False))
        else:
            # Si pas de données structurées, on affiche le texte brut
            content_area.setPlainText(content)
        content_area.setReadOnly(True)
        tab_layout.addWidget(content_area)
        # Stocker le contenu
        self.stored_contents[tab_name] = content
        # Ajout d'un bouton de validation si Interaction
        if tab_name in self.stored_interactions:
            validate_button = QPushButton("Valider cette interaction")
            validate_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))
            def on_validate(tab_name=tab_name):
                self.validate_interaction_requested.emit(tab_name, self.stored_interactions[tab_name])
            validate_button.clicked.connect(on_validate)
            tab_layout.addWidget(validate_button)
        self.addTab(tab, tab_name)
        self.setCurrentWidget(tab)

    def add_interaction_tab(self, tab_name: str, interaction: Interaction):
        """Ajoute un nouvel onglet pour une interaction structurée (affichage lisible)."""
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        # Affichage formaté lisible au lieu du JSON brut
        content_area = QTextEdit()
        formatted_text = self._format_interaction_for_display(interaction)
        content_area.setPlainText(formatted_text)
        content_area.setReadOnly(True)
        tab_layout.addWidget(content_area)
        # Stocker l'interaction
        self.stored_interactions[tab_name] = interaction
        # Ajout d'un bouton de validation en bas de l'onglet
        validate_button = QPushButton("Valider cette interaction")
        validate_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))
        validate_button.clicked.connect(lambda: self.validate_interaction_requested.emit(tab_name, interaction))
        tab_layout.addWidget(validate_button)
        self.addTab(tab, tab_name)
        self.setCurrentWidget(tab)
        
    def _on_tab_close_requested(self, index: int):
        """Ferme un onglet à l'index spécifié."""
        tab_name = self.tabText(index)
        self.removeTab(index)
        
        # Supprimer également des stockages
        if tab_name in self.stored_contents:
            del self.stored_contents[tab_name]
        if tab_name in self.stored_interactions:
            del self.stored_interactions[tab_name]
            
    def _on_validate_variant_triggered(self, tab_name: str):
        """Émet un signal pour valider une variante OU une interaction structurée."""
        if tab_name in self.stored_interactions:
            self.validate_interaction_requested.emit(tab_name, self.stored_interactions[tab_name])
        elif tab_name in self.stored_contents:
            self.validate_variant_requested.emit(tab_name, self.stored_contents[tab_name])
        else:
            logger.error(f"Contenu de l'onglet '{tab_name}' non trouvé.")
            
    def _on_regenerate_variant_triggered(self, tab_name: str):
        """Émet un signal pour régénérer une variante."""
        self.regenerate_variant_requested.emit(tab_name)
        
    def _on_save_all_triggered(self):
        """Émet un signal pour sauvegarder toutes les variantes."""
        variants_data = []
        for tab_name, content in self.stored_contents.items():
            variants_data.append({"title": tab_name, "content": content})
        self.save_all_variants_requested.emit(variants_data)

    def update_or_add_tab(self, tab_name: str, content: str, set_current: bool = True) -> int:
        """Met à jour un onglet existant ou en crée un nouveau."""
        # Mettre à jour le stockage du contenu
        self.stored_contents[tab_name] = content
        
        # Supprimer l'ancienne interaction si elle existe
        if tab_name in self.stored_interactions:
            del self.stored_interactions[tab_name]
            
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
        
        # Créer un nouvel onglet
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        text_edit = QPlainTextEdit()
        text_edit.setPlainText(content)
        text_edit.setReadOnly(True)
        
        scroll_area.setWidget(text_edit)
        scroll_area.setWidgetResizable(True)
        
        index = self.addTab(scroll_area, tab_name)
        if set_current:
            self.setCurrentIndex(index)
        logger.debug(f"Onglet '{tab_name}' ajouté à l'index {index}.")
        return index

    def get_tab_content(self, tab_name: str) -> str | None:
        # Vérifier d'abord dans le stockage des contenus
        if tab_name in self.stored_contents:
            return self.stored_contents[tab_name]
            
        # Sinon chercher dans les widgets (pour compatibilité)
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
            tab_name = self.tabText(i)
            logger.debug(f"Suppression de l'onglet de variante: {tab_name}")
            # Supprimer l'interaction associée si elle existe
            if tab_name in self.stored_interactions:
                del self.stored_interactions[tab_name]
            # Supprimer le contenu stocké si existant
            if tab_name in self.stored_contents:
                del self.stored_contents[tab_name]
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
                    return True
        return False

    def display_variants(self, variants, prompt: str = None):
        """
        Affiche le prompt estimé (si fourni) et les variantes dans les onglets.
        variants: list[str] ou list[dict] (avec 'title' et 'content')
        prompt: str (texte du prompt estimé)
        """
        # 1. Mettre à jour ou créer l'onglet du prompt estimé
        if prompt is not None:
            self.update_or_add_tab("Prompt Estimé", prompt, set_current=True)
        # 2. Supprimer les anciens onglets de variantes
        self.remove_variant_tabs()
        # 3. Ajouter les nouveaux onglets de variantes
        if variants:
            for i, variant in enumerate(variants):
                if isinstance(variant, dict):
                    title = variant.get("title") or f"Variante {i+1}"
                    content = variant.get("content", "")
                else:
                    title = f"Variante {i+1}"
                    content = variant
                self.update_or_add_tab(title, content, set_current=(i==0 and prompt is None))
        else:
            logger.info("Aucune variante à afficher dans display_variants.") 
            
    def _format_interaction_for_display(self, interaction: Interaction) -> str:
        """Convertit une interaction en texte lisible pour l'affichage utilisateur.
        
        Args:
            interaction: L'objet Interaction à formater
            
        Returns:
            Chaîne formatée pour l'affichage humain
        """
        try:
            lines = []
            
            # Titre et ID
            title = getattr(interaction, 'title', 'Sans titre')
            lines.append(f"=== {title} ===")
            lines.append(f"ID: {interaction.interaction_id}")
            lines.append("")
            
            # Tags d'en-tête si présents
            if hasattr(interaction, 'header_tags') and interaction.header_tags:
                lines.append(f"Tags: {', '.join(interaction.header_tags)}")
                lines.append("")
            
            # 1) Parcourir via attribut 'elements' si présent (ancien schéma)
            elements_iterable = None
            if hasattr(interaction, 'elements') and getattr(interaction, 'elements'):
                elements_iterable = getattr(interaction, 'elements')

            # 2) Sinon, tenter de détecter les champs phase_X dynamiques
            if elements_iterable is None:
                phases = []
                idx = 1
                while True:
                    field_name = f"phase_{idx}"
                    if hasattr(interaction, field_name):
                        phases.append(getattr(interaction, field_name))
                        idx += 1
                    else:
                        break
                if phases:
                    elements_iterable = phases

            # Affichage des éléments (qu'ils proviennent de 'elements' ou des phases dynamiques)
            if elements_iterable:
                for i, element in enumerate(elements_iterable):
                    element_type = getattr(element, 'element_type', 'unknown')
                    
                    if element_type == 'dialogue_line':
                        speaker = getattr(element, 'speaker', 'Inconnu')
                        text = getattr(element, 'text', '')
                        lines.append(f"💬 {speaker}: \"{text}\"")
                        
                        # Afficher les tags si présents
                        if hasattr(element, 'tags') and element.tags:
                            lines.append(f"   Tags: {', '.join(element.tags)}")
                            
                    elif element_type == 'command':
                        command = getattr(element, 'command_string', '')
                        lines.append(f"⚙️ Commande: {command}")
                        
                    elif element_type == 'player_choices_block':
                        lines.append("🎯 Choix du joueur:")
                        choices = getattr(element, 'choices', [])
                        for j, choice in enumerate(choices):
                            choice_text = getattr(choice, 'text', '')
                            next_id = getattr(choice, 'next_interaction_id', None)
                            lines.append(f"   {j+1}. \"{choice_text}\"")
                            if next_id:
                                lines.append(f"      → Mène à: {next_id}")
                            
                            # Condition si présente
                            condition = getattr(choice, 'condition', None)
                            if condition:
                                lines.append(f"      Condition: {condition}")
                                
                            # Actions si présentes
                            actions = getattr(choice, 'actions', [])
                            if actions:
                                lines.append(f"      Actions: {', '.join(actions)}")
                    
                    lines.append("")  # Ligne vide entre les éléments
            
            # Interaction suivante par défaut
            if hasattr(interaction, 'next_interaction_id_if_no_choices') and interaction.next_interaction_id_if_no_choices:
                lines.append(f"➡️ Suite automatique: {interaction.next_interaction_id_if_no_choices}")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Erreur lors du formatage de l'interaction pour affichage: {e}")
            return f"Erreur lors de l'affichage de l'interaction: {str(e)}"

    def display_interaction_variants(self, interaction_variants: List[Interaction], prompt: str = None):
        print(f"[DEBUG] display_interaction_variants appelé sur widget={self} @ {id(self)} avec {len(interaction_variants)} interactions")
        # 1. Mettre à jour ou créer l'onglet du prompt estimé
        if prompt is not None:
            self.update_or_add_tab("Prompt Estimé", prompt, set_current=True)
        # 2. Supprimer les anciens onglets de variantes
        self.remove_variant_tabs()
        self.stored_interactions = {}  # Réinitialiser le stockage des interactions
        # 3. Ajouter les nouveaux onglets de variantes d'interactions
        if interaction_variants:
            for i, interaction in enumerate(interaction_variants):
                tab_name = f"Variante {i+1}"  # Titre simplifié sans le titre de l'interaction
                print(f"[DEBUG] Ajout de l'onglet: {tab_name}, interaction_id={getattr(interaction, 'interaction_id', None)}")
                
                # Log du JSON pour debug
                try:
                    interaction_dict = interaction.to_dict()
                    formatted_json = json.dumps(interaction_dict, indent=2, ensure_ascii=False)
                    logger.debug(f"JSON de l'interaction '{tab_name}':\n{formatted_json}")
                except Exception as e:
                    logger.error(f"Erreur lors de la sérialisation JSON de l'interaction '{tab_name}': {e}")
                
                self.stored_interactions[tab_name] = interaction
                # Création du widget d'onglet
                tab = QWidget()
                tab_layout = QVBoxLayout(tab)
                
                # Affichage formaté lisible au lieu du JSON brut
                content_area = QTextEdit()
                formatted_text = self._format_interaction_for_display(interaction)
                content_area.setPlainText(formatted_text)
                content_area.setReadOnly(True)
                # Utilisation d'une police à chasse fixe pour un meilleur alignement
                font = content_area.font()
                font.setFamily("Consolas, Monaco, monospace")
                content_area.setFont(font)
                tab_layout.addWidget(content_area)
                
                # Bouton de validation
                validate_button = QPushButton("Valider cette interaction")
                validate_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))
                def make_validate(tab_name=tab_name, interaction=interaction):
                    return lambda: self.validate_interaction_requested.emit(tab_name, interaction)
                validate_button.clicked.connect(make_validate(tab_name, interaction))
                tab_layout.addWidget(validate_button)
                self.addTab(tab, tab_name)
                self.setCurrentWidget(tab)
            logger.info(f"{len(interaction_variants)} variantes d'interactions affichées en format lisible.")
        else:
            logger.info("Aucune variante d'interaction à afficher.")
            
    def get_interaction(self, tab_name: str) -> Optional[Interaction]:
        """
        Récupère l'objet Interaction associé à un onglet.
        
        Args:
            tab_name: Nom de l'onglet
            
        Returns:
            L'objet Interaction associé ou None si non trouvé
        """
        return self.stored_interactions.get(tab_name)
    
    def get_all_interactions(self) -> Dict[str, Interaction]:
        """
        Récupère toutes les interactions stockées.
        
        Returns:
            Dictionnaire {tab_name: Interaction}
        """
        return self.stored_interactions.copy() 
