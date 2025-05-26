# --- Imports standard ---
import os
import sys
import uuid
import pathlib
from pathlib import Path
import logging
import asyncio
from typing import Optional

# --- Imports PySide6 ---
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QComboBox, QTextEdit, QPushButton, QProgressBar, QApplication, QMessageBox, QSplitter
from PySide6.QtCore import Qt, Signal, Slot

# --- Imports internes (services, modèles, constantes) ---
from services.interaction_service import InteractionService
from services.repositories.file_repository import FileInteractionRepository
from constants import UIText, Defaults

# --- Imports locaux (widgets et handlers du panneau de génération) ---
from .generation_panel.scene_selection_widget import SceneSelectionWidget
from .generation_panel.context_actions_widget import ContextActionsWidget
from .generation_panel.generation_params_widget import GenerationParamsWidget
from .generation_panel.instructions_widget import InstructionsWidget
from .generation_panel.token_estimation_actions_widget import TokenEstimationActionsWidget
from .generation_panel.generated_variants_tabs_widget import GeneratedVariantsTabsWidget
from .generation_panel.interactions_tab_widget import InteractionsTabWidget
from .generation_panel.dialogue_structure_widget import DialogueStructureWidget
from .generation_panel.dialogue_generation_handler import DialogueGenerationHandler
from .generation_panel.handlers import (
    handle_select_linked_elements, handle_unlink_unrelated, handle_uncheck_all, handle_system_prompt_changed, handle_restore_default_system_prompt, handle_max_context_tokens_changed, handle_k_variants_changed, handle_structure_changed, handle_user_instructions_changed, handle_refresh_token, handle_generate_dialogue, handle_validate_interaction_requested_from_tabs, handle_interaction_selected, handle_sequence_changed, handle_edit_interaction_requested, handle_interaction_changed, get_generation_panel_settings, load_generation_panel_settings, handle_update_structured_output_checkbox_state, handle_generation_task_started, handle_generation_task_succeeded, handle_generation_task_failed, handle_prompt_preview_ready_for_display
)

# --- Imports pour compatibilité exécution directe (try/except) ---
try:
    from services.linked_selector import LinkedSelectorService
    from services.yarn_renderer import JinjaYarnRenderer
    from llm_client import OpenAIClient, DummyLLMClient
except ImportError:
    current_dir = pathlib.Path(__file__).resolve().parent.parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    from services.linked_selector import LinkedSelectorService
    from services.yarn_renderer import JinjaYarnRenderer
    from llm_client import OpenAIClient, DummyLLMClient

logger = logging.getLogger(__name__)

# Chemins et constantes
DIALOGUE_GENERATOR_DIR = Path(__file__).resolve().parent.parent
LLM_CONFIG_FILE_PATH = DIALOGUE_GENERATOR_DIR / "llm_config.json"
DEFAULT_INTERACTIONS_DIR = DIALOGUE_GENERATOR_DIR / "data" / "interactions"

