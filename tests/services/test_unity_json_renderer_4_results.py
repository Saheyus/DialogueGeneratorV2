"""Tests pour UnityJsonRenderer avec 4 résultats de test."""
import pytest
from services.json_renderer import UnityJsonRenderer


@pytest.fixture
def renderer() -> UnityJsonRenderer:
    """Fixture pour créer un UnityJsonRenderer."""
    return UnityJsonRenderer()


def test_validate_nodes_accepts_4_test_results():
    """Test que validate_nodes accepte les 4 résultats de test valides.
    
    AC: #4 - Validation des 4 champs test*Node.
    """
    # GIVEN: Nœuds avec choix contenant les 4 résultats de test
    nodes = [
        {
            "id": "START",
            "speaker": "PNJ",
            "line": "Bonjour",
            "choices": [
                {
                    "text": "Tenter de convaincre",
                    "test": "Raison+Diplomatie:8",
                    "testCriticalFailureNode": "NODE_CRITICAL_FAILURE",
                    "testFailureNode": "NODE_FAILURE",
                    "testSuccessNode": "NODE_SUCCESS",
                    "testCriticalSuccessNode": "NODE_CRITICAL_SUCCESS",
                }
            ]
        },
        {
            "id": "NODE_CRITICAL_FAILURE",
            "speaker": "PNJ",
            "line": "Réponse échec critique",
        },
        {
            "id": "NODE_FAILURE",
            "speaker": "PNJ",
            "line": "Réponse échec",
        },
        {
            "id": "NODE_SUCCESS",
            "speaker": "PNJ",
            "line": "Réponse réussite",
        },
        {
            "id": "NODE_CRITICAL_SUCCESS",
            "speaker": "PNJ",
            "line": "Réponse réussite critique",
        },
    ]
    
    # WHEN: Validation
    renderer = UnityJsonRenderer()
    is_valid, errors = renderer.validate_nodes(nodes)
    
    # THEN: Validation doit réussir
    assert is_valid is True
    assert len(errors) == 0


def test_validate_nodes_detects_invalid_test_critical_failure_reference():
    """Test que validate_nodes détecte une référence invalide pour testCriticalFailureNode."""
    # GIVEN: Nœud avec référence invalide
    nodes = [
        {
            "id": "START",
            "speaker": "PNJ",
            "line": "Bonjour",
            "choices": [
                {
                    "text": "Tenter de convaincre",
                    "test": "Raison+Diplomatie:8",
                    "testCriticalFailureNode": "NONEXISTENT_NODE",
                }
            ]
        },
    ]
    
    # WHEN: Validation
    renderer = UnityJsonRenderer()
    is_valid, errors = renderer.validate_nodes(nodes)
    
    # THEN: Validation doit échouer avec message d'erreur approprié
    assert is_valid is False
    assert any("testCriticalFailureNode" in error for error in errors)
    assert any("NONEXISTENT_NODE" in error for error in errors)


def test_validate_nodes_detects_invalid_test_critical_success_reference():
    """Test que validate_nodes détecte une référence invalide pour testCriticalSuccessNode."""
    # GIVEN: Nœud avec référence invalide
    nodes = [
        {
            "id": "START",
            "speaker": "PNJ",
            "line": "Bonjour",
            "choices": [
                {
                    "text": "Tenter de convaincre",
                    "test": "Raison+Diplomatie:8",
                    "testCriticalSuccessNode": "INVALID_NODE",
                }
            ]
        },
    ]
    
    # WHEN: Validation
    renderer = UnityJsonRenderer()
    is_valid, errors = renderer.validate_nodes(nodes)
    
    # THEN: Validation doit échouer avec message d'erreur approprié
    assert is_valid is False
    assert any("testCriticalSuccessNode" in error for error in errors)
    assert any("INVALID_NODE" in error for error in errors)


def test_validate_nodes_retrocompatibilite_2_results():
    """Test rétrocompatibilité : validate_nodes avec seulement 2 résultats (success/failure)."""
    # GIVEN: Nœuds avec seulement testSuccessNode et testFailureNode
    nodes = [
        {
            "id": "START",
            "speaker": "PNJ",
            "line": "Bonjour",
            "choices": [
                {
                    "text": "Tenter de convaincre",
                    "test": "Raison+Diplomatie:8",
                    "testFailureNode": "NODE_FAILURE",
                    "testSuccessNode": "NODE_SUCCESS",
                }
            ]
        },
        {
            "id": "NODE_FAILURE",
            "speaker": "PNJ",
            "line": "Échec",
        },
        {
            "id": "NODE_SUCCESS",
            "speaker": "PNJ",
            "line": "Réussite",
        },
    ]
    
    # WHEN: Validation
    renderer = UnityJsonRenderer()
    is_valid, errors = renderer.validate_nodes(nodes)
    
    # THEN: Validation doit réussir (rétrocompatibilité)
    assert is_valid is True
    assert len(errors) == 0
