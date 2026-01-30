# Story 16.2: Backend document – GET/PUT, revision, 409

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **frontend ou client API**,
I want **des endpoints GET/PUT par document avec revision et gestion des conflits (409)**,
so that **le backend soit le propriétaire du document canonique et que les conflits soient gérés proprement**.

## Acceptance Criteria

1. **Given** un endpoint GET document existe (ex. GET /documents/{id})  
   **When** j'appelle GET  
   **Then** la réponse contient `{ document, schemaVersion, revision }`  
   **And** le backend ne reconstruit pas le document à partir d'un graphe UI ; il sert le document persisté.

2. **Given** un endpoint PUT document existe (ex. PUT /documents/{id}) avec payload `{ document, revision }`  
   **When** j'envoie un document valide (v1.1.0, choiceId présents) avec la revision courante  
   **Then** le backend valide et normalise le document sans casser choiceId, ordre des choices[], node.id  
   **And** la réponse contient `{ revision, validationReport }` (validationReport : liste d'erreurs structurées, ex. code + message)  
   **And** en cas de conflit (revision obsolète), le backend retourne 409 + dernier état.

3. **Given** un client envoie un payload contenant nodes/edges (ancien contrat) au lieu du document  
   **When** le backend reçoit la requête PUT  
   **Then** le backend refuse la requête (ex. 400) avec erreur structurée indiquant que seul le document canonique est accepté (pas de rétrocompatibilité).

4. **Given** la validation distingue draft (non bloquant, autosave autorisé) et export (bloquant)  
   **When** une validation échoue en mode draft  
   **Then** les erreurs sont structurées mais n'empêchent pas la sauvegarde draft  
   **When** une validation échoue en mode export  
   **Then** l'export est refusé avec erreurs structurées.

5. Conformité ADR-008 et objectifs-contraintes : pas de régression sur les scénarios existants (tests API, E2E, validation).

## Tasks / Subtasks

- [ ] **Task 1** (AC: 1) – Endpoint GET /documents/{id}
  - [ ] 1.1 Définir schémas Pydantic : DocumentGetResponse (document, schemaVersion, revision).
  - [ ] 1.2 Implémenter GET : lecture persistance par id ; retourner document tel quel + schemaVersion (depuis document) + revision.
  - [ ] 1.3 Ne jamais reconstruire le document à partir de nodes/edges ; servir uniquement le blob persisté.
- [ ] **Task 2** (AC: 2) – Endpoint PUT /documents/{id} + revision + 409
  - [ ] 2.1 Schémas : PutDocumentRequest (document, revision), PutDocumentResponse (revision, validationReport).
  - [ ] 2.2 Valider/normaliser le document reçu (validate_unity_json_structured) sans modifier choiceId, ordre choices[], node.id.
  - [ ] 2.3 Comparer revision client vs stockée ; si différente → 409 + corps avec dernier état (document, schemaVersion, revision).
  - [ ] 2.4 En cas de succès : persister, incrémenter revision, retourner { revision, validationReport }.
- [ ] **Task 3** (AC: 3) – Refus payload nodes/edges
  - [ ] 3.1 Détecter payload de type nodes/edges (ex. présence de "nodes" et "edges" au top level sans schemaVersion ou format graphe).
  - [ ] 3.2 Répondre 400 avec erreur structurée (code + message) : seul le document canonique est accepté, pas de rétrocompatibilité.
- [ ] **Task 4** (AC: 4) – Modes draft vs export
  - [ ] 4.1 Paramètre ou header (ex. X-Validation-Mode: draft | export) ou champ dans le body (ex. validationMode).
  - [ ] 4.2 Draft : exécuter validation, inclure validationReport dans la réponse ; ne pas bloquer la persistance.
  - [ ] 4.3 Export : si validation échoue (ex. missing_choice_id), refuser la persistance et retourner 400 + validationReport.
- [ ] **Task 5** (AC: 5) – Tests et non-régression
  - [ ] 5.1 Tests unitaires/intégration : GET/PUT succès, PUT 409 (revision obsolète), PUT 400 (payload nodes/edges), draft vs export.
  - [ ] 5.2 Vérifier non-régression : tests existants api/routers, unity_dialogues, graph, validation.

## Dev Notes

- **Jalon 1 – Backend document.** API parle uniquement en « document canonique » ; pas d'échange nodes/edges ; pas de rétrocompatibilité. Référence : ADR-008 Backend, Constraints.

### Existants à réutiliser / étendre

- **Validateur** : `api/utils/unity_schema_validator.py` — `validate_unity_json_structured()` retourne (is_valid, errors) avec erreurs `{ code, message, path }`. À appeler côté PUT pour validation ; ne pas casser choiceId, ordre choices[], node.id lors de toute normalisation.
- **Schéma document** : `docs/resources/dialogue-format.schema.json` (v1.1.0). Document = objet avec schemaVersion, nodes[]. Pas de reconstruction à partir d'un graphe.
- **Router existant** : `api/routers/unity_dialogues.py` — GET "" (list), GET /{filename} (read), DELETE /{filename}. Actuellement basé sur filename et fichier plat ; pas de revision. Story 16.2 introduit un **nouveau** espace de ressources « documents » avec id et revision (ex. nouveau router `api/routers/documents.py` ou sous-route `/api/v1/documents`) pour ne pas casser les usages actuels de unity-dialogues (list/read par filename). Décision à trancher : même base de persistance (fichiers) avec id = filename ou nouvel identifiant ; dans tous les cas, GET/PUT par id avec revision.
- **Graph router** : `api/routers/graph.py` — POST /load, POST /save avec `SaveGraphRequest` (nodes/edges). Ne pas modifier le contrat save dans cette story ; le refus nodes/edges s'applique aux **nouveaux** endpoints PUT document. Les appels existants à graph/save restent inchangés jusqu'à la story 16.4 (frontend SoT document).
- **Persistance** : Actuellement `ConfigurationService.get_unity_dialogues_path()` + fichiers .json. Pour revision, il faut stocker une revision par document (ex. fichier .meta à côté du .json, ou champ dans un index). Décision implémentation : fichier `{id}.json` + `{id}.meta` (revision, updated_at) ou équivalent.

### GARDE-FOUS (epic 16)

- Vérifier `docs/resources/dialogue-format.schema.json`, `api/utils/unity_schema_validator.py`, `api/routers/dialogues.py`, `api/routers/unity_dialogues.py`, `api/routers/graph.py`.
- Pas de couche de contournement : ne pas accepter nodes/edges sur PUT document ; ne jamais reconstruire le document à partir du graphe.
- Chaque livrable fait progresser vers l'état cible ADR-008.

### Architecture & conformité

- **ADR-008** : `_bmad-output/planning-artifacts/architecture/v10-architectural-decisions-adrs.md` — Backend : GET /documents/{path|id} → { document, schemaVersion, revision } ; PUT /documents/{path|id} avec { document, revision } → { revision, validationReport } ; conflit → 409 + dernier état.
- **Pipeline** : `docs/architecture/pipeline-unity-backend-front-architecture.md` — Backend valide et normalise sans casser choiceId, ordre choices[], node.id.
- **Objectifs / contraintes** : `_bmad-output/planning-artifacts/epics/objectifs-contraintes-implementation-adr-008.md` — Zéro régression, priorité absolue.

### Stack & librairies

- **FastAPI** : router, status 400/409, Pydantic pour request/response.
- **jsonschema** : déjà utilisé par `unity_schema_validator` ; pas de nouvelle dépendance.

### Structure de fichiers

- Nouveau router recommandé : `api/routers/documents.py` (GET/PUT par id) ou extension sous `/api/v1/documents`.
- Schémas : `api/schemas/dialogue.py` ou nouveau `api/schemas/documents.py` pour DocumentGetResponse, PutDocumentRequest, PutDocumentResponse, validationReport (errors[].code, message, path).
- Persistance : réutiliser ou étendre le chemin Unity (config) ; ajouter stockage revision (fichier .meta ou index).
- Enregistrement : `api/main.py` — `app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])`.

### Tests

- Unitaires / intégration : GET document existant (200, corps document + schemaVersion + revision) ; GET document inexistant (404) ; PUT document valide + revision à jour (200, revision, validationReport) ; PUT avec revision obsolète (409, dernier état) ; PUT avec body nodes/edges (400, erreur structurée) ; mode draft vs export (draft : erreurs dans report mais 200 ; export : erreur validation → 400).
- Non-régression : `tests/api/`, `tests/integration/`, tests frontend-backend existants.

### Previous story (16.1) intelligence

- Schéma v1.1.0 et validateur avec `validate_unity_json_structured()` sont en place. TODO Story 16.2 dans la docstring du validateur : « connecter à endpoint export » — cette story implémente cet endpoint (PUT document avec mode export = validation bloquante).
- Ne pas réintroduire de rétrocompatibilité schéma v1.0 ; pas de génération choiceId à la volée en production.
- Fichiers modifiés en 16.1 : `docs/resources/dialogue-format.schema.json`, `api/utils/unity_schema_validator.py`, `docs/architecture/pipeline-unity-backend-front-architecture.md`, `docs/architecture/validation-et-mise-en-place-decisions.md`.

### Project Structure Notes

- Alignement avec `api/routers/`, `api/schemas/`, `api/dependencies.py`. Pas de logique métier dans le router ; déléguer persistance et revision à un service (ex. `services/document_storage_service.py` ou module dédié) si nécessaire.

### References

- [Source: _bmad-output/planning-artifacts/architecture/v10-architectural-decisions-adrs.md – ADR-008 Backend]
- [Source: _bmad-output/planning-artifacts/epics/epic-16.md – Story 16.2, GARDE-FOUS]
- [Source: _bmad-output/planning-artifacts/epics/objectifs-contraintes-implementation-adr-008.md]
- [Source: docs/architecture/pipeline-unity-backend-front-architecture.md]
- [Source: docs/architecture/validation-et-mise-en-place-decisions.md]
- [Source: api/utils/unity_schema_validator.py – validate_unity_json_structured]
- [Source: api/routers/unity_dialogues.py – lecture actuelle par filename]
- [Source: api/routers/graph.py – POST /save nodes/edges (à ne pas étendre ; refus sur PUT document)]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
