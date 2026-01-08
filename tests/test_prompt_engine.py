"""Tests pour prompt_engine.py"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any, Optional

from prompt_engine import PromptEngine


class TestPromptEngineInjection:
    """Tests pour les méthodes d'injection de vocabulaire et guides narratifs."""
    
    @pytest.fixture
    def prompt_engine(self):
        """Fixture pour créer une instance de PromptEngine."""
        return PromptEngine(system_prompt_template="Test system prompt")
    
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
    
    def test_inject_vocabulary_with_service(self, mock_vocab_service):
        """Test que l'injection de vocabulaire fonctionne avec un service injecté via constructeur."""
        prompt_engine = PromptEngine(
            system_prompt_template="Test system prompt",
            vocab_service=mock_vocab_service
        )
        prompt_parts = ["System prompt"]
        vocabulary_config = {"Mondialement": "all", "Régionalement": "none"}
        result = prompt_engine._enricher.enrich_with_vocabulary(
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
    
    def test_inject_vocabulary_without_config(self, prompt_engine):
        """Test que l'injection de vocabulaire ne fait rien si config est None."""
        prompt_parts = ["System prompt"]
        result = prompt_engine._enricher.enrich_with_vocabulary(
            prompt_parts,
            vocabulary_config=None
        )
        
        assert result == prompt_parts
        assert len(result) == 1
    
    def test_inject_vocabulary_standard_format(self, mock_vocab_service):
        """Test que le format standard ajoute \n avant le vocabulaire."""
        prompt_engine = PromptEngine(
            system_prompt_template="Test system prompt",
            vocab_service=mock_vocab_service
        )
        prompt_parts = ["System prompt"]
        vocabulary_config = {"Mondialement": "all"}
        result = prompt_engine._enricher.enrich_with_vocabulary(
            prompt_parts,
            vocabulary_config=vocabulary_config,
            format_style="standard"
        )
        
        assert result[1].startswith("\n")
    
    def test_inject_vocabulary_unity_format(self, mock_vocab_service):
        """Test que le format Unity n'ajoute pas \n avant mais ajoute "" après."""
        prompt_engine = PromptEngine(
            system_prompt_template="Test system prompt",
            vocab_service=mock_vocab_service
        )
        prompt_parts = ["System prompt"]
        vocabulary_config = {"Mondialement": "all"}
        result = prompt_engine._enricher.enrich_with_vocabulary(
            prompt_parts,
            vocabulary_config=vocabulary_config,
            format_style="unity"
        )
        
        assert len(result) == 3  # System prompt + vocab + ""
        assert not result[1].startswith("\n")
        assert result[2] == ""
    
    def test_inject_narrative_guides_with_service(self, mock_guides_service):
        """Test que l'injection de guides narratifs fonctionne avec un service injecté via constructeur."""
        prompt_engine = PromptEngine(
            system_prompt_template="Test system prompt",
            guides_service=mock_guides_service
        )
        prompt_parts = ["System prompt"]
        result = prompt_engine._enricher.enrich_with_narrative_guides(
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
    
    def test_inject_narrative_guides_disabled(self, prompt_engine):
        """Test que l'injection de guides narratifs ne fait rien si désactivée."""
        prompt_parts = ["System prompt"]
        result = prompt_engine._enricher.enrich_with_narrative_guides(
            prompt_parts,
            include_narrative_guides=False
        )
        
        assert result == prompt_parts
        assert len(result) == 1
    
    def test_inject_narrative_guides_unity_format(self, mock_guides_service):
        """Test que le format Unity ajoute "" après les guides."""
        prompt_engine = PromptEngine(
            system_prompt_template="Test system prompt",
            guides_service=mock_guides_service
        )
        prompt_parts = ["System prompt"]
        result = prompt_engine._enricher.enrich_with_narrative_guides(
            prompt_parts,
            include_narrative_guides=True,
            format_style="unity"
        )
        
        assert len(result) == 3  # System prompt + guides + ""
        assert result[2] == ""
    
    @patch('services.vocabulary_service.VocabularyService')
    def test_inject_vocabulary_auto_instantiate(self, mock_vocab_class, prompt_engine):
        """Test que le service est instancié automatiquement si None."""
        mock_service = Mock()
        mock_service.load_vocabulary.return_value = [{"term": "term1", "popularité": "Mondialement"}]
        mock_service.filter_by_config.return_value = [{"term": "term1", "popularité": "Mondialement"}]
        mock_service.format_for_prompt.return_value = "[VOCABULAIRE ALTEIR]\nterm1: definition"
        mock_vocab_class.return_value = mock_service
        
        prompt_parts = ["System prompt"]
        vocabulary_config = {"Mondialement": "all"}
        result = prompt_engine._enricher.enrich_with_vocabulary(
            prompt_parts,
            vocabulary_config=vocabulary_config
        )
        
        mock_vocab_class.assert_called_once()
        assert len(result) == 2
    
    @patch('services.narrative_guides_service.NarrativeGuidesService')
    def test_inject_narrative_guides_auto_instantiate(self, mock_guides_class, prompt_engine):
        """Test que le service est instancié automatiquement si None."""
        mock_service = Mock()
        mock_service.load_guides.return_value = {"dialogue_guide": "Guide"}
        mock_service.format_for_prompt.return_value = "Guides text"
        mock_guides_class.return_value = mock_service
        
        prompt_parts = ["System prompt"]
        result = prompt_engine._enricher.enrich_with_narrative_guides(
            prompt_parts,
            include_narrative_guides=True
        )
        
        mock_guides_class.assert_called_once()
        assert len(result) == 2


# TestPromptEngineBuildPrompt supprimé - build_prompt() supprimé, système texte libre obsolète, utiliser build_unity_dialogue_prompt() à la place

class TestPromptEngineBuildUnityDialoguePrompt:
    """Tests pour build_unity_dialogue_prompt() après refactoring."""
    
    @pytest.fixture
    def prompt_engine(self):
        """Fixture pour créer une instance de PromptEngine."""
        return PromptEngine(system_prompt_template="Test system prompt")
    
    def test_build_unity_dialogue_prompt_uses_enricher(self, prompt_engine):
        """Test que build_unity_dialogue_prompt() utilise PromptEnricher avec format_style='unity'."""
        with patch.object(prompt_engine._enricher, 'enrich_with_vocabulary') as mock_enrich_vocab, \
             patch.object(prompt_engine._enricher, 'enrich_with_narrative_guides') as mock_enrich_guides:
            
            mock_enrich_vocab.return_value = []
            mock_enrich_guides.return_value = []
            
            prompt_engine.build_unity_dialogue_prompt(
                user_instructions="Test instructions",
                npc_speaker_id="NPC1",
                vocabulary_config={"Mondialement": "all"},
                include_narrative_guides=True
            )
            
            # enrich_with_vocabulary est appelé au moins une fois
            assert mock_enrich_vocab.call_count >= 1
            # Vérifier que format_style="unity" est passé au moins une fois
            calls = mock_enrich_vocab.call_args_list
            assert any(call[1].get('format_style') == "unity" for call in calls)
            
            # enrich_with_narrative_guides est appelé au moins une fois
            assert mock_enrich_guides.call_count >= 1
            # Vérifier que format_style="unity" est passé au moins une fois
            calls = mock_enrich_guides.call_args_list
            assert any(call[1].get('format_style') == "unity" for call in calls)
    
    def test_build_unity_dialogue_prompt_produces_valid_output(self, prompt_engine):
        """Test que build_unity_dialogue_prompt() produit une sortie valide (format XML)."""
        prompt, tokens = prompt_engine.build_unity_dialogue_prompt(
            user_instructions="Test instructions",
            npc_speaker_id="NPC1",
            scene_location={"lieu": "Test location"}
        )
        
        assert isinstance(prompt, str)
        assert isinstance(tokens, int)
        assert tokens > 0
        # Vérifier que c'est du XML
        assert prompt.startswith('<?xml version="1.0" encoding="UTF-8"?>')
        # Vérifier la présence des éléments XML
        assert "<prompt>" in prompt
        assert "NPC1" in prompt
        assert "Test instructions" in prompt
        # Le lieu est maintenant dans un élément <location> en XML
        assert "Test location" in prompt


class TestPromptEngineCompatibility:
    """Tests de compatibilité pour s'assurer qu'il n'y a pas de régression."""
    
    @pytest.fixture
    def prompt_engine(self):
        """Fixture pour créer une instance de PromptEngine."""
        return PromptEngine(system_prompt_template="Test system prompt")
    
    # test_build_prompt_backward_compatible supprimé - build_prompt() supprimé, système texte libre obsolète
    
    def test_build_unity_dialogue_prompt_backward_compatible(self, prompt_engine):
        """Test que build_unity_dialogue_prompt() reste compatible avec l'API existante."""
        # Test avec tous les paramètres optionnels
        prompt, tokens = prompt_engine.build_unity_dialogue_prompt(
            user_instructions="Instructions",
            npc_speaker_id="NPC1",
            player_character_id="PLAYER",
            skills_list=None,
            traits_list=None,
            context_summary=None,
            scene_location=None,
            max_choices=None,
            narrative_tags=None,
            author_profile=None,
            vocabulary_config=None,
            include_narrative_guides=False
        )
        
        assert isinstance(prompt, str)
        assert isinstance(tokens, int)
        assert "NPC1" in prompt
        assert "Instructions" in prompt

