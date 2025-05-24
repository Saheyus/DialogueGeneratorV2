from typing import List, Type, Optional, Dict, Any, Union, Tuple
from pydantic import BaseModel, Field, create_model
import logging
import uuid
from .dialogue_elements import DialogueLineElement, PlayerChoicesBlockElement, CommandElement, AnyDialogueElement
from .interaction import Interaction

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

def convert_dynamic_to_standard_interaction(dynamic_interaction: BaseModel) -> Interaction:
    """
    Convertit un modèle Pydantic dynamique (avec des champs phase_X) en un objet Interaction standard.
    """
    elements: List[AnyDialogueElement] = []
    
    # Tenter d'extraire les phases ordonnées
    # Les modèles dynamiques peuvent avoir phase_1, phase_2, etc.
    # ou directement les noms des éléments comme pnj_line_1, player_choices_1
    
    # D'abord, vérifier les champs phase_X
    i = 1
    phase_found = False
    while True:
        phase_attr_name = f"phase_{i}"
        if hasattr(dynamic_interaction, phase_attr_name):
            phase_found = True
            element = getattr(dynamic_interaction, phase_attr_name)
            if element: # S'assurer que la phase n'est pas None
                if isinstance(element, (DialogueLineElement, PlayerChoicesBlockElement, CommandElement)):
                    elements.append(element)
                else:
                    logger.warning(f"L'attribut '{phase_attr_name}' du modèle dynamique n'est pas un élément de dialogue valide: {type(element)}")
            else: # phase_X est None, peut indiquer la fin de la structure définie
                logger.debug(f"L'attribut '{phase_attr_name}' est None, fin possible des phases.")
        elif phase_found: # Si on a trouvé des phase_X mais que la suivante manque, on arrête pour phase_X
            break
        else: # Si aucune phase_X n'a été trouvée et que celle-ci manque, on arrête aussi la recherche de phase_X
            break
        i += 1

    # Si aucune phase_X n'a été trouvée, essayer d'extraire les éléments directement
    # en se basant sur les annotations de type du modèle dynamique (plus complexe et moins fiable ici)
    # Pour l'instant, on se concentre sur les phase_X qui sont le pattern actuel.
    # Si besoin, on ajoutera une logique pour inspecter dynamic_interaction.__fields__

    if not elements and not phase_found: # Si toujours pas d'éléments et aucune phase_X trouvée
        logger.warning(f"Aucun élément de dialogue trouvé via les champs 'phase_X' pour {type(dynamic_interaction).__name__}. L'interaction sera vide.")

    # Copier les autres attributs de Interaction s'ils existent sur le dynamic_interaction
    # (interaction_id, title, header_tags, etc.)
    # Générer un UUID si interaction_id n'est pas fourni par le LLM
    interaction_id_str = getattr(dynamic_interaction, "interaction_id", None)
    if not interaction_id_str:
        logger.warning(f"Aucun interaction_id fourni par le LLM pour {type(dynamic_interaction).__name__}, génération d'un nouveau UUID.")
        interaction_id_str = str(uuid.uuid4())
    elif not isinstance(interaction_id_str, str): # Au cas où ce ne serait pas une string
        logger.warning(f"interaction_id '{interaction_id_str}' n'est pas une chaîne, conversion en str.")
        interaction_id_str = str(interaction_id_str)


    interaction_data = {
        "interaction_id": interaction_id_str,
        "title": getattr(dynamic_interaction, "title", f"Generated Interaction - {interaction_id_str[:8]}"),
        "header_tags": getattr(dynamic_interaction, "header_tags", []),
        "header_commands": getattr(dynamic_interaction, "header_commands", []),
        "next_interaction_id_if_no_choices": getattr(dynamic_interaction, "next_interaction_id_if_no_choices", None),
        "elements": elements
    }
    
    try:
        standard_interaction = Interaction(**interaction_data)
        logger.info(f"Conversion de {type(dynamic_interaction).__name__} en Interaction standard réussie. ID: {standard_interaction.interaction_id}, Elements: {len(standard_interaction.elements)}")
        return standard_interaction
    except Exception as e:
        logger.error(f"Erreur lors de la création de l'objet Interaction standard à partir de {type(dynamic_interaction).__name__}: {e}", exc_info=True)
        # Renvoyer une Interaction vide ou lever une exception ? Pour l'instant, on lève pour que l'appelant gère.
        raise ValueError(f"Impossible de convertir {type(dynamic_interaction).__name__} en Interaction standard: {e}") 