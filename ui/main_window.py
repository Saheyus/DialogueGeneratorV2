# DialogueGenerator/ui/main_window.py
import json
import asyncio # Ajout pour exécuter les tâches asynchrones
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QComboBox, QTextEdit, QSplitter, 
                               QListWidget, QListWidgetItem, QTreeView, QAbstractItemView, QLineEdit,
                               QGroupBox, QHeaderView, QPushButton, QTabWidget, QApplication, QGridLayout, QCheckBox)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QPalette, QColor, QAction
from PySide6.QtCore import Qt, QSize, QTimer, QItemSelectionModel, QSortFilterProxyModel, QRegularExpression
import sys
import os
from pathlib import Path # Ajout pour la gestion des chemins
import webbrowser # Ajout pour ouvrir le fichier de configuration

# Importer les nouveaux modules
from prompt_engine import PromptEngine
from llm_client import OpenAIClient, DummyLLMClient

# Chemin vers le répertoire du DialogueGenerator
DIALOGUE_GENERATOR_DIR = Path(__file__).parent.parent
UI_SETTINGS_FILE = DIALOGUE_GENERATOR_DIR / "ui_settings.json" # Fichier pour sauvegarder les paramètres UI
CONTEXT_CONFIG_FILE_PATH = DIALOGUE_GENERATOR_DIR / "context_config.json" # Chemin vers context_config.json

# S'assurer que le répertoire parent de DialogueGenerator (racine du projet) est dans le PYTHONPATH
PROJECT_ROOT = DIALOGUE_GENERATOR_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Importer ContextBuilder après avoir ajusté le path
from DialogueGenerator.context_builder import ContextBuilder

# Pour le logging
import logging
logger = logging.getLogger(__name__)

def populate_tree_view(model, parent_item, data):
    """Popule récursivement le QTreeView avec les données d'un dictionnaire ou d'une liste."""
    if isinstance(data, dict):
        for key, value in data.items():
            key_item = QStandardItem(str(key))
            key_item.setEditable(False)
            
            if isinstance(value, (dict, list)):
                # La clé est une ligne parente, les enfants seront les paires clé-valeur du dict/list imbriqué
                parent_item.appendRow(key_item) 
                populate_tree_view(model, key_item, value) # Appel récursif pour les enfants
            else:
                # Clé et valeur simple sur la même ligne, dans des colonnes différentes
                value_item = QStandardItem(str(value))
                value_item.setEditable(False)
                parent_item.appendRow([key_item, value_item]) 

    elif isinstance(data, list):
        for index, value in enumerate(data):
            # L'index est affiché comme une "clé" pour les éléments de la liste
            index_item = QStandardItem(f"[{index}]")
            index_item.setEditable(False)

            if isinstance(value, (dict, list)):
                parent_item.appendRow(index_item)
                populate_tree_view(model, index_item, value)
            else:
                value_item = QStandardItem(str(value))
                value_item.setEditable(False)
                parent_item.appendRow([index_item, value_item])

