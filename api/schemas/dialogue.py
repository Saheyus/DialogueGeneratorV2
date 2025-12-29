"""Schémas Pydantic pour la génération de dialogues."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import sys
from pathlib import Path

# Ajouter le répertoire racine au path pour importer constants
_root_dir = Path(__file__).parent.parent.parent
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

from constants import Defaults


class ContextSelection(BaseModel):
    """Sélection de contexte pour la génération.
    
    Attributes:
        characters_full: Liste des noms de personnages à inclure en mode complet.
        characters_excerpt: Liste des noms de personnages à inclure en mode extrait.
        locations_full: Liste des noms de lieux à inclure en mode complet.
        locations_excerpt: Liste des noms de lieux à inclure en mode extrait.
        items_full: Liste des noms d'objets à inclure en mode complet.
        items_excerpt: Liste des noms d'objets à inclure en mode extrait.
        species_full: Liste des noms d'espèces à inclure en mode complet.
        species_excerpt: Liste des noms d'espèces à inclure en mode extrait.
        communities_full: Liste des noms de communautés à inclure en mode complet.
        communities_excerpt: Liste des noms de communautés à inclure en mode extrait.
        dialogues_examples: Liste des titres d'exemples de dialogues à inclure.
        scene_protagonists: Dictionnaire des protagonistes de la scène (sera converti en _scene_protagonists pour le service).
        scene_location: Dictionnaire du lieu de la scène (sera converti en _scene_location pour le service).
        generation_settings: Paramètres de génération additionnels.
    """
    characters_full: List[str] = Field(default_factory=list, description="Liste des personnages (mode complet)")
    characters_excerpt: List[str] = Field(default_factory=list, description="Liste des personnages (mode extrait)")
    locations_full: List[str] = Field(default_factory=list, description="Liste des lieux (mode complet)")
    locations_excerpt: List[str] = Field(default_factory=list, description="Liste des lieux (mode extrait)")
    items_full: List[str] = Field(default_factory=list, description="Liste des objets (mode complet)")
    items_excerpt: List[str] = Field(default_factory=list, description="Liste des objets (mode extrait)")
    species_full: List[str] = Field(default_factory=list, description="Liste des espèces (mode complet)")
    species_excerpt: List[str] = Field(default_factory=list, description="Liste des espèces (mode extrait)")
    communities_full: List[str] = Field(default_factory=list, description="Liste des communautés (mode complet)")
    communities_excerpt: List[str] = Field(default_factory=list, description="Liste des communautés (mode extrait)")
    dialogues_examples: List[str] = Field(default_factory=list, description="Liste des exemples de dialogues")
    scene_protagonists: Optional[Dict[str, Any]] = Field(None, description="Protagonistes de la scène")
    scene_location: Optional[Dict[str, Any]] = Field(None, description="Lieu de la scène")
    generation_settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Paramètres de génération")
    
    def to_service_dict(self) -> Dict[str, Any]:
        """Convertit le ContextSelection en dictionnaire pour le service (avec préfixes underscore et métadonnées de mode).
        
        Returns:
            Dictionnaire avec _scene_protagonists, _scene_location, et _element_modes pour compatibilité service.
            Les listes sont fusionnées et un dictionnaire _element_modes indique le mode de chaque élément.
        """
        data = self.model_dump(exclude_none=True)
        
        # Convertir scene_protagonists -> _scene_protagonists
        if "scene_protagonists" in data:
            data["_scene_protagonists"] = data.pop("scene_protagonists")
        # Convertir scene_location -> _scene_location
        if "scene_location" in data:
            data["_scene_location"] = data.pop("scene_location")
        
        # Construire _element_modes pour indiquer le mode de chaque élément
        element_modes: Dict[str, Dict[str, str]] = {}
        
        # Fusionner les listes et créer les métadonnées de mode
        for element_type in ["characters", "locations", "items", "species", "communities"]:
            full_list = data.get(f"{element_type}_full", [])
            excerpt_list = data.get(f"{element_type}_excerpt", [])
            
            # Fusionner les listes (mode full par défaut pour compatibilité)
            merged_list = full_list + excerpt_list
            data[element_type] = merged_list
            
            # Créer le dictionnaire de modes pour ce type
            if merged_list:
                element_modes[element_type] = {}
                for name in full_list:
                    element_modes[element_type][name] = "full"
                for name in excerpt_list:
                    element_modes[element_type][name] = "excerpt"
            
            # Supprimer les listes séparées
            data.pop(f"{element_type}_full", None)
            data.pop(f"{element_type}_excerpt", None)
        
        # Ajouter _element_modes si non vide
        if element_modes:
            data["_element_modes"] = element_modes
        
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
        npc_speaker_id: ID du PNJ interlocuteur (si None, utiliser le premier personnage sélectionné).
    """
    k_variants: int = Field(default=1, ge=1, le=10, description="Nombre de variantes à générer")
    user_instructions: str = Field(..., min_length=1, description="Instructions spécifiques pour la scène")
    context_selections: ContextSelection = Field(..., description="Sélections de contexte GDD")
    max_context_tokens: int = Field(default=1500, ge=100, le=Defaults.MAX_CONTEXT_TOKENS, description="Nombre maximum de tokens pour le contexte")
    structured_output: bool = Field(default=False, description="Générer en format structuré")
    system_prompt_override: Optional[str] = Field(None, description="Surcharge du system prompt")
    llm_model_identifier: str = Field(default="gpt-5.2-mini", description="Identifiant du modèle LLM")
    npc_speaker_id: Optional[str] = Field(None, description="ID du PNJ interlocuteur (si None, utiliser le premier personnage sélectionné)")


