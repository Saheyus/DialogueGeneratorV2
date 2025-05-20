# DialogueGenerator/ui/main_window.py
import json
import asyncio # Added for asynchronous tasks
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QComboBox, QTextEdit, QSplitter, 
                               QListWidget, QListWidgetItem, QTreeView, QAbstractItemView, QLineEdit,
                               QGroupBox, QHeaderView, QPushButton, QTabWidget, QApplication, QGridLayout, QCheckBox, QSizePolicy, QMessageBox, QSpacerItem, QFileDialog)
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
from .generation_panel_base import GenerationPanel # New import
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

        self.app_settings: dict = { # Initialisation avec des valeurs par défaut robustes
            "max_context_tokens": 1500,
            "restore_selections_on_startup": True,
            "window_geometry": None,
            "main_splitter_sizes": None,
            "generation_panel_splitter_sizes": None,
            "current_llm_model_identifier": None
        }
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
        
        self.configure_unity_path_action = QAction("Configure &Unity Dialogues Path...", self)
        self.configure_unity_path_action.triggered.connect(self._configure_unity_dialogues_path)

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
        options_menu.addAction(self.configure_unity_path_action) 
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

    def _configure_unity_dialogues_path(self):
        """Ouvre une boîte de dialogue pour configurer le chemin des dialogues Unity."""
        current_path = config_manager.get_unity_dialogues_path()
        current_path_str = str(current_path) if current_path else ""
        
        new_path = QFileDialog.getExistingDirectory(
            self,
            "Sélectionner le dossier des dialogues Unity",
            current_path_str
        )
        
        if new_path:  # L'utilisateur n'a pas annulé
            if config_manager.set_unity_dialogues_path(new_path):
                logger.info(f"Chemin des dialogues Unity configuré: {new_path}")
                self.statusBar().showMessage(f"Chemin des dialogues Unity configuré: {new_path}", 5000)
                
                # Mettre à jour l'interface pour refléter le nouveau chemin
                if hasattr(self.left_panel, 'populate_yarn_files_list'):
                    self.left_panel.populate_yarn_files_list()
            else:
                logger.error(f"Échec de la configuration du chemin des dialogues Unity: {new_path}")
                self.statusBar().showMessage("Échec de la configuration du chemin des dialogues Unity", 5000)

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
        """Récupère les sélections de contexte actuelles pour le GenerationPanel."""
        if not self.generation_panel:
            return {}
        
        # Accès via le sous-widget scene_selection_widget
        char_a_name = self.generation_panel.scene_selection_widget.character_a_combo.currentText()
        char_b_name = self.generation_panel.scene_selection_widget.character_b_combo.currentText()
        scene_region_name = self.generation_panel.scene_selection_widget.scene_region_combo.currentText()
        scene_sub_location_name = self.generation_panel.scene_selection_widget.scene_sub_location_combo.currentText()

        # Nettoyage des valeurs pour les rendre utilisables (None si non pertinent)
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

        if char_a_name not in ignore_values: selections["characters"].append(char_a_name)
        if char_b_name not in ignore_values: selections["characters"].append(char_b_name)

        if scene_sub_location_name not in ignore_values:
            selections["locations"].append(scene_sub_location_name)
        elif scene_region_name not in ignore_values:
            selections["locations"].append(scene_region_name)

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

        if not self.generation_panel or not self.generation_panel.isVisible():
            return None, 0, None, 0

        # Accès via le sous-widget generation_params_widget
        include_dialogue_type_flag = self.generation_panel.generation_params_widget.structured_output_checkbox.isChecked()
        # Accès via le sous-widget instructions_widget
        user_instructions = self.generation_panel.instructions_widget.get_user_instructions_text()

        selected_elements = self._get_current_context_selections()
        
        MAX_TOKENS_FOR_CONTEXT_BUILDING = 32000 
        
        try:
            context_string = self.context_builder.build_context(
                selected_elements,
                user_instructions, 
                max_tokens=self.app_settings.get("max_context_tokens", 1500), # Utiliser app_settings
                include_dialogue_type=include_dialogue_type_flag
            )
            context_token_count = self.context_builder._count_tokens(context_string)

            generation_parameters = {} 
            
            estimated_full_prompt_text, estimated_total_token_count = self.prompt_engine.build_prompt(
                context_summary=context_string, 
                user_specific_goal=user_instructions,
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

    def _load_ui_settings(self):
        """Charge les paramètres UI sauvegardés (taille fenêtre, position, état splitter, sélections, etc.)."""
        logger.info(f"Chargement des paramètres UI depuis {UI_SETTINGS_FILE}")
        if not UI_SETTINGS_FILE.exists():
            logger.info(f"Aucun fichier de paramètres UI trouvé à {UI_SETTINGS_FILE}. Utilisation des valeurs par défaut déjà dans self.app_settings.")
            # Les valeurs par défaut sont déjà dans self.app_settings lors de l'initialisation
            # Charger les settings par défaut pour les panneaux aussi, ou laisser les panneaux gérer leurs défauts.
            self.generation_panel.load_settings({}) # Permet à GenerationPanel de charger ses propres défauts
            self.left_panel.load_settings({}) # Idem pour LeftSelectionPanel
            return

        all_settings = {}
        try:
            with open(UI_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                all_settings = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de décodage JSON dans {UI_SETTINGS_FILE}: {e}. Utilisation des valeurs par défaut.")
            # Conserver les valeurs par défaut de self.app_settings
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la lecture de {UI_SETTINGS_FILE}: {e}. Utilisation des valeurs par défaut.")
            # Conserver les valeurs par défaut de self.app_settings

        # Mettre à jour self.app_settings avec les valeurs chargées, en gardant les défauts si clés manquantes
        self.app_settings["window_geometry"] = all_settings.get("window_geometry", self.app_settings["window_geometry"])
        self.app_settings["main_splitter_sizes"] = all_settings.get("main_splitter_sizes", self.app_settings["main_splitter_sizes"])
        self.app_settings["generation_panel_splitter_sizes"] = all_settings.get("generation_panel_splitter_sizes", self.app_settings["generation_panel_splitter_sizes"])
        self.app_settings["restore_selections_on_startup"] = all_settings.get("restore_selections_on_startup", self.app_settings["restore_selections_on_startup"])
        self.app_settings["max_context_tokens"] = all_settings.get("max_context_tokens", self.app_settings["max_context_tokens"])
        self.app_settings["current_llm_model_identifier"] = all_settings.get("current_llm_model_identifier", self.app_settings["current_llm_model_identifier"])

        logger.info(f"Paramètres de l'application chargés: max_context_tokens={self.app_settings['max_context_tokens']}")

        if self.app_settings.get("window_geometry"):
            try:
                self.restoreGeometry(QByteArray.fromHex(self.app_settings["window_geometry"].encode()))
                logger.info("Géométrie de la fenêtre restaurée.")
            except Exception as e:
                logger.warning(f"Impossible de restaurer la géométrie de la fenêtre: {e}")

        if self.app_settings.get("main_splitter_sizes"):
            self.main_splitter.setSizes(self.app_settings["main_splitter_sizes"])
            logger.info("Tailles du splitter principal restaurées.")

        self.restore_selections_action.setChecked(self.app_settings["restore_selections_on_startup"])
        
        generation_panel_settings = all_settings.get("generation_panel", {})
        self.generation_panel.load_settings(generation_panel_settings)
        logger.info("Paramètres du GenerationPanel chargés.")

        if self.app_settings["restore_selections_on_startup"]:
            left_panel_settings = all_settings.get("left_selection_panel", {})
            self.left_panel.load_settings(left_panel_settings)
            logger.info("Paramètres du LeftSelectionPanel chargés.")
        else:
            logger.info("Restauration des sélections du LeftSelectionPanel désactivée. Effacement des sélections précédentes.")
            self.left_panel.load_settings({}) # Charge un dictionnaire vide pour effacer les sélections

        saved_llm_model_id_ui = generation_panel_settings.get("llm_model", self.app_settings["current_llm_model_identifier"]) # Utilise celui de app_settings comme fallback
        config_default_llm_model_id = self.llm_config.get("default_model_identifier", "dummy")
        final_model_to_set = saved_llm_model_id_ui or config_default_llm_model_id

        if final_model_to_set != (self.llm_client.model_identifier if self.llm_client and hasattr(self.llm_client, 'model_identifier') else None):
            logger.info(f"Synchronisation du client LLM avec le modèle: {final_model_to_set} après chargement des settings.")
            self._on_llm_model_selected_from_panel(final_model_to_set, from_load_settings=True)
        else:
            self.generation_panel.select_model_in_combo(final_model_to_set)

        logger.info("Paramètres UI chargés.")

    def _save_ui_settings(self, source: str):
        """Sauvegarde les paramètres UI courants."""
        # Utiliser les valeurs de self.app_settings et les mettre à jour si nécessaire avant de sauvegarder
        self.app_settings["window_geometry"] = self.saveGeometry().toHex().data().decode()
        self.app_settings["main_splitter_sizes"] = self.main_splitter.sizes()
        self.app_settings["generation_panel_splitter_sizes"] = self.generation_panel.main_splitter.sizes() if hasattr(self.generation_panel, 'main_splitter') else []
        self.app_settings["restore_selections_on_startup"] = self.restore_selections_action.isChecked()
        # max_context_tokens est déjà dans self.app_settings, il sera sauvegardé.
        # current_llm_model_identifier est aussi dans self.app_settings, mis à jour par _on_llm_model_selected_from_panel

        settings_to_save = {
            "window_geometry": self.app_settings["window_geometry"],
            "main_splitter_sizes": self.app_settings["main_splitter_sizes"],
            "generation_panel_splitter_sizes": self.app_settings["generation_panel_splitter_sizes"],
            "restore_selections_on_startup": self.app_settings["restore_selections_on_startup"],
            "max_context_tokens": self.app_settings.get("max_context_tokens", 1500), # Assurer une valeur par défaut
            "current_llm_model_identifier": self.app_settings.get("current_llm_model_identifier"),
            "generation_panel": self.generation_panel.get_settings(),
            "left_selection_panel": self.left_panel.get_settings()
        }
        
        try:
            with open(UI_SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings_to_save, f, indent=4)
            logger.info(f"Paramètres UI sauvegardés dans {UI_SETTINGS_FILE} (source: {source}).")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des paramètres UI dans {UI_SETTINGS_FILE}: {e}")
            self.statusBar().showMessage(f"Erreur de sauvegarde des paramètres: {e}")

    def _perform_actual_save_ui_settings(self):
        self._save_ui_settings(source="timer_or_event")

    def _schedule_save_ui_settings(self):
        # Démarre ou redémarre le timer pour sauvegarder les paramètres après un délai.
        self.save_settings_timer.start(self.save_settings_delay_ms)

    def _connect_signals_for_auto_save(self):
        # Connecter les signaux des panneaux qui indiquent un changement de paramètre pertinent.
        self.left_panel.context_selection_changed.connect(self._schedule_save_ui_settings)
        self.generation_panel.settings_changed.connect(self._schedule_save_ui_settings)
        
        # Ajouter une connexion pour mettre à jour l'estimation des tokens quand le contexte change
        self.left_panel.context_selection_changed.connect(self._trigger_context_changed_token_update)
        
        # Ajouter d'autres signaux si nécessaire, par ex. de ConfigDialog si les paramètres LLM sont modifiés.
        logger.info("Signaux connectés pour la sauvegarde automatique des paramètres UI.")
    
    def _trigger_context_changed_token_update(self):
        """Déclenche la mise à jour de l'estimation des tokens quand le contexte change."""
        # Légère pause pour laisser le temps aux widgets de se mettre à jour
        QTimer.singleShot(50, self.generation_panel._trigger_token_update)
        logger.debug("Mise à jour des tokens programmée suite à changement de contexte.")

    def get_current_llm_model_properties(self) -> Optional[dict]:
        """Récupère les propriétés du modèle LLM actuellement sélectionné."""
        current_model_identifier = None
        if self.llm_client and hasattr(self.llm_client, 'model_identifier') and self.llm_client.model_identifier:
            current_model_identifier = self.llm_client.model_identifier
        elif self.llm_client and hasattr(self.llm_client, 'model') and self.llm_client.model: # Ancien attribut possible
             current_model_identifier = self.llm_client.model
        else: # Fallback sur ce qui est dans la config si le client n'a pas l'info directement
            current_model_identifier = self.generation_panel.llm_model_combo.currentData()
            if not current_model_identifier and self.available_llm_models: # Si rien dans combo, prendre le premier dispo
                current_model_identifier = self.available_llm_models[0].get("api_identifier")

        if not current_model_identifier:
            logger.warning("Impossible de déterminer l'identifiant du modèle LLM actuel pour récupérer ses propriétés.")
            return None

        for model_props in self.available_llm_models:
            if model_props.get("api_identifier") == current_model_identifier:
                logger.debug(f"Propriétés trouvées pour le modèle LLM '{current_model_identifier}': {model_props}")
                return model_props
        
        logger.warning(f"Aucune propriété trouvée pour le modèle LLM '{current_model_identifier}' dans available_llm_models.")
        return None

    def closeEvent(self, close_event: QCloseEvent):
        """Overrides closeEvent to save settings before exiting.

        Args:
            close_event: The close event.
        """
        self._save_ui_settings(source="event")
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
    def _on_llm_model_selected_from_panel(self, new_model_identifier: str, from_load_settings: bool = False):
        logger.info(f"LLM model selection changed from panel to: {new_model_identifier}")
        
        if self.llm_client and hasattr(self.llm_client, 'model') and self.llm_client.model == new_model_identifier and not from_load_settings:
            logger.debug(f"LLM model unchanged (already {new_model_identifier}), skipping client recreation.")
            return

        # Mise à jour de l'app_settings avant de recharger le client
        self.app_settings["current_llm_model_identifier"] = new_model_identifier
        
        # Attempt to initialize the client with the new model
        try:
            # Get API key env var from config
            api_key_var = self.llm_config.get("api_key_env_var", "OPENAI_API_KEY")
            
            # Create a new client with the selected model
            new_client = OpenAIClient(model_identifier=new_model_identifier, api_key_env_var=api_key_var)
            
            # If successful, update our reference and inform GP
            self.llm_client = new_client
            self.generation_panel.set_llm_client(new_client)
            logger.info(f"LLM Client updated with model: {new_model_identifier}")
            
            if not from_load_settings: # Avoid feedback loop on startup
                self._save_ui_settings("llm_model_change") 
                
        except Exception as e:
            logger.error(f"Failed to initialize LLM client with model {new_model_identifier}: {e}")
            QMessageBox.critical(self, "LLM Error", f"Could not initialize LLM client with model {new_model_identifier}: {e}")
            # We don't fall back to dummy here since we already have a working client.
            # Just notify the user and keep using the current client.
            # Optionally reset the UI selection to match the current client.
            if self.llm_client and hasattr(self.llm_client, 'model'):
                self.generation_panel.select_model_in_combo(self.llm_client.model)

    def get_unity_dialogues_path(self) -> Optional[Path]:
        """
        Retourne le chemin des dialogues Unity.
        Utilise config_manager.get_unity_dialogues_path() pour récupérer le chemin.
        
        Returns:
            Optional[Path]: Le chemin des dialogues Unity, ou None si non configuré ou invalide.
        """
        logger.debug("MainWindow.get_unity_dialogues_path appelé")
        return config_manager.get_unity_dialogues_path()

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