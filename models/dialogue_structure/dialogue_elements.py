from typing import List, Optional, Union, Literal
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod

class DialogueLineElement(BaseModel):
    element_type: Literal["dialogue_line"] = Field("dialogue_line", description="Type de l'élément : ligne de dialogue.")
    text: str = Field(..., description="Texte du dialogue.")
    speaker: Optional[str] = Field(None, description="Nom du personnage qui parle.")
    tags: List[str] = Field(default_factory=list, description="Tags associés à la ligne.")
    pre_line_commands: List[str] = Field(default_factory=list, description="Commandes à exécuter avant la ligne.")
    post_line_commands: List[str] = Field(default_factory=list, description="Commandes à exécuter après la ligne.")

class PlayerChoiceOption(BaseModel):
    text: str = Field(..., description="Texte de l'option de choix.")
    next_interaction_id: str = Field(..., description="ID de l'interaction suivante si ce choix est sélectionné.")
    condition: Optional[str] = Field(None, description="Condition pour que ce choix soit visible/actif.")
    actions: List[str] = Field(default_factory=list, description="Actions à exécuter si ce choix est sélectionné.")
    tags: List[str] = Field(default_factory=list, description="Tags associés à ce choix.")

class PlayerChoicesBlockElement(BaseModel):
    element_type: Literal["player_choices_block"] = Field("player_choices_block", description="Type de l'élément : bloc de choix pour le joueur.")
    choices: List[PlayerChoiceOption] = Field(default_factory=list, description="Liste des options de choix.")

class CommandElement(BaseModel):
    element_type: Literal["command"] = Field("command", description="Type de l'élément : commande.")
    command_string: str = Field(..., description="La commande à exécuter (ex: '<<wait 1>>').")

AnyDialogueElement = Union[DialogueLineElement, PlayerChoicesBlockElement, CommandElement]

# La classe AbstractDialogueElement n'est plus nécessaire avec Pydantic et Union discriminée
# Si une base commune non-Pydantic est requise pour une autre logique, elle peut être réintroduite,
# mais pour le schéma OpenAI, l'Union est préférable.

# Commentaire original pour référence (supprimé car la logique est maintenant dans Pydantic)
# class AbstractDialogueElement(ABC):
#     element_type: str
# 
#     @abstractmethod
#     def to_dict(self) -> Dict[str, Any]:
#         pass
# 
#     @classmethod
#     @abstractmethod
#     def from_dict(cls, data: Dict[str, Any]) -> 'AbstractDialogueElement':
#         pass

# Vérifications (à faire manuellement ou via tests après) :
# - S'assurer que tous les champs optionnels ont des valeurs par défaut (None ou default_factory).
# - S'assurer que les types sont corrects (List[str] et non Optional[List[str]] si une liste vide est la valeur par défaut).
# - Vérifier que la discrimination fonctionne comme attendu avec element_type. 