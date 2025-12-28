"""Tests for UnityJsonRenderer."""

import pytest
import json
from pathlib import Path
from typing import List

from services.json_renderer import UnityJsonRenderer
from models.dialogue_structure import (
    Interaction,
    DialogueLineElement,
    PlayerChoicesBlockElement,
    PlayerChoiceOption,
)


@pytest.fixture
def renderer() -> UnityJsonRenderer:
    """Fixture pour créer un UnityJsonRenderer."""
    return UnityJsonRenderer()


@pytest.fixture
def sample_interaction() -> Interaction:
    """Fixture pour créer une Interaction de test."""
    return Interaction(
        interaction_id="TEST_NODE_1",
        title="Test Interaction",
        elements=[
            DialogueLineElement(
                element_type="dialogue_line",
                text="Hello, this is a test dialogue.",
                speaker="CHARACTER_A"
            ),
            PlayerChoicesBlockElement(
                element_type="player_choices_block",
                choices=[
                    PlayerChoiceOption(
                        text="Choice 1",
                        next_interaction_id="TEST_NODE_2"
                    ),
                    PlayerChoiceOption(
                        text="Choice 2",
                        next_interaction_id="TEST_NODE_3"
                    )
                ]
            )
        ],
        next_interaction_id_if_no_choices=None
    )


@pytest.fixture
def sample_interaction_with_next() -> Interaction:
    """Fixture pour créer une Interaction avec nextNode."""
    return Interaction(
        interaction_id="TEST_NODE_2",
        title="Test Interaction 2",
        elements=[
            DialogueLineElement(
                element_type="dialogue_line",
                text="This is the next dialogue.",
                speaker="CHARACTER_B"
            )
        ],
        next_interaction_id_if_no_choices="TEST_NODE_3"
    )


