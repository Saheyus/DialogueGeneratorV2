# DialogueGenerator/ui/main_window.py
import json
import asyncio # Added for asynchronous tasks
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QComboBox, QTextEdit, QSplitter, 
                               QListWidget, QListWidgetItem, QTreeView, QAbstractItemView, QLineEdit,
                               QGroupBox, QHeaderView, QPushButton, QTabWidget, QApplication, QGridLayout, QCheckBox, QSizePolicy, QMessageBox, QSpacerItem)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QPalette, QColor, QAction, QCloseEvent, QGuiApplication
from PySide6.QtCore import Qt, QSize, QTimer, QItemSelectionModel, QSortFilterProxyModel, QRegularExpression, QSettings, Signal, Slot, QByteArray
import sys
import os
from pathlib import Path # Added for path management
import webbrowser # Added to open the configuration file
from typing import Optional, List

# Local imports from the same 'ui' package
from .left_selection_panel import LeftSelectionPanel # Added import
from .details_panel import DetailsPanel # Added import
from .generation_panel import GenerationPanel # Added import
# from .config_dialog import ConfigDialog  # Assuming ConfigDialog is in ui package -> Fichier manquant, commenté
from .utils import get_icon_path # Assurez-vous que utils.py et get_icon_path existent

# Imports from the parent 'DialogueGenerator' package
from ..context_builder import ContextBuilder 
from ..llm_client import OpenAIClient, DummyLLMClient, ILLMClient 
from ..prompt_engine import PromptEngine 
from .. import config_manager 
from ..services.linked_selector import LinkedSelectorService # Example if needed elsewhere

# Path to the DialogueGenerator directory
DIALOGUE_GENERATOR_DIR = Path(__file__).resolve().parent.parent
UI_SETTINGS_FILE = DIALOGUE_GENERATOR_DIR / "ui_settings.json" # File to save UI settings
CONTEXT_CONFIG_FILE_PATH = DIALOGUE_GENERATOR_DIR / "context_config.json" # Path to context_config.json
LLM_CONFIG_FILE_PATH = DIALOGUE_GENERATOR_DIR / "llm_config.json" # Ajout pour la config LLM

