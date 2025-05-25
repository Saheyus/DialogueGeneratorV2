import pytest
from models.dialogue_structure.dialogue_elements import (
    DialogueLineElement, PlayerChoiceOption, PlayerChoicesBlockElement, CommandElement
)
from models.dialogue_structure.interaction import Interaction

def test_dialogue_line_element_serialization():
    elem = DialogueLineElement(
        text="Bonjour !", speaker="PNJ", tags=["intro"],
        pre_line_commands=["set $a = 1"], post_line_commands=["set $b = 2"]
    )
    d = elem.model_dump()
    elem2 = DialogueLineElement.model_validate(d)
    assert elem2.text == elem.text
    assert elem2.speaker == elem.speaker
    assert elem2.tags == elem.tags
    assert elem2.pre_line_commands == elem.pre_line_commands
    assert elem2.post_line_commands == elem.post_line_commands

def test_player_choice_option_serialization():
    opt = PlayerChoiceOption(
        text="Choix 1", next_interaction_id="Node2",
        condition="<<if $ok>>", actions=["set $ok = false"], tags=["important"]
    )
    d = opt.model_dump()
    opt2 = PlayerChoiceOption.model_validate(d)
    assert opt2.text == opt.text
    assert opt2.next_interaction_id == opt.next_interaction_id
    assert opt2.condition == opt.condition
    assert opt2.actions == opt.actions
    assert opt2.tags == opt.tags

def test_player_choices_block_element_serialization():
    opt1 = PlayerChoiceOption(text="A", next_interaction_id="NodeA")
    opt2 = PlayerChoiceOption(text="B", next_interaction_id="NodeB", condition="<<if $b>>")
    block = PlayerChoicesBlockElement(choices=[opt1, opt2])
    d = block.model_dump()
    block2 = PlayerChoicesBlockElement.model_validate(d)
    assert len(block2.choices) == 2
    assert block2.choices[0].text == "A"
    assert block2.choices[1].condition == "<<if $b>>"

def test_command_element_serialization():
    cmd = CommandElement(command_string="set $x = 1")
    d = cmd.model_dump()
    cmd2 = CommandElement.model_validate(d)
    assert cmd2.command_string == cmd.command_string

def test_interaction_serialization():
    elem1 = DialogueLineElement(text="Bonjour", speaker="PNJ")
    elem2 = CommandElement(command_string="set $x = 1")
    opt = PlayerChoiceOption(text="Aller", next_interaction_id="Node2")
    block = PlayerChoicesBlockElement(choices=[opt])
    interaction = Interaction(
        interaction_id="Node1",
        elements=[elem1, elem2, block],
        header_commands=["set $start = true"],
        header_tags=["intro"],
        next_interaction_id_if_no_choices="Node2"
    )
    d = interaction.model_dump()
    interaction2 = Interaction.model_validate(d)
    assert interaction2.interaction_id == interaction.interaction_id
    assert len(interaction2.elements) == 3
    assert interaction2.header_commands == ["set $start = true"]
    assert interaction2.header_tags == ["intro"]
    assert interaction2.next_interaction_id_if_no_choices == "Node2" 
