"""Tests unitaires pour UnityDialogueOrchestrator."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from services.unity_dialogue_orchestrator import UnityDialogueOrchestrator, GenerationEvent
from api.schemas.dialogue import GenerateUnityDialogueRequest, GenerateUnityDialogueResponse, ContextSelection
from api.exceptions import ValidationException, InternalServerException


@pytest.fixture
def mock_services():
    """Crée des mocks pour tous les services nécessaires."""
    return {
        'dialogue_service': Mock(),
        'prompt_engine': Mock(),
        'skill_service': Mock(),
        'trait_service': Mock(),
        'config_service': Mock(),
        'usage_service': Mock(),
    }


@pytest.fixture
def orchestrator(mock_services):
    """Crée un orchestrateur avec des services mockés."""
    return UnityDialogueOrchestrator(
        dialogue_service=mock_services['dialogue_service'],
        prompt_engine=mock_services['prompt_engine'],
        skill_service=mock_services['skill_service'],
        trait_service=mock_services['trait_service'],
        config_service=mock_services['config_service'],
        usage_service=mock_services['usage_service'],
        request_id="test_request_123"
    )


@pytest.fixture
def sample_request_data():
    """Crée des données de requête de test."""
    context_selection = ContextSelection(
        characters_full=["character_1"],
        characters_excerpt=[],
        locations_full=[],
        locations_excerpt=[],
        items_full=[],
        items_excerpt=[],
        species_full=[],
        species_excerpt=[],
        communities_full=[],
        communities_excerpt=[],
        dialogues_examples=[],
        scene_location=None
    )
    
    return GenerateUnityDialogueRequest(
        user_instructions="Test dialogue",
        context_selections=context_selection,
        llm_model_identifier="gpt-4o"
    )


@pytest.mark.asyncio
async def test_orchestrator_generate_with_events_sequence(orchestrator, sample_request_data, mock_services):
    """Test que l'orchestrateur yield les bons événements dans le bon ordre."""
    
    # Mock context_builder
    mock_context_builder = Mock()
    mock_context_builder.build_context_json.return_value = {"test": "context"}
    mock_context_builder._context_serializer.serialize_to_text.return_value = "Context summary"
    orchestrator.dialogue_service.context_builder = mock_context_builder
    
    # Mock prompt_engine
    mock_built = Mock()
    mock_built.raw_prompt = "Test prompt"
    mock_built.prompt_hash = "hash123"
    mock_built.token_count = 100
    mock_built.structured_prompt = None
    mock_services['prompt_engine'].build_prompt.return_value = mock_built
    
    # Mock skill/trait services
    mock_services['skill_service'].load_skills.return_value = []
    mock_services['trait_service'].get_trait_labels.return_value = []
    
    # Mock config service
    mock_services['config_service'].get_llm_config.return_value = {}
    mock_services['config_service'].get_available_llm_models.return_value = [
        {"model_identifier": "gpt-4o"}
    ]
    
    # Mock LLM client factory
    mock_llm_client = Mock()
    mock_llm_client.reasoning_trace = None
    mock_llm_client.warning = None
    mock_llm_client.last_call_cost = 0.001
    
    with patch('services.unity_dialogue_orchestrator.LLMClientFactory') as mock_factory:
        mock_factory.create_client.return_value = mock_llm_client
        
        # Mock UnityDialogueGenerationService
        with patch('services.unity_dialogue_orchestrator.UnityDialogueGenerationService') as mock_unity_service_class:
            mock_unity_service = Mock()
            mock_unity_service_class.return_value = mock_unity_service
            
            # Mock generation response
            mock_generation_response = Mock()
            mock_generation_response.title = "Test Dialogue"
            mock_unity_service.generate_dialogue_node = AsyncMock(return_value=mock_generation_response)
            
            # Mock enrich_with_ids
            mock_enriched_nodes = [{"id": "START", "text": "Test"}]
            mock_unity_service.enrich_with_ids.return_value = mock_enriched_nodes
            
            # Mock renderer
            with patch('services.unity_dialogue_orchestrator.UnityJsonRenderer') as mock_renderer_class:
                mock_renderer = Mock()
                mock_renderer_class.return_value = mock_renderer
                mock_renderer.render_unity_nodes.return_value = '{"nodes": []}'
                
                # Collecter les événements
                events = []
                async for event in orchestrator.generate_with_events(sample_request_data, lambda: False):
                    events.append(event)
                
                # Vérifier séquence des événements
                assert len(events) >= 4
                assert events[0].type == 'step' and events[0].data['step'] == 'Prompting'
                assert events[1].type == 'step' and events[1].data['step'] == 'Generating'
                assert events[2].type == 'step' and events[2].data['step'] == 'Validating'
                
                # Vérifier metadata
                metadata_events = [e for e in events if e.type == 'metadata']
                assert len(metadata_events) > 0
                assert metadata_events[0].data['tokens'] == 100
                
                # Vérifier complete
                complete_events = [e for e in events if e.type == 'complete']
                assert len(complete_events) > 0
                assert 'result' in complete_events[0].data