# Ensure the parent directory of DialogueGenerator (project root) is in PYTHONPATH
PROJECT_ROOT = DIALOGUE_GENERATOR_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

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
        self.current_selected_gdd_item_id: Optional[str] = None # Store ID of selected item
        self.current_selected_gdd_category: Optional[str] = None
        self.current_gdd_item_data: Optional[dict] = None # To store full data of selected GDD item

        self.llm_client: Optional[ILLMClient] = None
        self.prompt_engine: Optional[PromptEngine] = None
        self.llm_config: dict = {} # Pour stocker la config LLM chargée
        self.available_llm_models: List[dict] = [] # Pour stocker les modèles dispo
        
        self._load_llm_configuration() # Charger la configuration LLM

        # Initialize PromptEngine first, as it might be needed by GenerationPanel's init or early methods
        self.prompt_engine = PromptEngine()

        try:
            # Utiliser les valeurs de la config chargée
            default_model = self.llm_config.get("default_model_identifier", "gpt-4o-mini") # Fallback si non défini
            api_key_var = self.llm_config.get("api_key_env_var", "OPENAI_API_KEY")
            
            self.llm_client = OpenAIClient(model_identifier=default_model, api_key_env_var=api_key_var)
            logger.info(f"LLM Client initialized with {type(self.llm_client).__name__} using model '{default_model}'.")
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            QMessageBox.critical(self, "LLM Error", f"Could not initialize LLM client: {e}")
            self.llm_client = DummyLLMClient() # Fallback to dummy
            logger.info(f"Fell back to DummyLLMClient due to error.")
            # S'assurer que available_llm_models est initialisé même en cas d'erreur pour éviter crash UI
            if not self.available_llm_models:
                 self.available_llm_models = [{"display_name": "Dummy Client", "api_identifier": "dummy", "notes": "Fallback client"}]


        self.setWindowTitle("DialogueGenerator IA - Context Builder")
        self.setWindowIcon(get_icon_path("icon.png"))
        self.setGeometry(100, 100, 1600, 900) # Default size

        self._create_actions()
        self._create_menu_bar()

        self.left_panel = LeftSelectionPanel(context_builder=self.context_builder, parent=self)
        self.details_panel = DetailsPanel(parent=self) # Instantiate DetailsPanel
        self.generation_panel = GenerationPanel(
            context_builder=self.context_builder, 
            prompt_engine=self.prompt_engine, 
            llm_client=self.llm_client, # L'instance initiale est passée
            available_llm_models=self.available_llm_models, # Passer la liste des modèles
            current_llm_model_identifier=self.llm_client.model if self.llm_client and hasattr(self.llm_client, 'model') else self.llm_config.get("default_model_identifier", "dummy"), # Passer l'identifiant du modèle actuel
            main_window_ref=self,
            parent=self
        )

        self.setup_ui()
        # Déplacé après l'instanciation de generation_panel pour que les signaux soient connectés à une instance existante
        self.generation_panel.llm_model_selection_changed.connect(self._on_llm_model_selected_from_panel)
        self.generation_panel.finalize_ui_setup()
        
        self.left_panel.item_clicked_for_details.connect(self._on_explorer_list_item_clicked)

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
        self.left_panel.add_details_panel_as_tab(self.details_panel) # Ajout du DetailsPanel comme onglet
        self.main_splitter.addWidget(self.left_panel)
        self.main_splitter.addWidget(self.generation_panel)
        
        self.main_splitter.setStretchFactor(0, 1) # LeftPanel (avec onglets Sélection et Détails)
        self.main_splitter.setStretchFactor(1, 2) # GenerationPanel

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
        # Initialize avec toutes les clés attendues par ContextBuilder pour éviter des KeyError plus tard
        selections = {
            category_config['key']: [] for category_config in self.left_panel.categories_config
        }
        # Assurer que les clés spécifiques utilisées par GenerationPanel sont aussi présentes si pas dans categories_config
        # (normalement characters et locations y sont déjà)
        if "characters" not in selections: selections["characters"] = []
        if "locations" not in selections: selections["locations"] = []
        # Ajouter d'autres clés si ContextBuilder les attend et qu'elles ne viennent pas de LeftPanel
        # Par exemple, si 'quests' est une catégorie non affichée mais attendue par ContextBuilder:
        # if "quests" not in selections: selections["quests"] = [] 

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
        left_panel_settings = self.left_panel.get_settings()
        left_panel_checked_items = left_panel_settings.get("checked_items", {})
        
        for category_key, item_names_list in left_panel_checked_items.items():
            if category_key in selections:
                for item_name in item_names_list:
                    if item_name not in ignore_values:
                        selections[category_key].append(item_name)
            else:
                logger.warning(f"Category key '{category_key}' from LeftSelectionPanel not initially in main selections dict. Adding it.")
                selections[category_key] = [name for name in item_names_list if name not in ignore_values]
        
        # Deduplicate and clean final selections
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
        user_instruction_text = self.generation_panel.user_instructions_textedit.toPlainText()
        include_dialogue_type_flag = self.generation_panel.structured_output_checkbox.isChecked()
        
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
        
        # Pass all necessary info directly to DetailsPanel, including category_key
        # DetailsPanel will now handle finding the item if it's a GDD item, or reading the file if it's a yarn file.
        self.details_panel.update_details(category_key, item_text, category_data, category_singular_name)

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
        """Saves UI settings including splitter sizes and panel-specific settings.
        Triggered indirectly by _schedule_save_ui_settings.
        """
        if not hasattr(self, 'save_settings_timer'): # Peut être appelé avant init complet lors des tests
            return
            
        settings_data = {
            "main_window": {
                "geometry": self.saveGeometry().toBase64().data().decode(),
                "state": self.saveState().toBase64().data().decode(),
                "splitter_sizes": self.main_splitter.sizes(),
                "restore_selections_on_startup": self.restore_selections_action.isChecked()
            },
            # Déléguer aux panels pour leurs propres settings
            "left_panel": self.left_panel.get_settings(),
            "generation_panel": self.generation_panel.get_settings() 
        }
        
        # Ajouter l'identifiant du modèle LLM sélectionné par défaut pour le prochain démarrage
        if self.llm_client and hasattr(self.llm_client, 'model') and self.llm_client.model: # S'assurer que llm_client existe et a un modèle
            settings_data["main_window"]["default_llm_model"] = self.llm_client.model
        elif self.llm_config: # Fallback sur la config si le client n'est pas encore prêt ou a échoué
            settings_data["main_window"]["default_llm_model"] = self.llm_config.get("default_model_identifier")

        try:
            with open(UI_SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, indent=4)
            logger.info(f"UI settings saved to {UI_SETTINGS_FILE}")
            # self.statusBar().showMessage("UI settings saved.", 2000) # Peut être redondant si appelé souvent
        except Exception as e:
            logger.error(f"Error saving UI settings to {UI_SETTINGS_FILE}: {e}")
            # self.statusBar().showMessage(f"Error saving UI settings: {e}", 5000)

    def _load_ui_settings(self):
        """Loads UI settings including geometry, state, and panel-specific settings."""
        if UI_SETTINGS_FILE.exists():
            try:
                with open(UI_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    settings_data = json.load(f)
                
                main_window_settings = settings_data.get("main_window", {})
                geometry_b64 = main_window_settings.get("geometry", "")
                if geometry_b64: self.restoreGeometry(QByteArray.fromBase64(geometry_b64.encode()))
                
                state_b64 = main_window_settings.get("state", "")
                if state_b64: self.restoreState(QByteArray.fromBase64(state_b64.encode()))
                
                splitter_sizes = main_window_settings.get("splitter_sizes")
                if splitter_sizes and len(splitter_sizes) == 2 and hasattr(self, 'main_splitter'): # Check for validity
                    self.main_splitter.setSizes(splitter_sizes)
                
                if hasattr(self, 'restore_selections_action'):
                    self.restore_selections_action.setChecked(main_window_settings.get("restore_selections_on_startup", True))

                # Charger le modèle LLM par défaut sauvegardé
                saved_default_llm_model = main_window_settings.get("default_llm_model")
                if saved_default_llm_model and self.llm_config: 
                    current_default_in_config = self.llm_config.get("default_model_identifier")
                    if saved_default_llm_model != current_default_in_config:
                        logger.info(f"Modèle LLM par défaut des settings UI ('{saved_default_llm_model}') diffère de celui de llm_config.json ('{current_default_in_config}'). Priorité à celui des settings UI pour l'init du client.")
                        self.llm_config["default_model_identifier"] = saved_default_llm_model
                    else:
                         logger.info(f"Modèle LLM par défaut chargé depuis les settings UI : {saved_default_llm_model}")

                    # La logique d'initialisation du client dans __init__ utilisera maintenant cette valeur.
                    # Si le client est déjà initialisé et que le modèle diffère, il faut le recréer.
                    if self.llm_client and hasattr(self.llm_client, 'model') and self.llm_client.model != saved_default_llm_model:
                        logger.info(f"Tentative de resynchronisation du client LLM avec le modèle sauvegardé: {saved_default_llm_model} après chargement des settings.")
                        # Il est important que GenerationPanel soit déjà initialisé pour que le slot puisse fonctionner correctement
                        # et que le combobox soit mis à jour.
                        if hasattr(self, 'generation_panel') and self.generation_panel:
                           self._on_llm_model_selected_from_panel(saved_default_llm_model) 
                        else:
                            logger.warning("GenerationPanel non encore initialisé, impossible de resynchroniser le client LLM via _on_llm_model_selected_from_panel au chargement des settings.")

                # Déléguer aux panels pour charger leurs settings
                if hasattr(self, 'left_panel') and self.left_panel and "left_panel" in settings_data:
                    self.left_panel.load_settings(settings_data["left_panel"])
                    logger.info("LeftSelectionPanel settings loaded.")
                
                if hasattr(self, 'generation_panel') and self.generation_panel and "generation_panel" in settings_data:
                    self.generation_panel.load_settings(settings_data["generation_panel"])
                    logger.info("GenerationPanel settings loaded.")
                
                logger.info("UI settings loaded.")

            except json.JSONDecodeError:
                logger.error(f"Error decoding JSON from {UI_SETTINGS_FILE}")
            except Exception as e:
                logger.error(f"Unexpected error loading UI settings from {UI_SETTINGS_FILE}: {e}")
        else:
            logger.info(f"UI settings file {UI_SETTINGS_FILE} not found. Using default UI settings.")

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

    def _load_llm_configuration(self):
        """Charge la configuration LLM depuis le fichier JSON."""
        if LLM_CONFIG_FILE_PATH.exists():
            try:
                with open(LLM_CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                    self.llm_config = json.load(f)
                self.available_llm_models = self.llm_config.get("available_models", [])
                if not self.available_llm_models:
                    logger.warning(f"Aucun modèle LLM trouvé dans {LLM_CONFIG_FILE_PATH}. L'application pourrait ne pas fonctionner correctement.")
                    # Fournir une option par défaut minimale pour éviter les crashs
                    self.available_llm_models = [{"display_name": "Erreur Config Modèle", "api_identifier": "error", "notes": "Vérifier llm_config.json"}]
                logger.info(f"LLM configuration loaded from {LLM_CONFIG_FILE_PATH}.")
            except json.JSONDecodeError:
                logger.error(f"Erreur de décodage JSON dans {LLM_CONFIG_FILE_PATH}.")
                self._provide_default_llm_config_for_ui()
            except Exception as e:
                logger.error(f"Erreur inattendue lors du chargement de {LLM_CONFIG_FILE_PATH}: {e}")
                self._provide_default_llm_config_for_ui()
        else:
            logger.warning(f"Fichier de configuration LLM {LLM_CONFIG_FILE_PATH} introuvable. Utilisation de valeurs par défaut.")
            self._provide_default_llm_config_for_ui()

    def _provide_default_llm_config_for_ui(self):
        """Fournit une configuration LLM par défaut minimale pour l'UI en cas d'échec du chargement."""
        self.llm_config = {
            "available_models": [{"display_name": "Dummy (Config manquante)", "api_identifier": "dummy", "notes": "Fichier llm_config.json non trouvé ou invalide."}],
            "default_model_identifier": "dummy",
            "api_key_env_var": "OPENAI_API_KEY"
        }
        self.available_llm_models = self.llm_config["available_models"]

    @Slot(str) # Ajout du décorateur Slot
    def _on_llm_model_selected_from_panel(self, new_model_identifier: str):
        """Réagit au changement de sélection du modèle LLM dans GenerationPanel."""
        logger.info(f"MainWindow: Changement de modèle LLM demandé pour : {new_model_identifier}")
        api_key_var = self.llm_config.get("api_key_env_var", "OPENAI_API_KEY")
        try:
            # Tenter de créer le nouveau client. Si cela échoue, garder l'ancien.
            new_llm_client = OpenAIClient(model_identifier=new_model_identifier, api_key_env_var=api_key_var)
            
            # Si le client est créé avec succès (pas d'exception et clé API trouvée), alors on met à jour.
            if new_llm_client.client: # Vérifie que le client interne AsyncOpenAI est initialisé (donc clé API ok)
                self.llm_client = new_llm_client
                if hasattr(self.generation_panel, 'set_llm_client'):
                    self.generation_panel.set_llm_client(self.llm_client)
                logger.info(f"LLM Client mis à jour avec le modèle : {new_model_identifier}")
                self.statusBar().showMessage(f"Modèle LLM changé en : {new_model_identifier}", 3000)
                # Déclencher la mise à jour de l'estimation des tokens dans GenerationPanel
                if hasattr(self.generation_panel, '_trigger_token_update'): # Check if method exists
                    self.generation_panel._trigger_token_update()
            else:
                logger.error(f"Échec de l'initialisation du nouveau LLMClient pour {new_model_identifier} (probablement clé API manquante pour {api_key_var}). L'ancien client est conservé.")
                QMessageBox.warning(self, "Erreur de Modèle LLM", 
                                    f"Impossible de changer pour le modèle {new_model_identifier}. "
                                    f"Vérifiez que la variable d'environnement '{api_key_var}' est bien configurée et que le modèle est accessible. "
                                    "L'ancien modèle LLM est conservé.")
                # Remettre le combobox du GenerationPanel sur l'ancien modèle si possible
                if self.llm_client and hasattr(self.generation_panel, 'select_model_in_combo') and hasattr(self.llm_client, 'model'):
                    self.generation_panel.select_model_in_combo(self.llm_client.model)


        except Exception as e:
            logger.error(f"Erreur lors du changement du client LLM pour {new_model_identifier}: {e}")
            QMessageBox.critical(self, "Erreur LLM", f"Impossible de changer le modèle LLM pour {new_model_identifier}: {e}")
            # Remettre le combobox du GenerationPanel sur l'ancien modèle si possible
            if self.llm_client and hasattr(self.generation_panel, 'select_model_in_combo') and hasattr(self.llm_client, 'model'):
                    self.generation_panel.select_model_in_combo(self.llm_client.model)

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