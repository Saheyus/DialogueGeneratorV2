# DialogueGenerator/ui/main_window.py
import json
import asyncio # Added for asynchronous tasks
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QComboBox, QTextEdit, QSplitter, 
                               QListWidget, QListWidgetItem, QTreeView, QAbstractItemView, QLineEdit,
                               QGroupBox, QHeaderView, QPushButton, QTabWidget, QApplication, QGridLayout, QCheckBox)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QPalette, QColor, QAction, QCloseEvent
from PySide6.QtCore import Qt, QSize, QTimer, QItemSelectionModel, QSortFilterProxyModel, QRegularExpression
import sys
import os
from pathlib import Path # Added for path management
import webbrowser # Added to open the configuration file

# Import new modules
from prompt_engine import PromptEngine
from llm_client import OpenAIClient, DummyLLMClient
from .generation_panel import GenerationPanel
from .left_selection_panel import LeftSelectionPanel # Added import
from .details_panel import DetailsPanel # Added import

# Path to the DialogueGenerator directory
DIALOGUE_GENERATOR_DIR = Path(__file__).parent.parent
UI_SETTINGS_FILE = DIALOGUE_GENERATOR_DIR / "ui_settings.json" # File to save UI settings
CONTEXT_CONFIG_FILE_PATH = DIALOGUE_GENERATOR_DIR / "context_config.json" # Path to context_config.json

# Ensure the parent directory of DialogueGenerator (project root) is in PYTHONPATH
PROJECT_ROOT = DIALOGUE_GENERATOR_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Import ContextBuilder after adjusting the path
from DialogueGenerator.context_builder import ContextBuilder

