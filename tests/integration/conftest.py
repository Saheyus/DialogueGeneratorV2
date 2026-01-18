"""Fixtures partagées pour les tests d'intégration."""
import pytest
from core.context.context_builder import ContextBuilder


@pytest.fixture
def context_builder_with_real_data():
    """Construit un ContextBuilder avec données GDD réelles.
    
    Skip automatiquement si les données GDD ne sont pas disponibles.
    """
    builder = ContextBuilder()
    builder.load_gdd_files()
    
    # Vérifier que les données sont chargées
    if not builder.characters:
        pytest.skip("Données GDD non disponibles (aucun personnage chargé)")
    
    return builder


@pytest.fixture
def context_construction_service(context_builder_with_real_data):
    """Expose le ContextConstructionService du builder.
    
    Dépend de context_builder_with_real_data pour avoir les données chargées.
    """
    builder = context_builder_with_real_data
    
    if builder._context_construction_service is None:
        pytest.skip("ContextConstructionService non initialisé")
    
    return builder._context_construction_service