@pytest.mark.asyncio
async def test_orchestrator_cancellation(orchestrator, sample_request_data, mock_services):
    """Test que l'annulation fonctionne correctement et arrête immédiatement."""
    
    # Mock context_builder
    mock_context_builder = Mock()
    mock_context_builder.build_context_json.return_value = {"test": "context"}
    mock_context_builder._context_serializer.serialize_to_text.return_value = "Context summary"
    orchestrator.dialogue_service.context_builder = mock_context_builder
    
    # Mock prompt_engine
    mock_built = Mock()
    mock_built.raw_prompt = "Test prompt"
    mock_built.prompt_hash = "hash123"
    mock_built.token_count = 100
    mock_built.structured_prompt = None
    mock_services['prompt_engine'].build_prompt.return_value = mock_built
    
    # Mock skill/trait services
    mock_services['skill_service'].load_skills.return_value = []
    mock_services['trait_service'].get_trait_labels.return_value = []
    
    # Mock config service
    mock_services['config_service'].get_llm_config.return_value = {}
    mock_services['config_service'].get_available_llm_models.return_value = [
        {"model_identifier": "gpt-4o"}
    ]
    
    # Mock UnityDialogueGenerationService pour retourner un dialogue avec texte à streamer
    from unittest.mock import AsyncMock
    mock_unity_service = AsyncMock()
    mock_node = Mock()
    mock_node.speaker = "Test Speaker"
    mock_node.line = "Test line"
    mock_node.choices = []
    mock_response = Mock()
    mock_response.node = mock_node
    mock_response.title = "Test Dialogue"
    mock_unity_service.generate_dialogue_node.return_value = mock_response
    
    # Remplacer temporairement le service Unity
    import services.unity_dialogue_generation_service
    original_service = services.unity_dialogue_generation_service.UnityDialogueGenerationService
    services.unity_dialogue_generation_service.UnityDialogueGenerationService = lambda: mock_unity_service
    
    try:
        # Simuler annulation pendant streaming (après quelques chunks)
        cancelled = False
        chunk_count = 0
        
        def check_cancelled():
            return cancelled
        
        events = []
        async for event in orchestrator.generate_with_events(sample_request_data, check_cancelled):
            events.append(event)
            # Annuler après quelques chunks pour tester l'arrêt immédiat
            if event.type == 'chunk':
                chunk_count += 1
                if chunk_count == 3:  # Annuler après 3 chunks
                    cancelled = True
        
        # Vérifier que erreur annulation est yieldée
        error_events = [e for e in events if e.type == 'error']
        assert len(error_events) > 0
        assert 'annulée' in error_events[0].data['message'].lower() or 'cancelled' in error_events[0].data['message'].lower()
        
        # Vérifier que le streaming s'arrête immédiatement (pas de chunks après annulation)
        error_index = next(i for i, e in enumerate(events) if e.type == 'error')
        chunks_after_cancellation = [e for i, e in enumerate(events) if i > error_index and e.type == 'chunk']
        assert len(chunks_after_cancellation) == 0, "Le streaming doit s'arrêter immédiatement après annulation"
        
        # Vérifier qu'aucun événement 'complete' n'est envoyé si annulé
        complete_events = [e for e in events if e.type == 'complete']
        assert len(complete_events) == 0, "Aucun dialogue partiel ne doit être sauvegardé si annulé"
    finally:
        # Restaurer le service original
        services.unity_dialogue_generation_service.UnityDialogueGenerationService = original_service


