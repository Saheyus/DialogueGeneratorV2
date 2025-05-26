import pathlib
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QGridLayout, 
                               QLabel, QComboBox, QTextEdit, QPushButton, 
                               QTabWidget, QLineEdit, QCheckBox, QHBoxLayout, QApplication, QSizePolicy, QProgressBar, QScrollArea, QSplitter, QFrame, QPlainTextEdit, QMessageBox, QSpacerItem, QMenu, QStyle, QSpinBox, QDoubleSpinBox)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QPalette, QColor, QFont, QIcon, QAction
import logging # Added for logging
import asyncio # Added for asynchronous tasks
from typing import Optional, Callable, Any, List # Added List
import json # Ajout pour charger la config LLM potentiellement ici aussi si besoin
from pathlib import Path
import uuid
import sys
import os

from models.dialogue_structure.interaction import Interaction
from services.interaction_service import InteractionService
from services.repositories.file_repository import FileInteractionRepository
from constants import UIText, FilePaths, Defaults
from services.dialogue_generation_service import DialogueGenerationService

# Import local de la fonction utilitaire
from .utils import get_icon_path
# Ajout de l'import du nouveau widget extrait
from .generation_panel.scene_selection_widget import SceneSelectionWidget
from .generation_panel.context_actions_widget import ContextActionsWidget
from .generation_panel.generation_params_widget import GenerationParamsWidget
from .generation_panel.instructions_widget import InstructionsWidget
from .generation_panel.token_estimation_actions_widget import TokenEstimationActionsWidget
from .generation_panel.generated_variants_tabs_widget import GeneratedVariantsTabsWidget
from .generation_panel.interactions_tab_widget import InteractionsTabWidget
from .generation_panel.dialogue_structure_widget import DialogueStructureWidget
from .generation_panel.dialogue_generation_handler import DialogueGenerationHandler # Ajouté
from .generation_panel.handlers import handle_select_linked_elements, handle_unlink_unrelated, handle_uncheck_all

# New service import
try:
    from services.linked_selector import LinkedSelectorService
    from services.yarn_renderer import JinjaYarnRenderer
    from llm_client import OpenAIClient, DummyLLMClient
except ImportError:
    # Support exécution directe
    current_dir = pathlib.Path(__file__).resolve().parent.parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    from services.linked_selector import LinkedSelectorService
    from services.yarn_renderer import JinjaYarnRenderer
    from llm_client import OpenAIClient, DummyLLMClient

logger = logging.getLogger(__name__) # Added logger

