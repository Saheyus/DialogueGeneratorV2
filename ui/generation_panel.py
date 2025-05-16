from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QGridLayout, 
                               QLabel, QComboBox, QTextEdit, QPushButton, 
                               QTabWidget, QLineEdit, QCheckBox, QHBoxLayout)
from PySide6.QtCore import Qt

class GenerationPanel(QWidget):
    """Manages the UI elements for the dialogue generation parameters and display.

    This panel includes selections for the scene (characters, location),
    generation parameters (number of variants, max tokens),
    the field for user instructions, the generation button,
    and tabs to display the prompt and generated variants.
    """
    def __init__(self, parent=None):
        """Initializes the GenerationPanel.

        Args:
            parent: The parent widget.
        """
        super().__init__(parent)
        
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

        # Note: Signal connections that were in MainWindow.__init__ or _create_right_generation_panel
        # for these widgets will be handled by MainWindow initially after this panel is instantiated,
        # or eventually moved into this class if the handling logic also moves. 