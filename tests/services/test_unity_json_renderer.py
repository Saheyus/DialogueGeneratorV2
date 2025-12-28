"""Tests for UnityJsonRenderer."""

import pytest
import json
from pathlib import Path
from typing import List

from services.json_renderer import UnityJsonRenderer
# Imports d'Interaction supprimés - système obsolète


@pytest.fixture
def renderer() -> UnityJsonRenderer:
    """Fixture pour créer un UnityJsonRenderer."""
    return UnityJsonRenderer()


class TestUnityJsonRenderer:
    """Tests pour UnityJsonRenderer."""
    
    # Tests render_interactions supprimés - système obsolète
    
    def test_normalize_node_removes_empty_fields(self, renderer: UnityJsonRenderer):
        """Test que la normalisation supprime les champs vides."""
        node = {
            "id": "TEST_NODE_1",
            "speaker": "CHARACTER_A",
            "line": "Hello",
            "empty_string": "",
            "empty_list": [],
            "empty_dict": {},
            "false_value": False,
            "zero_value": 0
        }
        
        normalized = renderer._normalize_node(node)
        
        assert "empty_string" not in normalized  # Chaîne vide supprimée
        assert "empty_list" not in normalized  # Liste vide supprimée
        assert "empty_dict" not in normalized  # Dict vide supprimé
        assert "false_value" not in normalized  # False supprimé
        assert "zero_value" not in normalized  # 0 supprimé
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
    
    def test_validate_nodes_success(self, renderer: UnityJsonRenderer):
        """Test de validation réussie."""
        nodes = [
            {
                "id": "NODE_1",
                "speaker": "CHAR",
                "line": "First",
                "choices": [
                    {
                        "text": "Go to 2",
                        "targetNode": "NODE_2"
                    }
                ]
            },
            {
                "id": "NODE_2",
                "speaker": "CHAR",
                "line": "Second",
                "nextNode": "NODE_3"
            },
            {
                "id": "NODE_3",
                "speaker": "CHAR",
                "line": "Third"
            }
        ]
        
        is_valid, errors = renderer.validate_nodes(nodes)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_nodes_duplicate_ids(self, renderer: UnityJsonRenderer):
        """Test de validation avec IDs dupliqués."""
        nodes = [
            {"id": "NODE_1", "speaker": "CHAR", "line": "First"},
            {"id": "NODE_1", "speaker": "CHAR", "line": "Duplicate"}  # Même ID
        ]
        
        is_valid, errors = renderer.validate_nodes(nodes)
        
        assert is_valid is False
        assert any("dupliqués" in error.lower() or "duplicate" in error.lower() for error in errors)
    
    def test_validate_nodes_invalid_reference(self, renderer: UnityJsonRenderer):
        """Test de validation avec référence invalide."""
        nodes = [
            {
                "id": "NODE_1",
                "nextNode": "NONEXISTENT_NODE"
            }
        ]
        
        is_valid, errors = renderer.validate_nodes(nodes)
        
        assert is_valid is False
        assert any("NONEXISTENT_NODE" in error for error in errors)
    
    def test_validate_nodes_empty_list(self, renderer: UnityJsonRenderer):
        """Test de validation avec liste vide."""
        is_valid, errors = renderer.validate_nodes([])
        
        assert is_valid is False
        assert any("au moins un nœud" in error.lower() or "at least" in error.lower() for error in errors)
    
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
    
    def test_render_unity_nodes(self, renderer: UnityJsonRenderer):
        """Test de rendu de nœuds Unity en JSON."""
        nodes = [
            {
                "id": "START",
                "speaker": "TEST_NPC",
                "line": "Hello",
                "choices": [
                    {
                        "text": "Choice 1",
                        "targetNode": "END"
                    }
                ]
            }
        ]
        
        json_str = renderer.render_unity_nodes(nodes, normalize=True)
        
        # Vérifier que c'est du JSON valide
        parsed = json.loads(json_str)
        assert isinstance(parsed, list)
        assert len(parsed) == 1
        assert parsed[0]["id"] == "START"
        assert parsed[0]["speaker"] == "TEST_NPC"
        assert parsed[0]["line"] == "Hello"
        assert len(parsed[0]["choices"]) == 1
        assert parsed[0]["choices"][0]["targetNode"] == "END"
    
    def test_render_unity_nodes_validation_error(self, renderer: UnityJsonRenderer):
        """Test que render_unity_nodes lève une erreur si la validation échoue."""
        nodes = [
            {
                "id": "NODE_1",
                "nextNode": "NONEXISTENT_NODE"
            }
        ]
        
        with pytest.raises(ValueError, match="Erreurs de validation"):
            renderer.render_unity_nodes(nodes)