# =============================
#   Classe principale du panel
# =============================

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

        # Initialiser current_max_context_tokens_k avec une valeur par défaut.
        # Elle sera correctement mise à jour par load_settings() après _init_ui()
        # ou par le handler si la valeur du spinbox change manuellement.
        self.current_max_context_tokens_k = Defaults.CONTEXT_TOKENS / 1000 # en k_tokens

        self._init_ui()
        # finalize_ui_setup() est appelé par MainWindow

    # --- Initialisation UI et connexion des signaux ---
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

        self.generation_params_widget.k_variants_changed.connect(lambda value: handle_k_variants_changed(self, value))
        self.generation_params_widget.max_context_tokens_changed.connect(lambda value: handle_max_context_tokens_changed(self, value))
        # self.generation_params_widget.structured_output_changed.connect(self._schedule_settings_save) # Checkbox supprimée

        self.dialogue_structure_widget.structure_changed.connect(lambda: handle_structure_changed(self))

        self.instructions_widget.user_instructions_changed.connect(lambda: handle_user_instructions_changed(self))
        self.instructions_widget.system_prompt_changed.connect(lambda: handle_system_prompt_changed(self))
        self.instructions_widget.restore_default_system_prompt_clicked.connect(lambda: handle_restore_default_system_prompt(self))

        self.token_actions_widget.refresh_token_clicked.connect(lambda: handle_refresh_token(self))
        self.token_actions_widget.generate_dialogue_clicked.connect(lambda: handle_generate_dialogue(self))
        
        self.variants_display_widget.validate_interaction_requested.connect(lambda tab_name, interaction: handle_validate_interaction_requested_from_tabs(self, tab_name, interaction))

        self.interactions_tab_content_widget.interaction_selected_in_tab.connect(lambda interaction_id: handle_interaction_selected(self, interaction_id))
        self.interactions_tab_content_widget.sequence_changed_in_tab.connect(lambda: handle_sequence_changed(self))
        self.interactions_tab_content_widget.edit_interaction_requested_in_tab.connect(lambda interaction_id: handle_edit_interaction_requested(self, interaction_id))
        self.interactions_tab_content_widget.interaction_changed_in_tab.connect(lambda interaction: handle_interaction_changed(self, interaction))

        # Connexion des signaux du DialogueGenerationHandler
        self.generation_handler.generation_started.connect(lambda: handle_generation_task_started(self))
        self.generation_handler.generation_succeeded.connect(lambda processed_variants, full_prompt, estimated_tokens: handle_generation_task_succeeded(self, processed_variants, full_prompt, estimated_tokens))
        self.generation_handler.generation_failed.connect(self._on_generation_task_failed)
        self.generation_handler.prompt_preview_ready.connect(lambda prompt_text, estimated_tokens: handle_prompt_preview_ready_for_display(self, prompt_text, estimated_tokens))

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
        self.update_token_estimation_ui() 
        logger.debug("GenerationPanel UI setup finalized.")

    def populate_llm_model_combo(self):
        logger.debug("GenerationPanel.populate_llm_model_combo appelé, déléguant à GenerationParamsWidget.")
        if hasattr(self, 'generation_params_widget') and self.generation_params_widget:
            self.generation_params_widget.populate_llm_model_combo()
        else:
            logger.error("generation_params_widget non initialisé lors de l'appel à populate_llm_model_combo.")

    def _update_structured_output_checkbox_state(self):
        handle_update_structured_output_checkbox_state(self)

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

        self.update_token_estimation_ui()
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
        logger.info(f"[update_token_estimation_ui] selected_context_items (récupéré depuis main_window_ref): {selected_context_items}")
        logger.info(f"[update_token_estimation_ui] Type de selected_context_items: {type(selected_context_items)}")

        if not isinstance(selected_context_items, dict):
            logger.error(f"CRITICAL: selected_context_items récupéré N'EST PAS UN DICTIONNAIRE. C'est un {type(selected_context_items)}. Le contexte GDD ne sera pas correctement traité. Valeur: {selected_context_items}")
            # Si ce n'est pas un dictionnaire, selected_context_items est probablement une liste ou autre chose.
            # Pour la suite, nous allons traiter cela comme si aucun élément GDD n'était sélectionné.
            selected_context_items = {} # Assurer que c'est un dict pour la suite, même s'il est vide.

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
        # Assurer que selected_context_items est bien un dictionnaire avant de le copier.
        # Si ce n'était pas un dictionnaire à l'origine (géré par le bloc if/else plus haut), il sera maintenant {}
        context_selections_for_service = selected_context_items.copy()
        
        context_selections_for_service["_scene_protagonists"] = scene_protagonists_dict
        context_selections_for_service["_scene_location"] = scene_location_dict
        # La structure et la description de la structure ne sont pas directement utilisées par prepare_generation_preview,
        # mais structured_output l'est.
        # dialogue_structure_description = self.dialogue_structure_widget.get_structure_description()
        context_selections_for_service["generate_interaction"] = True # Par défaut pour l'estimation du pire cas (structuré)

        logger.info(f"[update_token_estimation_ui] context_selections_for_service transmis à prepare_generation_preview: {context_selections_for_service}")
        try:
            # max_tokens_val = self.main_window_ref.config_service.get_ui_setting("max_context_tokens", Defaults.CONTEXT_TOKENS)
            # Utiliser la valeur de l'attribut mis à jour par le handler
            max_tokens_val_k = self.current_max_context_tokens_k
            max_tokens_val = int(max_tokens_val_k * 1000) # Convertir k_tokens en tokens
            logger.info(f"[update_token_estimation_ui] Utilisation de max_tokens_val = {max_tokens_val} (provenant de self.current_max_context_tokens_k: {max_tokens_val_k}k)")
            
            system_prompt_override = self.instructions_widget.get_system_prompt_text()

            # Appel à la méthode du service
            full_prompt_for_estimation, prompt_tokens, _ = self.dialogue_generation_service.prepare_generation_preview(
                user_instructions=user_specific_goal,
                system_prompt_override=system_prompt_override,
                context_selections=context_selections_for_service,
                max_context_tokens=max_tokens_val,
                structured_output=True
            )
            logger.info(f"[update_token_estimation_ui] prompt généré (début): {full_prompt_for_estimation[:300] if full_prompt_for_estimation else 'None'}")
            logger.info(f"[update_token_estimation_ui] prompt_tokens retourné: {prompt_tokens}, longueur prompt: {len(full_prompt_for_estimation)} chars, {len(full_prompt_for_estimation.split())} mots. Affiché: {prompt_tokens/1000:.1f}k tokens.")
            
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
        logger.info(f"[update_token_estimation_ui] Label UI mis à jour: Tokens prompt (estimé): {prompt_tokens_k:.1f}k")
        
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

    def get_settings(self) -> dict:
        """Retourne les paramètres actuels du panneau pour sauvegarde."""
        settings = {
            "character_a": self.scene_selection_widget.character_a_combo.currentText(),
            "character_b": self.scene_selection_widget.character_b_combo.currentText(),
            "scene_region": self.scene_selection_widget.scene_region_combo.currentText(),
            "scene_sub_location": self.scene_selection_widget.scene_sub_location_combo.currentText(),
            "llm_model": self.generation_params_widget.get_settings().get("llm_model"), # Délégué
            "k_variants": self.generation_params_widget.get_settings().get("k_variants"), # Délégué
            "max_context_tokens": self.current_max_context_tokens_k, # Utiliser la valeur stockée
            "user_instructions": self.instructions_widget.get_user_instructions_text(),
            "system_prompt": self.instructions_widget.get_system_prompt_text(),
            "dialogue_structure": self.dialogue_structure_widget.get_structure(),
            "structured_output": self.generation_params_widget.get_settings().get("structured_output") # Délégué
        }
        logger.debug(f"Récupération des paramètres du panneau de génération: {settings}")
        return settings

    def load_settings(self, settings: dict):
        """Charge les paramètres sauvegardés dans l'UI."""
        self._is_loading_settings = True
        logger.debug(f"Chargement des paramètres dans GenerationPanel: {settings}")

        self.scene_selection_widget.character_a_combo.setCurrentText(settings.get("character_a", UIText.NONE))
        self.scene_selection_widget.character_b_combo.setCurrentText(settings.get("character_b", UIText.NONE))
        self.scene_selection_widget.scene_region_combo.setCurrentText(settings.get("scene_region", UIText.NONE_FEM))
        
        # Le sous-lieu dépend de la région, donc il est mis à jour par le signal de la région si nécessaire
        # On le charge explicitement ici au cas où la région n'aurait pas changé.
        sub_location_setting = settings.get("scene_sub_location")
        if sub_location_setting:
            self.scene_selection_widget.scene_sub_location_combo.setCurrentText(sub_location_setting)
        
        # Délégué à GenerationParamsWidget pour ses propres paramètres
        # On passe uniquement la section pertinente des settings
        llm_params_settings = {
            "llm_model": settings.get("llm_model"),
            "k_variants": settings.get("k_variants"),
            "max_context_tokens": settings.get("max_context_tokens"), # Passe la valeur k_tokens
            "structured_output": settings.get("structured_output")
        }
        self.generation_params_widget.load_settings(llm_params_settings)
        
        # Mettre à jour self.current_max_context_tokens_k après le chargement dans le widget
        self.current_max_context_tokens_k = self.generation_params_widget.max_context_tokens_spinbox.value()


        self.instructions_widget.user_instructions_textedit.setPlainText(settings.get("user_instructions", ""))
        self.instructions_widget.set_system_prompt_text(settings.get("system_prompt", None)) # None comme défaut
        self.dialogue_structure_widget.set_structure(settings.get("dialogue_structure", ["PNJ", "PJ", "Stop", "", "", ""])) # Défaut explicite

        self._is_loading_settings = False
        self.update_token_estimation_ui() # Mettre à jour l'estimation après le chargement
        # Pas besoin d'émettre settings_changed ici car c'est un chargement
        logger.debug("Paramètres du panneau de génération chargés.")