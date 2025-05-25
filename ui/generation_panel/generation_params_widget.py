from PySide6.QtWidgets import (QWidget, QGroupBox, QGridLayout, QLabel, QComboBox, QCheckBox, QDoubleSpinBox, QVBoxLayout)
from PySide6.QtCore import Signal, Qt
import logging
from llm_client import DummyLLMClient # Nouvel import direct
from constants import UIText, FilePaths, Defaults

logger = logging.getLogger(__name__)

class AlwaysTrueCheckbox:
    def isChecked(self):
        return True

class GenerationParamsWidget(QWidget):
    llm_model_selection_changed = Signal(str) # identifier
    k_variants_changed = Signal(str)
    max_context_tokens_changed = Signal(float) # k_tokens
    structured_output_changed = Signal(bool)
    settings_changed = Signal() # Generic signal for any setting change

    def __init__(self, available_llm_models, current_llm_model_identifier, parent=None):
        super().__init__(parent)
        self.available_llm_models = available_llm_models if available_llm_models else []
        self.current_llm_model_identifier = current_llm_model_identifier
        self._is_loading_settings = False
        self.structured_output_checkbox = AlwaysTrueCheckbox()
        self._init_ui()
        self.populate_llm_model_combo()

    def _init_ui(self):
        self.group_box = QGroupBox("Options LLM", self)
        self.main_layout = QVBoxLayout(self.group_box)
        
        row = 0
        layout = QGridLayout()
        layout.addWidget(QLabel("Modèle LLM:"), row, 0)
        self.llm_model_combo = QComboBox()
        self.llm_model_combo.setToolTip("Choisissez le modèle de langage à utiliser pour la génération.")
        self.llm_model_combo.currentTextChanged.connect(self._on_llm_model_combo_changed)
        layout.addWidget(self.llm_model_combo, row, 1)
        row += 1

        layout.addWidget(QLabel("Nombre de Variantes (k):"), row, 0)
        self.k_variants_combo = QComboBox()
        self.k_variants_combo.addItems([str(i) for i in range(1, 6)])
        self.k_variants_combo.setCurrentText("1")
        self.k_variants_combo.setToolTip("Nombre de dialogues alternatifs à générer.")
        self.k_variants_combo.currentTextChanged.connect(self._on_k_variants_changed)
        layout.addWidget(self.k_variants_combo, row, 1)
        row += 1

        layout.addWidget(QLabel("Limite de tokens (contexte GDD):"), row, 0)
        self.max_context_tokens_spinbox = QDoubleSpinBox()
        self.max_context_tokens_spinbox.setMinimum(0.5)
        self.max_context_tokens_spinbox.setMaximum(1000)
        self.max_context_tokens_spinbox.setSingleStep(0.5)
        self.max_context_tokens_spinbox.setValue(5.0)
        self.max_context_tokens_spinbox.setSuffix("k")
        self.max_context_tokens_spinbox.setDecimals(1)
        self.max_context_tokens_spinbox.setToolTip("Nombre maximum de tokens à utiliser pour le contexte GDD en milliers (k).")
        self.max_context_tokens_spinbox.valueChanged.connect(self._on_max_context_tokens_spinbox_changed)
        layout.addWidget(self.max_context_tokens_spinbox, row, 1)
        row += 1

        # self.structured_output_checkbox = QCheckBox("Utiliser Sortie Structurée (JSON)")
        # self.structured_output_checkbox.setToolTip("Si coché, demande au LLM de formater la sortie en JSON.")
        # self.structured_output_checkbox.setChecked(True)
        # self.structured_output_checkbox.stateChanged.connect(self._on_structured_output_changed)
        # layout.addWidget(self.structured_output_checkbox, row, 0, 1, 2)
        
        self.main_layout.addLayout(layout)

        # Correction : ajouter le group_box au layout principal du widget
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.group_box)

    def populate_llm_model_combo(self):
        self.llm_model_combo.blockSignals(True)
        self.llm_model_combo.clear()
        found_current_model = False

        if not self.available_llm_models:
            logger.warning(UIText.NO_MODEL_CONFIGURED)
            self.llm_model_combo.addItem(UIText.NO_MODEL_CONFIGURED, userData="dummy_error")
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
            logger.warning(f"Modèle LLM actuel '{self.current_llm_model_identifier}' non trouvé. Sélection du premier.")
            self.llm_model_combo.setCurrentIndex(0)
            self.current_llm_model_identifier = self.llm_model_combo.currentData()
            # Emit signal if changed due to not found
            self.llm_model_selection_changed.emit(self.current_llm_model_identifier)
            
        self.llm_model_combo.setEnabled(self.llm_model_combo.count() > 0 and self.llm_model_combo.itemData(0) != "dummy_error")
        self.llm_model_combo.blockSignals(False)

    def _on_llm_model_combo_changed(self, text_model_display_name: str):
        selected_identifier = self.llm_model_combo.currentData()
        if selected_identifier and selected_identifier != self.current_llm_model_identifier and selected_identifier != "dummy_error":
            logger.info(f"Sélection du modèle LLM changée pour : {selected_identifier} ({text_model_display_name})")
            self.current_llm_model_identifier = selected_identifier
            self.llm_model_selection_changed.emit(selected_identifier)
            if not self._is_loading_settings: self.settings_changed.emit()

    def _on_k_variants_changed(self, value: str):
        self.k_variants_changed.emit(value)
        if not self._is_loading_settings: self.settings_changed.emit()

    def _on_max_context_tokens_spinbox_changed(self, value: float):
        self.max_context_tokens_changed.emit(value)
        if not self._is_loading_settings: self.settings_changed.emit()
        
    def _on_structured_output_changed(self, state: int): # state is Qt.CheckState enum
        is_checked = (state == Qt.CheckState.Checked.value)
        self.structured_output_changed.emit(is_checked)
        if not self._is_loading_settings: self.settings_changed.emit()

    def update_llm_client_dependent_state(self, llm_client, current_llm_model_properties):
        # Placeholder for logic similar to _update_structured_output_checkbox_state in GenerationPanel
        # This might involve enabling/disabling structured_output_checkbox based on llm_client type or model properties
        is_dummy = isinstance(llm_client, DummyLLMClient)
        
        if is_dummy:
            if not hasattr(self, '_was_structured_output_checked_before_dummy'):
                self._was_structured_output_checked_before_dummy = self.structured_output_checkbox.isChecked()
            self.structured_output_checkbox.setChecked(False)
            self.structured_output_checkbox.setEnabled(False)
            self.structured_output_checkbox.setToolTip("La sortie structurée n'est pas applicable avec DummyLLMClient.")
        else:
            self.structured_output_checkbox.setEnabled(True)
            if hasattr(self, '_was_structured_output_checked_before_dummy'):
                self.structured_output_checkbox.setChecked(self._was_structured_output_checked_before_dummy)
                del self._was_structured_output_checked_before_dummy
            
            if current_llm_model_properties and current_llm_model_properties.get("supports_json_mode", False):
                self.structured_output_checkbox.setToolTip("Si coché, demande au LLM de formater la sortie en JSON (modèle compatible).")
            else:
                self.structured_output_checkbox.setToolTip("Si coché, demande au LLM de formater la sortie en JSON. La compatibilité du modèle actuel n'est pas garantie.")
        logger.debug(f"GenerationParamsWidget: structured_output_checkbox updated. Enabled: {self.structured_output_checkbox.isEnabled()}, Checked: {self.structured_output_checkbox.isChecked()}")


    def get_settings(self) -> dict:
        return {
            "llm_model": self.llm_model_combo.currentData(),
            "k_variants": self.k_variants_combo.currentText(),
            "max_context_tokens": self.max_context_tokens_spinbox.value(), # k_tokens
            "structured_output": self.structured_output_checkbox.isChecked()
        }

    def load_settings(self, settings: dict, default_k_variants="1", default_max_context_tokens_k=5.0, default_structured_output=True):
        self._is_loading_settings = True
        
        model_identifier = settings.get("llm_model")
        if model_identifier:
            self.select_model_in_combo(model_identifier)
        elif self.llm_model_combo.count() > 0: # Select first if no setting
            self.llm_model_combo.setCurrentIndex(0)
            self.current_llm_model_identifier = self.llm_model_combo.currentData()

        self.k_variants_combo.setCurrentText(settings.get("k_variants", default_k_variants))
        
        # Note: max_context_tokens is stored as k_tokens (float) in settings by GenerationPanel
        self.max_context_tokens_spinbox.setValue(settings.get("max_context_tokens", default_max_context_tokens_k))
        
        self.structured_output_checkbox.setChecked(settings.get("structured_output", default_structured_output))
        
        self._is_loading_settings = False
        
    def select_model_in_combo(self, model_identifier: str):
        self.llm_model_combo.blockSignals(True)
        found = False
        for i in range(self.llm_model_combo.count()):
            if self.llm_model_combo.itemData(i) == model_identifier:
                self.llm_model_combo.setCurrentIndex(i)
                self.current_llm_model_identifier = model_identifier # Ensure this is updated
                logger.debug(f"Modèle '{model_identifier}' sélectionné programmatiquement dans ComboBox LLM.")
                found = True
                break
        if not found and self.llm_model_combo.count() > 0 and self.llm_model_combo.itemData(0) != "dummy_error":
            logger.warning(f"Tentative de sélection du modèle '{model_identifier}' mais non trouvé. Le premier sera sélectionné.")
            # self.llm_model_combo.setCurrentIndex(0) # This might be too aggressive if a valid model was previously selected.
            # self.current_llm_model_identifier = self.llm_model_combo.currentData()
            # self.llm_model_selection_changed.emit(self.current_llm_model_identifier) # Emit if it truly changes to default
        self.llm_model_combo.blockSignals(False) 