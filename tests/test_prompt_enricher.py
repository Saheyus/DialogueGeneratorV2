"""Tests pour services/prompt_enricher.py"""
import pytest
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from services.prompt_enricher import PromptEnricher


class TestPromptEnricherVocabulary:
    """Tests pour enrich_with_vocabulary."""
    
    @pytest.fixture
    def prompt_enricher(self):
        """Fixture pour créer une instance de PromptEnricher sans services."""
        return PromptEnricher()
    
    @pytest.fixture
    def mock_vocab_service(self):
        """Fixture pour créer un mock du service de vocabulaire."""
        mock = Mock()
        mock.load_vocabulary.return_value = [
            {"term": "term1", "popularité": "Mondialement", "definition": "Test term 1"},
            {"term": "term2", "popularité": "Régionalement", "definition": "Test term 2"}
        ]
        mock.filter_by_config.return_value = [
            {"term": "term1", "popularité": "Mondialement", "definition": "Test term 1"}
        ]
        mock.format_for_prompt.return_value = "[VOCABULAIRE ALTEIR]\nterm1: Test term 1"
        return mock
    
    def test_enrich_with_vocabulary_with_service(self, mock_vocab_service):
        """Test que l'enrichissement de vocabulaire fonctionne avec un service injecté."""
        enricher = PromptEnricher(vocab_service=mock_vocab_service)
        prompt_parts = ["System prompt"]
        vocabulary_config = {"Mondialement": "all", "Régionalement": "none"}
        result = enricher.enrich_with_vocabulary(
            prompt_parts,
            vocabulary_config=vocabulary_config
        )
        
        assert len(result) == 2
        assert result[0] == "System prompt"
        assert "[VOCABULAIRE ALTEIR]" in result[1]
        mock_vocab_service.load_vocabulary.assert_called_once()
        mock_vocab_service.filter_by_config.assert_called_once_with(
            mock_vocab_service.load_vocabulary.return_value,
            vocabulary_config,
            None
        )
        mock_vocab_service.format_for_prompt.assert_called_once()
    
    def test_enrich_with_vocabulary_without_config(self, prompt_enricher):
        """Test que l'enrichissement de vocabulaire ne fait rien si config est None."""
        prompt_parts = ["System prompt"]
        result = prompt_enricher.enrich_with_vocabulary(
            prompt_parts,
            vocabulary_config=None
        )
        
        assert result == prompt_parts
        assert len(result) == 1
    
    def test_enrich_with_vocabulary_standard_format(self, mock_vocab_service):
        """Test que le format standard ajoute \n avant le vocabulaire."""
        enricher = PromptEnricher(vocab_service=mock_vocab_service)
        prompt_parts = ["System prompt"]
        vocabulary_config = {"Mondialement": "all"}
        result = enricher.enrich_with_vocabulary(
            prompt_parts,
            vocabulary_config=vocabulary_config,
            format_style="standard"
        )
        
        assert result[1].startswith("\n")
    
    def test_enrich_with_vocabulary_unity_format(self, mock_vocab_service):
        """Test que le format Unity n'ajoute pas \n avant mais ajoute "" après."""
        enricher = PromptEnricher(vocab_service=mock_vocab_service)
        prompt_parts = ["System prompt"]
        vocabulary_config = {"Mondialement": "all"}
        result = enricher.enrich_with_vocabulary(
            prompt_parts,
            vocabulary_config=vocabulary_config,
            format_style="unity"
        )
        
        assert len(result) == 3  # System prompt + vocab + ""
        assert not result[1].startswith("\n")
        assert result[2] == ""
    
    @patch('services.vocabulary_service.VocabularyService')
    def test_enrich_with_vocabulary_auto_instantiate(self, mock_vocab_class, prompt_enricher):
        """Test que le service est instancié automatiquement si None."""
        mock_service = Mock()
        mock_service.load_vocabulary.return_value = [{"term": "term1", "popularité": "Mondialement"}]
        mock_service.filter_by_config.return_value = [{"term": "term1", "popularité": "Mondialement"}]
        mock_service.format_for_prompt.return_value = "[VOCABULAIRE ALTEIR]\nterm1: definition"
        mock_vocab_class.return_value = mock_service
        
        prompt_parts = ["System prompt"]
        vocabulary_config = {"Mondialement": "all"}
        result = prompt_enricher.enrich_with_vocabulary(
            prompt_parts,
            vocabulary_config=vocabulary_config
        )
        
        mock_vocab_class.assert_called_once()
        assert len(result) == 2
    
    def test_enrich_with_vocabulary_error_handling(self, mock_vocab_service):
        """Test que les erreurs sont gérées gracieusement."""
        mock_vocab_service.load_vocabulary.side_effect = Exception("Service error")
        enricher = PromptEnricher(vocab_service=mock_vocab_service)
        prompt_parts = ["System prompt"]
        vocabulary_config = {"Mondialement": "all"}
        
        result = enricher.enrich_with_vocabulary(
            prompt_parts,
            vocabulary_config=vocabulary_config
        )
        
        # Devrait retourner les prompt_parts inchangés en cas d'erreur
        assert result == prompt_parts


