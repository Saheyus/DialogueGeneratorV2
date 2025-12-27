"""Schémas Pydantic pour la configuration des champs de contexte."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class FieldInfo(BaseModel):
    """Informations sur un champ détecté.
    
    Attributes:
        path: Chemin du champ (ex: "Background.Relations")
        label: Label lisible du champ
        type: Type de données ("string", "list", "dict")
        depth: Profondeur d'imbrication (0 = racine)
        frequency: Fréquence du champ (0.0 à 1.0)
        suggested: Si le champ est suggéré pour le type de génération
        category: Catégorie du champ ("identity", "characterization", "voice", "background", "mechanics")
        importance: Importance du champ ("essential", "common", "rare")
        is_essential: Si le champ est essentiel (court, toujours sélectionné, non désélectionnable)
    """
    path: str = Field(..., description="Chemin du champ")
    label: str = Field(..., description="Label lisible du champ")
    type: str = Field(..., description="Type de données")
    depth: int = Field(..., description="Profondeur d'imbrication")
    frequency: float = Field(..., ge=0.0, le=1.0, description="Fréquence du champ")
    suggested: bool = Field(default=False, description="Champ suggéré")
    category: Optional[str] = Field(None, description="Catégorie du champ")
    importance: Optional[str] = Field(None, description="Importance du champ")
    is_essential: bool = Field(default=False, description="Champ essentiel (non désélectionnable)")


class ContextFieldConfig(BaseModel):
    """Configuration des champs à inclure pour un type d'élément.
    
    Attributes:
        element_type: Type d'élément ("character", "location", "item", "species", "community")
        fields: Liste des chemins de champs à inclure
        organization: Mode d'organisation ("default", "narrative", "minimal")
    """
    element_type: str = Field(..., description="Type d'élément")
    fields: List[str] = Field(default_factory=list, description="Liste des champs à inclure")
    organization: Optional[str] = Field(default="default", description="Mode d'organisation")


class ContextFieldsResponse(BaseModel):
    """Réponse contenant les champs disponibles pour un type d'élément.
    
    Attributes:
        element_type: Type d'élément
        fields: Dictionnaire des champs disponibles (path -> FieldInfo)
        total: Nombre total de champs détectés
    """
    element_type: str = Field(..., description="Type d'élément")
    fields: Dict[str, FieldInfo] = Field(default_factory=dict, description="Champs disponibles")
    total: int = Field(..., description="Nombre total de champs")


class ContextFieldSuggestionsRequest(BaseModel):
    """Requête pour obtenir des suggestions de champs.
    
    Attributes:
        element_type: Type d'élément
        context: Contexte de génération ("dialogue", "action", "emotional", "revelation")
    """
    element_type: str = Field(..., description="Type d'élément")
    context: Optional[str] = Field(None, description="Contexte de génération")


class ContextFieldSuggestionsResponse(BaseModel):
    """Réponse contenant les suggestions de champs.
    
    Attributes:
        element_type: Type d'élément
        context: Contexte de génération
        suggested_fields: Liste des chemins de champs suggérés
    """
    element_type: str = Field(..., description="Type d'élément")
    context: Optional[str] = Field(None, description="Contexte de génération")
    suggested_fields: List[str] = Field(default_factory=list, description="Champs suggérés")


class ContextPreviewRequest(BaseModel):
    """Requête pour prévisualiser le contexte avec une configuration personnalisée.
    
    Attributes:
        selected_elements: Éléments sélectionnés (nom -> type)
        field_configs: Configuration des champs par type d'élément
        organization_mode: Mode d'organisation ("default", "narrative", "minimal")
        scene_instruction: Instruction de scène
        max_tokens: Nombre maximum de tokens
    """
    selected_elements: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Éléments sélectionnés par type (ex: {'characters': ['Uresaïr']})"
    )
    field_configs: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Configuration des champs par type d'élément (ex: {'character': ['Nom', 'Dialogue Type']})"
    )
    organization_mode: Optional[str] = Field(default="default", description="Mode d'organisation")
    scene_instruction: Optional[str] = Field(None, description="Instruction de scène")
    max_tokens: int = Field(default=70000, description="Nombre maximum de tokens")


class ContextPreviewResponse(BaseModel):
    """Réponse contenant la prévisualisation du contexte.
    
    Attributes:
        preview: Texte formaté du contexte
        tokens: Nombre de tokens estimé
    """
    preview: str = Field(..., description="Prévisualisation du contexte")
    tokens: int = Field(..., description="Nombre de tokens estimé")


class DefaultFieldConfigResponse(BaseModel):
    """Réponse contenant la configuration par défaut des champs.
    
    Attributes:
        essential_fields: Champs essentiels (courts, toujours sélectionnés) par type d'élément
        default_fields: Tous les champs par défaut par type d'élément
    """
    essential_fields: Dict[str, List[str]] = Field(..., description="Champs essentiels par type")
    default_fields: Dict[str, List[str]] = Field(..., description="Tous les champs par défaut par type")

