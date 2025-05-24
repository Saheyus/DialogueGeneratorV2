from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QGridLayout, 
                               QLabel, QTextEdit, QPushButton, 
                               QTabWidget, QApplication, QSizePolicy, QScrollArea, QSplitter, QMessageBox, QSpacerItem, QStyle, QHBoxLayout, QCheckBox)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QPalette, QColor, QFont, QIcon, QAction, QCursor
import logging
import asyncio
from typing import Optional, Callable, Any, Dict, List
import json
from pathlib import Path
import uuid
import os

# Import pour Interaction
try:
    from ..models.dialogue_structure.interaction import Interaction
except ImportError:
    import sys
    from pathlib import Path
    current_dir = Path(__file__).resolve().parent.parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    from DialogueGenerator.models.dialogue_structure.interaction import Interaction

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
    from ..services.linked_selector import LinkedSelectorService
    from ..services.yarn_renderer import JinjaYarnRenderer
    from ..services.interaction_service import InteractionService
    from ..llm_client import OpenAIClient, DummyLLMClient
    from ..services.dialogue_generation_service import DialogueGenerationService
except ImportError:
    # Support exécution directe
    import sys, os, pathlib
    current_dir = pathlib.Path(__file__).resolve().parent.parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    from DialogueGenerator.services.linked_selector import LinkedSelectorService
    from DialogueGenerator.services.yarn_renderer import JinjaYarnRenderer
    from DialogueGenerator.services.interaction_service import InteractionService
    from DialogueGenerator.llm_client import OpenAIClient, DummyLLMClient
    from DialogueGenerator.services.dialogue_generation_service import DialogueGenerationService

# Import du repository de fichiers
from DialogueGenerator.services.repositories.file_repository import FileInteractionRepository

logger = logging.getLogger(__name__)

DIALOGUE_GENERATOR_DIR = Path(__file__).resolve().parent.parent
LLM_CONFIG_FILE_PATH = DIALOGUE_GENERATOR_DIR / "llm_config.json"

