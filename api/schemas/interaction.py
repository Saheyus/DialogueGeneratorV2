"""Schémas Pydantic pour les interactions."""
from typing import List, Optional
from pydantic import BaseModel, Field
from models.dialogue_structure.interaction import Interaction as InteractionModel
from models.dialogue_structure.dialogue_elements import (
    DialogueLineElement,
    PlayerChoicesBlockElement,
    CommandElement,
    AnyDialogueElement
)


class InteractionResponse(BaseModel):
    """Réponse contenant une interaction.
    
    Ce schéma est basé sur le modèle Interaction mais adapté pour l'API.
    """
    interaction_id: str = Field(..., description="Identifiant unique de l'interaction")
    title: str = Field(default="", description="Titre descriptif de l'interaction")
    elements: List[dict] = Field(default_factory=list, description="Liste des éléments composant l'interaction")
    header_commands: List[str] = Field(default_factory=list, description="Commandes à exécuter au début")
    header_tags: List[str] = Field(default_factory=list, description="Tags de l'en-tête")
    next_interaction_id_if_no_choices: Optional[str] = Field(None, description="ID de l'interaction suivante si pas de choix")
    
    @classmethod
    def from_model(cls, interaction: InteractionModel) -> "InteractionResponse":
        """Crée une InteractionResponse depuis un modèle Interaction.
        
        Args:
            interaction: Le modèle Interaction.
            
        Returns:
            Une InteractionResponse.
        """
        return cls(
            interaction_id=interaction.interaction_id,
            title=interaction.title,
            elements=[elem.model_dump() for elem in interaction.elements],
            header_commands=interaction.header_commands,
            header_tags=interaction.header_tags,
            next_interaction_id_if_no_choices=interaction.next_interaction_id_if_no_choices
        )


class InteractionCreateRequest(BaseModel):
    """Requête pour créer une interaction.
    
    Attributes:
        title: Titre de l'interaction.
        elements: Liste des éléments (sérialisés en dict).
        header_commands: Commandes d'en-tête.
        header_tags: Tags d'en-tête.
        next_interaction_id_if_no_choices: ID de l'interaction suivante.
    """
    title: str = Field(default="", description="Titre descriptif de l'interaction")
    elements: List[dict] = Field(default_factory=list, description="Liste des éléments (sérialisés)")
    header_commands: List[str] = Field(default_factory=list, description="Commandes à exécuter au début")
    header_tags: List[str] = Field(default_factory=list, description="Tags de l'en-tête")
    next_interaction_id_if_no_choices: Optional[str] = Field(None, description="ID de l'interaction suivante si pas de choix")


class InteractionUpdateRequest(BaseModel):
    """Requête pour mettre à jour une interaction.
    
    Attributes:
        title: Titre de l'interaction (optionnel).
        elements: Liste des éléments (optionnel).
        header_commands: Commandes d'en-tête (optionnel).
        header_tags: Tags d'en-tête (optionnel).
        next_interaction_id_if_no_choices: ID de l'interaction suivante (optionnel).
    """
    title: Optional[str] = Field(None, description="Titre descriptif de l'interaction")
    elements: Optional[List[dict]] = Field(None, description="Liste des éléments (sérialisés)")
    header_commands: Optional[List[str]] = Field(None, description="Commandes à exécuter au début")
    header_tags: Optional[List[str]] = Field(None, description="Tags de l'en-tête")
    next_interaction_id_if_no_choices: Optional[str] = Field(None, description="ID de l'interaction suivante si pas de choix")


class InteractionListResponse(BaseModel):
    """Réponse contenant une liste d'interactions.
    
    Attributes:
        interactions: Liste des interactions.
        total: Nombre total d'interactions.
    """
    interactions: List[InteractionResponse] = Field(..., description="Liste des interactions")
    total: int = Field(..., description="Nombre total d'interactions")


class InteractionRelationsResponse(BaseModel):
    """Réponse contenant les relations d'une interaction.
    
    Attributes:
        parents: Liste des IDs des interactions parentes.
        children: Liste des IDs des interactions enfants.
    """
    parents: List[str] = Field(default_factory=list, description="IDs des interactions parentes")
    children: List[str] = Field(default_factory=list, description="IDs des interactions enfants")


class InteractionContextPathResponse(BaseModel):
    """Réponse contenant le chemin de contexte d'une interaction (tous les parents jusqu'à la racine).
    
    Attributes:
        path: Liste des interactions du chemin, de la racine à l'interaction cible.
        total: Nombre total d'interactions dans le chemin.
    """
    path: List[InteractionResponse] = Field(..., description="Liste des interactions du chemin")
    total: int = Field(..., description="Nombre total d'interactions dans le chemin")
