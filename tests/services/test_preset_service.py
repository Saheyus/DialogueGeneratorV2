"""Tests unitaires pour PresetService."""
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from uuid import UUID
from services.preset_service import PresetService, PresetValidationResult
from api.schemas.preset import Preset, PresetMetadata, PresetConfiguration


@pytest.fixture
def mock_config_service() -> Mock:
    """Fixture pour ConfigurationService mocké."""
    service = Mock()
    # Mock GDD data structure
    service.get_all_characters.return_value = [
        {"Nom": "Akthar", "id": "char-001"},
        {"Nom": "Neth", "id": "char-002"}
    ]
    service.get_all_locations.return_value = [
        {"Nom": "Avili de l'Éternel Retour", "id": "loc-001"},
        {"Nom": "Temple", "id": "loc-002"}
    ]
    return service


@pytest.fixture
def mock_context_builder() -> Mock:
    """Fixture pour ContextBuilder mocké."""
    builder = Mock()
    builder.gdd_data = {
        "Personnages": [
            {"Nom": "Akthar", "id": "char-001"},
            {"Nom": "Neth", "id": "char-002"}
        ],
        "Lieux": [
            {"Nom": "Avili de l'Éternel Retour", "id": "loc-001"},
            {"Nom": "Temple", "id": "loc-002"}
        ]
    }
    builder.get_characters_names.return_value = ["Akthar", "Neth"]
    builder.get_locations_names.return_value = ["Avili de l'Éternel Retour", "Temple"]
    return builder


@pytest.fixture
def preset_service(tmp_path: Path, mock_config_service: Mock, mock_context_builder: Mock) -> PresetService:
    """Fixture pour PresetService avec dossier temporaire."""
    service = PresetService(
        config_service=mock_config_service,
        context_builder=mock_context_builder,
        presets_dir=tmp_path / "presets"
    )
    return service


@pytest.fixture
def sample_preset_data() -> dict:
    """Fixture pour données preset valides."""
    return {
        "name": "Test Preset",
        "icon": "🎭",
        "configuration": {
            "characters": ["Akthar", "Neth"],
            "locations": ["Avili de l'Éternel Retour", "Temple"],
            "region": "Avili de l'Éternel Retour",
            "subLocation": "Temple",
            "sceneType": "Première rencontre",
            "instructions": "Test scene instructions",
            "fieldConfigs": {}
        }
    }


