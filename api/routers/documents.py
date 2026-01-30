"""Router pour les documents canoniques (GET/PUT par id avec revision).

Story 16.2 : endpoints GET/PUT /documents/{id} ; document = blob persisté ;
revision dans .meta ; pas de reconstruction à partir de nodes/edges.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Header, status
from fastapi.responses import JSONResponse

from api.dependencies import get_config_service, get_request_id
from api.exceptions import APIException, NotFoundException, ValidationException, InternalServerException
from api.schemas.documents import DocumentGetResponse, PutDocumentRequest, PutDocumentResponse
from api.utils.unity_schema_validator import validate_unity_json_structured
from services.configuration_service import ConfigurationService

logger = logging.getLogger(__name__)

router = APIRouter()

META_FILENAME_SUFFIX = ".meta"


def _safe_document_id(document_id: str) -> str:
    """Valide l'id document (pas de path traversal). Retourne l'id normalisé."""
    if ".." in document_id or "/" in document_id or "\\" in document_id:
        raise ValueError("document_id invalide (path traversal)")
    return document_id.strip() or ""


def _read_document_blob(base_dir: Path, document_id: str) -> dict:
    """Lit le fichier JSON du document. Lève FileNotFoundError si absent."""
    path = base_dir / f"{document_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Document {document_id} non trouvé")
    raw = path.read_text(encoding="utf-8")
    return json.loads(raw)


def _read_meta(base_dir: Path, document_id: str) -> int:
    """Lit la revision depuis {id}.meta. Retourne 1 si pas de .meta."""
    meta_path = base_dir / f"{document_id}{META_FILENAME_SUFFIX}"
    if not meta_path.exists():
        return 1
    try:
        data = json.loads(meta_path.read_text(encoding="utf-8"))
        return int(data.get("revision", 1))
    except (json.JSONDecodeError, TypeError, ValueError):
        return 1


def _write_document_blob(base_dir: Path, document_id: str, document: dict) -> None:
    """Écrit le document JSON. Crée le dossier si besoin."""
    base_dir.mkdir(parents=True, exist_ok=True)
    path = base_dir / f"{document_id}.json"
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_meta(base_dir: Path, document_id: str, revision: int) -> None:
    """Écrit {id}.meta avec revision et updated_at."""
    meta_path = base_dir / f"{document_id}{META_FILENAME_SUFFIX}"
    meta_path.write_text(
        json.dumps(
            {"revision": revision, "updated_at": datetime.now(timezone.utc).isoformat()},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _document_exists(base_dir: Path, document_id: str) -> bool:
    """Indique si le document existe (fichier .json présent)."""
    return (base_dir / f"{document_id}.json").exists()


@router.get(
    "/{document_id}",
    response_model=DocumentGetResponse,
    status_code=status.HTTP_200_OK,
)
async def get_document(
    document_id: str,
    config_service: Annotated[ConfigurationService, Depends(get_config_service)],
    request_id: Annotated[str, Depends(get_request_id)],
) -> DocumentGetResponse:
    """Retourne le document persisté avec schemaVersion et revision (pas de reconstruction)."""
    try:
        doc_id = _safe_document_id(document_id)
        if not doc_id:
            raise ValidationException(
                message="document_id requis",
                details={"document_id": document_id},
                request_id=request_id,
            )
        unity_path = config_service.get_unity_dialogues_path()
        if not unity_path:
            raise ValidationException(
                message="Le chemin Unity dialogues n'est pas configuré.",
                details={"field": "unity_dialogues_path"},
                request_id=request_id,
            )
        base_dir = Path(unity_path)
        base_dir.mkdir(parents=True, exist_ok=True)

        document = _read_document_blob(base_dir, doc_id)
        revision = _read_meta(base_dir, doc_id)
        schema_version = (document.get("schemaVersion") or "1.1.0") if isinstance(document, dict) else "1.1.0"

        logger.info(f"GET document {doc_id} revision={revision} (request_id: {request_id})")
        return DocumentGetResponse(
            document=document,
            schemaVersion=schema_version,
            revision=revision,
        )
    except ValueError as e:
        if "path traversal" in str(e).lower() or "invalide" in str(e).lower():
            raise ValidationException(
                message="Identifiant de document invalide",
                details={"document_id": document_id},
                request_id=request_id,
            )
        raise
    except FileNotFoundError:
        raise NotFoundException(
            resource_type="Document",
            resource_id=document_id,
            request_id=request_id,
        )
    except (ValidationException, NotFoundException):
        raise
    except Exception as e:
        logger.exception(f"Erreur GET document {document_id} (request_id: {request_id})")
        raise InternalServerException(
            message="Erreur lors de la lecture du document",
            details={"error": str(e)},
            request_id=request_id,
        )


@router.put(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
    response_model=PutDocumentResponse,
)
async def put_document(
    document_id: str,
    body: PutDocumentRequest,
    config_service: Annotated[ConfigurationService, Depends(get_config_service)],
    request_id: Annotated[str, Depends(get_request_id)],
    x_validation_mode: Annotated[str | None, Header(alias="X-Validation-Mode")] = None,
) -> PutDocumentResponse | JSONResponse:
    """Valide et persiste le document ; revision optimiste ; 409 si conflit ; draft vs export (AC4)."""
    try:
        doc_id = _safe_document_id(document_id)
        if not doc_id:
            raise ValidationException(
                message="document_id requis",
                details={"document_id": document_id},
                request_id=request_id,
            )
        unity_path = config_service.get_unity_dialogues_path()
        if not unity_path:
            raise ValidationException(
                message="Le chemin Unity dialogues n'est pas configuré.",
                details={"field": "unity_dialogues_path"},
                request_id=request_id,
            )
        base_dir = Path(unity_path)
        base_dir.mkdir(parents=True, exist_ok=True)

        doc = body.document
        client_revision = body.revision

        # AC3 : refuser payload type nodes/edges (ancien contrat graphe)
        if isinstance(doc, dict):
            has_nodes = "nodes" in doc
            has_edges = "edges" in doc
            has_schema_version = "schemaVersion" in doc
            if has_nodes and has_edges and not has_schema_version:
                raise APIException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    code="GRAPH_PAYLOAD_NOT_ACCEPTED",
                    message="Seul le document canonique est accepté (schemaVersion, nodes). Payload nodes/edges non accepté.",
                    details={"code": "graph_payload_not_accepted"},
                    request_id=request_id,
                )

        # Révision optimiste : si document existe, comparer revision
        if _document_exists(base_dir, doc_id):
            current_revision = _read_meta(base_dir, doc_id)
            if client_revision != current_revision:
                current_doc = _read_document_blob(base_dir, doc_id)
                schema_ver = (current_doc.get("schemaVersion") or "1.1.0") if isinstance(current_doc, dict) else "1.1.0"
                payload = DocumentGetResponse(
                    document=current_doc,
                    schemaVersion=schema_ver,
                    revision=current_revision,
                )
                return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=payload.model_dump())
            new_revision = current_revision + 1
        else:
            new_revision = 1

        # Mode validation : header X-Validation-Mode override body.validationMode
        validation_mode = (x_validation_mode or body.validationMode or "draft").strip().lower()
        if validation_mode not in ("draft", "export"):
            validation_mode = "draft"

        # Validation (validate_unity_json_structured sans modifier choiceId, ordre choices[], node.id)
        is_valid, errors_structured = validate_unity_json_structured(doc)
        validation_report = [{"code": e.get("code", "validation_error"), "message": e.get("message", ""), "path": e.get("path", "")} for e in errors_structured]

        # AC4 export : si validation échoue, refuser persistance et retourner 400 + validationReport
        if validation_mode == "export" and not is_valid:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"validationReport": validation_report, "message": "Validation export échouée"},
            )

        # Persistance : ne pas modifier choiceId, ordre choices[], node.id (document tel quel)
        _write_document_blob(base_dir, doc_id, doc)
        _write_meta(base_dir, doc_id, new_revision)

        logger.info(f"PUT document {doc_id} revision={new_revision} mode={validation_mode} (request_id: {request_id})")
        return PutDocumentResponse(revision=new_revision, validationReport=validation_report)
    except ValueError as e:
        if "path traversal" in str(e).lower() or "invalide" in str(e).lower():
            raise ValidationException(
                message="Identifiant de document invalide",
                details={"document_id": document_id},
                request_id=request_id,
            )
        raise
    except (APIException, ValidationException, NotFoundException):
        raise
    except Exception as e:
        logger.exception(f"Erreur PUT document {document_id} (request_id: {request_id})")
        raise InternalServerException(
            message="Erreur lors de l'écriture du document",
            details={"error": str(e)},
            request_id=request_id,
        )
