import asyncio
import logging
from PySide6.QtCore import QObject, Signal
from typing import List, Dict, Any, Optional

from models.dialogue_structure.interaction import Interaction
from models.dialogue_structure.dynamic_interaction_schema import build_interaction_model_from_structure, validate_interaction_elements_order, convert_dynamic_to_standard_interaction
from services.dialogue_generation_service import DialogueGenerationService
from llm_client import ILLMClient # Correction de l'import
from constants import UIText

logger = logging.getLogger(__name__)

class DialogueGenerationHandler(QObject):
    generation_started = Signal()
    # variants_objects, full_prompt_for_display, estimated_tokens_for_display
    generation_succeeded = Signal(list, str, int)
    # error_message, full_prompt_for_display (peut être None)
    generation_failed = Signal(str, str)
    # For updating the prompt tab and token count before/during generation if needed
    # prompt_text, estimated_tokens
    prompt_preview_ready = Signal(str, int) 

    def __init__(self, 
                 llm_client: ILLMClient, 
                 dialogue_generation_service: DialogueGenerationService,
                 parent: Optional[QObject] = None):
        super().__init__(parent)
        self.llm_client = llm_client
        self.dialogue_generation_service = dialogue_generation_service

    async def generate_dialogue_async(self,
                                      k_variants: int,
                                      user_instructions: str,
                                      system_prompt_override: str,
                                      context_selections_for_service: Dict[str, Any], # Contient GDD items, _scene_protagonists, _scene_location
                                      dialogue_structure_description: str,
                                      dialogue_structure_elements: List[str],
                                      max_context_tokens_val: int,
                                      current_llm_model_identifier: str
                                     ):
        logger.info("DialogueGenerationHandler: Début de la génération de dialogue asynchrone.")
        self.generation_started.emit()

        full_prompt_for_display = "Erreur: Le prompt n'a pas pu être construit."
        estimated_tokens_for_display = 0
        variants_objects = []

        try:
            target_response_model_pydantic = build_interaction_model_from_structure(dialogue_structure_elements)
            
            logger.info(f"Handler: Appel de dialogue_generation_service.generate_structured_object_variants avec k={k_variants}...")
            logger.info(f"Handler: Modèle Pydantic dynamique pour la structure: {dialogue_structure_elements}")
            logger.info(f"Handler: Schéma du modèle: {target_response_model_pydantic.model_json_schema()}")

            variants_objects, full_prompt_from_service, estimated_tokens_from_service = \
                await self.dialogue_generation_service.generate_structured_object_variants(
                    llm_client=self.llm_client,
                    k_variants=k_variants,
                    max_context_tokens_for_context_builder=max_context_tokens_val,
                    user_instructions=user_instructions,
                    system_prompt_override=system_prompt_override,
                    context_selections=context_selections_for_service,
                    dialogue_structure_description=dialogue_structure_description,
                    target_response_model=target_response_model_pydantic,
                    current_llm_model_identifier=current_llm_model_identifier
                )
            
            full_prompt_for_display = full_prompt_from_service
            estimated_tokens_for_display = estimated_tokens_from_service

            if not full_prompt_for_display:
                full_prompt_for_display = "Erreur: Le prompt n'a pas pu être construit par le service."
            
            self.prompt_preview_ready.emit(full_prompt_for_display, estimated_tokens_for_display)

            if variants_objects:
                logger.info(f"Handler: {len(variants_objects)} variantes (objets) générées par le service.")
                # La conversion et la validation de structure se feront dans le slot connecté à generation_succeeded
                # pour ne pas surcharger le handler avec la logique UI.
                # Cependant, une validation minimale de l'ordre peut être faite ici si c'est critique.
                processed_variants = []
                for i, variant_data_obj in enumerate(variants_objects):
                    if isinstance(variant_data_obj, Interaction) or (hasattr(variant_data_obj, '__class__') and 'DynamicInteraction' in str(type(variant_data_obj))):
                        is_valid_order = validate_interaction_elements_order(variant_data_obj, dialogue_structure_elements)
                        if not is_valid_order:
                            logger.error(f"[VALIDATION STRUCTURE HANDLER] Variante {i+1} (objet) ne respecte pas l'ordre: {dialogue_structure_elements}")
                            # On pourrait émettre un signal d'erreur partiel ici ou la remplacer par un objet d'erreur
                            error_placeholder = Interaction(
                                interaction_id=f"error_order_{i+1}",
                                title=f"Erreur Structure Variante {i+1}",
                                elements=[{"element_type": "error", "text": f"La variante générée ne respecte pas l'ordre des éléments: {dialogue_structure_elements}"}]
                            )
                            processed_variants.append(error_placeholder)
                            continue
                        
                        try:
                            standard_interaction = convert_dynamic_to_standard_interaction(variant_data_obj)
                            processed_variants.append(standard_interaction)
                        except ValueError as ve:
                            logger.error(f"Erreur de conversion de DynamicInteraction (objet) en Interaction: {ve}", exc_info=True)
                            error_placeholder_conv = Interaction(
                                interaction_id=f"error_conversion_{i+1}",
                                title=f"Erreur Conversion Variante {i+1}",
                                elements=[{"element_type": "error", "text": f"Erreur de conversion: {ve}"}]
                            )
                            processed_variants.append(error_placeholder_conv)
                            continue
                    elif isinstance(variant_data_obj, str):
                         logger.warning(f"Handler: Variante {i+1} est une chaîne (str), inattendu. Création d'un objet Interaction d'erreur.")
                         error_placeholder_str = Interaction(
                            interaction_id=f"error_str_variant_{i+1}",
                            title=f"Erreur Type Variante {i+1}",
                            elements=[{"element_type": "error", "text": f"Variante de type str inattendue: {variant_data_obj[:100]}..."}]
                         )
                         processed_variants.append(error_placeholder_str)
                    else:
                        logger.warning(f"Handler: Variante {i+1} type inattendu {type(variant_data_obj)}. Création d'un objet Interaction d'erreur.")
                        error_placeholder_unknown = Interaction(
                            interaction_id=f"error_unknown_type_{i+1}",
                            title=f"Erreur Type Inconnu Variante {i+1}",
                            elements=[{"element_type": "error", "text": f"Type de variante inattendu: {type(variant_data_obj)}"}]
                        )
                        processed_variants.append(error_placeholder_unknown)

                self.generation_succeeded.emit(processed_variants, full_prompt_for_display, estimated_tokens_for_display)
            else:
                logger.warning("Handler: Aucune variante (objet) reçue du service ou variants_objects est None/vide.")
                self.generation_succeeded.emit([], full_prompt_for_display, estimated_tokens_for_display) # Émettre avec liste vide

        except asyncio.CancelledError:
            logger.warning("Handler: La tâche de génération de dialogue a été annulée.")
            # Ne pas émettre generation_failed ici, car c'est une annulation, pas une erreur.
            # Le contrôleur (GenerationPanel) devrait gérer l'état de l'UI en conséquence.
            # On peut émettre le prompt s'il a été construit.
            if full_prompt_for_display and full_prompt_for_display != "Erreur: Le prompt n'a pas pu être construit.":
                self.prompt_preview_ready.emit(full_prompt_for_display, estimated_tokens_for_display)
            return # Important de retourner pour que le finally ne s'exécute pas comme une erreur
            
        except Exception as e:
            logger.error(f"Handler: Erreur majeure lors de la génération des dialogues: {e}", exc_info=True)
            error_message = f"{type(e).__name__}: {e}"
            # Tenter d'émettre le prompt même en cas d'erreur s'il a été partiellement construit
            if full_prompt_for_display and full_prompt_for_display != "Erreur: Le prompt n'a pas pu être construit.":
                 self.prompt_preview_ready.emit(full_prompt_for_display, estimated_tokens_for_display)
            self.generation_failed.emit(error_message, full_prompt_for_display)
        # finally:
            # Le finally dans GenerationPanel s'occupera de réactiver le bouton etc.
            # Le handler n'a pas à connaître l'état de l'UI.
            # logger.debug("Handler: Fin de la méthode generate_dialogue_async.")
            pass 