# Story 16.4: Frontend SoT document + layout, projection, IDs stables

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **utilisateur éditant un dialogue dans le graphe**,
I want **que le frontend ait pour SoT le document (et le layout) et que nodes/edges soient une projection dérivée avec identités stables (choiceId)**,
so that **je n'envoie plus nodes/edges au save et que les identités UI ne « sautent » plus**.

## Acceptance Criteria

1. **Given** le store frontend  
   **When** un dialogue est chargé ou édité  
   **Then** la SoT contenu = `document` (Unity JSON) ; la SoT layout = `layout`  
   **And** nodes/edges = projection dérivée uniquement (pas de SoT nodes/edges)

2. **Given** les identités UI  
   **Then** node id = `node.id` (SCREAMING_SNAKE_CASE, ADR-008) ; choice handle = `choice:${choiceId}` ; TestNode id = `test:${choiceId}` ; edge ids basés sur la sortie (ex. `e:${nodeId}:choice:${choiceId}:target`), jamais sur la destination seule.

3. **Given** la sauvegarde (autosave ou manuelle)  
   **When** le frontend envoie les données au backend  
   **Then** le frontend envoie le **document** (et optionnellement le layout) ; il n'envoie **pas** nodes/edges.

4. **Given** la saisie (form local, debounce/throttle/blur)  
   **When** l'utilisateur édite line/speaker/choice  
   **Then** la projection ne provoque pas de reset du panel ; les identités restent stables.

5. Conformité ADR-008 et objectifs-contraintes : pas de régression sur les scénarios existants (tests API documents, E2E, validation).

## Tasks / Subtasks

- [ ] **Task 1** (AC: 1, 3) – Store SoT document + layout, load/save via API documents
  - [ ] 1.1 Étendre ou créer store : SoT contenu = `document` (Unity JSON), SoT layout = `layout` (objet libre positions/viewport). Ne plus stocker nodes/edges comme source de vérité ; les dériver du document.
  - [ ] 1.2 Load : appeler GET /api/v1/documents/{id} → { document, schemaVersion, revision } ; GET /api/v1/documents/{id}/layout → { layout, revision } (404 si layout absent = pas de layout). Initialiser store avec document + layout.
  - [ ] 1.3 Save : envoyer PUT /api/v1/documents/{id} avec { document, revision } ; PUT /api/v1/documents/{id}/layout avec { layout, revision }. Gérer 409 : afficher conflit, proposer recharger ou écraser (selon UX définie). Ne plus appeler /api/v1/unity-dialogues/graph/load ni graph/save-and-write pour le flux principal.
- [ ] **Task 2** (AC: 1, 2) – Projection document → nodes/edges, IDs stables
  - [ ] 2.1 Projection : à partir du document (nodes[] avec node.id, choices[].choiceId), calculer nodes React Flow et edges. node.id = `node.id` (SCREAMING_SNAKE_CASE) ; handle choix = `choice:${choiceId}` ; TestNode id = `test:${choiceId}` ; edge id = `e:${nodeId}:choice:${choiceId}:${targetNodeId}` (ou convention ADR-008). Positions : depuis layout (nodes positions, viewport si applicable).
  - [ ] 2.2 Édition (line/speaker/choice) : modifier le document en mémoire (pas nodes/edges) ; recalculer la projection pour l'affichage. Pas de reset du panel : identités stables (choiceId, node.id) évitent les re-créations de composants.
  - [ ] 2.3 Drag position : mettre à jour le layout (positions des nœuds), pas le document ; sauvegarder layout via PUT layout.
- [ ] **Task 3** (AC: 4) – Form local, debounce/throttle/blur, pas de reset
  - [ ] 3.1 Panneau Détails (NodeEditorPanel, ChoiceEditor) : lecture/écriture sur le document (ou sur une couche qui met à jour le document). Debounce/throttle/blur inchangés ; la projection ne doit pas recréer les champs (clés stables choiceId, node.id).
  - [ ] 3.2 Vérifier qu'éditer line/speaker/choice ne provoque pas de reset du panel (tests manuels ou E2E).