# Chemin vers le fichier de configuration LLM, au cas où GenerationPanel aurait besoin de le lire directement
# Bien que la liste des modèles soit passée par MainWindow, cela pourrait servir pour d'autres settings.
DIALOGUE_GENERATOR_DIR = Path(__file__).resolve().parent.parent
LLM_CONFIG_FILE_PATH = DIALOGUE_GENERATOR_DIR / "llm_config.json"
# Dossier par défaut pour stocker les interactions
DEFAULT_INTERACTIONS_DIR = DIALOGUE_GENERATOR_DIR / "data" / "interactions"

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
    generation_finished = Signal(bool) # True pour succès (variantes ajoutées), False en cas d'erreur majeure avant ajout
    llm_model_selection_changed = Signal(str) # Émis lorsque l'utilisateur sélectionne un nouveau modèle LLM

    def __init__(self, context_builder, prompt_engine, llm_client, available_llm_models, current_llm_model_identifier, main_window_ref, dialogue_generation_service, parent=None):
        """Initializes the GenerationPanel.

        Args:
            context_builder: Instance of ContextBuilder to access GDD data (e.g., character names,
                             location names, linked elements) and to build context strings.
            prompt_engine: Instance of PromptEngine to construct the final prompt for the LLM.
            llm_client: Instance of an LLMClient (e.g., OpenAIClient or DummyLLMClient) to generate text.
            available_llm_models: List of available LLM models.
            current_llm_model_identifier: Identifier of the current LLM model.
            main_window_ref: Reference to the MainWindow, used for accessing shared functionalities
                             like the status bar, or methods like _get_current_context_selections and
                             _update_token_estimation_and_prompt_display.
            dialogue_generation_service: Instance of DialogueGenerationService.
            parent: The parent widget.
        """
        super().__init__(parent)
        
        self.context_builder = context_builder
        self.prompt_engine = prompt_engine
        self.llm_client = llm_client
        self.main_window_ref = main_window_ref
        self.linked_selector = LinkedSelectorService(self.context_builder)
        self.yarn_renderer = JinjaYarnRenderer()
        
        # Initialisation de interaction_service ici pour qu'il soit dispo dans _init_ui
        interactions_dir = DEFAULT_INTERACTIONS_DIR
        os.makedirs(interactions_dir, exist_ok=True)
        self.interaction_repository = FileInteractionRepository(str(interactions_dir))
        self.interaction_service = InteractionService(repository=self.interaction_repository)

        self.dialogue_generation_service = dialogue_generation_service
        if not self.dialogue_generation_service:
            logger.error("DialogueGenerationService non fourni à GenerationPanel!")

        # Initialisation du Handler de génération
        self.generation_handler = DialogueGenerationHandler(
            llm_client=self.llm_client, 
            dialogue_generation_service=self.dialogue_generation_service,
            parent=self  # QObject parent pour la gestion de la mémoire
        )

        self.available_llm_models = available_llm_models if available_llm_models else []
        self.current_llm_model_identifier = current_llm_model_identifier

        # Pour éviter les signaux inutiles pendant le chargement 
        self._is_settings_loading = False
        self._is_loading_settings = False  # Flag pour éviter les signaux pendant le chargement
        
        self._init_ui()
        # finalize_ui_setup() est appelé par MainWindow

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)

        left_column_widget = QWidget()
        left_column_layout = QVBoxLayout(left_column_widget)
        left_column_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_splitter.addWidget(left_column_widget)

        # Onglets central
        central_tabs = QTabWidget()
        left_column_layout.addWidget(central_tabs)
        
        generation_tab = QWidget()
        generation_tab_layout = QVBoxLayout(generation_tab)
        generation_tab_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 1. Initialisation de TOUS les widgets de section
        self.scene_selection_widget = SceneSelectionWidget(self.context_builder)
        self.context_actions_widget = ContextActionsWidget()
        self.generation_params_widget = GenerationParamsWidget(
            self.available_llm_models,
            self.current_llm_model_identifier
        )
        self.dialogue_structure_widget = DialogueStructureWidget()
        self.instructions_widget = InstructionsWidget()
        self.token_actions_widget = TokenEstimationActionsWidget()
        self.variants_display_widget = GeneratedVariantsTabsWidget() # Doit être ici pour l'alias plus bas

        # Ajout des widgets au layout de l'onglet Génération
        generation_tab_layout.addWidget(self.scene_selection_widget)
        generation_tab_layout.addWidget(self.context_actions_widget)
        generation_tab_layout.addWidget(self.generation_params_widget)
        generation_tab_layout.addWidget(self.dialogue_structure_widget)
        generation_tab_layout.addWidget(self.instructions_widget)
        generation_tab_layout.addWidget(self.token_actions_widget)
        generation_tab_layout.addStretch(1)
        central_tabs.addTab(generation_tab, "Génération")

        # --- Onglet Interactions (initialisation inchangée pour l'instant) ---
        self.interactions_tab_content_widget = InteractionsTabWidget(self.interaction_service)
        central_tabs.addTab(self.interactions_tab_content_widget, "Interactions")

        # Colonne de Droite (inchangée, variants_display_widget déjà initialisé)
        right_column_widget = QWidget()
        right_column_layout = QVBoxLayout(right_column_widget)
        right_column_layout.setContentsMargins(0,0,0,0)
        main_splitter.addWidget(right_column_widget)
        right_column_layout.addWidget(self.variants_display_widget)
        
        # 2. Création de TOUS les alias APRÈS l'initialisation des widgets enfants
        self.llm_model_combo = self.generation_params_widget.llm_model_combo
        self.k_variants_combo = self.generation_params_widget.k_variants_combo
        self.max_context_tokens_spinbox = self.generation_params_widget.max_context_tokens_spinbox
        self.structured_output_checkbox = self.generation_params_widget.structured_output_checkbox # Même si supprimé logiquement, l'alias peut exister
        self.token_estimation_label = self.token_actions_widget.token_estimation_label
        self.generation_progress_bar = self.token_actions_widget.generation_progress_bar
        self.generate_dialogue_button = self.token_actions_widget.generate_dialogue_button
        self.refresh_token_button = self.token_actions_widget.refresh_token_button
        self.variant_display_tabs = self.variants_display_widget # Alias correct

        # 3. Connexion des signaux des widgets et des alias
        # Signaux des widgets de section
        self.scene_selection_widget.character_a_changed.connect(self._schedule_settings_save_and_token_update)
        self.scene_selection_widget.character_b_changed.connect(self._schedule_settings_save_and_token_update)
        self.scene_selection_widget.scene_region_changed.connect(self._schedule_settings_save_and_token_update) # Le widget gère la mise à jour des sous-lieux
        self.scene_selection_widget.scene_sub_location_changed.connect(self._schedule_settings_save_and_token_update)
        # swap_characters_clicked n'est plus directement connecté ici,
        # car _perform_swap_and_emit dans le widget émettra character_a/b_changed.

        self.context_actions_widget.select_linked_clicked.connect(lambda: handle_select_linked_elements(self))
        self.context_actions_widget.unlink_unrelated_clicked.connect(lambda: handle_unlink_unrelated(self))
        self.context_actions_widget.uncheck_all_clicked.connect(lambda: handle_uncheck_all(self))

        self.generation_params_widget.k_variants_changed.connect(self._schedule_settings_save)
        self.generation_params_widget.max_context_tokens_changed.connect(self._on_max_context_tokens_changed)
        # self.generation_params_widget.structured_output_changed.connect(self._schedule_settings_save) # Checkbox supprimée

        self.dialogue_structure_widget.structure_changed.connect(self._schedule_settings_save_and_token_update)

        self.instructions_widget.user_instructions_changed.connect(self._schedule_settings_save_and_token_update)
        self.instructions_widget.system_prompt_changed.connect(self._on_system_prompt_changed)
        self.instructions_widget.restore_default_system_prompt_clicked.connect(self._restore_default_system_prompt)

        self.token_actions_widget.refresh_token_clicked.connect(self._trigger_token_update)
        self.token_actions_widget.generate_dialogue_clicked.connect(self._launch_dialogue_generation)
        
        self.variants_display_widget.validate_interaction_requested.connect(self._on_validate_interaction_requested_from_tabs)

        self.interactions_tab_content_widget.interaction_selected_in_tab.connect(self._on_interaction_selected)
        self.interactions_tab_content_widget.sequence_changed_in_tab.connect(self._on_sequence_changed)
        self.interactions_tab_content_widget.edit_interaction_requested_in_tab.connect(self._on_edit_interaction_requested)
        self.interactions_tab_content_widget.interaction_changed_in_tab.connect(self._on_interaction_changed)

        # Connexion des signaux du DialogueGenerationHandler
        self.generation_handler.generation_started.connect(self._on_generation_task_started)
        self.generation_handler.generation_succeeded.connect(self._on_generation_task_succeeded)
        self.generation_handler.generation_failed.connect(self._on_generation_task_failed)
        self.generation_handler.prompt_preview_ready.connect(self._on_prompt_preview_ready_for_display)

        # Connexion du signal de l'alias (pour la sauvegarde de max_context_tokens)
        self.max_context_tokens_spinbox.valueChanged.connect(self._schedule_settings_save)
        
        # Autres configurations UI
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 2)
        initial_widths = [self.width() // 3 if self.width() > 0 else 300, 2 * self.width() // 3 if self.width() > 0 else 600]
        if all(w > 50 for w in initial_widths):
            main_splitter.setSizes(initial_widths)
        else:
            logger.warning("Largeurs initiales pour QSplitter non valides, utilisation des tailles par défaut.")
        
        self.update_token_estimation_signal.connect(self.update_token_estimation_ui)

    def finalize_ui_setup(self):
        logger.debug("Finalizing GenerationPanel UI setup...")
        # Récupérer les listes de noms pour le peuplement
        character_names = sorted(self.context_builder.get_characters_names())
        region_names = sorted(self.context_builder.get_regions())

        self.scene_selection_widget.populate_character_combos(character_names)
        self.scene_selection_widget.populate_scene_combos(region_names)
        
        self.generation_params_widget.populate_llm_model_combo()
        self._trigger_token_update() 
        logger.debug("GenerationPanel UI setup finalized.")

    def populate_llm_model_combo(self):
        logger.debug("GenerationPanel.populate_llm_model_combo appelé, déléguant à GenerationParamsWidget.")
        if hasattr(self, 'generation_params_widget') and self.generation_params_widget:
            self.generation_params_widget.populate_llm_model_combo()
        else:
            logger.error("generation_params_widget non initialisé lors de l'appel à populate_llm_model_combo.")

    def _update_structured_output_checkbox_state(self):
        # Plus rien à faire, la checkbox n'existe plus dans l'UI
        pass

    def _restore_default_system_prompt(self):
        default_prompt = self.prompt_engine._get_default_system_prompt()
        self.instructions_widget.set_system_prompt_text(default_prompt)
        self._update_prompt_engine_system_prompt()
        self.update_token_estimation_signal.emit()
        QMessageBox.information(self, "Prompt Restauré", "Le prompt système par défaut a été restauré.")


    def _on_system_prompt_changed(self):
        self._update_prompt_engine_system_prompt()
        self._schedule_settings_save_and_token_update()

    def _update_prompt_engine_system_prompt(self):
        new_system_prompt = self.instructions_widget.get_system_prompt_text()
        if self.prompt_engine.system_prompt_template != new_system_prompt:
            self.prompt_engine.system_prompt_template = new_system_prompt
            logger.info("PromptEngine system_prompt_template mis à jour.")
            # La mise à jour des tokens est gérée par _schedule_settings_save_and_token_update
            # ou explicitement par _restore_default_system_prompt


    def set_llm_client(self, new_llm_client):
        logger.info(f"GenerationPanel: Réception d'un nouveau client LLM: {type(new_llm_client).__name__}")
        self.llm_client = new_llm_client
        
        # Mettre à jour le client LLM dans le handler aussi
        if hasattr(self, 'generation_handler') and self.generation_handler:
            self.generation_handler.llm_client = new_llm_client
        else:
            logger.warning("GenerationHandler non initialisé lors de la mise à jour du client LLM.")
            
        new_model_identifier_from_client = None
        if hasattr(new_llm_client, 'model_identifier') and new_llm_client.model_identifier:
            new_model_identifier_from_client = new_llm_client.model_identifier
        elif hasattr(new_llm_client, 'model') and new_llm_client.model: # Ancien attribut
            new_model_identifier_from_client = new_llm_client.model
        
        if new_model_identifier_from_client:
            self.current_llm_model_identifier = new_model_identifier_from_client
             # MODIFIÉ: Délégué à GenerationParamsWidget
            if hasattr(self, 'generation_params_widget') and self.generation_params_widget:
                self.generation_params_widget.select_model_in_combo(new_model_identifier_from_client)
        else: 
            if isinstance(new_llm_client, DummyLLMClient):
                self.current_llm_model_identifier = "dummy" 
                if hasattr(self, 'generation_params_widget') and self.generation_params_widget:
                    self.generation_params_widget.select_model_in_combo("dummy")
            else:
                logger.warning("Nouveau client LLM n'a pas d'attribut 'model_identifier' ou 'model', l'identifiant actuel pourrait être incorrect.")

        self._trigger_token_update()
        self._update_structured_output_checkbox_state()

    @Slot()
    def _schedule_settings_save(self):
        """Déclenche un signal pour indiquer que les paramètres ont changé."""
        if not self._is_loading_settings:  # Éviter les sauvegardes pendant le chargement initial
            self.settings_changed.emit()

    @Slot()
    def _schedule_settings_save_and_token_update(self):
        """Déclenche un signal pour indiquer que les paramètres ont changé et met à jour l'estimation des tokens."""
        self._schedule_settings_save()
        self.update_token_estimation_ui()
        
    def _trigger_token_update(self):
        """
        Méthode appelée par MainWindow quand le contexte change (éléments cochés, combos, etc.).
        Rafraîchit l'estimation du prompt et le nombre de tokens affichés.
        """
        self.update_token_estimation_ui()

    @Slot()
    def update_token_estimation_ui(self):
        if not self.dialogue_generation_service or not self.llm_client: # MODIFIÉ: Vérifier dialogue_generation_service
            self.token_estimation_label.setText("Erreur: Services non initialisés")
            self._display_prompt_in_tab("Erreur: Le service de génération ou le client LLM ne sont pas initialisés.")
            return

        user_specific_goal = self.instructions_widget.get_user_instructions_text()
        selected_context_items = self.main_window_ref._get_current_context_selections() if hasattr(self.main_window_ref, '_get_current_context_selections') else {}

        # Récupérer les sélections de scène depuis le widget
        scene_info = self.scene_selection_widget.get_selected_scene_info()
        char_a_name = scene_info.get("character_a")
        char_b_name = scene_info.get("character_b")
        scene_region_name = scene_info.get("scene_region")
        scene_sub_location_name = scene_info.get("scene_sub_location")

        char_a_name = char_a_name if char_a_name and char_a_name != UIText.NONE else None
        char_b_name = char_b_name if char_b_name and char_b_name != UIText.NONE else None
        scene_region_name = scene_region_name if scene_region_name and scene_region_name != UIText.NONE_FEM else None
        scene_sub_location_name = scene_sub_location_name if scene_sub_location_name and scene_sub_location_name != UIText.ALL and scene_sub_location_name != UIText.NONE_SUBLOCATION and scene_sub_location_name != UIText.NO_SELECTION else None

        scene_protagonists_dict = {}
        if char_a_name: scene_protagonists_dict["personnage_a"] = char_a_name
        if char_b_name: scene_protagonists_dict["personnage_b"] = char_b_name

        scene_location_dict = {}
        if scene_region_name: scene_location_dict["lieu"] = scene_region_name
        if scene_sub_location_name: scene_location_dict["sous_lieu"] = scene_sub_location_name
        
        # Préparer context_selections pour le service
        context_selections_for_service = selected_context_items.copy()
        context_selections_for_service["_scene_protagonists"] = scene_protagonists_dict
        context_selections_for_service["_scene_location"] = scene_location_dict
        # La structure et la description de la structure ne sont pas directement utilisées par prepare_generation_preview,
        # mais structured_output l'est.
        # dialogue_structure_description = self.dialogue_structure_widget.get_structure_description()
        context_selections_for_service["generate_interaction"] = True # Par défaut pour l'estimation du pire cas (structuré)

        full_prompt_for_estimation = "Erreur lors de la construction du prompt pour estimation."
        prompt_tokens = 0
        # context_tokens n'est plus directement retourné par prepare_generation_preview, 
        # mais le service s'en occupe en interne pour construire le prompt.
        # Le label affichera uniquement les tokens du prompt total.

        try:
            max_tokens_val = self.main_window_ref.config_service.get_ui_setting("max_context_tokens", Defaults.CONTEXT_TOKENS)
            system_prompt_override = self.instructions_widget.get_system_prompt_text()

            # Appel à la méthode du service
            # structured_output=True car l'estimation doit refléter le cas le plus coûteux (génération structurée)
            # si c'est ce que l'utilisateur a configuré ou pourrait configurer.
            # Pour une estimation générique, on peut supposer True.
            # Note: La méthode du service gère elle-même le system_prompt_override.
            full_prompt_for_estimation, prompt_tokens, _ = self.dialogue_generation_service.prepare_generation_preview(
                user_instructions=user_specific_goal,
                system_prompt_override=system_prompt_override,
                context_selections=context_selections_for_service,
                max_context_tokens=max_tokens_val,
                structured_output=True # On estime pour un output structuré par défaut
            )
            
            if not full_prompt_for_estimation:
                 full_prompt_for_estimation = "Erreur: Le service n'a pas pu construire le prompt pour l'estimation."


            logger.debug(f"[GenerationPanel.update_token_estimation_ui via Service] Full prompt for estimation (first 300 chars): {full_prompt_for_estimation[:300] if full_prompt_for_estimation else 'None'}")

        except Exception as e:
            logger.error(f"Erreur pendant l'appel à prepare_generation_preview du service: {e}", exc_info=True)
            full_prompt_for_estimation = f"Erreur lors de la préparation de la prévisualisation via le service:\n{type(e).__name__}: {e}"
            prompt_tokens = 0

        # Affichage des tokens en milliers (k) - Uniquement le total prompt
        prompt_tokens_k = prompt_tokens / 1000
        self.token_estimation_label.setText(f"Tokens prompt (estimé): {prompt_tokens_k:.1f}k")
        logger.debug(f"Token estimation UI updated (via Service): Prompt total {prompt_tokens} ({prompt_tokens_k:.1f}k).")
        
        self._display_prompt_in_tab(full_prompt_for_estimation)


    def _launch_dialogue_generation(self):
        logger.info("Lancement de la génération de dialogue...")
        if not self.llm_client:
            QMessageBox.critical(self, "Erreur LLM", "Le client LLM n'est pas initialisé.")
            logger.error("Tentative de génération de dialogue sans client LLM initialisé.")
            return

        self.generation_progress_bar.setRange(0, 0) 
        self.generation_progress_bar.setVisible(True)
        self.generate_dialogue_button.setEnabled(False)
        QApplication.processEvents() 

        # Récupérer les paramètres et appeler le handler
        try:
            k_variants = int(self.k_variants_combo.currentText())
            user_instructions = self.instructions_widget.get_user_instructions_text()
            system_prompt_override = self.instructions_widget.get_system_prompt_text() 
            selected_gdd_items = self.main_window_ref._get_current_context_selections() 
            
            scene_info = self.scene_selection_widget.get_selected_scene_info()
            char_a_name = scene_info.get("character_a")
            char_b_name = scene_info.get("character_b")
            scene_region_name = scene_info.get("scene_region")
            scene_sub_location_name = scene_info.get("scene_sub_location")

            char_a_name = char_a_name if char_a_name and char_a_name != UIText.NONE else None
            char_b_name = char_b_name if char_b_name and char_b_name != UIText.NONE else None
            scene_region_name = scene_region_name if scene_region_name and scene_region_name != UIText.NONE_FEM else None
            scene_sub_location_name = scene_sub_location_name if scene_sub_location_name and scene_sub_location_name != UIText.ALL and scene_sub_location_name != UIText.NONE_SUBLOCATION and scene_sub_location_name != UIText.NO_SELECTION else None

            scene_protagonists_dict = {}
            if char_a_name: scene_protagonists_dict["personnage_a"] = char_a_name
            if char_b_name: scene_protagonists_dict["personnage_b"] = char_b_name

            scene_location_dict = {}
            if scene_region_name: scene_location_dict["lieu"] = scene_region_name
            if scene_sub_location_name: scene_location_dict["sous_lieu"] = scene_sub_location_name
            
            context_selections_for_service = selected_gdd_items.copy()
            context_selections_for_service["_scene_protagonists"] = scene_protagonists_dict
            context_selections_for_service["_scene_location"] = scene_location_dict

            dialogue_structure_description = self.dialogue_structure_widget.get_structure_description()
            dialogue_structure_elements = self.dialogue_structure_widget.get_structure()
            max_context_tokens_val = self.main_window_ref.config_service.get_ui_setting("max_context_tokens", Defaults.CONTEXT_TOKENS)

            asyncio.create_task(self.generation_handler.generate_dialogue_async(
                k_variants=k_variants,
                user_instructions=user_instructions,
                system_prompt_override=system_prompt_override,
                context_selections_for_service=context_selections_for_service,
                dialogue_structure_description=dialogue_structure_description,
                dialogue_structure_elements=dialogue_structure_elements,
                max_context_tokens_val=max_context_tokens_val,
                current_llm_model_identifier=self.current_llm_model_identifier
            ))
        except Exception as e:
            logger.error(f"Erreur lors de la préparation du lancement de la génération: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur Pré-Génération", f"Impossible de lancer la génération: {e}")
            self.generation_progress_bar.setVisible(False)
            self.generate_dialogue_button.setEnabled(True)

    @Slot()
    def _on_generation_task_started(self):
        logger.info("GenerationPanel: Tâche de génération démarrée (via signal du handler).")
        self.generation_progress_bar.setRange(0, 0) # Indeterminate
        self.generation_progress_bar.setVisible(True)
        self.generate_dialogue_button.setEnabled(False)
        QApplication.processEvents() 

    @Slot(list, str, int) # variants_objects, full_prompt_for_display, estimated_tokens_for_display
    def _on_generation_task_succeeded(self, processed_variants: List[Interaction], full_prompt: str, estimated_tokens: int):
        logger.info(f"GenerationPanel: Tâche de génération réussie. {len(processed_variants)} variantes traitées reçues.")
        
        if full_prompt:
            estimated_tokens_k = estimated_tokens / 1000 if estimated_tokens else 0
            self.token_estimation_label.setText(f"Tokens prompt final: {estimated_tokens_k:.1f}k")
            self._display_prompt_in_tab(full_prompt)
        else:
            self.token_estimation_label.setText("Tokens prompt final: Erreur")
            self._display_prompt_in_tab("Erreur: Le prompt n'a pas pu être construit par le service/handler.")

        self.variants_display_widget.blockSignals(True)
        num_tabs_to_keep = 0
        if self.variants_display_widget.count() > 0 and self.variants_display_widget.tabText(0) == "Prompt Estimé":
            num_tabs_to_keep = 1
        
        while self.variants_display_widget.count() > num_tabs_to_keep:
            self.variants_display_widget.removeTab(num_tabs_to_keep)
        
        if processed_variants:
            for i, interaction_obj in enumerate(processed_variants):
                # Les objets sont déjà des Interactions (ou des Interactions d'erreur)
                if interaction_obj.interaction_id.startswith("error_"):
                     # C'est un placeholder d'erreur créé par le handler
                    error_text = interaction_obj.elements[0].get('text', 'Erreur inconnue dans la variante') if interaction_obj.elements else 'Erreur inconnue'
                    text_edit = QTextEdit(f"// {interaction_obj.title}\n{error_text}")
                    text_edit.setReadOnly(True)
                    self.variants_display_widget.addTab(text_edit, f"Variante {i+1} (Erreur)")
                else:
                    self.variants_display_widget.add_interaction_tab(f"Variante {i+1}", interaction_obj)
                    logger.info(f"[GP] Variante {i+1} (Interaction) ajoutée via add_interaction_tab. ID: {interaction_obj.interaction_id}")
            
            logger.info(f"{len(processed_variants)} variantes affichées depuis le handler.")
        else:
            logger.warning("Aucune variante valide reçue du handler (liste vide).")
            error_tab = QTextEdit(UIText.NO_VARIANT + " (via Handler)")
            self.variants_display_widget.addTab(error_tab, "Aucune Variante (Handler)")
        
        self.variants_display_widget.blockSignals(False)
        self.generation_finished.emit(True if processed_variants else False)
        self._finalize_generation_ui_state()

    @Slot(str, str) # error_message, full_prompt_for_display
    def _on_generation_task_failed(self, error_message: str, full_prompt: Optional[str]):
        logger.error(f"GenerationPanel: Tâche de génération échouée: {error_message}")
        
        if full_prompt and full_prompt != "Erreur: Le prompt n'a pas pu être construit.":
             self._display_prompt_in_tab(full_prompt)
        else:
            self._display_prompt_in_tab(f"Erreur critique avant ou pendant la construction du prompt: {error_message}")

        self.variants_display_widget.blockSignals(True)
        num_tabs_to_keep_err = 0
        if self.variants_display_widget.count() > 0 and self.variants_display_widget.tabText(0) == "Prompt Estimé":
            num_tabs_to_keep_err = 1
        while self.variants_display_widget.count() > num_tabs_to_keep_err:
            self.variants_display_widget.removeTab(num_tabs_to_keep_err)
        
        error_tab_content = QTextEdit()
        error_tab_content.setPlainText(f"Une erreur majeure est survenue lors de la génération (via Handler):\n\n{error_message}")
        error_tab_content.setReadOnly(True)
        self.variants_display_widget.addTab(error_tab_content, "Erreur Critique (Handler)")
        self.variants_display_widget.blockSignals(False)
        
        self.generation_finished.emit(False)
        self._finalize_generation_ui_state()

    @Slot(str, int) # prompt_text, estimated_tokens
    def _on_prompt_preview_ready_for_display(self, prompt_text: str, estimated_tokens: int):
        logger.debug(f"GenerationPanel: Prévisualisation du prompt prête (via Handler). Tokens: {estimated_tokens}")
        if prompt_text:
            estimated_tokens_k = estimated_tokens / 1000 if estimated_tokens else 0
            self.token_estimation_label.setText(f"Tokens prompt (en cours): {estimated_tokens_k:.1f}k")
            self._display_prompt_in_tab(prompt_text)
        else:
            self.token_estimation_label.setText("Tokens prompt (en cours): Erreur")
            self._display_prompt_in_tab("Erreur: Le prompt n'a pas pu être construit par le service/handler pour la prévisualisation.")

    def _finalize_generation_ui_state(self):
        current_task = asyncio.current_task() # Peut être None si la boucle d'event n'est pas gérée par asyncio ici
        if not current_task or not current_task.cancelled(): 
            self.generation_progress_bar.setVisible(False)
            self.generate_dialogue_button.setEnabled(True)
            QApplication.processEvents() 
            logger.debug("GenerationPanel: État UI finalisé après génération.")

    def _display_prompt_in_tab(self, prompt_text: str):
        logger.info(f"_display_prompt_in_tab: Entrée avec prompt_text de longueur {len(prompt_text if prompt_text else 0)} chars.") # Ajout d'une vérification pour prompt_text None
        self.variants_display_widget.blockSignals(True)
        
        prompt_tab_index = -1
        for i in range(self.variants_display_widget.count()):
            if self.variants_display_widget.tabText(i) == "Prompt Estimé":
                prompt_tab_index = i
                break
        
        if prompt_tab_index != -1:
            logger.info(f"_display_prompt_in_tab: Onglet 'Prompt Estimé' trouvé à l'index {prompt_tab_index}. Mise à jour du contenu.")
            self.variants_display_widget.update_or_add_tab("Prompt Estimé", prompt_text, set_current=True)
        else:
            logger.info("_display_prompt_in_tab: Onglet 'Prompt Estimé' non trouvé. Création d'un nouvel onglet via update_or_add_tab.")
            self.variants_display_widget.update_or_add_tab("Prompt Estimé", prompt_text, set_current=True)
        
        self.variants_display_widget.blockSignals(False)

    # --- Validation et sauvegarde d'une Interaction générée ---
    @Slot(str, Interaction)
    def _on_validate_interaction_requested_from_tabs(self, tab_name: str, interaction: Interaction):
        """Sauvegarde l'interaction validée et met à jour l'UI.

        Args:
            tab_name: Nom de l'onglet source (non utilisé pour l'instant mais conservé pour compatibilité).
            interaction: L'objet Interaction à sauvegarder.
        """
        logger.info(f"[VALIDATE] Demande de validation depuis l'onglet '{tab_name}' pour l'interaction ID={interaction.interaction_id}")
        try:
            # 1) Sauvegarde via le service → JSON sur disque
            self.interaction_service.save(interaction)

            # 2) Feedback utilisateur
            title_display = interaction.title if getattr(interaction, 'title', None) else str(interaction.interaction_id)[:8]
            QMessageBox.information(self, "Interaction Validée", f"L'interaction '{title_display}' a été sauvegardée.")

            # 3) Rafraîchir la liste des interactions et sélectionner la nouvelle
            try:
                # Déconnecte temporairement pour éviter les effets de bord pendant la mise à jour
                self.interactions_tab_content_widget.interaction_selected_in_tab.disconnect(self._on_interaction_selected)
            except Exception:
                pass  # Pas critique si déjà déconnecté

            self.interactions_tab_content_widget.refresh_sequence_list(select_id=str(interaction.interaction_id))

            # Affiche l'interaction dans l'éditeur
            self.interactions_tab_content_widget.display_interaction_in_editor(interaction)

            # Reconnecte le signal
            try:
                self.interactions_tab_content_widget.interaction_selected_in_tab.connect(self._on_interaction_selected)
            except Exception:
                pass

            # Message de statut dans la barre inférieure si disponible
            if hasattr(self.main_window_ref, 'statusBar'):
                self.main_window_ref.statusBar().showMessage(f"Interaction '{title_display}' sauvegardée.", 3000)

        except Exception as e:
            logger.exception("Erreur lors de la validation/sauvegarde de l'interaction.")
            QMessageBox.critical(self, "Erreur", f"Impossible de sauvegarder l'interaction : {e}")

    # Ancien slot conservé (désormais inutilisé)
    @Slot(int)
    def _on_validate_interaction_clicked(self, variant_index: int):
        logger.warning("_on_validate_interaction_clicked est obsolète. Utilisation du nouveau slot de validation d'interaction.")
        QMessageBox.information(self, "Validation", "Ce mécanisme de validation est obsolète.")

    @Slot()
    def _on_uncheck_all_clicked(self):
        """Slot pour le bouton "Tout Décocher".
        """
        if hasattr(self.main_window_ref, 'left_panel') and hasattr(self.main_window_ref.left_panel, 'uncheck_all_items'):
            self.main_window_ref.left_panel.uncheck_all_items()
            logger.info("Tous les éléments ont été décochés dans LeftSelectionPanel.")
            self.main_window_ref.statusBar().showMessage(UIText.ERROR_PREFIX + "Impossible de tout décocher.", 3000)
            # QApplication.instance().beep() # Optionnel, si le son est gênant
        else:
            logger.warning("Impossible de tout décocher: left_panel ou méthode uncheck_all_items non trouvée.")
            self.main_window_ref.statusBar().showMessage(UIText.ERROR_PREFIX + "Impossible de tout décocher.", 3000)

    def get_settings(self) -> dict:
        # Récupère les paramètres actuels du panneau pour la sauvegarde.
        scene_settings = self.scene_selection_widget.get_selected_scene_info()
        settings = {
            # Utiliser les clés de scene_settings directement
            "character_a": scene_settings.get("character_a"),
            "character_b": scene_settings.get("character_b"),
            "scene_region": scene_settings.get("scene_region"),
            "scene_sub_location": scene_settings.get("scene_sub_location"),
            "k_variants": self.k_variants_combo.currentText(),
            "user_instructions": self.instructions_widget.get_user_instructions_text(),
            "llm_model": self.llm_model_combo.currentData(), 
            "system_prompt": self.instructions_widget.get_system_prompt_text(),
            "max_context_tokens": self.max_context_tokens_spinbox.value(),
            "dialogue_structure": self.dialogue_structure_widget.get_structure()
        }
        logger.debug(f"Récupération des paramètres du GenerationPanel: {settings}")
        return settings

    def load_settings(self, settings: dict):
        logger.debug(f"Chargement des paramètres dans GenerationPanel: {settings}")
        self._is_loading_settings = True
        
        # Charger les paramètres de scène via le widget
        scene_info_to_load = {
            "character_a": settings.get("character_a"),
            "character_b": settings.get("character_b"),
            "scene_region": settings.get("scene_region"),
            "scene_sub_location": settings.get("scene_sub_location")
        }
        self.scene_selection_widget.load_selection(scene_info_to_load)
        # Les signaux émis par load_selection (via _is_populating=False à la fin)
        # vont déclencher _schedule_settings_save_and_token_update.
        
        self.k_variants_combo.setCurrentText(settings.get("k_variants", "3"))
        
        instruction_settings_to_load = {
            "user_instructions": settings.get("user_instructions", ""),
            "system_prompt": settings.get("system_prompt") 
        }
        default_system_prompt_for_iw = self.prompt_engine._get_default_system_prompt() if self.prompt_engine else ""
        self.instructions_widget.load_settings(
            instruction_settings_to_load, 
            default_user_instructions="", 
            default_system_prompt=default_system_prompt_for_iw
        )
        
        model_identifier = settings.get("llm_model")
        if model_identifier:
            if hasattr(self, 'generation_params_widget') and self.generation_params_widget:
                self.generation_params_widget.select_model_in_combo(model_identifier)
        else:
            if hasattr(self, 'generation_params_widget') and self.generation_params_widget and self.generation_params_widget.llm_model_combo.count() > 0:
                 self.generation_params_widget.llm_model_combo.setCurrentIndex(0)
        
        if "dialogue_structure" in settings:
            self.dialogue_structure_widget.set_structure(settings["dialogue_structure"])
        
        if "max_context_tokens" in settings:
            self.max_context_tokens_spinbox.setValue(settings["max_context_tokens"])
        
        self._is_loading_settings = False
        self.update_token_estimation_signal.emit() # Assurer un rafraîchissement global à la fin du chargement
        logger.info("Paramètres du GenerationPanel chargés.")

    @Slot(float)
    def _on_max_context_tokens_changed(self, new_value: float):
        """Gère le changement de valeur dans le spinbox max_context_tokens."""
        tokens_value = int(new_value * 1000)
        logger.info(f"Limite de tokens pour le contexte mise à jour: {tokens_value}")
        self._schedule_settings_save_and_token_update()

    # --- Gestion des Interactions ---
    
    @Slot(uuid.UUID)
    def _on_interaction_selected(self, interaction_id: uuid.UUID):
        """Gère la sélection d'une interaction dans la liste.
        
        Args:
            interaction_id: L'identifiant de l'interaction sélectionnée ou None si aucune.
        """
        if interaction_id:
            logger.info(f"Interaction sélectionnée : {interaction_id}")
            interaction = self.interaction_service.get_by_id(str(interaction_id))
            if interaction:
                title_display = getattr(interaction, 'title', str(interaction_id)[:8])
                self.main_window_ref.statusBar().showMessage(f"Interaction '{title_display}' sélectionnée.", 3000)
                
                # Afficher l'interaction dans l'éditeur - Géré par InteractionsTabWidget
                # self.interaction_editor_widget.set_interaction(interaction)
            else:
                logger.warning(f"Interaction {interaction_id} non trouvée par le service.")
                self.main_window_ref.statusBar().showMessage(UIText.ERROR_PREFIX + f"Interaction {interaction_id} non trouvée.", 3000)
                # La sélection dans la liste devrait déjà avoir mis à jour l'éditeur via la logique interne de InteractionsTabWidget
                # Si on veut forcer l'affichage d'une interaction spécifique NON sélectionnée dans la liste:
                self.interactions_tab_content_widget.display_interaction_in_editor(interaction)

            title_display = getattr(interaction, 'title', str(interaction_id)[:8])
            self.main_window_ref.statusBar().showMessage(f"Édition de l'interaction '{title_display}'", 3000)
        else:
            logger.info("Aucune interaction sélectionnée.")
            self.main_window_ref.statusBar().showMessage(UIText.NO_INTERACTION_FOUND, 3000)
            self.interactions_tab_content_widget.display_interaction_in_editor(None)

    @Slot()
    def _on_sequence_changed(self):
        """Gère le changement dans la séquence d'interactions (ajout, suppression, réorganisation)."""
        logger.info("La séquence d'interactions a changé (ajout, suppression, réorganisation).")
        self.main_window_ref.statusBar().showMessage("Séquence d'interactions modifiée.", 3000)
    
    @Slot(uuid.UUID)
    def _on_edit_interaction_requested(self, interaction_id: uuid.UUID):
        """Gère la demande d'édition d'une interaction.
        
        Args:
            interaction_id: L'identifiant de l'interaction à éditer.
        """
        logger.info(f"Demande d'édition pour l'interaction : {interaction_id}")
        interaction = self.interaction_service.get_by_id(str(interaction_id))
        if interaction:
            # Sélectionner l'onglet Interactions s'il ne l'est pas déjà
            tabs = self.findChild(QTabWidget)
            if tabs:
                interactions_tab_index = tabs.indexOf(self.interactions_tab_content_widget.parent())
                if interactions_tab_index >= 0 and tabs.currentIndex() != interactions_tab_index:
                    tabs.setCurrentIndex(interactions_tab_index)
            
            # Afficher l'interaction dans l'éditeur
            self.interactions_tab_content_widget.display_interaction_in_editor(interaction)
            title_display = getattr(interaction, 'title', str(interaction_id)[:8])
            self.main_window_ref.statusBar().showMessage(f"Édition de l'interaction '{title_display}'", 3000)
        else:
            QMessageBox.warning(self, "Erreur", f"Impossible de trouver l'interaction {str(interaction_id)} pour l'édition.")
    
    @Slot(Interaction)
    def _on_interaction_changed(self, interaction: Interaction):
        """Gère le changement d'une interaction après édition.
        
        Args:
            interaction: L'interaction modifiée.
        """
        logger.info(f"Interaction modifiée : {interaction.interaction_id}")
        
        # Mettre à jour l'affichage de la séquence
        # self.interaction_sequence_widget.refresh_list()
        # La liste est rafraîchie en interne par InteractionsTabWidget après un changement dans l'éditeur
        
        title_display = getattr(interaction, 'title', str(interaction.interaction_id)[:8])
        self.main_window_ref.statusBar().showMessage(f"Interaction '{title_display}' mise à jour.", 3000)