class GenerationPanel(QWidget):
    settings_changed = Signal() 
    generation_requested: Signal = Signal(str, int, str, str, str, str, list)
    update_token_estimation_signal: Signal = Signal()
    generation_finished = Signal(bool)
    llm_model_selection_changed = Signal(str)

    def __init__(self, context_builder, prompt_engine, llm_client, available_llm_models, current_llm_model_identifier, main_window_ref, parent=None):
        super().__init__(parent)
        
        self.context_builder = context_builder
        self.prompt_engine = prompt_engine
        self.llm_client = llm_client
        self.main_window_ref = main_window_ref
        
        # Configuration du service d'interaction avec stockage fichier
        interactions_dir = Path(__file__).resolve().parent.parent / "data" / "interactions"
        os.makedirs(interactions_dir, exist_ok=True)
        print(f"Dossier de stockage des interactions: {interactions_dir}")
        interaction_repository = FileInteractionRepository(str(interactions_dir))
        self.interaction_service = InteractionService(repository=interaction_repository)
        
        self.linked_selector = LinkedSelectorService(self.context_builder)
        self.yarn_renderer = JinjaYarnRenderer()
        self.dialogue_generation_service = DialogueGenerationService(
            self.context_builder, 
            self.prompt_engine,
            self.interaction_service
        )
        
        self.available_llm_models = available_llm_models if available_llm_models else []
        self.current_llm_model_identifier = current_llm_model_identifier
        
        self._is_settings_loading = False
        self._is_loading_settings = False
        
        self._init_ui()
        print(f"[DEBUG] GenerationPanel construit: self={self}, generated_variants_tabs={getattr(self, 'generated_variants_tabs', None)} @ {id(getattr(self, 'generated_variants_tabs', None))}")

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)

        left_column_widget = QWidget()
        left_column_layout = QVBoxLayout(left_column_widget)
        left_column_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # main_splitter.addWidget(left_column_widget) # Retiré car vide pour l'instant

        # --- QTabWidget central ---
        central_tabs = QTabWidget()
        main_splitter.addWidget(central_tabs) # Maintenant à l'index 0

        # --- Onglet 1 : Interactions ---
        interactions_tab = QWidget()
        interactions_tab_layout = QVBoxLayout(interactions_tab)
        interactions_tab_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.interaction_sequence_widget = InteractionSequenceWidget(self.interaction_service)
        interactions_tab_layout.addWidget(self.interaction_sequence_widget)
        self.interaction_sequence_widget.interaction_selected.connect(self._on_interaction_selected)
        self.interaction_sequence_widget.sequence_changed.connect(self._on_sequence_changed)
        
        # Ajout de l'éditeur d'interaction juste sous la séquence
        self.interaction_editor_widget = InteractionEditorWidget(self.interaction_service, self.context_builder)
        interactions_tab_layout.addWidget(self.interaction_editor_widget)
        self.interaction_editor_widget.interaction_saved.connect(lambda: self.interaction_sequence_widget.refresh_list(select_id=self.interaction_editor_widget.current_interaction.interaction_id if self.interaction_editor_widget.current_interaction else None))

        interactions_tab_layout.addStretch(1)
        central_tabs.addTab(interactions_tab, "Interactions")

        # --- Onglet 2 : Génération ---
        generation_tab = QWidget()
        generation_tab_layout = QVBoxLayout(generation_tab)
        generation_tab_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scene_selection_widget = SceneSelectionWidget(self.context_builder)
        generation_tab_layout.addWidget(self.scene_selection_widget)
        self.scene_selection_widget.character_a_changed.connect(self._schedule_settings_save_and_token_update)
        self.scene_selection_widget.character_b_changed.connect(self._schedule_settings_save_and_token_update)
        self.scene_selection_widget.scene_region_changed.connect(self._schedule_settings_save_and_token_update)
        self.scene_selection_widget.scene_sub_location_changed.connect(self._schedule_settings_save_and_token_update)
        self.scene_selection_widget.swap_characters_clicked.connect(self._swap_characters)

        self.context_actions_widget = ContextActionsWidget()
        generation_tab_layout.addWidget(self.context_actions_widget)
        self.context_actions_widget.select_linked_clicked.connect(self._on_select_linked_elements_clicked)
        self.context_actions_widget.unlink_unrelated_clicked.connect(self._on_unlink_unrelated_clicked)
        self.context_actions_widget.uncheck_all_clicked.connect(self._on_uncheck_all_clicked)

        self.generation_params_widget = GenerationParamsWidget(
            self.available_llm_models,
            self.current_llm_model_identifier
        )
        generation_tab_layout.addWidget(self.generation_params_widget)
        self.generation_params_widget.llm_model_selection_changed.connect(self._on_llm_model_selected_from_widget)
        self.generation_params_widget.k_variants_changed.connect(self._schedule_settings_save)
        self.generation_params_widget.max_context_tokens_changed.connect(self._on_max_context_tokens_changed_from_widget)
        self.generation_params_widget.structured_output_changed.connect(self._schedule_settings_save)
        self.generation_params_widget.settings_changed.connect(self._schedule_settings_save_and_token_update)
        
        # Ajout d'une checkbox pour la génération d'interactions structurées
        self.generate_interaction_checkbox = QCheckBox("Générer une Interaction structurée")
        self.generate_interaction_checkbox.setToolTip("Si coché, le LLM générera une structure JSON compatible avec le modèle Interaction")
        self.generate_interaction_checkbox.setChecked(False)
        self.generate_interaction_checkbox.stateChanged.connect(self._on_generate_interaction_state_changed)
        generation_tab_layout.addWidget(self.generate_interaction_checkbox)

        # Widget de contrôle de structure de dialogue
        self.dialogue_structure_widget = DialogueStructureWidget()
        generation_tab_layout.addWidget(self.dialogue_structure_widget)
        self.dialogue_structure_widget.structure_changed.connect(self._on_dialogue_structure_changed)
        self.dialogue_structure_widget.structure_changed.connect(self._schedule_settings_save_and_token_update)

        self.instructions_widget = InstructionsWidget()
        generation_tab_layout.addWidget(self.instructions_widget)
        self.instructions_widget.user_instructions_changed.connect(self._schedule_settings_save_and_token_update)
        self.instructions_widget.system_prompt_changed.connect(self._on_system_prompt_changed_from_widget)
        self.instructions_widget.restore_default_system_prompt_clicked.connect(self._restore_default_system_prompt)
        self.instructions_widget.settings_changed.connect(self._schedule_settings_save_and_token_update)

        self.token_actions_widget = TokenEstimationActionsWidget()
        generation_tab_layout.addWidget(self.token_actions_widget)
        self.token_actions_widget.refresh_token_clicked.connect(self._trigger_token_update)
        self.token_actions_widget.generate_dialogue_clicked.connect(self._launch_dialogue_generation)

        generation_tab_layout.addStretch(1)
        central_tabs.addTab(generation_tab, "Génération")

        # --- Colonne de Droite: Affichage des Variantes ---
        right_column_widget = QWidget()
        right_column_layout = QVBoxLayout(right_column_widget)
        self.generated_variants_tabs = GeneratedVariantsTabsWidget()
        right_column_layout.addWidget(self.generated_variants_tabs)
        print(f"[DEBUG] _init_ui: generated_variants_tabs instance={self.generated_variants_tabs} @ {id(self.generated_variants_tabs)}")
        main_splitter.addWidget(right_column_widget)

        self.generated_variants_tabs.validate_variant_requested.connect(self._on_validate_variant_requested_from_tabs)
        self.generated_variants_tabs.validate_interaction_requested.connect(self._on_validate_interaction_requested_from_tabs)
        self.generated_variants_tabs.save_all_variants_requested.connect(self._on_save_all_variants_requested_from_tabs)
        self.generated_variants_tabs.regenerate_variant_requested.connect(self._on_regenerate_variant_requested_from_tabs)

        # Ajustement des indices et des proportions pour le splitter
        main_splitter.setStretchFactor(0, 1)  # central_tabs (anciennement index 1)
        main_splitter.setStretchFactor(1, 3)  # right_column_widget (anciennement index 2) - augmenté de 2 à 3
        
        # Ajustement des largeurs initiales - plus de place pour le panneau de droite
        initial_widths = [self.width() * 1 // 4 if self.width() > 0 else 250, 
                          self.width() * 3 // 4 if self.width() > 0 else 750]  # Augmenté de 2/3 à 3/4
        if all(w > 50 for w in initial_widths):
            main_splitter.setSizes(initial_widths)
        else:
            logger.warning("Largeurs initiales pour main_splitter (2 éléments) non valides, utilisation des tailles par défaut.")
        
        self.update_token_estimation_signal.connect(self.update_token_estimation_ui)

    def finalize_ui_setup(self):
        logger.debug("Finalizing GenerationPanel UI setup...")
        character_names = sorted(self.context_builder.get_characters_names())
        region_names = sorted(self.context_builder.get_regions())
        self.scene_selection_widget.populate_characters(character_names)
        self.scene_selection_widget.populate_regions(region_names)
        self.generation_params_widget.populate_llm_model_combo()
        self._trigger_token_update() 
        logger.debug("GenerationPanel UI setup finalized.")

    @Slot(str)
    def _on_llm_model_selected_from_widget(self, selected_identifier: str):
        if selected_identifier and selected_identifier != self.current_llm_model_identifier and selected_identifier != "dummy_error":
            logger.info(f"Sélection du modèle LLM relayée au GenerationPanel : {selected_identifier}")
            self.current_llm_model_identifier = selected_identifier
            self.llm_model_selection_changed.emit(selected_identifier)
            self._schedule_settings_save_and_token_update()
            self._update_structured_output_checkbox_state()

    def _update_structured_output_checkbox_state(self):
        current_model_props = self.main_window_ref.get_current_llm_model_properties()
        self.generation_params_widget.update_llm_client_dependent_state(self.llm_client, current_model_props)

    def _restore_default_system_prompt(self):
        default_prompt = self.prompt_engine._get_default_system_prompt()
        self.instructions_widget.set_system_prompt_text(default_prompt)
        self._update_prompt_engine_system_prompt()
        self.update_token_estimation_signal.emit()
        QMessageBox.information(self, "Prompt Restauré", "Le prompt système par défaut a été restauré.")

    @Slot()
    def _on_system_prompt_changed_from_widget(self):
        self._update_prompt_engine_system_prompt()
        self._schedule_settings_save_and_token_update()

    def _update_prompt_engine_system_prompt(self):
        new_system_prompt = self.instructions_widget.get_system_prompt_text()
        if self.prompt_engine.system_prompt_template != new_system_prompt:
            self.prompt_engine.system_prompt_template = new_system_prompt
            logger.info("PromptEngine system_prompt_template mis à jour via InstructionsWidget.")

    def set_llm_client(self, new_llm_client):
        logger.info(f"GenerationPanel: Réception d'un nouveau client LLM: {type(new_llm_client).__name__}")
        self.llm_client = new_llm_client
        model_identifier_to_select = None
        if hasattr(new_llm_client, 'model'):
            model_identifier_to_select = new_llm_client.model
        elif isinstance(new_llm_client, DummyLLMClient):
            model_identifier_to_select = "dummy"
        
        if model_identifier_to_select:
            self.current_llm_model_identifier = model_identifier_to_select
            self.generation_params_widget.select_model_in_combo(model_identifier_to_select)

        self._trigger_token_update()
        self._update_structured_output_checkbox_state()

    def _swap_characters(self):
        current_a_index = self.scene_selection_widget.character_a_combo.currentIndex()
        current_b_index = self.scene_selection_widget.character_b_combo.currentIndex()
        self.scene_selection_widget.character_a_combo.setCurrentIndex(current_b_index)
        self.scene_selection_widget.character_b_combo.setCurrentIndex(current_a_index)
        logger.debug("Characters A and B swapped via GenerationPanelBase method.")
        self._schedule_settings_save_and_token_update()

    @Slot()
    def _schedule_settings_save(self):
        if not self._is_loading_settings:
            self.settings_changed.emit()

    @Slot()
    def _schedule_settings_save_and_token_update(self):
        self._schedule_settings_save()
        self.update_token_estimation_ui()
        
    def _trigger_token_update(self):
        self.update_token_estimation_ui()

    def update_token_estimation_ui(self):
        if not self.prompt_engine or not self.context_builder or not self.llm_client or not self.dialogue_generation_service:
            self.token_actions_widget.set_token_estimation_text("Erreur: Moteurs/Service non initialisés")
            self._display_prompt_in_tab("Erreur: Les moteurs (prompt, context, llm) ou le service de génération ne sont pas tous initialisés.")
            return

        user_instructions = self.instructions_widget.get_user_instructions_text()
        self._update_prompt_engine_system_prompt() 
        system_prompt_override_from_ui = self.instructions_widget.get_system_prompt_text()
        
        system_prompt_for_service = None
        if self.prompt_engine.system_prompt_template != system_prompt_override_from_ui :
            system_prompt_for_service = system_prompt_override_from_ui
        elif system_prompt_override_from_ui != self.prompt_engine._get_default_system_prompt():
             system_prompt_for_service = system_prompt_override_from_ui

        context_selections_for_service = self.main_window_ref._get_current_context_selections() if hasattr(self.main_window_ref, '_get_current_context_selections') else {}
        
        # Ajouter le réglage de génération d'interaction aux sélections de contexte
        generate_interaction = self.generate_interaction_checkbox.isChecked()
        if "generation_settings" not in context_selections_for_service:
            context_selections_for_service["generation_settings"] = {}
        context_selections_for_service["generation_settings"]["generate_interaction"] = generate_interaction
        
        # Ajouter la structure de dialogue si on génère des interactions
        if generate_interaction:
            dialogue_structure = self.dialogue_structure_widget.get_structure_description()
            context_selections_for_service["generation_settings"]["dialogue_structure"] = dialogue_structure

        char_a_name = self.scene_selection_widget.character_a_combo.currentText()
        char_b_name = self.scene_selection_widget.character_b_combo.currentText()
        scene_region_name = self.scene_selection_widget.scene_region_combo.currentText()
        scene_sub_location_name = self.scene_selection_widget.scene_sub_location_combo.currentText()

        placeholders = ["(Aucun)", "(Aucune)", "(Tous / Non spécifié)", "(Aucun sous-lieu)", "(Sélectionner une région d'abord)"]

        protagonists = {}
        if char_a_name and char_a_name not in placeholders: protagonists["personnage_a"] = char_a_name
        if char_b_name and char_b_name not in placeholders: protagonists["personnage_b"] = char_b_name
        context_selections_for_service["_scene_protagonists"] = protagonists

        location = {}
        if scene_region_name and scene_region_name not in placeholders: location["lieu"] = scene_region_name
        if scene_sub_location_name and scene_sub_location_name not in placeholders: location["sous_lieu"] = scene_sub_location_name
        context_selections_for_service["_scene_location"] = location
        
        max_context_tokens_for_builder = int(self.generation_params_widget.max_context_tokens_spinbox.value() * 1000)
        structured_output_flag = self.generation_params_widget.structured_output_checkbox.isChecked()

        full_prompt_for_display = "Erreur lors de la préparation de la prévisualisation."
        estimated_total_tokens = 0
        context_summary_tokens = 0

        try:
            full_prompt_for_display, estimated_total_tokens, context_summary_text = self.dialogue_generation_service.prepare_generation_preview(
                user_instructions=user_instructions,
                system_prompt_override=system_prompt_for_service,
                context_selections=context_selections_for_service, 
                max_context_tokens=max_context_tokens_for_builder,
                structured_output=structured_output_flag
            )
            context_summary_tokens = self.prompt_engine._count_tokens(context_summary_text) if context_summary_text else 0
        except Exception as e:
            logger.error(f"Erreur lors de l'appel à prepare_generation_preview: {e}", exc_info=True)
            full_prompt_for_display = f"Erreur lors de la préparation de la prévisualisation:\n{type(e).__name__}: {e}"
            estimated_total_tokens = 0
            context_summary_tokens = 0

        context_tokens_k = context_summary_tokens / 1000
        prompt_tokens_k = estimated_total_tokens / 1000
        
        self.token_actions_widget.set_token_estimation_text(f"Tokens (contexte GDD/prompt total): {context_tokens_k:.1f}k / {prompt_tokens_k:.1f}k")
        logger.debug(f"Token estimation UI updated (via service): Context GDD {context_summary_tokens} ({context_tokens_k:.1f}k), Prompt total {estimated_total_tokens} ({prompt_tokens_k:.1f}k).")
        self._display_prompt_in_tab(full_prompt_for_display if full_prompt_for_display else "Aucun prompt n'a pu être généré.")

    def _launch_dialogue_generation(self):
        logger.info("Lancement de la génération de dialogue...")
        if not self.llm_client:
            QMessageBox.critical(self, "Erreur LLM", "Le client LLM n'est pas initialisé.")
            logger.error("Tentative de génération de dialogue sans client LLM initialisé.")
            return

        self.token_actions_widget.set_progress_bar_indeterminate(True)
        self.token_actions_widget.set_progress_bar_visibility(True)
        self.token_actions_widget.set_generate_button_enabled(False)
        QApplication.processEvents() 

        asyncio.create_task(self._on_generate_dialogue_button_clicked_local())

    async def _on_generate_dialogue_button_clicked_local(self):
        logger.info("Début de la génération de dialogue via GenerationPanelBase (appel au service).")
        generation_succeeded = False
        try:
            k_variants = int(self.generation_params_widget.k_variants_combo.currentText())
            max_context_tokens_for_builder = int(self.generation_params_widget.max_context_tokens_spinbox.value() * 1000)
            structured_text_output = self.generation_params_widget.structured_output_checkbox.isChecked()
            generate_interaction_mode = self.generate_interaction_checkbox.isChecked()
            user_instructions = self.instructions_widget.get_user_instructions_text()
            system_prompt_override = self.instructions_widget.get_system_prompt_text() if self.instructions_widget.is_system_prompt_customized() else None
            current_llm_model_identifier = self.generation_params_widget.llm_model_combo.currentData()

            context_selections_dict = self.main_window_ref._get_current_context_selections()
            char_a_name = self.scene_selection_widget.character_a_combo.currentText()
            char_b_name = self.scene_selection_widget.character_b_combo.currentText()
            scene_region_name = self.scene_selection_widget.scene_region_combo.currentText()
            scene_sub_location_name = self.scene_selection_widget.scene_sub_location_combo.currentText()

            placeholders = ["(Aucun)", "(Aucune)", "(Tous / Non spécifié)", "(Aucun sous-lieu)", "(Sélectionner une région d'abord)"]
            
            protagonists = {}
            if char_a_name and char_a_name not in placeholders: protagonists["personnage_a"] = char_a_name
            if char_b_name and char_b_name not in placeholders: protagonists["personnage_b"] = char_b_name
            if protagonists: context_selections_dict["_scene_protagonists"] = protagonists

            location = {}
            if scene_region_name and scene_region_name not in placeholders: location["lieu"] = scene_region_name
            if scene_sub_location_name and scene_sub_location_name not in placeholders: location["sous_lieu"] = scene_sub_location_name
            if location: context_selections_dict["_scene_location"] = location
            
            context_selections_dict["generate_interaction"] = generate_interaction_mode
            if generate_interaction_mode:
                dialogue_structure_description = self.dialogue_structure_widget.get_structure_description()
                if "generation_settings" not in context_selections_dict:
                    context_selections_dict["generation_settings"] = {}
                context_selections_dict["generation_settings"]["dialogue_structure"] = dialogue_structure_description

            if not self.llm_client:
                QMessageBox.critical(self, "Erreur LLM", "Le client LLM n'est pas disponible.")
                logger.error("LLM client non disponible pour la génération.")
                return

            variants = None
            full_prompt = None
            estimated_tokens = 0

            if generate_interaction_mode:
                logger.info("GenerationPanel: Appel de generate_interaction_variants du service.")
                variants, full_prompt, estimated_tokens = await self.dialogue_generation_service.generate_interaction_variants(
                    llm_client=self.llm_client,
                    k_variants=k_variants,
                    max_context_tokens_for_context_builder=max_context_tokens_for_builder,
                    user_instructions=user_instructions,
                    system_prompt_override=system_prompt_override,
                    context_selections=context_selections_dict,
                    current_llm_model_identifier=current_llm_model_identifier
                )
                self.generated_variants_tabs.display_interaction_variants(variants or [], full_prompt)
            else:
                logger.info("GenerationPanel: Appel de generate_dialogue_variants du service (texte).")
                variants, full_prompt, estimated_tokens = await self.dialogue_generation_service.generate_dialogue_variants(
                    llm_client=self.llm_client,
                    k_variants=k_variants,
                    max_context_tokens_for_context_builder=max_context_tokens_for_builder,
                    structured_output=structured_text_output,
                    user_instructions=user_instructions,
                    system_prompt_override=system_prompt_override,
                    context_selections=context_selections_dict,
                    current_llm_model_identifier=current_llm_model_identifier
                )
                self.generated_variants_tabs.display_variants(variants or [], full_prompt)
            
            self.token_actions_widget.set_token_estimation_text(f"Tokens prompt final: {(estimated_tokens or 0) / 1000:.1f}k")

            if full_prompt is not None and variants is not None:
                generation_succeeded = True
            elif full_prompt is None:
                 QMessageBox.warning(self, "Erreur de Prompt", "Impossible de construire le prompt. Vérifiez les logs.")
                 generation_succeeded = False
            else: # full_prompt ok, mais variants est None ou vide
                QMessageBox.warning(self, "Aucune Variante", "Le LLM n'a retourné aucune variante ou une erreur est survenue.")
                generation_succeeded = False
                    
        except Exception as e:
            logger.exception("Erreur majeure dans GenerationPanelBase._on_generate_dialogue_button_clicked_local")
            QMessageBox.critical(self, "Erreur Critique", f"Une erreur inattendue est survenue dans GenerationPanel: {e}")
            generation_succeeded = False # Assurer que c'est False en cas d'exception
        finally:
            # Assurer que current_task est défini avant de vérifier s'il est annulé
            current_task_obj = asyncio.current_task()
            if not current_task_obj or not current_task_obj.cancelled(): 
                self.token_actions_widget.set_progress_bar_visibility(False)
                self.token_actions_widget.set_generate_button_enabled(True)
                QApplication.processEvents() 
                logger.debug(f"Émission du signal generation_finished avec la valeur : {generation_succeeded}")
                self.generation_finished.emit(generation_succeeded)

    def _display_prompt_in_tab(self, prompt_text: str):
        logger.info(f"_display_prompt_in_tab: Entrée avec prompt_text de longueur {len(prompt_text)} chars.")
        self.generated_variants_tabs.update_or_add_tab("Prompt Estimé", prompt_text, set_current=True)
        logger.info("_display_prompt_in_tab: Sortie.")

    @Slot(str, str)
    def _on_validate_variant_requested_from_tabs(self, tab_name: str, content: str):
        logger.info(f"Validation de la variante '{tab_name}' demandée depuis le widget d'onglets.")
        QMessageBox.information(self, "Validation", f"La variante '{tab_name}' serait validée avec le contenu:\n{content[:200]}...")

    @Slot(str, Interaction)
    def _on_validate_interaction_requested_from_tabs(self, tab_name: str, interaction: Interaction):
        """Gère la validation d'une interaction générée depuis un onglet de variante.
        
        Cette méthode sauvegarde l'interaction, met à jour la liste des interactions,
        puis affiche l'interaction validée dans l'éditeur.
        
        Points importants:
        - Déconnecte temporairement le signal interaction_selected pour éviter des effets de bord
          lors du changement d'onglet qui pourrait vider l'éditeur
        - Sélectionne l'onglet "Interactions" automatiquement
        - Force l'affichage direct de l'interaction validée dans l'éditeur
        
        Args:
            tab_name: Nom de l'onglet source
            interaction: L'objet Interaction à valider et sauvegarder
        """
        print(f"[DEBUG] SLOT _on_validate_interaction_requested_from_tabs appelé pour tab_name={tab_name}, id={interaction.interaction_id}, self.generated_variants_tabs={self.generated_variants_tabs} @ {id(self.generated_variants_tabs)}")
        logger.info(f"[DEBUG] Début validation interaction depuis onglet: tab_name={tab_name}, id={interaction.interaction_id}, titre={interaction.title}")
        try:
            # Sauvegarder l'interaction dans le service
            self.interaction_service.save(interaction)
            logger.info(f"[DEBUG] Interaction sauvegardée avec ID: {interaction.interaction_id}, titre: {interaction.title}")
            
            # Afficher une boîte de dialogue de confirmation
            QMessageBox.information(self, "Interaction Validée", f"L'interaction '{interaction.title}' a été ajoutée à la séquence.")
            
            # Déconnecter temporairement le signal pour éviter le vidage de l'éditeur
            # Obtenir la signature de la méthode avec le bon type de paramètre
            try:
                self.interaction_sequence_widget.interaction_selected.disconnect(self._on_interaction_selected)
                print(f"[DEBUG] Signal interaction_selected déconnecté avec succès")
            except Exception as e:
                print(f"[DEBUG] Erreur lors de la déconnexion du signal: {e}")
            
            # Rafraîchir la liste des interactions
            self.interaction_sequence_widget.refresh_list(select_id=str(interaction.interaction_id))
            logger.info(f"[DEBUG] refresh_list appelé avec select_id={interaction.interaction_id}")
            
            # Debug: vérifier le type de l'ID
            print(f"[DEBUG] Type de interaction.interaction_id: {type(interaction.interaction_id)}, valeur: {interaction.interaction_id}")
            
            # Sélectionner l'onglet "Interactions" si possible
            if hasattr(self.main_window_ref, 'central_tabs'):
                tabs = self.main_window_ref.central_tabs
                for i in range(tabs.count()):
                    if tabs.tabText(i) == "Interactions":
                        tabs.setCurrentIndex(i)
                        logger.info(f"[DEBUG] Passage à l'onglet Interactions (index {i}) via main_window_ref.central_tabs")
                        break
            
            # Forcer directement l'éditeur à afficher l'interaction
            print(f"[DEBUG] Appel direct de interaction_editor_widget.set_interaction()")
            self.interaction_editor_widget.set_interaction(interaction)
            
            # Reconnecter le signal après avoir effectué les changements
            try:
                self.interaction_sequence_widget.interaction_selected.connect(self._on_interaction_selected)
                print(f"[DEBUG] Signal interaction_selected reconnecté avec succès")
            except Exception as e:
                print(f"[DEBUG] Erreur lors de la reconnexion du signal: {e}")
            
        except Exception as e:
            logger.exception(f"Erreur lors de la validation de l'interaction: {str(e)}")
            QMessageBox.critical(self, "Erreur", f"Impossible de valider l'interaction: {str(e)}")

    @Slot(list)
    def _on_save_all_variants_requested_from_tabs(self, variants_data: list):
        logger.info(f"Sauvegarde de {len(variants_data)} variantes demandée depuis le widget d'onglets.")
        if not variants_data:
            QMessageBox.information(self, "Sauvegarde", "Aucune variante à sauvegarder.")
            return
        details = "\n".join([f"- {v['title']} ({len(v['content'])} chars)" for v in variants_data])
        QMessageBox.information(self, "Sauvegarder Tout", f"{len(variants_data)} variantes seraient sauvegardées :\n{details}")

    @Slot(str)
    def _on_regenerate_variant_requested_from_tabs(self, variant_id: str):
        logger.info(f"Régénération de la variante '{variant_id}' demandée.")
        QMessageBox.information(self, "Régénération", f"La variante '{variant_id}' serait régénérée.\nPour l'instant, relancez une génération complète.")

    def get_settings(self) -> dict:
        settings = self.scene_selection_widget.get_selected()
        settings.update(self.generation_params_widget.get_settings())
        settings.update(self.instructions_widget.get_settings())
        # Ajouter le réglage de génération d'interaction
        settings["generate_interaction"] = self.generate_interaction_checkbox.isChecked()
        logger.debug(f"Récupération des paramètres du GenerationPanel (combinés): {settings}")
        return settings

    def load_settings(self, settings: dict):
        logger.debug(f"Chargement des paramètres dans GenerationPanel (combinés): {settings}")
        self._is_loading_settings = True

        self.scene_selection_widget.set_selected(
            settings.get("character_a", ""),
            settings.get("character_b", ""),
            settings.get("scene_region", ""),
            settings.get("scene_sub_location", "")
        )
        QApplication.processEvents() 

        self.generation_params_widget.load_settings(settings)
        
        # Charger le réglage de génération d'interaction
        generate_interaction = settings.get("generate_interaction", False)
        self.generate_interaction_checkbox.setChecked(generate_interaction)
        
        default_system_prompt_for_widget = self.prompt_engine._get_default_system_prompt() if self.prompt_engine else ""
        self.instructions_widget.load_settings(
            settings, 
            default_user_instructions=settings.get("user_instructions", ""), 
            default_system_prompt=settings.get("system_prompt", default_system_prompt_for_widget) 
        )

        self._update_prompt_engine_system_prompt()
        
        if "max_context_tokens" in settings: 
             self.generation_params_widget.max_context_tokens_spinbox.setValue(settings.get("max_context_tokens"))
        
        self._is_loading_settings = False
        self.update_token_estimation_signal.emit()
        self._update_structured_output_checkbox_state() 
        logger.info("Paramètres du GenerationPanel chargés (combinés).")

    @Slot(float)
    def _on_max_context_tokens_changed_from_widget(self, new_k_value: float):
        tokens_value = int(new_k_value * 1000)
        if hasattr(self.main_window_ref, 'app_settings'):
            self.main_window_ref.app_settings["max_context_tokens"] = tokens_value
            logger.info(f"Limite de tokens pour le contexte (via widget) : {tokens_value} ({new_k_value}k)")
            self._schedule_settings_save_and_token_update()

    @Slot()
    def _on_select_linked_elements_clicked(self) -> None:
        char_a_raw = self.scene_selection_widget.character_a_combo.currentText()
        char_b_raw = self.scene_selection_widget.character_b_combo.currentText()
        scene_region_raw = self.scene_selection_widget.scene_region_combo.currentText()
        scene_sub_location_raw = self.scene_selection_widget.scene_sub_location_combo.currentText()

        placeholders = ["(Aucun)", "(Aucune)", "(Tous / Non spécifié)", "(Aucun sous-lieu)", "(Sélectionner une région d'abord)"]

        char_a = None if char_a_raw in placeholders or not char_a_raw.strip() else char_a_raw
        char_b = None if char_b_raw in placeholders or not char_b_raw.strip() else char_b_raw
        scene_region = None if scene_region_raw in placeholders or not scene_region_raw.strip() else scene_region_raw
        scene_sub_location = None if scene_sub_location_raw in placeholders or not scene_sub_location_raw.strip() else scene_sub_location_raw

        elements_to_select_set = self.linked_selector.get_elements_to_select(
            char_a, char_b, scene_region, scene_sub_location
        )
        elements_to_select_list = list(elements_to_select_set)

        if hasattr(self.main_window_ref, 'left_panel'):
            if elements_to_select_list:
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
        char_a_raw = self.scene_selection_widget.character_a_combo.currentText()
        char_b_raw = self.scene_selection_widget.character_b_combo.currentText()
        scene_region_raw = self.scene_selection_widget.scene_region_combo.currentText()
        scene_sub_location_raw = self.scene_selection_widget.scene_sub_location_combo.currentText()

        placeholders = ["(Aucun)", "(Aucune)", "(Tous / Non spécifié)", "(Aucun sous-lieu)", "(Sélectionner une région d'abord)"]

        char_a = None if char_a_raw in placeholders or not char_a_raw.strip() else char_a_raw
        char_b = None if char_b_raw in placeholders or not char_b_raw.strip() else char_b_raw
        scene_region = None if scene_region_raw in placeholders or not scene_region_raw.strip() else scene_region_raw
        scene_sub_location = None if scene_sub_location_raw in placeholders or not scene_sub_location_raw.strip() else scene_sub_location_raw

        currently_checked_set = set()
        if hasattr(self.main_window_ref, 'left_panel'):
            currently_checked_list = self.main_window_ref.left_panel.get_all_selected_item_names()
            currently_checked_set = set(currently_checked_list)
        else:
            logger.warning("Référence à left_panel non trouvée lors de la récupération des items cochés.")

        items_to_keep_checked = self.linked_selector.compute_items_to_keep_checked(
            currently_checked_set,
            char_a, 
            char_b, 
            scene_region, 
            scene_sub_location
        )

        if hasattr(self.main_window_ref, 'left_panel'):
            self.main_window_ref.left_panel.set_checked_items_by_name(list(items_to_keep_checked))
            logger.info(f"Conservation des éléments liés : {items_to_keep_checked}, autres décochés.")
            if items_to_keep_checked:
                self.main_window_ref.statusBar().showMessage(f"Seuls les {len(items_to_keep_checked)} éléments liés sont conservés.", 3000)
            else:
                self.main_window_ref.statusBar().showMessage("Aucun élément lié à conserver. Tous les éléments secondaires ont été décochés.", 3000)
        else:
            logger.warning("Référence à left_panel non trouvée pour mettre à jour les coches.")

    @Slot()
    def _on_uncheck_all_clicked(self):
        if hasattr(self.main_window_ref, 'left_panel') and hasattr(self.main_window_ref.left_panel, 'uncheck_all_items'):
            self.main_window_ref.left_panel.uncheck_all_items()
            logger.info("Tous les éléments ont été décochés dans LeftSelectionPanel.")
            self.main_window_ref.statusBar().showMessage("Tous les éléments ont été décochés.", 3000)
        else:
            logger.warning("Impossible de tout décocher: left_panel ou méthode uncheck_all_items non trouvée.")
            self.main_window_ref.statusBar().showMessage("Erreur: Impossible de tout décocher.", 3000)

    @Slot(object)
    def _on_interaction_selected(self, interaction_id):
        """Gère la sélection d'une interaction dans la liste.
        
        Cette méthode est appelée lorsque l'utilisateur sélectionne une interaction
        dans la liste des interactions. Elle récupère l'interaction depuis le service
        et l'affiche dans l'éditeur.
        
        Compatibilité ID:
        - Supporte les identifiants sous forme d'UUID ou de chaîne de caractères
        - Convertit les identifiants en chaîne pour la récupération dans le service
        
        Args:
            interaction_id: L'identifiant de l'interaction sélectionnée (UUID ou str)
                            ou None si aucune sélection
        """
        print(f"[DEBUG] _on_interaction_selected appelé avec interaction_id={interaction_id}, type={type(interaction_id)}")
        if interaction_id is not None:
            logger.info(f"Interaction sélectionnée : {interaction_id}")
            interaction = self.interaction_service.get_by_id(str(interaction_id))
            print(f"[DEBUG] Interaction récupérée depuis le service: {interaction}")
            if interaction:
                print(f"[DEBUG] Appel de interaction_editor_widget.set_interaction() avec interaction trouvée")
                self.interaction_editor_widget.set_interaction(interaction)
                self.interaction_editor_widget.show()
                title_display = interaction.interaction_id 
                if hasattr(interaction, 'title') and interaction.title:
                    title_display = interaction.title
                self.main_window_ref.statusBar().showMessage(f"Interaction '{title_display}' sélectionnée.", 3000)
            else:
                print(f"[DEBUG] Interaction {interaction_id} non trouvée par le service")
                self.interaction_editor_widget.set_interaction(None)
                logger.warning(f"Interaction {interaction_id} non trouvée par le service.")
                self.main_window_ref.statusBar().showMessage(f"Erreur: Interaction {interaction_id} non trouvée.", 3000)
        else:
            print(f"[DEBUG] interaction_id est None, effacement de l'éditeur")
            self.interaction_editor_widget.set_interaction(None)
            logger.info("Aucune interaction sélectionnée.")
            self.main_window_ref.statusBar().showMessage("Sélection d'interaction effacée.", 3000)

    @Slot()
    def _on_sequence_changed(self):
        logger.info("La séquence d'interactions a changé (ajout, suppression, réorganisation).")
        self.main_window_ref.statusBar().showMessage("Séquence d'interactions modifiée.", 3000)

    @Slot(bool)
    def _on_generate_interaction_state_changed(self, state):
        """Gère le changement d'état de la checkbox de génération d'interactions."""
        is_checked = state == Qt.CheckState.Checked
        logger.info(f"Mode de génération d'Interaction structurée: {'activé' if is_checked else 'désactivé'}")
        self._schedule_settings_save_and_token_update()
        
        # Mise à jour visuelle en fonction du mode
        if is_checked:
            self.generation_params_widget.structured_output_checkbox.setChecked(True)
            self.generation_params_widget.structured_output_checkbox.setEnabled(False)
            self.generation_params_widget.structured_output_checkbox.setToolTip("La sortie structurée est requise pour la génération d'Interactions")
        else:
            self.generation_params_widget.structured_output_checkbox.setEnabled(True)
            self.generation_params_widget.structured_output_checkbox.setToolTip("Demande au LLM de générer du JSON au lieu de texte brut")

    @Slot(list)
    def _on_dialogue_structure_changed(self, structure):
        """Appelé quand la structure de dialogue change."""
        logger.debug(f"Structure de dialogue modifiée: {structure}")
        # La structure a déjà été modifiée dans le widget, pas besoin de la réappliquer