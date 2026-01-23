"""Normalisation des noms de champs pour XML et comparaison.

Ce module fournit des utilitaires pour normaliser les noms de champs de manière
cohérente, en gérant les accents, les espaces et les caractères spéciaux.
"""
import re
import unicodedata
import logging

logger = logging.getLogger(__name__)


class FieldNormalizer:
    """Normalise les noms de champs pour comparaison et génération de tags XML.
    
    Gère la normalisation Unicode, la suppression des accents, et la création
    de tags XML valides.
    """
    
    def normalize_for_comparison(self, field_name: str) -> str:
        """Normalise un nom de champ pour la comparaison (insensible à la casse, accents).
        
        Utilisé pour détecter les duplications de champs et comparer les noms
        indépendamment de la casse et des accents.
        
        Args:
            field_name: Nom du champ à normaliser.
            
        Returns:
            Nom de champ normalisé pour comparaison (lowercase, sans accents).
            
        Example:
            >>> normalizer = FieldNormalizer()
            >>> normalizer.normalize_for_comparison("Identité")
            'identite'
            >>> normalizer.normalize_for_comparison("Désir Principal")
            'desir_principal'
        """
        # Normaliser Unicode (NFKD) pour convertir les accents
        normalized = unicodedata.normalize('NFKD', field_name.lower().strip())
        # Supprimer les caractères de combinaison (diacritiques)
        normalized = ''.join(c for c in normalized if not unicodedata.combining(c))
        # Remplacer espaces et caractères spéciaux par underscores
        normalized = re.sub(r'[^a-z0-9_]', '_', normalized)
        normalized = re.sub(r'_+', '_', normalized)
        return normalized.strip('_')
    
    def normalize_for_xml_tag(self, field_name: str) -> str:
        """Normalise un nom de champ pour créer un tag XML valide.
        
        Convertit un nom de champ quelconque en tag XML valide selon les règles:
        - Lowercase
        - Pas d'accents
        - Pas de caractères spéciaux (seulement a-z, 0-9, _)
        - Ne commence pas par un chiffre
        
        Args:
            field_name: Nom du champ à convertir.
            
        Returns:
            Tag XML valide.
            
        Example:
            >>> normalizer = FieldNormalizer()
            >>> normalizer.normalize_for_xml_tag("Désir Principal")
            'desir_principal'
            >>> normalizer.normalize_for_xml_tag("2ème Nom")
            'field_2eme_nom'
        """
        # Commencer avec la même base que la comparaison
        tag = field_name.lower().strip()
        
        # Remplacer les caractères accentués courants avant normalisation complète
        tag = tag.replace("é", "e").replace("è", "e").replace("ê", "e")
        tag = tag.replace("à", "a").replace("â", "a")
        tag = tag.replace("ù", "u").replace("û", "u")
        tag = tag.replace("î", "i").replace("ï", "i")
        tag = tag.replace("ô", "o")
        tag = tag.replace("ç", "c")
        
        # Normaliser les caractères Unicode (NFKD) pour convertir les caractères accentués
        tag = unicodedata.normalize('NFKD', tag)
        # Supprimer les caractères de combinaison (diacritiques)
        tag = ''.join(c for c in tag if not unicodedata.combining(c))
        
        # Nettoyer le tag pour qu'il soit valide en XML
        tag = re.sub(r'[^a-z0-9_]', '_', tag)
        tag = re.sub(r'_+', '_', tag)
        tag = tag.strip('_')
        
        # Validation et fallback
        if not tag:
            tag = "field"
        elif tag[0].isdigit():
            tag = "field_" + tag
        
        return tag