class TestUnityJsonRenderer:
    """Tests pour UnityJsonRenderer."""
    
    def test_render_single_interaction(self, renderer: UnityJsonRenderer, sample_interaction: Interaction):
        """Test de conversion d'une seule Interaction en JSON Unity."""
        nodes = renderer.render_interactions([sample_interaction])
        
        assert len(nodes) == 1
        node = nodes[0]
        
        assert node["id"] == "TEST_NODE_1"
        assert node["speaker"] == "CHARACTER_A"
        assert node["line"] == "Hello, this is a test dialogue."
        assert "choices" in node
        assert len(node["choices"]) == 2
        assert node["choices"][0]["text"] == "Choice 1"
        assert node["choices"][0]["targetNode"] == "TEST_NODE_2"
    
    def test_render_multiple_interactions(self, renderer: UnityJsonRenderer, sample_interaction: Interaction, sample_interaction_with_next: Interaction):
        """Test de conversion de plusieurs Interactions."""
        nodes = renderer.render_interactions([sample_interaction, sample_interaction_with_next])
        
        assert len(nodes) == 2
        assert nodes[0]["id"] == "TEST_NODE_1"
        assert nodes[1]["id"] == "TEST_NODE_2"
        assert nodes[1]["nextNode"] == "TEST_NODE_3"
    
    def test_normalize_node_removes_empty_fields(self, renderer: UnityJsonRenderer, sample_interaction: Interaction):
        """Test que la normalisation supprime les champs vides."""
        nodes = renderer.render_interactions([sample_interaction])
        node = nodes[0]
        
        # Ajouter des champs vides pour tester la normalisation
        node["test"] = ""
        node["cutsceneMode"] = False
        node["isLongRest"] = False
        
        normalized = renderer._normalize_node(node)
        
        assert "test" not in normalized  # Chaîne vide supprimée
        assert "cutsceneMode" not in normalized  # False supprimé
        assert "isLongRest" not in normalized  # False supprimé
        assert "id" in normalized  # id toujours présent
        assert "speaker" in normalized
        assert "line" in normalized
    
    def test_normalize_preserves_id_and_targetnode(self, renderer: UnityJsonRenderer):
        """Test que id et targetNode sont toujours conservés même vides."""
        node = {
            "id": "",
            "targetNode": "",
            "speaker": "TEST"
        }
        
        normalized = renderer._normalize_node(node)
        
        assert "id" in normalized
        assert "targetNode" in normalized
        assert normalized["id"] == ""
        assert normalized["targetNode"] == ""
    
    def test_render_to_string_format(self, renderer: UnityJsonRenderer, sample_interaction: Interaction):
        """Test que render_to_string produit un JSON valide et formaté."""
        json_str = renderer.render_interactions_to_string([sample_interaction])
        
        # Vérifier que c'est du JSON valide
        parsed = json.loads(json_str)
        assert isinstance(parsed, list)
        assert len(parsed) == 1
        
        # Vérifier le format (indentation)
        lines = json_str.split('\n')
        assert lines[0].strip() == '['
        assert lines[1].strip().startswith('{')
    
    def test_render_to_file(self, renderer: UnityJsonRenderer, sample_interaction: Interaction, tmp_path: Path):
        """Test d'export vers fichier."""
        output_file = tmp_path / "test_output.json"
        
        renderer.render_interactions_to_file([sample_interaction], output_file)
        
        assert output_file.exists()
        
        # Vérifier le contenu
        content = output_file.read_text(encoding='utf-8')
        parsed = json.loads(content)
        assert len(parsed) == 1
        assert parsed[0]["id"] == "TEST_NODE_1"
    
    def test_validate_nodes_success(self, renderer: UnityJsonRenderer):
        """Test de validation réussie."""
        # Créer des interactions avec des références valides
        interaction1 = Interaction(
            interaction_id="NODE_1",
            elements=[
                DialogueLineElement(
                    element_type="dialogue_line",
                    text="First",
                    speaker="CHAR"
                ),
                PlayerChoicesBlockElement(
                    element_type="player_choices_block",
                    choices=[
                        PlayerChoiceOption(
                            text="Go to 2",
                            next_interaction_id="NODE_2"
                        )
                    ]
                )
            ]
        )
        interaction2 = Interaction(
            interaction_id="NODE_2",
            elements=[
                DialogueLineElement(
                    element_type="dialogue_line",
                    text="Second",
                    speaker="CHAR"
                )
            ],
            next_interaction_id_if_no_choices="NODE_3"
        )
        interaction3 = Interaction(
            interaction_id="NODE_3",
            elements=[
                DialogueLineElement(
                    element_type="dialogue_line",
                    text="Third",
                    speaker="CHAR"
                )
            ]
        )
        
        nodes = renderer.render_interactions([interaction1, interaction2, interaction3])
        
        is_valid, errors = renderer.validate_nodes(nodes)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_nodes_duplicate_ids(self, renderer: UnityJsonRenderer, sample_interaction: Interaction):
        """Test de validation avec IDs dupliqués."""
        # Créer deux interactions avec le même ID
        interaction2 = Interaction(
            interaction_id="TEST_NODE_1",  # Même ID
            title="Duplicate",
            elements=[]
        )
        
        with pytest.raises(ValueError, match="dupliqués"):
            renderer.render_interactions([sample_interaction, interaction2])
    
    def test_validate_nodes_invalid_reference(self, renderer: UnityJsonRenderer):
        """Test de validation avec référence invalide."""
        interaction = Interaction(
            interaction_id="NODE_1",
            elements=[],
            next_interaction_id_if_no_choices="NONEXISTENT_NODE"
        )
        
        nodes = renderer.render_interactions([interaction])
        is_valid, errors = renderer.validate_nodes(nodes)
        
        # La validation devrait détecter la référence invalide
        # Note: Le renderer log un warning mais ne lève pas d'exception
        # La validation explicite devrait retourner des erreurs
        assert is_valid is False
        assert any("NONEXISTENT_NODE" in error for error in errors)
    
    def test_validate_nodes_empty_list(self, renderer: UnityJsonRenderer):
        """Test de validation avec liste vide."""
        is_valid, errors = renderer.validate_nodes([])
        
        assert is_valid is False
        assert any("au moins un nœud" in error.lower() or "at least" in error.lower() for error in errors)
    
    def test_multiple_dialogue_lines_concat(self, renderer: UnityJsonRenderer):
        """Test avec plusieurs lignes de dialogue (devraient être concaténées)."""
        interaction = Interaction(
            interaction_id="MULTI_LINE",
            elements=[
                DialogueLineElement(
                    element_type="dialogue_line",
                    text="First line.",
                    speaker="CHAR"
                ),
                DialogueLineElement(
                    element_type="dialogue_line",
                    text="Second line.",
                    speaker="CHAR"
                )
            ]
        )
        
        nodes = renderer.render_interactions([interaction])
        node = nodes[0]
        
        # Les lignes devraient être concaténées avec \n
        assert "\n" in node["line"]
        assert "First line." in node["line"]
        assert "Second line." in node["line"]
    
    def test_interaction_without_speaker(self, renderer: UnityJsonRenderer):
        """Test avec Interaction sans speaker."""
        interaction = Interaction(
            interaction_id="NO_SPEAKER",
            elements=[
                DialogueLineElement(
                    element_type="dialogue_line",
                    text="Text without speaker",
                    speaker=None
                )
            ]
        )
        
        nodes = renderer.render_interactions([interaction])
        node = nodes[0]
        
        assert "speaker" not in node
        assert node["line"] == "Text without speaker"
    
    def test_validate_nodes_accepts_end_special_node(self, renderer: UnityJsonRenderer):
        """Test que le validateur accepte "END" comme nœud spécial même s'il n'est pas dans la liste.
        
        "END" est un nœud terminal spécial reconnu par Unity pour terminer le dialogue.
        Il peut être référencé même s'il n'est pas présent explicitement dans le JSON.
        """
        # Créer un nœud qui pointe vers "END" sans créer le nœud END
        node_with_end = {
            "id": "START",
            "speaker": "TEST_NPC",
            "line": "Test dialogue",
            "choices": [
                {
                    "text": "Choice 1",
                    "targetNode": "END"
                },
                {
                    "text": "Choice 2",
                    "targetNode": "END"
                }
            ]
        }
        
        # Valider : "END" devrait être accepté même s'il n'est pas dans la liste
        is_valid, errors = renderer.validate_nodes([node_with_end])
        
        assert is_valid is True
        assert len(errors) == 0
        # "END" est reconnu comme nœud spécial valide

