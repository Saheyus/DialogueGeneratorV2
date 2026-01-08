"""Tests pour le service DialogueGenerationService."""
import pytest
from unittest.mock import MagicMock
from services.dialogue_generation_service import DialogueGenerationService
from context_builder import ContextBuilder
from prompt_engine import PromptEngine


@pytest.fixture
def mock_context_builder():
    """Mock du ContextBuilder."""
    mock_builder = MagicMock(spec=ContextBuilder)
    mock_builder.build_context = MagicMock(return_value="Test context")
    mock_builder.build_context_with_custom_fields = MagicMock(return_value="Test context with custom fields")
    return mock_builder


@pytest.fixture
def mock_prompt_engine():
    """Mock du PromptEngine."""
    mock_engine = MagicMock(spec=PromptEngine)
    mock_engine.system_prompt_template = "Test system prompt"
    return mock_engine


@pytest.fixture
def dialogue_service(mock_context_builder, mock_prompt_engine):
    """Fixture pour créer un DialogueGenerationService."""
    return DialogueGenerationService(
        context_builder=mock_context_builder,
        prompt_engine=mock_prompt_engine
    )


class TestDialogueGenerationService:
    """Tests pour DialogueGenerationService."""
    
    def test_init(self, mock_context_builder, mock_prompt_engine):
        """Test d'initialisation du service."""
        service = DialogueGenerationService(
            context_builder=mock_context_builder,
            prompt_engine=mock_prompt_engine
        )
        
        assert service.context_builder == mock_context_builder
        assert service.prompt_engine == mock_prompt_engine
    
    def test_build_context_summary_basic(self, dialogue_service, mock_context_builder):
        """Test de construction de résumé contextuel basique."""
        context_selections = {
            "characters": ["Test Character"],
            "locations": []
        }
        user_instructions = "Test instructions"
        max_tokens = 1000
        
        result = dialogue_service._build_context_summary(
            context_selections=context_selections,
            user_instructions=user_instructions,
            max_tokens=max_tokens
        )
        
        assert result == "Test context"
        mock_context_builder.build_context.assert_called_once()
    
    def test_build_context_summary_with_field_configs(self, dialogue_service, mock_context_builder):
        """Test de construction avec field_configs."""
        context_selections = {
            "characters": ["Test Character"]
        }
        field_configs = {
            "character": {
                "1": [{"path": "Nom", "label": "Nom"}]
            }
        }
        
        result = dialogue_service._build_context_summary(
            context_selections=context_selections,
            user_instructions="Test",
            max_tokens=1000,
            field_configs=field_configs
        )
        
        # Si build_context_with_custom_fields existe, il devrait être appelé
        if hasattr(mock_context_builder, 'build_context_with_custom_fields'):
            assert result == "Test context with custom fields"
        else:
            assert result == "Test context"
    
    def test_build_context_summary_with_organization_mode(self, dialogue_service, mock_context_builder):
        """Test de construction avec organization_mode."""
        context_selections = {
            "characters": ["Test Character"]
        }
        field_configs = {
            "character": {
                "1": [{"path": "Nom", "label": "Nom"}]
            }
        }
        
        result = dialogue_service._build_context_summary(
            context_selections=context_selections,
            user_instructions="Test",
            max_tokens=1000,
            field_configs=field_configs,
            organization_mode="narrative"
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_build_context_summary_no_limit(self, dialogue_service, mock_context_builder):
        """Test de construction avec no_limit=True."""
        context_selections = {
            "characters": ["Test Character"]
        }
        
        result = dialogue_service._build_context_summary(
            context_selections=context_selections,
            user_instructions="Test",
            max_tokens=1000,
            no_limit=True
        )
        
        # Vérifier que max_tokens élevé est utilisé
        call_args = mock_context_builder.build_context.call_args
        assert call_args[1]["max_tokens"] == 999999
    
    def test_restore_prompt_on_error(self, dialogue_service, mock_prompt_engine):
        """Test de restauration du prompt après erreur."""
        original_prompt = "Original prompt"
        mock_prompt_engine.system_prompt_template = "Modified prompt"
        
        dialogue_service._restore_prompt_on_error(original_prompt)
        
        assert mock_prompt_engine.system_prompt_template == original_prompt
    
    def test_restore_prompt_on_error_no_change(self, dialogue_service, mock_prompt_engine):
        """Test de restauration quand le prompt n'a pas changé."""
        original_prompt = "Original prompt"
        mock_prompt_engine.system_prompt_template = original_prompt
        
        # Ne devrait pas lever d'erreur
        dialogue_service._restore_prompt_on_error(original_prompt)
    
    def test_restore_prompt_on_error_none(self, dialogue_service, mock_prompt_engine):
        """Test de restauration avec None (pas de prompt original)."""
        # Ne devrait pas lever d'erreur
        dialogue_service._restore_prompt_on_error(None)
    
    def test_extract_json_from_text_markdown_block(self, dialogue_service):
        """Test d'extraction JSON depuis bloc markdown."""
        text = "```json\n{\"key\": \"value\"}\n```"
        
        result = dialogue_service._extract_json_from_text(text)
        
        assert result == "{\"key\": \"value\"}"
    
    def test_extract_json_from_text_code_block(self, dialogue_service):
        """Test d'extraction JSON depuis bloc code sans json."""
        text = "```\n{\"key\": \"value\"}\n```"
        
        result = dialogue_service._extract_json_from_text(text)
        
        assert result == "{\"key\": \"value\"}"
    
    def test_extract_json_from_text_direct(self, dialogue_service):
        """Test d'extraction JSON directement dans le texte."""
        text = "Some text {\"key\": \"value\"} more text"
        
        result = dialogue_service._extract_json_from_text(text)
        
        assert result is not None
        assert "key" in result
    
    def test_extract_json_from_text_no_json(self, dialogue_service):
        """Test d'extraction avec texte sans JSON."""
        text = "Just plain text without JSON"
        
        result = dialogue_service._extract_json_from_text(text)
        
        assert result is None
    
    def test_extract_json_from_text_nested_braces(self, dialogue_service):
        """Test d'extraction JSON avec accolades imbriquées."""
        text = "```json\n{\"key\": {\"nested\": \"value\"}}\n```"
        
        result = dialogue_service._extract_json_from_text(text)
        
        assert result is not None
        assert "nested" in result