- [ ] **Task 4** (AC: 5) – Non-régression et tests
  - [ ] 4.1 Conserver ou adapter les tests existants (graphStore, GraphCanvas, NodeEditorPanel, load/save) pour le nouveau flux GET/PUT document + GET/PUT layout.
  - [ ] 4.2 Non-régression : tests API documents (16.2, 16.3), E2E chargement/édition/sauvegarde, validation.

## Dev Notes

- **Jalon 3 – Frontend SoT.** Contrainte ADR-008 : « Le frontend NE DOIT PLUS envoyer nodes/edges au backend pour le save ». Référence : ADR-008 Frontend, Constraints.

### Existants à réutiliser / étendre

- **API documents** : Backend expose déjà GET/PUT /api/v1/documents/{id} et GET/PUT /api/v1/documents/{id}/layout (story 16.2, 16.3). Le frontend utilise aujourd'hui `api/graph.ts` : `loadGraph` → POST `/api/v1/unity-dialogues/graph/load`, `saveGraphAndWrite` → POST `/api/v1/unity-dialogues/graph/save-and-write`. **Remplacer** (ou compléter) par des appels GET/PUT vers `api/documents.ts` (à créer ou étendre) : loadDocument(id), saveDocument(id, document, revision), getLayout(id), putLayout(id, layout, revision).
- **Store** : `frontend/src/store/graphStore.ts` — actuellement SoT = nodes/edges, loadDialogue → graph/load, saveDialogue → graph/save-and-write avec nodes/edges. **Refactor** : SoT = document + layout ; nodes/edges = dérivés (projection). Conserver les actions utilisées par l'UI (setSelectedNode, updateNode, etc.) mais qu'elles opèrent sur le document + layout puis recalculent la projection.
- **Projection** : Aujourd'hui le backend fait JSON → graphe (graph/load) et graphe → JSON (graph/save). La logique de conversion doit être **déplacée côté frontend** (ou réutilisée via un module partagé si existant) : document → nodes/edges pour l'affichage ; édition UI → mise à jour document + layout. Référence schéma Unity : `docs/resources/dialogue-format.schema.json` (v1.1.0), node.id SCREAMING_SNAKE_CASE, choices[].choiceId requis.
- **IDs stables** : ADR-008 impose node id = node.id ; choice handle = `choice:${choiceId}` ; TestNode id = `test:${choiceId}` ; edge id basé sur la sortie (ex. `e:${nodeId}:choice:${choiceId}:target`). Vérifier `frontend/src/utils/graphEdgeBuilders.ts` (choiceEdgeId, etc.) et les composants qui utilisent sourceHandle/targetHandle pour les connecter au choiceId.
- **Journal / autosave** : ADR-006 (seq, journal IndexedDB) est implémenté dans graphStore (saveDialogue, journalWriteSnapshot, etc.). Adapter pour envoyer document + revision (et layout + revision) au lieu de nodes/edges ; conserver seq/last_seq si le backend documents le supporte ou documenter la transition (story 16.2 utilise revision, pas seq — vérifier si seq doit être abandonné au profit de revision).

### GARDE-FOUS (epic 16)

- Vérifier `docs/architecture/pipeline-unity-backend-front-architecture.md`, `api/routers/documents.py`, `frontend/src/store/graphStore.ts`.
- Pas de couche de contournement : ne pas garder nodes/edges comme SoT en parallèle ; une seule SoT = document + layout.
- Chaque livrable fait progresser vers l'état cible ADR-008.

### Architecture & conformité

- **ADR-008** : Frontend SoT = document (Unity JSON) + layout. Nodes/edges = projection dérivée. Save : envoyer document (+ layout) uniquement. Identités stables : choiceId, node.id, edge ids basés sur la sortie.
- **Pipeline** : `docs/architecture/pipeline-unity-backend-front-architecture.md` — Frontend, Backend (GET/PUT document, GET/PUT layout).
- **Objectifs / contraintes** : `_bmad-output/planning-artifacts/epics/objectifs-contraintes-implementation-adr-008.md` — Zéro régression.

