from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

class AbstractDialogueElement(ABC):
    element_type: str

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AbstractDialogueElement':
        pass

class DialogueLineElement(AbstractDialogueElement):
    element_type: str = "dialogue_line"

    def __init__(self, text: str, speaker: Optional[str] = None, tags: Optional[List[str]] = None,
                 pre_line_commands: Optional[List[str]] = None, post_line_commands: Optional[List[str]] = None):
        self.speaker = speaker
        self.text = text
        self.tags = tags or []
        self.pre_line_commands = pre_line_commands or []
        self.post_line_commands = post_line_commands or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "element_type": self.element_type,
            "speaker": self.speaker,
            "text": self.text,
            "tags": self.tags,
            "pre_line_commands": self.pre_line_commands,
            "post_line_commands": self.post_line_commands
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DialogueLineElement':
        return cls(
            text=data['text'],
            speaker=data.get('speaker'),
            tags=data.get('tags'),
            pre_line_commands=data.get('pre_line_commands'),
            post_line_commands=data.get('post_line_commands')
        )

class PlayerChoiceOption:
    def __init__(self, text: str, next_interaction_id: str, condition: Optional[str] = None,
                 actions: Optional[List[str]] = None, tags: Optional[List[str]] = None):
        self.text = text
        self.next_interaction_id = next_interaction_id
        self.condition = condition
        self.actions = actions or []
        self.tags = tags or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "next_interaction_id": self.next_interaction_id,
            "condition": self.condition,
            "actions": self.actions,
            "tags": self.tags
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlayerChoiceOption':
        return cls(
            text=data['text'],
            next_interaction_id=data['next_interaction_id'],
            condition=data.get('condition'),
            actions=data.get('actions'),
            tags=data.get('tags')
        )

class PlayerChoicesBlockElement(AbstractDialogueElement):
    element_type: str = "player_choices_block"

    def __init__(self, choices: Optional[List[PlayerChoiceOption]] = None):
        self.choices = choices or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "element_type": self.element_type,
            "choices": [choice.to_dict() for choice in self.choices]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlayerChoicesBlockElement':
        return cls(
            choices=[PlayerChoiceOption.from_dict(c) for c in data.get('choices', [])]
        )

class CommandElement(AbstractDialogueElement):
    element_type: str = "command"

    def __init__(self, command_string: str):
        self.command_string = command_string

    def to_dict(self) -> Dict[str, Any]:
        return {
            "element_type": self.element_type,
            "command_string": self.command_string
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommandElement':
        return cls(command_string=data['command_string']) 