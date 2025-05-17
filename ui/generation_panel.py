from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QGridLayout, 
                               QLabel, QComboBox, QTextEdit, QPushButton, 
                               QTabWidget, QLineEdit, QCheckBox, QHBoxLayout, QApplication, QSizePolicy)
from PySide6.QtCore import Qt, Signal, Slot
import logging # Added for logging
import asyncio # Added for asynchronous tasks
from typing import Optional, Callable, Any # Added Any

# --- Ajouts pour YarnRenderer ---
from pathlib import Path
import uuid
# --- Fin Ajouts ---

# New service import
try:
    from ..services.linked_selector import LinkedSelectorService
    from ..services.yarn_renderer import YarnRenderer # Ajout YarnRenderer
except ImportError:
    # Support exécution directe
    import sys, os, pathlib
    current_dir = pathlib.Path(__file__).resolve().parent.parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    from DialogueGenerator.services.linked_selector import LinkedSelectorService
    from DialogueGenerator.services.yarn_renderer import YarnRenderer # Ajout YarnRenderer

logger = logging.getLogger(__name__) # Added logger

class GenerationPanel(QWidget):
    """Manages UI elements for dialogue generation parameters, context selection, and results display.

    This panel includes:
    - Scene selection (Character A, Character B, Scene Region, Sub-Location comboboxes).
    - A button to suggest GDD elements linked to the selected characters.
    - Generation parameters (number of variants, max tokens for context, include dialogue type checkbox).
    - A text input for user-specific instructions/prompt for the LLM.
    - A button to trigger dialogue generation.
    - A label to display estimated token counts (context and total prompt).
    - A tab widget to display the full LLM prompt and the generated dialogue variants.

    It interacts with MainWindow to get overall context selections, to trigger prompt/token
    updates, and to use the status bar. It uses ContextBuilder, PromptEngine, and LLMClient
    for its core generation logic when the user clicks "Generate Dialogue".
    It also handles saving and loading its own UI state (combo selections, input values).
    """
    settings_changed = Signal() # Define the new signal
    generation_requested: Signal = Signal(str, int, str, str, str, str, list) # prompt, k, model, char_a_name, char_b_name, scene_name, selected_items_for_context
    update_token_estimation_signal: Signal = Signal()

    def __init__(self, context_builder, prompt_engine, llm_client, main_window_ref, parent=None):
        """Initializes the GenerationPanel.

        Args:
            context_builder: Instance of ContextBuilder to access GDD data (e.g., character names,
                             location names, linked elements) and to build context strings.
            prompt_engine: Instance of PromptEngine to construct the final prompt for the LLM.
            llm_client: Instance of an LLMClient (e.g., OpenAIClient or DummyLLMClient) to generate text.
            main_window_ref: Reference to the MainWindow, used for accessing shared functionalities
                             like the status bar, or methods like _get_current_context_selections and
                             _update_token_estimation_and_prompt_display.
            parent: The parent widget.
        """
        super().__init__(parent)
        
        self.context_builder = context_builder
        self.prompt_engine = prompt_engine
        self.llm_client = llm_client
        self.main_window_ref = main_window_ref

        # Service pour la logique de liens
        self.linked_selector = LinkedSelectorService(self.context_builder)
        # Service pour le rendu Yarn
        self.yarn_renderer = YarnRenderer()

        # Main layout for this panel widget itself
        panel_layout = QVBoxLayout(self) # self is the QWidget

        # --- Start of content from old _create_right_generation_panel ---
        self.generation_parameters_groupbox = QGroupBox("Generation Parameters")
        generation_params_layout = QVBoxLayout()

        # Scene character and location selection
        context_selection_layout = QGridLayout()
        self.character_a_label = QLabel("Character A:")
        self.character_a_combo = QComboBox()
        self.character_a_combo.setObjectName("character_a_combo")
        self.character_a_combo.setMaxVisibleItems(15)
        
        self.character_b_label = QLabel("Character B (Interlocutor):")
        self.character_b_combo = QComboBox()
        self.character_b_combo.setObjectName("character_b_combo")
        self.character_b_combo.setMaxVisibleItems(15)
        
        self.scene_region_label = QLabel("Scene Region:")
        self.scene_region_combo = QComboBox()
        self.scene_region_combo.setObjectName("scene_region_combo")
        self.scene_region_combo.setMaxVisibleItems(15)

        self.scene_sub_location_label = QLabel("Sub-Location (optional):")
        self.scene_sub_location_combo = QComboBox()
        self.scene_sub_location_combo.setObjectName("scene_sub_location_combo")
        self.scene_sub_location_combo.setMaxVisibleItems(15)

        self.suggest_linked_elements_button = QPushButton("Select Linked Elements")
        self.suggest_linked_elements_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.suggest_linked_elements_button.setToolTip(
            "Automatically select elements in the left panel that are linked to Character A, Character B, and the Scene."
        )
        self.suggest_linked_elements_button.clicked.connect(self._on_select_linked_elements_clicked)

        self.unlink_everything_button = QPushButton("Unlink Everything")
        self.unlink_everything_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.unlink_everything_button.setToolTip(
            "Uncheck all items in the left selection panel."
        )
        self.unlink_everything_button.clicked.connect(self._on_unlink_everything_clicked)

        self.unlink_unrelated_button = QPushButton("Unlink Unrelated Elements")
        self.unlink_unrelated_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.unlink_unrelated_button.setToolTip(
            "Uncheck items in the left panel that are not related to the current Character A, B, or Scene."
        )
        self.unlink_unrelated_button.clicked.connect(self._on_unlink_unrelated_clicked)

        context_selection_layout.addWidget(self.character_a_label, 0, 0)
        context_selection_layout.addWidget(self.character_a_combo, 0, 1)
        context_selection_layout.addWidget(self.character_b_label, 1, 0)
        context_selection_layout.addWidget(self.character_b_combo, 1, 1)
        context_selection_layout.addWidget(self.scene_region_label, 2, 0)
        context_selection_layout.addWidget(self.scene_region_combo, 2, 1)
        context_selection_layout.addWidget(self.scene_sub_location_label, 3, 0)
        context_selection_layout.addWidget(self.scene_sub_location_combo, 3, 1)
        context_selection_layout.addWidget(self.suggest_linked_elements_button)
        context_selection_layout.addWidget(self.unlink_everything_button)
        context_selection_layout.addWidget(self.unlink_unrelated_button)
        
        generation_params_layout.addLayout(context_selection_layout)
        generation_params_layout.addSpacing(10)

        # Number of variants k
        variant_count_layout = QVBoxLayout() # Changed to QVBoxLayout for consistency if more items added later
        variant_count_sub_layout = QHBoxLayout()
        variant_count_sub_layout.addWidget(QLabel("Number of variants (k):"))
        self.variant_count_input = QLineEdit("1")
        self.variant_count_input.setFixedWidth(50)
        variant_count_sub_layout.addWidget(self.variant_count_input)
        variant_count_sub_layout.addStretch() 
        variant_count_layout.addLayout(variant_count_sub_layout)
        generation_params_layout.addLayout(variant_count_layout)

        # Max Tokens for generation
        max_tokens_layout = QVBoxLayout() # Changed to QVBoxLayout
        max_tokens_sub_layout = QHBoxLayout()
        max_tokens_sub_layout.addWidget(QLabel("Max K Tokens:"))
        self.max_tokens_input = QLineEdit("4")
        self.max_tokens_input.setPlaceholderText("e.g., 4 (for 4000)")
        self.max_tokens_input.setFixedWidth(60)
        max_tokens_sub_layout.addWidget(self.max_tokens_input)
        max_tokens_sub_layout.addStretch()
        max_tokens_layout.addLayout(max_tokens_sub_layout)
        generation_params_layout.addLayout(max_tokens_layout)

        self.include_dialogue_type_checkbox = QCheckBox("Include 'Dialogue Type' from character")
        self.include_dialogue_type_checkbox.setChecked(True) 
        generation_params_layout.addWidget(self.include_dialogue_type_checkbox)
        generation_params_layout.addSpacing(5)

        generation_params_layout.addWidget(QLabel("Specific instructions for the scene / User prompt:"))
        self.user_instruction_input = QTextEdit("E.g.: Character A must convince Character B to reveal a secret. Tone: mysterious. Include a reference to artifact X.")
        self.user_instruction_input.setFixedHeight(100)
        generation_params_layout.addWidget(self.user_instruction_input)
        
        generate_action_layout = QHBoxLayout()
        self.generate_dialogue_button = QPushButton("Generate Dialogue")
        self.estimated_token_count_label = QLabel("Est. words: 0")
        self.estimated_token_count_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        generate_action_layout.addWidget(self.generate_dialogue_button)
        generate_action_layout.addStretch()
        generate_action_layout.addWidget(self.estimated_token_count_label)
        generation_params_layout.addLayout(generate_action_layout)
        
        self.generation_parameters_groupbox.setLayout(generation_params_layout)
        
        self.variant_display_tabs = QTabWidget()
        
        # Add groupbox and tabs to the panel's main layout
        panel_layout.addWidget(self.generation_parameters_groupbox)
        panel_layout.addWidget(self.variant_display_tabs)
        
        self.setMinimumWidth(500)
        # --- End of content from old _create_right_generation_panel ---

        # Connect button clicks here as they are direct user actions
        # and don't immediately trigger the problematic initialization loop.
        self.generate_dialogue_button.clicked.connect(self._on_generate_dialogue_button_clicked_local)
        
        # Signals that trigger token updates and initial population are deferred to finalize_ui_setup

    def finalize_ui_setup(self):
        """Finalizes the UI setup by connecting signals and populating comboboxes.
        
        This method is called after the GenerationPanel is fully initialized and
        its reference is available to the MainWindow. It connects internal UI element
        signals (e.g., combobox changes, text input changes) to internal slots
        that trigger token updates (via MainWindow) and emit `settings_changed` for auto-saving.
        It also populates the character and scene comboboxes with initial data from ContextBuilder.
        """
        logger.info("GenerationPanel: Finalizing UI setup...")
        # Connect signals that might trigger updates through MainWindow via _trigger_token_update
        # AND trigger a settings save using lambda to call emit() without arguments
        self.character_a_combo.currentIndexChanged.connect(self._trigger_token_update)
        self.character_a_combo.currentIndexChanged.connect(lambda: self.settings_changed.emit())

        self.character_b_combo.currentIndexChanged.connect(self._trigger_token_update)
        self.character_b_combo.currentIndexChanged.connect(lambda: self.settings_changed.emit())

        self.scene_region_combo.currentIndexChanged.connect(self._on_scene_region_changed) 
        self.scene_region_combo.currentIndexChanged.connect(self._trigger_token_update) 
        self.scene_region_combo.currentIndexChanged.connect(lambda: self.settings_changed.emit())

        self.scene_sub_location_combo.currentIndexChanged.connect(self._trigger_token_update)
        self.scene_sub_location_combo.currentIndexChanged.connect(lambda: self.settings_changed.emit())

        self.include_dialogue_type_checkbox.stateChanged.connect(self._trigger_token_update)
        self.include_dialogue_type_checkbox.stateChanged.connect(lambda: self.settings_changed.emit())

        self.user_instruction_input.textChanged.connect(self._trigger_token_update)
        self.user_instruction_input.textChanged.connect(lambda: self.settings_changed.emit())
        
        self.variant_count_input.editingFinished.connect(lambda: self.settings_changed.emit())
        self.max_tokens_input.editingFinished.connect(lambda: self.settings_changed.emit())

        self.populate_scene_combos()
        logger.info("GenerationPanel: Finalizing UI setup complete.")

    def _trigger_token_update(self):
        """Helper method to request a prompt/token update from MainWindow and then update local UI display.
        Calls `_request_and_update_prompt_estimation` to handle the logic.
        """
        self._request_and_update_prompt_estimation() # Call the new method

    def _request_and_update_prompt_estimation(self):
        """Requests prompt and token information from MainWindow and updates GenerationPanel's UI.
        
        Calls `MainWindow._update_token_estimation_and_prompt_display()` to get the
        context string, token counts, and the full estimated prompt. Updates the
        `estimated_token_count_label` and the prompt preview tab with this information.
        Handles cases where the information might not be available (e.g., errors during prompt building).
        """
        if hasattr(self.main_window_ref, '_update_token_estimation_and_prompt_display'):
            context_string, context_token_count, estimated_full_prompt_text, estimated_total_token_count = \
                self.main_window_ref._update_token_estimation_and_prompt_display()

            if estimated_full_prompt_text is not None:
                self.estimated_token_count_label.setText(f"Context: {context_token_count} / Total Prompt (est.): {estimated_total_token_count} tokens")
                
                # Lire la limite de tokens pour le contexte définie par l'utilisateur
                user_defined_max_k_tokens_str = self.max_tokens_input.text().replace("k", "").replace("K", "").strip()
                try:
                    user_defined_max_context_tokens = int(float(user_defined_max_k_tokens_str) * 1000)
                    if user_defined_max_context_tokens <= 0:
                        user_defined_max_context_tokens = 4000 # Default si invalide
                except ValueError:
                    user_defined_max_context_tokens = 4000 # Default si non numérique

                # Seuils basés sur la limite définie par l'utilisateur pour le CONTEXTE
                CONTEXT_TOKEN_THRESHOLD_WARNING_PERCENT = 0.80 # 80% de la limite utilisateur
                CONTEXT_TOKEN_THRESHOLD_CRITICAL_PERCENT = 0.95 # 95% de la limite utilisateur

                # TOKEN_THRESHOLD_WARNING_PERCENT = 0.75 # Anciennes valeurs normales pour le prompt total
                # TOKEN_THRESHOLD_CRITICAL_PERCENT = 0.90 # Anciennes valeurs normales pour le prompt total

                CONTEXT_TOKEN_THRESHOLD_WARNING = user_defined_max_context_tokens * CONTEXT_TOKEN_THRESHOLD_WARNING_PERCENT
                CONTEXT_TOKEN_THRESHOLD_CRITICAL = user_defined_max_context_tokens * CONTEXT_TOKEN_THRESHOLD_CRITICAL_PERCENT

                # logger.debug(f"User max context tokens: {user_defined_max_context_tokens}, Context Warning at: {CONTEXT_TOKEN_THRESHOLD_WARNING}, Context Critical at: {CONTEXT_TOKEN_THRESHOLD_CRITICAL}, Current context: {context_token_count}")

                # La couleur est basée sur le dépassement du contexte par rapport à la limite utilisateur
                if context_token_count > CONTEXT_TOKEN_THRESHOLD_CRITICAL:
                    self.estimated_token_count_label.setStyleSheet("color: red; font-weight: bold;")
                elif context_token_count > CONTEXT_TOKEN_THRESHOLD_WARNING:
                    self.estimated_token_count_label.setStyleSheet("color: orange; font-weight: bold;")
                else:
                    self.estimated_token_count_label.setStyleSheet("") # Default color

                preview_tab_title_text = "Full Prompt (Est.)"
                # Ensure the prompt preview tab exists (usually the first one)
                if self.variant_display_tabs.count() == 0:
                    prompt_preview_text_edit = QTextEdit()
                    prompt_preview_text_edit.setReadOnly(True)
                    self.variant_display_tabs.addTab(prompt_preview_text_edit, preview_tab_title_text)
                else:
                    # Assume the first tab is for the prompt preview if it exists
                    self.variant_display_tabs.setTabText(0, preview_tab_title_text)
                
                preview_widget_item = self.variant_display_tabs.widget(0)
                if isinstance(preview_widget_item, QTextEdit):
                    preview_widget_item.setPlainText(estimated_full_prompt_text)
                else: # If first tab is not a QTextEdit (e.g., after generation error), create it.
                    # This case might need more robust handling if tabs are dynamically added/removed for errors elsewhere.
                    for i in range(self.variant_display_tabs.count()): # Remove existing non-prompt tabs if any
                        self.variant_display_tabs.removeTab(0)
                    prompt_preview_text_edit = QTextEdit()
                    prompt_preview_text_edit.setReadOnly(True)
                    prompt_preview_text_edit.setPlainText(estimated_full_prompt_text)
                    self.variant_display_tabs.insertTab(0, prompt_preview_text_edit, preview_tab_title_text)
                    self.variant_display_tabs.setCurrentIndex(0)

            else:
                # Handle case where prompt generation failed in MainWindow
                self.estimated_token_count_label.setText("Context: N/A / Total Prompt (est.): N/A tokens")
                preview_widget_item = self.variant_display_tabs.widget(0)
                if isinstance(preview_widget_item, QTextEdit):
                    preview_widget_item.setPlainText("Error: Could not generate prompt estimation.")
                elif self.variant_display_tabs.count() == 0: # If no tab exists
                    error_preview_text_edit = QTextEdit("Error: Could not generate prompt estimation.")
                    error_preview_text_edit.setReadOnly(True)
                    self.variant_display_tabs.addTab(error_preview_text_edit, "Prompt Error")

        else:
            logger.warning("MainWindow reference does not have _update_token_estimation_and_prompt_display method.")
            self.estimated_token_count_label.setText("Error fetching prompt info.")

    def populate_scene_combos(self):
        """Populates the character and location comboboxes for scene selection.
        
        Retrieves lists of character names and region names from the ContextBuilder
        and populates the `character_a_combo`, `character_b_combo`, and `scene_region_combo`.
        Also triggers an initial update of the `scene_sub_location_combo` based on the
        default or current selection in `scene_region_combo`.
        """
        if not self.context_builder:
            logger.warning("ContextBuilder not available in GenerationPanel for populating combos.")
            return

        char_names_list = ["-- None --"] + (self.context_builder.get_characters_names() or [])
        self.character_a_combo.clear()
        self.character_a_combo.addItems(char_names_list)
        self.character_b_combo.clear()
        self.character_b_combo.addItems(char_names_list)

        region_names_list = ["-- All --"] + (self.context_builder.get_regions() or [])
        self.scene_region_combo.clear()
        self.scene_region_combo.addItems(region_names_list)
        self._on_scene_region_changed() # Call to populate sub-locations initially

    def _on_scene_region_changed(self):
        """Updates the sub-location combobox when the selected scene region changes.
        
        Clears the `scene_sub_location_combo` and repopulates it with sub-locations
        relevant to the newly selected region, by querying the ContextBuilder.
        Signals are temporarily disconnected during repopulation to avoid premature updates.
        """
        if not self.context_builder: return
        
        selected_region_name = self.scene_region_combo.currentText()
        # --- Temporarily disconnect to avoid triggering token update during clear/repopulation ---
        try:
            self.scene_sub_location_combo.currentIndexChanged.disconnect(self._trigger_token_update)
        except RuntimeError:
            pass # Already disconnected or never connected

        self.scene_sub_location_combo.clear()
        self.scene_sub_location_combo.addItem("-- None --")

        if selected_region_name and selected_region_name != "-- All --":
            sub_location_names = self.context_builder.get_sub_locations(selected_region_name)
            if sub_location_names:
                self.scene_sub_location_combo.addItems(sub_location_names)
        
        # --- Reconnect ---
        self.scene_sub_location_combo.currentIndexChanged.connect(self._trigger_token_update)
        # Manually trigger an update if needed, as the change might not have propagated through a signal yet.
        # However, the population of sub_location_combo itself shouldn't change the *total* token count
        # until a sub-location is *selected*. The primary trigger for token update after region change
        # is already connected to scene_region_combo.currentIndexChanged.

    # Nouvelle méthode pour gérer la validation d'une variante
    @Slot(int)
    def _on_validate_variant_clicked(self, variant_index: int):
        logger.info(f"Validation demandée pour la variante {variant_index}")
        if not (0 <= variant_index < self.variant_display_tabs.count() -1 ): # -1 car le premier onglet est le prompt
            logger.error(f"Index de variante invalide : {variant_index}. Nombre d'onglets de variante : {self.variant_display_tabs.count() -1}")
            self.main_window_ref.statusBar().showMessage(f"Erreur : Index de variante invalide {variant_index}", 5000)
            return

        # L'onglet de variante réel est à variant_index + 1 (car le premier onglet est le prompt)
        actual_tab_index = variant_index + 1
        variant_tab_widget = self.variant_display_tabs.widget(actual_tab_index)
        if not variant_tab_widget:
            logger.error(f"Impossible de récupérer le widget de l'onglet pour l'index de variante {variant_index} (onglet actuel {actual_tab_index})")
            self.main_window_ref.statusBar().showMessage("Erreur : Onglet de variante non trouvé.", 5000)
            return

        # Le QTextEdit est le premier enfant du layout du widget de l'onglet
        try:
            dialogue_text_edit = variant_tab_widget.layout().itemAt(0).widget()
            if not isinstance(dialogue_text_edit, QTextEdit):
                raise AttributeError("Le premier widget n'est pas un QTextEdit")
            dialogue_text = dialogue_text_edit.toPlainText()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du texte de la variante {variant_index}: {e}")
            self.main_window_ref.statusBar().showMessage("Erreur : Impossible de lire le texte de la variante.", 5000)
            return

        char_a_name = self.character_a_combo.currentText()
        char_b_name = self.character_b_combo.currentText()
        scene_region_name = self.scene_region_combo.currentText()
        scene_sub_location_name = self.scene_sub_location_combo.currentText()

        # Création d'un titre pour le noeud Yarn. S'assurer qu'il est compatible avec les noms de fichiers.
        base_title = f"{char_a_name.replace(' ', '_')}__{char_b_name.replace(' ', '_')}__{scene_region_name.replace(' ', '_')}__{variant_index + 1}"
        # Nettoyage pour nom de fichier (simpliste, pourrait être amélioré)
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
        node_title = "".join(c if c in safe_chars else '_' for c in base_title)
        node_title = node_title[:100] + f"_{uuid.uuid4().hex[:6]}" # Limiter la longueur et assurer l'unicité
        
        metadata = {
            "title": node_title,
            "character_a": char_a_name,
            "character_b": char_b_name,
            "scene_region": scene_region_name,
        }
        if scene_sub_location_name and scene_sub_location_name.lower() != "any":
            metadata["scene_sub_location"] = scene_sub_location_name
        
        try:
            yarn_content = self.yarn_renderer.render(dialogue_text, metadata)
            output_dir = Path("Assets/Dialogues/generated")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Nom de fichier basé sur le titre nettoyé
            file_name = f"{node_title}.yarn"
            output_file_path = output_dir / file_name
            
            output_file_path.write_text(yarn_content, encoding="utf-8")
            logger.info(f"Fichier Yarn généré : {output_file_path}")
            self.main_window_ref.statusBar().showMessage(f"Fichier {file_name} enregistré avec succès !", 5000)

        except Exception as e:
            logger.error(f"Erreur lors du rendu ou de l'écriture du fichier Yarn : {e}")
            self.main_window_ref.statusBar().showMessage(f"Erreur lors de la génération du fichier .yarn : {e}", 7000)

    async def _on_generate_dialogue_button_clicked_local(self):
        """Handles the 'Generate Dialogue' button click locally.

        This local version directly calls the LLM client and updates the UI.
        It prepares the prompt, sends it to the LLM, and displays the results
        in the tab widget. This replaces the old signal emission to MainWindow.
        """
        logger.info("'Generate Dialogue' button clicked. Processing locally.")
        self.main_window_ref.statusBar().showMessage("Génération en cours...", 3000)

        # 1. Récupérer les sélections de contexte de GenerationPanel lui-même
        # (Personnages, Scène, etc.)
        char_a_name = self.character_a_combo.currentText()
        char_b_name = self.character_b_combo.currentText()
        scene_name = self.scene_region_combo.currentText()
        # sub_location_name = self.scene_sub_location_combo.currentText() # Peut-être utile plus tard

        # 2. Récupérer les éléments cochés dans LeftSelectionPanel via MainWindow
        # Assurez-vous que cette méthode existe et retourne ce qui est attendu par build_context_string
        # Doit retourner une liste de tuples (category_key, item_name)
        selected_items_for_context = []
        if hasattr(self.main_window_ref, 'get_all_checked_items_for_context'):
            selected_items_for_context = self.main_window_ref.get_all_checked_items_for_context()
            logger.debug(f"Éléments sélectionnés pour le contexte (depuis MainWindow): {selected_items_for_context}")
        else:
            logger.warning("Méthode 'get_all_checked_items_for_context' non trouvée sur MainWindow.")

        user_instructions = self.user_instruction_input.toPlainText()
        include_dialogue_type = self.include_dialogue_type_checkbox.isChecked()
        k_variants = int(self.variant_count_input.text())
        max_context_k_tokens_str = self.max_tokens_input.text().replace("k", "").replace("K", "").strip()
        try:
            max_context_tokens = int(float(max_context_k_tokens_str) * 1000)
        except ValueError:
            max_context_tokens = 4000  # Default to 4000 if input is invalid
            logger.warning(f"Valeur max_tokens invalide: '{max_context_k_tokens_str}'. Utilisation de 4000 par défaut.")
            self.main_window_ref.statusBar().showMessage(f"Max tokens invalide, utilisation de {max_context_tokens} par défaut.", 3000)

        # Construire le contexte avec ContextBuilder
        context_data = self.context_builder.build_context_for_llm(
            character_a_name=char_a_name,
            character_b_name=char_b_name,
            scene_name=scene_name,
            include_dialogue_type=include_dialogue_type,
            selected_gdd_items=selected_items_for_context, # Transmettre les éléments sélectionnés
            max_tokens=max_context_tokens
        )
        context_string = context_data["context_string"]
        # context_token_count = context_data["token_count"]

        # Préparer le prompt avec PromptEngine
        full_prompt = self.prompt_engine.create_prompt(
            context_string,
            user_instructions,
            char_a_name,
            char_b_name,
            scene_name
        )

        # Mettre à jour l'estimation des tokens (si la méthode existe dans MainWindow)
        self._request_and_update_prompt_estimation()

        self.variant_display_tabs.clear()  # Clear previous results

        # Add a tab for the full prompt
        prompt_display_tab = QTextEdit()
        prompt_display_tab.setPlainText(full_prompt)
        prompt_display_tab.setReadOnly(True)
        self.variant_display_tabs.addTab(prompt_display_tab, "LLM Prompt")

        # Désactiver le bouton de génération pendant le traitement
        self.generate_dialogue_button.setEnabled(False)
        QApplication.processEvents() # Force UI update

        try:
            loop = asyncio.get_event_loop()
            variants = await self.llm_client.generate_variants(full_prompt, k_variants)
            
            if variants:
                for i, variant_text in enumerate(variants):
                    # Crée un widget conteneur pour chaque onglet de variante
                    variant_tab_content_widget = QWidget()
                    tab_layout = QVBoxLayout(variant_tab_content_widget)
                    tab_layout.setContentsMargins(5, 5, 5, 5) # Marges réduites
                    tab_layout.setSpacing(5) # Espacement réduit

                    text_edit = QTextEdit()
                    text_edit.setPlainText(variant_text.strip())
                    # text_edit.setReadOnly(True) # Peut-être permettre l'édition avant validation
                    tab_layout.addWidget(text_edit)

                    validate_button = QPushButton(f"Valider et Enregistrer Variante {i+1} en .yarn")
                    # Utilisation de lambda pour passer l'index de la variante (i) au slot.
                    # L'index i ici correspond à l'index dans la liste `variants`,
                    # qui sera utilisé comme `variant_index` dans le slot.
                    validate_button.clicked.connect(lambda checked=False, idx=i: self._on_validate_variant_clicked(idx))
                    tab_layout.addWidget(validate_button)
                    
                    self.variant_display_tabs.addTab(variant_tab_content_widget, f"Variant {i + 1}")
                self.main_window_ref.statusBar().showMessage(f"{len(variants)} variantes générées.", 5000)
            else:
                self.main_window_ref.statusBar().showMessage("Aucune variante n'a été générée.", 5000)
                # Add a tab indicating no variants
                no_variant_tab = QTextEdit("Aucune variante n'a été générée par le LLM.")
                no_variant_tab.setReadOnly(True)
                self.variant_display_tabs.addTab(no_variant_tab, "No Variants")

        except Exception as e:
            logger.error(f"Erreur pendant la génération des dialogues : {e}", exc_info=True)
            self.main_window_ref.statusBar().showMessage(f"Erreur de génération: {e}", 7000)
            error_tab = QTextEdit(f"Erreur lors de la génération des dialogues :\n\n{str(e)}\n\nConsultez les logs pour plus de détails.")
            error_tab.setReadOnly(True)
            self.variant_display_tabs.addTab(error_tab, "Error")
        finally:
            # Réactiver le bouton de génération
            self.generate_dialogue_button.setEnabled(True)

    def _on_select_linked_elements_clicked(self) -> None:
        """Auto-selects elements in LeftSelectionPanel based on Character A, B, and Scene.
        Uses the main_window_ref to access LeftSelectionPanel.
        """
        char_a_name = self.character_a_combo.currentText()
        char_b_name = self.character_b_combo.currentText()
        scene_region = self.scene_region_combo.currentText()
        sub_location = self.scene_sub_location_combo.currentText()
        
        # Utilisation du nouveau service
        try:
            elements_to_select = self.linked_selector.get_elements_to_select(
                character_a=char_a_name,
                character_b=char_b_name,
                scene_region=scene_region,
                sub_location=sub_location,
            )

            logger.info("Suggesting to select in LeftPanel: %s", list(elements_to_select))
            if hasattr(self.main_window_ref, 'left_panel') and hasattr(self.main_window_ref.left_panel, 'set_checked_items_by_name'):
                self.main_window_ref.left_panel.set_checked_items_by_name(list(elements_to_select))
        except Exception as e:
            logger.exception("Error during selecting linked elements", exc_info=True)
            if hasattr(self.main_window_ref, 'statusBar'):
                self.main_window_ref.statusBar().showMessage(f"Error selecting linked elements: {e}", 5000)

    def _on_unlink_everything_clicked(self):
        """Unchecks all items in the LeftSelectionPanel."""
        logger.info("GenerationPanel: Unlink Everything button clicked.")
        if hasattr(self.main_window_ref, 'left_panel') and hasattr(self.main_window_ref.left_panel, 'uncheck_all_items'):
            # self.main_window_ref.left_panel.clear_and_set_selected_items([], True) # Clear selections too
            self.main_window_ref.left_panel.uncheck_all_items() # Correction ici
            # self.main_window_ref.left_panel.context_selection_changed.emit() # Assurer la mise à jour du contexte
        else:
            logger.error("LeftPanel or uncheck_all_items method not found on main_window_ref for unlinking everything.")

    def _on_unlink_unrelated_clicked(self) -> None:
        """
        Handles the click of the 'Unlink Unrelated Elements' button.
        Unchecks items in the left panel that are currently checked AND are not
        directly related to Character A, B, or Scene (including their linked elements).
        It does NOT check any currently unchecked items, even if they are related.
        """
        if not (self.main_window_ref and self.main_window_ref.left_panel):
            logger.warning("Left panel not available for unlinking unrelated elements.")
            return

        # 1. Get currently checked items from LeftSelectionPanel
        currently_checked_items: set[str] = set(self.main_window_ref.left_panel.get_all_selected_item_names())
        if not currently_checked_items:
            logger.info("Unlink Unrelated: No items currently checked. Nothing to do.")
            # self.main_window_ref.statusBar().showMessage("No items are currently selected to unlink from.", 3000)
            return # No need to proceed if nothing is checked

        # 2. Identify all "essential" or "directly related" elements
        char_a_name: str = self.character_a_combo.currentText()
        char_b_name: str = self.character_b_combo.currentText()
        scene_name: str = self.scene_region_combo.currentText()
        sub_location_name: str = self.scene_sub_location_combo.currentText()

        # 3. Determine items to keep checked: intersection of currently checked and directly related
        items_to_keep_checked = self.linked_selector.compute_items_to_keep_checked(
            currently_checked=currently_checked_items,
            character_a=char_a_name,
            character_b=char_b_name,
            scene_region=scene_name,
            sub_location=sub_location_name,
        )

        # 4. Signal LeftSelectionPanel to update its state
        # set_checked_items_by_name will uncheck anything not in items_to_keep_checked
        # and ensure items_to_keep_checked are checked.
        if set(items_to_keep_checked) != currently_checked_items: # Only update if there's a change
            self.main_window_ref.left_panel.set_checked_items_by_name(items_to_keep_checked)
            # Pas besoin de clear_and_set_selected_items ici, car set_checked_items_by_name gère déjà le signal context_selection_changed
            # self.main_window_ref.statusBar().showMessage(f"{len(currently_checked_items) - len(items_to_keep_checked)} unrelated item(s) unlinked.", 3000)
        # else:
            # self.main_window_ref.statusBar().showMessage("No unrelated items to unlink among currently selected.", 3000)

    # Methods for MainWindow to get/set UI states of this panel (for _save/_load_ui_settings)
    def get_settings(self) -> dict:
        """Returns a dictionary containing the current UI settings of this panel.
        
        This includes the current text/state of comboboxes, line edits, checkboxes,
        and the text edit for user instructions. Used by MainWindow for saving UI state.
        """
        return {
            "character_a_combo_text": self.character_a_combo.currentText(),
            "character_b_combo_text": self.character_b_combo.currentText(),
            "scene_region_combo_text": self.scene_region_combo.currentText(),
            "scene_sub_location_combo_text": self.scene_sub_location_combo.currentText(),
            "variant_count_input_text": self.variant_count_input.text(),
            "max_tokens_input_text": self.max_tokens_input.text(),
            "include_dialogue_type_checkbox_checked": self.include_dialogue_type_checkbox.isChecked(),
            "user_instruction_input_text": self.user_instruction_input.toPlainText(),
        }

    def load_settings(self, settings: dict):
        """Loads UI settings into this panel's widgets from a dictionary.
        
        Sets the state of comboboxes, line edits, checkboxes, and the user instruction
        text edit based on the provided settings dictionary. Handles repopulating
        the sub-location combo based on the loaded region. Blocks signals during
        the loading process to prevent unwanted updates and restores them afterwards.
        Triggers a final token update once all settings are applied.
        Used by MainWindow when restoring UI state.
        """
        logger.info(f"GenerationPanel: Attempting to load settings...")
        
        combos_to_block = [
            self.character_a_combo, self.character_b_combo, 
            self.scene_region_combo, self.scene_sub_location_combo
        ]
        other_widgets_to_block_signals = {
            self.include_dialogue_type_checkbox: self.include_dialogue_type_checkbox.blockSignals,
            self.user_instruction_input: self.user_instruction_input.blockSignals
        }
        original_signal_states = {}

        for combo in combos_to_block:
            original_signal_states[combo.objectName()] = combo.signalsBlocked()
            combo.blockSignals(True)
        for widget, block_method in other_widgets_to_block_signals.items():
            original_signal_states[widget.objectName()] = widget.signalsBlocked()
            block_method(True)

        # --- Load settings ---
        self._set_combo_text_robust(self.character_a_combo, settings.get("character_a_combo_text", "-- None --"))
        self._set_combo_text_robust(self.character_b_combo, settings.get("character_b_combo_text", "-- None --"))
        
        saved_region_text = settings.get("scene_region_combo_text", "-- All --")
        self._set_combo_text_robust(self.scene_region_combo, saved_region_text)
        
        self._on_scene_region_changed()

        saved_sub_location_text = settings.get("scene_sub_location_combo_text", "-- None --")
        self._set_combo_text_robust(self.scene_sub_location_combo, saved_sub_location_text)

        variant_count = settings.get("variant_count_input_text", "1")
        self.variant_count_input.setText(variant_count)

        max_tokens = settings.get("max_tokens_input_text", "4")
        self.max_tokens_input.setText(max_tokens)

        include_dialogue_type = settings.get("include_dialogue_type_checkbox_checked", True)
        self.include_dialogue_type_checkbox.setChecked(include_dialogue_type)

        user_instruction = settings.get("user_instruction_input_text", "")
        self.user_instruction_input.setPlainText(user_instruction)

        # --- Restore signal states ---
        for combo in combos_to_block:
            if not original_signal_states.get(combo.objectName(), False):
                combo.blockSignals(False)
        for widget, block_method in other_widgets_to_block_signals.items():
             if not original_signal_states.get(widget.objectName(), False):
                block_method(False)
        
        logger.info("GenerationPanel: Settings loading complete. Triggering final token update.")
        self._trigger_token_update()

    def _set_combo_text_robust(self, combo_box: QComboBox, text_to_set: str):
        """Helper to set QComboBox current item by text, robustly finding the item.

        Tries an exact match first. If not found, attempts a case-insensitive and
        space-insensitive match. Logs a warning if the item still cannot be found.
        
        Args:
            combo_box (QComboBox): The combobox to modify.
            text_to_set (str): The text of the item to select.
        """
        combo_name = combo_box.objectName() if combo_box.objectName() else "Unnamed ComboBox"
        if not text_to_set:
            return
        
        idx = combo_box.findText(text_to_set)
        if idx == -1:
            normalized_target = "".join(text_to_set.split()).lower()
            for i in range(combo_box.count()):
                candidate = combo_box.itemText(i)
                normalized_candidate = "".join(candidate.split()).lower()
                if normalized_candidate == normalized_target:
                    idx = i
                    break
        if idx != -1:
            combo_box.setCurrentIndex(idx)
        else:
            logger.warning(f"GenerationPanel._set_combo_text_robust: Item '{text_to_set}' not found in {combo_name}. Current items: {[combo_box.itemText(i) for i in range(combo_box.count())]}") 