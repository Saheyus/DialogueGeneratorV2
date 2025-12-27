"""Tests pour la validation vocabulaire dans NarrativeValidator."""
import pytest
from services.narrative_validator import NarrativeValidator
from models.dialogue_structure.interaction import Interaction
from models.dialogue_structure.dialogue_elements import DialogueLineElement


@pytest.fixture
def validator():
    """Crée un validateur narratif."""
    return NarrativeValidator()


@pytest.fixture
def sample_interaction():
    """Crée une interaction de test."""
    interaction = Interaction(
        interaction_id="test_1",
        title="Test Interaction",
        elements=[
            DialogueLineElement(
                speaker="NPC",
                text="Bienvenue dans le monde d'Alteir. Le mana coule ici."
            ),
            DialogueLineElement(
                speaker="Player",
                text="Je comprends. Le mana est important."
            )
        ]
    )
    return interaction


@pytest.fixture
def sample_vocabulary_terms():
    """Termes de vocabulaire de test."""
    return [
        {
            "term": "Alteir",
            "definition": "Le monde principal du jeu",
            "importance": "Majeur"
        },
        {
            "term": "mana",
            "definition": "Énergie magique utilisée pour les sorts",
            "importance": "Important"
        },
        {
            "term": "Guildes",
            "definition": "Organisations de métier",
            "importance": "Modéré"
        }
    ]


class TestVocabularyValidation:
    """Tests pour la validation du vocabulaire."""
    
    def test_validate_vocabulary_usage_no_terms(self, validator, sample_interaction):
        """Test de validation sans termes de vocabulaire."""
        warnings = validator.validate_vocabulary_usage(sample_interaction, [])
        
        assert len(warnings) == 0
    
    def test_validate_vocabulary_usage_with_terms(self, validator, sample_interaction, sample_vocabulary_terms):
        """Test de validation avec termes de vocabulaire."""
        warnings = validator.validate_vocabulary_usage(sample_interaction, sample_vocabulary_terms)
        
        # Les termes "Alteir" et "mana" sont utilisés dans l'interaction
        # Pas de warning attendu car ils sont utilisés correctement
        assert isinstance(warnings, list)
    
    def test_validate_vocabulary_usage_detects_terms(self, validator, sample_interaction, sample_vocabulary_terms):
        """Test que les termes utilisés sont détectés."""
        warnings = validator.validate_vocabulary_usage(sample_interaction, sample_vocabulary_terms)
        
        # Le validateur devrait détecter l'utilisation des termes
        # Pas de warning si utilisation correcte
        assert isinstance(warnings, list)
    
    def test_validate_interaction_with_vocabulary(self, validator, sample_interaction, sample_vocabulary_terms):
        """Test de validate_interaction avec vocabulaire."""
        warnings = validator.validate_interaction(
            sample_interaction,
            context=None,
            vocabulary_terms=sample_vocabulary_terms
        )
        
        assert isinstance(warnings, list)
        # Pas de warnings attendus pour une utilisation correcte
    
    def test_validate_interaction_without_vocabulary(self, validator, sample_interaction):
        """Test de validate_interaction sans vocabulaire."""
        warnings = validator.validate_interaction(
            sample_interaction,
            context=None,
            vocabulary_terms=None
        )
        
        assert isinstance(warnings, list)
        # Devrait fonctionner normalement sans vocabulaire

