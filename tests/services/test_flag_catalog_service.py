"""Tests unitaires pour FlagCatalogService."""
import pytest
import csv
from pathlib import Path
from services.flag_catalog_service import FlagCatalogService


@pytest.fixture
def temp_flag_csv(tmp_path: Path) -> Path:
    """Crée un CSV de test temporaire avec quelques flags."""
    csv_path = tmp_path / "FlagCatalog.csv"
    
    # Créer le CSV avec des données de test
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Id", "Type", "Category", "Label", "Description", "DefaultValue", "Tags", "IsFavorite"])
        writer.writerow(["TEST_BOOL_FLAG", "bool", "Event", "Test Bool", "A test boolean flag", "false", "test;bool", "true"])
        writer.writerow(["TEST_INT_FLAG", "int", "Stat", "Test Int", "A test integer flag", "5", "test;stat", "false"])
        writer.writerow(["TEST_FLOAT_FLAG", "float", "Stat", "Test Float", "A test float flag", "2.5", "test;stat", "false"])
    
    return csv_path


def test_load_definitions(temp_flag_csv: Path):
    """Test du chargement des définitions depuis le CSV."""
    service = FlagCatalogService(csv_path=temp_flag_csv)
    flags = service.load_definitions()
    
    assert len(flags) == 3
    
    # Vérifier le premier flag
    flag_bool = flags[0]
    assert flag_bool["id"] == "TEST_BOOL_FLAG"
    assert flag_bool["type"] == "bool"
    assert flag_bool["category"] == "Event"
    assert flag_bool["label"] == "Test Bool"
    assert flag_bool["description"] == "A test boolean flag"
    assert flag_bool["defaultValue"] == "false"
    assert flag_bool["tags"] == ["test", "bool"]
    assert flag_bool["isFavorite"] is True
    
    # Vérifier le deuxième flag
    flag_int = flags[1]
    assert flag_int["id"] == "TEST_INT_FLAG"
    assert flag_int["type"] == "int"
    assert flag_int["isFavorite"] is False


def test_load_definitions_cache(temp_flag_csv: Path):
    """Test du cache du chargement."""
    service = FlagCatalogService(csv_path=temp_flag_csv)
    
    # Premier chargement
    flags1 = service.load_definitions()
    assert len(flags1) == 3
    
    # Deuxième chargement (depuis le cache)
    flags2 = service.load_definitions()
    assert flags1 is flags2  # Même objet en mémoire


def test_search_by_query(temp_flag_csv: Path):
    """Test de la recherche par terme."""
    service = FlagCatalogService(csv_path=temp_flag_csv)
    
    # Recherche par ID
    results = service.search(query="BOOL")
    assert len(results) == 1
    assert results[0]["id"] == "TEST_BOOL_FLAG"
    
    # Recherche par label
    results = service.search(query="Test Int")
    assert len(results) == 1
    assert results[0]["id"] == "TEST_INT_FLAG"
    
    # Recherche par tag
    results = service.search(query="stat")
    assert len(results) == 2


def test_search_by_category(temp_flag_csv: Path):
    """Test de la recherche par catégorie."""
    service = FlagCatalogService(csv_path=temp_flag_csv)
    
    results = service.search(category="Event")
    assert len(results) == 1
    assert results[0]["id"] == "TEST_BOOL_FLAG"
    
    results = service.search(category="Stat")
    assert len(results) == 2


def test_search_favorites_only(temp_flag_csv: Path):
    """Test du filtre favoris."""
    service = FlagCatalogService(csv_path=temp_flag_csv)
    
    results = service.search(favorites_only=True)
    assert len(results) == 1
    assert results[0]["id"] == "TEST_BOOL_FLAG"


def test_search_combined_filters(temp_flag_csv: Path):
    """Test de la combinaison de filtres."""
    service = FlagCatalogService(csv_path=temp_flag_csv)
    
    # Catégorie Stat + recherche "int"
    results = service.search(query="int", category="Stat")
    assert len(results) == 1
    assert results[0]["id"] == "TEST_INT_FLAG"


