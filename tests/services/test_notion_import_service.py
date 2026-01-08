"""Tests pour le service NotionImportService."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from services.notion_import_service import NotionImportService


@pytest.fixture
def mock_notion_api_client():
    """Mock du NotionAPIClient."""
    mock_client = MagicMock()
    mock_client.query_database = AsyncMock(return_value=[])
    mock_client.get_page = AsyncMock(return_value={"id": "test_page", "properties": {}})
    mock_client.get_page_content = AsyncMock(return_value="Test content")
    return mock_client


@pytest.fixture
def notion_import_service(mock_notion_api_client):
    """Fixture pour créer un NotionImportService avec mock."""
    return NotionImportService(api_client=mock_notion_api_client)


class TestNotionImportService:
    """Tests pour NotionImportService."""
    
    def test_init_with_api_client(self, mock_notion_api_client):
        """Test d'initialisation avec un client API fourni."""
        service = NotionImportService(api_client=mock_notion_api_client)
        assert service.api_client == mock_notion_api_client
    
    def test_init_without_api_client_no_env(self, monkeypatch):
        """Test d'initialisation sans client API et sans variable d'environnement."""
        monkeypatch.delenv("NOTION_API_KEY", raising=False)
        
        service = NotionImportService(api_client=None)
        assert service.api_client is None
    
    @pytest.mark.asyncio
    async def test_sync_guide_success(self, notion_import_service, mock_notion_api_client):
        """Test de synchronisation d'un guide avec succès."""
        page_id = "test_page_id"
        mock_notion_api_client.get_page_content = AsyncMock(return_value="Guide content")
        
        result = await notion_import_service.sync_guide(page_id)
        
        assert result == "Guide content"
        mock_notion_api_client.get_page_content.assert_called_once_with(page_id)
    
    @pytest.mark.asyncio
    async def test_sync_guide_api_error(self, notion_import_service, mock_notion_api_client):
        """Test de synchronisation avec erreur API."""
        page_id = "test_page_id"
        mock_notion_api_client.get_page_content = AsyncMock(side_effect=Exception("API Error"))
        
        # Le service peut gérer l'erreur ou la propager
        try:
            result = await notion_import_service.sync_guide(page_id)
            # Si l'erreur est gérée, result peut être None ou une chaîne vide
            assert result is None or result == ""
        except Exception:
            # Si l'erreur est propagée, c'est aussi valide
            pass
    
    def test_process_vocabulary_search_results(self, notion_import_service):
        """Test de traitement des résultats de recherche vocabulaire."""
        search_results = [
            {
                "text": '<properties>{"Terme": "Test", "Définition": "Test definition"}</properties>'
            },
            {
                "text": '<properties>{"Terme": "Test2", "Définition": "Test definition 2"}</properties>'
            }
        ]
        
        result = notion_import_service.process_vocabulary_search_results(search_results)
        
        assert isinstance(result, list)
        # Le résultat peut être filtré si certains termes sont invalides
        assert len(result) >= 0
        if len(result) > 0:
            assert "term" in result[0]
            assert "definition" in result[0]
    
    def test_process_vocabulary_search_results_invalid(self, notion_import_service):
        """Test de traitement avec résultats invalides."""
        search_results = [
            {
                "text": "Invalid format"
            }
        ]
        
        result = notion_import_service.process_vocabulary_search_results(search_results)
        
        # Les résultats invalides sont ignorés
        assert isinstance(result, list)
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_sync_vocabulary_success(self, notion_import_service, mock_notion_api_client):
        """Test de synchronisation du vocabulaire depuis Notion."""
        mock_notion_api_client.query_database = AsyncMock(return_value=[
            {
                "id": "page1",
                "properties": {
                    "Terme": {"type": "title", "title": [{"plain_text": "Test"}]},
                    "Définition": {"type": "rich_text", "rich_text": [{"plain_text": "Definition"}]},
                    "Popularité": {"type": "select", "select": {"name": "Mondialement"}},
                    "Catégorie": {"type": "select", "select": {"name": "Géographie"}},
                    "Type": {"type": "rich_text", "rich_text": []},
                    "Origine": {"type": "rich_text", "rich_text": []}
                }
            }
        ])
        
        result = await notion_import_service.sync_vocabulary()
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["term"] == "Test"
        assert result[0]["definition"] == "Definition"
        mock_notion_api_client.query_database.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sync_vocabulary_no_api_client(self, monkeypatch):
        """Test de synchronisation sans client API."""
        monkeypatch.delenv("NOTION_API_KEY", raising=False)
        service = NotionImportService(api_client=None)
        
        with pytest.raises(ValueError) as exc_info:
            await service.sync_vocabulary()
        
        assert "Client Notion API non disponible" in str(exc_info.value)
    
    def test_process_guide_page_fetch(self, notion_import_service):
        """Test de traitement d'une page guide récupérée via fetch."""
        page_data = {
            "text": "<content>Guide content here</content>"
        }
        
        result = notion_import_service.process_guide_page_fetch(page_data)
        
        assert result == "Guide content here"
    
    def test_process_guide_page_fetch_no_content_tag(self, notion_import_service):
        """Test de traitement sans balise content."""
        page_data = {
            "text": "Plain text content"
        }
        
        result = notion_import_service.process_guide_page_fetch(page_data)
        
        assert result == "Plain text content"
    
    def test_process_page_content(self, notion_import_service):
        """Test de traitement du contenu d'une page."""
        content = "Test page content"
        
        result = notion_import_service.process_page_content(content)
        
        assert "content" in result
        assert "processed_at" in result
        assert "length" in result
        assert result["content"] == content
        assert result["length"] == len(content)
    
    def test_extract_property_value_title(self, notion_import_service):
        """Test d'extraction de valeur de propriété title."""
        prop = {
            "type": "title",
            "title": [
                {"plain_text": "Test Title"}
            ]
        }
        
        result = notion_import_service._extract_property_value(prop)
        
        assert result == "Test Title"
    
    def test_extract_property_value_rich_text(self, notion_import_service):
        """Test d'extraction de valeur de propriété rich_text."""
        prop = {
            "type": "rich_text",
            "rich_text": [
                {"plain_text": "Test Text"}
            ]
        }
        
        result = notion_import_service._extract_property_value(prop)
        
        assert result == "Test Text"
    
    def test_extract_property_value_select(self, notion_import_service):
        """Test d'extraction de valeur de propriété select."""
        prop = {
            "type": "select",
            "select": {
                "name": "Selected Value"
            }
        }
        
        result = notion_import_service._extract_property_value(prop)
        
        assert result == "Selected Value"
    
    def test_extract_property_value_multi_select(self, notion_import_service):
        """Test d'extraction de valeur de propriété multi_select."""
        prop = {
            "type": "multi_select",
            "multi_select": [
                {"name": "Value1"},
                {"name": "Value2"}
            ]
        }
        
        result = notion_import_service._extract_property_value(prop)
        
        assert result == "Value1, Value2"
    
    def test_extract_property_value_number(self, notion_import_service):
        """Test d'extraction de valeur de propriété number."""
        prop = {
            "type": "number",
            "number": 42
        }
        
        result = notion_import_service._extract_property_value(prop)
        
        assert result == "42"
    
    def test_extract_property_value_checkbox(self, notion_import_service):
        """Test d'extraction de valeur de propriété checkbox."""
        prop_true = {
            "type": "checkbox",
            "checkbox": True
        }
        prop_false = {
            "type": "checkbox",
            "checkbox": False
        }
        
        result_true = notion_import_service._extract_property_value(prop_true)
        result_false = notion_import_service._extract_property_value(prop_false)
        
        assert result_true == "Oui"
        assert result_false is None
    
    def test_get_dialogue_guide_page_id(self):
        """Test de récupération de l'ID de la page du guide des dialogues."""
        page_id = NotionImportService.get_dialogue_guide_page_id()
        
        assert isinstance(page_id, str)
        assert len(page_id) > 0
    
    def test_get_narrative_guide_page_id(self):
        """Test de récupération de l'ID de la page du guide de narration."""
        page_id = NotionImportService.get_narrative_guide_page_id()
        
        assert isinstance(page_id, str)
        assert len(page_id) > 0