# GenerateInteractionVariantsRequest supprimé - système obsolète remplacé par Unity JSON


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
        warning: Avertissement si DummyLLMClient a été utilisé.
    """
    variants: List[DialogueVariantResponse] = Field(..., description="Liste des variantes générées")
    prompt_used: Optional[str] = Field(None, description="Prompt complet utilisé")
    estimated_tokens: int = Field(..., description="Nombre estimé de tokens")
    warning: Optional[str] = Field(None, description="Avertissement (ex: DummyLLMClient utilisé)")


class EstimateTokensRequest(BaseModel):
    """Requête pour estimer le nombre de tokens.
    
    Attributes:
        context_selections: Sélections de contexte GDD.
        user_instructions: Instructions utilisateur (peut être vide si des sélections existent).
        max_context_tokens: Nombre maximum de tokens pour le contexte.
        system_prompt_override: Surcharge du system prompt (optionnel).
        field_configs: Configuration des champs de contexte à inclure (optionnel).
        organization_mode: Mode d'organisation du contexte (optionnel).
    """
    context_selections: ContextSelection = Field(..., description="Sélections de contexte GDD")
    user_instructions: str = Field(default="", description="Instructions utilisateur")
    max_context_tokens: int = Field(default=1500, ge=100, le=Defaults.MAX_CONTEXT_TOKENS, description="Nombre maximum de tokens pour le contexte")
    system_prompt_override: Optional[str] = Field(None, description="Surcharge du system prompt")
    field_configs: Optional[Dict[str, List[str]]] = Field(None, description="Configuration des champs de contexte par type d'élément")
    organization_mode: Optional[str] = Field(None, description="Mode d'organisation du contexte (default, narrative, minimal)")


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


class GenerateUnityDialogueRequest(BaseModel):
    """Requête pour générer un nœud de dialogue au format Unity JSON.
    
    Attributes:
        user_instructions: Instructions spécifiques de l'utilisateur.
        context_selections: Sélections de contexte GDD (doit contenir au moins un personnage).
        npc_speaker_id: ID du PNJ interlocuteur (si None, utiliser le premier personnage sélectionné).
        max_context_tokens: Nombre maximum de tokens pour le contexte.
        system_prompt_override: Surcharge du system prompt (optionnel).
        llm_model_identifier: Identifiant du modèle LLM à utiliser.
        max_choices: Nombre maximum de choix à générer (0-8, ou None pour laisser l'IA décider).
    """
    user_instructions: str = Field(..., min_length=1, description="Instructions spécifiques pour la scène")
    context_selections: ContextSelection = Field(..., description="Sélections de contexte GDD")
    npc_speaker_id: Optional[str] = Field(None, description="ID du PNJ interlocuteur (si None, utiliser le premier personnage sélectionné)")
    max_context_tokens: int = Field(default=1500, ge=100, le=Defaults.MAX_CONTEXT_TOKENS, description="Nombre maximum de tokens pour le contexte")
    system_prompt_override: Optional[str] = Field(None, description="Surcharge du system prompt")
    author_profile: Optional[str] = Field(None, description="Profil d'auteur global (style réutilisable entre scènes)")
    llm_model_identifier: str = Field(default="gpt-5.2-mini", description="Identifiant du modèle LLM")
    max_choices: Optional[int] = Field(None, ge=0, le=8, description="Nombre maximum de choix à générer (0-8, ou None pour laisser l'IA décider librement)")
    narrative_tags: Optional[List[str]] = Field(None, description="Tags narratifs pour guider le ton (ex: tension, humour, dramatique)")
    vocabulary_min_importance: Optional[str] = Field(None, description="Niveau d'importance minimum pour le vocabulaire Alteir (Majeur, Important, Modéré, Secondaire, Mineur, Anecdotique)")
    include_narrative_guides: bool = Field(default=True, description="Inclure les guides narratifs dans le prompt système")
    previous_dialogue_preview: Optional[str] = Field(None, description="Texte formaté du dialogue précédent (généré par preview_unity_dialogue_for_context) pour continuité narrative")


class GenerateUnityDialogueResponse(BaseModel):
    """Réponse pour la génération d'un nœud de dialogue Unity JSON.
    
    Attributes:
        json_content: Contenu JSON du dialogue au format Unity (tableau de nœuds).
        title: Titre descriptif du dialogue généré par l'IA.
        prompt_used: Le prompt complet utilisé pour la génération.
        estimated_tokens: Nombre estimé de tokens utilisés.
        warning: Avertissement si DummyLLMClient a été utilisé.
    """
    json_content: str = Field(..., description="Contenu JSON du dialogue au format Unity")
    title: Optional[str] = Field(None, description="Titre descriptif du dialogue généré par l'IA")
    prompt_used: Optional[str] = Field(None, description="Prompt complet utilisé")
    estimated_tokens: int = Field(..., description="Nombre estimé de tokens")
    warning: Optional[str] = Field(None, description="Avertissement (ex: DummyLLMClient utilisé)")


class ExportUnityDialogueRequest(BaseModel):
    """Requête pour exporter un dialogue Unity JSON vers un fichier.
    
    Attributes:
        json_content: Contenu JSON du dialogue au format Unity (tableau de nœuds).
        title: Titre descriptif du dialogue (utilisé pour générer le nom de fichier).
        filename: Nom de fichier optionnel (si non fourni, généré à partir du titre).
    """
    json_content: str = Field(..., description="Contenu JSON du dialogue au format Unity")
    title: str = Field(..., description="Titre descriptif du dialogue")
    filename: Optional[str] = Field(None, description="Nom de fichier optionnel (sans extension)")


class ExportUnityDialogueResponse(BaseModel):
    """Réponse pour l'export d'un dialogue Unity JSON.
    
    Attributes:
        file_path: Chemin absolu du fichier créé.
        filename: Nom du fichier créé.
        success: Indique si l'export a réussi.
    """
    file_path: str = Field(..., description="Chemin absolu du fichier créé")
    filename: str = Field(..., description="Nom du fichier créé")
    success: bool = Field(..., description="Indique si l'export a réussi")


# Schemas pour la bibliothèque Unity Dialogues
class UnityDialogueMetadata(BaseModel):
    """Métadonnées d'un fichier de dialogue Unity JSON.
    
    Attributes:
        filename: Nom du fichier (avec extension .json).
        file_path: Chemin absolu du fichier.
        size_bytes: Taille du fichier en octets.
        modified_time: Date de modification (ISO format).
        title: Titre extrait depuis le JSON (optionnel).
    """
    filename: str = Field(..., description="Nom du fichier")
    file_path: str = Field(..., description="Chemin absolu du fichier")
    size_bytes: int = Field(..., description="Taille en octets")
    modified_time: str = Field(..., description="Date de modification (ISO format)")
    title: Optional[str] = Field(None, description="Titre extrait du dialogue")


class UnityDialogueListResponse(BaseModel):
    """Réponse pour la liste des dialogues Unity.
    
    Attributes:
        dialogues: Liste des métadonnées des fichiers.
        total: Nombre total de fichiers.
    """
    dialogues: List[UnityDialogueMetadata] = Field(..., description="Liste des métadonnées")
    total: int = Field(..., description="Nombre total de fichiers")


class UnityDialogueReadResponse(BaseModel):
    """Réponse pour la lecture d'un dialogue Unity.
    
    Attributes:
        filename: Nom du fichier.
        json_content: Contenu JSON brut (string).
        title: Titre extrait du dialogue (optionnel).
        size_bytes: Taille du fichier en octets.
        modified_time: Date de modification (ISO format).
    """
    filename: str = Field(..., description="Nom du fichier")
    json_content: str = Field(..., description="Contenu JSON brut")
    title: Optional[str] = Field(None, description="Titre extrait du dialogue")
    size_bytes: int = Field(..., description="Taille en octets")
    modified_time: str = Field(..., description="Date de modification (ISO format)")


class UnityDialoguePreviewRequest(BaseModel):
    """Requête pour générer un preview texte d'un dialogue Unity.
    
    Attributes:
        json_content: Contenu JSON du dialogue Unity.
    """
    json_content: str = Field(..., description="Contenu JSON du dialogue Unity")


class UnityDialoguePreviewResponse(BaseModel):
    """Réponse pour le preview texte d'un dialogue Unity.
    
    Attributes:
        preview_text: Texte formaté pour injection LLM.
        node_count: Nombre de nœuds dans le dialogue.
    """
    preview_text: str = Field(..., description="Texte formaté pour injection LLM")
    node_count: int = Field(..., description="Nombre de nœuds")
