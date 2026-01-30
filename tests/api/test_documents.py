"""Tests pour les endpoints GET/PUT /api/v1/documents (Story 16.2)."""
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from api.main import app
from api.dependencies import get_config_service
from api.exceptions import NotFoundException, ValidationException


@pytest.fixture
def mock_config_service():
    """Mock du ConfigurationService."""
    from services.configuration_service import ConfigurationService
    mock = MagicMock(spec=ConfigurationService)
    return mock


@pytest.fixture
def client(mock_config_service):
    """Client de test avec config mockée."""
    app.dependency_overrides[get_config_service] = lambda: mock_config_service
    yield TestClient(app)
    app.dependency_overrides.clear()


def _doc_v1_1_0():
    """Document canonique v1.1.0 (schemaVersion, nodes)."""
    return {
        "schemaVersion": "1.1.0",
        "nodes": [
            {"id": "START", "speaker": "NPC", "line": "Hello", "nextNode": "END"},
        ],
    }


class TestGetDocument:
    """Tests GET /api/v1/documents/{id} (AC1)."""

    def test_get_document_returns_document_schema_version_revision(
        self, client, mock_config_service, tmp_path
    ):
        """GET retourne document, schemaVersion, revision (AC1)."""
        doc_id = "my-dialogue"
        doc = _doc_v1_1_0()
        (tmp_path / f"{doc_id}.json").write_text(json.dumps(doc), encoding="utf-8")
        (tmp_path / f"{doc_id}.meta").write_text(
            json.dumps({"revision": 3, "updated_at": "2026-01-30T12:00:00Z"}),
            encoding="utf-8",
        )
        mock_config_service.get_unity_dialogues_path.return_value = tmp_path

        response = client.get(f"/api/v1/documents/{doc_id}")

        assert response.status_code == 200
        data = response.json()
        assert "document" in data
        assert data["document"] == doc
        assert data["schemaVersion"] == "1.1.0"
        assert data["revision"] == 3

    def test_get_document_serves_persisted_blob_only(
        self, client, mock_config_service, tmp_path
    ):
        """Backend ne reconstruit pas le document ; sert le blob persisté (AC1)."""
        doc_id = "blob-only"
        doc = {"schemaVersion": "1.1.0", "nodes": [{"id": "A", "line": "Only node"}]}
        (tmp_path / f"{doc_id}.json").write_text(json.dumps(doc), encoding="utf-8")
        mock_config_service.get_unity_dialogues_path.return_value = tmp_path

        response = client.get(f"/api/v1/documents/{doc_id}")

        assert response.status_code == 200
        assert response.json()["document"] == doc

    def test_get_document_no_meta_defaults_revision_one(
        self, client, mock_config_service, tmp_path
    ):
        """Sans .meta, revision vaut 1."""
        doc_id = "no-meta"
        doc = _doc_v1_1_0()
        (tmp_path / f"{doc_id}.json").write_text(json.dumps(doc), encoding="utf-8")
        mock_config_service.get_unity_dialogues_path.return_value = tmp_path

        response = client.get(f"/api/v1/documents/{doc_id}")

        assert response.status_code == 200
        assert response.json()["revision"] == 1

    def test_get_document_not_found_404(self, client, mock_config_service, tmp_path):
        """GET document inexistant → 404."""
        tmp_path.mkdir(parents=True, exist_ok=True)
        mock_config_service.get_unity_dialogues_path.return_value = tmp_path

        response = client.get("/api/v1/documents/nonexistent-id")

        assert response.status_code == 404

    def test_get_document_path_traversal_rejected(self, client, mock_config_service):
        """Id contenant '..' → 422 (validation)."""
        mock_config_service.get_unity_dialogues_path.return_value = Path("/any")
        # Encoder ".." pour que le path ne soit pas normalisé (document_id reçu = "..")
        response = client.get("/api/v1/documents/%2e%2e")
        assert response.status_code == 422

    def test_get_document_empty_id_returns_422(self, client, mock_config_service):
        """GET avec document_id vide après strip (ex. espaces) → 422 (AC1, validation)."""
        mock_config_service.get_unity_dialogues_path.return_value = Path("/any")
        # document_id = "   " → _safe_document_id retourne "" → ValidationException
        response = client.get("/api/v1/documents/%20%20%20")
        assert response.status_code == 422


