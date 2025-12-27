"""Schémas Pydantic pour le vocabulaire Alteir et les guides narratifs."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class VocabularyTerm(BaseModel):
    """Terme du vocabulaire Alteir.
    
    Attributes:
        term: Le terme/concept.
        definition: Définition brève du terme.
        importance: Niveau d'importance ("Majeur", "Important", "Modéré", "Secondaire", "Mineur", "Anecdotique").
        category: Catégorie du terme ("Technologie", "Magie", "Race/Espèce", etc.).
        type: Type linguistique ("Calque linguistique", "Dérivation sémantique", etc.).
        origin: Origine du terme.
    """
    term: str = Field(..., description="Le terme/concept")
    definition: str = Field(default="", description="Définition brève du terme")
    importance: str = Field(default="Anecdotique", description="Niveau d'importance")
    category: str = Field(default="Autre", description="Catégorie du terme")
    type: str = Field(default="", description="Type linguistique")
    origin: str = Field(default="", description="Origine du terme")


class VocabularyResponse(BaseModel):
    """Réponse contenant le vocabulaire filtré.
    
    Attributes:
        terms: Liste des termes filtrés.
        total: Nombre total de termes.
        filtered_count: Nombre de termes après filtrage.
        min_importance: Niveau d'importance minimum utilisé pour le filtrage.
        statistics: Statistiques sur le vocabulaire.
    """
    terms: List[VocabularyTerm] = Field(default_factory=list, description="Liste des termes filtrés")
    total: int = Field(..., description="Nombre total de termes dans le vocabulaire")
    filtered_count: int = Field(..., description="Nombre de termes après filtrage")
    min_importance: str = Field(..., description="Niveau d'importance minimum utilisé")
    statistics: Dict[str, Any] = Field(default_factory=dict, description="Statistiques sur le vocabulaire")


class VocabularySyncResponse(BaseModel):
    """Réponse de synchronisation du vocabulaire.
    
    Attributes:
        success: Indique si la synchronisation a réussi.
        terms_count: Nombre de termes synchronisés.
        last_sync: Timestamp de dernière synchronisation.
        error: Message d'erreur si la synchronisation a échoué.
    """
    success: bool = Field(..., description="Indique si la synchronisation a réussi")
    terms_count: int = Field(default=0, description="Nombre de termes synchronisés")
    last_sync: Optional[str] = Field(None, description="Timestamp de dernière synchronisation (ISO format)")
    error: Optional[str] = Field(None, description="Message d'erreur si échec")


class NarrativeGuideResponse(BaseModel):
    """Réponse contenant les guides narratifs.
    
    Attributes:
        dialogue_guide: Contenu du guide des dialogues.
        narrative_guide: Contenu du guide de narration.
        rules: Règles extraites (ton, structure, interdits, principes).
        last_sync: Timestamp de dernière synchronisation.
    """
    dialogue_guide: str = Field(default="", description="Contenu du guide des dialogues")
    narrative_guide: str = Field(default="", description="Contenu du guide de narration")
    rules: Dict[str, List[str]] = Field(default_factory=dict, description="Règles extraites par catégorie")
    last_sync: Optional[str] = Field(None, description="Timestamp de dernière synchronisation (ISO format)")


class NarrativeGuidesSyncResponse(BaseModel):
    """Réponse de synchronisation des guides narratifs.
    
    Attributes:
        success: Indique si la synchronisation a réussi.
        dialogue_guide_length: Longueur du guide des dialogues (caractères).
        narrative_guide_length: Longueur du guide de narration (caractères).
        last_sync: Timestamp de dernière synchronisation.
        error: Message d'erreur si la synchronisation a échoué.
    """
    success: bool = Field(..., description="Indique si la synchronisation a réussi")
    dialogue_guide_length: int = Field(default=0, description="Longueur du guide des dialogues")
    narrative_guide_length: int = Field(default=0, description="Longueur du guide de narration")
    last_sync: Optional[str] = Field(None, description="Timestamp de dernière synchronisation (ISO format)")
    error: Optional[str] = Field(None, description="Message d'erreur si échec")


class VocabularyStatsResponse(BaseModel):
    """Réponse contenant les statistiques du vocabulaire.
    
    Attributes:
        total: Nombre total de termes.
        by_importance: Nombre de termes par niveau d'importance.
        by_category: Nombre de termes par catégorie.
        by_type: Nombre de termes par type linguistique.
    """
    total: int = Field(..., description="Nombre total de termes")
    by_importance: Dict[str, int] = Field(default_factory=dict, description="Nombre par importance")
    by_category: Dict[str, int] = Field(default_factory=dict, description="Nombre par catégorie")
    by_type: Dict[str, int] = Field(default_factory=dict, description="Nombre par type")