class TestPromptEnricherNarrativeGuides:
    """Tests pour enrich_with_narrative_guides."""
    
    @pytest.fixture
    def prompt_enricher(self):
        """Fixture pour créer une instance de PromptEnricher sans services."""
        return PromptEnricher()
    
    @pytest.fixture
    def mock_guides_service(self):
        """Fixture pour créer un mock du service de guides narratifs."""
        mock = Mock()
        mock.load_guides.return_value = {
            "dialogue_guide": "Guide de dialogue",
            "narrative_guide": "Guide narratif"
        }
        mock.format_for_prompt.return_value = "--- GUIDES NARRATIFS ---\nGuide de dialogue"
        return mock
    
    def test_enrich_with_narrative_guides_with_service(self, mock_guides_service):
        """Test que l'enrichissement de guides narratifs fonctionne avec un service injecté."""
        enricher = PromptEnricher(guides_service=mock_guides_service)
        prompt_parts = ["System prompt"]
        result = enricher.enrich_with_narrative_guides(
            prompt_parts,
            include_narrative_guides=True
        )
        
        assert len(result) == 2
        assert result[0] == "System prompt"
        assert "--- GUIDES NARRATIFS ---" in result[1]
        mock_guides_service.load_guides.assert_called_once()
        mock_guides_service.format_for_prompt.assert_called_once_with(
            {"dialogue_guide": "Guide de dialogue", "narrative_guide": "Guide narratif"},
            include_rules=True
        )
    
    def test_enrich_with_narrative_guides_disabled(self, prompt_enricher):
        """Test que l'enrichissement de guides narratifs ne fait rien si désactivé."""
        prompt_parts = ["System prompt"]
        result = prompt_enricher.enrich_with_narrative_guides(
            prompt_parts,
            include_narrative_guides=False
        )
        
        assert result == prompt_parts
        assert len(result) == 1
    
    def test_enrich_with_narrative_guides_unity_format(self, mock_guides_service):
        """Test que le format Unity ajoute "" après les guides."""
        enricher = PromptEnricher(guides_service=mock_guides_service)
        prompt_parts = ["System prompt"]
        result = enricher.enrich_with_narrative_guides(
            prompt_parts,
            include_narrative_guides=True,
            format_style="unity"
        )
        
        assert len(result) == 3  # System prompt + guides + ""
        assert result[2] == ""
    
    @patch('services.narrative_guides_service.NarrativeGuidesService')
    def test_enrich_with_narrative_guides_auto_instantiate(self, mock_guides_class, prompt_enricher):
        """Test que le service est instancié automatiquement si None."""
        mock_service = Mock()
        mock_service.load_guides.return_value = {"dialogue_guide": "Guide"}
        mock_service.format_for_prompt.return_value = "Guides text"
        mock_guides_class.return_value = mock_service
        
        prompt_parts = ["System prompt"]
        result = prompt_enricher.enrich_with_narrative_guides(
            prompt_parts,
            include_narrative_guides=True
        )
        
        mock_guides_class.assert_called_once()
        assert len(result) == 2
    
    def test_enrich_with_narrative_guides_error_handling(self, mock_guides_service):
        """Test que les erreurs sont gérées gracieusement."""
        mock_guides_service.load_guides.side_effect = Exception("Service error")
        enricher = PromptEnricher(guides_service=mock_guides_service)
        prompt_parts = ["System prompt"]
        
        result = enricher.enrich_with_narrative_guides(
            prompt_parts,
            include_narrative_guides=True
        )
        
        # Devrait retourner les prompt_parts inchangés en cas d'erreur
        assert result == prompt_parts
    
    def test_enrich_with_narrative_guides_no_guides(self, mock_guides_service):
        """Test que l'enrichissement ne fait rien si aucun guide n'est disponible."""
        mock_guides_service.load_guides.return_value = {}
        mock_guides_service.format_for_prompt.return_value = ""
        enricher = PromptEnricher(guides_service=mock_guides_service)
        prompt_parts = ["System prompt"]
        
        result = enricher.enrich_with_narrative_guides(
            prompt_parts,
            include_narrative_guides=True
        )
        
        # Devrait retourner les prompt_parts inchangés si aucun guide
        assert result == prompt_parts