class TestPutDocument:
    """Tests PUT /api/v1/documents/{id} (AC2)."""

    def test_put_document_success_returns_revision_and_validation_report(
        self, client, mock_config_service, tmp_path
    ):
        """PUT document valide + revision à jour → 200, revision, validationReport."""
        doc_id = "my-doc"
        doc = _doc_v1_1_0()
        (tmp_path / f"{doc_id}.json").write_text(json.dumps(doc), encoding="utf-8")
        (tmp_path / f"{doc_id}.meta").write_text(
            json.dumps({"revision": 2, "updated_at": "2026-01-30T12:00:00Z"}),
            encoding="utf-8",
        )
        mock_config_service.get_unity_dialogues_path.return_value = tmp_path

        updated = {"schemaVersion": "1.1.0", "nodes": [{"id": "START", "line": "Updated", "nextNode": "END"}]}
        response = client.put(
            f"/api/v1/documents/{doc_id}",
            json={"document": updated, "revision": 2},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["revision"] == 3
        assert "validationReport" in data
        # Document persisté
        with open(tmp_path / f"{doc_id}.json", encoding="utf-8") as f:
            persisted = json.load(f)
        assert persisted == updated
        meta = json.loads((tmp_path / f"{doc_id}.meta").read_text(encoding="utf-8"))
        assert meta["revision"] == 3

    def test_put_document_conflict_409_returns_last_state(
        self, client, mock_config_service, tmp_path
    ):
        """PUT avec revision obsolète → 409 + dernier état (document, schemaVersion, revision)."""
        doc_id = "conflict-doc"
        current_doc = _doc_v1_1_0()
        (tmp_path / f"{doc_id}.json").write_text(json.dumps(current_doc), encoding="utf-8")
        (tmp_path / f"{doc_id}.meta").write_text(
            json.dumps({"revision": 5, "updated_at": "2026-01-30T12:00:00Z"}),
            encoding="utf-8",
        )
        mock_config_service.get_unity_dialogues_path.return_value = tmp_path

        response = client.put(
            f"/api/v1/documents/{doc_id}",
            json={"document": {"schemaVersion": "1.1.0", "nodes": []}, "revision": 3},
        )

        assert response.status_code == 409
        data = response.json()
        assert data["document"] == current_doc
        assert data["schemaVersion"] == "1.1.0"
        assert data["revision"] == 5
        # Document inchangé sur disque
        with open(tmp_path / f"{doc_id}.json", encoding="utf-8") as f:
            assert json.load(f) == current_doc

    def test_put_document_new_creates_with_revision_one(
        self, client, mock_config_service, tmp_path
    ):
        """PUT sur document inexistant crée avec revision 1."""
        tmp_path.mkdir(parents=True, exist_ok=True)
        mock_config_service.get_unity_dialogues_path.return_value = tmp_path
        doc = _doc_v1_1_0()

        response = client.put(
            "/api/v1/documents/new-doc",
            json={"document": doc, "revision": 1},
        )

        assert response.status_code == 200
        assert response.json()["revision"] == 1
        assert (tmp_path / "new-doc.json").exists()
        assert (tmp_path / "new-doc.meta").exists()
        assert json.loads((tmp_path / "new-doc.json").read_text(encoding="utf-8")) == doc

    def test_put_document_nodes_edges_payload_rejected_400(
        self, client, mock_config_service, tmp_path
    ):
        """PUT avec body nodes/edges (ancien contrat) → 400, erreur structurée (AC3)."""
        tmp_path.mkdir(parents=True, exist_ok=True)
        mock_config_service.get_unity_dialogues_path.return_value = tmp_path
        graph_payload = {
            "nodes": [{"id": "n1", "data": {}}],
            "edges": [{"source": "n1", "target": "n2"}],
        }

        response = client.put(
            "/api/v1/documents/any-id",
            json={"document": graph_payload, "revision": 1},
        )

        assert response.status_code == 400
        data = response.json()
        # Réponse structurée : top-level ou sous "error"
        assert "detail" in data or "code" in data or "message" in data or "error" in data
        if "error" in data:
            assert "code" in data["error"] or "message" in data["error"]


class TestPutDocumentDraftVsExport:
    """Tests PUT modes draft vs export (AC4)."""

    def _doc_with_missing_choice_id(self):
        """Document v1.1.0 avec un choice sans choiceId → validation échoue en export."""
        return {
            "schemaVersion": "1.1.0",
            "nodes": [
                {
                    "id": "START",
                    "line": "Hello",
                    "choices": [
                        {"text": "OK", "targetNode": "END"},
                    ],
                },
            ],
        }

    def test_put_draft_mode_persists_despite_validation_errors(
        self, client, mock_config_service, tmp_path
    ):
        """Mode draft : validation échoue mais persistance autorisée, 200 + validationReport."""
        tmp_path.mkdir(parents=True, exist_ok=True)
        mock_config_service.get_unity_dialogues_path.return_value = tmp_path
        doc = self._doc_with_missing_choice_id()

        response = client.put(
            "/api/v1/documents/draft-doc",
            json={"document": doc, "revision": 1, "validationMode": "draft"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["revision"] == 1
        assert "validationReport" in data
        assert len(data["validationReport"]) > 0
        assert (tmp_path / "draft-doc.json").exists()

    def test_put_export_mode_rejects_on_validation_failure_400(
        self, client, mock_config_service, tmp_path
    ):
        """Mode export : validation échoue → 400 + validationReport, pas de persistance."""
        tmp_path.mkdir(parents=True, exist_ok=True)
        mock_config_service.get_unity_dialogues_path.return_value = tmp_path
        doc = self._doc_with_missing_choice_id()

        response = client.put(
            "/api/v1/documents/export-doc",
            json={"document": doc, "revision": 1, "validationMode": "export"},
        )

        assert response.status_code == 400
        data = response.json()
        assert "validationReport" in data
        assert len(data["validationReport"]) > 0
        assert not (tmp_path / "export-doc.json").exists()

    def test_put_export_mode_header_overrides_body(
        self, client, mock_config_service, tmp_path
    ):
        """Header X-Validation-Mode: export override body validationMode."""
        tmp_path.mkdir(parents=True, exist_ok=True)
        mock_config_service.get_unity_dialogues_path.return_value = tmp_path
        doc = self._doc_with_missing_choice_id()

        response = client.put(
            "/api/v1/documents/header-doc",
            json={"document": doc, "revision": 1, "validationMode": "draft"},
            headers={"X-Validation-Mode": "export"},
        )

        assert response.status_code == 400
        assert "validationReport" in response.json()
        assert not (tmp_path / "header-doc.json").exists()
