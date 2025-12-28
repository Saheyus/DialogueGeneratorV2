"""Schémas Pydantic pour les endpoints de configuration."""
from typing import List, Optional
from pydantic import BaseModel, Field


class FieldInfo(BaseModel):
    """Information sur un champ de contexte.
    
    Attributes:
        field_name: Nom du champ.
        description: Description du champ.
        is_essential: Si True, le champ est considéré comme essentiel.
    """
    field_name: str = Field(..., description="Nom du champ")
    description: str = Field(..., description="Description du champ")
    is_essential: bool = Field(default=False, description="Si True, le champ est essentiel")


class ContextFieldsResponse(BaseModel):
    """Réponse contenant la liste des champs de contexte disponibles.
    
    Attributes:
        fields: Liste des informations sur les champs.
    """
    fields: List[FieldInfo] = Field(default_factory=list, description="Liste des champs de contexte")


class ContextFieldSuggestionsRequest(BaseModel):
    """Requête pour obtenir des suggestions de champs de contexte.
    
    Attributes:
        element_type: Type d'élément (character, location, item, etc.).
        selected_fields: Champs déjà sélectionnés.
    """
    element_type: str = Field(..., description="Type d'élément")
    selected_fields: List[str] = Field(default_factory=list, description="Champs déjà sélectionnés")


class ContextFieldSuggestionsResponse(BaseModel):
    """Réponse contenant des suggestions de champs de contexte.
    
    Attributes:
        suggestions: Liste des suggestions de champs.
    """
    suggestions: List[str] = Field(default_factory=list, description="Liste des suggestions")


class ContextPreviewRequest(BaseModel):
    """Requête pour obtenir un aperçu du contexte construit.
    
    Attributes:
        context_selections: Sélections de contexte.
        max_tokens: Nombre maximum de tokens pour l'aperçu.
        organization_mode: Mode d'organisation du contexte.
    """
    context_selections: dict = Field(..., description="Sélections de contexte")
    max_tokens: int = Field(default=1500, description="Nombre maximum de tokens")
    organization_mode: Optional[str] = Field(None, description="Mode d'organisation")


class ContextPreviewResponse(BaseModel):
    """Réponse contenant un aperçu du contexte.
    
    Attributes:
        preview_text: Texte de l'aperçu.
        estimated_tokens: Nombre estimé de tokens.
    """
    preview_text: str = Field(..., description="Texte de l'aperçu")
    estimated_tokens: int = Field(..., description="Nombre estimé de tokens")


class DefaultFieldConfigResponse(BaseModel):
    """Réponse contenant la configuration par défaut des champs.
    
    Attributes:
        config: Configuration par défaut.
    """
    config: dict = Field(..., description="Configuration par défaut")


class SceneInstructionTemplate(BaseModel):
    """Template d'instructions de scène.
    
    Attributes:
        id: Identifiant du template.
        name: Nom du template.
        description: Description du template.
        instructions: Instructions de scène.
    """
    id: str = Field(..., description="Identifiant du template")
    name: str = Field(..., description="Nom du template")
    description: str = Field(..., description="Description du template")
    instructions: str = Field(..., description="Instructions de scène")


class SceneInstructionTemplatesResponse(BaseModel):
    """Réponse contenant la liste des templates d'instructions de scène.
    
    Attributes:
        templates: Liste des templates.
        total: Nombre total de templates.
    """
    templates: List[SceneInstructionTemplate] = Field(default_factory=list, description="Liste des templates")
    total: int = Field(default=0, description="Nombre total de templates")


class AuthorProfileTemplate(BaseModel):
    """Template de profil d'auteur.
    
    Attributes:
        id: Identifiant du template.
        name: Nom du template.
        description: Description du template.
        profile: Profil d'auteur.
    """
    id: str = Field(..., description="Identifiant du template")
    name: str = Field(..., description="Nom du template")
    description: str = Field(..., description="Description du template")
    profile: str = Field(..., description="Profil d'auteur")


class AuthorProfileTemplatesResponse(BaseModel):
    """Réponse contenant la liste des templates de profils d'auteur.
    
    Attributes:
        templates: Liste des templates.
        total: Nombre total de templates.
    """
    templates: List[AuthorProfileTemplate] = Field(default_factory=list, description="Liste des templates")
    total: int = Field(default=0, description="Nombre total de templates")


class TemplateFilePathsResponse(BaseModel):
    """Réponse contenant les chemins des fichiers de templates.
    
    Attributes:
        system_prompt_path: Chemin du fichier system prompt par défaut.
        scene_instructions_dir: Chemin du répertoire des instructions de scène.
        author_profiles_dir: Chemin du répertoire des profils d'auteur.
    """
    system_prompt_path: str = Field(..., description="Chemin du fichier system prompt par défaut")
    scene_instructions_dir: str = Field(..., description="Chemin du répertoire des instructions de scène")
    author_profiles_dir: str = Field(..., description="Chemin du répertoire des profils d'auteur")
    config_dir: str = Field(..., description="Chemin du répertoire de configuration")
