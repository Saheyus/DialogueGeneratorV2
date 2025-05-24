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
# from .generation_panel_base import GenerationPanel # New import # MODIFIÉ: Commenté
from .generation_panel_main import GenerationPanel # MODIFIÉ: Ajout de cet import
# from .config_dialog import ConfigDialog  # Assuming ConfigDialog is in ui package -> Fichier manquant, commenté
from .utils import get_icon_path # Assurez-vous que utils.py et get_icon_path existent

# Imports from the parent 'DialogueGenerator' package
from ..context_builder import ContextBuilder 
from ..llm_client import OpenAIClient, DummyLLMClient, ILLMClient 
from ..prompt_engine import PromptEngine 
from ..services.configuration_service import ConfigurationService # MODIFIÉ: Ajouter ConfigurationService
from ..services.llm_service import LLMService # MODIFIÉ: Ajouter LLMService
from ..services.linked_selector import LinkedSelectorService # Example if needed elsewhere
from ..services.interaction_service import InteractionService # Importation ajoutée
from ..services.repositories import FileInteractionRepository # Pour l'InteractionService
from ..models.dialogue_structure.interaction import Interaction # Importation pour le type hint

# Path to the DialogueGenerator directory
DIALOGUE_GENERATOR_DIR = Path(__file__).resolve().parent.parent
# Définir le chemin de stockage par défaut pour les interactions
DEFAULT_INTERACTIONS_STORAGE_DIR = DIALOGUE_GENERATOR_DIR / "data" / "interactions"

