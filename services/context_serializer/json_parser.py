"""Détection et parsing de contenu JSON dans les sections.

Ce module fournit des utilitaires pour détecter si du contenu est au format JSON
et le parser en structures Python (dict/list).
"""
import json
import re
import logging
from typing import Any, Optional, Dict, List

logger = logging.getLogger(__name__)


class JsonParser:
    """Détecte et parse le contenu JSON dans les sections.
    
    Gère à la fois le JSON pur (commence par { ou [) et le JSON embedded
    dans du texte.
    """
    
    def parse(self, content: str) -> Optional[Dict | List]:
        """Détecte et parse le contenu JSON si présent.
        
        Essaie de parser le contenu comme JSON. Si le contenu commence par
        { ou [, c'est probablement du JSON pur. Sinon, cherche du JSON embedded.
        
        Args:
            content: Contenu à analyser.
            
        Returns:
            Dict ou List si le contenu est du JSON valide, None sinon.
            
        Example:
            >>> parser = JsonParser()
            >>> parser.parse('{"key": "value"}')
            {'key': 'value'}
            >>> parser.parse('[1, 2, 3]')
            [1, 2, 3]
            >>> parser.parse('Normal text')
            None
        """
        if not content or not content.strip():
            return None
        
        content_stripped = content.strip()
        
        # Détecter si c'est du JSON (commence par { ou [)
        if content_stripped.startswith('{') or content_stripped.startswith('['):
            try:
                parsed = json.loads(content_stripped)
                if isinstance(parsed, (dict, list)):
                    logger.debug(
                        f"JSON détecté et parsé avec succès "
                        f"(type: {type(parsed).__name__}, "
                        f"clés: {list(parsed.keys()) if isinstance(parsed, dict) else len(parsed)})"
                    )
                    return parsed
            except (json.JSONDecodeError, ValueError) as e:
                logger.debug(f"JSON parsing failed: {e}, content preview: {content_stripped[:100]}")
                return None
        
        # Essayer de détecter du JSON même s'il y a du texte avant
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}|\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]'
        json_matches = re.findall(json_pattern, content_stripped, re.DOTALL)
        if json_matches:
            for json_match in sorted(json_matches, key=len, reverse=True):
                try:
                    parsed = json.loads(json_match)
                    if isinstance(parsed, (dict, list)):
                        logger.debug(f"JSON détecté dans le contenu (type: {type(parsed).__name__})")
                        return parsed
                except (json.JSONDecodeError, ValueError):
                    continue
        
        return None
