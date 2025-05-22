from typing import List, Optional, Dict, Any
from .dialogue_elements import AbstractDialogueElement, DialogueLineElement, PlayerChoicesBlockElement, CommandElement

class Interaction:
    def __init__(self, interaction_id: str, elements: Optional[List[AbstractDialogueElement]] = None,
                 header_commands: Optional[List[str]] = None, header_tags: Optional[List[str]] = None,
                 next_interaction_id_if_no_choices: Optional[str] = None, title: str = ""):
        self.interaction_id = interaction_id
        self.elements = elements or []
        self.header_commands = header_commands or []
        self.header_tags = header_tags or []
        self.next_interaction_id_if_no_choices = next_interaction_id_if_no_choices
        self.title = title

    def to_dict(self) -> Dict[str, Any]:
        return {
            "interaction_id": self.interaction_id,
            "elements": [e.to_dict() for e in self.elements],
            "header_commands": self.header_commands,
            "header_tags": self.header_tags,
            "next_interaction_id_if_no_choices": self.next_interaction_id_if_no_choices,
            "title": self.title
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Interaction':
        elements = []
        for elem_data in data.get('elements', []):
            elem_type = elem_data.get('element_type')
            if elem_type == DialogueLineElement.element_type:
                elements.append(DialogueLineElement.from_dict(elem_data))
            elif elem_type == PlayerChoicesBlockElement.element_type:
                elements.append(PlayerChoicesBlockElement.from_dict(elem_data))
            elif elem_type == CommandElement.element_type:
                elements.append(CommandElement.from_dict(elem_data))
            else:
                raise ValueError(f"Type d'élément inconnu: {elem_type}")
        return cls(
            interaction_id=data['interaction_id'],
            elements=elements,
            header_commands=data.get('header_commands'),
            header_tags=data.get('header_tags'),
            next_interaction_id_if_no_choices=data.get('next_interaction_id_if_no_choices'),
            title=data.get('title', "")
        ) 