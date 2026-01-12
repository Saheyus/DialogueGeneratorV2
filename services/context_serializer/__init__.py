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

Note: Le fichier `services/context_serializer.py` (racine du package) est un wrapper
de compatibilité qui réexporte ContextSerializer. Il est maintenu pour rétrocompatibilité
avec le code existant. Les nouveaux imports devraient utiliser directement ce package.
"""

from services.context_serializer.context_serializer import ContextSerializer

__all__ = ['ContextSerializer']