class MainWindow(QMainWindow):
    """Fenêtre principale de l'application DialogueGenerator.

    Cette classe gère l'interface utilisateur pour la sélection du contexte,
    la configuration des paramètres de génération, l'affichage des prompts
    et des variantes de dialogues générées par un LLM.
    """
    def __init__(self, context_builder: ContextBuilder):
        """Initialise la MainWindow.

        Args:
            context_builder: Instance de ContextBuilder pour accéder aux données du GDD.
        """
        super().__init__()
        self.context_builder = context_builder
        self.prompt_engine = PromptEngine()
        
        # --- Choix du Client LLM ---
        # Pour l'instant, on utilise OpenAIClient par défaut.
        # Assurez-vous que la variable d'environnement OPENAI_API_KEY est définie.
        try:
            self.llm_client = OpenAIClient(model="gpt-4o-mini") # Utilisation de gpt-4o-mini
            if not self.llm_client.api_key:
                print("ATTENTION: Clé API OpenAI non trouvée. Passage au DummyLLMClient.")
                self.llm_client = DummyLLMClient()
        except Exception as e:
            print(f"Erreur lors de l'initialisation de OpenAIClient: {e}. Passage au DummyLLMClient.")
            self.llm_client = DummyLLMClient()

        self.setWindowTitle("Générateur de Dialogues IA - Context Builder")
        self.setGeometry(100, 100, 1800, 900) # Encore un peu plus large pour les onglets

        self._create_actions() # Créer les actions avant de créer les menus
        self._create_menu_bar() # Créer la barre de menus

        self.setup_ui()
        if self.context_builder:
            self.load_initial_data()

        # Charger les paramètres UI après avoir peuplé les widgets
        self._load_ui_settings() 

        # Initialiser le timer pour la mise à jour du contexte/tokens (si nécessaire)
        self.token_update_timer = QTimer(self)
        self.token_update_timer.setSingleShot(True)
        self.token_update_timer.timeout.connect(self._update_token_estimation_and_prompt_display)
        self.token_update_timer.start(500) # Lancer une première fois après le chargement

    def _create_actions(self):
        """Crée les actions pour les menus."""
        self.restore_selections_action = QAction("Restaurer les sélections au démarrage", self)
        self.restore_selections_action.setCheckable(True)
        self.restore_selections_action.setChecked(True) # Par défaut
        # La logique de sauvegarde/chargement de cet état sera dans _save/_load_ui_settings

        self.edit_context_config_action = QAction("&Modifier la configuration du contexte...", self)
        self.edit_context_config_action.triggered.connect(self._open_context_config_file)

        self.exit_action = QAction("&Quitter", self)
        self.exit_action.triggered.connect(self.close)

    def _create_menu_bar(self):
        """Crée la barre de menus principale avec les options de l'application."""
        menu_bar = self.menuBar()

        # Menu Fichier (ou Options)
        options_menu = menu_bar.addMenu("&Options")
        options_menu.addAction(self.restore_selections_action)
        options_menu.addSeparator()
        options_menu.addAction(self.edit_context_config_action) 
        options_menu.addSeparator()
        options_menu.addAction(self.exit_action)

    def _open_context_config_file(self):
        """Ouvre le fichier de configuration du contexte (context_config.json)
        dans l'éditeur par défaut du système.
        """
        if CONTEXT_CONFIG_FILE_PATH.exists():
            try:
                webbrowser.open(os.path.realpath(CONTEXT_CONFIG_FILE_PATH))
                logger.info(f"Tentative d'ouverture de {CONTEXT_CONFIG_FILE_PATH}")
            except Exception as e:
                logger.error(f"Impossible d'ouvrir {CONTEXT_CONFIG_FILE_PATH}: {e}")
                self.statusBar().showMessage(f"Erreur: Impossible d'ouvrir le fichier de configuration: {e}")
        else:
            logger.warning(f"Le fichier de configuration {CONTEXT_CONFIG_FILE_PATH} n'existe pas.")
            self.statusBar().showMessage("Erreur: Fichier de configuration du contexte non trouvé.")

    def _create_left_selection_panel(self) -> QWidget:
        """Crée et configure le panneau de sélection de gauche.

        Ce panneau contient des listes filtrables pour les personnages, lieux, objets,
        espèces, communautés et exemples de dialogues.

        Returns:
            QWidget: Le widget contenant le panneau de sélection de gauche.
        """
        left_scroll_area_content = QWidget()
        left_panel_layout = QVBoxLayout(left_scroll_area_content)
        left_panel_layout.setSpacing(10)

        def create_list_section(label_text, object_name_prefix):
            label = QLabel(label_text)
            filter_edit = QLineEdit()
            filter_edit.setPlaceholderText(f"Filtrer {label_text.lower().replace(':', '')}...")
            list_widget = QListWidget()
            list_widget.setObjectName(f"{object_name_prefix}_list")
            
            filter_edit.textChanged.connect(lambda text, lw=list_widget, lbl=label, original_text=label_text: self.filter_list_widget(text, lw, lbl, original_text))
            
            left_panel_layout.addWidget(label)
            left_panel_layout.addWidget(filter_edit)
            left_panel_layout.addWidget(list_widget)
            return list_widget, filter_edit, label

        self.character_list, self.character_filter, self.character_label = create_list_section("Personnages:", "character")
        self.character_list.itemClicked.connect(lambda item_widget: self.on_explorer_list_item_clicked(self.character_list, self.context_builder.characters if self.context_builder else [], "Personnage", item_widget))

        self.location_list, self.location_filter, self.location_label = create_list_section("Lieux:", "location")
        self.location_list.itemClicked.connect(lambda item_widget: self.on_explorer_list_item_clicked(self.location_list, self.context_builder.locations if self.context_builder else [], "Lieu", item_widget))
        
        self.item_list, self.item_filter, self.item_label = create_list_section("Objets:", "item")
        self.item_list.itemClicked.connect(lambda item_widget: self.on_explorer_list_item_clicked(self.item_list, self.context_builder.items if self.context_builder else [], "Objet", item_widget))

        self.species_list, self.species_filter, self.species_label = create_list_section("Espèces:", "species")
        self.species_list.itemClicked.connect(lambda item_widget: self.on_explorer_list_item_clicked(self.species_list, self.context_builder.species if self.context_builder else [], "Espèce", item_widget))

        self.communities_list, self.communities_filter, self.communities_label = create_list_section("Communautés:", "communities")
        self.communities_list.itemClicked.connect(lambda item_widget: self.on_explorer_list_item_clicked(self.communities_list, self.context_builder.communities if self.context_builder else [], "Communauté", item_widget))
        
        self.dialogues_list, self.dialogues_filter, self.dialogues_label = create_list_section("Exemples Dialogues:", "dialogues")
        self.dialogues_list.itemClicked.connect(lambda item_widget: self.on_explorer_list_item_clicked(self.dialogues_list, self.context_builder.dialogues_examples if self.context_builder else [], "Dialogue Exemple", item_widget, name_key_priority=["Nom", "Titre", "ID"]))
        
        left_container_widget = QWidget()
        left_container_widget.setLayout(left_panel_layout)
        left_container_widget.setMinimumWidth(300)
        left_container_widget.setMaximumWidth(400)
        return left_container_widget

    def _create_center_details_panel(self) -> QWidget:
        """Crée et configure le panneau central pour afficher les détails.

        Ce panneau utilise un QTreeView pour présenter les informations
        détaillées de l'élément sélectionné dans les listes de gauche.

        Returns:
            QWidget: Le widget contenant le panneau des détails.
        """
        details_panel = QWidget()
        details_layout = QVBoxLayout(details_panel)
        self.details_label = QLabel("Détails de l'élément sélectionné:")
        self.details_tree_view = QTreeView()
        self.details_tree_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.details_tree_model = QStandardItemModel()
        self.details_tree_model.setHorizontalHeaderLabels(["Propriété", "Valeur"])
        self.details_tree_view.setModel(self.details_tree_model)
        self.details_tree_view.header().setVisible(True)
        
        details_layout.addWidget(self.details_label)
        details_layout.addWidget(self.details_tree_view)
        return details_panel

    def _create_right_generation_panel(self) -> QWidget:
        """Crée et configure le panneau de droite pour la génération de dialogues.

        Ce panneau inclut les sélections pour la scène (personnages, lieu),
        les paramètres de génération (nombre de variantes, tokens max, mode test),
        le champ pour les instructions utilisateur, le bouton de génération,
        et les onglets pour afficher le prompt et les variantes générées.

        Returns:
            QWidget: Le widget contenant le panneau de génération.
        """
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        self.generation_params_group = QGroupBox("Paramètres de Génération")
        generation_params_layout = QVBoxLayout()

        # Sélection des personnages et du lieu pour la scène
        context_select_layout = QGridLayout()
        self.char_a_label = QLabel("Personnage A:")
        self.char_a_combo = QComboBox()
        self.char_a_combo.setMaxVisibleItems(15) # Augmentation du nombre d'items visibles
        self.char_a_combo.currentIndexChanged.connect(self._update_token_estimation_and_prompt_display)
        self.char_b_label = QLabel("Personnage B (Interlocuteur):")
        self.char_b_combo = QComboBox()
        self.char_b_combo.setMaxVisibleItems(15) # Augmentation du nombre d'items visibles
        self.char_b_combo.currentIndexChanged.connect(self._update_token_estimation_and_prompt_display)
        
        # Remplacement de location_combo_gen par region et sub_location
        self.region_label_gen = QLabel("Région de la Scène:")
        self.region_combo_gen = QComboBox()
        self.region_combo_gen.setMaxVisibleItems(15)
        self.region_combo_gen.currentIndexChanged.connect(self.on_region_changed_for_sub_locations)
        self.region_combo_gen.currentIndexChanged.connect(self._update_token_estimation_and_prompt_display)

        self.sub_location_label_gen = QLabel("Sous-Lieu (optionnel):")
        self.sub_location_combo_gen = QComboBox()
        self.sub_location_combo_gen.setMaxVisibleItems(15)
        self.sub_location_combo_gen.currentIndexChanged.connect(self._update_token_estimation_and_prompt_display)

        # Bouton pour suggérer les éléments liés
        self.suggest_linked_button = QPushButton("Sélectionner Éléments Liés")
        self.suggest_linked_button.clicked.connect(self.on_suggest_linked_elements)

        context_select_layout.addWidget(self.char_a_label, 0, 0)
        context_select_layout.addWidget(self.char_a_combo, 0, 1)
        context_select_layout.addWidget(self.char_b_label, 1, 0)
        context_select_layout.addWidget(self.char_b_combo, 1, 1)
        context_select_layout.addWidget(self.region_label_gen, 2, 0) # Nouveau label pour région
        context_select_layout.addWidget(self.region_combo_gen, 2, 1) # Nouveau combo pour région
        context_select_layout.addWidget(self.sub_location_label_gen, 3, 0) # Nouveau label pour sous-lieu
        context_select_layout.addWidget(self.sub_location_combo_gen, 3, 1) # Nouveau combo pour sous-lieu
        context_select_layout.addWidget(self.suggest_linked_button, 4, 0, 1, 2) # Bouton sur toute la largeur
        
        generation_params_layout.addLayout(context_select_layout)
        generation_params_layout.addSpacing(10)

        # Nombre de variantes k
        k_layout = QHBoxLayout()
        k_layout.addWidget(QLabel("Nombre de variantes (k):"))
        self.k_variants_input = QLineEdit("1") # Valeur par défaut à 1
        self.k_variants_input.setFixedWidth(50)
        k_layout.addWidget(self.k_variants_input)
        k_layout.addStretch() # Pousse le QLineEdit vers la gauche
        generation_params_layout.addLayout(k_layout)

        # Max Tokens pour la génération
        tokens_layout = QHBoxLayout()
        tokens_layout.addWidget(QLabel("Max K Tokens:"))
        self.max_tokens_input = QLineEdit("4")
        self.max_tokens_input.setPlaceholderText("ex: 4 (pour 4000)")
        self.max_tokens_input.setFixedWidth(60)
        tokens_layout.addWidget(self.max_tokens_input)
        tokens_layout.addStretch()
        generation_params_layout.addLayout(tokens_layout)

        self.include_dialogue_type_checkbox = QCheckBox("Inclure 'Dialogue Type' du personnage")
        self.include_dialogue_type_checkbox.setChecked(True) # Coché par défaut
        self.include_dialogue_type_checkbox.stateChanged.connect(self._update_token_estimation_and_prompt_display)
        generation_params_layout.addWidget(self.include_dialogue_type_checkbox)
        generation_params_layout.addSpacing(5)

        generation_params_layout.addWidget(QLabel("Instructions spécifiques pour la scène / Prompt utilisateur:"))
        self.user_instruction_input = QTextEdit("Ex: Le Personnage A doit convaincre le Personnage B de lui révéler un secret. Ton: mystérieux. Inclure une référence à l'artefact X.")
        self.user_instruction_input.setFixedHeight(100)
        self.user_instruction_input.textChanged.connect(self._update_token_estimation_and_prompt_display)
        generation_params_layout.addWidget(self.user_instruction_input)
        
        # Layout pour bouton Générer et compteur de tokens
        generate_action_layout = QHBoxLayout()
        self.generate_button = QPushButton("Générer le Dialogue")
        self.generate_button.clicked.connect(self.on_generate_button_clicked)
        self.token_count_label = QLabel("Estim. mots: 0") # Nouveau QLabel
        self.token_count_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        generate_action_layout.addWidget(self.generate_button)
        generate_action_layout.addStretch()
        generate_action_layout.addWidget(self.token_count_label)
        generation_params_layout.addLayout(generate_action_layout)
        
        self.generation_params_group.setLayout(generation_params_layout)
        
        self.variant_tabs = QTabWidget()
        right_layout.addWidget(self.generation_params_group)
        right_layout.addWidget(self.variant_tabs)
        right_panel.setMinimumWidth(500) # Augmenter un peu la largeur minimale
        return right_panel

    def setup_ui(self):
        """Configure l'interface utilisateur principale de la fenêtre.

        Initialise les panneaux gauche, central et droit, les assemble dans un
        splitter et les ajoute au widget central de la fenêtre.
        """
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        left_panel = self._create_left_selection_panel()
        center_panel = self._create_center_details_panel()
        right_panel = self._create_right_generation_panel()
        
        # Utilisation d'un QSplitter principal pour séparer listes, détails et paramètres
        # Il est important que self.splitter soit assigné ici si _save_ui_settings et _load_ui_settings
        # y font référence.
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(left_panel) 
        self.splitter.addWidget(center_panel)
        self.splitter.addWidget(right_panel)
        
        self.splitter.setStretchFactor(0, 1) # Panel listes
        self.splitter.setStretchFactor(1, 2) # Panel détails TreeView
        self.splitter.setStretchFactor(2, 2) # Panel génération + variantes

        main_layout.addWidget(self.splitter)
        
        self.statusBar().showMessage("Prêt.")
        self.active_list_widget_for_details = None

    def _get_current_selections_for_context(self) -> dict:
        """Récupère toutes les sélections utilisateur pertinentes pour la construction du contexte.

        Retourne:
            dict: Un dictionnaire avec les catégories d'éléments (characters, locations, etc.)
                  et une liste de noms d'éléments sélectionnés pour chaque catégorie.
        """
        ignore_values = {"-- Aucun --", "<Aucun>", "-- Toutes --", ""}
        selections = {
            "characters": [],
            "locations": [],
            "items": [],
            "species": [],
            "communities": [],
            "dialogues_examples": [],
            "quests": [] # Gardé pour une éventuelle utilisation future
        }

        # Personnages principaux depuis les ComboBox
        char_a = self.char_a_combo.currentText()
        char_b = self.char_b_combo.currentText()
        if char_a not in ignore_values: selections["characters"].append(char_a)
        if char_b not in ignore_values: selections["characters"].append(char_b)

        # Lieux sélectionnés (région et/ou sous-lieu) depuis les ComboBox
        current_region = self.region_combo_gen.currentText()
        current_sub_location = self.sub_location_combo_gen.currentText()
        
        # Priorité au sous-lieu s'il est spécifié et valide
        if current_sub_location not in ignore_values:
            selections["locations"].append(current_sub_location)
        elif current_region not in ignore_values:
            selections["locations"].append(current_region)

        # Éléments cochés des listes de gauche
        for list_w, cat_name in [
            (self.character_list, "characters"), 
            (self.location_list, "locations"),
            (self.item_list, "items"), 
            (self.species_list, "species"),
            (self.communities_list, "communities"), 
            (self.dialogues_list, "dialogues_examples")
            # Ajouter (self.quest_list, "quests") si une liste de quêtes est implémentée
        ]:
            for i in range(list_w.count()):
                item_w = list_w.item(i)
                if item_w.checkState() == Qt.Checked:
                    item_text = item_w.text()
                    if item_text not in ignore_values:
                        selections[cat_name].append(item_text)
        
        # Dédoublonner les listes et s'assurer que les valeurs ignorées sont parties
        for cat_key in selections:
            valid_items = []
            seen = set() 
            for item_name in selections[cat_key]:
                if item_name not in ignore_values and item_name not in seen:
                    valid_items.append(item_name)
                    seen.add(item_name)
            selections[cat_key] = valid_items
        
        return selections

    def _update_token_estimation_and_prompt_display(self):
        """Met à jour l'estimation du nombre de tokens et affiche le prompt estimé.

        Cette méthode est appelée lorsque les sélections de contexte ou les
        instructions utilisateur changent. Elle construit le contexte, puis
        le prompt complet avec PromptEngine, et met à jour le label de comptage
        des tokens ainsi que l'onglet de prévisualisation du prompt.
        """
        if not self.context_builder: return

        # Valeurs à ignorer lors de la collecte des noms
        ignore_values = {"-- Aucun --", "<Aucun>", "-- Toutes --", ""} # Conservé localement si besoin plus tard, mais la logique principale est dans _get_current_selections

        # Récupérer les sélections pour build_context via la nouvelle méthode centralisée
        selected_elements_for_build = self._get_current_selections_for_context()

        user_instruction = self.user_instruction_input.toPlainText()
        include_dialogue_type = self.include_dialogue_type_checkbox.isChecked()
        
        # Appel à build_context pour le contexte brut
        MAX_TOKENS_FOR_CONTEXT_BUILDING = 32000 # Assez grand pour ne pas tronquer lors de la construction initiale du contexte
        
        context_str = self.context_builder.build_context(
            selected_elements_for_build,
            user_instruction, # L'instruction est passée ici pour que ContextBuilder puisse potentiellement l'utiliser
            max_tokens=MAX_TOKENS_FOR_CONTEXT_BUILDING, 
            include_dialogue_type=include_dialogue_type
        )
        
        context_tokens = self.context_builder._count_tokens(context_str) 

        # Maintenant, construire le prompt complet avec PromptEngine pour l'estimation totale
        generation_params_preview = {} # Pour l'instant, pas de paramètres UI spécifiques pour le PromptEngine
        # L'instruction utilisateur est déjà dans user_instruction
        
        estimated_full_prompt, estimated_total_tokens = self.prompt_engine.build_prompt(
            context_summary=context_str, # Le contexte déjà construit (et potentiellement tronqué)
            user_specific_goal=user_instruction,
            generation_params=generation_params_preview
        )
        
        self.token_count_label.setText(f"Contexte: {context_tokens} / Prompt Total (estim.): {estimated_total_tokens} tokens")

        # Afficher le prompt complet estimé dans le premier onglet
        preview_tab_title = "Prompt Complet (Estim.)"
        if self.variant_tabs.count() == 0:
            prompt_preview_tab = QTextEdit()
            prompt_preview_tab.setReadOnly(True)
            self.variant_tabs.addTab(prompt_preview_tab, preview_tab_title)
        else:
            # S'assurer que le premier onglet est bien celui de la prévisualisation
            self.variant_tabs.setTabText(0, preview_tab_title) 
        
        preview_widget = self.variant_tabs.widget(0)
        if isinstance(preview_widget, QTextEdit):
            preview_widget.setPlainText(estimated_full_prompt)

    def on_generate_button_clicked(self):
        """Gère l'événement de clic sur le bouton 'Générer le Dialogue'.

        Récupère les sélections utilisateur, construit le contexte et le prompt final,
        appelle le client LLM pour générer les variantes de dialogue, et affiche
        le prompt et les variantes (ou erreurs) dans des onglets.
        """
        self.statusBar().showMessage("Génération en cours...")
        # Nettoyer les anciens onglets de variantes, mais garder le premier (prévisualisation du prompt)
        # s'il existe déjà. Sinon, il sera créé par _update_token_estimation_and_prompt_display si nécessaire.
        # Ou, pour être plus simple, on le recrée ici s'il n'est pas là ou s'il y a d'autres onglets.
        while self.variant_tabs.count() > 0: # Enlever tous les onglets (y compris celui de preview pour le recréer avec le prompt final)
            self.variant_tabs.removeTab(0)

        if not self.context_builder:
            self.statusBar().showMessage("ContextBuilder non initialisé.")
            return

        user_instruction = self.user_instruction_input.toPlainText()
        if not user_instruction.strip():
            self.statusBar().showMessage("Veuillez entrer une instruction pour le LLM.")
            # Remettre un onglet de base pour le prompt si on s'arrête ici
            self._update_token_estimation_and_prompt_display() # Pour réafficher le prompt estimé
            return
        
        # Récupérer les sélections actuelles via la nouvelle méthode centralisée
        selected_elements_for_build = self._get_current_selections_for_context()

        include_dialogue_type = self.include_dialogue_type_checkbox.isChecked()
        
        try:
            max_k_tokens_str = self.max_tokens_input.text().replace("k", "").replace("K", "").strip()
            max_context_tokens_for_builder = int(float(max_k_tokens_str) * 1000) if max_k_tokens_str else 4000 # Ceci est pour ContextBuilder
            if max_context_tokens_for_builder <= 0: max_context_tokens_for_builder = 4000 
        except ValueError:
            max_context_tokens_for_builder = 4000 
        
        # 1. Construire le contexte avec ContextBuilder
        # L'instruction utilisateur est passée ici car ContextBuilder la prend en compte pour le résumé "Vision"
        context_summary_str = self.context_builder.build_context(
            selected_elements_for_build,
            user_instruction, # L'instruction utilisateur
            max_tokens=max_context_tokens_for_builder, # Max tokens pour la chaîne de contexte seule
            include_dialogue_type=include_dialogue_type
        )

        # 2. Construire le prompt final avec PromptEngine
        generation_params_for_engine = {} # Peut être rempli par des contrôles UI pour le ton, style, etc.
        # if self.tone_combo.currentText() != "-- Aucun --": # Exemple
        #     generation_params_for_engine["tone"] = self.tone_combo.currentText()

        current_prompt_for_llm, num_tokens_total_prompt = self.prompt_engine.build_prompt(
            context_summary=context_summary_str,
            user_specific_goal=user_instruction,
            generation_params=generation_params_for_engine
        )
        
        # Mettre à jour le label avec le compte de tokens du prompt qui sera envoyé au LLM
        context_tokens_final = self.context_builder._count_tokens(context_summary_str) # Recalculer pour le contexte réellement utilisé
        self.token_count_label.setText(f"Contexte: {context_tokens_final} / Prompt LLM: {num_tokens_total_prompt} tokens")

        # Afficher le prompt final (celui envoyé au LLM) dans le premier onglet
        prompt_display_tab = QTextEdit()
        prompt_display_tab.setReadOnly(True)
        prompt_display_tab.setPlainText(current_prompt_for_llm)
        self.variant_tabs.insertTab(0, prompt_display_tab, "Prompt Final (pour LLM)") # Insérer en premier
        self.variant_tabs.setCurrentIndex(0) # S'assurer qu'il est visible

        try:
            k_value = int(self.k_variants_input.text())
            if k_value <= 0:
                self.statusBar().showMessage("Le nombre de variantes (k) doit être positif.")
                # Pas besoin de recréer l'onglet prompt ici, il est déjà là
                return
        except ValueError:
            self.statusBar().showMessage("Le nombre de variantes (k) doit être un entier.")
            return

        self.statusBar().showMessage(f"Génération de {k_value} variantes avec {type(self.llm_client).__name__}... (Prompt: {num_tokens_total_prompt} tokens)")
        QApplication.processEvents() 

        try:
            variants = asyncio.run(self.llm_client.generate_variants(current_prompt_for_llm, k_value))
            
            if variants:
                for i, variant_text in enumerate(variants):
                    tab_content = QTextEdit()
                    tab_content.setPlainText(variant_text)
                    tab_content.setReadOnly(True) 
                    self.variant_tabs.addTab(tab_content, f"Variante {i+1}")
                self.statusBar().showMessage(f"{len(variants)} variantes générées. Prompt LLM: {num_tokens_total_prompt} tokens.")
            else:
                self.statusBar().showMessage("Aucune variante n'a été générée.")

        except Exception as e:
            self.statusBar().showMessage(f"Erreur lors de la génération: {e}")
            error_tab = QTextEdit()
            # Afficher l'erreur et le prompt qui a causé l'erreur
            error_tab.setPlainText(f"Une erreur est survenue:\\n{type(e).__name__}: {e}\\n\\nPrompt utilisé ({num_tokens_total_prompt} tokens):\\n{current_prompt_for_llm}")
            self.variant_tabs.addTab(error_tab, "Erreur") # Ajouter l'onglet d'erreur après celui du prompt
            logger.error(f"Erreur lors de la génération : {e}", exc_info=True)

    def filter_list_widget(self, text, list_widget, label_widget, original_label_text):
        """Filtre les éléments d'un QListWidget en fonction du texte saisi.

        Cache les éléments qui ne correspondent pas au texte et met à jour
        le label associé pour afficher le nombre d'éléments visibles/total.

        Args:
            text (str): Le texte utilisé pour filtrer.
            list_widget (QListWidget): Le widget QListWidget à filtrer.
            label_widget (QLabel): Le QLabel à mettre à jour avec le comptage.
            original_label_text (str): Le texte original du label (sans le comptage).
        """
        visible_items = 0
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            if item:
                is_hidden = text.lower() not in item.text().lower()
                item.setHidden(is_hidden)
                if not is_hidden:
                    visible_items += 1
        # Met à jour le label avec le nombre d'éléments visibles/total
        total_items = list_widget.count()
        label_widget.setText(f"{original_label_text} ({visible_items}/{total_items})")

    def _populate_list_widget(self, list_widget: QListWidget, data_list, name_extractor_func, label_widget, original_label_text):
        """Peuple un QListWidget avec des données et configure les éléments pour être cochables.
        
        Args:
            list_widget: Le QListWidget à peupler.
            data_list: La liste de données source (actuellement non utilisée directement).
            name_extractor_func: Une fonction callable qui retourne une liste de noms à afficher.
            label_widget: Le QLabel associé à la liste, pour afficher le comptage.
            original_label_text: Le texte de base du label.
        """
        list_widget.clear()
        names = []
        valid_names = [] # Initialiser valid_names ici
        if self.context_builder and callable(name_extractor_func): # Vérifier que name_extractor_func est appelable
            names = name_extractor_func()
        
        # Déconnecter les anciens signaux pour éviter les connexions multiples si cette fonction est appelée plusieurs fois
        try:
            list_widget.itemChanged.disconnect()
        except (TypeError, RuntimeError): # TypeError si jamais connecté, RuntimeError si connecté mais slot introuvable
            pass

        if names:
            valid_names = [str(name) for name in names if name is not None]
            for name_str in valid_names:
                item = QListWidgetItem(name_str)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
                list_widget.addItem(item)
            label_widget.setText(f"{original_label_text} ({len(valid_names)}/{len(valid_names)})")
            list_widget.itemChanged.connect(self._on_list_item_check_changed) # Connecter le signal ici
        else:
            list_widget.addItem(QListWidgetItem("Aucun élément."))
            label_widget.setText(f"{original_label_text} (0/0)")
        if list_widget.count() > 0:
            list_widget.setCurrentItem(None)
        self.statusBar().showMessage(f"Données chargées: {len(valid_names)} éléments Prêt.")
        self._update_token_estimation_and_prompt_display() # Appel initial pour mettre à jour le compteur

    def load_initial_data(self):
        """Charge les données initiales dans les listes et combobox de l'interface.
        
        Peuple les listes de personnages, lieux, etc., ainsi que les combobox
        pour la sélection de la scène. Met également à jour l'estimation des tokens.
        """
        if not self.context_builder: return

        # Peupler les listes de gauche
        self._populate_list_widget(self.character_list, [], self.context_builder.get_characters_names, self.character_label, "Personnages:")
        self._populate_list_widget(self.location_list, [], self.context_builder.get_locations_names, self.location_label, "Lieux:")
        self._populate_list_widget(self.item_list, [], self.context_builder.get_items_names, self.item_label, "Objets:")
        self._populate_list_widget(self.species_list, [], self.context_builder.get_species_names, self.species_label, "Espèces:")
        self._populate_list_widget(self.communities_list, [], self.context_builder.get_communities_names, self.communities_label, "Communautés:")
        self._populate_list_widget(self.dialogues_list, [], self.context_builder.get_dialogue_examples_titles, self.dialogues_label, "Exemples Dialogues:")

        # Peupler les ComboBox pour Personnage A et B
        char_names = ["-- Aucun --"] + (self.context_builder.get_characters_names() if self.context_builder else [])
        self.char_a_combo.clear()
        self.char_a_combo.addItems(char_names)
        self.char_b_combo.clear()
        self.char_b_combo.addItems(char_names)

        # Peupler le ComboBox des Régions
        region_names = ["-- Toutes --"] + self.context_builder.get_regions()
        self.region_combo_gen.clear()
        self.region_combo_gen.addItems(region_names)
        self.on_region_changed_for_sub_locations() # Pour peupler les sous-lieux initialement
        
        self.statusBar().showMessage("Données initiales chargées.")
        self._update_token_estimation_and_prompt_display() # Mettre à jour l'estimation initiale

    def on_region_changed_for_sub_locations(self):
        """Met à jour la liste des sous-lieux lorsque la région sélectionnée change.
        
        Appelé lorsque l'utilisateur modifie la sélection dans le combobox des régions.
        Peuple le combobox des sous-lieux avec les localités correspondantes à la région.
        """
        if not self.context_builder: return
        
        selected_region = self.region_combo_gen.currentText()
        self.sub_location_combo_gen.clear()
        self.sub_location_combo_gen.addItem("-- Aucun --") # Option par défaut

        if selected_region and selected_region != "-- Toutes --":
            sub_locations = self.context_builder.get_sub_locations(selected_region)
            if sub_locations:
                self.sub_location_combo_gen.addItems(sub_locations)
        # Si "-- Toutes --" est sélectionné pour la région, sub_location_combo_gen reste avec "-- Aucun --" 
        # ou pourrait être désactivé/caché.

    def on_suggest_linked_elements(self):
        """Gère le clic sur le bouton 'Sélectionner Éléments Liés'.
        
        Récupère les éléments liés au personnage A et/ou au lieu sélectionnés
        via ContextBuilder, puis coche automatiquement ces éléments dans les
        listes de gauche correspondantes.
        """
        if not self.context_builder: return

        char_a_name = self.char_a_combo.currentText()
        if char_a_name == "-- Aucun --" or char_a_name == "<Aucun>": char_a_name = None # Correction pour gérer <Aucun>
        
        selected_locations = []
        region_name = self.region_combo_gen.currentText()
        sub_loc_name = self.sub_location_combo_gen.currentText()

        if sub_loc_name and sub_loc_name != "-- Aucun --":
            selected_locations.append(sub_loc_name)
        elif region_name and region_name != "-- Toutes --" and region_name != "<Aucun>": # Correction pour gérer <Aucun>
            selected_locations.append(region_name)

        if not char_a_name and not selected_locations:
            self.statusBar().showMessage("Veuillez sélectionner un Personnage A et/ou un Lieu/Région pour suggérer des liens.")
            return

        linked_data = self.context_builder.get_linked_elements(char_a_name, selected_locations)
        
        # Parcourir les listes de gauche et cocher les éléments trouvés
        list_map = {
            "characters": self.character_list,
            "locations": self.location_list,
            "items": self.item_list,
            "species": self.species_list,
            "communities": self.communities_list
            # "quests" et "dialogues_examples" ne sont pas typiquement liés de cette manière dans get_linked_elements pour l'instant
        }

        for category, names_set in linked_data.items():
            if category in list_map and names_set:
                list_widget = list_map[category]
                for i in range(list_widget.count()):
                    item = list_widget.item(i)
                    if item.text() in names_set:
                        item.setCheckState(Qt.Checked)
        
        # Les lignes suivantes qui repeuplent les QComboBox des personnages sont commentées
        # car elles réinitialisent la sélection existante.
        # character_names = self.context_builder.get_characters_names() if self.context_builder else []
        # valid_character_names = ["<Aucun>"] + [str(name) for name in character_names if name is not None]
        # self.char_a_combo.clear()
        # self.char_a_combo.addItems(valid_character_names)
        # self.char_b_combo.clear()
        # self.char_b_combo.addItems(valid_character_names)

        self.statusBar().showMessage("Suggestions de liens appliquées. Vérifiez les éléments cochés.") # Message mis à jour
        self._update_token_estimation_and_prompt_display() # Mettre à jour l'estimation après avoir coché

    def _display_details_in_tree(self, data_item):
        """Affiche les détails d'un item dans le QTreeView.

        Args:
            data_item (dict or list): Les données à afficher.
        """
        self.details_tree_model.clear()
        # Pas besoin de remettre les header labels, ils sont sur le modèle.
        root_item = self.details_tree_model.invisibleRootItem()
        if data_item:
            populate_tree_view(self.details_tree_model, root_item, data_item)
            self.details_tree_view.expandToDepth(0)
            # Ajuster la largeur des colonnes après le peuplement
            self.details_tree_view.header().resizeSections(QHeaderView.ResizeToContents) # ou QHeaderView.Interactive pour manuel
            # Peut-être donner plus de place à la valeur si elle est longue
            self.details_tree_view.header().setSectionResizeMode(0, QHeaderView.ResizeToContents) 
            self.details_tree_view.header().setSectionResizeMode(1, QHeaderView.Stretch)
        else:
            # Afficher un message si data_item est None après une tentative de sélection
            no_details_item = QStandardItem("Aucun détail à afficher pour la sélection.")
            no_details_item.setEditable(False)
            self.details_tree_model.invisibleRootItem().appendRow(no_details_item)

    def on_explorer_list_item_clicked(self, list_widget_clicked: QListWidget, category_data_list, category_name_singular, item_widget: QListWidgetItem, name_key_priority=None):
        """Gère le clic sur un élément dans l'une des listes de gauche (explorateur).

        Affiche les détails de l'élément cliqué dans le QTreeView central.

        Args:
            list_widget_clicked: La QListWidget d'où provient le clic.
            category_data_list: La liste complète des données pour cette catégorie.
            category_name_singular: Le nom singulier de la catégorie (ex: "Personnage").
            item_widget: L'item QListWidgetItem qui a été cliqué.
            name_key_priority (list, optional): Liste des clés à utiliser pour trouver
                                            le nom de l'item dans les données. 
                                            Défaut à ["Nom"].
        """
        if name_key_priority is None:
            name_key_priority = ["Nom"]
        
        self.active_list_widget_for_details = list_widget_clicked
        
        if not item_widget: 
            self.details_tree_model.clear() 
            self.statusBar().showMessage("Aucun élément cliqué.")
            return
            
        selected_display_name = item_widget.text()
        selected_item_details = None
        
        if category_data_list: 
            for item_data in category_data_list:
                if isinstance(item_data, dict):
                    current_item_name = None
                    for key in name_key_priority: 
                        if key in item_data:
                            val = item_data[key]
                            if isinstance(val, (str, int, float)):
                               current_item_name = str(val)
                               break 
                    if current_item_name == selected_display_name:
                        selected_item_details = item_data
                        break
        
        self.statusBar().showMessage(f"Détails pour {category_name_singular}: {selected_display_name}")
        if selected_item_details:
            self._display_details_in_tree(selected_item_details)
        else:
            self.details_tree_model.clear()
            error_item_key = QStandardItem(f"Détails non trouvés pour : {selected_display_name}")
            error_item_key.setEditable(False)
            error_item_val = QStandardItem("")
            error_item_val.setEditable(False)
            self.details_tree_model.invisibleRootItem().appendRow([error_item_key, error_item_val])
            self.statusBar().showMessage(f"Détails non trouvés pour {category_name_singular}: {selected_display_name}") 

    def _on_list_item_check_changed(self, item: QListWidgetItem):
        """Appelé lorsque l'état coché d'un élément de liste change.

        Déclenche une mise à jour de l'estimation des tokens et du prompt.

        Args:
            item: L'item QListWidgetItem dont l'état a changé.
        """
        self._update_token_estimation_and_prompt_display()

    def _save_ui_settings(self):
        """Sauvegarde l'état actuel de l'interface utilisateur dans un fichier JSON.
        
        Ceci inclut la géométrie de la fenêtre, la taille des panneaux du splitter,
        les sélections dans les combobox, les états des cases à cocher, le texte
        des instructions utilisateur et les éléments cochés dans les listes.
        """
        settings = {
            "window_geometry": self.saveGeometry().data().hex(), # PySide6 utilise .data().hex()
            "splitter_sizes": self.splitter.sizes() if hasattr(self, 'splitter') else [], # Vérifier si splitter existe
            "char_a_combo_text": self.char_a_combo.currentText(),
            "char_b_combo_text": self.char_b_combo.currentText(),
            "region_combo_gen_text": self.region_combo_gen.currentText(),
            "sub_location_combo_gen_text": self.sub_location_combo_gen.currentText(),
            "k_variants_input_text": self.k_variants_input.text(),
            "max_tokens_input_text": self.max_tokens_input.text(),
            "include_dialogue_type_checkbox_checked": self.include_dialogue_type_checkbox.isChecked(),
            "restore_selections_action_checked": self.restore_selections_action.isChecked(), # Utiliser l'action du menu
            "user_instruction_input_text": self.user_instruction_input.toPlainText(),
            "checked_characters": self._get_checked_items(self.character_list),
            "checked_locations": self._get_checked_items(self.location_list),
            "checked_items": self._get_checked_items(self.item_list),
            "checked_species": self._get_checked_items(self.species_list),
            "checked_communities": self._get_checked_items(self.communities_list),
            "checked_dialogue_examples": self._get_checked_items(self.dialogues_list),
        }
        try:
            with open(UI_SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4)
            logger.info(f"Paramètres UI sauvegardés dans {UI_SETTINGS_FILE}")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des paramètres UI: {e}")

    def _load_ui_settings(self):
        """Charge et applique l'état de l'interface utilisateur depuis un fichier JSON.
        
        Restaure la géométrie de la fenêtre, les sélections et les états des contrôles
        si l'option "Restaurer les sélections au démarrage" est activée.
        """
        if not UI_SETTINGS_FILE.exists():
            logger.info("Aucun fichier de paramètres UI trouvé. Utilisation des valeurs par défaut.")
            # S'assurer que l'action de menu a un état par défaut si le fichier n'existe pas
            if hasattr(self, 'restore_selections_action'): # Vérifier si l'action existe déjà
                 self.restore_selections_action.setChecked(True)
            return

        try:
            with open(UI_SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except Exception as e:
            logger.error(f"Erreur lors du chargement des paramètres UI: {e}")
            return

        # Mettre à jour l'état de l'action du menu
        self.restore_selections_action.setChecked(settings.get("restore_selections_action_checked", True))

        if not self.restore_selections_action.isChecked():
            logger.info("Restauration des sélections désactivée via le menu.")
            if "window_geometry" in settings: self.restoreGeometry(bytes.fromhex(settings["window_geometry"])) 
            if "splitter_sizes" in settings and hasattr(self, 'splitter') and settings["splitter_sizes"]: self.splitter.setSizes(settings["splitter_sizes"]) # Vérifier si splitter existe et sizes non vide
            return

        if "window_geometry" in settings: self.restoreGeometry(bytes.fromhex(settings["window_geometry"])) 
        if "splitter_sizes" in settings and hasattr(self, 'splitter') and settings["splitter_sizes"]: self.splitter.setSizes(settings["splitter_sizes"]) # Idem
        
        def set_combo_text(combo: QComboBox, text: str):
            """Sélectionne l'item `text` dans le QComboBox `combo`.

            La recherche se fait d'abord en correspondance exacte. Si aucun item
            n'est trouvé, une recherche insensible à la casse et aux espaces
            superflus est tentée.
            """
            if not text:
                return
            index = combo.findText(text)
            if index == -1:
                # Tentative de correspondance moins stricte (insensible à la casse et aux espaces)
                normalized_target = "".join(text.split()).lower()
                for i in range(combo.count()):
                    candidate = combo.itemText(i)
                    if "".join(candidate.split()).lower() == normalized_target:
                        index = i
                        break
            if index != -1:
                combo.setCurrentIndex(index)
            else:
                logger.warning(f"Item '{text}' non trouvé dans {combo.objectName()} lors du chargement.")

        set_combo_text(self.char_a_combo, settings.get("char_a_combo_text", "-- Aucun --"))
        set_combo_text(self.char_b_combo, settings.get("char_b_combo_text", "-- Aucun --"))
        
        # Restaurer la région d'abord
        saved_region = settings.get("region_combo_gen_text", "-- Toutes --")
        set_combo_text(self.region_combo_gen, saved_region)
        
        # Forcer le traitement des événements pour que on_region_changed_for_sub_locations s'exécute
        # et peuple sub_location_combo_gen en fonction de la région restaurée.
        QApplication.processEvents()
        
        # Maintenant, tenter de restaurer le sous-lieu directement.
        saved_sub_location = settings.get("sub_location_combo_gen_text", "-- Aucun --")
        set_combo_text(self.sub_location_combo_gen, saved_sub_location)

        self.k_variants_input.setText(settings.get("k_variants_input_text", "1"))
        self.max_tokens_input.setText(settings.get("max_tokens_input_text", "4"))
        self.include_dialogue_type_checkbox.setChecked(settings.get("include_dialogue_type_checkbox_checked", True))
        self.user_instruction_input.setPlainText(settings.get("user_instruction_input_text", ""))

        def set_checked_items(list_widget: QListWidget, checked_texts: list[str]):
            # Déconnecter temporairement
            try: list_widget.itemChanged.disconnect() 
            except RuntimeError: pass
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                if item.text() in checked_texts:
                    item.setCheckState(Qt.Checked)
                else:
                    item.setCheckState(Qt.Unchecked)
            # Reconnecter
            list_widget.itemChanged.connect(self._on_list_item_check_changed)

        set_checked_items(self.character_list, settings.get("checked_characters", []))
        set_checked_items(self.location_list, settings.get("checked_locations", []))
        set_checked_items(self.item_list, settings.get("checked_items", []))
        set_checked_items(self.species_list, settings.get("checked_species", []))
        set_checked_items(self.communities_list, settings.get("checked_communities", []))
        set_checked_items(self.dialogues_list, settings.get("checked_dialogue_examples", []))

        logger.info(f"Paramètres UI chargés depuis {UI_SETTINGS_FILE}")
        self._update_token_estimation_and_prompt_display() # Mettre à jour le contexte après chargement

    def closeEvent(self, event):
        """Surcharge closeEvent pour sauvegarder les paramètres avant de quitter.

        Args:
            event: L'événement de fermeture.
        """
        self._save_ui_settings()
        super().closeEvent(event)

# Pour les tests, si vous exécutez main_window.py directement (nécessite quelques ajustements)
if __name__ == '__main__':
    # Configuration du logging de base
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[logging.StreamHandler()]) # Afficher les logs dans la console

    logger.info("Démarrage de l'application DialogueGenerator...")
    app = QApplication(sys.argv)

    # Styles pour un look un peu plus moderne (optionnel)
    # app.setStyle("Fusion")
    # dark_palette = QPalette()
    # dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    # ... (configuration complète du thème sombre si désiré)
    # app.setPalette(dark_palette)

    logger.info("Initialisation du ContextBuilder...")
    context_builder = ContextBuilder() # Le ContextBuilder charge sa propre config maintenant
    context_builder.load_gdd_files()
    logger.info("ContextBuilder initialisé.")

    logger.info("Initialisation de la MainWindow...")
    window = MainWindow(context_builder)
    window.show()
    logger.info("MainWindow affichée.")

    sys.exit(app.exec()) 