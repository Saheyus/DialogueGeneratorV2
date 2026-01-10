"""Package de sérialisation du contexte.

Ce package fournit des composants modulaires pour sérialiser les structures de contexte
en différents formats (XML, texte) pour le LLM.

Composants principaux:
- ContextSerializer: Façade principale pour la sérialisation
- FieldNormalizer: Normalisation des noms de champs
- SectionMapper: Mapping des sections vers tags XML
- JsonParser: Détection et parsing de contenu JSON
- XmlElementBuilder: Construction d'éléments XML
- InformationsSectionParser: Parsing des sections INFORMATIONS
- TextSerializer: Sérialisation en format texte
"""

from services.context_serializer.context_serializer import ContextSerializer

__all__ = ['ContextSerializer']
