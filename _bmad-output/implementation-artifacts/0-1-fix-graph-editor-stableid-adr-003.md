# Story 0.1: Fix Graph Editor stableID (ADR-003)

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **développeur/utilisateur**,
I want **que les nœuds du graphe utilisent stableID (UUID) au lieu de displayName comme identifiant**,
so that **le graphe ne se corrompe pas lors du renommage de dialogues et que les connexions restent stables**.

## Acceptance Criteria

1. **Given** un dialogue existant avec des nœuds dans le graphe
   **When** je renomme le dialogue (displayName change)
   **Then** toutes les connexions parent/enfant restent intactes
   **And** le graphe se charge correctement sans erreurs

2. **Given** un dialogue sans stableID (données legacy)
   **When** le dialogue est chargé dans l'éditeur
   **Then** un stableID (UUID) est généré automatiquement
   **And** le dialogue est sauvegardé avec le nouveau stableID

3. **Given** un graphe avec plusieurs nœuds
   **When** je crée une connexion entre deux nœuds
   **Then** la connexion utilise les stableID des nœuds (pas displayName)
   **And** la connexion persiste après sauvegarde/chargement

4. **Given** un dialogue avec displayName dupliqué
   **When** le graphe est rendu
   **Then** aucun conflit d'ID ne se produit (chaque nœud a un stableID unique)
   **And** tous les nœuds sont visibles et éditables

## Tasks / Subtasks

