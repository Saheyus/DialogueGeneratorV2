import os
import pytest
import tempfile
from pathlib import Path

from models.dialogue_structure import (
    DialogueLineElement, PlayerChoiceOption, PlayerChoicesBlockElement, Interaction
)
from services.yarn_renderer import YarnParser, JinjaYarnRenderer

class TestYarnParser:
    @pytest.fixture
    def yarn_file_content(self):
        """Fixture retournant le contenu d'un fichier Yarn de test."""
        return """title: dialogue_marchand
---
tags: boutique, marchand
<<set $has_visited_shop = true>>
===

Marchand: Bonjour aventurier !
Marchand: Qu'est-ce qui vous amène dans ma boutique ?
-> Je cherche des armes
    <<jump acheter_armes>>
-> Je veux vendre des objets
    <<jump vendre_objets>>
-> Juste en train de regarder
    <<jump fin_dialogue>>
==="""
    
    @pytest.fixture
    def temp_yarn_file(self, yarn_file_content):
        """Fixture créant un fichier Yarn temporaire."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yarn', delete=False, encoding='utf-8') as f:
            f.write(yarn_file_content)
            temp_path = f.name
        
        yield temp_path
        
        # Nettoyage après le test
        try:
            os.unlink(temp_path)
        except (PermissionError, FileNotFoundError):
            pass
    
    def test_parse_string(self, yarn_file_content):
        """Teste le parsing d'une chaîne de caractères Yarn."""
        parser = YarnParser()
        interaction = parser.parse_string(yarn_file_content)
        
        # Vérification que l'interaction a été créée
        assert interaction is not None
        assert interaction.interaction_id == "dialogue_marchand"
        assert "boutique" in interaction.header_tags
        assert "marchand" in interaction.header_tags
        assert "set $has_visited_shop = true" in interaction.header_commands
        
        # Vérification des éléments de dialogue
        assert len(interaction.elements) == 3
        
        # Vérification des lignes de dialogue
        dialogue1 = interaction.elements[0]
        assert isinstance(dialogue1, DialogueLineElement)
        assert dialogue1.speaker == "Marchand"
        assert dialogue1.text == "Bonjour aventurier !"
        
        dialogue2 = interaction.elements[1]
        assert isinstance(dialogue2, DialogueLineElement)
        assert dialogue2.speaker == "Marchand"
        assert dialogue2.text == "Qu'est-ce qui vous amène dans ma boutique ?"
        
        # Vérification des choix
        choices = interaction.elements[2]
        assert isinstance(choices, PlayerChoicesBlockElement)
        assert len(choices.choices) == 3
        
        choice1 = choices.choices[0]
        assert choice1.text == "Je cherche des armes"
        assert choice1.next_interaction_id == "acheter_armes"
        
        choice2 = choices.choices[1]
        assert choice2.text == "Je veux vendre des objets"
        assert choice2.next_interaction_id == "vendre_objets"
        
        choice3 = choices.choices[2]
        assert choice3.text == "Juste en train de regarder"
        assert choice3.next_interaction_id == "fin_dialogue"
    
    def test_parse_file(self, temp_yarn_file):
        """Teste le parsing d'un fichier Yarn."""
        parser = YarnParser()
        interaction = parser.parse_file(temp_yarn_file)
        
        # Vérification de base
        assert interaction is not None
        assert interaction.interaction_id == "dialogue_marchand"
        assert len(interaction.elements) == 3
    
    def test_round_trip(self, yarn_file_content):
        """Teste le cycle complet: parse, puis rendu, puis parse à nouveau."""
        # Première étape: parsing initial
        parser = YarnParser()
        interaction1 = parser.parse_string(yarn_file_content)
        
        # Deuxième étape: rendu
        renderer = JinjaYarnRenderer()
        rendered = renderer.render_to_string(interaction1)
        
        # Troisième étape: parsing du rendu
        interaction2 = parser.parse_string(rendered)
        
        # Vérification que l'interaction a été préservée
        assert interaction2 is not None
        assert interaction2.interaction_id == interaction1.interaction_id
        assert len(interaction2.elements) == len(interaction1.elements)
        
        # Vérification des éléments
        for i in range(len(interaction1.elements)):
            element1 = interaction1.elements[i]
            element2 = interaction2.elements[i]
            
            if isinstance(element1, DialogueLineElement):
                assert isinstance(element2, DialogueLineElement)
                assert element2.speaker == element1.speaker
                assert element2.text == element1.text
            
            elif isinstance(element1, PlayerChoicesBlockElement):
                assert isinstance(element2, PlayerChoicesBlockElement)
                assert len(element2.choices) == len(element1.choices)
                
                for j in range(len(element1.choices)):
                    choice1 = element1.choices[j]
                    choice2 = element2.choices[j]
                    
                    assert choice2.text == choice1.text
                    assert choice2.next_interaction_id == choice1.next_interaction_id 
