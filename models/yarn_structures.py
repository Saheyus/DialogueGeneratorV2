from typing import Optional, List
from pydantic import BaseModel, Field

class YarnNode(BaseModel):
    """
    Represents a single node in a Yarn Spinner dialogue file.
    """
    title: str = Field(
        ...,
        description="The title of the dialogue node. Must be unique within a Yarn file.",
        pattern=r"^[A-Za-z0-9_]+$"  # Simplifié pour éviter les espaces pour l'instant, plus robuste pour les titres.
    )
    tags: Optional[List[str]] = Field(
        default_factory=list,
        description="A list of tags associated with the node, used for categorization or conditional logic."
    )
    body: List[str] = Field(
        ...,
        description="The content of the dialogue node, as a list of strings. Each string is a line (dialogue, command, etc.).",
        min_length=1 # Pydantic v2 utilise min_length, pour Pydantic v1 c'était min_items
    )
    # Future fields à considérer:
    # character: Optional[str] = Field(default=None, description="The character speaking, if applicable for the entire node or default.")
    # conditions: Optional[List[str]] = Field(default_factory=list, description="Conditions for this node to be active.")
    # metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata like line IDs for localization.")

class YarnScene(BaseModel):
    """
    Represents a collection of YarnNodes, typically corresponding to a single .yarn file or a coherent scene.
    """
    nodes: List[YarnNode] = Field(
        ...,
        description="A list of YarnNode objects that make up the scene."
    )

    # Potentially add scene-level metadata here if needed in the future
    # scene_title: Optional[str] = Field(default=None, description="An optional title for the entire scene/file.") 