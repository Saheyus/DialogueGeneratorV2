"""Schémas Pydantic pour le contexte GDD."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from api.schemas.dialogue import ContextSelection


class CharacterResponse(BaseModel):
    """Réponse contenant un personnage.
    
    Attributes:
        name: Nom du personnage.
        data: Données complètes du personnage (dict JSON).
    """
    name: str = Field(..., description="Nom du personnage")
    data: Dict[str, Any] = Field(..., description="Données complètes du personnage")


class LocationResponse(BaseModel):
    """Réponse contenant un lieu.
    
    Attributes:
        name: Nom du lieu.
        data: Données complètes du lieu (dict JSON).
    """
    name: str = Field(..., description="Nom du lieu")
    data: Dict[str, Any] = Field(..., description="Données complètes du lieu")


class ItemResponse(BaseModel):
    """Réponse contenant un objet.
    
    Attributes:
        name: Nom de l'objet.
        data: Données complètes de l'objet (dict JSON).
    """
    name: str = Field(..., description="Nom de l'objet")
    data: Dict[str, Any] = Field(..., description="Données complètes de l'objet")


class CharacterListResponse(BaseModel):
    """Réponse contenant une liste de personnages.
    
    Attributes:
        characters: Liste des personnages.
        total: Nombre total de personnages.
    """
    characters: List[CharacterResponse] = Field(..., description="Liste des personnages")
    total: int = Field(..., description="Nombre total de personnages")


class LocationListResponse(BaseModel):
    """Réponse contenant une liste de lieux.
    
    Attributes:
        locations: Liste des lieux.
        total: Nombre total de lieux.
    """
    locations: List[LocationResponse] = Field(..., description="Liste des lieux")
    total: int = Field(..., description="Nombre total de lieux")


class ItemListResponse(BaseModel):
    """Réponse contenant une liste d'objets.
    
    Attributes:
        items: Liste des objets.
        total: Nombre total d'objets.
    """
    items: List[ItemResponse] = Field(..., description="Liste des objets")
    total: int = Field(..., description="Nombre total d'objets")


class BuildContextRequest(BaseModel):
    """Requête pour construire un contexte personnalisé.
    
    Attributes:
        context_selections: Sélections de contexte GDD.
        user_instructions: Instructions utilisateur.
        max_tokens: Nombre maximum de tokens.
        include_dialogue_type: Inclure le type de dialogue dans le contexte.
    """
    context_selections: ContextSelection = Field(..., description="Sélections de contexte GDD")
    user_instructions: str = Field(default="", description="Instructions utilisateur")
    max_tokens: int = Field(default=1500, ge=100, le=50000, description="Nombre maximum de tokens")
    include_dialogue_type: bool = Field(default=False, description="Inclure le type de dialogue")


class BuildContextResponse(BaseModel):
    """Réponse contenant le contexte construit.
    
    Attributes:
        context: Le contexte construit (texte).
        token_count: Nombre de tokens du contexte.
    """
    context: str = Field(..., description="Contexte construit")
    token_count: int = Field(..., description="Nombre de tokens")

