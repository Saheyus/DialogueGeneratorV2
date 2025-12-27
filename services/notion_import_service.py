"""Service pour récupérer les données depuis Notion via MCP."""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# IDs Notion
VOCABULARY_DATABASE_ID = "2d16e4d21b458016ba74ccb4fbd92b72"
VOCABULARY_DATA_SOURCE_ID = "2d16e4d2-1b45-8023-b748-000b66bac9a0"
DIALOGUE_GUIDE_PAGE_ID = "1886e4d21b45812094c4fb4e9666e0cb"
NARRATIVE_GUIDE_PAGE_ID = "1886e4d21b4581339cf2ef6486fa001d"


class NotionImportService:
    """Service pour récupérer les données depuis Notion via MCP.
    
    Note: Les appels MCP sont effectués depuis les endpoints API qui ont accès
    aux outils MCP. Ce service fournit les méthodes de traitement des données.
    """
    
    def __init__(self):
        """Initialise le service d'import Notion."""
        logger.info("NotionImportService initialisé")
    
    def process_vocabulary_search_results(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Traite les résultats de recherche Notion pour le vocabulaire.
        
        Args:
            search_results: Liste des résultats de recherche Notion (format MCP).
            
        Returns:
            Liste des termes formatés avec leurs métadonnées.
        """
        terms = []
        
        for result in search_results:
            try:
                # Extraire les propriétés depuis le format Notion
                properties = result.get("properties", {})
                
                terme = self._extract_title(properties.get("Terme", {}))
                definition = self._extract_text(properties.get("Définition", {}))
                importance = self._extract_select(properties.get("Importance", {}))
                categorie = self._extract_select(properties.get("Catégorie", {}))
                type_term = self._extract_select(properties.get("Type", {}))
                origine = self._extract_text(properties.get("Origine", {}))
                
                if terme:
                    terms.append({
                        "term": terme,
                        "definition": definition or "",
                        "importance": importance or "Anecdotique",
                        "category": categorie or "Autre",
                        "type": type_term or "",
                        "origin": origine or ""
                    })
            except Exception as e:
                logger.warning(f"Erreur lors du traitement d'un terme: {e}")
                continue
        
        logger.info(f"Traitement de {len(terms)} termes depuis Notion")
        return terms
    
    def process_page_content(self, page_content: str) -> Dict[str, Any]:
        """Traite le contenu markdown d'une page Notion.
        
        Args:
            page_content: Contenu markdown de la page Notion.
            
        Returns:
            Dictionnaire avec le contenu formaté et les métadonnées.
        """
        return {
            "content": page_content,
            "processed_at": datetime.now().isoformat(),
            "length": len(page_content)
        }
    
    def _extract_title(self, title_prop: Dict[str, Any]) -> Optional[str]:
        """Extrait le texte d'une propriété title Notion.
        
        Args:
            title_prop: Propriété title au format Notion.
            
        Returns:
            Texte du titre ou None.
        """
        if not title_prop:
            return None
        
        # Format Notion title: {"title": [{"plain_text": "..."}]}
        title_array = title_prop.get("title", [])
        if title_array and len(title_array) > 0:
            return title_array[0].get("plain_text", "")
        return None
    
    def _extract_text(self, text_prop: Dict[str, Any]) -> Optional[str]:
        """Extrait le texte d'une propriété rich_text Notion.
        
        Args:
            text_prop: Propriété rich_text au format Notion.
            
        Returns:
            Texte ou None.
        """
        if not text_prop:
            return None
        
        # Format Notion rich_text: {"rich_text": [{"plain_text": "..."}]}
        rich_text_array = text_prop.get("rich_text", [])
        if rich_text_array and len(rich_text_array) > 0:
            return rich_text_array[0].get("plain_text", "")
        return None
    
    def _extract_select(self, select_prop: Dict[str, Any]) -> Optional[str]:
        """Extrait la valeur d'une propriété select Notion.
        
        Args:
            select_prop: Propriété select au format Notion.
            
        Returns:
            Nom de l'option sélectionnée ou None.
        """
        if not select_prop:
            return None
        
        # Format Notion select: {"select": {"name": "..."}}
        select_obj = select_prop.get("select", {})
        if select_obj:
            return select_obj.get("name")
        return None
    
    @staticmethod
    def get_vocabulary_database_id() -> str:
        """Retourne l'ID de la base de données Vocabulaire Alteir.
        
        Returns:
            ID de la base de données.
        """
        return VOCABULARY_DATABASE_ID
    
    @staticmethod
    def get_vocabulary_data_source_id() -> str:
        """Retourne l'ID de la data source Vocabulaire Alteir.
        
        Returns:
            ID de la data source.
        """
        return VOCABULARY_DATA_SOURCE_ID
    
    @staticmethod
    def get_dialogue_guide_page_id() -> str:
        """Retourne l'ID de la page Guide des dialogues.
        
        Returns:
            ID de la page.
        """
        return DIALOGUE_GUIDE_PAGE_ID
    
    @staticmethod
    def get_narrative_guide_page_id() -> str:
        """Retourne l'ID de la page Guide de narration.
        
        Returns:
            ID de la page.
        """
        return NARRATIVE_GUIDE_PAGE_ID

