"""Service pour récupérer les données depuis Notion."""
import json
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# IDs Notion
VOCABULARY_DATABASE_ID = "2d16e4d21b458016ba74ccb4fbd92b72"
VOCABULARY_DATA_SOURCE_ID = "2d16e4d2-1b45-8023-b748-000b66bac9a0"
DIALOGUE_GUIDE_PAGE_ID = "1886e4d21b45812094c4fb4e9666e0cb"
NARRATIVE_GUIDE_PAGE_ID = "1886e4d21b4581339cf2ef6486fa001d"


class NotionImportService:
    """Service pour récupérer les données depuis Notion.
    
    Utilise l'API Notion officielle pour récupérer les données.
    """
    
    def __init__(self, api_client=None):
        """Initialise le service d'import Notion.
        
        Args:
            api_client: Client API Notion (optionnel, créé automatiquement si None).
        """
        if api_client is None:
            try:
                from services.notion_api_client import NotionAPIClient
                self.api_client = NotionAPIClient()
            except ValueError as e:
                logger.warning(f"Client Notion API non disponible: {e}")
                self.api_client = None
        else:
            self.api_client = api_client
        
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
    
    def process_vocabulary_page_fetch(self, page_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Traite une page Notion récupérée via fetch pour le vocabulaire.
        
        Le format MCP Notion retourne les propriétés dans une balise <properties>
        avec du JSON dans le texte de la page.
        
        Args:
            page_data: Données de la page Notion (format MCP fetch).
            
        Returns:
            Dictionnaire avec le terme formaté ou None si invalide.
        """
        import json
        import re
        
        try:
            page_text = page_data.get("text", "")
            
            # Extraire le JSON des propriétés depuis la balise <properties>
            match = re.search(r'<properties>\s*(\{.*?\})\s*</properties>', page_text, re.DOTALL)
            if not match:
                logger.warning("Aucune propriété trouvée dans la page")
                return None
            
            properties_json = match.group(1)
            # Nettoyer le JSON (enlever les {{ }} autour des URLs)
            properties_json = re.sub(r'\{\{([^}]+)\}\}', r'\1', properties_json)
            properties = json.loads(properties_json)
            
            # Extraire les propriétés
            terme = properties.get("Terme", "")
            definition = properties.get("Définition", "")
            importance = properties.get("Importance", "Anecdotique")
            categorie = properties.get("Catégorie", "Autre")
            type_term = properties.get("Type", "")
            origine = properties.get("Origine", "")
            
            if not terme:
                return None
            
            return {
                "term": terme,
                "definition": definition or "",
                "importance": importance or "Anecdotique",
                "category": categorie or "Autre",
                "type": type_term or "",
                "origin": origine or ""
            }
        except Exception as e:
            logger.warning(f"Erreur lors du traitement d'une page: {e}")
            return None
    
    def process_guide_page_fetch(self, page_data: Dict[str, Any]) -> Optional[str]:
        """Traite une page Notion récupérée via fetch pour un guide narratif.
        
        Args:
            page_data: Données de la page Notion (format MCP fetch).
            
        Returns:
            Contenu markdown de la page ou None si invalide.
        """
        try:
            page_text = page_data.get("text", "")
            
            # Extraire le contenu depuis la balise <content>
            match = re.search(r'<content>\s*(.*?)\s*</content>', page_text, re.DOTALL)
            if match:
                content = match.group(1)
                # Nettoyer les URLs dans les mentions
                content = re.sub(r'\{\{([^}]+)\}\}', r'\1', content)
                return content
            
            # Si pas de balise <content>, retourner le texte complet
            return page_text
        except Exception as e:
            logger.warning(f"Erreur lors du traitement d'une page guide: {e}")
            return None
    
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
    
    def _extract_property_value(self, prop: Dict[str, Any]) -> Optional[str]:
        """Extrait la valeur d'une propriété Notion (tous types).
        
        Inspiré de la fonction transform_database_row de main.py.
        
        Args:
            prop: Propriété Notion au format API.
            
        Returns:
            Valeur extraite sous forme de string ou None.
        """
        if not prop or prop is None:
            return None
        
        prop_type = prop.get("type")
        
        if prop_type == "title" and prop.get("title"):
            # Title: array de rich_text
            value = " ".join(x.get("plain_text", "") for x in prop["title"])
            return value if value.strip() else None
        
        elif prop_type == "rich_text" and prop.get("rich_text"):
            # Rich text: array de rich_text
            value = " ".join(x.get("plain_text", "") for x in prop["rich_text"])
            return value if value.strip() else None
        
        elif prop_type == "select":
            # Select: {"select": {"name": "..."}}
            select_obj = prop.get("select")
            if select_obj:
                return select_obj.get("name", "")
            return None
        
        elif prop_type == "status":
            # Status: {"status": {"name": "..."}}
            status_obj = prop.get("status")
            if status_obj:
                return status_obj.get("name", "")
            return None
        
        elif prop_type == "multi_select":
            # Multi-select: array d'objets avec "name"
            multi = prop.get("multi_select", [])
            if multi:
                return ", ".join(x.get("name", "") for x in multi)
            return None
        
        elif prop_type == "number":
            # Number: valeur numérique
            num = prop.get("number")
            return str(num) if num is not None else None
        
        elif prop_type == "date":
            # Date: {"date": {"start": "..."}}
            date_obj = prop.get("date")
            if date_obj:
                return date_obj.get("start", "")
            return None
        
        elif prop_type == "checkbox":
            # Checkbox: booléen (on retourne None pour False, "Oui" pour True)
            return "Oui" if prop.get("checkbox") else None
        
        elif prop_type == "url":
            # URL: string
            url = prop.get("url", "")
            return url if url.strip() else None
        
        elif prop_type == "email":
            # Email: string
            email = prop.get("email", "")
            return email if email.strip() else None
        
        elif prop_type == "phone_number":
            # Phone: string
            phone = prop.get("phone_number", "")
            return phone if phone.strip() else None
        
        # Fallback: ignorer les propriétés non reconnues
        return None
    
    def _extract_title(self, title_prop: Dict[str, Any]) -> Optional[str]:
        """Extrait le texte d'une propriété title Notion (compatibilité).
        
        Args:
            title_prop: Propriété title au format Notion.
            
        Returns:
            Texte du titre ou None.
        """
        return self._extract_property_value(title_prop)
    
    def _extract_text(self, text_prop: Dict[str, Any]) -> Optional[str]:
        """Extrait le texte d'une propriété rich_text Notion (compatibilité).
        
        Args:
            text_prop: Propriété rich_text au format Notion.
            
        Returns:
            Texte ou None.
        """
        return self._extract_property_value(text_prop)
    
    def _extract_select(self, select_prop: Dict[str, Any]) -> Optional[str]:
        """Extrait la valeur d'une propriété select Notion (compatibilité).
        
        Args:
            select_prop: Propriété select au format Notion.
            
        Returns:
            Nom de l'option sélectionnée ou None.
        """
        return self._extract_property_value(select_prop)
    
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
    
    async def sync_vocabulary(self) -> List[Dict[str, Any]]:
        """Synchronise le vocabulaire depuis Notion.
        
        Returns:
            Liste des termes formatés.
        """
        if not self.api_client:
            raise ValueError("Client Notion API non disponible. Configurez NOTION_API_KEY.")
        
        # Récupérer toutes les pages de la base de données
        pages = await self.api_client.query_database(VOCABULARY_DATABASE_ID)
        
        terms = []
        for page in pages:
            try:
                properties = page.get("properties", {})
                
                # Utiliser la méthode complète d'extraction (comme dans main.py)
                terme = self._extract_property_value(properties.get("Terme", {}))
                definition = self._extract_property_value(properties.get("Définition", {}))
                importance = self._extract_property_value(properties.get("Importance", {}))
                categorie = self._extract_property_value(properties.get("Catégorie", {}))
                type_term = self._extract_property_value(properties.get("Type", {}))
                origine = self._extract_property_value(properties.get("Origine", {}))
                
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
                logger.warning(f"Erreur lors du traitement d'une page: {e}")
                continue
        
        logger.info(f"Synchronisation de {len(terms)} termes depuis Notion")
        return terms
    
    async def sync_guide(self, page_id: str) -> Optional[str]:
        """Synchronise un guide narratif depuis Notion.
        
        Args:
            page_id: ID de la page Notion.
            
        Returns:
            Contenu markdown du guide ou None si erreur.
        """
        if not self.api_client:
            raise ValueError("Client Notion API non disponible. Configurez NOTION_API_KEY.")
        
        try:
            content = await self.api_client.get_page_content(page_id)
            logger.info(f"Guide synchronisé depuis Notion (page_id: {page_id}, {len(content)} caractères)")
            return content
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation du guide: {e}")
            return None

