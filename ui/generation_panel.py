from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QGridLayout, 
                               QLabel, QComboBox, QTextEdit, QPushButton, 
                               QTabWidget, QLineEdit, QCheckBox, QHBoxLayout, QApplication, QSizePolicy, QProgressBar, QScrollArea, QSplitter, QFrame, QPlainTextEdit, QMessageBox, QSpacerItem, QMenu, QStyle)
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
        selection_group = QGroupBox("Contexte Principal de la Scène")
        selection_layout = QGridLayout(selection_group)
        left_column_layout.addWidget(selection_group)

        row = 0
        selection_layout.addWidget(QLabel("Personnage A:"), row, 0)
        self.character_a_combo = QComboBox()
        self.character_a_combo.setToolTip("Sélectionnez le premier personnage principal de la scène.")
        self.character_a_combo.currentTextChanged.connect(self._schedule_settings_save_and_token_update)
        selection_layout.addWidget(self.character_a_combo, row, 1)
        row += 1

        selection_layout.addWidget(QLabel("Personnage B:"), row, 0)
        self.character_b_combo = QComboBox()
        self.character_b_combo.setToolTip("Sélectionnez le second personnage principal de la scène (optionnel).")
        self.character_b_combo.currentTextChanged.connect(self._schedule_settings_save_and_token_update)
        selection_layout.addWidget(self.character_b_combo, row, 1)
        row += 1
        
        self.swap_characters_button = QPushButton()
        self.swap_characters_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ToolBarHorizontalExtensionButton))
        self.swap_characters_button.setToolTip("Échanger Personnage A et Personnage B")
        self.swap_characters_button.clicked.connect(self._swap_characters)
        self.swap_characters_button.setFixedSize(QSize(28, 28)) 
        selection_layout.addWidget(self.swap_characters_button, 0, 2, 2, 1, Qt.AlignmentFlag.AlignCenter)

        selection_layout.addWidget(QLabel("Région de la Scène:"), row, 0)
        self.scene_region_combo = QComboBox()
        self.scene_region_combo.setToolTip("Sélectionnez la région où se déroule la scène.")
        self.scene_region_combo.currentTextChanged.connect(self._on_scene_region_changed)
        selection_layout.addWidget(self.scene_region_combo, row, 1, 1, 2) 
        row += 1

        selection_layout.addWidget(QLabel("Sous-Lieu (optionnel):"), row, 0)
        self.scene_sub_location_combo = QComboBox()
        self.scene_sub_location_combo.setToolTip("Sélectionnez le sous-lieu plus spécifique (si applicable).")
        self.scene_sub_location_combo.currentTextChanged.connect(self._schedule_settings_save_and_token_update)
        selection_layout.addWidget(self.scene_sub_location_combo, row, 1, 1, 2)
        row += 1

        # --- Section Actions sur le Contexte ---
        context_actions_group = QGroupBox("Actions sur le Contexte Secondaire")
        context_actions_layout = QHBoxLayout(context_actions_group)
        left_column_layout.addWidget(context_actions_group)

        self.select_linked_button = QPushButton("Lier Éléments Connexes")
        self.select_linked_button.setIcon(get_icon_path("link.png"))
        self.select_linked_button.setToolTip(
            "Coche automatiquement dans le panneau de gauche les éléments (personnages, lieux) liés aux personnages A/B et à la scène sélectionnés ici."
        )
        self.select_linked_button.clicked.connect(self._on_select_linked_elements_clicked)
        context_actions_layout.addWidget(self.select_linked_button)

        self.unlink_unrelated_button = QPushButton("Décocher Non-Connexes")
        self.unlink_unrelated_button.setIcon(get_icon_path("link_off.png"))
        self.unlink_unrelated_button.setToolTip(
            "Décoche dans le panneau de gauche les éléments qui ne sont PAS liés aux personnages A/B et à la scène sélectionnés ici."
        )
        self.unlink_unrelated_button.clicked.connect(self._on_unlink_unrelated_clicked)
        context_actions_layout.addWidget(self.unlink_unrelated_button)

        self.uncheck_all_button = QPushButton("Tout Décocher")
        self.uncheck_all_button.setIcon(get_icon_path("clear_all.png"))
        self.uncheck_all_button.setToolTip(
            "Décoche tous les éléments dans toutes les listes du panneau de gauche."
        )
        self.uncheck_all_button.clicked.connect(self._on_uncheck_all_clicked)
        context_actions_layout.addWidget(self.uncheck_all_button)

        # --- Section Paramètres de Génération ---
        generation_params_group = QGroupBox("Paramètres de Génération")
        generation_params_layout = QGridLayout(generation_params_group)
        left_column_layout.addWidget(generation_params_group)

        row = 0
        generation_params_layout.addWidget(QLabel("Modèle LLM:"), row, 0)
        self.llm_model_combo = QComboBox()
        self.llm_model_combo.setToolTip("Choisissez le modèle de langage à utiliser pour la génération.")
        self.llm_model_combo.currentTextChanged.connect(self._on_llm_model_combo_changed) # Connecter le signal
        generation_params_layout.addWidget(self.llm_model_combo, row, 1)
        row += 1

        generation_params_layout.addWidget(QLabel("Nombre de Variantes (k):"), row, 0)
        self.k_variants_combo = QComboBox()
        self.k_variants_combo.addItems([str(i) for i in range(1, 6)]) 
        self.k_variants_combo.setCurrentText("2")
        self.k_variants_combo.setToolTip("Nombre de dialogues alternatifs à générer.")
        self.k_variants_combo.currentTextChanged.connect(self._schedule_settings_save)
        generation_params_layout.addWidget(self.k_variants_combo, row, 1)
        row += 1
        
        self.structured_output_checkbox = QCheckBox("Utiliser Sortie Structurée (JSON)")
        self.structured_output_checkbox.setToolTip("Si coché, demande au LLM de formater la sortie en JSON (nécessite un modèle compatible). Peut améliorer la fiabilité du format Yarn.")
        self.structured_output_checkbox.setChecked(True) 
        self.structured_output_checkbox.setEnabled(True) # Sera mis à jour par _update_structured_output_checkbox_state
        self.structured_output_checkbox.stateChanged.connect(self._schedule_settings_save)
        generation_params_layout.addWidget(self.structured_output_checkbox, row, 0, 1, 2)
        row +=1

        # --- Section Instructions Utilisateur ---
        instructions_group = QGroupBox("Instructions Utilisateur pour le LLM")
        instructions_layout = QVBoxLayout(instructions_group)
        left_column_layout.addWidget(instructions_group)

        self.user_instructions_textedit = QPlainTextEdit()
        self.user_instructions_textedit.setPlaceholderText(
            "Ex: Bob doit annoncer à Alice qu'il part à l'aventure. Ton désiré: Héroïque. Inclure une condition sur la compétence 'Charisme' de Bob."
        )
        self.user_instructions_textedit.setToolTip("Décrivez le but de la scène, le ton, les points clés à aborder, ou toute autre instruction spécifique pour l'IA.")
        self.user_instructions_textedit.textChanged.connect(self._schedule_settings_save_and_token_update)
        instructions_layout.addWidget(self.user_instructions_textedit)

        # --- Section Estimation Tokens et Bouton Générer ---
        token_button_group = QGroupBox("Actions")
        token_button_layout = QVBoxLayout(token_button_group)
        left_column_layout.addWidget(token_button_group)
        
        estimation_h_layout = QHBoxLayout()
        self.token_estimation_label = QLabel("Estimation tokens (contexte/prompt): N/A")
        self.token_estimation_label.setToolTip("Estimation du nombre de tokens basé sur le contexte sélectionné et les instructions.")
        estimation_h_layout.addWidget(self.token_estimation_label)
        estimation_h_layout.addStretch()
        self.refresh_token_button = QPushButton()
        self.refresh_token_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        self.refresh_token_button.setToolTip("Rafraîchir l'estimation des tokens")
        self.refresh_token_button.clicked.connect(self._trigger_token_update)
        self.refresh_token_button.setFixedSize(QSize(28,28))
        estimation_h_layout.addWidget(self.refresh_token_button)
        token_button_layout.addLayout(estimation_h_layout)

        self.generation_progress_bar = QProgressBar()
        self.generation_progress_bar.setVisible(False) 
        token_button_layout.addWidget(self.generation_progress_bar)

        self.generate_dialogue_button = QPushButton("Générer Dialogues")
        self.generate_dialogue_button.setIcon(get_icon_path("robot.png"))
        self.generate_dialogue_button.setToolTip("Lance la génération des dialogues avec les paramètres actuels (F5).")
        self.generate_dialogue_button.clicked.connect(self._launch_dialogue_generation) 
        self.generate_dialogue_button.setStyleSheet("font-weight: bold; padding: 5px;")
        token_button_layout.addWidget(self.generate_dialogue_button)

        left_column_layout.addStretch() 

        # --- Colonne de Droite: Affichage des Variantes ---
        right_column_widget = QWidget()
        right_column_layout = QVBoxLayout(right_column_widget)
        right_column_layout.setContentsMargins(0,0,0,0)
        main_splitter.addWidget(right_column_widget)

        self.variant_display_tabs = QTabWidget()
        self.variant_display_tabs.setToolTip("Les dialogues générés par l'IA apparaîtront ici, chacun dans son onglet.")
        self.variant_display_tabs.setTabsClosable(False) 
        right_column_layout.addWidget(self.variant_display_tabs)

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
        self.populate_character_combos()
        self.populate_scene_combos()
        self.populate_llm_model_combo() # Charger les modèles LLM dans le ComboBox
        self._trigger_token_update() 
        logger.debug("GenerationPanel UI setup finalized.")

    def populate_llm_model_combo(self):
        self.llm_model_combo.blockSignals(True)
        self.llm_model_combo.clear()
        found_current_model = False
        
        if not self.available_llm_models:
            logger.warning("Aucun modèle LLM disponible à afficher dans le ComboBox.")
            self.llm_model_combo.addItem("Aucun modèle configuré", userData="dummy_error")
            self.llm_model_combo.setEnabled(False)
            self.llm_model_combo.blockSignals(False)
            return

        for model_info in self.available_llm_models:
            display_name = model_info.get("display_name", model_info.get("api_identifier"))
            api_identifier = model_info.get("api_identifier")
            notes = model_info.get("notes", "")
            tooltip = f"{display_name}\nIdentifiant: {api_identifier}\n{notes}"
            self.llm_model_combo.addItem(display_name, userData=api_identifier)
            self.llm_model_combo.setItemData(self.llm_model_combo.count() - 1, tooltip, Qt.ItemDataRole.ToolTipRole)
            if api_identifier == self.current_llm_model_identifier:
                self.llm_model_combo.setCurrentIndex(self.llm_model_combo.count() - 1)
                found_current_model = True
        
        if not found_current_model and self.llm_model_combo.count() > 0:
            logger.warning(f"Modèle LLM actuel '{self.current_llm_model_identifier}' non trouvé dans la liste. Sélection du premier disponible.")
            self.llm_model_combo.setCurrentIndex(0)
            new_default_identifier = self.llm_model_combo.currentData()
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
        is_openai_model = False
        # On considère qu'un modèle est OpenAI s'il est géré par OpenAIClient et commence par "gpt-"
        # ou si self.llm_client est une instance de OpenAIClient (ce qui est plus fiable).
        if self.llm_client and isinstance(self.llm_client, OpenAIClient):
             if self.current_llm_model_identifier and self.current_llm_model_identifier.startswith("gpt-"):
                 is_openai_model = True
        
        self.structured_output_checkbox.setEnabled(is_openai_model)
        if not is_openai_model and self.structured_output_checkbox.isChecked():
            self.structured_output_checkbox.setChecked(False) 
            logger.info("Sortie structurée désactivée car le modèle sélectionné ou le client actuel ne semble pas la supporter (non OpenAI gpt-).")
        elif is_openai_model:
             logger.debug(f"Modèle {self.current_llm_model_identifier} est OpenAI, checkbox 'sortie structurée' activée.")


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
        self.character_a_combo.blockSignals(True)
        self.character_b_combo.blockSignals(True)
        self.character_a_combo.clear()
        self.character_b_combo.clear()
        self.character_a_combo.addItems(["(Aucun)"] + characters)
        self.character_b_combo.addItems(["(Aucun)"] + characters)
        self.character_a_combo.blockSignals(False)
        self.character_b_combo.blockSignals(False)
        logger.debug("Character combos populated.")

    def populate_scene_combos(self):
        regions = sorted(self.context_builder.get_regions())
        self.scene_region_combo.blockSignals(True)
        self.scene_sub_location_combo.blockSignals(True)
        self.scene_region_combo.clear()
        self.scene_region_combo.addItem("(Aucune)") 
        self.scene_region_combo.addItems(regions)
        self.scene_region_combo.blockSignals(False)
        self.scene_sub_location_combo.blockSignals(False)
        self._on_scene_region_changed(self.scene_region_combo.currentText() or "(Aucune)")
        logger.debug("Scene region combo populated.")

    @Slot(str)
    def _on_scene_region_changed(self, region_name: str):
        self.scene_sub_location_combo.clear()
        if region_name and region_name != "(Aucun)" and region_name != "(Sélectionner une région)":
            try:
                # sub_locations = sorted(self.context_builder.get_sub_locations_for_region(region_name))
                sub_locations = sorted(self.context_builder.get_sub_locations(region_name))
                if not sub_locations:
                    logger.info(f"Aucun sous-lieu trouvé pour la région : {region_name}")
                    self.scene_sub_location_combo.addItem("(Aucun sous-lieu)")
                else:
                    self.scene_sub_location_combo.addItems(["(Tous / Non spécifié)"] + sub_locations)
                    self.scene_sub_location_combo.setEnabled(True)
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des sous-lieux pour la région {region_name}: {e}", exc_info=True)
                self.scene_sub_location_combo.addItem("(Erreur de chargement des sous-lieux)")
                self.scene_sub_location_combo.setEnabled(False)
        else:
            self.scene_sub_location_combo.addItem("(Sélectionner une région d'abord)")
            self.scene_sub_location_combo.setEnabled(False)
        self._schedule_settings_save_and_token_update()
        logger.debug(f"Sub-location combo updated for region: {region_name}")

    def _swap_characters(self):
        current_a_index = self.character_a_combo.currentIndex()
        current_b_index = self.character_b_combo.currentIndex()
        self.character_a_combo.setCurrentIndex(current_b_index)
        self.character_b_combo.setCurrentIndex(current_a_index)
        logger.debug("Characters A and B swapped.")
        self._schedule_settings_save_and_token_update()

    @Slot()
    def _schedule_settings_save_and_token_update(self):
        self.settings_changed.emit()
        self._trigger_token_update()

    @Slot()
    def _schedule_settings_save(self):
        self.settings_changed.emit()

    @Slot()
    def _trigger_token_update(self):
        self.update_token_estimation_signal.emit()
        logger.debug("Token update triggered.")

    @Slot()
    def update_token_estimation_ui(self):
        if not self.prompt_engine or not self.context_builder or not self.llm_client:
            self.token_estimation_label.setText("Erreur: Moteurs non initialisés")
            # Aussi mettre à jour l'onglet du prompt pour indiquer l'erreur
            self._display_prompt_in_tab("Erreur: Les moteurs (prompt, context, llm) ne sont pas tous initialisés.")
            return

        user_specific_goal = self.user_instructions_textedit.toPlainText()
        selected_elements_for_context = {}
        if hasattr(self.main_window_ref, '_get_current_context_selections'):
            selected_elements_for_context = self.main_window_ref._get_current_context_selections()
        else:
            logger.warning("MainWindow n'a pas la méthode '_get_current_context_selections'. Le contexte sera limité.")
            # Fallback pour construction locale (moins complet)
            char_a = self.character_a_combo.currentText() if self.character_a_combo.currentText() != "(Aucun)" else None
            char_b = self.character_b_combo.currentText() if self.character_b_combo.currentText() != "(Aucun)" else None
            scene_region = self.scene_region_combo.currentText() if self.scene_region_combo.currentText() != "(Aucune)" else None
            scene_sub = self.scene_sub_location_combo.currentText() if self.scene_sub_location_combo.currentText() not in ["(Tous / Non spécifié)", "(Aucun sous-lieu)", "(Sélectionner une région d'abord)"] else None
            local_selection = {}
            if char_a: local_selection.setdefault("Personnages", []).append(char_a)
            if char_b: local_selection.setdefault("Personnages", []).append(char_b)
            if scene_region: local_selection.setdefault("Lieux", []).append(scene_region)
            if scene_sub: local_selection.setdefault("Lieux", []).append(scene_sub)
            selected_elements_for_context = local_selection
            
        context_summary = ""
        full_prompt = "Erreur lors de la construction du contexte ou du prompt." # Message par défaut
        context_tokens = 0
        prompt_tokens = 0
        
        try:
            context_summary = self.context_builder.build_context(
                selected_elements=selected_elements_for_context,
                scene_instruction=user_specific_goal
            )
            full_prompt, prompt_tokens = self.prompt_engine.build_prompt(context_summary, user_specific_goal)
            context_tokens = self.prompt_engine._count_tokens(context_summary) # Utiliser _count_tokens
        except Exception as e:
            logger.error(f"Erreur pendant la construction du prompt dans update_token_estimation_ui: {e}", exc_info=True)
            full_prompt = f"Erreur lors de la génération du prompt estimé:\\n{type(e).__name__}: {e}"
            # Les tokens resteront à 0 ou à leur dernière valeur valide avant l'erreur

        self.token_estimation_label.setText(f"Tokens (contexte/prompt): {context_tokens} / {prompt_tokens}")
        logger.debug(f"Token estimation UI updated: Context {context_tokens}, Prompt {prompt_tokens}.")
        
        # Mettre à jour l'onglet "Prompt Estimé" avec le prompt complet calculé
        self._display_prompt_in_tab(full_prompt)


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
        generation_succeeded = False
        try:
            logger.info("Coroutine _on_generate_dialogue_button_clicked_local démarrée.")
            k_variants = int(self.k_variants_combo.currentText())
            
            user_specific_goal = self.user_instructions_textedit.toPlainText()
            selected_elements_for_context = {}
            if hasattr(self.main_window_ref, '_get_current_context_selections'):
                selected_elements_for_context = self.main_window_ref._get_current_context_selections()
            else:
                logger.warning("MainWindow n'a pas _get_current_context_selections, fallback sur contexte local GenerationPanel.")
                char_a_name_local = self.character_a_combo.currentText() if self.character_a_combo.currentText() != "(Aucun)" else None
                char_b_name_local = self.character_b_combo.currentText() if self.character_b_combo.currentText() != "(Aucun)" else None
                scene_name_local = self.scene_region_combo.currentText() if self.scene_region_combo.currentText() != "(Aucune)" else None
                sub_location_name_local = self.scene_sub_location_combo.currentText() if self.scene_sub_location_combo.currentText() not in ["(Tous / Non spécifié)", "(Aucun sous-lieu)", "(Sélectionner une région d'abord)"] else None
                
                # Construire une scene_instruction plus riche si les éléments principaux sont définis
                # pour aider ContextBuilder si besoin.
                # Note: user_specific_goal (l'instruction utilisateur) sera ajoutée par PromptEngine.
                # Ici, on construit une "scene_instruction" de base pour ContextBuilder.
                # Cette partie est laissée telle quelle car build_context prend selected_elements et scene_instruction.
                # Le ContextBuilder devra utiliser ces deux sources.
                
                current_scene_instruction_parts = []
                if char_a_name_local: current_scene_instruction_parts.append(f"Personnage A: {char_a_name_local}")
                if char_b_name_local: current_scene_instruction_parts.append(f"Personnage B: {char_b_name_local}")
                if scene_name_local: current_scene_instruction_parts.append(f"Scène: {scene_name_local}")
                if sub_location_name_local: current_scene_instruction_parts.append(f"Sous-lieu: {sub_location_name_local}")
                
                effective_scene_instruction_for_context = ". ".join(current_scene_instruction_parts)
                if user_specific_goal: # On pourrait fusionner ici, mais build_context prend déjà scene_instruction
                    # effective_scene_instruction_for_context += ". Objectif: " + user_specific_goal
                    pass


                local_sel = {}
                if char_a_name_local: local_sel.setdefault("Personnages", []).append(char_a_name_local)
                if char_b_name_local: local_sel.setdefault("Personnages", []).append(char_b_name_local)
                if scene_name_local: local_sel.setdefault("Lieux", []).append(scene_name_local)
                if sub_location_name_local: local_sel.setdefault("Lieux", []).append(sub_location_name_local)
                selected_elements_for_context = {**selected_elements_for_context, **local_sel} # fusionner


            context_summary = self.context_builder.build_context(
                selected_elements=selected_elements_for_context,
                scene_instruction=user_specific_goal # Ou effective_scene_instruction_for_context ? À clarifier. Pour l'instant, on garde user_specific_goal pour cohérence avec l'appel dans update_token_estimation_ui
                # Les arguments main_characters, main_location, sub_location ont été supprimés
            )
            full_prompt, _ = self.prompt_engine.build_prompt(context_summary, user_specific_goal)
            logger.info(f"Appel de _display_prompt_in_tab avec le prompt de longueur: {len(full_prompt)} chars.")
            self._display_prompt_in_tab(full_prompt) 

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
            
            self.variant_display_tabs.blockSignals(True)
            num_tabs_to_keep = 0
            if self.variant_display_tabs.count() > 0 and self.variant_display_tabs.tabText(0) == "Prompt Estimé":
                num_tabs_to_keep = 1
            
            while self.variant_display_tabs.count() > num_tabs_to_keep:
                self.variant_display_tabs.removeTab(num_tabs_to_keep)
            
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
                    
                    self.variant_display_tabs.addTab(variant_tab_content_widget, f"Variante {i+1}")
                generation_succeeded = True
                logger.info(f"{len(variants)} variantes affichées.")
            else:
                logger.warning("Aucune variante reçue du LLM ou variants est None/vide.")
                error_tab = QTextEdit("Aucune variante n'a été générée par le LLM ou une erreur s'est produite.")
                error_tab.setReadOnly(True)
                self.variant_display_tabs.addTab(error_tab, "Erreur Génération")
            
            self.variant_display_tabs.blockSignals(False)

        except asyncio.CancelledError:
            logger.warning("La tâche de génération de dialogue a été annulée.")
            return 
        except Exception as e:
            logger.error(f"Erreur majeure lors de la génération des dialogues: {e}", exc_info=True)
            self.variant_display_tabs.blockSignals(True)
            num_tabs_to_keep_err = 0
            if self.variant_display_tabs.count() > 0 and self.variant_display_tabs.tabText(0) == "Prompt Estimé":
                num_tabs_to_keep_err = 1
            while self.variant_display_tabs.count() > num_tabs_to_keep_err:
                self.variant_display_tabs.removeTab(num_tabs_to_keep_err)
            
            error_tab_content = QTextEdit()
            error_tab_content.setPlainText(f"Une erreur majeure est survenue lors de la génération:\n\n{type(e).__name__}: {e}")
            error_tab_content.setReadOnly(True)
            self.variant_display_tabs.addTab(error_tab_content, "Erreur Critique")
            self.variant_display_tabs.blockSignals(False)
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
        self.variant_display_tabs.blockSignals(True)
        
        prompt_tab_index = -1
        for i in range(self.variant_display_tabs.count()):
            if self.variant_display_tabs.tabText(i) == "Prompt Estimé":
                prompt_tab_index = i
                break
        
        if prompt_tab_index != -1:
            logger.info(f"_display_prompt_in_tab: Onglet 'Prompt Estimé' trouvé à l'index {prompt_tab_index}. Mise à jour du contenu.")
            # Onglet existant, mettre à jour son contenu
            widget = self.variant_display_tabs.widget(prompt_tab_index)
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
            self.variant_display_tabs.insertTab(0, prompt_tab_widget, "Prompt Estimé")
        
        logger.info("_display_prompt_in_tab: Appel de setCurrentIndex(0).")
        self.variant_display_tabs.setCurrentIndex(0) 
        self.variant_display_tabs.blockSignals(False)
        logger.info("_display_prompt_in_tab: Sortie.")

    @Slot(int)
    def _on_validate_variant_clicked(self, variant_index: int):
        actual_tab_index = -1
        expected_tab_name = f"Variante {variant_index + 1}"
        for i in range(self.variant_display_tabs.count()):
            if self.variant_display_tabs.tabText(i) == expected_tab_name:
                actual_tab_index = i
                break

        if actual_tab_index == -1:
            logger.error(f"Onglet pour la variante {variant_index + 1} non trouvé.")
            self.main_window_ref.statusBar().showMessage(f"Erreur: Onglet pour variante {variant_index + 1} non trouvé.", 5000)
            return

        tab_content_widget = self.variant_display_tabs.widget(actual_tab_index)
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
        char_a_name = self.character_a_combo.currentText() if self.character_a_combo.currentText() != "(Aucun)" else "PersonnageA"
        char_b_name = self.character_b_combo.currentText() if self.character_b_combo.currentText() != "(Aucun)" else "PersonnageB"
        scene_name = self.scene_region_combo.currentText() if self.scene_region_combo.currentText() != "(Aucune)" else "LieuIndéfini"
        
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
        char_a_raw = self.character_a_combo.currentText()
        char_b_raw = self.character_b_combo.currentText()
        scene_region_raw = self.scene_region_combo.currentText()
        scene_sub_location_raw = self.scene_sub_location_combo.currentText()

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
        char_a_raw = self.character_a_combo.currentText()
        char_b_raw = self.character_b_combo.currentText()
        scene_region_raw = self.scene_region_combo.currentText()
        scene_sub_location_raw = self.scene_sub_location_combo.currentText()

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
        settings = {
            "character_a": self.character_a_combo.currentText(),
            "character_b": self.character_b_combo.currentText(),
            "scene_region": self.scene_region_combo.currentText(),
            "scene_sub_location": self.scene_sub_location_combo.currentText(),
            "k_variants": self.k_variants_combo.currentText(),
            "user_instructions": self.user_instructions_textedit.toPlainText(),
            "llm_model_identifier": self.llm_model_combo.currentData() if self.llm_model_combo.count() > 0 and self.llm_model_combo.currentData() != "dummy_error" else self.current_llm_model_identifier,
            "structured_output_checked": self.structured_output_checkbox.isChecked(),
        }
        logger.debug(f"GenerationPanel settings to be saved: {settings}")
        return settings

    def load_settings(self, settings: dict):
        logger.debug(f"Loading GenerationPanel settings: {settings}")
        
        # Block signals to prevent premature updates
        blocked_widgets = [
            self.character_a_combo, self.character_b_combo, 
            self.scene_region_combo, self.scene_sub_location_combo,
            self.k_variants_combo, self.user_instructions_textedit,
            self.llm_model_combo, self.structured_output_checkbox
        ]
        for widget in blocked_widgets: widget.blockSignals(True)

        # Ensure combos are populated before setting values
        if self.character_a_combo.count() == 0: self.populate_character_combos() 
        if self.scene_region_combo.count() == 0: self.populate_scene_combos()
        if self.llm_model_combo.count() == 0: self.populate_llm_model_combo()

        self.character_a_combo.setCurrentText(settings.get("character_a", "(Aucun)"))
        self.character_b_combo.setCurrentText(settings.get("character_b", "(Aucun)"))
        
        saved_region = settings.get("scene_region", "(Aucune)")
        self.scene_region_combo.setCurrentText(saved_region)
        # Trigger _on_scene_region_changed manually AFTER scene_region_combo is unblocked
        # to populate sub-locations and then set the sub-location.
        
        self.k_variants_combo.setCurrentText(settings.get("k_variants", "2"))
        self.user_instructions_textedit.setPlainText(settings.get("user_instructions", ""))
        
        saved_model_id = settings.get("llm_model_identifier")
        if saved_model_id:
            self.select_model_in_combo(saved_model_id) 
        
        self.structured_output_checkbox.setChecked(settings.get("structured_output_checked", True))

        # Unblock signals
        for widget in blocked_widgets: widget.blockSignals(False)

        # Manually trigger updates that depend on loaded values AFTER signals are unblocked
        self._on_scene_region_changed(self.scene_region_combo.currentText()) # Populate sub-locations
        # Set sub-location only after its combo is populated
        if "scene_sub_location" in settings:
             self.scene_sub_location_combo.setCurrentText(settings.get("scene_sub_location", "(Tous / Non spécifié)"))

        self._trigger_token_update() 
        self._update_structured_output_checkbox_state() 
        logger.info("GenerationPanel settings loaded.")