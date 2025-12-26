from typing import List, Optional
from pydantic import BaseModel, Field
from .dialogue_elements import AnyDialogueElement, DialogueLineElement, PlayerChoicesBlockElement, CommandElement

class Interaction(BaseModel):
    interaction_id: str = Field(..., description="Identifiant unique de l'interaction.")
    title: str = Field("", description="Titre descriptif de l'interaction.")
    elements: List[AnyDialogueElement] = Field(default_factory=list, description="Liste des éléments composant l'interaction (lignes de dialogue, choix, commandes).")
    header_commands: List[str] = Field(default_factory=list, description="Commandes à exécuter au début de l'interaction (avant les éléments).")
    header_tags: List[str] = Field(default_factory=list, description="Tags de l'en-tête (ex: pour la couleur, le suivi)." )
    next_interaction_id_if_no_choices: Optional[str] = Field(None, description="ID de l'interaction suivante si celle-ci se termine sans choix du joueur.") 