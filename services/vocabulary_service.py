"""Service pour gérer le vocabulaire Alteir avec filtrage par importance."""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from api.utils.notion_cache import get_notion_cache

logger = logging.getLogger(__name__)

# Ordre d'importance (du plus au moins important)
IMPORTANCE_ORDER = {
    "Majeur": 1,
    "Important": 2,
    "Modéré": 3,
    "Secondaire": 4,
    "Mineur": 5,
    "Anecdotique": 6
}

DEFAULT_MIN_IMPORTANCE = "Important"


class VocabularyService:
    """Service pour gérer le vocabulaire Alteir.
    
    Charge le vocabulaire depuis le cache Notion, filtre par niveau d'importance,
    et formate pour injection dans les prompts système.
    """
    
    def __init__(self, cache=None):
        """Initialise le service de vocabulaire.
        
        Args:
            cache: Instance de NotionCache. Si None, utilise le singleton.
        """
        self.cache = cache or get_notion_cache()
        logger.info("VocabularyService initialisé")
    
    def load_vocabulary(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Charge le vocabulaire depuis le cache.
        
        Args:
            force_refresh: Si True, force le rechargement (ignore le cache).
            
        Returns:
            Liste des termes avec leurs métadonnées.
        """
        if force_refresh:
            logger.info("Rechargement forcé du vocabulaire (cache ignoré)")
            return []
        
        vocabulary_data = self.cache.get("vocabulary")
        
        if vocabulary_data is None:
            logger.warning("Vocabulaire non trouvé dans le cache. Synchronisation nécessaire.")
            return []
        
        terms = vocabulary_data.get("terms", [])
        logger.info(f"Vocabulaire chargé: {len(terms)} termes")
        return terms
    
    def filter_by_importance(
        self,
        terms: List[Dict[str, Any]],
        min_level: str = DEFAULT_MIN_IMPORTANCE
    ) -> List[Dict[str, Any]]:
        """Filtre les termes par niveau d'importance.
        
        Inclut le niveau sélectionné + tous les niveaux plus importants.
        
        Args:
            terms: Liste des termes à filtrer.
            min_level: Niveau d'importance minimum ("Majeur", "Important", etc.).
                      Si "Modéré" est sélectionné, inclut Majeur + Important + Modéré.
        
        Returns:
            Liste des termes filtrés, triés par importance puis alphabétiquement.
        """
        if not terms:
            return []
        
        # Vérifier que le niveau est valide
        if min_level not in IMPORTANCE_ORDER:
            logger.warning(f"Niveau d'importance invalide: {min_level}. Utilisation du défaut: {DEFAULT_MIN_IMPORTANCE}")
            min_level = DEFAULT_MIN_IMPORTANCE
        
        min_order = IMPORTANCE_ORDER[min_level]
        
        # Filtrer les termes
        filtered_terms = [
            term for term in terms
            if term.get("importance") in IMPORTANCE_ORDER
            and IMPORTANCE_ORDER[term["importance"]] <= min_order
        ]
        
        # Trier par importance (ordre croissant) puis alphabétiquement par terme
        filtered_terms.sort(
            key=lambda t: (
                IMPORTANCE_ORDER.get(t.get("importance", "Anecdotique"), 99),
                t.get("term", "").lower()
            )
        )
        
        logger.info(
            f"Filtrage vocabulaire: {len(filtered_terms)}/{len(terms)} termes "
            f"(niveau minimum: {min_level})"
        )
        
        return filtered_terms
    
    def format_for_prompt(
        self,
        terms: List[Dict[str, Any]],
        max_terms: Optional[int] = None
    ) -> str:
        """Formate les termes pour injection dans le prompt système.
        
        Format: `[VOCABULAIRE ALTEIR] Terme: définition`
        
        Args:
            terms: Liste des termes à formater.
            max_terms: Nombre maximum de termes à inclure (None = tous).
        
        Returns:
            Texte formaté pour injection dans le prompt.
        """
        if not terms:
            return ""
        
        # Limiter le nombre de termes si nécessaire
        terms_to_format = terms[:max_terms] if max_terms else terms
        
        lines = ["[VOCABULAIRE ALTEIR]"]
        
        for term in terms_to_format:
            terme = term.get("term", "")
            definition = term.get("definition", "")
            
            if terme:
                if definition:
                    lines.append(f"{terme}: {definition}")
                else:
                    lines.append(f"{terme}: (définition non disponible)")
        
        formatted_text = "\n".join(lines)
        
        if max_terms and len(terms) > max_terms:
            formatted_text += f"\n\n(Note: {len(terms) - max_terms} autres termes non affichés)"
        
        logger.debug(f"Formatage vocabulaire: {len(terms_to_format)} termes formatés")
        return formatted_text
    
    def get_terms_by_category(
        self,
        terms: List[Dict[str, Any]],
        category: str
    ) -> List[Dict[str, Any]]:
        """Filtre les termes par catégorie.
        
        Args:
            terms: Liste des termes à filtrer.
            category: Catégorie à filtrer (ex: "Magie", "Technologie").
        
        Returns:
            Liste des termes de la catégorie spécifiée.
        """
        filtered = [
            term for term in terms
            if term.get("category") == category
        ]
        
        logger.debug(f"Filtrage par catégorie '{category}': {len(filtered)} termes")
        return filtered
    
    def get_statistics(self, terms: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcule des statistiques sur le vocabulaire.
        
        Args:
            terms: Liste des termes.
        
        Returns:
            Dictionnaire avec statistiques (nombre par importance, par catégorie, etc.).
        """
        stats = {
            "total": len(terms),
            "by_importance": {},
            "by_category": {},
            "by_type": {}
        }
        
        for term in terms:
            # Par importance
            importance = term.get("importance", "Anecdotique")
            stats["by_importance"][importance] = stats["by_importance"].get(importance, 0) + 1
            
            # Par catégorie
            category = term.get("category", "Autre")
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
            
            # Par type
            type_term = term.get("type", "")
            if type_term:
                stats["by_type"][type_term] = stats["by_type"].get(type_term, 0) + 1
        
        return stats
    
    def count_terms_by_importance(
        self,
        terms: List[Dict[str, Any]],
        min_level: str = DEFAULT_MIN_IMPORTANCE
    ) -> int:
        """Compte le nombre de termes qui seront inclus pour un niveau d'importance donné.
        
        Args:
            terms: Liste complète des termes.
            min_level: Niveau d'importance minimum.
        
        Returns:
            Nombre de termes qui seront inclus.
        """
        filtered = self.filter_by_importance(terms, min_level)
        return len(filtered)