@pytest.mark.asyncio
async def test_orchestrator_generate_rest_usage(orchestrator, sample_request_data, mock_services):
    """Test que generate() (usage REST) fonctionne correctement."""
    
    # Mock context_builder
    mock_context_builder = Mock()
    mock_context_builder.build_context_json.return_value = {"test": "context"}
    mock_context_builder._context_serializer.serialize_to_text.return_value = "Context summary"
    orchestrator.dialogue_service.context_builder = mock_context_builder
    
    # Mock prompt_engine
    mock_built = Mock()
    mock_built.raw_prompt = "Test prompt"
    mock_built.prompt_hash = "hash123"
    mock_built.token_count = 100
    mock_built.structured_prompt = None
    mock_services['prompt_engine'].build_prompt.return_value = mock_built
    
    # Mock skill/trait services
    mock_services['skill_service'].load_skills.return_value = []
    mock_services['trait_service'].get_trait_labels.return_value = []
    
    # Mock config service
    mock_services['config_service'].get_llm_config.return_value = {}
    mock_services['config_service'].get_available_llm_models.return_value = [
        {"model_identifier": "gpt-4o"}
    ]
    
    # Mock LLM client factory
    mock_llm_client = Mock()
    mock_llm_client.reasoning_trace = None
    mock_llm_client.warning = None
    mock_llm_client.last_call_cost = 0.001
    
    with patch('services.unity_dialogue_orchestrator.LLMClientFactory') as mock_factory:
        mock_factory.create_client.return_value = mock_llm_client
        
        # Mock UnityDialogueGenerationService
        with patch('services.unity_dialogue_orchestrator.UnityDialogueGenerationService') as mock_unity_service_class:
            mock_unity_service = Mock()
            mock_unity_service_class.return_value = mock_unity_service
            
            # Mock generation response
            mock_generation_response = Mock()
            mock_generation_response.title = "Test Dialogue"
            mock_unity_service.generate_dialogue_node = AsyncMock(return_value=mock_generation_response)
            
            # Mock enrich_with_ids
            mock_enriched_nodes = [{"id": "START", "text": "Test"}]
            mock_unity_service.enrich_with_ids.return_value = mock_enriched_nodes
            
            # Mock renderer
            with patch('services.unity_dialogue_orchestrator.UnityJsonRenderer') as mock_renderer_class:
                mock_renderer = Mock()
                mock_renderer_class.return_value = mock_renderer
                mock_renderer.render_unity_nodes.return_value = '{"nodes": []}'
                
                # Appel generate() (usage REST)
                result = await orchestrator.generate(sample_request_data)
                
                # Vérifier que le résultat est une GenerateUnityDialogueResponse
                assert isinstance(result, GenerateUnityDialogueResponse)
                assert result.raw_prompt == "Test prompt"
                assert result.prompt_hash == "hash123"
                assert result.estimated_tokens == 100


@pytest.mark.asyncio
async def test_orchestrator_validation_error(orchestrator, mock_services):
    """Test que ValidationException est re-raise correctement."""
    
    # Créer une requête sans personnages (devrait lever ValidationException)
    context_selection = ContextSelection(
        characters_full=[],
        characters_excerpt=[],
        locations_full=[],
        locations_excerpt=[],
        items_full=[],
        items_excerpt=[],
        species_full=[],
        species_excerpt=[],
        communities_full=[],
        communities_excerpt=[],
        dialogues_examples=[],
        scene_location=None
    )
    
    request_data = GenerateUnityDialogueRequest(
        user_instructions="Test",
        context_selections=context_selection,
        llm_model_identifier="gpt-4o"
    )
    
    # Vérifier que ValidationException est levée
    with pytest.raises(ValidationException):
        async for _ in orchestrator.generate_with_events(request_data, lambda: False):
            pass
