from typing import List, Type, Optional, Dict, Any
from pydantic import BaseModel, Field, create_model
import logging
from .dialogue_elements import DialogueLineElement, PlayerChoicesBlockElement

logger = logging.getLogger(__name__)

STRUCTURE_TYPE_MAP = {
    "PNJ": {"type": DialogueLineElement, "description": "Une ligne de dialogue dite par un personnage non-joueur (PNJ). Doit contenir le nom du locuteur et le texte du dialogue."},
    "PJ": {"type": PlayerChoicesBlockElement, "description": "Un bloc de choix pour le joueur. Doit contenir une liste d'au moins deux options de dialogue/action pour le joueur."}
}

def build_interaction_model_from_structure(structure: List[str]) -> Type[BaseModel]:
    fields: Dict[str, Any] = {
        "interaction_id": (str, Field(..., description="Identifiant unique de l'interaction, généralement un UUID.")),
        "title": (str, Field(..., description="Titre descriptif et concis de l'interaction ou de la scène.")),
        "header_tags": (List[str], Field(default_factory=list, description="Liste de mots-clés ou tags pour catégoriser l'interaction (ex: ['quête', 'combat', 'humour']).")),
        "next_interaction_id_if_no_choices": (Optional[str], Field(default=None, description="Optionnel. ID de l'interaction suivante si celle-ci se termine sans que le joueur ait fait de choix (rare). Laissez null la plupart du temps."))
    }
    
    model_name_parts = []
    for i, element_type_label in enumerate(filter(None, structure)):
        element_config = STRUCTURE_TYPE_MAP.get(element_type_label)
        if element_config:
            element_actual_type = element_config["type"]
            element_description = element_config["description"]
            fields[f"phase_{i+1}"] = (element_actual_type, Field(..., description=f"Phase {i+1} ({element_type_label}): {element_description}"))
            model_name_parts.append(element_type_label)
        elif element_type_label != "Stop":
            logger.warning(f"Type d'élément inconnu ou non mappé '{element_type_label}' dans la structure, il sera ignoré.")

    dynamic_model_name = f"DynamicInteraction_{'_'.join(model_name_parts)}_{len(fields)}"
    model_type = create_model(dynamic_model_name, **fields, __base__=BaseModel)
    return model_type

def get_json_schema_for_model(model_type: Type[BaseModel]) -> Dict[str, Any]:
    logger.debug(f"Génération du JSON Schema pour le modèle: {model_type.__name__}")
    return model_type.model_json_schema()

def validate_interaction_elements_order(interaction_instance: BaseModel, expected_structure: List[str]) -> bool:
    actual_elements = []
    i = 1
    while True:
        field_name = f"phase_{i}"
        if hasattr(interaction_instance, field_name):
            element = getattr(interaction_instance, field_name)
            if isinstance(element, DialogueLineElement):
                actual_elements.append("PNJ")
            elif isinstance(element, PlayerChoicesBlockElement):
                actual_elements.append("PJ")
            else:
                logger.warning(f"Type d'élément inattendu {type(element)} dans {field_name} de {interaction_instance}")
                actual_elements.append("UNKNOWN")
        else:
            break
        i += 1

    filtered_expected_structure = [s for s in expected_structure if s and s != "Stop"]

    if len(actual_elements) != len(filtered_expected_structure):
        logger.warning(f"Validation échouée: Nombre d'éléments ({len(actual_elements)}) différent ({len(filtered_expected_structure)}). Réels: {actual_elements}, Attendus: {filtered_expected_structure}")
        return False

    for actual, expected_label in zip(actual_elements, filtered_expected_structure):
        # Pas besoin de vérifier expected_type ici, car on compare les labels dérivés
        if actual != expected_label:
            logger.warning(f"Validation échouée: Type '{actual}' ne correspond pas à '{expected_label}'.")
            return False
            
    logger.info(f"Validation structure OK pour {interaction_instance.__class__.__name__}: {filtered_expected_structure}")
    return True 