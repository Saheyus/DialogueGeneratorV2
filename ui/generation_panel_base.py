from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QGridLayout, 
                               QLabel, QTextEdit, QPushButton, 
                               QTabWidget, QApplication, QSizePolicy, QScrollArea, QSplitter, QMessageBox, QSpacerItem, QStyle, QHBoxLayout)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QPalette, QColor, QFont, QIcon, QAction
import logging # Added for logging
import asyncio # Added for asynchronous tasks
from typing import Optional, Callable, Any # Added Any
import json # Ajout pour charger la config LLM potentiellement ici aussi si besoin
from pathlib import Path
import uuid

# Import local de la fonction utilitaire
from .utils import get_icon_path
# Ajout de l'import du nouveau widget extrait
from .generation_panel.scene_selection_widget import SceneSelectionWidget
from .generation_panel.context_actions_widget import ContextActionsWidget
from .generation_panel.generation_params_widget import GenerationParamsWidget
from .generation_panel.instructions_widget import InstructionsWidget # Ajout de l'import
from .generation_panel.token_estimation_actions_widget import TokenEstimationActionsWidget # Ajout de l'import
from .generation_panel.generated_variants_tabs_widget import GeneratedVariantsTabsWidget # Ajout de l'import

# New service import
try:
    from ..services.linked_selector import LinkedSelectorService
    from ..services.yarn_renderer import YarnRenderer # Ajout YarnRenderer
    from ..llm_client import OpenAIClient, DummyLLMClient # Ajout OpenAIClient et DummyLLMClient
    from ..services.dialogue_generation_service import DialogueGenerationService # Ajout du nouveau service
except ImportError:
    # Support exécution directe
    import sys, os, pathlib
    current_dir = pathlib.Path(__file__).resolve().parent.parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    from DialogueGenerator.services.linked_selector import LinkedSelectorService
    from DialogueGenerator.services.yarn_renderer import YarnRenderer # Ajout YarnRenderer
    from DialogueGenerator.llm_client import OpenAIClient, DummyLLMClient # Ajout OpenAIClient et DummyLLMClient
    from DialogueGenerator.services.dialogue_generation_service import DialogueGenerationService # Ajout du nouveau service

logger = logging.getLogger(__name__) # Added logger

