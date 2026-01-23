"""Tests pour les modèles Unity avec 4 résultats de test."""
import pytest
from models.dialogue_structure.unity_dialogue_node import (
    UnityDialogueChoiceContent,
    UnityDialogueNodeContent
)


def test_unity_dialogue_choice_content_2_results_retrocompatibilite():
    """Test rétrocompatibilité : choix avec 2 résultats (testSuccessNode, testFailureNode)."""
    choice_data = {
        "text": "Test choice",
        "test": "Raison+Diplomatie:8",
        "testSuccessNode": "node-success",
        "testFailureNode": "node-failure"
    }
    
    choice = UnityDialogueChoiceContent(**choice_data)
    assert choice.text == "Test choice"
    assert choice.test == "Raison+Diplomatie:8"
    assert choice.testSuccessNode == "node-success"
    assert choice.testFailureNode == "node-failure"
    
    # Sérialisation/désérialisation
    serialized = choice.model_dump()
    deserialized = UnityDialogueChoiceContent(**serialized)
    assert deserialized.testSuccessNode == "node-success"
    assert deserialized.testFailureNode == "node-failure"


def test_unity_dialogue_choice_content_4_results():
    """Test choix avec 4 résultats de test."""
    choice_data = {
        "text": "Test choice",
        "test": "Raison+Diplomatie:8",
        "testCriticalFailureNode": "node-critical-failure",
        "testFailureNode": "node-failure",
        "testSuccessNode": "node-success",
        "testCriticalSuccessNode": "node-critical-success"
    }
    
    choice = UnityDialogueChoiceContent(**choice_data)
    assert choice.text == "Test choice"
    assert choice.test == "Raison+Diplomatie:8"
    assert choice.testCriticalFailureNode == "node-critical-failure"
    assert choice.testFailureNode == "node-failure"
    assert choice.testSuccessNode == "node-success"
    assert choice.testCriticalSuccessNode == "node-critical-success"
    
    # Sérialisation/désérialisation
    serialized = choice.model_dump()
    deserialized = UnityDialogueChoiceContent(**serialized)
    assert deserialized.testCriticalFailureNode == "node-critical-failure"
    assert deserialized.testFailureNode == "node-failure"
    assert deserialized.testSuccessNode == "node-success"
    assert deserialized.testCriticalSuccessNode == "node-critical-success"


def test_unity_dialogue_choice_content_only_critical_results():
    """Test choix avec seulement les résultats critiques."""
    choice_data = {
        "text": "Test choice",
        "test": "Raison+Diplomatie:8",
        "testCriticalFailureNode": "node-critical-failure",
        "testCriticalSuccessNode": "node-critical-success"
    }
    
    choice = UnityDialogueChoiceContent(**choice_data)
    assert choice.testCriticalFailureNode == "node-critical-failure"
    assert choice.testCriticalSuccessNode == "node-critical-success"
    assert choice.testFailureNode is None
    assert choice.testSuccessNode is None
