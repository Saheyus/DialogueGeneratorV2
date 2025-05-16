# DialogueGenerator/ui/main_window.py
import json
import asyncio # Ajout pour exécuter les tâches asynchrones
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QComboBox, QTextEdit, QSplitter, 
                               QListWidget, QListWidgetItem, QTreeView, QAbstractItemView, QLineEdit,
                               QGroupBox, QHeaderView, QPushButton, QTabWidget, QApplication, QGridLayout, QCheckBox)
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt

# Importer les nouveaux modules
from prompt_engine import PromptEngine
from llm_client import OpenAIClient, DummyLLMClient

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
        self.prompt_engine = PromptEngine()
        self.MAX_WORDS_PER_FIELD_TEST_MODE = 30 # Nouvelle constante pour le mode test par champ
        self.TEST_MODE_PRIORITY_KEYS = [ # Clés à conserver (et tronquer) en mode test
            "Nom", "Titre", "ID", "Alias", "Archétype littéraire", "Type", 
            "Résumé de la fiche", "Description", "Ambiance", "Objectifs",
            "Apparence", "Traits de caractère", "Motivations", 
            "Background", "Contexte", "Relations", 
            "Arcs Narratifs", "Envie vs Besoin", "Quêtes annexes", "Enjeux",
            "Fonction dans le Lore", "Secrets", "Notes de design", "Tags"
        ]
        
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
        self.location_label_gen = QLabel("Lieu de la Scène:")
        self.location_combo_gen = QComboBox()
        self.location_combo_gen.setMaxVisibleItems(15) # Augmentation du nombre d'items visibles
        self.location_combo_gen.currentIndexChanged.connect(self._update_token_estimation_and_prompt_display)

        context_select_layout.addWidget(self.char_a_label, 0, 0)
        context_select_layout.addWidget(self.char_a_combo, 0, 1)
        context_select_layout.addWidget(self.char_b_label, 1, 0)
        context_select_layout.addWidget(self.char_b_combo, 1, 1)
        context_select_layout.addWidget(self.location_label_gen, 2, 0)
        context_select_layout.addWidget(self.location_combo_gen, 2, 1)
        
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

        # Case à cocher pour le mode Test
        self.test_mode_checkbox = QCheckBox("Mode Test (contexte limité)")
        self.test_mode_checkbox.stateChanged.connect(self._update_token_estimation_and_prompt_display)
        generation_params_layout.addWidget(self.test_mode_checkbox)
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
        self.active_list_widget_for_details = None

    def _get_simplified_details_for_test_mode(self, details_dict: dict) -> dict:
        """ Simplifie et tronque les détails d'un item pour le mode test. """
        if not isinstance(details_dict, dict):
            return details_dict # Retourne tel quel si ce n'est pas un dictionnaire
        
        simplified = {}
        for key, value in details_dict.items():
            if key in self.TEST_MODE_PRIORITY_KEYS:
                if isinstance(value, str):
                    words = value.split()
                    if len(words) > self.MAX_WORDS_PER_FIELD_TEST_MODE:
                        simplified[key] = " ".join(words[:self.MAX_WORDS_PER_FIELD_TEST_MODE]) + " [...]"
                    else:
                        simplified[key] = value
                elif isinstance(value, list):
                    # Pour les listes, on pourrait prendre les N premiers éléments ou simplifier chaque élément
                    # Pour l'instant, on les garde telles quelles mais on pourrait les tronquer aussi.
                    simplified[key] = value # Garder les listes (ex: de tags) telles quelles pour l'instant
                else:
                    simplified[key] = value # Garder les autres types tels quels (nombres, booléens)
            # Les clés non prioritaires sont ignorées en mode test
        
        if not simplified and "Nom" in details_dict: # Au cas où aucune clé prioritaire n'est trouvée mais qu'il y a un Nom
            simplified["Nom"] = details_dict["Nom"]
            simplified["_test_mode_info"] = "Aucune clé prioritaire trouvée, seul le Nom est inclus."
        elif not simplified:
            simplified["_test_mode_info"] = "Dictionnaire original vide ou sans clés prioritaires."

        return simplified

    def _get_selected_context_summary(self) -> str:
        """Construit un résumé simple du contexte actuellement sélectionné."""
        summary_parts = ["--- CONTEXTE PRINCIPAL ---"]
        
        char_a_name = self.char_a_combo.currentText()
        char_b_name = self.char_b_combo.currentText()
        location_name = self.location_combo_gen.currentText()

        if self.context_builder:
            if char_a_name and char_a_name != "<Aucun>" and char_a_name != "<Aucun personnage chargé>":
                details_a = self.context_builder.get_character_details_by_name(char_a_name)
                summary_parts.append(f"Personnage A (Acteur Principal): {char_a_name}")
                if details_a:
                    processed_details_a = self._get_simplified_details_for_test_mode(details_a) if self.test_mode_checkbox.isChecked() else details_a
                    summary_parts.append(f"  Détails Personnage A: {json.dumps(processed_details_a, ensure_ascii=False, indent=2)}")
            else:
                summary_parts.append("Personnage A: <Non sélectionné>")

            if char_b_name and char_b_name != "<Aucun>" and char_b_name != "<Aucun personnage chargé>":
                details_b = self.context_builder.get_character_details_by_name(char_b_name)
                summary_parts.append(f"Personnage B (Interlocuteur): {char_b_name}")
                if details_b:
                    processed_details_b = self._get_simplified_details_for_test_mode(details_b) if self.test_mode_checkbox.isChecked() else details_b
                    summary_parts.append(f"  Détails Personnage B: {json.dumps(processed_details_b, ensure_ascii=False, indent=2)}")
            else:
                summary_parts.append("Personnage B: <Non sélectionné>")
            
            if location_name and location_name != "<Aucun>" and location_name != "<Aucun lieu chargé>":
                details_loc = self.context_builder.get_location_details_by_name(location_name)
                summary_parts.append(f"Lieu de la scène: {location_name}")
                if details_loc:
                    processed_details_loc = self._get_simplified_details_for_test_mode(details_loc) if self.test_mode_checkbox.isChecked() else details_loc
                    summary_parts.append(f"  Détails Lieu: {json.dumps(processed_details_loc, ensure_ascii=False, indent=2)}")
            else:
                summary_parts.append("Lieu de la scène: <Non sélectionné>")

            if char_a_name == char_b_name and char_a_name != "<Aucun>" and char_a_name != "<Aucun personnage chargé>":
                summary_parts.append("NOTE: Personnage A et Personnage B sont identiques.")
        
        additional_context_section_parts = ["\n--- CONTEXTE ADDITIONNEL (Éléments cochés) ---"]
        found_additional = False

        def add_checked_details_from_list(list_widget: QListWidget, category_name: str, detail_fetch_func, name_keys=None):
            nonlocal found_additional
            checked_items_details_json = []
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                if item.checkState() == Qt.Checked:
                    item_name = item.text()
                    details = None
                    if self.context_builder:
                        if name_keys: # Pour les cas comme les dialogues qui peuvent avoir plusieurs clés pour le titre
                            details = detail_fetch_func(item_name, name_keys=name_keys) 
                        else:
                            details = detail_fetch_func(item_name)
                    
                    if details:
                        # Pour éviter de surcharger, on peut ajouter une version simplifiée ou juste une confirmation
                        # Pour l'instant, ajoutons le JSON complet
                        processed_details = self._get_simplified_details_for_test_mode(details) if self.test_mode_checkbox.isChecked() else details
                        checked_items_details_json.append(json.dumps(processed_details, ensure_ascii=False, indent=2))
                    else:
                        checked_items_details_json.append(f'"{item_name}" (détails non trouvés ou erreur)')
            
            if checked_items_details_json:
                additional_context_section_parts.append(f"{category_name} notables:")
                additional_context_section_parts.extend(checked_items_details_json)
                found_additional = True

        if self.context_builder:
            add_checked_details_from_list(self.character_list, "Autres Personnages", self.context_builder.get_character_details_by_name)
            add_checked_details_from_list(self.location_list, "Autres Lieux", self.context_builder.get_location_details_by_name)
            add_checked_details_from_list(self.item_list, "Objets", self.context_builder.get_item_details_by_name)
            add_checked_details_from_list(self.species_list, "Espèces", self.context_builder.get_species_details_by_name)
            add_checked_details_from_list(self.communities_list, "Communautés", self.context_builder.get_community_details_by_name)
            # Pour les dialogues, la fonction de récupération est get_dialogue_example_details_by_title
            # et elle gère déjà les multiples clés possibles via _get_element_details_by_name
            add_checked_details_from_list(self.dialogues_list, "Exemples Dialogues", self.context_builder.get_dialogue_example_details_by_title)

        if found_additional:
            summary_parts.extend(additional_context_section_parts)
        
        full_context_text = "\n".join(summary_parts)

        return full_context_text

    def _update_token_estimation_and_prompt_display(self):
        """Met à jour l'estimation du nombre de tokens et affiche le prompt formaté."""
        context_summary = self._get_selected_context_summary()
        user_instruction = self.user_instruction_input.toPlainText()
        
        # Générer le prompt complet pour l'estimation
        # Le PromptEngine s'occupe du formatage final incluant le system prompt.
        current_prompt, word_count = self.prompt_engine.build_prompt(
            context_summary=context_summary,
            user_specific_goal=user_instruction
        )
        self.token_count_label.setText(f"Estim. mots: {word_count}")

        # Optionnel: afficher le prompt complet quelque part si utile pour le debug
        # Par exemple, dans un onglet "Prompt Complet" ou une infobulle.
        # Pour l'instant, on se contente de mettre à jour le compteur.

    def on_generate_button_clicked(self):
        self.statusBar().showMessage("Génération en cours...")
        self.variant_tabs.clear()

        user_instruction = self.user_instruction_input.toPlainText()
        if not user_instruction.strip():
            self.statusBar().showMessage("Veuillez entrer une instruction pour le LLM.")
            return

        context_summary = self._get_selected_context_summary()
        
        try:
            k_value = int(self.k_variants_input.text())
            if k_value <= 0:
                self.statusBar().showMessage("Le nombre de variantes (k) doit être positif.")
                return
        except ValueError:
            self.statusBar().showMessage("Le nombre de variantes (k) doit être un entier.")
            return

        current_prompt, word_count = self.prompt_engine.build_prompt(
            context_summary=context_summary, 
            user_specific_goal=user_instruction
        )
        self.token_count_label.setText(f"Estim. mots: {word_count}") # Mise à jour du label

        self.statusBar().showMessage(f"Génération de {k_value} variantes avec {type(self.llm_client).__name__}... (Prompt: ~{word_count} mots)")
        QApplication.processEvents()

        try:
            variants = asyncio.run(self.llm_client.generate_variants(current_prompt, k_value))
            
            if variants:
                for i, variant_text in enumerate(variants):
                    tab_content = QTextEdit()
                    tab_content.setPlainText(variant_text)
                    tab_content.setReadOnly(True) 
                    self.variant_tabs.addTab(tab_content, f"Variante {i+1}")
                self.statusBar().showMessage(f"{len(variants)} variantes générées avec succès. Prompt: ~{word_count} mots.")
            else:
                self.statusBar().showMessage("Aucune variante n'a été générée.")

        except Exception as e:
            self.statusBar().showMessage(f"Erreur lors de la génération: {e}")
            error_tab = QTextEdit()
            error_tab.setPlainText(f"Une erreur est survenue:\n{type(e).__name__}: {e}\n\nPrompt utilisé (~{word_count} mots):\n{current_prompt}")
            self.variant_tabs.addTab(error_tab, "Erreur")
            print(f"Erreur lors de la génération : {e}")

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

    def _populate_list_widget(self, list_widget: QListWidget, data_list, name_extractor_func, label_widget, original_label_text):
        list_widget.clear()
        names = []
        if self.context_builder:
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
        if not self.context_builder: 
            self.statusBar().showMessage("Erreur: ContextBuilder non initialisé.")
            return

        # Populate character selectors in the generation panel
        character_names = self.context_builder.get_characters_names()
        if character_names:
            valid_character_names = [str(name) for name in character_names if name is not None]
            self.char_a_combo.clear()
            self.char_a_combo.addItems(["<Aucun>"] + valid_character_names)
            self.char_b_combo.clear()
            self.char_b_combo.addItems(["<Aucun>"] + valid_character_names)
        else:
            self.char_a_combo.addItem("<Aucun personnage chargé>")
            self.char_b_combo.addItem("<Aucun personnage chargé>")

        # Populate location selector in the generation panel
        location_names = self.context_builder.get_locations_names()
        if location_names:
            valid_location_names = [str(name) for name in location_names if name is not None]
            self.location_combo_gen.clear()
            self.location_combo_gen.addItems(["<Aucun>"] + valid_location_names)
        else:
            self.location_combo_gen.addItem("<Aucun lieu chargé>")

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

    def on_explorer_list_item_clicked(self, list_widget_clicked: QListWidget, category_data_list, category_name_singular, item_widget: QListWidgetItem, name_key_priority=None):
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
        """Appelé lorsque l'état coché d'un élément de liste change."""
        self._update_token_estimation_and_prompt_display()

