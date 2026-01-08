"""Modèles Pydantic pour la structure JSON du prompt."""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class ItemSection(BaseModel):
    """Section d'une fiche individuelle (IDENTITÉ, CARACTÉRISATION, etc.)."""
    title: str = Field(..., description="Titre de la section (ex: 'IDENTITÉ', 'CARACTÉRISATION')")
    content: str = Field(..., description="Contenu textuel de la section")
    tokenCount: Optional[int] = Field(None, description="Nombre de tokens dans cette section")


class ContextItem(BaseModel):
    """Fiche individuelle (PNJ 1, LIEU 2, etc.)."""
    id: str = Field(..., description="Identifiant unique (ex: 'PNJ_1', 'LIEU_2')")
    name: str = Field(..., description="Nom affiché (ex: 'PNJ 1', 'LIEU 2')")
    sections: List[ItemSection] = Field(default_factory=list, description="Sections de la fiche")
    tokenCount: Optional[int] = Field(None, description="Nombre total de tokens dans cette fiche")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Métadonnées additionnelles (ex: nom réel de l'élément)")


class ContextCategory(BaseModel):
    """Catégorie de contexte (CHARACTERS, LOCATIONS, etc.)."""
    type: str = Field(..., description="Type de catégorie (ex: 'characters', 'locations')")
    title: str = Field(..., description="Titre de la catégorie (ex: 'CHARACTERS', 'LOCATIONS')")
    items: List[ContextItem] = Field(default_factory=list, description="Fiches dans cette catégorie")
    tokenCount: Optional[int] = Field(None, description="Nombre total de tokens dans cette catégorie")


class PromptSection(BaseModel):
    """Section principale du prompt (system_prompt, context, etc.)."""
    type: Literal["system_prompt", "context", "instruction", "other"] = Field(
        ..., description="Type de section"
    )
    title: str = Field(..., description="Titre de la section")
    content: str = Field(..., description="Contenu textuel de la section")
    tokenCount: Optional[int] = Field(None, description="Nombre de tokens dans cette section")
    categories: Optional[List[ContextCategory]] = Field(
        None, description="Catégories de contexte (uniquement pour type='context')"
    )


class PromptMetadata(BaseModel):
    """Métadonnées du prompt."""
    totalTokens: int = Field(..., description="Nombre total de tokens dans le prompt")
    generatedAt: str = Field(..., description="Date de génération au format ISO 8601")
    organizationMode: Optional[str] = Field(None, description="Mode d'organisation utilisé (narrative, default, minimal)")


class PromptStructure(BaseModel):
    """Structure racine du prompt JSON."""
    model_config = ConfigDict(json_encoders={
        datetime: lambda v: v.isoformat()
    })
    
    sections: List[PromptSection] = Field(..., description="Sections du prompt")
    metadata: PromptMetadata = Field(..., description="Métadonnées du prompt")
