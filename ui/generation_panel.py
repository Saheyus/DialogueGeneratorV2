from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QGridLayout, 
                               QLabel, QComboBox, QTextEdit, QPushButton, 
                               QTabWidget, QLineEdit, QCheckBox, QHBoxLayout)
from PySide6.QtCore import Qt
import logging # Added for logging

logger = logging.getLogger(__name__) # Added logger

class GenerationPanel(QWidget):
    """Manages the UI elements for the dialogue generation parameters and display.

    This panel includes selections for the scene (characters, location),
    generation parameters (number of variants, max tokens),
    the field for user instructions, the generation button,
    and tabs to display the prompt and generated variants.
    """
    def __init__(self, context_builder, prompt_engine, llm_client, main_window_ref, parent=None): # Added dependencies
        """Initializes the GenerationPanel.

        Args:
            context_builder: Instance of ContextBuilder.
            prompt_engine: Instance of PromptEngine.
            llm_client: Instance of LLMClient (OpenAIClient or DummyLLMClient).
            main_window_ref: Reference to the MainWindow for accessing status bar etc.
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

        context_selection_layout.addWidget(self.character_a_label, 0, 0)
        context_selection_layout.addWidget(self.character_a_combo, 0, 1)
        context_selection_layout.addWidget(self.character_b_label, 1, 0)
        context_selection_layout.addWidget(self.character_b_combo, 1, 1)
        context_selection_layout.addWidget(self.scene_region_label, 2, 0)
        context_selection_layout.addWidget(self.scene_region_combo, 2, 1)
        context_selection_layout.addWidget(self.scene_sub_location_label, 3, 0)
        context_selection_layout.addWidget(self.scene_sub_location_combo, 3, 1)
        context_selection_layout.addWidget(self.suggest_linked_elements_button, 4, 0, 1, 2)
        
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
        self.generate_dialogue_button.clicked.connect(self._on_generate_dialogue_button_clicked) 
        self.suggest_linked_elements_button.clicked.connect(self._on_suggest_linked_elements_clicked)
        
        # Signals that trigger token updates and initial population are deferred to finalize_ui_setup

    def finalize_ui_setup(self):
        """Finalizes the UI setup by connecting signals and populating combos.
        
        This method should be called after the GenerationPanel is fully initialized
        and its reference is available to the MainWindow.
        """
        logger.info("GenerationPanel: Finalizing UI setup...")
        # Connect signals that might trigger updates through MainWindow via _trigger_token_update
        self.character_a_combo.currentIndexChanged.connect(self._trigger_token_update)
        self.character_b_combo.currentIndexChanged.connect(self._trigger_token_update)
        self.scene_region_combo.currentIndexChanged.connect(self._on_scene_region_changed) 
        self.scene_region_combo.currentIndexChanged.connect(self._trigger_token_update) 
        self.scene_sub_location_combo.currentIndexChanged.connect(self._trigger_token_update)
        self.include_dialogue_type_checkbox.stateChanged.connect(self._trigger_token_update)
        self.user_instruction_input.textChanged.connect(self._trigger_token_update)

        # Populate comboboxes
        self.populate_scene_combos()
        logger.info("GenerationPanel: Finalizing UI setup complete.")

    def _trigger_token_update(self):
        """Helper method to request token update from MainWindow."""
        # This will eventually call a method (e.g., _update_token_estimation_and_prompt_display)
        # that will be moved into this class or MainWindow will expose a specific method.
        # For now, assuming MainWindow handles the update.
        if hasattr(self.main_window_ref, '_update_token_estimation_and_prompt_display'):
            self.main_window_ref._update_token_estimation_and_prompt_display()
        else:
            logger.warning("MainWindow reference does not have _update_token_estimation_and_prompt_display method.")

    def populate_scene_combos(self):
        """Populates the character and location comboboxes for scene selection."""
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
        """Updates the sub-location list when the selected region changes."""
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
    def _on_generate_dialogue_button_clicked(self):
        logger.info("GenerationPanel: Generate Dialogue button clicked (logic to be fully moved here).")
        # Call MainWindow's method for now, or implement fully here later.
        if hasattr(self.main_window_ref, '_on_generate_dialogue_button_clicked'):
             self.main_window_ref._on_generate_dialogue_button_clicked() # Still calling MainWindow's logic
        else:
            self.main_window_ref.statusBar().showMessage("Generate logic not yet fully moved to GenerationPanel.")


    def _on_suggest_linked_elements_clicked(self):
        logger.info("GenerationPanel: Suggest Linked Elements button clicked (logic to be fully moved here).")
        # Call MainWindow's method for now, or implement fully here later.
        if hasattr(self.main_window_ref, '_on_suggest_linked_elements_clicked'):
            self.main_window_ref._on_suggest_linked_elements_clicked() # Still calling MainWindow's logic
        else:
             self.main_window_ref.statusBar().showMessage("Suggest links logic not yet fully moved to GenerationPanel.")

    # Methods for MainWindow to get/set UI states of this panel (for _save/_load_ui_settings)
    def get_settings(self) -> dict:
        """Returns the current UI settings of this panel."""
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
        """Loads UI settings into this panel's widgets."""
        logger.info(f"GenerationPanel: Attempting to load settings: {settings}")
        
        # --- Store signal states and disconnect --- 
        # (Using a more direct way to manage signal blocking for simplicity here)
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
            original_signal_states[widget.objectName()] = widget.signalsBlocked() # Assuming QCheckBox/QTextEdit also have objectName set if needed
            block_method(True)

        # --- Load settings ---
        logger.info("GenerationPanel: Loading character_a_combo")
        self._set_combo_text_robust(self.character_a_combo, settings.get("character_a_combo_text", "-- None --"))
        
        logger.info("GenerationPanel: Loading character_b_combo")
        self._set_combo_text_robust(self.character_b_combo, settings.get("character_b_combo_text", "-- None --"))
        
        saved_region_text = settings.get("scene_region_combo_text", "-- All --")
        logger.info(f"GenerationPanel: Loading scene_region_combo with '{saved_region_text}'")
        self._set_combo_text_robust(self.scene_region_combo, saved_region_text)
        
        logger.info("GenerationPanel: Manually calling _on_scene_region_changed after setting region combo.")
        self._on_scene_region_changed() # This will populate sub-locations

        saved_sub_location_text = settings.get("scene_sub_location_combo_text", "-- None --")
        logger.info(f"GenerationPanel: Loading scene_sub_location_combo with '{saved_sub_location_text}'")
        self._set_combo_text_robust(self.scene_sub_location_combo, saved_sub_location_text)

        variant_count = settings.get("variant_count_input_text", "1")
        logger.info(f"GenerationPanel: Loading variant_count_input with '{variant_count}'")
        self.variant_count_input.setText(variant_count)

        max_tokens = settings.get("max_tokens_input_text", "4")
        logger.info(f"GenerationPanel: Loading max_tokens_input with '{max_tokens}'")
        self.max_tokens_input.setText(max_tokens)

        include_dialogue_type = settings.get("include_dialogue_type_checkbox_checked", True)
        logger.info(f"GenerationPanel: Loading include_dialogue_type_checkbox with {include_dialogue_type}")
        self.include_dialogue_type_checkbox.setChecked(include_dialogue_type)

        user_instruction = settings.get("user_instruction_input_text", "")
        logger.info(f"GenerationPanel: Loading user_instruction_input with '{user_instruction[:50]}...'")
        self.user_instruction_input.setPlainText(user_instruction)

        # --- Restore signal states ---
        logger.info("GenerationPanel: Restoring signal states.")
        for combo in combos_to_block:
            if not original_signal_states.get(combo.objectName(), False): # Only unblock if it was originally not blocked
                combo.blockSignals(False)
        for widget, block_method in other_widgets_to_block_signals.items():
             if not original_signal_states.get(widget.objectName(), False):
                block_method(False) # Call the original blockSignals(False)
        
        logger.info("GenerationPanel: Settings loading complete. Triggering final token update.")
        self._trigger_token_update() # Trigger a final update after all settings are loaded

    def _set_combo_text_robust(self, combo_box: QComboBox, text_to_set: str):
        """Helper to set QComboBox text, robustly finding the item."""
        combo_name = combo_box.objectName() if combo_box.objectName() else "Unnamed ComboBox"
        logger.info(f"GenerationPanel._set_combo_text_robust: Setting {combo_name} to '{text_to_set}'. Available items: {[combo_box.itemText(i) for i in range(combo_box.count())]}")
        if not text_to_set:
            logger.debug(f"GenerationPanel._set_combo_text_robust: Empty text_to_set for {combo_name}, skipping.")
            return
        
        idx = combo_box.findText(text_to_set) # Exact match first
        if idx == -1: # Case-insensitive and space-insensitive fallback
            normalized_target = "".join(text_to_set.split()).lower()
            logger.debug(f"GenerationPanel._set_combo_text_robust: '{text_to_set}' not found by exact match in {combo_name}. Trying normalized search for '{normalized_target}'.")
            for i in range(combo_box.count()):
                candidate = combo_box.itemText(i)
                normalized_candidate = "".join(candidate.split()).lower()
                if normalized_candidate == normalized_target:
                    idx = i
                    logger.debug(f"GenerationPanel._set_combo_text_robust: Normalized search found '{text_to_set}' (as '{candidate}') at index {i} in {combo_name}.")
                    break
        if idx != -1:
            combo_box.setCurrentIndex(idx)
            logger.info(f"GenerationPanel._set_combo_text_robust: Successfully set {combo_name} to '{text_to_set}' (index {idx}).")
        else:
            logger.warning(f"GenerationPanel._set_combo_text_robust: Item '{text_to_set}' not found in {combo_name}. Current items: {[combo_box.itemText(i) for i in range(combo_box.count())]}") 