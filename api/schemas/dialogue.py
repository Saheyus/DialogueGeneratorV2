"""Schémas Pydantic pour la génération de dialogues."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ContextSelection(BaseModel):
    """Sélection de contexte pour la génération.
    
    Attributes:
        characters: Liste des noms de personnages à inclure.
        locations: Liste des noms de lieux à inclure.
        items: Liste des noms d'objets à inclure.
        species: Liste des noms d'espèces à inclure.
        communities: Liste des noms de communautés à inclure.
        dialogues_examples: Liste des titres d'exemples de dialogues à inclure.
        scene_protagonists: Dictionnaire des protagonistes de la scène (sera converti en _scene_protagonists pour le service).
        scene_location: Dictionnaire du lieu de la scène (sera converti en _scene_location pour le service).
        generation_settings: Paramètres de génération additionnels.
    """
    characters: List[str] = Field(default_factory=list, description="Liste des personnages")
    locations: List[str] = Field(default_factory=list, description="Liste des lieux")
    items: List[str] = Field(default_factory=list, description="Liste des objets")
    species: List[str] = Field(default_factory=list, description="Liste des espèces")
    communities: List[str] = Field(default_factory=list, description="Liste des communautés")
    dialogues_examples: List[str] = Field(default_factory=list, description="Liste des exemples de dialogues")
    scene_protagonists: Optional[Dict[str, Any]] = Field(None, description="Protagonistes de la scène")
    scene_location: Optional[Dict[str, Any]] = Field(None, description="Lieu de la scène")
    generation_settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Paramètres de génération")
    
    def to_service_dict(self) -> Dict[str, Any]:
        """Convertit le ContextSelection en dictionnaire pour le service (avec préfixes underscore).
        
        Returns:
            Dictionnaire avec _scene_protagonists et _scene_location pour compatibilité service.
        """
        data = self.model_dump(exclude_none=True)
        # Convertir scene_protagonists -> _scene_protagonists
        if "scene_protagonists" in data:
            data["_scene_protagonists"] = data.pop("scene_protagonists")
        # Convertir scene_location -> _scene_location
        if "scene_location" in data:
            data["_scene_location"] = data.pop("scene_location")
        return data


class GenerateDialogueVariantsRequest(BaseModel):
    """Requête pour générer des variantes de dialogue texte.
    
    Attributes:
        k_variants: Nombre de variantes à générer.
        user_instructions: Instructions spécifiques de l'utilisateur.
        context_selections: Sélections de contexte GDD.
        max_context_tokens: Nombre maximum de tokens pour le contexte.
        structured_output: Générer en format structuré.
        system_prompt_override: Surcharge du system prompt (optionnel).
        llm_model_identifier: Identifiant du modèle LLM à utiliser.
    """
    k_variants: int = Field(default=1, ge=1, le=10, description="Nombre de variantes à générer")
    user_instructions: str = Field(..., min_length=1, description="Instructions spécifiques pour la scène")
    context_selections: ContextSelection = Field(..., description="Sélections de contexte GDD")
    max_context_tokens: int = Field(default=1500, ge=100, le=50000, description="Nombre maximum de tokens pour le contexte")
    structured_output: bool = Field(default=False, description="Générer en format structuré")
    system_prompt_override: Optional[str] = Field(None, description="Surcharge du system prompt")
    llm_model_identifier: str = Field(default="gpt-4o-mini", description="Identifiant du modèle LLM")


class GenerateInteractionVariantsRequest(BaseModel):
    """Requête pour générer des interactions structurées.
    
    Attributes:
        k_variants: Nombre de variantes à générer.
        user_instructions: Instructions spécifiques de l'utilisateur.
        context_selections: Sélections de contexte GDD.
        max_context_tokens: Nombre maximum de tokens pour le contexte.
        system_prompt_override: Surcharge du system prompt (optionnel).
        llm_model_identifier: Identifiant du modèle LLM à utiliser.
        previous_interaction_id: ID d'une interaction précédente pour la continuité narrative (optionnel).
    """
    k_variants: int = Field(default=1, ge=1, le=10, description="Nombre de variantes à générer")
    user_instructions: str = Field(..., min_length=1, description="Instructions spécifiques pour la scène")
    context_selections: ContextSelection = Field(..., description="Sélections de contexte GDD")
    max_context_tokens: int = Field(default=1500, ge=100, le=50000, description="Nombre maximum de tokens pour le contexte")
    system_prompt_override: Optional[str] = Field(None, description="Surcharge du system prompt")
    llm_model_identifier: str = Field(default="gpt-4o-mini", description="Identifiant du modèle LLM")
    previous_interaction_id: Optional[str] = Field(None, description="ID d'une interaction précédente pour la continuité narrative")


class DialogueVariantResponse(BaseModel):
    """Réponse contenant une variante de dialogue.
    
    Attributes:
        id: Identifiant unique de la variante.
        title: Titre de la variante.
        content: Contenu de la variante (texte ou JSON).
        is_new: Indique si c'est une nouvelle variante.
    """
    id: str = Field(..., description="Identifiant unique de la variante")
    title: str = Field(..., description="Titre de la variante")
    content: str = Field(..., description="Contenu de la variante")
    is_new: bool = Field(default=True, description="Indique si c'est une nouvelle variante")


class GenerateDialogueVariantsResponse(BaseModel):
    """Réponse pour la génération de variantes de dialogue.
    
    Attributes:
        variants: Liste des variantes générées.
        prompt_used: Le prompt complet utilisé pour la génération.
        estimated_tokens: Nombre estimé de tokens utilisés.
    """
    variants: List[DialogueVariantResponse] = Field(..., description="Liste des variantes générées")
    prompt_used: Optional[str] = Field(None, description="Prompt complet utilisé")
    estimated_tokens: int = Field(..., description="Nombre estimé de tokens")


class EstimateTokensRequest(BaseModel):
    """Requête pour estimer le nombre de tokens.
    
    Attributes:
        context_selections: Sélections de contexte GDD.
        user_instructions: Instructions utilisateur (peut être vide si des sélections existent).
        max_context_tokens: Nombre maximum de tokens pour le contexte.
        system_prompt_override: Surcharge du system prompt (optionnel).
    """
    context_selections: ContextSelection = Field(..., description="Sélections de contexte GDD")
    user_instructions: str = Field(default="", description="Instructions utilisateur")
    max_context_tokens: int = Field(default=1500, ge=100, le=50000, description="Nombre maximum de tokens pour le contexte")
    system_prompt_override: Optional[str] = Field(None, description="Surcharge du system prompt")


class EstimateTokensResponse(BaseModel):
    """Réponse pour l'estimation de tokens.
    
    Attributes:
        context_tokens: Nombre de tokens du contexte.
        total_estimated_tokens: Nombre total estimé de tokens (contexte + prompt).
        estimated_prompt: Le prompt estimé complet.
    """
    context_tokens: int = Field(..., description="Nombre de tokens du contexte")
    total_estimated_tokens: int = Field(..., description="Nombre total estimé de tokens")
    estimated_prompt: str | None = Field(default=None, description="Le prompt estimé complet")

