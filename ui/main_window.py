# DialogueGenerator/ui/main_window.py
import json
import asyncio # Ajout pour exécuter les tâches asynchrones
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QComboBox, QTextEdit, QSplitter, 
                               QListWidget, QTreeView, QAbstractItemView, QLineEdit,
                               QGroupBox, QHeaderView, QPushButton, QTabWidget, QApplication)
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt

# Importer les nouveaux modules
from prompt_engine import PromptEngine
from llm_client import DummyLLMClient

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
    def __init__(self, context_builder=None):
        super().__init__()
        self.context_builder = context_builder
        self.prompt_engine = PromptEngine() # Initialiser le PromptEngine
        self.llm_client = DummyLLMClient()  # Initialiser le LLMClient (Dummy pour l'instant)

        self.setWindowTitle("Générateur de Dialogues IA - Context Builder")
        self.setGeometry(100, 100, 1800, 900) # Encore un peu plus large pour les onglets

        self.setup_ui()
        if self.context_builder:
            self.load_initial_data()

    def setup_ui(self):
        """Configure l'interface utilisateur de la fenêtre principale."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # --- Panneau de sélection à gauche (multiple listes) ---
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
            return list_widget, filter_edit, label # Retourner aussi le label

        self.character_list, self.character_filter, self.character_label = create_list_section("Personnages:", "character")
        self.character_list.itemSelectionChanged.connect(lambda: self.on_list_item_selected(self.character_list, self.context_builder.characters if self.context_builder else [], "Personnage"))

        self.location_list, self.location_filter, self.location_label = create_list_section("Lieux:", "location")
        self.location_list.itemSelectionChanged.connect(lambda: self.on_list_item_selected(self.location_list, self.context_builder.locations if self.context_builder else [], "Lieu"))
        
        self.item_list, self.item_filter, self.item_label = create_list_section("Objets:", "item")
        self.item_list.itemSelectionChanged.connect(lambda: self.on_list_item_selected(self.item_list, self.context_builder.items if self.context_builder else [], "Objet"))

        self.species_list, self.species_filter, self.species_label = create_list_section("Espèces:", "species")
        self.species_list.itemSelectionChanged.connect(lambda: self.on_list_item_selected(self.species_list, self.context_builder.species if self.context_builder else [], "Espèce"))

        self.communities_list, self.communities_filter, self.communities_label = create_list_section("Communautés:", "communities")
        self.communities_list.itemSelectionChanged.connect(lambda: self.on_list_item_selected(self.communities_list, self.context_builder.communities if self.context_builder else [], "Communauté"))
        
        self.dialogues_list, self.dialogues_filter, self.dialogues_label = create_list_section("Exemples Dialogues:", "dialogues")
        self.dialogues_list.itemSelectionChanged.connect(lambda: self.on_list_item_selected(self.dialogues_list, self.context_builder.dialogues_examples if self.context_builder else [], "Dialogue Exemple", name_key_priority=["Nom", "Titre", "ID"]))
        
        left_container_widget = QWidget()
        left_container_widget.setLayout(left_panel_layout)
        left_container_widget.setMinimumWidth(300)
        left_container_widget.setMaximumWidth(400) # Un peu moins large pour donner de la place

        # --- Panneau central pour les détails (TreeView) ---
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

        # --- Panneau de droite pour les paramètres de génération et l'affichage des variantes ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Section Paramètres de Génération
        self.generation_params_group = QGroupBox("Paramètres de Génération")
        generation_params_layout = QVBoxLayout()
        # TODO: Ajouter des contrôles plus spécifiques (k, modèle, température)
        generation_params_layout.addWidget(QLabel("Nombre de variantes (k):"))
        self.k_variants_input = QLineEdit("3") # Défaut à 3
        self.k_variants_input.setFixedWidth(50)
        generation_params_layout.addWidget(self.k_variants_input)
        generation_params_layout.addWidget(QLabel("Instruction pour le LLM:"))
        self.user_instruction_input = QTextEdit("Décrire une interaction tendue entre [Personnage A] et [Personnage B] à propos de [Sujet].")
        self.user_instruction_input.setFixedHeight(100)
        self.generate_button = QPushButton("Générer le Dialogue")
        self.generate_button.clicked.connect(self.on_generate_button_clicked)
        generation_params_layout.addWidget(self.user_instruction_input)
        generation_params_layout.addWidget(self.generate_button)
        self.generation_params_group.setLayout(generation_params_layout)
        
        # Section pour afficher les variantes générées
        self.variant_tabs = QTabWidget()
        # On ajoutera des onglets ici dynamiquement

        right_layout.addWidget(self.generation_params_group)
        right_layout.addWidget(self.variant_tabs)
        right_panel.setMinimumWidth(450)

        # Utilisation d'un QSplitter principal pour séparer listes, détails et paramètres
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(left_container_widget) 
        main_splitter.addWidget(details_panel)
        main_splitter.addWidget(right_panel) # Nouveau panneau de droite
        
        main_splitter.setStretchFactor(0, 1) # Panel listes
        main_splitter.setStretchFactor(1, 2) # Panel détails TreeView
        main_splitter.setStretchFactor(2, 2) # Panel génération + variantes

        main_layout.addWidget(main_splitter)
        
        self.statusBar().showMessage("Prêt.")
        self.active_list_widget = None 

    def _get_selected_context_summary(self) -> str:
        """Construit un résumé simple du contexte actuellement sélectionné."""
        summary_parts = []
        if self.character_list.currentItem():
            summary_parts.append(f"Personnage Principal: {self.character_list.currentItem().text()}")
        # TODO: Permettre la sélection de plusieurs personnages (secondaires, etc.)
        if self.location_list.currentItem():
            summary_parts.append(f"Lieu de la scène: {self.location_list.currentItem().text()}")
        
        # On pourrait ajouter d'autres éléments ici (quête active, objets importants, etc.)
        # Pour l'instant, on reste simple.
        if not summary_parts:
            return "Contexte non spécifié (veuillez sélectionner au moins un personnage et/ou un lieu)."
        return "\n".join(summary_parts)

    def on_generate_button_clicked(self):
        self.statusBar().showMessage("Génération en cours...")
        self.variant_tabs.clear() # Effacer les anciens onglets

        user_instruction = self.user_instruction_input.toPlainText()
        if not user_instruction.strip():
            self.statusBar().showMessage("Veuillez entrer une instruction pour le LLM.")
            return

        context_summary = self._get_selected_context_summary()
        # Pour l'instant, on ne gère pas les generation_params au-delà de k
        
        try:
            k_value = int(self.k_variants_input.text())
            if k_value <= 0:
                self.statusBar().showMessage("Le nombre de variantes (k) doit être positif.")
                return
        except ValueError:
            self.statusBar().showMessage("Le nombre de variantes (k) doit être un entier.")
            return

        current_prompt = self.prompt_engine.build_prompt(
            context_summary=context_summary, 
            user_specific_goal=user_instruction
        )

        self.statusBar().showMessage(f"Génération de {k_value} variantes avec DummyLLMClient...")
        QApplication.processEvents() # Permet de rafraîchir l'UI avant l'appel bloquant

        try:
            # Exécution de la tâche asynchrone de manière bloquante pour l'instant
            # C'est acceptable avec DummyLLMClient qui est rapide.
            # Pour un vrai LLM, il faudra une meilleure gestion (asyncqt, QThread).
            variants = asyncio.run(self.llm_client.generate_variants(current_prompt, k_value))
            
            if variants:
                for i, variant_text in enumerate(variants):
                    tab_content = QTextEdit()
                    tab_content.setPlainText(variant_text)
                    tab_content.setReadOnly(True) # Les variantes ne sont pas éditables ici
                    self.variant_tabs.addTab(tab_content, f"Variante {i+1}")
                self.statusBar().showMessage(f"{len(variants)} variantes générées avec succès.")
            else:
                self.statusBar().showMessage("Aucune variante n'a été générée.")

        except Exception as e:
            self.statusBar().showMessage(f"Erreur lors de la génération: {e}")
            # Afficher l'erreur dans un onglet pourrait être utile aussi
            error_tab = QTextEdit()
            error_tab.setPlainText(f"Une erreur est survenue:\n{type(e).__name__}: {e}\n\nPrompt utilisé:\n{current_prompt}")
            self.variant_tabs.addTab(error_tab, "Erreur")
            print(f"Erreur lors de la génération : {e}") # Log console également

    def filter_list_widget(self, text, list_widget, label_widget, original_label_text):
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

    def _populate_list_widget(self, list_widget, data_list, name_extractor_func, label_widget, original_label_text):
        list_widget.clear()
        names = []
        if self.context_builder: # S'assurer que context_builder est initialisé
            names = name_extractor_func()
        
        if names:
            valid_names = [str(name) for name in names if name is not None]
            list_widget.addItems(valid_names)
            label_widget.setText(f"{original_label_text} ({len(valid_names)}/{len(valid_names)})")
        else:
            list_widget.addItem("Aucun élément.")
            label_widget.setText(f"{original_label_text} (0/0)")

    def load_initial_data(self):
        if not self.context_builder: 
            self.statusBar().showMessage("Erreur: ContextBuilder non initialisé.")
            return

        self._populate_list_widget(self.character_list, self.context_builder.characters, self.context_builder.get_characters_names, self.character_label, "Personnages:")
        self._populate_list_widget(self.location_list, self.context_builder.locations, self.context_builder.get_locations_names, self.location_label, "Lieux:")
        self._populate_list_widget(self.item_list, self.context_builder.items, self.context_builder.get_items_names, self.item_label, "Objets:")
        self._populate_list_widget(self.species_list, self.context_builder.species, self.context_builder.get_species_names, self.species_label, "Espèces:")
        self._populate_list_widget(self.communities_list, self.context_builder.communities, self.context_builder.get_communities_names, self.communities_label, "Communautés:")
        self._populate_list_widget(self.dialogues_list, self.context_builder.dialogues_examples, self.context_builder.get_dialogue_examples_titles, self.dialogues_label, "Exemples Dialogues:")
        
        loaded_counts = f"{self.character_list.count()}P, {self.location_list.count()}L, {self.item_list.count()}O, {self.species_list.count()}E, {self.communities_list.count()}C, {self.dialogues_list.count()}D."
        self.statusBar().showMessage(f"Données chargées: {loaded_counts} Prêt.")

    def _display_details_in_tree(self, data_item):
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

    def on_list_item_selected(self, list_widget, category_data_list, category_name_singular, name_key_priority=["Nom"]):
        if self.active_list_widget and self.active_list_widget != list_widget:
            # Tenter de bloquer les signaux temporairement pour éviter les appels récursifs/multiples
            # lors de la désélection programmatique.
            try:
                self.active_list_widget.blockSignals(True)
                self.active_list_widget.clearSelection()
            finally:
                if self.active_list_widget: # Vérifier s'il existe toujours
                     self.active_list_widget.blockSignals(False)
        
        self.active_list_widget = list_widget
        
        selected_items = list_widget.selectedItems()
        if not selected_items: 
            self.details_tree_model.clear() # Vider les détails si rien n'est sélectionné
            self.statusBar().showMessage("Aucun élément sélectionné.")
            return
            
        selected_display_name = selected_items[0].text()
        selected_item_details = None
        
        if category_data_list: # S'assurer que la liste de données de catégorie n'est pas None
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
        
        self.statusBar().showMessage(f"{category_name_singular} sélectionné: {selected_display_name}")
        if selected_item_details:
            self._display_details_in_tree(selected_item_details)
        else:
            self.details_tree_model.clear()
            error_item_key = QStandardItem(f"Détails non trouvés pour : {selected_display_name}")
            error_item_key.setEditable(False)
            self.details_tree_model.invisibleRootItem().appendRow(error_item_key)
            self.statusBar().showMessage(f"Détails non trouvés pour {category_name_singular}: {selected_display_name}") 