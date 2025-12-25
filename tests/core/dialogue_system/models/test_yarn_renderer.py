import os
import pytest
import tempfile
from pathlib import Path

from models.dialogue_structure import (
    DialogueLineElement, PlayerChoiceOption, PlayerChoicesBlockElement, Interaction
)
from services.yarn_renderer import JinjaYarnRenderer

class TestJinjaYarnRenderer:
    @pytest.fixture
    def sample_interaction(self):
        """Fixture créant une interaction de test."""
        line1 = DialogueLineElement(text="Bonjour aventurier !", speaker="Marchand")
        line2 = DialogueLineElement(text="Qu'est-ce qui vous amène dans ma boutique ?", speaker="Marchand")
        
        choice1 = PlayerChoiceOption(text="Je cherche des armes", next_interaction_id="acheter_armes")
        choice2 = PlayerChoiceOption(text="Je veux vendre des objets", next_interaction_id="vendre_objets")
        choice3 = PlayerChoiceOption(text="Juste en train de regarder", next_interaction_id="fin_dialogue")
        
        choices = PlayerChoicesBlockElement(choices=[choice1, choice2, choice3])
        
        return Interaction(
            interaction_id="dialogue_marchand",
            elements=[line1, line2, choices],
            header_tags=["boutique", "marchand"],
            header_commands=["set $has_visited_shop = true"]
        )
    
    @pytest.fixture
    def renderer(self):
        """Fixture créant un renderer avec un dossier temporaire."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield JinjaYarnRenderer(template_dir=temp_dir)
    
    def test_render_to_string(self, renderer, sample_interaction):
        """Teste le rendu d'une interaction en chaîne de caractères."""
        result = renderer.render_to_string(sample_interaction)
        
        # Affichage du résultat pour débogage
        print("\nRésultat du rendu:")
        print(result)
        print("-" * 50)
        
        # Vérification des éléments attendus dans le rendu
        assert "title: dialogue_marchand" in result
        assert "tags: boutique, marchand" in result
        assert "<<set $has_visited_shop = true>>" in result
        assert "Marchand: Bonjour aventurier !" in result
        assert "Marchand: Qu'est-ce qui vous amène dans ma boutique ?" in result
        assert "-> Je cherche des armes" in result
        assert "<<jump acheter_armes>>" in result
        assert "-> Je veux vendre des objets" in result
        assert "<<jump vendre_objets>>" in result
        assert "-> Juste en train de regarder" in result
        assert "<<jump fin_dialogue>>" in result
    
    def test_render_to_file(self, renderer, sample_interaction):
        """Teste le rendu d'une interaction dans un fichier."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_dialogue.yarn")
            
            # Rendu dans un fichier
            renderer.render_to_file(sample_interaction, output_path)
            
            # Vérification que le fichier existe
            assert os.path.exists(output_path)
            
            # Lecture du fichier et vérification du contenu
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            assert "title: dialogue_marchand" in content
            assert "tags: boutique, marchand" in content
            assert "Marchand: Bonjour aventurier !" in content
    
    def test_template_variables(self, renderer):
        """Teste la gestion des variables de template."""
        # Définition de variables
        variables = {
            'game_version': '1.0.0',
            'author': 'Test Author'
        }
        
        renderer.set_template_variables(variables)
        
        # Vérification que les variables sont correctement stockées
        assert renderer.get_template_variables() == variables
        
        # Vérification que les modifications du dictionnaire original n'affectent pas le renderer
        variables['game_version'] = '2.0.0'
        assert renderer.get_template_variables()['game_version'] == '1.0.0' 
