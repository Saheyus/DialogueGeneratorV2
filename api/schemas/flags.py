"""Schémas Pydantic pour les flags in-game."""
from typing import Optional, List, Union, Literal
from pydantic import BaseModel, Field


# Union type pour les valeurs de flags (bool, int, float, string)
FlagValue = Union[bool, int, float, str]


class FlagDefinition(BaseModel):
    """Définition d'un flag in-game (provenant du catalogue CSV).
    
    Attributes:
        id: Identifiant unique du flag (ex: "PLAYER_KILLED_BOSS").
        type: Type de valeur ("bool", "int", "float", "string").
        category: Catégorie du flag (ex: "Event", "Choice", "Stat").
        label: Label lisible par humain.
        description: Description détaillée du flag.
        defaultValue: Valeur par défaut (en string, sera convertie selon le type).
        tags: Liste de tags pour la recherche.
        isFavorite: Si le flag est marqué comme favori.
    """
    id: str = Field(..., description="Identifiant unique du flag")
    type: Literal["bool", "int", "float", "string"] = Field(..., description="Type de valeur du flag")
    category: str = Field(..., description="Catégorie du flag")
    label: str = Field(..., description="Label lisible par humain")
    description: Optional[str] = Field(None, description="Description détaillée")
    defaultValue: str = Field(..., description="Valeur par défaut (en string)")
    tags: List[str] = Field(default_factory=list, description="Liste de tags")
    isFavorite: bool = Field(default=False, description="Si le flag est marqué comme favori")


class InGameFlag(BaseModel):
    """Flag in-game avec sa valeur actuelle (sélection runtime).
    
    Attributes:
        id: Identifiant du flag.
        value: Valeur actuelle du flag.
        category: Catégorie du flag (pour affichage/tri).
        timestamp: Timestamp optionnel (ISO format).
    """
    id: str = Field(..., description="Identifiant du flag")
    value: FlagValue = Field(..., description="Valeur actuelle du flag")
    category: Optional[str] = Field(None, description="Catégorie du flag")
    timestamp: Optional[str] = Field(None, description="Timestamp ISO (optionnel)")


class FlagsCatalogResponse(BaseModel):
    """Réponse pour la liste des définitions de flags.
    
    Attributes:
        flags: Liste des définitions de flags.
        total: Nombre total de flags.
    """
    flags: List[FlagDefinition] = Field(..., description="Liste des définitions de flags")
    total: int = Field(..., description="Nombre total de flags")


class UpsertFlagRequest(BaseModel):
    """Requête pour créer ou mettre à jour une définition de flag.
    
    Attributes:
        id: Identifiant unique du flag.
        type: Type de valeur.
        category: Catégorie du flag.
        label: Label lisible.
        description: Description détaillée.
        defaultValue: Valeur par défaut.
        tags: Liste de tags.
        isFavorite: Si favori.
    """
    id: str = Field(..., min_length=1, description="Identifiant unique du flag")
    type: Literal["bool", "int", "float", "string"] = Field(..., description="Type de valeur")
    category: str = Field(..., min_length=1, description="Catégorie du flag")
    label: str = Field(..., min_length=1, description="Label lisible")
    description: Optional[str] = Field(None, description="Description détaillée")
    defaultValue: str = Field(..., description="Valeur par défaut (en string)")
    tags: List[str] = Field(default_factory=list, description="Liste de tags")
    isFavorite: bool = Field(default=False, description="Si favori")


class UpsertFlagResponse(BaseModel):
    """Réponse pour l'upsert d'un flag.
    
    Attributes:
        success: Si l'opération a réussi.
        flag: La définition du flag créée/mise à jour.
    """
    success: bool = Field(..., description="Si l'opération a réussi")
    flag: FlagDefinition = Field(..., description="La définition du flag")


class ToggleFavoriteRequest(BaseModel):
    """Requête pour activer/désactiver le statut favori d'un flag.
    
    Attributes:
        flag_id: ID du flag.
        is_favorite: True pour marquer comme favori, False sinon.
    """
    flag_id: str = Field(..., description="ID du flag")
    is_favorite: bool = Field(..., description="True pour marquer comme favori")


class ToggleFavoriteResponse(BaseModel):
    """Réponse pour toggle favorite.
    
    Attributes:
        success: Si l'opération a réussi.
        flag_id: ID du flag modifié.
        is_favorite: Nouveau statut favori.
    """
    success: bool = Field(..., description="Si l'opération a réussi")
    flag_id: str = Field(..., description="ID du flag modifié")
    is_favorite: bool = Field(..., description="Nouveau statut favori")