def test_upsert_definition_create(temp_flag_csv: Path):
    """Test de la création d'une nouvelle définition."""
    service = FlagCatalogService(csv_path=temp_flag_csv)
    
    new_flag = {
        "id": "NEW_FLAG",
        "type": "bool",
        "category": "Choice",
        "label": "New Flag",
        "description": "A newly created flag",
        "defaultValue": "true",
        "tags": ["new", "test"],
        "isFavorite": False
    }
    
    service.upsert_definition(new_flag)
    
    # Recharger et vérifier
    service.reload()
    flags = service.load_definitions()
    assert len(flags) == 4
    
    created_flag = next((f for f in flags if f["id"] == "NEW_FLAG"), None)
    assert created_flag is not None
    assert created_flag["label"] == "New Flag"
    assert created_flag["tags"] == ["new", "test"]


def test_upsert_definition_update(temp_flag_csv: Path):
    """Test de la mise à jour d'une définition existante."""
    service = FlagCatalogService(csv_path=temp_flag_csv)
    
    updated_flag = {
        "id": "TEST_BOOL_FLAG",
        "type": "bool",
        "category": "Event",
        "label": "Updated Bool Flag",
        "description": "Updated description",
        "defaultValue": "true",
        "tags": ["updated"],
        "isFavorite": False
    }
    
    service.upsert_definition(updated_flag)
    
    # Recharger et vérifier
    service.reload()
    flags = service.load_definitions()
    assert len(flags) == 3  # Pas de nouveau flag, juste une mise à jour
    
    updated = next((f for f in flags if f["id"] == "TEST_BOOL_FLAG"), None)
    assert updated is not None
    assert updated["label"] == "Updated Bool Flag"
    assert updated["description"] == "Updated description"
    assert updated["tags"] == ["updated"]
    assert updated["isFavorite"] is False


def test_upsert_definition_invalid(temp_flag_csv: Path):
    """Test de l'upsert avec définition invalide."""
    service = FlagCatalogService(csv_path=temp_flag_csv)
    
    # Manque le champ "label"
    invalid_flag = {
        "id": "INVALID_FLAG",
        "type": "bool",
        "category": "Event"
    }
    
    with pytest.raises(ValueError, match="Champs requis manquants"):
        service.upsert_definition(invalid_flag)
    
    # Type invalide
    invalid_type_flag = {
        "id": "INVALID_TYPE",
        "type": "invalid_type",
        "category": "Event",
        "label": "Invalid"
    }
    
    with pytest.raises(ValueError, match="Type invalide"):
        service.upsert_definition(invalid_type_flag)


def test_toggle_favorite(temp_flag_csv: Path):
    """Test du toggle du statut favori."""
    service = FlagCatalogService(csv_path=temp_flag_csv)
    
    # TEST_INT_FLAG est initialement non-favori
    service.toggle_favorite("TEST_INT_FLAG", True)
    
    # Recharger et vérifier
    service.reload()
    flags = service.load_definitions()
    flag = next((f for f in flags if f["id"] == "TEST_INT_FLAG"), None)
    assert flag is not None
    assert flag["isFavorite"] is True
    
    # Toggle à nouveau
    service.toggle_favorite("TEST_INT_FLAG", False)
    service.reload()
    flags = service.load_definitions()
    flag = next((f for f in flags if f["id"] == "TEST_INT_FLAG"), None)
    assert flag is not None
    assert flag["isFavorite"] is False


def test_toggle_favorite_not_found(temp_flag_csv: Path):
    """Test du toggle d'un flag inexistant."""
    service = FlagCatalogService(csv_path=temp_flag_csv)
    
    with pytest.raises(ValueError, match="Flag introuvable"):
        service.toggle_favorite("NON_EXISTENT_FLAG", True)


def test_load_definitions_missing_file():
    """Test du chargement avec fichier manquant."""
    non_existent_path = Path("/tmp/non_existent_flag_catalog.csv")
    service = FlagCatalogService(csv_path=non_existent_path)
    
    # Devrait retourner une liste vide au lieu de lever une erreur
    flags = service.load_definitions()
    assert flags == []


def test_reload(temp_flag_csv: Path):
    """Test du rechargement forcé du cache."""
    service = FlagCatalogService(csv_path=temp_flag_csv)
    
    # Premier chargement
    flags1 = service.load_definitions()
    assert len(flags1) == 3
    
    # Modifier le CSV directement
    with open(temp_flag_csv, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["NEW_FLAG_EXTERNAL", "bool", "Event", "External", "Added externally", "false", "external", "false"])
    
    # Sans reload, le cache est utilisé
    flags2 = service.load_definitions()
    assert len(flags2) == 3
    
    # Avec reload, le nouveau flag est visible
    service.reload()
    flags3 = service.load_definitions()
    assert len(flags3) == 4
