"""Schémas Pydantic pour l'API de gestion de graphes."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class LoadGraphRequest(BaseModel):
    """Requête pour charger un dialogue Unity JSON et le convertir en graphe."""
    json_content: str = Field(..., description="Contenu JSON Unity (tableau de nœuds)")


class GraphMetadata(BaseModel):
    """Métadonnées d'un graphe."""
    title: str = Field(..., description="Titre du dialogue")
    node_count: int = Field(..., description="Nombre de nœuds")
    edge_count: int = Field(..., description="Nombre de connexions")
    filename: Optional[str] = Field(None, description="Nom du fichier (si sauvegardé)")


class LoadGraphResponse(BaseModel):
    """Réponse après chargement d'un graphe."""
    nodes: List[Dict[str, Any]] = Field(..., description="Nœuds ReactFlow")
    edges: List[Dict[str, Any]] = Field(..., description="Edges ReactFlow")
    metadata: GraphMetadata = Field(..., description="Métadonnées du graphe")


class SaveGraphRequest(BaseModel):
    """Requête pour sauvegarder un graphe modifié."""
    nodes: List[Dict[str, Any]] = Field(..., description="Nœuds ReactFlow")
    edges: List[Dict[str, Any]] = Field(..., description="Edges ReactFlow")
    metadata: GraphMetadata = Field(..., description="Métadonnées du graphe")


class SaveGraphResponse(BaseModel):
    """Réponse après sauvegarde d'un graphe."""
    success: bool = Field(..., description="Succès de l'opération")
    filename: str = Field(..., description="Nom du fichier sauvegardé")
    json_content: str = Field(..., description="Contenu Unity JSON généré")


class GenerateNodeRequest(BaseModel):
    """Requête pour générer un nœud en contexte."""
    parent_node_id: str = Field(..., description="ID du nœud parent")
    parent_node_content: Dict[str, Any] = Field(..., description="Contenu du nœud parent (pour contexte)")
    user_instructions: str = Field(..., description="Instructions pour guider l'IA")
    context_selections: Dict[str, Any] = Field(..., description="Sélection de contexte GDD")
    max_choices: Optional[int] = Field(None, description="Nombre maximum de choix (0-8)")
    npc_speaker_id: Optional[str] = Field(None, description="ID du PNJ interlocuteur")
    system_prompt_override: Optional[str] = Field(None, description="Surcharge du system prompt")
    narrative_tags: Optional[List[str]] = Field(None, description="Tags narratifs")
    llm_model_identifier: Optional[str] = Field(None, description="Identifiant du modèle LLM")
    target_choice_index: Optional[int] = Field(None, description="Index du choix spécifique à connecter (si None, génère pour tous les choix sans targetNode)")
    generate_all_choices: bool = Field(False, description="Si True, génère un nœud pour chaque choix sans targetNode")


class SuggestedConnection(BaseModel):
    """Connexion suggérée entre nœuds."""
    from_node: str = Field(..., description="ID du nœud source", alias="from")
    to_node: str = Field(..., description="ID du nœud cible", alias="to")
    via_choice_index: Optional[int] = Field(None, description="Index du choix (si applicable)")
    connection_type: str = Field("choice", description="Type de connexion (choice, nextNode, success, failure)")


class GenerateNodeResponse(BaseModel):
    """Réponse après génération d'un nœud."""
    node: Dict[str, Any] = Field(..., description="Nœud généré (avec ID)")
    suggested_connections: List[SuggestedConnection] = Field(..., description="Connexions suggérées")
    parent_node_id: str = Field(..., description="ID du nœud parent")


class ValidateGraphRequest(BaseModel):
    """Requête pour valider un graphe."""
    nodes: List[Dict[str, Any]] = Field(..., description="Nœuds ReactFlow")
    edges: List[Dict[str, Any]] = Field(..., description="Edges ReactFlow")


class ValidationErrorDetail(BaseModel):
    """Détail d'une erreur de validation."""
    type: str = Field(..., description="Type d'erreur")
    node_id: Optional[str] = Field(None, description="ID du nœud concerné")
    message: str = Field(..., description="Message d'erreur")
    severity: str = Field("error", description="Sévérité (error, warning)")
    target: Optional[str] = Field(None, description="Cible de la référence (si applicable)")


class ValidateGraphResponse(BaseModel):
    """Réponse après validation d'un graphe."""
    valid: bool = Field(..., description="True si aucune erreur")
    errors: List[ValidationErrorDetail] = Field(..., description="Liste des erreurs")
    warnings: List[ValidationErrorDetail] = Field(..., description="Liste des warnings")


class CalculateLayoutRequest(BaseModel):
    """Requête pour calculer un layout automatique."""
    nodes: List[Dict[str, Any]] = Field(..., description="Nœuds ReactFlow")
    edges: List[Dict[str, Any]] = Field(..., description="Edges ReactFlow")
    algorithm: str = Field("dagre", description="Algorithme de layout (dagre, manual)")
    direction: str = Field("TB", description="Direction (TB, LR, BT, RL)")


class CalculateLayoutResponse(BaseModel):
    """Réponse après calcul de layout."""
    nodes: List[Dict[str, Any]] = Field(..., description="Nœuds avec positions calculées")
