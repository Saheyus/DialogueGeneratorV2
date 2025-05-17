from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QGridLayout, 
                               QLabel, QComboBox, QTextEdit, QPushButton, 
                               QTabWidget, QLineEdit, QCheckBox, QHBoxLayout, QApplication, QSizePolicy)
from PySide6.QtCore import Qt, Signal, Slot
import logging # Added for logging
import asyncio # Added for asynchronous tasks
from typing import Optional, Callable, Any # Added Any

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
        self.main_window_ref = main_window_ref # To access statusBar or call methods on MainWindow if needed

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

    # Placeholder methods for logic to be moved from MainWindow
    def _on_generate_dialogue_button_clicked_local(self):
        """Handles the click event of the 'Generate Dialogue' button.
        
        This is the core dialogue generation logic for this panel. It:
        1. Gets current context selections from MainWindow.
        2. Gets user instructions and generation parameters (k, max_tokens) from its own UI elements.
        3. Builds the context string using ContextBuilder.
        4. Builds the final LLM prompt using PromptEngine.
        5. Updates its UI to show the final prompt and token counts.
        6. Calls the LLMClient to generate the specified number of dialogue variants.
        7. Displays the generated variants in new tabs or an error message if generation fails.
        Uses MainWindow's status bar to provide feedback to the user during the process.
        """
        self.main_window_ref.statusBar().showMessage("Generation in progress...")
        
        while self.variant_display_tabs.count() > 0:
            self.variant_display_tabs.removeTab(0)

        if not self.context_builder:
            self.main_window_ref.statusBar().showMessage("ContextBuilder not initialized.")
            return

        user_instruction_text = self.user_instruction_input.toPlainText()
        if not user_instruction_text.strip():
            self.main_window_ref.statusBar().showMessage("Please enter an instruction for the LLM.")
            # self.main_window_ref._update_token_estimation_and_prompt_display() # MainWindow should handle this
            self._trigger_token_update() # Ask MainWindow to update token estimation
            return
        
        # selected_elements = self.main_window_ref._get_current_context_selections() # Get from MainWindow
        # MainWindow needs to provide this, or GenerationPanel needs LeftPanel ref too
        # For now, let's assume main_window_ref has a method to provide it
        if not hasattr(self.main_window_ref, '_get_current_context_selections'):
            logger.error("MainWindow reference does not have _get_current_context_selections method.")
            self.main_window_ref.statusBar().showMessage("Error: Cannot get context selections.")
            return
        selected_elements = self.main_window_ref._get_current_context_selections()


        include_dialogue_type_flag = self.include_dialogue_type_checkbox.isChecked()
        
        try:
            max_k_tokens_string = self.max_tokens_input.text().replace("k", "").replace("K", "").strip()
            max_context_tokens = int(float(max_k_tokens_string) * 1000) if max_k_tokens_string else 4000
            if max_context_tokens <= 0: max_context_tokens = 4000 
        except ValueError:
            max_context_tokens = 4000 
        
        context_summary_string = self.context_builder.build_context(
            selected_elements,
            user_instruction_text, 
            max_tokens=max_context_tokens, 
            include_dialogue_type=include_dialogue_type_flag
        )

        generation_parameters = {} 
        current_llm_prompt, total_prompt_tokens = self.prompt_engine.build_prompt(
            context_summary=context_summary_string,
            user_specific_goal=user_instruction_text,
            generation_params=generation_parameters
        )
        
        final_context_tokens = self.context_builder._count_tokens(context_summary_string)
        self.estimated_token_count_label.setText(f"Context: {final_context_tokens} / LLM Prompt: {total_prompt_tokens} tokens")

        prompt_display_text_edit = QTextEdit()
        prompt_display_text_edit.setReadOnly(True)
        prompt_display_text_edit.setPlainText(current_llm_prompt)
        self.variant_display_tabs.insertTab(0, prompt_display_text_edit, "Final Prompt (for LLM)")
        self.variant_display_tabs.setCurrentIndex(0)

        try:
            variant_count = int(self.variant_count_input.text())
            if variant_count <= 0:
                self.main_window_ref.statusBar().showMessage("Number of variants (k) must be positive.")
                return
        except ValueError:
            self.main_window_ref.statusBar().showMessage("Number of variants (k) must be an integer.")
            return

        self.main_window_ref.statusBar().showMessage(f"Generating {variant_count} variants with {type(self.llm_client).__name__}... (Prompt: {total_prompt_tokens} tokens)")
        QApplication.processEvents() 

        try:
            generated_variants = asyncio.run(self.llm_client.generate_variants(current_llm_prompt, variant_count))
            
            if generated_variants:
                for i, variant_text_content in enumerate(generated_variants):
                    variant_tab_content_widget = QTextEdit()
                    variant_tab_content_widget.setPlainText(variant_text_content)
                    variant_tab_content_widget.setReadOnly(True) 
                    self.variant_display_tabs.addTab(variant_tab_content_widget, f"Variant {i+1}")
                self.main_window_ref.statusBar().showMessage(f"{len(generated_variants)} variants generated. LLM Prompt: {total_prompt_tokens} tokens.")
            else:
                self.main_window_ref.statusBar().showMessage("No variants were generated.")

        except Exception as e:
            self.main_window_ref.statusBar().showMessage(f"Error during generation: {e}")
            error_report_tab = QTextEdit()
            error_report_tab.setPlainText(f"An error occurred:\\n{type(e).__name__}: {e}\\n\\nPrompt used ({total_prompt_tokens} tokens):\\n{current_llm_prompt}")
            self.variant_display_tabs.addTab(error_report_tab, "Error")
            logger.error(f"Error during generation: {e}", exc_info=True)

    def _on_select_linked_elements_clicked(self) -> None:
        """
        Handles the click of the 'Select Linked Elements' button.
        Identifies linked elements from Character A, B, and Scene,
        then signals the LeftSelectionPanel to check them.
        """
        char_a_name: str = self.character_a_combo.currentText()
        char_b_name: str = self.character_b_combo.currentText()
        scene_name: str = self.scene_region_combo.currentText()
        # sub_location_name = self.scene_sub_location_combo.currentText() # Optional, handle if needed

        elements_to_select: set[str] = set()

        if char_a_name and char_a_name != "-- None --":
            elements_to_select.add(char_a_name)
            # Add elements linked to char_a_name
            char_a_details = self.context_builder.get_character_details_by_name(char_a_name)
            if char_a_details:
                elements_to_select.update(self._extract_linked_names(char_a_details))

        if char_b_name and char_b_name != "-- None --":
            elements_to_select.add(char_b_name)
            # Add elements linked to char_b_name
            char_b_details = self.context_builder.get_character_details_by_name(char_b_name)
            if char_b_details:
                elements_to_select.update(self._extract_linked_names(char_b_details))

        if scene_name and scene_name != "-- None --" and scene_name != "-- All --":
            elements_to_select.add(scene_name)
            # Add elements linked to scene_name
            scene_details = self.context_builder.get_location_details_by_name(scene_name)
            if scene_details:
                elements_to_select.update(self._extract_linked_names(scene_details))
            
            # Consider Sub-location as well
            sub_location_name = self.scene_sub_location_combo.currentText()
            if sub_location_name and sub_location_name != "-- None --":
                elements_to_select.add(sub_location_name)
                sub_loc_details = self.context_builder.get_location_details_by_name(sub_location_name)
                if sub_loc_details:
                    elements_to_select.update(self._extract_linked_names(sub_loc_details))


        if elements_to_select:
            self.main_window_ref.left_panel.set_checked_items_by_name(list(elements_to_select))
            self.main_window_ref.left_panel.clear_and_set_selected_items(list(elements_to_select), True)

    def _on_unlink_everything_clicked(self):
        """
        Handles the click of the 'Unlink Everything' button.
        Signals the LeftSelectionPanel to uncheck all items.
        """
        if self.main_window_ref and self.main_window_ref.left_panel:
            self.main_window_ref.left_panel.uncheck_all_items()
            self.main_window_ref.left_panel.clear_and_set_selected_items([], True) # Clear selections too

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

        directly_related_elements: set[str] = set()

        # Add selected characters and scene, and elements linked within their details
        if char_a_name and char_a_name != "-- None --":
            directly_related_elements.add(char_a_name)
            char_a_details = self.context_builder.get_character_details_by_name(char_a_name)
            if char_a_details:
                directly_related_elements.update(self._extract_linked_names(char_a_details))

        if char_b_name and char_b_name != "-- None --":
            directly_related_elements.add(char_b_name)
            char_b_details = self.context_builder.get_character_details_by_name(char_b_name)
            if char_b_details:
                directly_related_elements.update(self._extract_linked_names(char_b_details))

        if scene_name and scene_name != "-- None --" and scene_name != "-- All --":
            directly_related_elements.add(scene_name)
            scene_details = self.context_builder.get_location_details_by_name(scene_name)
            if scene_details:
                directly_related_elements.update(self._extract_linked_names(scene_details))
        
        if sub_location_name and sub_location_name != "-- None --":
            directly_related_elements.add(sub_location_name)
            sub_loc_details = self.context_builder.get_location_details_by_name(sub_location_name)
            if sub_loc_details:
                directly_related_elements.update(self._extract_linked_names(sub_loc_details))

        # 3. Determine items to keep checked: intersection of currently checked and directly related
        items_to_keep_checked: list[str] = list(currently_checked_items.intersection(directly_related_elements))
        
        # Log pour débogage
        # logger.debug(f"Currently checked: {currently_checked_items}")
        # logger.debug(f"Directly related: {directly_related_elements}")
        # logger.debug(f"Items to keep checked: {items_to_keep_checked}")

        # 4. Signal LeftSelectionPanel to update its state
        # set_checked_items_by_name will uncheck anything not in items_to_keep_checked
        # and ensure items_to_keep_checked are checked.
        if set(items_to_keep_checked) != currently_checked_items: # Only update if there's a change
            self.main_window_ref.left_panel.set_checked_items_by_name(items_to_keep_checked)
            # Pas besoin de clear_and_set_selected_items ici, car set_checked_items_by_name gère déjà le signal context_selection_changed
            # self.main_window_ref.statusBar().showMessage(f"{len(currently_checked_items) - len(items_to_keep_checked)} unrelated item(s) unlinked.", 3000)
        # else:
            # self.main_window_ref.statusBar().showMessage("No unrelated items to unlink among currently selected.", 3000)

    def _extract_linked_names(self, item_details: dict[str, Any]) -> set[str]:
        """
        Extracts names of linked items from an item's details dictionary.
        Recursively searches through the dictionary values.
        If a value is a string, it's added if it's non-empty.
        If a value is a list or set, its string elements are added.
        If a value is a dictionary, it's processed recursively.
        """
        linked_names: set[str] = set()
        if not isinstance(item_details, dict):
            return linked_names

        for _key, value in item_details.items():
            if isinstance(value, str):
                # Nous pourrions ajouter une logique pour vérifier si cette chaîne
                # correspond à un nom d'entité connue avant de l'ajouter.
                # Pour l'instant, nous ajoutons toutes les chaînes non vides trouvées
                # dans les valeurs du dictionnaire de premier niveau.
                # Cela pourrait être trop permissif. À évaluer.
                # Si les noms liés sont TOUJOURS dans des listes/sets, cette partie n'est pas nécessaire.
                # Prenons un exemple: si item_details["LieuAssocié"] = "NomLieu", on veut le récupérer.
                if value.strip(): # Ajoute les chaînes non vides
                    linked_names.add(value.strip())
            elif isinstance(value, (list, set)):
                for item_in_collection in value:
                    if isinstance(item_in_collection, str):
                        if item_in_collection.strip(): # Ajoute les chaînes non vides
                            linked_names.add(item_in_collection.strip())
                    elif isinstance(item_in_collection, dict):
                        linked_names.update(self._extract_linked_names(item_in_collection))
            elif isinstance(value, dict):
                linked_names.update(self._extract_linked_names(value))
        return linked_names

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