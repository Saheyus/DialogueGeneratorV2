"""Module de sérialisation du contexte (refactoré).

Ce module réexporte ContextSerializer depuis le package context_serializer.
Import maintenu pour compatibilité avec le code existant.

Le code a été refactorisé en modules spécialisés pour une meilleure maintenabilité:
- field_normalizer: Normalisation des noms de champs
- section_mapper: Mapping des sections vers tags XML
- json_parser: Détection et parsing JSON
- xml_element_builder: Construction d'éléments XML
- informations_parser: Parsing des sections INFORMATIONS
- text_serializer: Sérialisation en format texte
- context_serializer: Façade principale

Pour plus de détails, voir services/context_serializer/
"""
from services.context_serializer.context_serializer import ContextSerializer

__all__ = ['ContextSerializer']