class TestPresetServiceCreate:
    """Tests pour création de presets."""
    
    def test_create_preset_success(self, preset_service: PresetService, sample_preset_data: dict):
        """Given: données preset valides
        When: create_preset est appelé
        Then: preset créé avec UUID et fichier JSON sauvegardé
        """
        preset, cleanup_message = preset_service.create_preset(sample_preset_data)
        
        # Vérifier preset retourné
        assert preset.name == "Test Preset"
        assert preset.icon == "🎭"
        assert preset.configuration.characters == ["Akthar", "Neth"]
        assert isinstance(preset.id, str)
        assert UUID(preset.id)  # Valide UUID format
        
        # Vérifier fichier créé
        preset_file = preset_service.presets_dir / f"{preset.id}.json"
        assert preset_file.exists()
        
        with open(preset_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
            assert saved_data["name"] == "Test Preset"
            assert saved_data["id"] == preset.id
    
    def test_create_preset_auto_creates_directory(self, tmp_path: Path, mock_config_service: Mock, 
                                                   mock_context_builder: Mock, sample_preset_data: dict):
        """Given: dossier presets n'existe pas
        When: create_preset est appelé
        Then: dossier créé automatiquement
        """
        presets_dir = tmp_path / "nested" / "presets"
        assert not presets_dir.exists()
        
        service = PresetService(mock_config_service, mock_context_builder, presets_dir)
        preset, _ = service.create_preset(sample_preset_data)
        
        assert presets_dir.exists()
        assert (presets_dir / f"{preset.id}.json").exists()
    
    def test_create_preset_generates_unique_ids(self, preset_service: PresetService, sample_preset_data: dict):
        """Given: plusieurs presets créés
        When: create_preset appelé plusieurs fois
        Then: chaque preset a un UUID unique
        """
        preset1, _ = preset_service.create_preset(sample_preset_data)
        preset2, _ = preset_service.create_preset(sample_preset_data)
        
        assert preset1.id != preset2.id
        assert UUID(preset1.id)
        assert UUID(preset2.id)


class TestPresetServiceList:
    """Tests pour liste des presets."""
    
    def test_list_presets_empty(self, preset_service: PresetService):
        """Given: aucun preset sauvegardé
        When: list_presets est appelé
        Then: liste vide retournée
        """
        presets = preset_service.list_presets()
        assert presets == []
    
    def test_list_presets_success(self, preset_service: PresetService, sample_preset_data: dict):
        """Given: plusieurs presets sauvegardés
        When: list_presets est appelé
        Then: tous les presets retournés
        """
        preset1, _ = preset_service.create_preset({**sample_preset_data, "name": "Preset 1"})
        preset2, _ = preset_service.create_preset({**sample_preset_data, "name": "Preset 2"})
        
        presets = preset_service.list_presets()
        
        assert len(presets) == 2
        preset_names = [p.name for p in presets]
        assert "Preset 1" in preset_names
        assert "Preset 2" in preset_names
    
    def test_list_presets_skips_corrupted_files(self, preset_service: PresetService, sample_preset_data: dict):
        """Given: un fichier JSON corrompu dans dossier presets
        When: list_presets est appelé
        Then: fichier corrompu ignoré, log erreur, pas de crash
        """
        # Créer preset valide
        preset_service.create_preset(sample_preset_data)
        
        # Créer fichier JSON corrompu
        corrupted_file = preset_service.presets_dir / "corrupted.json"
        with open(corrupted_file, "w", encoding="utf-8") as f:
            f.write("{ invalid json")
        
        with patch("services.preset_service.logger") as mock_logger:
            presets = preset_service.list_presets()
            
            # Seul le preset valide retourné
            assert len(presets) == 1
            assert presets[0].name == "Test Preset"
            
            # Log erreur appelé
            mock_logger.error.assert_called_once()


class TestPresetServiceLoad:
    """Tests pour chargement preset."""
    
    def test_load_preset_success(self, preset_service: PresetService, sample_preset_data: dict):
        """Given: preset existant
        When: load_preset est appelé avec ID valide
        Then: preset retourné avec données complètes
        """
        created_preset, _ = preset_service.create_preset(sample_preset_data)
        
        loaded_preset = preset_service.load_preset(created_preset.id)
        
        assert loaded_preset.id == created_preset.id
        assert loaded_preset.name == "Test Preset"
        assert loaded_preset.configuration.characters == ["Akthar", "Neth"]
    
    def test_load_preset_not_found(self, preset_service: PresetService):
        """Given: preset inexistant
        When: load_preset est appelé avec ID invalide
        Then: FileNotFoundError raised
        """
        with pytest.raises(FileNotFoundError, match="Preset.*not found"):
            preset_service.load_preset("non-existent-id")
    
    def test_load_preset_invalid_json(self, preset_service: PresetService):
        """Given: fichier preset JSON corrompu
        When: load_preset est appelé
        Then: ValueError raised
        """
        corrupted_file = preset_service.presets_dir / "corrupted.json"
        preset_service.presets_dir.mkdir(parents=True, exist_ok=True)
        with open(corrupted_file, "w", encoding="utf-8") as f:
            f.write("{ invalid json")
        
        with pytest.raises(ValueError, match="Invalid JSON"):
            preset_service.load_preset("corrupted")


class TestPresetServiceUpdate:
    """Tests pour mise à jour preset."""
    
    def test_update_preset_success(self, preset_service: PresetService, sample_preset_data: dict):
        """Given: preset existant
        When: update_preset est appelé avec nouvelles données
        Then: preset mis à jour, metadata.modified actualisé
        """
        preset, _ = preset_service.create_preset(sample_preset_data)
        original_modified = preset.metadata.modified
        
        # Attendre un instant pour différence timestamp
        import time
        time.sleep(0.1)
        
        updated_preset, _ = preset_service.update_preset(preset.id, {"name": "Updated Name"})
        
        assert updated_preset.name == "Updated Name"
        assert updated_preset.id == preset.id
        assert updated_preset.metadata.modified > original_modified
    
    def test_update_preset_not_found(self, preset_service: PresetService):
        """Given: preset inexistant
        When: update_preset est appelé
        Then: FileNotFoundError raised
        """
        with pytest.raises(FileNotFoundError):
            preset_service.update_preset("non-existent-id", {"name": "Test"})


class TestPresetServiceDelete:
    """Tests pour suppression preset."""
    
    def test_delete_preset_success(self, preset_service: PresetService, sample_preset_data: dict):
        """Given: preset existant
        When: delete_preset est appelé
        Then: fichier supprimé
        """
        preset, _ = preset_service.create_preset(sample_preset_data)
        preset_file = preset_service.presets_dir / f"{preset.id}.json"
        
        assert preset_file.exists()
        
        preset_service.delete_preset(preset.id)
        
        assert not preset_file.exists()
    
    def test_delete_preset_not_found(self, preset_service: PresetService):
        """Given: preset inexistant
        When: delete_preset est appelé
        Then: FileNotFoundError raised
        """
        with pytest.raises(FileNotFoundError):
            preset_service.delete_preset("non-existent-id")


class TestPresetValidation:
    """Tests pour validation références GDD."""
    
    def test_validate_preset_all_valid(self, preset_service: PresetService, sample_preset_data: dict):
        """Given: preset avec références GDD valides
        When: validate_preset_references est appelé
        Then: validation réussie (valid=True, warnings=[], obsoleteRefs=[])
        """
        preset, _ = preset_service.create_preset(sample_preset_data)
        
        result = preset_service.validate_preset_references(preset)
        
        assert result.valid is True
        assert result.warnings == []
        assert result.obsoleteRefs == []
    
    def test_validate_preset_obsolete_character(self, preset_service: PresetService, sample_preset_data: dict):
        """Given: preset avec personnage supprimé du GDD
        When: validate_preset_references est appelé
        Then: validation échoue avec warning spécifique
        """
        # Créer preset avec référence invalide directement (sans passer par create_preset qui nettoie)
        from api.schemas.preset import Preset, PresetMetadata, PresetConfiguration
        from datetime import datetime, timezone
        from uuid import uuid4
        
        invalid_preset = Preset(
            id=str(uuid4()),
            name="Test Preset",
            icon="🎭",
            metadata=PresetMetadata(created=datetime.now(timezone.utc), modified=datetime.now(timezone.utc)),
            configuration=PresetConfiguration(
                characters=["Akthar", "Inconnu-999"],
                locations=sample_preset_data["configuration"]["locations"],
                region=sample_preset_data["configuration"]["region"],
                subLocation=sample_preset_data["configuration"]["subLocation"],
                sceneType=sample_preset_data["configuration"]["sceneType"],
                instructions=sample_preset_data["configuration"]["instructions"]
            )
        )
        
        result = preset_service.validate_preset_references(invalid_preset)
        
        assert result.valid is False
        assert len(result.warnings) == 1
        assert "Inconnu-999" in result.warnings[0]
        assert "Inconnu-999" in result.obsoleteRefs
    
    def test_validate_preset_obsolete_location(self, preset_service: PresetService, sample_preset_data: dict):
        """Given: preset avec lieu supprimé du GDD
        When: validate_preset_references est appelé
        Then: validation échoue avec warning spécifique
        """
        # Créer preset avec référence invalide directement (sans passer par create_preset qui nettoie)
        from api.schemas.preset import Preset, PresetMetadata, PresetConfiguration
        from datetime import datetime, timezone
        from uuid import uuid4
        
        invalid_preset = Preset(
            id=str(uuid4()),
            name="Test Preset",
            icon="🎭",
            metadata=PresetMetadata(created=datetime.now(timezone.utc), modified=datetime.now(timezone.utc)),
            configuration=PresetConfiguration(
                characters=sample_preset_data["configuration"]["characters"],
                locations=["Lieu-Inconnu-999"],
                region=sample_preset_data["configuration"]["region"],
                subLocation=sample_preset_data["configuration"]["subLocation"],
                sceneType=sample_preset_data["configuration"]["sceneType"],
                instructions=sample_preset_data["configuration"]["instructions"]
            )
        )
        
        result = preset_service.validate_preset_references(invalid_preset)
        
        assert result.valid is False
        assert "Lieu-Inconnu-999" in result.warnings[0]
        assert "Lieu-Inconnu-999" in result.obsoleteRefs
    
    def test_validate_preset_multiple_obsolete_refs(self, preset_service: PresetService, sample_preset_data: dict):
        """Given: preset avec plusieurs références obsolètes
        When: validate_preset_references est appelé
        Then: tous les obsolètes détectés
        """
        # Créer preset avec références invalides directement (sans passer par create_preset qui nettoie)
        from api.schemas.preset import Preset, PresetMetadata, PresetConfiguration
        from datetime import datetime, timezone
        from uuid import uuid4
        
        invalid_preset = Preset(
            id=str(uuid4()),
            name="Test Preset",
            icon="🎭",
            metadata=PresetMetadata(created=datetime.now(timezone.utc), modified=datetime.now(timezone.utc)),
            configuration=PresetConfiguration(
                characters=["Inconnu-999", "Inconnu-888"],
                locations=["Lieu-Inconnu-999"],
                region=sample_preset_data["configuration"]["region"],
                subLocation=sample_preset_data["configuration"]["subLocation"],
                sceneType=sample_preset_data["configuration"]["sceneType"],
                instructions=sample_preset_data["configuration"]["instructions"]
            )
        )
        
        result = preset_service.validate_preset_references(invalid_preset)
        
        assert result.valid is False
        assert len(result.warnings) == 3
        assert len(result.obsoleteRefs) == 3
        assert "Inconnu-999" in result.obsoleteRefs
        assert "Inconnu-888" in result.obsoleteRefs
        assert "Lieu-Inconnu-999" in result.obsoleteRefs


class TestPresetServiceErrorHandling:
    """Tests pour gestion erreurs."""
    
    def test_create_preset_permission_error(self, preset_service: PresetService, sample_preset_data: dict):
        """Given: permissions insuffisantes sur dossier presets
        When: create_preset est appelé
        Then: PermissionError raised avec message clair
        """
        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            with pytest.raises(PermissionError, match="Access denied"):
                preset_service.create_preset(sample_preset_data)[0]
    
    def test_create_preset_disk_full_error(self, preset_service: PresetService, sample_preset_data: dict):
        """Given: disque plein
        When: create_preset est appelé
        Then: OSError raised
        """
        with patch("builtins.open", side_effect=OSError("No space left on device")):
            with pytest.raises(OSError, match="No space left on device"):
                preset_service.create_preset(sample_preset_data)[0]


class TestPresetAutoCleanup:
    """Tests pour auto-cleanup des références obsolètes lors de la sauvegarde."""
    
    def test_create_preset_auto_cleanup_obsolete_characters(
        self, preset_service: PresetService, sample_preset_data: dict
    ):
        """Given: preset avec personnage obsolète
        When: create_preset est appelé
        Then: personnage obsolète automatiquement supprimé du preset sauvegardé"""
        # GIVEN: preset avec personnage qui n'existe plus dans le GDD
        invalid_data = {**sample_preset_data}
        invalid_data["configuration"]["characters"] = ["Akthar", "ObsoleteChar"]
        
        # WHEN
        preset, cleanup_message = preset_service.create_preset(invalid_data)
        
        # THEN: personnage obsolète supprimé
        assert "ObsoleteChar" not in preset.configuration.characters
        assert "Akthar" in preset.configuration.characters  # Valide préservé
        assert cleanup_message is not None
        assert "ObsoleteChar" in cleanup_message or "1" in cleanup_message
    
    def test_create_preset_auto_cleanup_obsolete_locations(
        self, preset_service: PresetService, sample_preset_data: dict
    ):
        """Given: preset avec lieu obsolète
        When: create_preset est appelé
        Then: lieu obsolète automatiquement supprimé du preset sauvegardé"""
        # GIVEN: preset avec lieu qui n'existe plus dans le GDD
        invalid_data = {**sample_preset_data}
        invalid_data["configuration"]["locations"] = ["Avili de l'Éternel Retour", "ObsoleteLocation"]
        
        # WHEN
        preset, cleanup_message = preset_service.create_preset(invalid_data)
        
        # THEN: lieu obsolète supprimé
        assert "ObsoleteLocation" not in preset.configuration.locations
        assert "Avili de l'Éternel Retour" in preset.configuration.locations  # Valide préservé
        assert cleanup_message is not None
    
    def test_create_preset_auto_cleanup_multiple_obsolete_refs(
        self, preset_service: PresetService, sample_preset_data: dict
    ):
        """Given: preset avec plusieurs références obsolètes
        When: create_preset est appelé
        Then: toutes les références obsolètes supprimées"""
        # GIVEN
        invalid_data = {**sample_preset_data}
        invalid_data["configuration"]["characters"] = ["Akthar", "ObsoleteChar1", "ObsoleteChar2"]
        invalid_data["configuration"]["locations"] = ["Avili de l'Éternel Retour", "ObsoleteLocation"]
        
        # WHEN
        preset, cleanup_message = preset_service.create_preset(invalid_data)
        
        # THEN
        assert "ObsoleteChar1" not in preset.configuration.characters
        assert "ObsoleteChar2" not in preset.configuration.characters
        assert "ObsoleteLocation" not in preset.configuration.locations
        assert "Akthar" in preset.configuration.characters
        assert "Avili de l'Éternel Retour" in preset.configuration.locations
        assert cleanup_message is not None
    
    def test_create_preset_no_cleanup_when_all_valid(
        self, preset_service: PresetService, sample_preset_data: dict
    ):
        """Given: preset avec toutes références valides
        When: create_preset est appelé
        Then: pas de cleanup, message None"""
        # WHEN
        preset, cleanup_message = preset_service.create_preset(sample_preset_data)
        
        # THEN
        assert cleanup_message is None
        assert preset.configuration.characters == ["Akthar", "Neth"]
        assert preset.configuration.locations == ["Avili de l'Éternel Retour", "Temple"]
    
    def test_update_preset_auto_cleanup_obsolete_refs(
        self, preset_service: PresetService, sample_preset_data: dict
    ):
        """Given: mise à jour preset avec références obsolètes
        When: update_preset est appelé
        Then: références obsolètes automatiquement supprimées"""
        # GIVEN: preset existant
        preset, _ = preset_service.create_preset(sample_preset_data)
        
        # Mise à jour avec références obsolètes
        update_data = {
            "configuration": {
                **sample_preset_data["configuration"],
                "characters": ["Akthar", "ObsoleteChar"],
                "locations": ["Avili de l'Éternel Retour", "ObsoleteLocation"]
            }
        }
        
        # WHEN
        updated_preset, cleanup_message = preset_service.update_preset(preset.id, update_data)
        
        # THEN
        assert "ObsoleteChar" not in updated_preset.configuration.characters
        assert "ObsoleteLocation" not in updated_preset.configuration.locations
        assert cleanup_message is not None
    
    def test_update_preset_no_cleanup_when_all_valid(
        self, preset_service: PresetService, sample_preset_data: dict
    ):
        """Given: mise à jour preset avec toutes références valides
        When: update_preset est appelé
        Then: pas de cleanup, message None"""
        # GIVEN
        preset, _ = preset_service.create_preset(sample_preset_data)
        
        # WHEN
        updated_preset, cleanup_message = preset_service.update_preset(
            preset.id, {"name": "Updated Name"}
        )
        
        # THEN
        assert cleanup_message is None
        assert updated_preset.name == "Updated Name"
        assert updated_preset.configuration.characters == ["Akthar", "Neth"]
