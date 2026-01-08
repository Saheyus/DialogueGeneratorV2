"""Utilitaires XML partagés pour la construction de prompts.

Ce module fournit des fonctions réutilisables pour :
- L'échappement de texte XML
- L'indentation d'éléments XML
- La validation de contenu XML
- La création de documents XML complets
"""
import xml.etree.ElementTree as ET
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def escape_xml_text(text: str) -> str:
    """Échappe les caractères spéciaux XML dans un texte.
    
    Gère :
    - Les caractères XML de base (&, <, >)
    - Les caractères de contrôle (0x00-0x1F sauf 0x09, 0x0A, 0x0D)
    - Les entités déjà échappées (évite le double échappement)
    
    Args:
        text: Texte à échapper.
        
    Returns:
        Texte échappé pour inclusion dans XML.
    """
    if not text:
        return ""
    
    # Éviter le double échappement : si le texte contient déjà des entités échappées,
    # on ne les échappe pas à nouveau
    # Pattern pour détecter les entités XML valides : &amp; &lt; &gt; &quot; &apos; ou &#...;
    entity_pattern = r'&(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);'
    
    # Remplacer temporairement les entités existantes par des placeholders uniques
    placeholders = {}
    matches = list(re.finditer(entity_pattern, text))
    # Traiter de la fin vers le début pour préserver les indices
    for match in reversed(matches):
        placeholder = f"__ENTITY_PLACEHOLDER_{len(placeholders)}__"
        placeholders[placeholder] = match.group(0)
        text = text[:match.start()] + placeholder + text[match.end():]
    
    # Échapper les & restants (qui ne sont pas dans des entités)
    text = text.replace("&", "&amp;")
    
    # Échapper < et >
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    
    # Restaurer les entités originales (qui étaient déjà échappées)
    for placeholder, entity in placeholders.items():
        text = text.replace(placeholder, entity)
    
    # Supprimer les caractères de contrôle invalides (0x00-0x08, 0x0B-0x0C, 0x0E-0x1F)
    # Garder : 0x09 (tab), 0x0A (LF), 0x0D (CR)
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F]', '', text)
    
    return text


def indent_xml_element(elem: ET.Element, level: int = 0) -> None:
    """Indente récursivement un élément XML.
    
    Modifie l'élément en place en ajoutant des sauts de ligne et des espaces
    pour une indentation lisible.
    
    Args:
        elem: Élément XML à indenter.
        level: Niveau d'indentation initial (0 par défaut).
    """
    i = "\n" + "  " * level
    if len(elem):
        # Ne pas modifier le texte existant s'il contient du contenu
        # Seulement ajouter l'indentation si le texte est None ou vide
        if elem.text is None or (elem.text and not elem.text.strip()):
            elem.text = i + "  "
        # Ne pas toucher au texte s'il existe déjà
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for child in elem:
            indent_xml_element(child, level + 1)
            # Toujours définir le tail pour l'indentation après chaque enfant
            # Le tail est le texte après la balise fermante de l'enfant
            child.tail = i
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        # Élément sans enfants : définir le tail pour l'indentation
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def validate_xml_content(xml_str: str) -> bool:
    """Valide basiquement le contenu XML.
    
    Vérifie que le XML peut être parsé sans erreur.
    Ne valide pas contre un schéma XSD, seulement la structure de base.
    
    Args:
        xml_str: Chaîne XML à valider.
        
    Returns:
        True si le XML est valide, False sinon.
    """
    if not xml_str or not xml_str.strip():
        return False
    
    try:
        # Enlever la déclaration XML si présente pour le parsing
        xml_content = xml_str
        if xml_content.startswith('<?xml'):
            xml_content = xml_content.split('?>', 1)[-1].strip()
        
        # Parser le XML
        ET.fromstring(xml_content)
        return True
    except ET.ParseError as e:
        logger.error(f"Erreur de parsing XML: {e}")
        logger.error(f"XML invalide (premiers 500 caractères): {xml_content[:500]}")
        # Logger plus de détails sur l'erreur
        # Extraire ligne et colonne depuis le message d'erreur (format: "line X, column Y")
        import re
        lineno = None
        offset = None
        msg = str(e)
        match = re.search(r'line (\d+), column (\d+)', msg)
        if match:
            lineno = int(match.group(1))
            offset = int(match.group(2))
        elif hasattr(e, 'position') and e.position:
            lineno, offset = e.position
        elif hasattr(e, 'lineno'):
            lineno = e.lineno
            offset = getattr(e, 'offset', None) or getattr(e, 'colno', None)
        
        if lineno and offset:
            lines = xml_content.split('\n')
            if lineno <= len(lines):
                error_line = lines[lineno - 1]
                logger.error(f"Ligne {lineno}, colonne {offset}: {repr(error_line)}")
                if offset <= len(error_line):
                    start = max(0, offset - 10)
                    end = min(len(error_line), offset + 10)
                    logger.error(f"Caractère problématique (colonne {offset}): {repr(error_line[start:end])}")
        return False
    except Exception as e:
        logger.error(f"Erreur lors de la validation XML: {e}")
        logger.error(f"XML invalide (premiers 500 caractères): {xml_content[:500]}")
        return False


def create_xml_document(root_elem: ET.Element) -> str:
    """Crée un document XML complet avec déclaration.
    
    Args:
        root_elem: Élément racine du document XML.
        
    Returns:
        Document XML complet avec déclaration XML et encodage UTF-8.
    """
    # Indenter l'élément racine
    indent_xml_element(root_elem)
    
    # Convertir en string
    xml_str = ET.tostring(root_elem, encoding='unicode', method='xml')
    
    # Ajouter la déclaration XML
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str


def parse_xml_element(xml_str: str) -> Optional[ET.Element]:
    """Parse une chaîne XML et retourne l'élément racine.
    
    Gère automatiquement la présence ou l'absence de déclaration XML.
    
    Args:
        xml_str: Chaîne XML à parser.
        
    Returns:
        Élément racine XML, ou None si le parsing échoue.
    """
    if not xml_str or not xml_str.strip():
        return None
    
    try:
        # Enlever la déclaration XML si présente
        xml_content = xml_str
        if xml_content.startswith('<?xml'):
            xml_content = xml_content.split('?>', 1)[-1].strip()
        
        return ET.fromstring(xml_content)
    except ET.ParseError as e:
        logger.warning(f"Erreur de parsing XML: {e}")
        return None
    except Exception as e:
        logger.warning(f"Erreur lors du parsing XML: {e}")
        return None


def extract_text_from_element(elem: ET.Element) -> str:
    """Extrait récursivement tout le texte d'un élément XML.
    
    Parcourt récursivement l'élément et ses enfants pour extraire
    tout le texte (`.text` et `.tail` de chaque élément).
    Préserve les sauts de ligne et la structure.
    
    Args:
        elem: Élément XML dont on veut extraire le texte.
        
    Returns:
        Texte brut sans balises XML, avec sauts de ligne préservés.
    """
    if elem is None:
        return ""
    
    parts = []
    
    # Ajouter le texte de l'élément lui-même
    if elem.text:
        parts.append(elem.text)
    
    # Parcourir récursivement les enfants
    for child in elem:
        child_text = extract_text_from_element(child)
        if child_text:
            parts.append(child_text)
        
        # Ajouter le texte après l'enfant (tail)
        if child.tail:
            parts.append(child.tail)
    
    return "".join(parts)
