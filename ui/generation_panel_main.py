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

# Import local de la fonction utilitaire
from .utils import get_icon_path
# Ajout de l'import du nouveau widget extrait
from .generation_panel.scene_selection_widget import SceneSelectionWidget
from .generation_panel.context_actions_widget import ContextActionsWidget
from .generation_panel.generation_params_widget import GenerationParamsWidget
from .generation_panel.instructions_tabs_widget import InstructionsTabsWidget
from .generation_panel.token_and_generate_widget import TokenAndGenerateWidget
from .generation_panel.variants_display_widget import VariantsDisplayWidget

# New service import
try:
    from ..services.linked_selector import LinkedSelectorService
    from ..services.yarn_renderer import YarnRenderer # Ajout YarnRenderer
    from ..llm_client import OpenAIClient, DummyLLMClient # Ajout OpenAIClient et DummyLLMClient
except ImportError:
    # Support exécution directe
    import sys, os, pathlib
    current_dir = pathlib.Path(__file__).resolve().parent.parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    from DialogueGenerator.services.linked_selector import LinkedSelectorService
    from DialogueGenerator.services.yarn_renderer import YarnRenderer # Ajout YarnRenderer
    from DialogueGenerator.llm_client import OpenAIClient, DummyLLMClient # Ajout OpenAIClient et DummyLLMClient

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
        # Remplacement par le widget extrait
        self.scene_selection_widget = SceneSelectionWidget()
        left_column_layout.addWidget(self.scene_selection_widget)
        # Connexion des signaux du widget extrait aux méthodes existantes
        self.scene_selection_widget.character_a_changed.connect(self._schedule_settings_save_and_token_update)
        self.scene_selection_widget.character_b_changed.connect(self._schedule_settings_save_and_token_update)
        self.scene_selection_widget.scene_region_changed.connect(self._on_scene_region_changed)
        self.scene_selection_widget.scene_sub_location_changed.connect(self._schedule_settings_save_and_token_update)
        self.scene_selection_widget.swap_characters_clicked.connect(self._swap_characters)

        # --- Section Actions sur le Contexte ---
        self.context_actions_widget = ContextActionsWidget()
        left_column_layout.addWidget(self.context_actions_widget)
        self.context_actions_widget.select_linked_clicked.connect(self._on_select_linked_elements_clicked)
        self.context_actions_widget.unlink_unrelated_clicked.connect(self._on_unlink_unrelated_clicked)
        self.context_actions_widget.uncheck_all_clicked.connect(self._on_uncheck_all_clicked)

        # --- Section Paramètres de Génération ---
        self.generation_params_widget = GenerationParamsWidget()
        left_column_layout.addWidget(self.generation_params_widget)
        self.generation_params_widget.llm_model_changed.connect(self._on_llm_model_combo_changed)
        self.generation_params_widget.k_variants_changed.connect(self._schedule_settings_save)
        self.generation_params_widget.max_context_tokens_changed.connect(self._on_max_context_tokens_changed)
        self.generation_params_widget.structured_output_changed.connect(self._schedule_settings_save)

        # --- Section Instructions Utilisateur (modifiée en QTabWidget) ---
        self.instructions_tabs_widget = InstructionsTabsWidget()
        left_column_layout.addWidget(self.instructions_tabs_widget)
        self.instructions_tabs_widget.user_instructions_changed.connect(self._schedule_settings_save_and_token_update)
        self.instructions_tabs_widget.system_prompt_changed.connect(self._on_system_prompt_changed)
        self.instructions_tabs_widget.restore_default_system_prompt_clicked.connect(self._restore_default_system_prompt)

        # --- Section Estimation Tokens et Bouton Générer ---
        self.token_and_generate_widget = TokenAndGenerateWidget()
        left_column_layout.addWidget(self.token_and_generate_widget)
        self.token_and_generate_widget.refresh_token_clicked.connect(self._trigger_token_update)
        self.token_and_generate_widget.generate_dialogue_clicked.connect(self._launch_dialogue_generation)

        left_column_layout.addStretch() 

        # --- Colonne de Droite: Affichage des Variantes ---
        right_column_widget = QWidget()
        right_column_layout = QVBoxLayout(right_column_widget)
        right_column_layout.setContentsMargins(0,0,0,0)
        main_splitter.addWidget(right_column_widget)

        self.variants_display_widget = VariantsDisplayWidget()
        right_column_layout.addWidget(self.variants_display_widget)
        self.variants_display_widget.validate_variant_clicked.connect(self._on_validate_variant_clicked)

        main_splitter.setStretchFactor(0, 1) 
        main_splitter.setStretchFactor(1, 2) 
        initial_widths = [self.width() // 3 if self.width() > 0 else 300, 2 * self.width() // 3 if self.width() > 0 else 600] # Safe defaults
        if all(w > 50 for w in initial_widths): # Ensure some minimal width
            main_splitter.setSizes(initial_widths)
        else:
            logger.warning("Largeurs initiales calculées pour le splitter principal non valides ou trop petites, utilisation des tailles par défaut du QSplitter.")
        
        self.update_token_estimation_signal.connect(self.update_token_estimation_ui) 

        # Alias pour compatibilité avec l'ancien code (à refactoriser progressivement)
        self.llm_model_combo = self.generation_params_widget.llm_model_combo
        self.k_variants_combo = self.generation_params_widget.k_variants_combo
        self.max_context_tokens_spinbox = self.generation_params_widget.max_context_tokens_spinbox
        self.structured_output_checkbox = self.generation_params_widget.structured_output_checkbox
        self.token_estimation_label = self.token_and_generate_widget.token_estimation_label
        self.generation_progress_bar = self.token_and_generate_widget.generation_progress_bar
        self.generate_dialogue_button = self.token_and_generate_widget.generate_dialogue_button
        self.refresh_token_button = self.token_and_generate_widget.refresh_token_button
        self.variant_display_tabs = self.variants_display_widget.variant_display_tabs

    def finalize_ui_setup(self):
        logger.debug("Finalizing GenerationPanel UI setup...")
        self.populate_character_combos()
        self.populate_scene_combos()
        self.populate_llm_model_combo() # Charger les modèles LLM dans le ComboBox
        self._trigger_token_update() 
        logger.debug("GenerationPanel UI setup finalized.")

    def populate_llm_model_combo(self):
        self.generation_params_widget.blockSignals(True)
        self.generation_params_widget.clear()
        found_current_model = False
        
        if not self.available_llm_models:
            logger.warning("Aucun modèle LLM disponible à afficher dans le ComboBox.")
            self.generation_params_widget.addItem("Aucun modèle configuré", userData="dummy_error")
            self.generation_params_widget.setEnabled(False)
            self.generation_params_widget.blockSignals(False)
            return

        for model_info in self.available_llm_models:
            display_name = model_info.get("display_name", model_info.get("api_identifier"))
            api_identifier = model_info.get("api_identifier")
            notes = model_info.get("notes", "")
            tooltip = f"{display_name}\nIdentifiant: {api_identifier}\n{notes}"
            self.generation_params_widget.addItem(display_name, userData=api_identifier)
            self.generation_params_widget.setItemData(self.generation_params_widget.count() - 1, tooltip, Qt.ItemDataRole.ToolTipRole)
            if api_identifier == self.current_llm_model_identifier:
                self.generation_params_widget.setCurrentIndex(self.generation_params_widget.count() - 1)
                found_current_model = True
        
        if not found_current_model and self.generation_params_widget.count() > 0:
            logger.warning(f"Modèle LLM actuel '{self.current_llm_model_identifier}' non trouvé dans la liste. Sélection du premier disponible.")
            self.generation_params_widget.setCurrentIndex(0)
            new_default_identifier = self.generation_params_widget.currentData()
            if new_default_identifier and new_default_identifier != self.current_llm_model_identifier:
                self.current_llm_model_identifier = new_default_identifier
                # Pas besoin d'émettre llm_model_selection_changed ici, car c'est l'initialisation.
                # MainWindow sera informé par la valeur de retour de get_settings si nécessaire.
        
        self.llm_model_combo.setEnabled(self.llm_model_combo.count() > 0 and self.llm_model_combo.itemData(0) != "dummy_error")
        self.llm_model_combo.blockSignals(False)
        self._update_structured_output_checkbox_state()

    @Slot(str)
    def _on_llm_model_combo_changed(self, text_model_display_name: str):
        selected_identifier = self.llm_model_combo.currentData()
        if selected_identifier and selected_identifier != self.current_llm_model_identifier and selected_identifier != "dummy_error":
            logger.info(f"Sélection du modèle LLM changée dans GenerationPanel pour : {selected_identifier} ({text_model_display_name})")
            self.current_llm_model_identifier = selected_identifier
            self.llm_model_selection_changed.emit(selected_identifier) 
            self._schedule_settings_save_and_token_update() 
            self._update_structured_output_checkbox_state()
        elif selected_identifier == "dummy_error":
             logger.warning("Changement de modèle LLM ignoré car 'Aucun modèle configuré' est sélectionné.")


    def _update_structured_output_checkbox_state(self):
        # Si le client LLM est un DummyLLMClient, désactiver et décocher la case
        # car le dummy ne gère pas la sortie structurée.
        # Aussi, la rendre non-cochée par défaut si c'est un Dummy.
        is_dummy = isinstance(self.llm_client, DummyLLMClient)
        
        if is_dummy:
            # Garder une trace de l'état précédent si ce n'est pas un dummy
            if not hasattr(self, '_was_structured_output_checked_before_dummy'):
                self._was_structured_output_checked_before_dummy = self.structured_output_checkbox.isChecked()
            self.structured_output_checkbox.setChecked(False)
            self.structured_output_checkbox.setEnabled(False)
            self.structured_output_checkbox.setToolTip("La sortie structurée n'est pas applicable avec DummyLLMClient.")
        else:
            self.structured_output_checkbox.setEnabled(True)
            # Restaurer l'état précédent si on revient d'un dummy
            if hasattr(self, '_was_structured_output_checked_before_dummy'):
                self.structured_output_checkbox.setChecked(self._was_structured_output_checked_before_dummy)
                del self._was_structured_output_checked_before_dummy # Nettoyer l'attribut
            
            # Mise à jour du tooltip en fonction du modèle actuel (si besoin de plus de logique)
            current_model_props = self.main_window_ref.get_current_llm_model_properties()
            if current_model_props and current_model_props.get("supports_json_mode", False):
                self.structured_output_checkbox.setToolTip("Si coché, demande au LLM de formater la sortie en JSON (modèle compatible). Peut améliorer la fiabilité du format Yarn.")
            else:
                # Si le modèle ne supporte pas le mode JSON, on peut choisir de désactiver la case ou juste d'informer.
                # Pour l'instant, on informe et on laisse cocher, car le support peut être implicite.
                self.structured_output_checkbox.setToolTip("Si coché, demande au LLM de formater la sortie en JSON. La compatibilité du modèle actuel avec le mode JSON forcé n'est pas garantie.")

    def _restore_default_system_prompt(self):
        default_prompt = self.prompt_engine._get_default_system_prompt()
        self.system_prompt_textedit.setPlainText(default_prompt)
        # Pas besoin de _schedule_settings_save ici, car _on_system_prompt_changed sera appelé par setPlainText
        # qui appellera _schedule_settings_save_and_token_update.
        # On force la mise à jour du prompt_engine immédiatement.
        self._update_prompt_engine_system_prompt()
        # Déclencher une mise à jour des tokens car le prompt a changé.
        self.update_token_estimation_signal.emit()
        QMessageBox.information(self, "Prompt Restauré", "Le prompt système par défaut a été restauré.")


    def _on_system_prompt_changed(self):
        self._update_prompt_engine_system_prompt()
        self._schedule_settings_save_and_token_update()

    def _update_prompt_engine_system_prompt(self):
        new_system_prompt = self.system_prompt_textedit.toPlainText()
        if self.prompt_engine.system_prompt_template != new_system_prompt:
            self.prompt_engine.system_prompt_template = new_system_prompt
            logger.info("PromptEngine system_prompt_template mis à jour.")
            # La mise à jour des tokens est gérée par _schedule_settings_save_and_token_update
            # ou explicitement par _restore_default_system_prompt


    def set_llm_client(self, new_llm_client):
        logger.info(f"GenerationPanel: Réception d'un nouveau client LLM: {type(new_llm_client).__name__}")
        self.llm_client = new_llm_client
        if hasattr(new_llm_client, 'model'): # Vérifie si le client a un attribut 'model'
            self.current_llm_model_identifier = new_llm_client.model
            self.select_model_in_combo(new_llm_client.model) 
        else: # Pour les clients comme DummyLLMClient qui n'ont pas 'model' mais on peut inférer
            if isinstance(new_llm_client, DummyLLMClient):
                self.current_llm_model_identifier = "dummy" # ou un identifiant spécifique pour dummy
                self.select_model_in_combo("dummy") # Assurez-vous que "dummy" peut être trouvé ou géré
            else:
                logger.warning("Nouveau client LLM n'a pas d'attribut 'model', l'identifiant actuel pourrait être incorrect.")

        self._trigger_token_update()
        self._update_structured_output_checkbox_state()

    def select_model_in_combo(self, model_identifier: str):
        self.llm_model_combo.blockSignals(True)
        found = False
        for i in range(self.llm_model_combo.count()):
            if self.llm_model_combo.itemData(i) == model_identifier:
                self.llm_model_combo.setCurrentIndex(i)
                logger.debug(f"Modèle '{model_identifier}' sélectionné programmatiquement dans le ComboBox LLM.")
                found = True
                break
        if not found:
            logger.warning(f"Tentative de sélection du modèle '{model_identifier}' dans ComboBox LLM, mais non trouvé. Le premier item sera peut-être sélectionné par défaut.")
            # Optionnel: si non trouvé et que la liste n'est pas vide et pas l'erreur dummy, sélectionner le premier.
            if self.llm_model_combo.count() > 0 and self.llm_model_combo.itemData(0) != "dummy_error":
                # self.llm_model_combo.setCurrentIndex(0)
                # self.current_llm_model_identifier = self.llm_model_combo.currentData()
                # logger.info(f"Modèle '{model_identifier}' non trouvé, '{self.current_llm_model_identifier}' sélectionné à la place.")
                # self.llm_model_selection_changed.emit(self.current_llm_model_identifier) # Informer MainWindow
                pass # Laisser le combobox tel quel ou sur la sélection précédente.
                     # La logique dans _on_llm_model_combo_changed gère l'émission du signal si l'utilisateur change.


        self.llm_model_combo.blockSignals(False)
        self._update_structured_output_checkbox_state() # Mettre à jour après la sélection

    def populate_character_combos(self):
        characters = sorted(self.context_builder.get_characters_names())
        self.scene_selection_widget.character_a_combo.blockSignals(True)
        self.scene_selection_widget.character_b_combo.blockSignals(True)
        self.scene_selection_widget.character_a_combo.clear()
        self.scene_selection_widget.character_b_combo.clear()
        self.scene_selection_widget.character_a_combo.addItems(["(Aucun)"] + characters)
        self.scene_selection_widget.character_b_combo.addItems(["(Aucun)"] + characters)
        self.scene_selection_widget.character_a_combo.blockSignals(False)
        self.scene_selection_widget.character_b_combo.blockSignals(False)
        logger.debug("Character combos populated.")

    def populate_scene_combos(self):
        regions = sorted(self.context_builder.get_regions())
        self.scene_selection_widget.scene_region_combo.blockSignals(True)
        self.scene_selection_widget.scene_sub_location_combo.blockSignals(True)
        self.scene_selection_widget.scene_region_combo.clear()
        self.scene_selection_widget.scene_region_combo.addItem("(Aucune)") 
        self.scene_selection_widget.scene_region_combo.addItems(regions)
        self.scene_selection_widget.scene_region_combo.blockSignals(False)
        self.scene_selection_widget.scene_sub_location_combo.blockSignals(False)
        self._on_scene_region_changed(self.scene_selection_widget.scene_region_combo.currentText() or "(Aucune)")
        logger.debug("Scene region combo populated.")

    @Slot(str)
    def _on_scene_region_changed(self, region_name: str):
        self.scene_selection_widget.scene_sub_location_combo.clear()
        if region_name and region_name != "(Aucun)" and region_name != "(Sélectionner une région)":
            try:
                # sub_locations = sorted(self.context_builder.get_sub_locations_for_region(region_name))
                sub_locations = sorted(self.context_builder.get_sub_locations(region_name))
                if not sub_locations:
                    logger.info(f"Aucun sous-lieu trouvé pour la région : {region_name}")
                    self.scene_selection_widget.scene_sub_location_combo.addItem("(Aucun sous-lieu)")
                else:
                    self.scene_selection_widget.scene_sub_location_combo.addItems(["(Tous / Non spécifié)"] + sub_locations)
                    self.scene_selection_widget.scene_sub_location_combo.setEnabled(True)
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des sous-lieux pour la région {region_name}: {e}", exc_info=True)
                self.scene_selection_widget.scene_sub_location_combo.addItem("(Erreur de chargement des sous-lieux)")
                self.scene_selection_widget.scene_sub_location_combo.setEnabled(False)
        else:
            self.scene_selection_widget.scene_sub_location_combo.addItem("(Sélectionner une région d'abord)")
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

        user_specific_goal = self.user_instructions_textedit.toPlainText()
        selected_context_items = self.main_window_ref._get_current_context_selections() if hasattr(self.main_window_ref, '_get_current_context_selections') else {}

        char_a_name = self.scene_selection_widget.character_a_combo.currentText()
        char_b_name = self.scene_selection_widget.character_b_combo.currentText()
        scene_region_name = self.scene_selection_widget.scene_region_combo.currentText()
        scene_sub_location_name = self.scene_selection_widget.scene_sub_location_combo.currentText()

        char_a_name = char_a_name if char_a_name and char_a_name != "(Aucun)" else None
        char_b_name = char_b_name if char_b_name and char_b_name != "(Aucun)" else None
        scene_region_name = scene_region_name if scene_region_name and scene_region_name != "(Aucune)" else None
        scene_sub_location_name = scene_sub_location_name if scene_sub_location_name and scene_sub_location_name != "(Tous / Non spécifié)" and scene_sub_location_name != "(Aucun sous-lieu)" and scene_sub_location_name != "(Sélectionner une région d\'abord)" else None

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
            # Assurer que le prompt_engine a le system_prompt à jour de l'UI pour une estimation correcte
            self._update_prompt_engine_system_prompt()

            # Similaire à _on_generate_dialogue_button_clicked_local
            context_summary_text_for_estimation = self.context_builder.build_context(
                selected_elements=selected_context_items,
                scene_instruction=user_specific_goal, # L'objectif utilisateur sert d'instruction de scène pour ContextBuilder
                max_tokens=self.main_window_ref.app_settings.get("max_context_tokens", 1500) # Utilise app_settings de MainWindow
            )
            
            full_prompt_for_estimation, prompt_tokens = self.prompt_engine.build_prompt(
                user_specific_goal=user_specific_goal,
                scene_protagonists=scene_protagonists_dict if scene_protagonists_dict else None,
                scene_location=scene_location_dict if scene_location_dict else None,
                context_summary=context_summary_text_for_estimation,
                generation_params=None # Pas besoin de params spécifiques pour l'estimation ici, ils n'affectent que le contenu pas la structure comptée
            )
            # Pour context_tokens, on ne compte que ce qui vient de context_builder
            # car le system_prompt, les persos/lieux et l'objectif sont fixes en termes de structure.
            # Ou, plus simplement, on recompte juste la partie context_summary_text_for_estimation.
            context_tokens = self.prompt_engine._count_tokens(context_summary_text_for_estimation) if context_summary_text_for_estimation else 0

            logger.debug(f"[GenerationPanel.update_token_estimation_ui] Context summary for estimation (first 300 chars): {context_summary_text_for_estimation[:300] if context_summary_text_for_estimation else 'None'}") # LOG AJOUTÉ
            logger.debug(f"[GenerationPanel.update_token_estimation_ui] Full prompt for estimation (first 300 chars): {full_prompt_for_estimation[:300] if full_prompt_for_estimation else 'None'}") # LOG AJOUTÉ

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

        try:
            k_variants = int(self.k_variants_combo.currentText())
            user_instructions = self.user_instructions_textedit.toPlainText()
            # Le system_prompt est maintenant géré directement par self.prompt_engine via _update_prompt_engine_system_prompt
            # lors de la modification du system_prompt_textedit ou de la restauration par défaut.
            # Il n'est donc plus nécessaire de le passer explicitement ici à build_prompt,
            # car self.prompt_engine aura déjà la version la plus à jour.

            selected_context_items = self.main_window_ref._get_current_context_selections() # Récupère les items cochés
            
            char_a_name = self.scene_selection_widget.character_a_combo.currentText()
            char_b_name = self.scene_selection_widget.character_b_combo.currentText()
            scene_region_name = self.scene_selection_widget.scene_region_combo.currentText()
            scene_sub_location_name = self.scene_selection_widget.scene_sub_location_combo.currentText()

            # Nettoyage des noms pour éviter de passer "(Aucun)" ou des chaînes vides si non pertinents
            char_a_name = char_a_name if char_a_name and char_a_name != "(Aucun)" else None
            char_b_name = char_b_name if char_b_name and char_b_name != "(Aucun)" else None
            scene_region_name = scene_region_name if scene_region_name and scene_region_name != "(Aucune)" else None
            scene_sub_location_name = scene_sub_location_name if scene_sub_location_name and scene_sub_location_name != "(Tous / Non spécifié)" else None

            scene_protagonists_dict = {}
            if char_a_name: scene_protagonists_dict["personnage_a"] = char_a_name
            if char_b_name: scene_protagonists_dict["personnage_b"] = char_b_name

            scene_location_dict = {}
            if scene_region_name: scene_location_dict["lieu"] = scene_region_name
            if scene_sub_location_name: scene_location_dict["sous_lieu"] = scene_sub_location_name
            
            # Mettre à jour le moteur de prompt avec le system prompt actuel de l'UI AVANT de construire le contexte
            # Cela garantit que l'estimation des tokens et la génération utilisent le dernier prompt système.
            self._update_prompt_engine_system_prompt() 

            # Construction du contexte via ContextBuilder
            # Le ContextBuilder doit maintenant aussi prendre les protagonistes et lieu pour potentiellement les exclure du résumé général
            # ou pour affiner le contexte. Pour l'instant, on passe les items sélectionnés et il fera le tri.
            # TODO: Affiner ContextBuilder pour qu'il utilise scene_protagonists et scene_location pour mieux cibler le contexte.
            # Pour l'instant, on passe les items sélectionnés et ContextBuilder.build_context s'attend à une "scene_instruction" qui peut être l'objectif utilisateur.
            context_summary_text = self.context_builder.build_context(
                selected_elements=selected_context_items,
                scene_instruction=user_instructions, # L'objectif utilisateur sert d'instruction de scène pour ContextBuilder
                max_tokens=self.main_window_ref.app_settings.get("max_context_tokens", 1500) # Utilise app_settings de MainWindow
            )

            # Construction du prompt via PromptEngine avec la nouvelle structure
            full_prompt, estimated_tokens = self.prompt_engine.build_prompt(
                user_specific_goal=user_instructions,
                scene_protagonists=scene_protagonists_dict if scene_protagonists_dict else None,
                scene_location=scene_location_dict if scene_location_dict else None,
                context_summary=context_summary_text, # Le reste du contexte
                generation_params={ # TODO: Exposer ces paramètres dans l'UI si nécessaire
                    "tone": "Neutre", 
                    "model_identifier": self.current_llm_model_identifier
                }
            )
            # Affichage des tokens en milliers (k)
            estimated_tokens_k = estimated_tokens / 1000
            self.token_estimation_label.setText(f"Tokens prompt final: {estimated_tokens_k:.1f}k")
            self._display_prompt_in_tab(full_prompt)

            logger.debug(f"[GenerationPanel._on_generate_dialogue_button_clicked_local] Context summary sent to LLM (first 300 chars): {context_summary_text[:300] if context_summary_text else 'None'}") # LOG AJOUTÉ
            logger.debug(f"[GenerationPanel._on_generate_dialogue_button_clicked_local] Full prompt sent to LLM (first 300 chars): {full_prompt[:300] if full_prompt else 'None'}") # LOG AJOUTÉ

            if not self.llm_client:
                logger.error("Erreur: Client LLM non initialisé.")
                self.generation_finished.emit(False)
                return

            logger.info(f"Appel de llm_client.generate_variants avec k={k_variants}...")
            
            # Modification pour gérer la sortie structurée
            # Cela nécessite que OpenAIClient.generate_variants soit adapté.
            response_format_param = None
            if self.structured_output_checkbox.isChecked() and isinstance(self.llm_client, OpenAIClient):
                logger.info("Sortie structurée demandée (JSON).")
                # L'API OpenAI attend un objet pour 'response_format', par exemple {'type': 'json_object'}
                # Pour utiliser un schéma JSON spécifique, il faut l'inclure dans les 'tools' ou 'functions'
                # et forcer son utilisation. Pour l'instant, on ne fait que demander du JSON simple.
                # IMPORTANT: Le prompt doit aussi instruire le LLM à produire du JSON.
                # Notre PromptEngine devrait être adapté pour inclure ces instructions et le schéma si nécessaire.
                response_format_param = {"type": "json_object"}
                # Il faudra aussi ajuster le system_prompt/user_prompt pour indiquer au LLM de suivre un schéma JSON
                # (par exemple, celui de YarnScene et YarnNode).
                # full_prompt += "\n\nIMPORTANT: Formattez votre réponse comme un objet JSON valide respectant le schéma YarnScene (une liste de YarnNode)."

            # TODO: Refactor ILLMClient and OpenAIClient to accept response_format_param
            # For now, this parameter is not used by the current llm_client.generate_variants signature.
            # variants = await self.llm_client.generate_variants(full_prompt, k_variants, response_format=response_format_param) # Hypothetical
            variants = await self.llm_client.generate_variants(full_prompt, k_variants) # Current signature

            logger.debug(f"Valeur de 'variants' reçue du LLM Client: {type(variants)} - Contenu (si liste): {variants if isinstance(variants, list) else 'Non une liste'}")
            
            self.variants_display_widget.blockSignals(True)
            num_tabs_to_keep = 0
            if self.variants_display_widget.count() > 0 and self.variants_display_widget.tabText(0) == "Prompt Estimé":
                num_tabs_to_keep = 1
            
            while self.variants_display_widget.count() > num_tabs_to_keep:
                self.variants_display_widget.removeTab(num_tabs_to_keep)
            
            if variants:
                for i, variant_text in enumerate(variants):
                    variant_tab_content_widget = QWidget()
                    tab_layout = QVBoxLayout(variant_tab_content_widget)
                    tab_layout.setContentsMargins(5, 5, 5, 5)
                    tab_layout.setSpacing(5)

                    text_edit = QTextEdit()
                    text_edit.setPlainText(variant_text)
                    text_edit.setReadOnly(True)
                    text_edit.setFont(QFont("Consolas", 10)) 
                    tab_layout.addWidget(text_edit)

                    validate_button = QPushButton(f"Valider et Enregistrer Variante {i+1} en .yarn")
                    validate_button.setIcon(get_icon_path("save.png"))
                    validate_button.clicked.connect(
                        lambda checked=False, index=i: self._on_validate_variant_clicked(index)
                    )
                    tab_layout.addWidget(validate_button)
                    
                    self.variants_display_widget.addTab(variant_tab_content_widget, f"Variante {i+1}")
                generation_succeeded = True
                logger.info(f"{len(variants)} variantes affichées.")
            else:
                logger.warning("Aucune variante reçue du LLM ou variants est None/vide.")
                error_tab = QTextEdit("Aucune variante n'a été générée par le LLM ou une erreur s'est produite.")
                error_tab.setReadOnly(True)
                self.variants_display_widget.addTab(error_tab, "Erreur Génération")
            
            self.variants_display_widget.blockSignals(False)

        except asyncio.CancelledError:
            logger.warning("La tâche de génération de dialogue a été annulée.")
            return 
        except Exception as e:
            logger.error(f"Erreur majeure lors de la génération des dialogues: {e}", exc_info=True)
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
                logger.debug(f"Émission du signal generation_finished avec la valeur : {generation_succeeded}")
                self.generation_finished.emit(generation_succeeded)

    def _display_prompt_in_tab(self, prompt_text: str):
        logger.info(f"_display_prompt_in_tab: Entrée avec prompt_text de longueur {len(prompt_text)} chars.")
        self.variants_display_widget.blockSignals(True)
        
        prompt_tab_index = -1
        for i in range(self.variants_display_widget.count()):
            if self.variants_display_widget.tabText(i) == "Prompt Estimé":
                prompt_tab_index = i
                break
        
        if prompt_tab_index != -1:
            logger.info(f"_display_prompt_in_tab: Onglet 'Prompt Estimé' trouvé à l'index {prompt_tab_index}. Mise à jour du contenu.")
            # Onglet existant, mettre à jour son contenu
            widget = self.variants_display_widget.widget(prompt_tab_index)
            if isinstance(widget, QTextEdit):
                 widget.setPlainText(prompt_text)
            else: # Si c'est un QWidget contenant un QTextEdit (moins probable avec le code actuel)
                text_edit = widget.findChild(QTextEdit)
                if text_edit: text_edit.setPlainText(prompt_text)
                else: logger.error("Impossible de trouver QTextEdit dans l'onglet Prompt existant.")
        else:
            logger.info("_display_prompt_in_tab: Onglet 'Prompt Estimé' non trouvé. Création d'un nouvel onglet à l'index 0.")
            # Créer un nouvel onglet pour le prompt
            prompt_tab_widget = QTextEdit()
            prompt_tab_widget.setPlainText(prompt_text)
            prompt_tab_widget.setReadOnly(True)
            prompt_tab_widget.setFont(QFont("Consolas", 9)) 
            self.variants_display_widget.insertTab(0, prompt_tab_widget, "Prompt Estimé")
        
        logger.info("_display_prompt_in_tab: Appel de setCurrentIndex(0).")
        self.variants_display_widget.setCurrentIndex(0) 
        self.variants_display_widget.blockSignals(False)
        logger.info("_display_prompt_in_tab: Sortie.")

    @Slot(int)
    def _on_validate_variant_clicked(self, variant_index: int):
        actual_tab_index = -1
        expected_tab_name = f"Variante {variant_index + 1}"
        for i in range(self.variants_display_widget.count()):
            if self.variants_display_widget.tabText(i) == expected_tab_name:
                actual_tab_index = i
                break

        if actual_tab_index == -1:
            logger.error(f"Onglet pour la variante {variant_index + 1} non trouvé.")
            self.main_window_ref.statusBar().showMessage(f"Erreur: Onglet pour variante {variant_index + 1} non trouvé.", 5000)
            return

        tab_content_widget = self.variants_display_widget.widget(actual_tab_index)
        if not tab_content_widget:
            logger.error(f"Contenu de l'onglet pour la variante {variant_index + 1} est None.")
            return

        text_edit: Optional[QTextEdit] = tab_content_widget.findChild(QTextEdit)
        
        if not text_edit:
            logger.error(f"QTextEdit non trouvé dans l'onglet de la variante {variant_index + 1}.")
            self.main_window_ref.statusBar().showMessage(f"Erreur: QTextEdit non trouvé pour variante {variant_index + 1}.", 5000)
            return

        dialogue_text_content = text_edit.toPlainText()

        title_from_text = f"GeneratedDialogue_Variant{variant_index + 1}"
        char_a_name = self.scene_selection_widget.character_a_combo.currentText() if self.scene_selection_widget.character_a_combo.currentText() != "(Aucun)" else "PersonnageA"
        char_b_name = self.scene_selection_widget.character_b_combo.currentText() if self.scene_selection_widget.character_b_combo.currentText() != "(Aucun)" else "PersonnageB"
        scene_name = self.scene_selection_widget.scene_region_combo.currentText() if self.scene_selection_widget.scene_region_combo.currentText() != "(Aucune)" else "LieuIndéfini"
        
        try:
            first_line = dialogue_text_content.split('\n', 1)[0]
            if first_line.startswith("---title:"):
                extracted_title = first_line.replace("---title:", "").strip()
                if extracted_title: title_from_text = extracted_title
        except Exception: 
            pass 

        metadata = {
            "title": title_from_text,
            "character_a": char_a_name,
            "character_b": char_b_name,
            "scene": scene_name,
        }

        try:
            yarn_content = self.yarn_renderer.render(dialogue_content=dialogue_text_content, metadata=metadata)
        except Exception as e:
            logger.error(f"Erreur lors du rendu Yarn pour la variante {variant_index + 1}: {e}", exc_info=True)
            self.main_window_ref.statusBar().showMessage(f"Erreur rendu Yarn: {e}", 5000)
            QMessageBox.critical(self, "Erreur de Rendu Yarn", f"Impossible de générer le contenu .yarn:\n{e}")
            return

        base_dialogues_path = None
        if hasattr(self.main_window_ref, 'get_unity_dialogues_path'):
             base_dialogues_path = self.main_window_ref.get_unity_dialogues_path()

        if not base_dialogues_path:
            QMessageBox.warning(self, "Chemin Manquant", 
                                "Le chemin des dialogues Unity n'est pas configuré. Impossible de sauvegarder.")
            self.main_window_ref.statusBar().showMessage("Erreur: Chemin des dialogues Unity non configuré.", 5000)
            return
        
        generated_path = base_dialogues_path / "generated"
        try:
            generated_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"Impossible de créer le dossier {generated_path}: {e}")
            QMessageBox.critical(self, "Erreur de Dossier", f"Impossible de créer le dossier de destination:\n{generated_path}\nErreur: {e}")
            return

        clean_title = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in title_from_text)
        if not clean_title: clean_title = f"dialogue_variant_{variant_index + 1}"
        output_filename = f"{clean_title}.yarn"
        output_filepath = generated_path / output_filename

        try:
            with open(output_filepath, "w", encoding="utf-8") as f:
                f.write(yarn_content)
            logger.info(f"Variante {variant_index + 1} sauvegardée avec succès sous: {output_filepath}")
            self.main_window_ref.statusBar().showMessage(f"Dialogue sauvegardé : {output_filename}", 5000)
        except IOError as e:
            logger.error(f"Erreur lors de la sauvegarde du fichier .yarn ({output_filepath}): {e}", exc_info=True)
            self.main_window_ref.statusBar().showMessage(f"Erreur sauvegarde: {e}", 5000)
            QMessageBox.critical(self, "Erreur de Sauvegarde", f"Impossible de sauvegarder le fichier .yarn:\n{output_filepath}\nErreur: {e}")

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

        placeholders = ["(Aucun)", "(Aucune)", "(Tous / Non spécifié)", "(Aucun sous-lieu)", "(Sélectionner une région d'abord)"]

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
            self.main_window_ref.statusBar().showMessage("Tous les éléments ont été décochés.", 3000)
            # QApplication.instance().beep() # Optionnel, si le son est gênant
        else:
            logger.warning("Impossible de tout décocher: left_panel ou méthode uncheck_all_items non trouvée.")
            self.main_window_ref.statusBar().showMessage("Erreur: Impossible de tout décocher.", 3000)

    def get_settings(self) -> dict:
        # Récupère les paramètres actuels du panneau pour la sauvegarde.
        settings = {
            "character_a": self.scene_selection_widget.character_a_combo.currentText(),
            "character_b": self.scene_selection_widget.character_b_combo.currentText(),
            "scene_region": self.scene_selection_widget.scene_region_combo.currentText(),
            "scene_sub_location": self.scene_selection_widget.scene_sub_location_combo.currentText(),
            "k_variants": self.k_variants_combo.currentText(),
            "user_instructions": self.user_instructions_textedit.toPlainText(),
            "llm_model": self.llm_model_combo.currentData(), # Sauvegarde l'identifiant du modèle
            "structured_output": self.structured_output_checkbox.isChecked(),
            "system_prompt": self.system_prompt_textedit.toPlainText(), # Ajout du system prompt
            "max_context_tokens": self.max_context_tokens_spinbox.value() # Ajout de max_context_tokens
        }
        logger.debug(f"Récupération des paramètres du GenerationPanel: {settings}")
        return settings

    def load_settings(self, settings: dict):
        logger.debug(f"Chargement des paramètres dans GenerationPanel: {settings}")
        
        # Indicateur pour éviter les mises à jour de tokens pendant le chargement
        self._is_loading_settings = True
        
        # Charger les combobox pour personnages et scènes
        # Ces appels vont déclencher currentTextChanged, qui appelle _schedule_settings_save_and_token_update
        # C'est pourquoi _is_loading_settings est important.
        self.scene_selection_widget.character_a_combo.setCurrentText(settings.get("character_a", ""))
        self.scene_selection_widget.character_b_combo.setCurrentText(settings.get("character_b", ""))
        self.scene_selection_widget.scene_region_combo.setCurrentText(settings.get("scene_region", ""))
        # _on_scene_region_changed sera appelé, qui remplira les sous-lieux.
        # Il faut donc charger le sous-lieu APRES que scene_region_combo ait potentiellement re-peuplé sub_location
        # Ce qui est un peu délicat. On peut appeler processEvents ou simplement le setter après.
        QApplication.processEvents() # Force le traitement des événements (comme _on_scene_region_changed)
        self.scene_selection_widget.scene_sub_location_combo.setCurrentText(settings.get("scene_sub_location", ""))
        
        self.k_variants_combo.setCurrentText(settings.get("k_variants", "3"))
        self.user_instructions_textedit.setPlainText(settings.get("user_instructions", ""))
        
        model_identifier = settings.get("llm_model")
        if model_identifier:
            self.select_model_in_combo(model_identifier)
        else:
            # Si aucun modèle n'est sauvegardé, essayer de sélectionner le premier de la liste
            if self.llm_model_combo.count() > 0:
                self.llm_model_combo.setCurrentIndex(0)
        
        self.structured_output_checkbox.setChecked(settings.get("structured_output", True))
        
        # Charger le system prompt
        saved_system_prompt = settings.get("system_prompt")
        if saved_system_prompt:
            self.system_prompt_textedit.setPlainText(saved_system_prompt)
        else:
            # Si aucun prompt système n'est sauvegardé, charger celui par défaut
            self._restore_default_system_prompt() # Ceci mettra aussi à jour prompt_engine
        self._update_prompt_engine_system_prompt() # Assurer la synchro avec prompt_engine
        
        # Charger max_context_tokens depuis MainWindow si disponible
        if hasattr(self.main_window_ref, 'app_settings') and "max_context_tokens" in self.main_window_ref.app_settings:
            # Convertir tokens en k-tokens pour l'affichage
            tokens_value = self.main_window_ref.app_settings["max_context_tokens"]
            k_tokens_value = tokens_value / 1000
            self.max_context_tokens_spinbox.setValue(k_tokens_value)
        
        self._is_loading_settings = False
        # Déclencher une mise à jour manuelle des tokens après le chargement complet
        self.update_token_estimation_signal.emit()
        logger.info("Paramètres du GenerationPanel chargés.")

    @Slot(float)
    def _on_max_context_tokens_changed(self, new_value: float):
        """Appelé quand l'utilisateur change la limite de tokens pour le contexte."""
        # Convertir de k-tokens (ex: 1.5k) en tokens (ex: 1500)
        tokens_value = int(new_value * 1000)
        
        if hasattr(self.main_window_ref, 'app_settings'):
            self.main_window_ref.app_settings["max_context_tokens"] = tokens_value
            logger.info(f"Limite de tokens pour le contexte mise à jour: {tokens_value} ({new_value}k)")
            self._schedule_settings_save_and_token_update()