### Stack & librairies

- **React / Zustand** : Store existant (graphStore) ; refactor pour SoT document + layout.
- **API client** : axios (api/client) ; ajouter ou étendre `frontend/src/api/documents.ts` pour GET/PUT documents et GET/PUT layout. Types : DocumentGetResponse, PutDocumentRequest, LayoutGetResponse, PutLayoutRequest (voir api/schemas/documents.py).

### Structure de fichiers

- **API** : `frontend/src/api/documents.ts` (nouveau ou étendre api/) — loadDocument(id), saveDocument(id, body), getLayout(id), putLayout(id, body). Types dans `frontend/src/types/documents.ts` si besoin (alignés sur api/schemas/documents.py).
- **Store** : `frontend/src/store/graphStore.ts` — refactor : state document, layout, revision (document), revision (layout) ; projection document+layout → nodes/edges ; actions loadFromApi, saveDocument, saveLayout, updateDocument, updateLayout.
- **Projection** : module dédié recommandé (ex. `frontend/src/utils/documentToGraph.ts` ou `projection.ts`) : document + layout → { nodes, edges } ; inverse : édition UI → patches document + layout. Réutiliser ou adapter la logique actuelle de conversion (actuellement côté backend dans unity_dialogues/graph).
- **Composants** : GraphCanvas, NodeEditorPanel, ChoiceEditor — consommer nodes/edges dérivés du store ; les mises à jour passent par des actions store qui mettent à jour document/layout puis recalculent la projection.

### Tests

- Unit : projection document → nodes/edges avec IDs stables (choiceId, node.id, edge ids).
- Unit : store load/save via GET/PUT document et GET/PUT layout ; gestion 409.
- E2E : charger un dialogue → éditer line/speaker/choice → sauvegarder → recharger ; pas de reset du panel ; pas d'envoi nodes/edges au save.
- Non-régression : tests API documents (test_documents.py), E2E existants (graph, éditeur).

### Previous story (16.3) intelligence

- Story 16.3 a livré GET/PUT /documents/{id}/layout côté backend ; révision layout dans .layout.meta ; 409 si revision obsolète. Le frontend doit appeler GET layout après GET document (ou en parallèle) et PUT layout lors de la sauvegarde des positions. Ne pas mélanger revision document et revision layout (deux révisions distinctes).
- Fichiers modifiés en 16.3 : api/schemas/documents.py, api/routers/documents.py, tests/api/test_documents.py. En 16.4 : pas de changement backend ; frontend uniquement (api/documents.ts, graphStore, projection).
- Code review 16.3 : test PUT layout 409 (création sans layout, revision != 1) ; cohérence ensure_ascii=False pour .meta. Côté frontend : gérer 409 layout (afficher conflit, recharger layout, permettre réessayer).

### Project Structure Notes

- Alignement avec `docs/architecture/pipeline-unity-backend-front-architecture.md`. Frontend = client des endpoints documents et layout ; pas d’appel graph/load ni graph/save-and-write pour le flux principal document canonique.

### References

- [Source: _bmad-output/planning-artifacts/architecture/v10-architectural-decisions-adrs.md – ADR-008 Frontend, identités stables]
- [Source: _bmad-output/planning-artifacts/epics/epic-16.md – Story 16.4, GARDE-FOUS]
- [Source: docs/architecture/pipeline-unity-backend-front-architecture.md]
- [Source: api/routers/documents.py – GET/PUT document, GET/PUT layout]
- [Source: api/schemas/documents.py – DocumentGetResponse, PutDocumentRequest, LayoutGetResponse, PutLayoutRequest]
- [Source: frontend/src/store/graphStore.ts – état actuel nodes/edges, loadDialogue, saveDialogue]
- [Source: frontend/src/api/graph.ts – loadGraph, saveGraphAndWrite à remplacer par documents API pour le flux principal]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
