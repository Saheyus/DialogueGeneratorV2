import pathlib
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QGridLayout, 
                               QLabel, QComboBox, QTextEdit, QPushButton, 
                               QTabWidget, QLineEdit, QCheckBox, QHBoxLayout, QApplication, QSizePolicy, QProgressBar, QScrollArea, QSplitter, QFrame, QPlainTextEdit, QMessageBox, QSpacerItem, QMenu, QStyle, QSpinBox, QDoubleSpinBox)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QPalette, QColor, QFont, QIcon, QAction
import logging # Added for logging
import asyncio # Added for asynchronous tasks
from typing import Optional, Callable, Any # Added Any
import json # Ajout pour charger la config LLM potentiellement ici aussi si besoin
from pathlib import Path
import uuid
import sys
import os

from models.dialogue_structure.interaction import Interaction
from services.interaction_service import InteractionService
from services.repositories.file_repository import FileInteractionRepository
from models.dialogue_structure.dynamic_interaction_schema import build_interaction_model_from_structure, validate_interaction_elements_order, convert_dynamic_to_standard_interaction
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
from .generation_panel.interaction_sequence_widget import InteractionSequenceWidget
from .generation_panel.interaction_editor_widget import InteractionEditorWidget
from .generation_panel.dialogue_structure_widget import DialogueStructureWidget

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

        # === MODIFIÉ : Utilisation du service injecté ===
        self.dialogue_generation_service = dialogue_generation_service
        if not self.dialogue_generation_service:
            # Fallback ou erreur si non fourni, bien que MainWindow devrait le fournir.
            logger.error("DialogueGenerationService non fourni à GenerationPanel!")
            # Optionnellement, créer une instance par défaut ici, mais l'injection est préférable.
            # self.dialogue_generation_service = DialogueGenerationService(
            # context_builder=self.context_builder, 
            # prompt_engine=self.prompt_engine, 
            # interaction_service=self.interaction_service
            # )
        # === FIN MODIFICATION ===

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
        interactions_tab = QWidget()
        interactions_tab_layout = QVBoxLayout(interactions_tab)
        # ... (code de l'onglet interactions inchangé)
        self.interaction_sequence_widget = InteractionSequenceWidget(
            interaction_service=self.interaction_service
        )
        interactions_tab_layout.addWidget(self.interaction_sequence_widget)
        self.interaction_editor_widget = InteractionEditorWidget(self.interaction_service)
        interactions_tab_layout.addWidget(self.interaction_editor_widget)
        interactions_tab_layout.addStretch(1)
        central_tabs.addTab(interactions_tab, "Interactions")

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
        self.scene_selection_widget.scene_region_changed.connect(self._on_scene_region_changed)
        self.scene_selection_widget.scene_sub_location_changed.connect(self._schedule_settings_save_and_token_update)
        self.scene_selection_widget.swap_characters_clicked.connect(self._swap_characters)

        self.context_actions_widget.select_linked_clicked.connect(self._on_select_linked_elements_clicked)
        self.context_actions_widget.unlink_unrelated_clicked.connect(self._on_unlink_unrelated_clicked)
        self.context_actions_widget.uncheck_all_clicked.connect(self._on_uncheck_all_clicked)

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

        self.interaction_sequence_widget.interaction_selected.connect(self._on_interaction_selected)
        self.interaction_sequence_widget.sequence_changed.connect(self._on_sequence_changed)
        self.interaction_sequence_widget.interaction_selected.connect(self._on_edit_interaction_requested)
        self.interaction_editor_widget.interaction_changed.connect(self._on_interaction_changed)

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
        self.populate_character_combos()
        self.populate_scene_combos()
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

    def populate_character_combos(self):
        characters = sorted(self.context_builder.get_characters_names())
        self.scene_selection_widget.character_a_combo.blockSignals(True)
        self.scene_selection_widget.character_b_combo.blockSignals(True)
        self.scene_selection_widget.character_a_combo.clear()
        self.scene_selection_widget.character_b_combo.clear()
        self.scene_selection_widget.character_a_combo.addItems([UIText.NONE] + characters)
        self.scene_selection_widget.character_b_combo.addItems([UIText.NONE] + characters)
        self.scene_selection_widget.character_a_combo.blockSignals(False)
        self.scene_selection_widget.character_b_combo.blockSignals(False)
        logger.debug("Character combos populated.")

    def populate_scene_combos(self):
        regions = sorted(self.context_builder.get_regions())
        self.scene_selection_widget.scene_region_combo.blockSignals(True)
        self.scene_selection_widget.scene_sub_location_combo.blockSignals(True)
        self.scene_selection_widget.scene_region_combo.clear()
        self.scene_selection_widget.scene_region_combo.addItem(UIText.NONE_FEM)
        self.scene_selection_widget.scene_region_combo.addItems(regions)
        self.scene_selection_widget.scene_region_combo.blockSignals(False)
        self.scene_selection_widget.scene_sub_location_combo.blockSignals(False)
        self._on_scene_region_changed(self.scene_selection_widget.scene_region_combo.currentText() or UIText.NONE_FEM)
        logger.debug("Scene region combo populated.")

    @Slot(str)
    def _on_scene_region_changed(self, region_name: str):
        self.scene_selection_widget.scene_sub_location_combo.clear()
        if region_name and region_name != UIText.NONE and region_name != UIText.NO_SELECTION:
            try:
                # sub_locations = sorted(self.context_builder.get_sub_locations_for_region(region_name))
                sub_locations = sorted(self.context_builder.get_sub_locations(region_name))
                if not sub_locations:
                    logger.info(f"Aucun sous-lieu trouvé pour la région : {region_name}")
                    self.scene_selection_widget.scene_sub_location_combo.addItem(UIText.NONE_SUBLOCATION)
                else:
                    self.scene_selection_widget.scene_sub_location_combo.addItems([UIText.ALL] + sub_locations)
                    self.scene_selection_widget.scene_sub_location_combo.setEnabled(True)
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des sous-lieux pour la région {region_name}: {e}", exc_info=True)
                self.scene_selection_widget.scene_sub_location_combo.addItem(UIText.ERROR_PREFIX + "Erreur de chargement des sous-lieux")
                self.scene_selection_widget.scene_sub_location_combo.setEnabled(False)
        else:
            self.scene_selection_widget.scene_sub_location_combo.addItem(UIText.NO_SELECTION)
            self.scene_selection_widget.scene_sub_location_combo.setEnabled(False)
        self._schedule_settings_save_and_token_update()
        logger.debug(f"Sub-location combo updated for region: {region_name}")

    def _swap_characters(self):
        current_a_index = self.scene_selection_widget.character_a_combo.currentIndex()
        current_b_index = self.scene_selection_widget.character_b_combo.currentIndex()
        self.scene_selection_widget.character_a_combo.setCurrentIndex(current_b_index)
        self.scene_selection_widget.character_b_combo.setCurrentIndex(current_a_index)
        logger.debug("Characters A and B swapped.")
        self._schedule_settings_save_and_token_update()

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
        if not self.prompt_engine or not self.context_builder or not self.llm_client:
            self.token_estimation_label.setText("Erreur: Moteurs non initialisés")
            self._display_prompt_in_tab("Erreur: Les moteurs (prompt, context, llm) ne sont pas tous initialisés.")
            return

        user_specific_goal = self.instructions_widget.get_user_instructions_text()
        selected_context_items = self.main_window_ref._get_current_context_selections() if hasattr(self.main_window_ref, '_get_current_context_selections') else {}

        char_a_name = self.scene_selection_widget.character_a_combo.currentText()
        char_b_name = self.scene_selection_widget.character_b_combo.currentText()
        scene_region_name = self.scene_selection_widget.scene_region_combo.currentText()
        scene_sub_location_name = self.scene_selection_widget.scene_sub_location_combo.currentText()

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
        
        full_prompt_for_estimation = "Erreur lors de la construction du prompt pour estimation." # Message par défaut
        context_tokens = 0
        prompt_tokens = 0

        try:
            # MODIFIÉ: Utiliser config_service depuis main_window_ref
            max_tokens_val = self.main_window_ref.config_service.get_ui_setting("max_context_tokens", Defaults.CONTEXT_TOKENS)
            
            # Assurer que le prompt_engine a le system_prompt à jour de l'UI pour une estimation correcte
            self._update_prompt_engine_system_prompt()

            # Construire le résumé du contexte d'abord
            context_summary_text_for_estimation = self.context_builder.build_context(
                selected_elements=selected_context_items,
                scene_instruction=user_specific_goal, 
                max_tokens=max_tokens_val 
                # include_dialogue_type n'est pas utilisé par context_builder.build_context directement
            )
            context_tokens = self.prompt_engine._count_tokens(context_summary_text_for_estimation) if context_summary_text_for_estimation else 0

            # Utiliser build_prompt pour obtenir le prompt complet et son nombre total de tokens
            full_prompt_for_estimation, prompt_tokens = self.prompt_engine.build_prompt(
                user_specific_goal=user_specific_goal,
                scene_protagonists=scene_protagonists_dict if scene_protagonists_dict else None,
                scene_location=scene_location_dict if scene_location_dict else None,
                context_summary=context_summary_text_for_estimation,
                generation_params={ # Passer les paramètres qui pourraient affecter la structure du prompt pour l'estimation
                    "dialogue_structure_narrative": self.dialogue_structure_widget.get_structure_description() 
                }
            )
            
            # current_prompt n'est plus retourné par une méthode séparée, c'est full_prompt_for_estimation
            # context_str est context_summary_text_for_estimation

            logger.debug(f"[GenerationPanel.update_token_estimation_ui] Context summary for estimation (first 300 chars): {context_summary_text_for_estimation[:300] if context_summary_text_for_estimation else 'None'}")
            logger.debug(f"[GenerationPanel.update_token_estimation_ui] Full prompt for estimation (first 300 chars): {full_prompt_for_estimation[:300] if full_prompt_for_estimation else 'None'}")

        except Exception as e:
            logger.error(f"Erreur pendant la construction du prompt dans update_token_estimation_ui: {e}", exc_info=True)
            full_prompt_for_estimation = f"Erreur lors de la génération du prompt estimé:\\n{type(e).__name__}: {e}"
            # Les tokens resteront à 0 ou à leur dernière valeur valide avant l'erreur

        # Affichage des tokens en milliers (k)
        context_tokens_k = context_tokens / 1000
        prompt_tokens_k = prompt_tokens / 1000
        self.token_estimation_label.setText(f"Tokens (contexte GDD/prompt total): {context_tokens_k:.1f}k / {prompt_tokens_k:.1f}k")
        logger.debug(f"Token estimation UI updated: Context GDD {context_tokens} ({context_tokens_k:.1f}k), Prompt total {prompt_tokens} ({prompt_tokens_k:.1f}k).")
        
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

        asyncio.create_task(self._on_generate_dialogue_button_clicked_local())

    async def _on_generate_dialogue_button_clicked_local(self):
        # Appelé par _launch_dialogue_generation qui gère le changement de curseur et le try/except global
        logger.info("Début de la génération de dialogue (méthode locale asynchrone).")
        self.generation_progress_bar.setRange(0, 0) # Indeterminate
        self.generation_progress_bar.setVisible(True)
        self.generate_dialogue_button.setEnabled(False)

        generation_succeeded = True # Renommé de generation_succeded
        # Initialisation de full_prompt pour le cas où la génération échoue avant sa définition
        full_prompt_for_display = "Erreur: Le prompt n'a pas pu être construit."
        estimated_tokens_for_display = 0

        try:
            k_variants = int(self.k_variants_combo.currentText())
            user_instructions = self.instructions_widget.get_user_instructions_text()
            system_prompt_override = self.instructions_widget.get_system_prompt_text() # Récupérer le prompt système de l'UI
            selected_gdd_items = self.main_window_ref._get_current_context_selections() # Récupère les items GDD cochés
            
            char_a_name = self.scene_selection_widget.character_a_combo.currentText()
            char_b_name = self.scene_selection_widget.character_b_combo.currentText()
            scene_region_name = self.scene_selection_widget.scene_region_combo.currentText()
            scene_sub_location_name = self.scene_selection_widget.scene_sub_location_combo.currentText()

            # Nettoyage des noms pour éviter de passer UIText.NONE ou des chaînes vides si non pertinents
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
            
            # Mettre à jour le moteur de prompt avec le system prompt actuel de l'UI AVANT de construire le contexte
            # Ceci est maintenant géré DANS le service si system_prompt_override est passé.
            # self._update_prompt_engine_system_prompt() 

            # --- Préparation des informations pour le service --- 
            # Le service attend _scene_protagonists et _scene_location DANS context_selections
            context_selections_for_service = selected_gdd_items.copy() # Commencer avec les items GDD
            context_selections_for_service["_scene_protagonists"] = scene_protagonists_dict
            context_selections_for_service["_scene_location"] = scene_location_dict
            # S'assurer que generate_interaction est bien dans les settings du contexte si besoin pour le prompt engine via le service
            # context_selections_for_service["generate_interaction"] = True 
            # (sera inféré par le service en fonction de la méthode appelée ou passé dans generation_params)

            dialogue_structure_description = self.dialogue_structure_widget.get_structure_description()
            dialogue_structure_elements = self.dialogue_structure_widget.get_structure() # ex: ["dialogue_line", "command"]
            target_response_model_pydantic = build_interaction_model_from_structure(dialogue_structure_elements)

            max_context_tokens_val = self.main_window_ref.config_service.get_ui_setting("max_context_tokens", Defaults.CONTEXT_TOKENS)

            logger.info(f"Appel de dialogue_generation_service.generate_structured_object_variants avec k={k_variants}...")
            logger.info(f"[STRUCTURED] Modèle Pydantic dynamique pour la structure: {dialogue_structure_elements}")
            logger.info(f"[STRUCTURED] Schéma du modèle: {target_response_model_pydantic.model_json_schema()}")

            # Appel au service au lieu de l'appel LLM direct
            variants_objects, full_prompt_from_service, estimated_tokens_from_service = \
                await self.dialogue_generation_service.generate_structured_object_variants(
                    llm_client=self.llm_client, 
                    k_variants=k_variants, 
                    max_context_tokens_for_context_builder=max_context_tokens_val,
                    user_instructions=user_instructions, 
                    system_prompt_override=system_prompt_override,
                    context_selections=context_selections_for_service, # Contient GDD items, _scene_protagonists, _scene_location
                    dialogue_structure_description=dialogue_structure_description, # Pour le prompt engine dans le service
                    target_response_model=target_response_model_pydantic,
                    current_llm_model_identifier=self.current_llm_model_identifier
                )
            
            # Mettre à jour les variables pour l'affichage du prompt et des tokens
            full_prompt_for_display = full_prompt_from_service
            estimated_tokens_for_display = estimated_tokens_from_service

            if full_prompt_for_display:
                estimated_tokens_k = estimated_tokens_for_display / 1000 if estimated_tokens_for_display else 0
                self.token_estimation_label.setText(f"Tokens prompt final: {estimated_tokens_k:.1f}k")
                self._display_prompt_in_tab(full_prompt_for_display)
            else:
                self.token_estimation_label.setText("Tokens prompt final: Erreur")
                self._display_prompt_in_tab("Erreur: Le prompt n'a pas pu être construit par le service.")

            logger.debug(f"Valeur de 'variants_objects' reçue du service: Type={type(variants_objects)}, Nombre={len(variants_objects) if variants_objects else 0}")
            if variants_objects:
                logger.debug(f"Type du premier élément dans variants_objects: {type(variants_objects[0])}")
            
                self.variants_display_widget.blockSignals(True)
                num_tabs_to_keep = 0
                if self.variants_display_widget.count() > 0 and self.variants_display_widget.tabText(0) == "Prompt Estimé":
                    num_tabs_to_keep = 1
                
                while self.variants_display_widget.count() > num_tabs_to_keep:
                    self.variants_display_widget.removeTab(num_tabs_to_keep)
                
                if variants_objects: # Remplacer variants par variants_objects
                    for i, variant_data_obj in enumerate(variants_objects): # Remplacer variant_data par variant_data_obj
                        # Le service retourne directement des objets Pydantic conformes au target_response_model
                        # Ces objets devraient être des DynamicInteraction (ou équivalent basé sur la structure)
                        if isinstance(variant_data_obj, Interaction) or (hasattr(variant_data_obj, '__class__') and 'DynamicInteraction' in str(type(variant_data_obj))):
                            # Validation stricte de la structure
                            # La structure est déjà validée par le modèle Pydantic lors de la génération par le LLM (si response_model est utilisé)
                            # Mais on peut faire une validation de l'ordre des éléments si nécessaire.
                            is_valid_order = validate_interaction_elements_order(variant_data_obj, dialogue_structure_elements)
                            if not is_valid_order:
                                logger.error(f"[VALIDATION STRUCTURE] La variante générée (objet) ne respecte pas l'ordre des éléments de la structure imposée : {dialogue_structure_elements}")
                                error_text = ("// Erreur : La variante générée (objet) ne respecte pas l'ordre des éléments imposé par la structure :\n"
                                              f"Structure attendue : {dialogue_structure_elements}\n"
                                              f"Types reçus : {[type(e).__name__ for e in getattr(variant_data_obj, 'elements', [])]}")
                                text_edit = QTextEdit(error_text)
                                text_edit.setReadOnly(True)
                                self.variants_display_widget.addTab(text_edit, f"Variante {i+1} (Erreur Ordre Structure)")
                                continue
                            logger.info(f"[VALIDATION STRUCTURE] Variante {i+1} (objet) conforme à l'ordre des éléments de la structure imposée.")
                            
                            # +++ CONVERSION EN INTERACTION STANDARD +++
                            try:
                                standard_interaction = convert_dynamic_to_standard_interaction(variant_data_obj)
                                self.variants_display_widget.add_interaction_tab(f"Variante {i+1}", standard_interaction)
                                logger.info(f"[LOG_DEBUG] Variante {i+1} (DynamicInteraction objet converti en Interaction) ajoutée via add_interaction_tab. ID: {standard_interaction.interaction_id}")
                            except ValueError as ve:
                                logger.error(f"Erreur de conversion de DynamicInteraction (objet) en Interaction: {ve}", exc_info=True)
                                error_text_conversion = ("// Erreur : Impossible de convertir la variante DynamicInteraction (objet) en Interaction standard.\n"
                                                       f"{ve}")
                                text_edit_conv = QTextEdit(error_text_conversion)
                                text_edit_conv.setReadOnly(True)
                                self.variants_display_widget.addTab(text_edit_conv, f"Variante {i+1} (Erreur Conversion)")
                                continue
                                
                        # Si ce n'est pas un DynamicInteraction ou Interaction, c'est une erreur car le service devrait retourner cela.
                        # Ou alors, le target_response_model était autre chose, auquel cas il faut adapter l'affichage.
                        elif isinstance(variant_data_obj, str): # Ne devrait plus arriver avec generate_structured_object_variants
                            logger.warning(f"[LOG_DEBUG] Variante {i+1} est une chaîne (str), inattendu du service pour objets structurés. Affichage brut.")
                            self.variants_display_widget.add_variant_tab(f"Variante {i+1}", variant_data_obj)
                        else:
                            display_text = f"// Erreur: Type de variante structurée inattendu du service: {type(variant_data_obj)}"
                            logger.warning(f"[LOG_DEBUG] Variante {i+1} (inattendu du service pour objets structurés): {type(variant_data_obj)}")
                            text_edit = QTextEdit(display_text)
                            text_edit.setReadOnly(True)
                            self.variants_display_widget.addTab(text_edit, f"Variante {i+1} (Inattendu Service)")
                    
                    generation_succeeded = True # Renommé de generation_succeded
                    logger.info(f"{len(variants_objects)} variantes (objets) affichées.") # Remplacer variants par variants_objects
                else:
                    logger.warning("Aucune variante (objet) reçue du service ou variants_objects est None/vide.")
                    error_tab = QTextEdit(UIText.NO_VARIANT)
                    self.variants_display_widget.addTab(error_tab, "Erreur Génération Service")
                
                self.variants_display_widget.blockSignals(False)

        except asyncio.CancelledError:
            logger.warning("La tâche de génération de dialogue a été annulée.")
            # Assurer que le prompt est affiché même si annulé pendant la génération LLM mais après la construction du prompt
            if full_prompt_for_display and full_prompt_for_display != "Erreur: Le prompt n'a pas pu être construit.":
                self._display_prompt_in_tab(full_prompt_for_display)
            return 
        except Exception as e:
            logger.error(f"Erreur majeure lors de la génération des dialogues: {e}", exc_info=True)
            # Afficher le prompt même en cas d'erreur si disponible
            if full_prompt_for_display and full_prompt_for_display != "Erreur: Le prompt n'a pas pu être construit.":
                 self._display_prompt_in_tab(full_prompt_for_display)
            else:
                self._display_prompt_in_tab(f"Erreur critique avant la construction du prompt: {type(e).__name__}: {e}")

            self.variants_display_widget.blockSignals(True)
            num_tabs_to_keep_err = 0
            if self.variants_display_widget.count() > 0 and self.variants_display_widget.tabText(0) == "Prompt Estimé":
                num_tabs_to_keep_err = 1
            while self.variants_display_widget.count() > num_tabs_to_keep_err:
                self.variants_display_widget.removeTab(num_tabs_to_keep_err)
            
            error_tab_content = QTextEdit()
            error_tab_content.setPlainText(f"Une erreur majeure est survenue lors de la génération:\n\n{type(e).__name__}: {e}")
            error_tab_content.setReadOnly(True)
            self.variants_display_widget.addTab(error_tab_content, "Erreur Critique")
            self.variants_display_widget.blockSignals(False)
        finally:
            current_task = asyncio.current_task()
            if not current_task or not current_task.cancelled(): 
                self.generation_progress_bar.setVisible(False)
                self.generate_dialogue_button.setEnabled(True)
                QApplication.processEvents() 
                logger.debug(f"Émission du signal generation_finished avec la valeur : {generation_succeeded}") # Renommé de generation_succeded
                self.generation_finished.emit(generation_succeeded) # Renommé de generation_succeded

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
                self.interaction_sequence_widget.interaction_selected.disconnect(self._on_interaction_selected)
            except Exception:
                pass  # Pas critique si déjà déconnecté

            self.interaction_sequence_widget.refresh_list(select_id=str(interaction.interaction_id))

            # Affiche l'interaction dans l'éditeur
            self.interaction_editor_widget.set_interaction(interaction)

            # Reconnecte le signal
            try:
                self.interaction_sequence_widget.interaction_selected.connect(self._on_interaction_selected)
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
    def _on_select_linked_elements_clicked(self) -> None:
        """
        Slot pour le bouton "Lier Éléments Connexes".
        Récupère les personnages A/B et la scène, puis demande au LeftSelectionPanel
        de cocher tous les éléments du GDD qui leur sont liés.
        """
        char_a_raw = self.scene_selection_widget.character_a_combo.currentText()
        char_b_raw = self.scene_selection_widget.character_b_combo.currentText()
        scene_region_raw = self.scene_selection_widget.scene_region_combo.currentText()
        scene_sub_location_raw = self.scene_selection_widget.scene_sub_location_combo.currentText()

        placeholders = [UIText.NONE, UIText.NONE_FEM, UIText.ALL, UIText.NONE_SUBLOCATION, UIText.NO_SELECTION]

        char_a = None if char_a_raw in placeholders or not char_a_raw.strip() else char_a_raw
        char_b = None if char_b_raw in placeholders or not char_b_raw.strip() else char_b_raw
        scene_region = None if scene_region_raw in placeholders or not scene_region_raw.strip() else scene_region_raw
        scene_sub_location = None if scene_sub_location_raw in placeholders or not scene_sub_location_raw.strip() else scene_sub_location_raw

        # Utilise la méthode existante du LinkedSelectorService
        elements_to_select_set = self.linked_selector.get_elements_to_select(
            char_a, char_b, scene_region, scene_sub_location
        )
        elements_to_select_list = list(elements_to_select_set)


        if hasattr(self.main_window_ref, 'left_panel'):
            if elements_to_select_list:
                # La règle 'linkedelements' indique d'utiliser set_checked_items_by_name
                # Cette méthode coche les items de la liste et décoche les autres.
                # Si le but est d'AJOUTER à la sélection existante, il faut d'abord lire les existants.
                current_checked_items = self.main_window_ref.left_panel.get_all_selected_item_names()
                combined_items_to_check = list(set(current_checked_items + elements_to_select_list))
                self.main_window_ref.left_panel.set_checked_items_by_name(combined_items_to_check)
                
                logger.info(f"Éléments liés ({len(elements_to_select_list)}) ajoutés à la sélection existante. Total coché: {len(combined_items_to_check)}")
                self.main_window_ref.statusBar().showMessage(f"{len(elements_to_select_list)} éléments liés ajoutés à la sélection.", 3000)
            else:
                logger.info("Aucun élément supplémentaire à lier trouvé pour le contexte principal.")
                self.main_window_ref.statusBar().showMessage("Aucun nouvel élément lié trouvé.", 3000)
        else:
            logger.warning("Référence à left_panel non trouvée dans main_window_ref.")


    @Slot()
    def _on_unlink_unrelated_clicked(self) -> None:
        """
        Slot pour le bouton "Décocher Non-Connexes".
        Récupère les personnages A/B et la scène, puis demande au LeftSelectionPanel
        de ne garder cochés QUE les éléments du GDD qui leur sont liés.
        """
        char_a_raw = self.scene_selection_widget.character_a_combo.currentText()
        char_b_raw = self.scene_selection_widget.character_b_combo.currentText()
        scene_region_raw = self.scene_selection_widget.scene_region_combo.currentText()
        scene_sub_location_raw = self.scene_selection_widget.scene_sub_location_combo.currentText()

        placeholders = [UIText.NONE, UIText.NONE_FEM, UIText.ALL, UIText.NONE_SUBLOCATION, UIText.NO_SELECTION]

        char_a = None if char_a_raw in placeholders or not char_a_raw.strip() else char_a_raw
        char_b = None if char_b_raw in placeholders or not char_b_raw.strip() else char_b_raw
        scene_region = None if scene_region_raw in placeholders or not scene_region_raw.strip() else scene_region_raw
        scene_sub_location = None if scene_sub_location_raw in placeholders or not scene_sub_location_raw.strip() else scene_sub_location_raw

        currently_checked_set = set()
        if hasattr(self.main_window_ref, 'left_panel'):
            # Utiliser la méthode publique pour obtenir les noms des items cochés
            currently_checked_list = self.main_window_ref.left_panel.get_all_selected_item_names()
            currently_checked_set = set(currently_checked_list)
        else:
            logger.warning("Référence à left_panel non trouvée lors de la récupération des items cochés.")


        # Utilise la méthode existante du LinkedSelectorService
        items_to_keep_checked = self.linked_selector.compute_items_to_keep_checked(
            currently_checked_set,
            char_a, 
            char_b, 
            scene_region, 
            scene_sub_location
        )

        if hasattr(self.main_window_ref, 'left_panel'):
            # set_checked_items_by_name cochera les items de la liste et décochera les autres.
            # Si items_to_keep_checked est vide, cela décochera tout.
            self.main_window_ref.left_panel.set_checked_items_by_name(items_to_keep_checked)
            
            logger.info(f"Conservation des éléments liés : {items_to_keep_checked}, autres décochés.")
            if items_to_keep_checked:
                self.main_window_ref.statusBar().showMessage(f"Seuls les {len(items_to_keep_checked)} éléments liés sont conservés.", 3000)
            else:
                self.main_window_ref.statusBar().showMessage("Aucun élément lié à conserver. Tous les éléments secondaires ont été décochés.", 3000)
        else:
            logger.warning("Référence à left_panel non trouvée pour mettre à jour les coches.")

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
        settings = {
            "character_a": self.scene_selection_widget.character_a_combo.currentText(),
            "character_b": self.scene_selection_widget.character_b_combo.currentText(),
            "scene_region": self.scene_selection_widget.scene_region_combo.currentText(),
            "scene_sub_location": self.scene_selection_widget.scene_sub_location_combo.currentText(),
            "k_variants": self.k_variants_combo.currentText(),
            "user_instructions": self.instructions_widget.get_user_instructions_text(),
            "llm_model": self.llm_model_combo.currentData(), # Sauvegarde l'identifiant du modèle
            "system_prompt": self.instructions_widget.get_system_prompt_text(),
            "max_context_tokens": self.max_context_tokens_spinbox.value(),
            "dialogue_structure": self.dialogue_structure_widget.get_structure()
        }
        logger.debug(f"Récupération des paramètres du GenerationPanel: {settings}")
        return settings

    def load_settings(self, settings: dict):
        logger.debug(f"Chargement des paramètres dans GenerationPanel: {settings}")
        self._is_loading_settings = True
        
        self.scene_selection_widget.character_a_combo.setCurrentText(settings.get("character_a", ""))
        self.scene_selection_widget.character_b_combo.setCurrentText(settings.get("character_b", ""))
        self.scene_selection_widget.scene_region_combo.setCurrentText(settings.get("scene_region", ""))
        QApplication.processEvents()
        self.scene_selection_widget.scene_sub_location_combo.setCurrentText(settings.get("scene_sub_location", ""))
        
        self.k_variants_combo.setCurrentText(settings.get("k_variants", "3"))
        
        # MODIFIÉ: Appel à load_settings de InstructionsWidget
        instruction_settings_to_load = {
            "user_instructions": settings.get("user_instructions", ""),
            "system_prompt": settings.get("system_prompt") # Peut être None, InstructionsWidget.load_settings gère cela
        }
        default_system_prompt_for_iw = self.prompt_engine._get_default_system_prompt() if self.prompt_engine else ""
        self.instructions_widget.load_settings(
            instruction_settings_to_load, 
            default_user_instructions="", # La valeur est déjà extraite dans instruction_settings_to_load
            default_system_prompt=default_system_prompt_for_iw
        )
        
        model_identifier = settings.get("llm_model")
        if model_identifier:
            # MODIFIÉ: Délégué à GenerationParamsWidget
            if hasattr(self, 'generation_params_widget') and self.generation_params_widget:
                self.generation_params_widget.select_model_in_combo(model_identifier)
        else:
            # Si aucun modèle n'est sauvegardé, essayer de sélectionner le premier de la liste
            # La logique est maintenant dans GenerationParamsWidget.populate_llm_model_combo
            if hasattr(self, 'generation_params_widget') and self.generation_params_widget and self.generation_params_widget.llm_model_combo.count() > 0:
                 self.generation_params_widget.llm_model_combo.setCurrentIndex(0)
        
        if "dialogue_structure" in settings:
            self.dialogue_structure_widget.set_structure(settings["dialogue_structure"])
        
        # Restaure la valeur sauvegardée pour max_context_tokens si présente
        if "max_context_tokens" in settings:
            self.max_context_tokens_spinbox.setValue(settings["max_context_tokens"])
        
        self._is_loading_settings = False
        self.update_token_estimation_signal.emit()
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
                
                # Afficher l'interaction dans l'éditeur
                self.interaction_editor_widget.set_interaction(interaction)
            else:
                logger.warning(f"Interaction {interaction_id} non trouvée par le service.")
                self.main_window_ref.statusBar().showMessage(UIText.ERROR_PREFIX + f"Interaction {interaction_id} non trouvée.", 3000)
                self.interaction_editor_widget.set_interaction(None)
        else:
            logger.info("Aucune interaction sélectionnée.")
            self.main_window_ref.statusBar().showMessage(UIText.NO_INTERACTION_FOUND, 3000)
            self.interaction_editor_widget.set_interaction(None)

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
                interactions_tab_index = tabs.indexOf(self.interaction_sequence_widget.parent())
                if interactions_tab_index >= 0 and tabs.currentIndex() != interactions_tab_index:
                    tabs.setCurrentIndex(interactions_tab_index)
            
            # Afficher l'interaction dans l'éditeur
            self.interaction_editor_widget.set_interaction(interaction)
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
        self.interaction_sequence_widget.refresh_list()
        
        title_display = getattr(interaction, 'title', str(interaction.interaction_id)[:8])
        self.main_window_ref.statusBar().showMessage(f"Interaction '{title_display}' mise à jour.", 3000)