# Pour les tests, si vous exécutez main_window.py directement (nécessite quelques ajustements)
if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QApplication
    # Simuler un context_builder pour le test
    class MockContextBuilder:
        def __init__(self):
            self.characters = [{"Nom": "Perso A"}, {"Nom": "Perso B"}]
            self.locations = [{"Nom": "Lieu X"}, {"Nom": "Lieu Y"}]
            self.items = [{"Nom": "Objet 1"}]
            self.species = [{"Nom": "Espece Alpha"}]
            self.communities = [{"Nom": "Communaute Z"}]
            self.dialogues_examples = [{"Titre": "Exemple Dialogue 1"}]

        def get_characters_names(self): return [c["Nom"] for c in self.characters]
        def get_locations_names(self): return [l["Nom"] for l in self.locations]
        def get_items_names(self): return [i["Nom"] for i in self.items]
        def get_species_names(self): return [s["Nom"] for s in self.species]
        def get_communities_names(self): return [c["Nom"] for c in self.communities]
        def get_dialogue_examples_titles(self): return [d["Titre"] for d in self.dialogues_examples]
        def load_data(self, data_path): pass


    app = QApplication(sys.argv)
    # Créer une instance de MockContextBuilder pour les tests
    mock_builder = MockContextBuilder()
    
    window = MainWindow(context_builder=mock_builder)
    window.show()
    sys.exit(app.exec()) 