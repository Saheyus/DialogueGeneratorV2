# Story 0.6: Validation cycles graphe (ID-002)

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **utilisateur créant des dialogues**,
I want **être averti si mon graphe contient des cycles (boucles)**,
So that **je peux décider consciemment si les cycles sont intentionnels (dialogues récursifs) ou des erreurs**.

## Acceptance Criteria

1. **Given** un graphe de dialogue avec un cycle (nœud A → B → C → A)
   **When** je sauvegarde ou lance une validation
   **Then** un warning non-bloquant s'affiche "Cycle détecté : A → B → C → A"
   **And** les nœuds du cycle sont surlignés dans le graphe (couleur orange)
   **And** je peux continuer à travailler (pas de blocage)

2. **Given** un graphe avec plusieurs cycles
   **When** la validation détecte les cycles
   **Then** tous les cycles sont listés dans le warning
   **And** chaque cycle est cliquable pour zoomer sur les nœuds concernés

3. **Given** un cycle intentionnel (dialogue récursif "Boucle de conversation")
   **When** je vois le warning
   **Then** je peux marquer le cycle comme "intentionnel" (checkbox)
   **And** le warning ne réapparaît plus pour ce cycle spécifique
   **And** le cycle est toujours validé structurellement (pas d'erreur)

4. **Given** un graphe sans cycles
   **When** je lance une validation
   **Then** aucun warning cycle n'est affiché
   **And** la validation structurelle continue normalement (orphans, START, etc.)

## Tasks / Subtasks

- [ ] Task 1: Améliorer détection cycles backend pour retourner chemin complet (AC: #1, #2)
  - [ ] Modifier `GraphValidationService._validate_cycles()` pour retourner chemin complet du cycle (liste de nœuds)
  - [ ] Retourner format `{cycle_id: string, nodes: [node_id1, node_id2, ...], path: "A → B → C → A"}`
  - [ ] Gérer plusieurs cycles distincts (chaque cycle a son propre `cycle_id`)
  - [ ] Tests unitaires : détection cycle avec chemin complet, détection plusieurs cycles

- [ ] Task 2: Étendre schéma API pour inclure chemin complet cycles (AC: #1, #2)
  - [ ] Modifier `api/schemas/graph.py::ValidationErrorDetail` pour inclure `cycle_path: Optional[str]` et `cycle_nodes: Optional[List[str]]`
  - [ ] Modifier `api/routers/graph.py::validate_graph()` pour mapper chemin complet depuis `GraphValidationService`
  - [ ] Tests unitaires : schéma inclut cycle_path et cycle_nodes

- [ ] Task 3: Améliorer affichage cycles dans GraphEditor.tsx (AC: #1, #2)
  - [ ] Afficher chemin complet du cycle dans le warning (format "A → B → C → A")
  - [ ] Rendre chaque cycle cliquable pour zoomer sur les nœuds concernés
  - [ ] Utiliser `reactFlowInstance.fitView()` avec `nodes: cycle_nodes` pour zoomer
  - [ ] Tests E2E : clic sur cycle zoome vers nœuds concernés

- [ ] Task 4: Implémenter highlight orange des nœuds dans cycles (AC: #1)
  - [ ] Ajouter état `highlightedCycleNodes: Set<string>` dans `graphStore.ts`
  - [ ] Mettre à jour `highlightedCycleNodes` quand cycles détectés
  - [ ] Modifier `GraphCanvas.tsx` pour appliquer style orange aux nœuds dans `highlightedCycleNodes`
  - [ ] Style : `border: 3px solid orange`, `backgroundColor: rgba(255, 165, 0, 0.2)`
  - [ ] Réinitialiser highlight quand validation relancée sans cycles
  - [ ] Tests E2E : nœuds cycles surlignés orange

- [ ] Task 5: Implémenter marquage cycles comme "intentionnels" (AC: #3)
  - [ ] Ajouter état `intentionalCycles: Set<string>` dans `graphStore.ts` (persisté localStorage)
  - [ ] Ajouter checkbox "Marquer comme intentionnel" dans affichage warning cycle
  - [ ] Quand checkbox cochée, ajouter `cycle_id` à `intentionalCycles`
  - [ ] Filtrer cycles intentionnels dans affichage warnings (ne pas afficher si dans `intentionalCycles`)
  - [ ] Persister `intentionalCycles` dans localStorage (clé `graph_intentional_cycles`)
  - [ ] Tests unitaires : filtrage cycles intentionnels, persistance localStorage
  - [ ] Tests E2E : marquer cycle intentionnel, warning disparaît

- [ ] Task 6: Validation et tests (AC: #4)
  - [ ] Tests unitaires : détection cycles avec chemin complet, plusieurs cycles
  - [ ] Tests intégration : API validation retourne cycles avec chemin complet
  - [ ] Tests E2E : warning affiché, highlight orange, zoom, marquage intentionnel
  - [ ] Tests E2E : graphe sans cycles ne montre pas de warning cycle

## Dev Notes

### Architecture Patterns (Extension Story 0.1)

**Réutilisation existante :**
- ✅ **Service existant** : `GraphValidationService._validate_cycles()` existe déjà (ligne 310-355 `services/graph_validation_service.py`)
  - **DÉCISION** : Étendre pour retourner chemin complet du cycle au lieu de juste détecter
  - **COMMENT** : Modifier algorithme DFS pour stocker chemin complet (backtracking)
- ✅ **Endpoint existant** : `/api/v1/graph/validate` existe déjà (ligne 310-363 `api/routers/graph.py`)
  - **DÉCISION** : Étendre schéma pour inclure `cycle_path` et `cycle_nodes`
  - **COMMENT** : Modifier `ValidationErrorDetail` pour inclure champs optionnels cycles
- ✅ **Affichage existant** : Erreurs/warnings affichés dans `GraphEditor.tsx` (ligne 693-873)
  - **DÉCISION** : Étendre affichage pour cycles avec chemin complet et actions
  - **COMMENT** : Ajouter section spéciale pour cycles avec checkbox "intentionnel" et bouton zoom

**Gestion cycles intentionnels :**
- **Persistance** : localStorage avec clé `graph_intentional_cycles` (Set de `cycle_id`)
- **Cycle ID** : Format `cycle_{hash(nodes)}` pour identifier un cycle de manière stable
- **Filtrage** : Ne pas afficher warning si `cycle_id` dans `intentionalCycles`
- **Validation structurelle** : Les cycles intentionnels sont toujours détectés structurellement (pas d'erreur, juste pas de warning)

**Highlight orange nœuds :**
- **État** : `highlightedCycleNodes: Set<string>` dans `graphStore.ts`
- **Mise à jour** : Quand validation retourne cycles, extraire tous les nœuds des cycles et mettre à jour `highlightedCycleNodes`
- **Style React Flow** : Utiliser `node.style` pour appliquer border orange et background semi-transparent
- **Réinitialisation** : Réinitialiser `highlightedCycleNodes` quand validation relancée sans cycles

**Zoom automatique vers cycles :**
- **React Flow API** : `reactFlowInstance.fitView({ nodes: cycle_nodes, padding: 0.2 })`
- **Action** : Clic sur cycle dans liste warnings déclenche zoom vers nœuds du cycle
- **UX** : Animation fluide (React Flow gère animation automatiquement)

### Fichiers existants à vérifier et étendre

**Backend :**
- ✅ `services/graph_validation_service.py` : Méthode `_validate_cycles()` existe (ligne 310-355)
  - **DÉCISION** : Étendre pour retourner chemin complet du cycle
  - **COMMENT** : Modifier DFS pour stocker chemin (backtracking), retourner format `{cycle_id, nodes, path}`
- ✅ `api/routers/graph.py` : Endpoint `/api/v1/graph/validate` existe (ligne 310-363)
  - **DÉCISION** : Étendre pour mapper chemin complet depuis service
  - **COMMENT** : Extraire `cycle_path` et `cycle_nodes` depuis `GraphValidationService` et inclure dans `ValidationErrorDetail`
- ✅ `api/schemas/graph.py` : Schéma `ValidationErrorDetail` existe
  - **DÉCISION** : Étendre avec champs optionnels `cycle_path: Optional[str]` et `cycle_nodes: Optional[List[str]]`
  - **COMMENT** : Ajouter champs pour cycles uniquement (None pour autres types d'erreurs/warnings)

**Frontend :**
- ✅ `frontend/src/store/graphStore.ts` : Store existe avec `validationErrors` (ligne 100)
  - **DÉCISION** : Ajouter `highlightedCycleNodes: Set<string>` et `intentionalCycles: Set<string>`
  - **COMMENT** : Gérer highlight et filtrage cycles intentionnels
- ✅ `frontend/src/components/graph/GraphEditor.tsx` : Affichage erreurs/warnings existe (ligne 693-873)
  - **DÉCISION** : Étendre affichage pour cycles avec chemin complet, checkbox intentionnel, bouton zoom
  - **COMMENT** : Ajouter section spéciale pour cycles avec actions interactives
- ✅ `frontend/src/components/graph/GraphCanvas.tsx` : Rendu nœuds React Flow existe
  - **DÉCISION** : Appliquer style orange aux nœuds dans `highlightedCycleNodes`
  - **COMMENT** : Utiliser `node.style` pour border orange et background semi-transparent

### Patterns existants à respecter

**Zustand stores :**
- Immutable updates : `set((state) => ({ ...state, newValue }))`
- Pattern validation : `validationErrors` déjà géré (ligne 100 graphStore.ts)
- Persistance localStorage : Pattern existant pour auto-save draft (Story 0.5)

**FastAPI routers :**
- Namespace `/api/v1/graph/*` (cohérent)
- Pattern endpoint : `@router.post("/validate", response_model=ValidateGraphResponse)`
- Gestion erreurs : `InternalServerException` avec `request_id`

**React composants :**
- Pattern affichage erreurs : `GraphEditor.tsx` ligne 693-873 (grouper par type, icônes, labels)
- Pattern React Flow : `node.style` pour styling dynamique
- Pattern zoom : `reactFlowInstance.fitView()` avec options

**Gestion cycles :**
- **Algorithme DFS** : Existant dans `_validate_cycles()`, à étendre pour chemin complet
- **Format cycle ID** : `cycle_{hash(sorted(nodes))}` pour identifier cycle de manière stable
- **Chemin format** : `"A → B → C → A"` (noms displayName ou IDs selon disponibilité)

### Format cycle ID

**Pattern pour identifier cycles de manière stable :**
- **Format** : `cycle_{hash(sorted(node_ids))}`
- **Exemple** : Cycle A → B → C → A → `cycle_{hash(["A", "B", "C"])}`
- **Raison** : Permet d'identifier le même cycle même si ordre de détection change
- **Persistance** : `intentionalCycles` stocke Set de `cycle_id` dans localStorage

### Références techniques

**Source: `_bmad-output/planning-artifacts/prd/epic-00.md#Story-0.6`**
- Story complète avec acceptance criteria et technical requirements

**Source: `services/graph_validation_service.py#_validate_cycles` (ligne 310-355)**
- Méthode existante à étendre pour chemin complet

**Source: `api/routers/graph.py#validate_graph` (ligne 310-363)**
- Endpoint existant à étendre pour cycles avec chemin

**Source: `frontend/src/components/graph/GraphEditor.tsx` (ligne 693-873)**
- Affichage erreurs/warnings existant à étendre

**Source: `frontend/src/components/graph/GraphCanvas.tsx`**
- Rendu nœuds React Flow à étendre pour highlight orange

**Source: ID-002 (Architecture Document)**
- Décision architecture : Validation cycles warning non-bloquant

**Source: Story 0.1 (Graph Fix stableID)**
- Format IDs stable (utiliser pour cycle_id)

### Project Structure Notes

**Alignment avec structure unifiée :**
- ✅ Backend API : `api/routers/graph.py` (cohérent)
- ✅ Backend services : `services/graph_validation_service.py` (cohérent)
- ✅ Frontend stores : `frontend/src/store/graphStore.ts` (cohérent)
- ✅ Frontend components : `frontend/src/components/graph/` (cohérent)

**Détecté conflits ou variances :**
- Aucun conflit détecté, extension cohérente avec architecture existante

### References

- [Source: `_bmad-output/planning-artifacts/prd/epic-00.md#Story-0.6`] Story complète avec requirements
- [Source: ID-002] Architecture Decision : Validation cycles warning non-bloquant
- [Source: `services/graph_validation_service.py#_validate_cycles`] Méthode existante à étendre
- [Source: `api/routers/graph.py#validate_graph`] Endpoint existant à étendre
- [Source: `frontend/src/components/graph/GraphEditor.tsx`] Affichage erreurs existant à étendre
- [Source: `frontend/src/components/graph/GraphCanvas.tsx`] Rendu nœuds React Flow à étendre
- [Source: Story 0.1] Graph Fix stableID (format IDs à respecter)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