# MODIFIÉ: Supprimer les constantes de chemin de configuration, elles sont dans ConfigurationService
# UI_SETTINGS_FILE = DIALOGUE_GENERATOR_DIR / "ui_settings.json" 
# CONTEXT_CONFIG_FILE_PATH = DIALOGUE_GENERATOR_DIR / "context_config.json"
# LLM_CONFIG_FILE_PATH = DIALOGUE_GENERATOR_DIR / "llm_config.json" 

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
        self.config_service = ConfigurationService()
        self.llm_service = LLMService() # MODIFIÉ: Initialiser LLMService

        self.current_selected_gdd_item_id: Optional[str] = None 
        self.current_selected_gdd_category: Optional[str] = None
        self.current_gdd_item_data: Optional[dict] = None 

        # MODIFIÉ: Supprimer self.app_settings, les valeurs sont gérées via config_service
        # ou directement avec QSettings pour la géométrie/splitters.
        
        self.prompt_engine: Optional[PromptEngine] = None
        # self.llm_config et self.available_llm_models sont initialisés par _load_llm_configuration
        
        interactions_repo = FileInteractionRepository(storage_dir=str(DEFAULT_INTERACTIONS_STORAGE_DIR)) 
        self.interaction_service = InteractionService(repository=interactions_repo)
        logger.info(f"InteractionService initialisé avec {type(interactions_repo).__name__} sur {DEFAULT_INTERACTIONS_STORAGE_DIR}.")
        
        self._initialize_llm_system()

        self.prompt_engine = PromptEngine()

        self.setWindowTitle("DialogueGenerator IA - Context Builder")
        self.setWindowIcon(get_icon_path("icon.png"))
        self.setGeometry(100, 100, 1600, 900) # Default size

        self._create_actions()
        self._create_menu_bar()

        self.left_panel = LeftSelectionPanel(context_builder=self.context_builder, 
                                           interaction_service=self.interaction_service, # Passer le service
                                           parent=self)
        self.details_panel = DetailsPanel(parent=self) # Instantiate DetailsPanel
        
        # MODIFIÉ: Passer le client LLM depuis le service
        initial_llm_client = self.llm_service.get_current_client()
        initial_llm_model_id = self.config_service.get_ui_setting(
            "current_llm_model_identifier", 
            self.llm_service.get_default_model_identifier() # MODIFIÉ: Utiliser llm_service
        )

        self.generation_panel = GenerationPanel(
            context_builder=self.context_builder, 
            prompt_engine=self.prompt_engine, 
            llm_client=initial_llm_client, # MODIFIÉ: Passer le client du service
            available_llm_models=self.llm_service.get_available_models(), # MODIFIÉ: Utiliser llm_service
            current_llm_model_identifier=initial_llm_model_id, 
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

        # Connexion du signal pour la sélection du dialogue précédent
        self.left_panel.previous_interaction_context_selected.connect(self._on_previous_interaction_selected)

    def _create_actions(self):
        """Creates actions for the menus."""
        self.restore_selections_action = QAction("Restore selections on startup", self)
        self.restore_selections_action.setCheckable(True)
        # MODIFIÉ: Charger la valeur depuis config_service
        self.restore_selections_action.setChecked(
            self.config_service.get_ui_setting("restore_selections_on_startup", True)
        )

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
        # MODIFIÉ: Utiliser la méthode du service pour obtenir le chemin
        context_file_to_open = self.config_service.get_context_config_file_path()

        if context_file_to_open.exists():
            try:
                webbrowser.open(os.path.realpath(context_file_to_open))
                logger.info(f"Attempting to open {context_file_to_open}")
            except Exception as e:
                logger.error(f"Could not open {context_file_to_open}: {e}")
                self.statusBar().showMessage(f"Error: Could not open configuration file: {e}")
        else:
            logger.warning(f"Configuration file {context_file_to_open} does not exist.")
            self.statusBar().showMessage("Error: Context configuration file not found.")

    def _configure_unity_dialogues_path(self):
        """Ouvre une boîte de dialogue pour configurer le chemin des dialogues Unity."""
        # MODIFIÉ: Utiliser ConfigurationService
        current_path = self.config_service.get_unity_dialogues_path()
        current_path_str = str(current_path) if current_path else ""
        
        new_path_str = QFileDialog.getExistingDirectory(
            self,
            "Sélectionner le dossier des dialogues Unity",
            current_path_str
        )
        
        if new_path_str:  
            if self.config_service.set_unity_dialogues_path(new_path_str): # MODIFIÉ
                logger.info(f"Chemin des dialogues Unity configuré: {new_path_str}")
                self.statusBar().showMessage(f"Chemin des dialogues Unity configuré: {new_path_str}", 5000)
                
                if hasattr(self.left_panel, 'populate_yarn_files_list'):
                    self.left_panel.populate_yarn_files_list() # Ceci devra utiliser le service aussi
            else:
                logger.error(f"Échec de la configuration du chemin des dialogues Unity: {new_path_str}")
                # Afficher une QMessageBox pour plus de visibilité
                QMessageBox.warning(self, "Erreur Configuration", 
                                    f"Le chemin '{new_path_str}' n'a pas pu être configuré. "
                                    "Vérifiez les permissions et que le chemin est valide.")
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
                max_tokens=self.config_service.get_ui_setting("max_context_tokens", 1500), # Utiliser config_service
                include_dialogue_type=include_dialogue_type_flag
            )
            context_token_count = self.context_builder._count_tokens(context_string)

            generation_parameters = {} 
            
            estimated_full_prompt_text, estimated_total_token_count = self.prompt_engine.build_prompt(
                context_summary=context_string, 
                user_specific_goal=user_instructions,
                generation_params=generation_parameters
            )
            
            # Mettre à jour l'affichage du prompt estimé dans le GenerationPanel
            if estimated_full_prompt_text and hasattr(self.generation_panel, '_display_prompt_in_tab'):
                self.generation_panel._display_prompt_in_tab(estimated_full_prompt_text)
                logger.debug("Prompt estimé mis à jour dans GenerationPanel.")
            
            # Mettre à jour l'affichage des tokens si la méthode existe
            if hasattr(self.generation_panel, 'update_token_counts_display'):
                self.generation_panel.update_token_counts_display(context_token_count, estimated_total_token_count)
            
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
        """Charge les paramètres UI sauvegardés en utilisant ConfigurationService et QSettings."""
        logger.info(f"Chargement des paramètres UI via ConfigurationService.")
        
        # Charger tous les paramètres gérés par ConfigurationService (hors QSettings directs)
        loaded_app_settings = self.config_service.get_all_ui_settings()

        # 1. Restaurer les paramètres gérés par QSettings (géométrie, splitters)
        # Ces valeurs sont lues depuis le fichier par ConfigurationService, puis appliquées ici.
        window_geometry_hex = loaded_app_settings.get("window_geometry")
        if window_geometry_hex:
            try:
                self.restoreGeometry(QByteArray.fromHex(window_geometry_hex.encode()))
                logger.info("Géométrie de la fenêtre restaurée.")
            except Exception as e:
                logger.warning(f"Impossible de restaurer la géométrie de la fenêtre: {e}")

        main_splitter_sizes = loaded_app_settings.get("main_splitter_sizes")
        if main_splitter_sizes:
            self.main_splitter.setSizes(main_splitter_sizes)
            logger.info("Tailles du splitter principal restaurées.")
        
        # generation_panel_splitter_sizes est généralement dans les settings du panel lui-même.
        # Si GenerationPanel a son propre splitter, il le restaurera via son load_settings.

        # 2. Restaurer les autres paramètres applicatifs
        restore_selections = loaded_app_settings.get("restore_selections_on_startup", True)
        self.restore_selections_action.setChecked(restore_selections)
        
        # max_context_tokens est utilisé par ContextBuilder, généralement pas directement par MainWindow UI
        # Il est chargé par ConfigurationService et accessible via config_service.get_ui_setting("max_context_tokens")
        # si un composant en a besoin.
        # logger.info(f"Paramètre 'max_context_tokens' chargé: {self.config_service.get_ui_setting('max_context_tokens')}")

        # 3. Charger les paramètres des panneaux enfants
        generation_panel_settings_loaded = loaded_app_settings.get("generation_panel", {})
        self.generation_panel.load_settings(generation_panel_settings_loaded)
        logger.info("Paramètres du GenerationPanel chargés.")

        if restore_selections:
            left_panel_settings_loaded = loaded_app_settings.get("left_selection_panel", {})
            self.left_panel.load_settings(left_panel_settings_loaded)
            logger.info("Paramètres du LeftSelectionPanel chargés (restauration active).")
        else:
            self.left_panel.load_settings({}) # Effacer les sélections
            logger.info("Restauration des sélections du LeftSelectionPanel désactivée.")

        # 4. Synchroniser le modèle LLM
        # current_llm_model_identifier est prioritaire depuis les settings du generation_panel, sinon ui_settings global, sinon défaut config LLM
        current_llm_id_from_gen_panel = generation_panel_settings_loaded.get("llm_model")
        current_llm_id_global = loaded_app_settings.get("current_llm_model_identifier")
        # MODIFIÉ: Utiliser llm_service pour le défaut
        config_default_llm_id = self.llm_service.get_default_model_identifier() 
        
        final_model_to_set = current_llm_id_from_gen_panel or current_llm_id_global or config_default_llm_id

        # Comparer avec le modèle actuel du client LLM du service
        current_client_model_id = None
        # MODIFIÉ: Accéder au client via le service
        service_client = self.llm_service.get_current_client()
        if service_client:
            if hasattr(service_client, 'model_identifier') and service_client.model_identifier:
                current_client_model_id = service_client.model_identifier
            elif hasattr(service_client, 'model') and service_client.model: # Ancien attribut possible
                current_client_model_id = service_client.model

        if final_model_to_set != current_client_model_id:
            logger.info(f"Synchronisation du client LLM (via service) avec le modèle: '{final_model_to_set}' après chargement des settings.")
            self._on_llm_model_selected_from_panel(final_model_to_set, from_load_settings=True)
        elif self.generation_panel.llm_model_combo.currentData() != final_model_to_set: 
            self.generation_panel.select_model_in_combo(final_model_to_set)
            logger.info(f"Combobox LLM synchronisée sur '{final_model_to_set}'.")

        logger.info("Tous les paramètres UI pertinents ont été chargés et appliqués.")

    def _save_ui_settings(self, source: str):
        """Sauvegarde les paramètres UI courants en utilisant ConfigurationService."""
        logger.debug(f"Début de _save_ui_settings (source: {source})")

        # 1. Mettre à jour les valeurs dans ConfigurationService avant de sauvegarder
        # Paramètres gérés par QSettings (directement ou indirectement)
        self.config_service.update_ui_setting("window_geometry", self.saveGeometry().toHex().data().decode())
        self.config_service.update_ui_setting("main_splitter_sizes", self.main_splitter.sizes())
        
        # Paramètres applicatifs globaux
        self.config_service.update_ui_setting("restore_selections_on_startup", self.restore_selections_action.isChecked())
        
        # current_llm_model_identifier est mis à jour dans _on_llm_model_selected_from_panel
        # Si GenerationPanel a son propre mécanisme pour stocker le modèle sélectionné (get_settings),
        # il sera pris en compte ci-dessous. Sinon, s'assurer qu'il est bien dans config_service.
        # Par sécurité, on peut le remettre ici depuis une source fiable si ce n'est pas déjà fait par un signal.
        if self.generation_panel and hasattr(self.generation_panel, 'get_current_selected_model_identifier'):
             current_model_id_for_save = self.generation_panel.get_current_selected_model_identifier()
             if current_model_id_for_save:
                 self.config_service.update_ui_setting("current_llm_model_identifier", current_model_id_for_save)

        # Paramètres des panneaux enfants
        if hasattr(self.generation_panel, 'get_settings'):
            self.config_service.update_ui_setting("generation_panel", self.generation_panel.get_settings())
        else:
            logger.warning("GenerationPanel n'a pas de méthode get_settings pour sauvegarder ses paramètres.")
            # On pourrait vouloir sauvegarder le splitter du generation_panel s'il est géré ici
            if hasattr(self.generation_panel, 'main_splitter'): 
                 self.config_service.update_ui_setting("generation_panel_splitter_sizes", self.generation_panel.main_splitter.sizes())

        if hasattr(self.left_panel, 'get_settings'):
            self.config_service.update_ui_setting("left_selection_panel", self.left_panel.get_settings())
        else:
            logger.warning("LeftSelectionPanel n'a pas de méthode get_settings.")

        # max_context_tokens: Si modifiable par l'UI (par exemple dans GenerationPanel),
        # il faudrait le récupérer ici. Sinon, il est juste lu depuis config.
        # Exemple: max_tokens = self.generation_panel.get_max_tokens_setting()
        # self.config_service.update_ui_setting("max_context_tokens", max_tokens)

        # 2. Sauvegarder tous les paramètres via le service
        if self.config_service.save_ui_settings():
            logger.info(f"Paramètres UI sauvegardés avec succès via ConfigurationService (source: {source}).")
        else:
            logger.error(f"Échec de la sauvegarde des paramètres UI via ConfigurationService (source: {source}).")
            self.statusBar().showMessage("Erreur de sauvegarde des paramètres UI.")

    def _perform_actual_save_ui_settings(self):
        self._save_ui_settings(source="timer_or_event_ended") # Clarifier la source

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
        # Relance le timer à chaque changement de contexte pertinent.
        self.token_update_timer.start(500) # Délai de 500ms pour regrouper les changements rapides

    @Slot(str, list)
    def _on_previous_interaction_selected(self, interaction_id: str, path_interactions: List[Interaction]):
        """Slot appelé lorsque l'utilisateur sélectionne une interaction précédente pour le contexte."""
        logger.info(f"MainWindow: Contexte de dialogue précédent sélectionné - ID: {interaction_id}")
        # logger.info(f"Chemin de dialogue ({len(path_interactions)} interactions):")
        # for i, inter in enumerate(path_interactions):
        #     logger.info(f"  {i+1}. {inter.title or '(Sans titre)'} (ID: {inter.interaction_id})")
        
        # Passer l'information au ContextBuilder
        if self.context_builder:
            self.context_builder.set_previous_dialogue_context(path_interactions)
            logger.info(f"ContextBuilder informé du contexte de dialogue précédent ({len(path_interactions)} interaction(s)).")
        else:
            logger.warning("ContextBuilder non disponible, impossible de définir le contexte de dialogue précédent.")
        
        # Afficher un message dans la barre de statut
        if path_interactions:
            final_title = path_interactions[-1].title or "(Sans titre)"
            self.statusBar().showMessage(f"Contexte de continuité: '{final_title}' (ID: {interaction_id[:8]}...) sélectionné.", 10000)
        else: # Si path_interactions est vide ou None (ne devrait pas arriver si interaction_id est valide)
            self.statusBar().showMessage(f"Contexte de continuité: Réinitialisé.", 5000)
            if self.context_builder: # S'assurer de réinitialiser aussi dans ce cas
                 self.context_builder.set_previous_dialogue_context(None)
        
        # Mettre à jour l'estimation des tokens car le contexte a changé
        self._trigger_context_changed_token_update()

    def get_current_llm_model_properties(self) -> Optional[dict]:
        """Renvoie les propriétés du modèle LLM actuellement sélectionné via LLMService."""
        # MODIFIÉ: Utiliser llm_service
        current_client = self.llm_service.get_current_client()
        if not current_client:
            logger.warning("LLMService n'a pas de client actuel.")
            return None

        current_model_identifier = None
        if hasattr(current_client, 'model_identifier') and current_client.model_identifier:
            current_model_identifier = current_client.model_identifier
        elif hasattr(current_client, 'model') and current_client.model: # Ancien attribut possible
             current_model_identifier = current_client.model
        
        if not current_model_identifier:
            # Fallback si le client n'a pas l'info directement, essayer la config du service
            current_model_identifier = self.llm_service.get_llm_setting("default_model_identifier")
            # Ou celui sélectionné dans le panneau de génération s'il est différent
            if self.generation_panel and self.generation_panel.llm_model_combo.currentData():
                current_model_identifier = self.generation_panel.llm_model_combo.currentData()

        if not current_model_identifier:
            logger.warning("Impossible de déterminer l'identifiant du modèle LLM actuel pour récupérer ses propriétés via LLMService.")
            return None

        # MODIFIÉ: Utiliser llm_service
        for model_props in self.llm_service.get_available_models():
            if model_props.get("api_identifier") == current_model_identifier:
                logger.debug(f"Propriétés trouvées pour le modèle LLM '{current_model_identifier}': {model_props}")
                return model_props
        
        logger.warning(f"Aucune propriété trouvée pour le modèle LLM '{current_model_identifier}' dans LLMService.available_models.")
        return None

    def closeEvent(self, close_event: QCloseEvent):
        """Overrides closeEvent to save settings before exiting.

        Args:
            close_event: The close event.
        """
        self._save_ui_settings(source="event")
        super().closeEvent(close_event)

    def _initialize_llm_system(self):
        """Initializes the LLM client and related attributes using LLMService."""
        # LLMService est déjà initialisé dans __init__
        # La configuration LLM (self.llm_config, self.available_llm_models) est chargée par LLMService
        # lors de son initialisation.
        
        # Récupérer le client LLM initial (probablement le modèle par défaut ou le dernier sauvegardé si géré par le service)
        # Si `get_current_client` crée le client s'il n'existe pas, c'est parfait.
        self.llm_client = self.llm_service.get_current_client()
        
        if not self.llm_client:
            # Ce cas ne devrait pas arriver si LLMService._ensure_config_defaults et get_current_client fonctionnent
            logger.critical("LLMService failed to provide an initial LLM client! Application might not function correctly.")
            QMessageBox.critical(self, "LLM Critical Error", "LLM Service could not initialize a client.")
            # Fallback très basique si tout a échoué, bien que LLMService devrait déjà faire un fallback sur Dummy
            self.llm_client = DummyLLMClient()
            self.llm_service.current_client = self.llm_client # Assurer la cohérence
        else:
            logger.info(f"Initial LLM client obtained from LLMService: {type(self.llm_client).__name__}")

        # self.llm_config et self.available_llm_models sont maintenant des propriétés de llm_service
        # On ne les stocke plus directement dans MainWindow.
        # Si des parties du code y accèdent encore directement, elles devront passer par self.llm_service.get_llm_config() ou get_available_models()

    @Slot(str) 
    def _on_llm_model_selected_from_panel(self, new_model_identifier: str, from_load_settings: bool = False):
        """Slot appelé lorsque le modèle LLM est changé depuis GenerationPanel.
        Utilise LLMService pour changer de client.
        """
        logger.info(f"Modèle LLM sélectionné: {new_model_identifier} (Depuis chargement settings: {from_load_settings})")

        if not new_model_identifier:
            logger.warning("Aucun identifiant de modèle LLM fourni. Sélection annulée.")
            return

        # MODIFIÉ: Utiliser llm_service pour changer de modèle et obtenir le client
        new_client = self.llm_service.switch_model(new_model_identifier)
        
        if new_client:
            self.llm_client = new_client # Mettre à jour la référence locale de MainWindow
            logger.info(f"Client LLM actif mis à jour dans MainWindow: {type(self.llm_client).__name__} pour modèle '{new_model_identifier}'.")
            self.generation_panel.set_llm_client(self.llm_client)
            
            # Sauvegarder l'identifiant du modèle dans les paramètres UI via ConfigurationService
            self.config_service.update_ui_setting("current_llm_model_identifier", new_model_identifier)
            if not from_load_settings: 
                self._schedule_save_ui_settings()
        else:
            # LLMService.switch_model gère déjà les erreurs et le fallback vers Dummy si nécessaire.
            # Il devrait retourner le client Dummy dans ce cas.
            # Si new_client est None, c'est un cas inattendu.
            logger.error(f"LLMService.switch_model n'a pas retourné de client pour '{new_model_identifier}'. Utilisation du client existant ou Dummy.")
            # S'assurer que generation_panel a un client valide (au pire, le précédent ou un nouveau Dummy)
            if not self.llm_service.get_current_client(): # Si le service n'a plus de client
                self.llm_service.create_client() # Forcer la création d'un (dummy par défaut)
            self.llm_client = self.llm_service.get_current_client()
            self.generation_panel.set_llm_client(self.llm_client)
            QMessageBox.warning(self, "Erreur LLM", f"Impossible de basculer vers le modèle LLM '{new_model_identifier}'. Vérifiez la configuration.")

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