- [ ] Task 1: Créer fonction utilitaire `generateStableID()` (AC: #2)
  - [ ] Créer `frontend/src/utils/uuid.ts` avec fonction `generateStableID(): string`
  - [ ] Utiliser `crypto.randomUUID()` (natif navigateur) ou bibliothèque `uuid` si nécessaire
  - [ ] Tests unitaires : vérifier unicité (générer 1000 UUID, vérifier aucun doublon)
  - [ ] Tests unitaires : vérifier format UUID v4 valide

- [ ] Task 2: Modifier conversion Unity → ReactFlow pour utiliser stableID (AC: #1, #3)
  - [ ] Modifier `services/graph_conversion_service.py::unity_json_to_graph()`
  - [ ] Ajouter logique : si nœud Unity a `stableID` → utiliser comme `node.id`, sinon générer UUID
  - [ ] Stocker `displayName` (ou `id` Unity) dans `node.data.displayName` pour affichage UI
  - [ ] Tests intégration : conversion avec/sans stableID, vérifier `node.id` = UUID

- [ ] Task 3: Modifier conversion ReactFlow → Unity pour préserver stableID (AC: #1, #3)
  - [ ] Modifier `services/graph_conversion_service.py::graph_to_unity_json()`
  - [ ] Extraire `stableID` depuis `node.id` (UUID) et l'ajouter au nœud Unity
  - [ ] Préserver `displayName` depuis `node.data.displayName` si présent
  - [ ] Tests intégration : round-trip conversion (Unity → ReactFlow → Unity), vérifier stableID préservé

- [ ] Task 4: Modifier frontend GraphStore pour utiliser stableID (AC: #1, #3, #4)
  - [ ] Modifier `frontend/src/store/graphStore.ts::loadDialogue()`
  - [ ] Vérifier que `node.id` utilise stableID (UUID) et non displayName
  - [ ] Modifier `frontend/src/store/graphStore.ts::generateFromNode()` pour générer stableID pour nouveaux nœuds
  - [ ] Tests unitaires : vérifier `node.id` format UUID dans store

- [ ] Task 5: Migration données existantes (AC: #2)
  - [ ] Créer script `scripts/migrate-stableids.py` pour migration batch
  - [ ] Script : charger dialogues Unity JSON, générer stableID si manquant, sauvegarder backup + nouveau fichier
  - [ ] Tests : migration dialogue sans stableID, vérifier stableID généré et sauvegardé

- [ ] Task 6: Tests régression collisions displayName (AC: #4)
  - [ ] Créer test E2E : dialogue avec 2 nœuds displayName identique, vérifier aucun conflit
  - [ ] Créer test intégration : conversion graphe avec displayName dupliqués, vérifier stableID uniques
  - [ ] Tests unitaires : `generateStableID()` génère UUID uniques même avec displayName identiques

- [ ] Task 7: Tests E2E renommage dialogue (AC: #1)
  - [ ] Créer test Playwright : charger dialogue, renommer, vérifier connexions intactes
  - [ ] Test : sauvegarder, recharger, vérifier graphe identique (connexions préservées)

## Dev Notes

### Architecture Patterns

**Séparation ID technique vs Display :**
- **ID technique (stableID)** : UUID immuable, utilisé pour `node.id` ReactFlow et connexions
- **Display name** : Nom éditable affiché dans UI, stocké dans `node.data.displayName`

**Pattern de conversion :**
- Unity JSON → ReactFlow : `node.id = unity_node.stableID || generateStableID()`
- ReactFlow → Unity JSON : `unity_node.stableID = node.id` (UUID), `unity_node.id = node.data.displayName || node.id` (pour compatibilité Unity)

**Backward Compatibility :**
- Dialogues legacy sans stableID : génération automatique au chargement
- Migration gracieuse : script batch pour migration existante, auto-génération pour nouveaux chargements

### Source Tree Components

**Backend (Python) :**
- `services/graph_conversion_service.py` : 
  - `unity_json_to_graph()` : Ligne 13-73, modifier pour utiliser stableID
  - `graph_to_unity_json()` : Ligne 176-231, modifier pour préserver stableID
- `scripts/migrate-stableids.py` : **NOUVEAU** - Script migration batch

**Frontend (TypeScript) :**
- `frontend/src/utils/uuid.ts` : **NOUVEAU** - Fonction `generateStableID()`
- `frontend/src/store/graphStore.ts` :
  - `loadDialogue()` : Ligne 106-146, vérifier utilisation stableID
  - `generateFromNode()` : Ligne 263-323, générer stableID pour nouveaux nœuds
- `frontend/src/components/graph/GraphEditor.tsx` : Pas de modification directe (utilise store)

**Tests :**
- `tests/services/test_graph_conversion_service.py` : Tests conversion avec/sans stableID
- `tests/utils/test_uuid.ts` : **NOUVEAU** - Tests `generateStableID()`
- `tests/frontend/graphStore.test.ts` : Tests store avec stableID
- `e2e/graph-stableid.spec.ts` : **NOUVEAU** - Tests E2E renommage + collisions

### Technical Constraints

**UUID Format :**
- Utiliser UUID v4 (RFC 4122) : format `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`
- Bibliothèque : `crypto.randomUUID()` (natif navigateur moderne) ou `uuid` package si fallback nécessaire

**Unity JSON Compatibility :**
- Unity utilise `id` (SCREAMING_SNAKE_CASE) pour identification nœuds
- Ajouter champ `stableID` (UUID) dans nœuds Unity pour traçabilité
- Préserver `id` Unity existant pour compatibilité (peut être displayName ou autre)

**React Flow Requirements :**
- React Flow `node.id` : DOIT être string unique, utilisé pour connexions (edges source/target)
- React Flow `node.data` : Stocke données Unity complètes (incluant displayName pour UI)

**Migration Strategy :**
- Script batch : Parcourir `Assets/Dialogues/`, charger JSON, générer stableID si manquant, sauvegarder backup + nouveau
- Auto-migration : Au chargement dialogue sans stableID, générer automatiquement et sauvegarder

### Testing Standards

**Unit Tests :**
- `generateStableID()` : Unicité (1000 générations, vérifier aucun doublon), format UUID v4 valide
- Conversion services : Round-trip (Unity → ReactFlow → Unity), vérifier stableID préservé

**Integration Tests :**
- Graph conversion : Dialogue avec/sans stableID, vérifier comportement correct
- Store : Chargement dialogue legacy, vérifier stableID auto-généré

**E2E Tests (Playwright) :**
- Renommage dialogue : Charger dialogue, renommer, sauvegarder, recharger, vérifier connexions intactes
- Collisions displayName : Créer 2 nœuds displayName identique, vérifier aucun conflit (stableID uniques)

### Project Structure Notes

**Alignment :**
- ✅ Utilise structure existante : `services/` pour logique métier, `frontend/src/utils/` pour utilitaires
- ✅ Suit patterns Zustand : Store `graphStore.ts` pour état graphe
- ✅ Suit patterns FastAPI : Service `GraphConversionService` pour conversion

**New Files :**
- `frontend/src/utils/uuid.ts` : Utilitaire UUID (nouveau fichier)
- `scripts/migrate-stableids.py` : Script migration (nouveau fichier)
- `tests/utils/test_uuid.ts` : Tests UUID (nouveau fichier)
- `e2e/graph-stableid.spec.ts` : Tests E2E (nouveau fichier)

**Modified Files :**
- `services/graph_conversion_service.py` : Conversion Unity ↔ ReactFlow
- `frontend/src/store/graphStore.ts` : Store graphe (chargement, génération)

### References

- **ADR-003** : [Source: _bmad-output/planning-artifacts/architecture/v10-architectural-decisions-adrs.md#ADR-003] - Graph Editor Fixes (DisplayName vs stableID)
- **Epic 0 Story 0.1** : [Source: _bmad-output/planning-artifacts/epics/epic-00.md#Story-0.1] - Fix Graph Editor stableID
- **NFR-R1** : Zero Blocking Bugs - Ce fix résout bug critique corruption graphe
- **React Flow Documentation** : `node.id` doit être string unique pour connexions
- **UUID RFC 4122** : Format UUID v4 standard pour identifiants uniques

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