# For logging
import logging
logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Main window of the DialogueGenerator application.

    This class manages the main UI structure, including the LeftSelectionPanel
    for GDD element browsing and selection, the DetailsPanel for displaying
    item details, and the GenerationPanel for configuring and triggering
    dialogue generation. 
    
    It orchestrates interactions between these panels and core components like
    ContextBuilder and PromptEngine, primarily by connecting signals and slots,
    and by providing access to shared data or functionality when necessary.
    It also handles UI settings persistence (loading/saving window state,
    splitter sizes, and delegating panel-specific settings).
    """
    def __init__(self, context_builder: ContextBuilder):
        """Initializes the MainWindow.

        Args:
            context_builder: Instance of ContextBuilder to access GDD data.
        """
        super().__init__()
        self.context_builder = context_builder
        self.prompt_engine = PromptEngine()
        
        try:
            self.llm_client = OpenAIClient(model="gpt-4o-mini")
            if not self.llm_client.api_key:
                print("WARNING: OpenAI API key not found. Switching to DummyLLMClient.")
                self.llm_client = DummyLLMClient()
        except Exception as e:
            print(f"Error initializing OpenAIClient: {e}. Switching to DummyLLMClient.")
            self.llm_client = DummyLLMClient()

        self.setWindowTitle("DialogueGenerator IA - Context Builder")
        self.setGeometry(100, 100, 1800, 900)

        self._create_actions()
        self._create_menu_bar()

        self.left_panel = LeftSelectionPanel(context_builder=self.context_builder, parent=self)
        self.details_panel = DetailsPanel(parent=self) # Instantiate DetailsPanel
        self.generation_panel = GenerationPanel(
            context_builder=self.context_builder, 
            prompt_engine=self.prompt_engine, 
            llm_client=self.llm_client, 
            main_window_ref=self,
            parent=self
        )

        self.setup_ui()
        self.generation_panel.finalize_ui_setup()
        
        self.left_panel.item_clicked_for_details.connect(self._on_explorer_list_item_clicked)
        self.left_panel.context_selection_changed.connect(self._trigger_generation_panel_token_ui_update)

        if self.context_builder:
            self.load_initial_data()

        self._load_ui_settings() 
        self._connect_signals_for_auto_save()

        QTimer.singleShot(50, self._update_token_estimation_and_prompt_display)

        self.token_update_timer = QTimer(self)
        self.token_update_timer.setSingleShot(True)
        self.token_update_timer.timeout.connect(self._update_token_estimation_and_prompt_display)

        self.save_settings_timer = QTimer(self)
        self.save_settings_timer.setSingleShot(True)
        self.save_settings_timer.timeout.connect(self._perform_actual_save_ui_settings)
        self.save_settings_delay_ms = 1500

    def _create_actions(self):
        """Creates actions for the menus."""
        self.restore_selections_action = QAction("Restore selections on startup", self)
        self.restore_selections_action.setCheckable(True)
        self.restore_selections_action.setChecked(True) # Default
        # Logic for saving/loading this state will be in _save/_load_ui_settings

        self.edit_context_config_action = QAction("&Edit Context Configuration...", self)
        self.edit_context_config_action.triggered.connect(self._open_context_config_file)

        self.exit_action = QAction("&Exit", self)
        self.exit_action.triggered.connect(self.close)

    def _create_menu_bar(self):
        """Creates the main menu bar with application options."""
        menu_bar = self.menuBar()

        # File Menu (or Options)
        options_menu = menu_bar.addMenu("&Options")
        options_menu.addAction(self.restore_selections_action)
        options_menu.addSeparator()
        options_menu.addAction(self.edit_context_config_action) 
        options_menu.addSeparator()
        options_menu.addAction(self.exit_action)

    def _open_context_config_file(self):
        """Opens the context configuration file (context_config.json)
        in the system's default editor.
        """
        if CONTEXT_CONFIG_FILE_PATH.exists():
            try:
                webbrowser.open(os.path.realpath(CONTEXT_CONFIG_FILE_PATH))
                logger.info(f"Attempting to open {CONTEXT_CONFIG_FILE_PATH}")
            except Exception as e:
                logger.error(f"Could not open {CONTEXT_CONFIG_FILE_PATH}: {e}")
                self.statusBar().showMessage(f"Error: Could not open configuration file: {e}")
        else:
            logger.warning(f"Configuration file {CONTEXT_CONFIG_FILE_PATH} does not exist.")
            self.statusBar().showMessage("Error: Context configuration file not found.")

    def setup_ui(self):
        """Configures the main user interface of the window.

        Initializes the LeftSelectionPanel, DetailsPanel, and GenerationPanel,
        assembles them within a QSplitter, and sets this as the central widget.
        """
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.addWidget(self.left_panel)
        self.main_splitter.addWidget(self.details_panel) # Use the instantiated DetailsPanel
        self.main_splitter.addWidget(self.generation_panel)
        
        self.main_splitter.setStretchFactor(0, 1) 
        self.main_splitter.setStretchFactor(1, 2) 
        self.main_splitter.setStretchFactor(2, 2) 

        main_layout.addWidget(self.main_splitter)
        
        self.statusBar().showMessage("Ready.")

    def _get_current_context_selections(self) -> dict:
        """Retrieves all user selections relevant for context building.

        Combines selections from GenerationPanel (character/scene combos)
        and LeftSelectionPanel (checked items in lists). This data is then
        passed to the ContextBuilder.

        Returns:
            dict: A dictionary with item categories (e.g., "characters", "locations")
                  and a list of selected item names for each category.
        """
        ignore_values = {"-- None --", "<None>", "-- All --", ""}
        selections = {
            "characters": [], "locations": [], "items": [], "species": [],
            "communities": [], "dialogues_examples": [], "quests": [] 
        }

        char_a_name = self.generation_panel.character_a_combo.currentText()
        char_b_name = self.generation_panel.character_b_combo.currentText()
        if char_a_name not in ignore_values: selections["characters"].append(char_a_name)
        if char_b_name not in ignore_values: selections["characters"].append(char_b_name)

        current_region_name = self.generation_panel.scene_region_combo.currentText()
        current_sub_location_name = self.generation_panel.scene_sub_location_combo.currentText()
        if current_sub_location_name not in ignore_values:
            selections["locations"].append(current_sub_location_name)
        elif current_region_name not in ignore_values:
            selections["locations"].append(current_region_name)

        # Get selections from LeftSelectionPanel
        left_panel_checked_items = self.left_panel.get_all_checked_items()
        for category_key, item_names_list in left_panel_checked_items.items():
            if category_key in selections:
                for item_name in item_names_list:
                    if item_name not in ignore_values:
                        selections[category_key].append(item_name)
            else:
                logger.warning(f"Category key '{category_key}' from LeftSelectionPanel not in main selections dict.")
        
        for category_key in selections:
            valid_items = []
            seen_items = set()
            for item_name in selections[category_key]:
                if item_name not in ignore_values and item_name not in seen_items:
                    valid_items.append(item_name)
                    seen_items.add(item_name)
            selections[category_key] = valid_items
        
        return selections

    def _trigger_generation_panel_token_ui_update(self) -> None:
        """
        Slot pour réagir aux changements de sélection du LeftPanel.
        Demande au GenerationPanel de mettre à jour son estimation de tokens et son UI.
        """
        if hasattr(self.generation_panel, '_request_and_update_prompt_estimation'):
            # logger.debug("MainWindow: LeftPanel selection changed, triggering GenerationPanel UI update.")
            self.generation_panel._request_and_update_prompt_estimation()
        # else:
            # logger.warning("MainWindow: GenerationPanel does not have _request_and_update_prompt_estimation method.")

    def _update_token_estimation_and_prompt_display(self) -> tuple[str | None, int, str | None, int]:
        """Calculates context string, full prompt string, and their token counts.

        This method is called when context selections change (from LeftSelectionPanel
        or GenerationPanel) or when user instructions in GenerationPanel change.
        It uses ContextBuilder to get the context string and PromptEngine to get
        the full prompt estimation.
        
        The returned values are intended to be used by GenerationPanel to update
        its display of token counts and the estimated prompt.

        Returns:
            tuple[str | None, int, str | None, int]: 
                - context_string (str): The assembled context string from ContextBuilder, or None if an error occurs.
                - context_token_count (int): The token count for the context_string.
                - estimated_full_prompt_text (str): The full prompt text estimated by PromptEngine, or None if an error occurs.
                - estimated_total_token_count (int): The total token count for the estimated_full_prompt_text.
        """
        if not self.context_builder or not self.prompt_engine:
            logger.warning("_update_token_estimation_and_prompt_display: ContextBuilder or PromptEngine not initialized.")
            return None, 0, None, 0

        selected_elements = self._get_current_context_selections()
        user_instruction_text = self.generation_panel.user_instruction_input.toPlainText()
        include_dialogue_type_flag = self.generation_panel.include_dialogue_type_checkbox.isChecked()
        
        MAX_TOKENS_FOR_CONTEXT_BUILDING = 32000 
        
        try:
            context_string = self.context_builder.build_context(
                selected_elements,
                user_instruction_text, 
                max_tokens=MAX_TOKENS_FOR_CONTEXT_BUILDING, 
                include_dialogue_type=include_dialogue_type_flag
            )
            context_token_count = self.context_builder._count_tokens(context_string)

            generation_parameters = {} 
            
            estimated_full_prompt_text, estimated_total_token_count = self.prompt_engine.build_prompt(
                context_summary=context_string, 
                user_specific_goal=user_instruction_text,
                generation_params=generation_parameters
            )
            
            return context_string, context_token_count, estimated_full_prompt_text, estimated_total_token_count
        except Exception as e:
            logger.error(f"Error in _update_token_estimation_and_prompt_display: {e}", exc_info=True)
            return None, 0, None, 0

    def _on_explorer_list_item_clicked(self, category_key: str, item_text: str, category_data: list, category_singular_name: str):
        """Handles clicks on items in the explorer lists (signaled by LeftSelectionPanel).
        
        Retrieves the detailed data for the clicked item using the provided
        category_data and item_text, then instructs the DetailsPanel
        to display these details.

        Args:
            category_key (str): The key identifying the category of the clicked item (e.g., "characters").
            item_text (str): The display text of the clicked item.
            category_data (list): The list of all items in that category, typically a list of dictionaries.
            category_singular_name (str): The singular display name for the category (e.g., "Character").
        """
        logger.debug(f"Item clicked in category '{category_key}': '{item_text}'")
        self.statusBar().showMessage(f"Selected: {category_singular_name} - {item_text}")
        
        selected_item_data = None
        if not hasattr(self, 'left_panel') or not hasattr(self.left_panel, 'category_name_key_priorities'):
            logger.error("LeftPanel or its category_name_key_priorities attribute is not initialized.")
            self.details_panel.display_details(None, category_singular_name, item_text)
            return

        name_key_priority_list = self.left_panel.category_name_key_priorities.get(
            category_key, 
            ["Nom", "Name", "Titre", "ID"] 
        )

        if not category_data:
            logger.warning(f"No category data provided for '{category_key}' to find '{item_text}'.")
            self.details_panel.display_details(None, category_singular_name, item_text)
            return

        for i, item_dict in enumerate(category_data):
            if isinstance(item_dict, dict):
                for key_to_check in name_key_priority_list:
                    value_in_dict = item_dict.get(key_to_check)
                    if value_in_dict is not None and str(value_in_dict) == item_text:
                        selected_item_data = item_dict
                        break  
            if selected_item_data: 
                break 
        
        if selected_item_data:
            self.details_panel.display_details(selected_item_data, category_singular_name, item_text)
        else:
            logger.warning(f"Could not find details for '{item_text}' in {category_singular_name} data after checking {len(category_data)} items.")
            if category_data and isinstance(category_data[0], dict):
                 pass
            self.details_panel.display_details(None, category_singular_name, item_text)

    def load_initial_data(self):
        """Loads initial GDD data into the UI.
        
        Primarily populates lists in the LeftSelectionPanel using data from the
        ContextBuilder. Also ensures the GenerationPanel populates its own
        character and location comboboxes.
        """
        logger.info("Loading initial GDD data into UI...")
        if self.context_builder:
            self.left_panel.populate_all_lists()
            # GenerationPanel's combos are populated via its finalize_ui_setup or internal logic
            logger.info("Initial data loaded into LeftSelectionPanel.")
        else:
            logger.warning("ContextBuilder not available. Cannot load initial data.")
        self.statusBar().showMessage("GDD data loaded.", 3000)
        # self._update_token_estimation_and_prompt_display() # This is called via QTimer.singleShot in __init__ after load

    def _save_ui_settings(self):
        """Saves the current UI settings.
        
        This includes window geometry, splitter sizes, the state of the 
        'restore selections on startup' option, and delegates to LeftSelectionPanel 
        and GenerationPanel to retrieve their specific settings.
        The combined settings are saved to a JSON file.
        """
        if not self.isVisible():
            return
            
        logger.info("Saving UI settings...")
        settings = {
            "window_geometry": self.saveGeometry().data().hex(),
            "splitter_sizes": self.main_splitter.sizes(),
            "restore_on_startup": self.restore_selections_action.isChecked(),
            "left_panel": self.left_panel.get_settings(), # MODIFIED
            "generation_panel": self.generation_panel.get_settings()
        }
        try:
            with open(UI_SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=4)
            logger.info(f"UI settings saved to {UI_SETTINGS_FILE}")
            self.statusBar().showMessage("UI settings saved.", 2000)
        except Exception as e:
            logger.error(f"Error saving UI settings: {e}")
            self.statusBar().showMessage(f"Error saving settings: {e}", 3000)

    def _load_ui_settings(self):
        """Loads UI settings from the JSON file.
        
        Restores window geometry, splitter state, and the 'restore selections on startup'
        option. If 'restore selections' is enabled, it delegates to LeftSelectionPanel
        and GenerationPanel to load their specific settings from the loaded data.
        Triggers an update of the token estimation after loading.
        """
        logger.info(f"Attempting to load UI settings from {UI_SETTINGS_FILE}...")
        try:
            if UI_SETTINGS_FILE.exists():
                with open(UI_SETTINGS_FILE, 'r') as f:
                    settings = json.load(f) # Correctly indented
                    logger.info(f"Successfully loaded settings: {list(settings.keys())}")
                    
                    if settings.get("window_geometry"):
                        self.restoreGeometry(bytes.fromhex(settings["window_geometry"]))
                    if settings.get("splitter_sizes"):
                        self.main_splitter.setSizes(settings["splitter_sizes"])
                    
                    self.restore_selections_action.setChecked(settings.get("restore_on_startup", True))

                    if self.restore_selections_action.isChecked():
                        logger.info("Restore selections on startup is TRUE. Loading panel settings.")
                        left_panel_settings = settings.get("left_panel")
                        if left_panel_settings:
                            self.left_panel.load_settings(left_panel_settings)
                        else:
                            logger.info("No settings found for left_panel in ui_settings.json")

                        generation_panel_settings = settings.get("generation_panel")
                        if generation_panel_settings:
                            self.generation_panel.load_settings(generation_panel_settings)
                        else:
                            logger.info("No settings found for generation_panel in ui_settings.json")
                    else:
                        logger.info("Restore selections on startup is FALSE. Skipping panel settings load.")
                    self.statusBar().showMessage("UI settings loaded.", 2000)
                    logger.info("UI settings loaded successfully.")
            else:
                logger.info(f"Settings file {UI_SETTINGS_FILE} not found. Using default settings.")
                self.statusBar().showMessage("Settings file not found. Using defaults.", 2000)
                self.left_panel.load_settings({}) 
                self.generation_panel.load_settings({})

        except Exception as e:
            logger.error(f"Error loading UI settings: {e}", exc_info=True)
            self.statusBar().showMessage(f"Error loading settings: {e}. Using defaults.", 3000)
            # Ensure panels are in a known state even if settings load fails partially or completely
            self.left_panel.load_settings({}) 
            self.generation_panel.load_settings({})
        
        # This call was potentially problematic if settings load itself caused issues that affected UI state
        # before this was called. Moving it to be more reliably after all other UI setup and loading.
        # Consider if this QTimer.singleShot is still the best place or if it should be at the very end of __init__.
        QTimer.singleShot(100, self._update_token_estimation_and_prompt_display)

    def _perform_actual_save_ui_settings(self):
        self._save_ui_settings()

    def _schedule_save_ui_settings(self):
        logger.debug("Scheduling UI settings save.")
        self.save_settings_timer.start(self.save_settings_delay_ms)

    def _connect_signals_for_auto_save(self):
        """Connects signals from various UI elements to schedule settings save.
        
        Changes in LeftSelectionPanel (checked items, filters) and GenerationPanel
        (combo boxes, text inputs, checkboxes) will trigger a delayed save
        of the UI settings.
        """
        # Left Panel changes
        self.left_panel.context_selection_changed.connect(self._schedule_save_ui_settings)
        for filter_edit in self.left_panel.filter_edits.values():
            filter_edit.textChanged.connect(self._schedule_save_ui_settings)

        # Generation Panel changes
        # Connect to the new consolidated signal from GenerationPanel
        self.generation_panel.settings_changed.connect(self._schedule_save_ui_settings)

        self.restore_selections_action.triggered.connect(self._schedule_save_ui_settings)
        logger.info("Connected signals for auto-saving UI settings.")

    def closeEvent(self, close_event: QCloseEvent):
        """Overrides closeEvent to save settings before exiting.

        Args:
            close_event: The close event.
        """
        self._save_ui_settings()
        super().closeEvent(close_event)

# For testing, if you run main_window.py directly (requires some adjustments)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[logging.StreamHandler()]) 

    logger.info("Starting DialogueGenerator application...") # Translated
    app = QApplication(sys.argv)

    logger.info("Initializing ContextBuilder...") # Translated
    context_builder_instance = ContextBuilder() # Renamed
    context_builder_instance.load_gdd_files()
    logger.info("ContextBuilder initialized.") # Translated

    logger.info("Initializing MainWindow...") # Translated
    main_application_window = MainWindow(context_builder_instance) # Renamed
    main_application_window.show()
    logger.info("MainWindow displayed.") # Translated

    sys.exit(app.exec()) 