# Chemin vers le fichier de configuration LLM, au cas où GenerationPanel aurait besoin de le lire directement
# Bien que la liste des modèles soit passée par MainWindow, cela pourrait servir pour d'autres settings.
DIALOGUE_GENERATOR_DIR = Path(__file__).resolve().parent.parent
LLM_CONFIG_FILE_PATH = DIALOGUE_GENERATOR_DIR / "llm_config.json"

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

    def __init__(self, context_builder, prompt_engine, llm_client, available_llm_models, current_llm_model_identifier, main_window_ref, parent=None):
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
            parent: The parent widget.
        """
        super().__init__(parent)
        
        self.context_builder = context_builder
        self.prompt_engine = prompt_engine
        self.llm_client = llm_client
        self.main_window_ref = main_window_ref
        self.linked_selector = LinkedSelectorService(self.context_builder)
        self.yarn_renderer = YarnRenderer()
        self.dialogue_generation_service = DialogueGenerationService(self.context_builder, self.prompt_engine) # Instanciation
        
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

        # --- Section Sélection Personnages et Scène ---
        self.scene_selection_widget = SceneSelectionWidget(self.context_builder)
        left_column_layout.addWidget(self.scene_selection_widget)
        self.scene_selection_widget.character_a_changed.connect(self._schedule_settings_save_and_token_update)
        self.scene_selection_widget.character_b_changed.connect(self._schedule_settings_save_and_token_update)
        self.scene_selection_widget.scene_region_changed.connect(self._schedule_settings_save_and_token_update)
        self.scene_selection_widget.scene_sub_location_changed.connect(self._schedule_settings_save_and_token_update)
        self.scene_selection_widget.swap_characters_clicked.connect(self._swap_characters)

        # --- Section Actions sur le Contexte ---
        self.context_actions_widget = ContextActionsWidget()
        left_column_layout.addWidget(self.context_actions_widget)
        self.context_actions_widget.select_linked_clicked.connect(self._on_select_linked_elements_clicked)
        self.context_actions_widget.unlink_unrelated_clicked.connect(self._on_unlink_unrelated_clicked)
        self.context_actions_widget.uncheck_all_clicked.connect(self._on_uncheck_all_clicked)

        # --- Section Paramètres de Génération ---
        self.generation_params_widget = GenerationParamsWidget(
            self.available_llm_models,
            self.current_llm_model_identifier
        )
        left_column_layout.addWidget(self.generation_params_widget)
        self.generation_params_widget.llm_model_selection_changed.connect(self._on_llm_model_selected_from_widget)
        self.generation_params_widget.k_variants_changed.connect(self._schedule_settings_save)
        self.generation_params_widget.max_context_tokens_changed.connect(self._on_max_context_tokens_changed_from_widget)
        self.generation_params_widget.structured_output_changed.connect(self._schedule_settings_save)
        self.generation_params_widget.settings_changed.connect(self._schedule_settings_save_and_token_update)

        # --- Section Instructions Utilisateur et Système (remplacée par le widget) ---
        self.instructions_widget = InstructionsWidget()
        left_column_layout.addWidget(self.instructions_widget)
        self.instructions_widget.user_instructions_changed.connect(self._schedule_settings_save_and_token_update)
        self.instructions_widget.system_prompt_changed.connect(self._on_system_prompt_changed_from_widget)
        self.instructions_widget.restore_default_system_prompt_clicked.connect(self._restore_default_system_prompt)
        self.instructions_widget.settings_changed.connect(self._schedule_settings_save_and_token_update)

        # --- Section Estimation Tokens et Bouton Générer (remplacée par le widget) ---
        self.token_actions_widget = TokenEstimationActionsWidget()
        left_column_layout.addWidget(self.token_actions_widget)
        self.token_actions_widget.refresh_token_clicked.connect(self._trigger_token_update)
        self.token_actions_widget.generate_dialogue_clicked.connect(self._launch_dialogue_generation)

        left_column_layout.addStretch(1)

        # --- Colonne de Droite: Affichage des Variantes (remplacée par le widget) ---
        right_column_widget = QWidget()
        right_column_layout = QVBoxLayout(right_column_widget)
        self.generated_variants_tabs = GeneratedVariantsTabsWidget() # Utilisation du widget extrait
        right_column_layout.addWidget(self.generated_variants_tabs)
        main_splitter.addWidget(right_column_widget)

        # Connecter les signaux du nouveau widget si nécessaire
        self.generated_variants_tabs.validate_variant_requested.connect(self._on_validate_variant_requested_from_tabs)
        self.generated_variants_tabs.save_all_variants_requested.connect(self._on_save_all_variants_requested_from_tabs)
        self.generated_variants_tabs.regenerate_variant_requested.connect(self._on_regenerate_variant_requested_from_tabs)

        main_splitter.setStretchFactor(0, 1) 
        main_splitter.setStretchFactor(1, 2) 
        initial_widths = [self.width() // 3 if self.width() > 0 else 300, 2 * self.width() // 3 if self.width() > 0 else 600] # Safe defaults
        if all(w > 50 for w in initial_widths): # Ensure some minimal width
            main_splitter.setSizes(initial_widths)
        else:
            logger.warning("Largeurs initiales calculées pour le splitter principal non valides ou trop petites, utilisation des tailles par défaut du QSplitter.")
        
        self.update_token_estimation_signal.connect(self.update_token_estimation_ui) 

    def finalize_ui_setup(self):
        logger.debug("Finalizing GenerationPanel UI setup...")
        character_names = sorted(self.context_builder.get_characters_names())
        region_names = sorted(self.context_builder.get_regions())
        self.scene_selection_widget.populate_characters(character_names)
        self.scene_selection_widget.populate_regions(region_names)
        self.generation_params_widget.populate_llm_model_combo() # S'assurer qu'il est peuplé
        self._trigger_token_update() 
        logger.debug("GenerationPanel UI setup finalized.")

    @Slot(str)
    def _on_llm_model_selected_from_widget(self, selected_identifier: str):
        if selected_identifier and selected_identifier != self.current_llm_model_identifier and selected_identifier != "dummy_error":
            logger.info(f"Sélection du modèle LLM relayée au GenerationPanel : {selected_identifier}")
            self.current_llm_model_identifier = selected_identifier
            self.llm_model_selection_changed.emit(selected_identifier) # Émettre vers MainWindow
            self._schedule_settings_save_and_token_update()
            self._update_structured_output_checkbox_state() # Assurer que l'état du checkbox est mis à jour si nécessaire

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

    def update_token_estimation_ui(self):
        if not self.prompt_engine or not self.context_builder or not self.llm_client or not self.dialogue_generation_service: # Ajout vérification service
            self.token_actions_widget.set_token_estimation_text("Erreur: Moteurs/Service non initialisés")
            self._display_prompt_in_tab("Erreur: Les moteurs (prompt, context, llm) ou le service de génération ne sont pas tous initialisés.")
            return

        # Préparer les arguments pour le service
        user_instructions = self.instructions_widget.get_user_instructions_text()
        
        # S'assurer que le system_prompt de prompt_engine est à jour avant de potentiellement le surcharger
        self._update_prompt_engine_system_prompt() 
        system_prompt_override_from_ui = self.instructions_widget.get_system_prompt_text()
        
        # Déterminer si le prompt de l'UI est un "override" réel
        # On ne passe system_prompt_override au service QUE si le texte de l'UI est différent du défaut interne du prompt_engine
        # Ceci évite de forcer un "override" si l'utilisateur a juste restauré le défaut.
        # Le service, lui, réappliquera le system_prompt par défaut de l'engine s'il reçoit None.
        system_prompt_for_service = None
        if self.prompt_engine.system_prompt_template != system_prompt_override_from_ui : # Compare avec le template actuel de l'engine
            system_prompt_for_service = system_prompt_override_from_ui
        elif system_prompt_override_from_ui != self.prompt_engine._get_default_system_prompt(): # Cas où le template a été changé mais l'UI correspond toujours
             system_prompt_for_service = system_prompt_override_from_ui


        # Récupérer les sélections de contexte GDD (via MainWindow) et y ajouter les infos de scène
        context_selections_for_service = self.main_window_ref._get_current_context_selections() if hasattr(self.main_window_ref, '_get_current_context_selections') else {}

        char_a_name = self.scene_selection_widget.character_a_combo.currentText()
        char_b_name = self.scene_selection_widget.character_b_combo.currentText()
        scene_region_name = self.scene_selection_widget.scene_region_combo.currentText()
        scene_sub_location_name = self.scene_selection_widget.scene_sub_location_combo.currentText()

        placeholders = ["(Aucun)", "(Aucune)", "(Tous / Non spécifié)", "(Aucun sous-lieu)", "(Sélectionner une région d\'abord)"]

        protagonists = {}
        if char_a_name and char_a_name not in placeholders: protagonists["personnage_a"] = char_a_name
        if char_b_name and char_b_name not in placeholders: protagonists["personnage_b"] = char_b_name
        # On met _scene_protagonists dans le dictionnaire même s'il est vide, 
        # car le service s'attend à pouvoir le .pop() (avec un défaut {}).
        context_selections_for_service["_scene_protagonists"] = protagonists

        location = {}
        if scene_region_name and scene_region_name not in placeholders: location["lieu"] = scene_region_name
        if scene_sub_location_name and scene_sub_location_name not in placeholders: location["sous_lieu"] = scene_sub_location_name
        context_selections_for_service["_scene_location"] = location
        
        max_context_tokens_for_builder = int(self.generation_params_widget.max_context_tokens_spinbox.value() * 1000)
        structured_output_flag = self.generation_params_widget.structured_output_checkbox.isChecked()

        full_prompt_for_display = "Erreur lors de la préparation de la prévisualisation."
        estimated_total_tokens = 0
        # context_summary_tokens = 0 # Si on veut le réintroduire

        try:
            full_prompt_for_display, estimated_total_tokens, context_summary_text = self.dialogue_generation_service.prepare_generation_preview(
                user_instructions=user_instructions,
                system_prompt_override=system_prompt_for_service, # Peut être None
                context_selections=context_selections_for_service, 
                max_context_tokens=max_context_tokens_for_builder,
                structured_output=structured_output_flag
            )
            
            # Pour afficher la distinction, nous avons besoin des tokens du contexte seul.
            # Le service ne le retourne pas encore séparément.
            # Pour l'instant, nous recalculons les tokens du résumé du contexte ici.
            # Idéalement, le service le fournirait.
            context_summary_tokens = self.prompt_engine._count_tokens(context_summary_text) if context_summary_text else 0

        except Exception as e:
            logger.error(f"Erreur lors de l'appel à prepare_generation_preview: {e}", exc_info=True)
            full_prompt_for_display = f"Erreur lors de la préparation de la prévisualisation:\\n{type(e).__name__}: {e}"
            estimated_total_tokens = 0
            context_summary_tokens = 0


        # Affichage des tokens
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
            # 1. Collecter les paramètres UI
            k_variants = int(self.generation_params_widget.k_variants_combo.currentText())
            max_context_tokens_for_builder = int(self.generation_params_widget.max_context_tokens_spinbox.value() * 1000)
            structured_output = self.generation_params_widget.structured_output_checkbox.isChecked()
            user_instructions = self.instructions_widget.get_user_instructions_text()
            system_prompt_override = self.instructions_widget.get_system_prompt_text()
            current_llm_model_identifier = self.generation_params_widget.llm_model_combo.currentData()

            # Obtenir les sélections de contexte GDD général (via MainWindow)
            context_selections_dict = self.main_window_ref._get_current_context_selections()
            
            # Extraire les infos de scène directement depuis SceneSelectionWidget et les ajouter au dict
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

            if not self.llm_client:
                QMessageBox.critical(self, "Erreur LLM", "Le client LLM n'est pas disponible.")
                logger.error("LLM client non disponible pour la génération.")
                return

            # 2. Appeler le service de génération
            variants, full_prompt, estimated_tokens = await self.dialogue_generation_service.generate_dialogue_variants(
                llm_client=self.llm_client,
                k_variants=k_variants,
                max_context_tokens_for_context_builder=max_context_tokens_for_builder,
                structured_output=structured_output,
                user_instructions=user_instructions,
                system_prompt_override=system_prompt_override,
                context_selections=context_selections_dict, # Contient maintenant _scene_protagonists et _scene_location
                current_llm_model_identifier=current_llm_model_identifier
            )

            # 3. Mettre à jour l'UI avec les résultats
            self.token_actions_widget.set_token_estimation_text(f"Tokens prompt final: {(estimated_tokens or 0) / 1000:.1f}k")
            self.generated_variants_tabs.display_variants(variants or [], full_prompt)
            if full_prompt is not None:
                generation_succeeded = True if variants is not None else False
            else:
                QMessageBox.warning(self, "Erreur de Prompt", "Impossible de construire le prompt. Vérifiez les logs.")
                generation_succeeded = False

        except Exception as e:
            logger.exception("Erreur majeure dans GenerationPanelBase._on_generate_dialogue_button_clicked_local")
            QMessageBox.critical(self, "Erreur Critique", f"Une erreur inattendue est survenue dans GenerationPanel: {e}")
        finally:
            current_task = asyncio.current_task()
            if not current_task or not current_task.cancelled(): 
                self.token_actions_widget.set_progress_bar_visibility(False)
                self.token_actions_widget.set_generate_button_enabled(True)
                QApplication.processEvents() 
                logger.debug(f"Émission du signal generation_finished avec la valeur : {generation_succeeded}")
                self.generation_finished.emit(generation_succeeded)

    def _display_prompt_in_tab(self, prompt_text: str):
        logger.info(f"_display_prompt_in_tab: Entrée avec prompt_text de longueur {len(prompt_text)} chars.")
        self.generated_variants_tabs.update_or_add_tab("Prompt Estimé", prompt_text, set_current=True)
        logger.info("_display_prompt_in_tab: Sortie.")

    # --- Slots pour les signaux de GeneratedVariantsTabsWidget ---
    @Slot(str, str)
    def _on_validate_variant_requested_from_tabs(self, tab_name: str, content: str):
        logger.info(f"Validation de la variante '{tab_name}' demandée depuis le widget d'onglets.")
        # Ici, vous implémenteriez la logique de validation et de sauvegarde du fichier Yarn.
        # Pour l'instant, on affiche un message.
        QMessageBox.information(self, "Validation", f"La variante '{tab_name}' serait validée avec le contenu:\n{content[:200]}...")
        # Exemple: self.yarn_writer_service.write_and_commit(content, ...)

    @Slot(list)
    def _on_save_all_variants_requested_from_tabs(self, variants_data: list):
        logger.info(f"Sauvegarde de {len(variants_data)} variantes demandée depuis le widget d'onglets.")
        # Implémenter la logique pour sauvegarder toutes les variantes (par ex. dans des fichiers texte séparés)
        # ou les proposer pour une validation individuelle.
        if not variants_data:
            QMessageBox.information(self, "Sauvegarde", "Aucune variante à sauvegarder.")
            return

        # Exemple de logique (pour l'instant, affichage)
        details = "\n".join([f"- {v['title']} ({len(v['content'])} chars)" for v in variants_data])
        QMessageBox.information(self, "Sauvegarder Tout", f"{len(variants_data)} variantes seraient sauvegardées :\n{details}")

    @Slot(str)
    def _on_regenerate_variant_requested_from_tabs(self, variant_id: str):
        logger.info(f"Régénération de la variante '{variant_id}' demandée.")
        # Logique pour la régénération d'une variante spécifique.
        # Cela pourrait impliquer de réutiliser le prompt original avec une seed différente,
        # ou de modifier légèrement le prompt.
        # Pour l'instant, nous allons juste relancer une génération complète pour la démo.
        QMessageBox.information(self, "Régénération", f"La variante '{variant_id}' serait régénérée.\nPour l'instant, relancez une génération complète.")
        # Potentiellement: self._launch_dialogue_generation(variant_to_regenerate=variant_id)

    def get_settings(self) -> dict:
        settings = self.scene_selection_widget.get_selected()
        settings.update(self.generation_params_widget.get_settings())
        settings.update(self.instructions_widget.get_settings())
        # Pas de settings UI spécifiques pour GeneratedVariantsTabsWidget pour l'instant, car son état est éphémère (contenu généré)
        # ou géré par la session globale (onglet actif, etc. - si cela devient pertinent)
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
        
        default_system_prompt_for_widget = self.prompt_engine._get_default_system_prompt() if self.prompt_engine else ""
        self.instructions_widget.load_settings(
            settings, 
            default_user_instructions=settings.get("user_instructions", ""), 
            default_system_prompt=settings.get("system_prompt", default_system_prompt_for_widget) 
        )

        self._update_prompt_engine_system_prompt()
        
        if "max_context_tokens" in settings: 
             self.generation_params_widget.max_context_tokens_spinbox.setValue(settings.get("max_context_tokens"))

        # Ne pas charger les onglets de variantes ici, car ils sont générés dynamiquement.
        # Si on voulait restaurer un prompt estimé précédent, il faudrait le faire ici.
        # Pour l'instant, l'onglet "Prompt Estimé" est mis à jour par update_token_estimation_ui.
        
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

    # --- Méthodes pour les actions sur le contexte (restaurées) ---
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
        """
        Slot pour le bouton "Décocher Non-Connexes".
        Récupère les personnages A/B et la scène, puis demande au LeftSelectionPanel
        de ne garder cochés QUE les éléments du GDD qui leur sont liés.
        """
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
            self.main_window_ref.left_panel.set_checked_items_by_name(list(items_to_keep_checked)) # set_checked_items_by_name attend une liste
            logger.info(f"Conservation des éléments liés : {items_to_keep_checked}, autres décochés.")
            if items_to_keep_checked:
                self.main_window_ref.statusBar().showMessage(f"Seuls les {len(items_to_keep_checked)} éléments liés sont conservés.", 3000)
            else:
                self.main_window_ref.statusBar().showMessage("Aucun élément lié à conserver. Tous les éléments secondaires ont été décochés.", 3000)
        else:
            logger.warning("Référence à left_panel non trouvée pour mettre à jour les coches.")

    @Slot()
    def _on_uncheck_all_clicked(self):
        """Slot pour le bouton "Tout Décocher"."""
        if hasattr(self.main_window_ref, 'left_panel') and hasattr(self.main_window_ref.left_panel, 'uncheck_all_items'):
            self.main_window_ref.left_panel.uncheck_all_items()
            logger.info("Tous les éléments ont été décochés dans LeftSelectionPanel.")
            self.main_window_ref.statusBar().showMessage("Tous les éléments ont été décochés.", 3000)
        else:
            logger.warning("Impossible de tout décocher: left_panel ou méthode uncheck_all_items non trouvée.")
            self.main_window_ref.statusBar().showMessage("Erreur: Impossible de tout décocher.", 3000)
    # --- Fin des méthodes restaurées ---