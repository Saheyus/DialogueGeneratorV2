import logging
from PySide6.QtCore import QObject, Signal
from typing import TYPE_CHECKING, Optional

from constants import UIText, Defaults

if TYPE_CHECKING:
    from services.dialogue_generation_service import DialogueGenerationService
    from ui.generation_panel.instructions_widget import InstructionsWidget
    from ui.generation_panel.scene_selection_widget import SceneSelectionWidget
    from ui.main_window import MainWindow # For type hinting main_window_ref

logger = logging.getLogger(__name__)

class TokenEstimationHandler(QObject):
    estimation_ready = Signal(str, int)  # prompt_text, estimated_tokens
    estimation_failed = Signal(str)     # error_message

    def __init__(self,
                 dialogue_generation_service: 'DialogueGenerationService',
                 instructions_widget: 'InstructionsWidget',
                 scene_selection_widget: 'SceneSelectionWidget',
                 main_window_ref: 'MainWindow', # Used for _get_current_context_selections & config_service
                 parent: Optional[QObject] = None):
        super().__init__(parent)
        self.dialogue_generation_service = dialogue_generation_service
        self.instructions_widget = instructions_widget
        self.scene_selection_widget = scene_selection_widget
        self.main_window_ref = main_window_ref

    def request_token_estimation(self):
        logger.debug("TokenEstimationHandler: Demande d'estimation de tokens reçue.")
        if not self.dialogue_generation_service:
            logger.error("TokenEstimationHandler: DialogueGenerationService non initialisé.")
            self.estimation_failed.emit("Erreur: DialogueGenerationService non initialisé.")
            return

        try:
            user_specific_goal = self.instructions_widget.get_user_instructions_text()
            selected_context_items = self.main_window_ref._get_current_context_selections() if hasattr(self.main_window_ref, '_get_current_context_selections') else {}

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

            context_selections_for_service = selected_context_items.copy()
            context_selections_for_service["_scene_protagonists"] = scene_protagonists_dict
            context_selections_for_service["_scene_location"] = scene_location_dict
            context_selections_for_service["generate_interaction"] = True # Pour estimer le pire cas (structuré)

            max_tokens_val = self.main_window_ref.config_service.get_ui_setting("max_context_tokens", Defaults.CONTEXT_TOKENS)
            system_prompt_override = self.instructions_widget.get_system_prompt_text()

            full_prompt_for_estimation, prompt_tokens, _ = self.dialogue_generation_service.prepare_generation_preview(
                user_instructions=user_specific_goal,
                system_prompt_override=system_prompt_override,
                context_selections=context_selections_for_service,
                max_context_tokens=max_tokens_val,
                structured_output=True # Estimer pour un output structuré par défaut
            )

            if not full_prompt_for_estimation:
                full_prompt_for_estimation = "Erreur: Le service n'a pas pu construire le prompt pour l'estimation."

            logger.debug(f"TokenEstimationHandler: Estimation prête. Tokens: {prompt_tokens}")
            self.estimation_ready.emit(full_prompt_for_estimation, prompt_tokens)

        except Exception as e:
            logger.error(f"TokenEstimationHandler: Erreur lors de l'estimation des tokens: {e}", exc_info=True)
            error_message = f"Erreur lors de la préparation de la prévisualisation: {type(e).__name__}: {e}"
            self.estimation_failed.emit(error_message) 