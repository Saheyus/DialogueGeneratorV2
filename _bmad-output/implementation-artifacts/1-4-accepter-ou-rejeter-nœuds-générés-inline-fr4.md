# Story 1.4: Accepter ou rejeter nœuds générés inline (FR4)

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **utilisateur générant des dialogues**,
I want **accepter ou rejeter les nœuds générés directement dans le graphe**,
so that **je peux itérer rapidement sur la qualité des dialogues sans workflow complexe**.

### Valeur Ajoutée par rapport au workflow actuel

**Actuellement :** On peut générer un nœud puis le supprimer avec la touche Suppr (avec confirmation).

**Avec cette story :**
1. **Visibilité de l'état** : Les nœuds générés sont visuellement distincts (bordure orange "pending") des nœuds validés (bordure verte "accepted"), permettant d'identifier rapidement dans un batch quels nœuds nécessitent validation
2. **Session recovery** : Les nœuds pending sont restaurés après reload de l'application (évite la perte de travail si fermeture accidentelle)
3. **Workflow batch optimisé** : Accept/reject inline sur chaque nœud sans sélection préalable (plus rapide que sélectionner puis Suppr pour chaque nœud)
4. **Préparation Story 1.10** : Le mécanisme de rejet prépare la régénération avec instructions ajustées (Story 1.10 bloquée sans cette story)

## Acceptance Criteria

1. **Given** un nœud vient d'être généré et apparaît dans le graphe
   **When** je survole le nœud
   **Then** des boutons "Accepter" (✓) et "Rejeter" (✗) s'affichent sur le nœud
   **And** le nœud est en état "pending" (couleur orange/border dashed)

2. **Given** je clique sur "Accepter"
   **When** le nœud est accepté
   **Then** le nœud passe en état "accepted" (couleur verte/border solid)
   **And** le nœud est sauvegardé dans le dialogue (persisté)
   **And** les boutons Accepter/Rejeter disparaissent

3. **Given** je clique sur "Rejeter"
   **When** le nœud est rejeté
   **Then** le nœud est supprimé du graphe (pas sauvegardé)
   **And** un message "Nœud rejeté" s'affiche
   **And** je peux régénérer le nœud avec instructions ajustées (voir Story 1.10)

4. **Given** j'ai plusieurs nœuds pending dans le graphe (batch généré)
   **When** je navigue dans le graphe
   **Then** tous les nœuds pending affichent les boutons Accepter/Rejeter au survol
   **And** je peux accepter/rejeter chaque nœud indépendamment sans sélection préalable
   **And** je peux voir visuellement quels nœuds sont pending (bordure orange) vs accepted (bordure verte)

5. **Given** je ferme l'application avec des nœuds pending
   **When** je rouvre l'application
   **Then** les nœuds pending sont restaurés (session recovery)
   **And** je peux toujours accepter/rejeter ces nœuds

## Tasks / Subtasks

- [ ] Task 1: Ajouter état "pending" aux nœuds générés (AC: #1)
  - [ ] Modifier `graphStore.ts` pour marquer nœuds générés avec `status: "pending"`
  - [ ] Ajouter `nodeStatus` dans `DialogueNodeData` interface
  - [ ] Persister `status` dans le dialogue JSON (champ métadonnée, non Unity)
- [ ] Task 2: Implémenter UI accept/reject dans `DialogueNode.tsx` (AC: #1, #2, #3)
  - [ ] Ajouter boutons "Accepter" (✓) et "Rejeter" (✗) visibles au survol
  - [ ] Styliser nœuds pending (bordure orange dashed)
  - [ ] Styliser nœuds accepted (bordure verte solid)
  - [ ] Masquer boutons après accept/reject
- [ ] Task 3: Implémenter logique accept/reject dans `graphStore.ts` (AC: #2, #3)
  - [ ] Ajouter méthode `acceptNode(nodeId: string)` dans `useGraphStore`
  - [ ] Ajouter méthode `rejectNode(nodeId: string)` dans `useGraphStore`
  - [ ] Accept: changer status à "accepted", déclencher sauvegarde
  - [ ] Reject: supprimer nœud du graphe, afficher toast
- [ ] Task 4: Implémenter endpoints API accept/reject (AC: #2, #3)
  - [ ] Créer endpoint `POST /api/v1/unity-dialogues/graph/nodes/{nodeId}/accept` dans `api/routers/graph.py`
  - [ ] Créer endpoint `POST /api/v1/unity-dialogues/graph/nodes/{nodeId}/reject` dans `api/routers/graph.py`
  - [ ] Accept: mettre à jour dialogue JSON avec status "accepted"
  - [ ] Reject: supprimer nœud du dialogue JSON
- [ ] Task 5: Intégrer accept/reject dans workflow de génération (AC: #1)
  - [ ] Modifier `generateFromNode()` dans `graphStore.ts` pour marquer nœuds générés comme "pending"
  - [ ] S'assurer que nœuds batch sont aussi marqués "pending"
- [ ] Task 6: Session recovery pour nœuds pending (AC: #5)
  - [ ] Sauvegarder nœuds pending dans dialogue JSON (champ `status: "pending"`)
  - [ ] Restaurer nœuds pending lors du chargement (`loadDialogue()`)
  - [ ] Vérifier que nœuds pending sont visibles après reload
- [ ] Task 7: Tests (AC: tous)
  - [ ] Unit: logique accept/reject dans `graphStore.ts`
  - [ ] Integration: API accept/reject endpoints
  - [ ] E2E: workflow complet accept/reject depuis génération

## Dev Notes

### Contexte Epic et Story

**Epic 1: Amélioration et peaufinage de la génération de dialogues**
- **Objectif:** Améliorer l'expérience utilisateur et la robustesse de la génération de dialogues existante
- **Valeur:** Réduire la friction dans le workflow de génération, améliorer la qualité des dialogues générés
- **Statut:** 8 stories DONE (1.1, 1.2, 1.3, 1.5, 1.8, 1.9, 1.13), 3 PRIORITÉ A (1.4, 1.6, 1.10)

**Story 1.4: Accepter ou rejeter nœuds générés inline (FR4)**
- **Valeur:** 
  - **Visibilité de l'état** : Distinction visuelle pending (orange) vs accepted (vert) pour identifier rapidement les nœuds à valider dans un batch
  - **Session recovery** : Nœuds pending restaurés après reload (évite perte de travail)
  - **Workflow batch optimisé** : Accept/reject inline sans sélection préalable (plus rapide que Suppr)
  - **Préparation Story 1.10** : Mécanisme de rejet nécessaire pour régénération avec instructions ajustées
- **Dépendances:** Story 1.1 (génération single), Story 1.2 (génération batch), Story 1.9 (auto-link)
- **Bloque:** Story 1.10 (régénération avec instructions ajustées)

### Vérification Codebase Existant

**✅ Fichiers/Composants à Étendre (pas de création nouvelle):**

1. **`frontend/src/store/graphStore.ts`** (EXISTE)
   - **Décision:** Étendre avec méthodes `acceptNode()` et `rejectNode()`
   - **Justification:** Le store gère déjà tous les nœuds du graphe, logique CRUD existante
   - **Modifications:**
     - Ajouter `nodeStatus: "pending" | "accepted" | null` dans `DialogueNodeData`
     - Ajouter méthodes `acceptNode(nodeId: string)` et `rejectNode(nodeId: string)`
     - Modifier `generateFromNode()` pour marquer nœuds générés comme "pending"
     - Modifier `loadDialogue()` pour restaurer nœuds pending depuis JSON

2. **`frontend/src/components/graph/nodes/DialogueNode.tsx`** (EXISTE)
   - **Décision:** Étendre avec UI accept/reject
   - **Justification:** Composant existant qui affiche déjà les nœuds, logique de survol présente
   - **Modifications:**
     - Ajouter boutons "Accepter" (✓) et "Rejeter" (✗) visibles au survol si `status === "pending"`
     - Ajouter styles conditionnels: bordure orange dashed (pending), verte solid (accepted)
     - Connecter boutons aux méthodes `acceptNode()` et `rejectNode()` du store

3. **`api/routers/graph.py`** (EXISTE)
   - **Décision:** Ajouter 2 nouveaux endpoints dans le router existant
   - **Justification:** Router existant pour toutes les opérations graphe (`/api/v1/unity-dialogues/graph/*`)
   - **Modifications:**
     - Ajouter `POST /api/v1/unity-dialogues/graph/nodes/{nodeId}/accept`
     - Ajouter `POST /api/v1/unity-dialogues/graph/nodes/{nodeId}/reject`
     - Utiliser `GraphConversionService` existant pour charger/sauvegarder dialogue JSON

4. **`services/graph_conversion_service.py`** (EXISTE - probablement)
   - **Décision:** Étendre pour gérer champ `status` dans métadonnées nœuds
   - **Justification:** Service existant qui convertit Unity JSON ↔ ReactFlow
   - **Modifications:**
     - Ajouter support champ `status` dans conversion (champ métadonnée, non Unity standard)
     - Le champ `status` doit être préservé lors conversion mais non exporté vers Unity JSON final

**❌ Fichiers/Composants à Créer (nouveaux):**

Aucun nouveau fichier requis. Toute la logique s'intègre dans les composants existants.

### Architecture et Patterns

**Patterns Zustand (graphStore.ts):**
- Utiliser `set()` avec spread operator pour updates immutables: `set({ nodes: [...nodes, newNode] })`
- Suivre pattern existant: méthodes async pour API calls, state loading flags (`isSaving`, `isGenerating`)
- Utiliser `temporal` middleware pour undo/redo (déjà présent)

**Patterns FastAPI (graph.py):**
- Suivre structure existante: `@router.post()` avec `response_model` et `status_code`
- Utiliser `Annotated[str, Depends(get_request_id)]` pour request ID
- Lever `ValidationException` pour erreurs de validation
- Utiliser `GraphConversionService` pour manipulation dialogue JSON

**Patterns React (DialogueNode.tsx):**
- Utiliser `useState` pour état hover local
- Utiliser `useGraphStore()` hook pour accéder au store
- Suivre pattern existant: styles conditionnels basés sur `data.validationErrors`, `selected`, etc.
- Boutons inline avec `position: absolute` pour overlay sur nœud

**Structure Données:**

Le champ `status` doit être stocké dans les métadonnées du nœud ReactFlow (dans `data`), mais **PAS** dans le JSON Unity final. Le JSON Unity ne supporte pas ce champ - c'est une métadonnée interne à l'éditeur.

```typescript
// ReactFlow Node avec status
interface DialogueNodeData {
  id: string
  speaker?: string
  line?: string
  choices?: Choice[]
  status?: "pending" | "accepted"  // Métadonnée éditeur, non Unity
  // ... autres champs
}
```

Lors de la sauvegarde:
- Nœuds avec `status: "pending"` → sauvegardés dans dialogue JSON (champ métadonnée)
- Nœuds avec `status: "accepted"` → sauvegardés normalement, `status` retiré avant export Unity
- Nœuds rejetés → supprimés du dialogue, non sauvegardés

### Intégration avec Stories Existantes

**Story 1.1 (Génération single) - DONE:**
- Les nœuds générés par `generateFromNode()` doivent être automatiquement marqués `status: "pending"`
- Modifier `generateFromNode()` dans `graphStore.ts` après ajout nœud: `updateNode(nodeId, { status: "pending" })`

**Story 1.2 (Génération batch) - DONE:**
- Les nœuds batch générés doivent aussi être marqués `status: "pending"`
- Même logique que single: après `addNode()` pour chaque nœud batch, ajouter `status: "pending"`

**Story 1.9 (Auto-link) - DONE:**
- Les connexions auto-link doivent être préservées même si nœud est en "pending"
- Lors accept: nœud accepté garde ses connexions
- Lors reject: connexions supprimées avec le nœud

**Story 1.10 (Régénération) - BLOQUÉE par cette story:**
- Cette story doit être complétée avant Story 1.10
- Story 1.10 utilisera le mécanisme de reject pour permettre régénération

**Epic 0 Story 0.5 (Auto-save) - DONE:**
- Les nœuds pending doivent être inclus dans l'auto-save
- L'auto-save doit sauvegarder le champ `status: "pending"` dans le draft

### Session Recovery

Les nœuds pending doivent être persistés dans le dialogue JSON (champ métadonnée) et restaurés lors du chargement:

1. **Sauvegarde:** Lors `saveDialogue()`, inclure nœuds avec `status: "pending"` dans JSON
2. **Chargement:** Lors `loadDialogue()`, restaurer nœuds avec `status: "pending"` depuis JSON
3. **Export Unity:** Avant export final vers Unity JSON, retirer champ `status` (non supporté Unity)

### Project Structure Notes

**Alignement avec structure unifiée:**
- ✅ Frontend: `frontend/src/components/graph/nodes/DialogueNode.tsx` (existant)
- ✅ Store: `frontend/src/store/graphStore.ts` (existant)
- ✅ API: `api/routers/graph.py` (existant)
- ✅ Services: `services/graph_conversion_service.py` (existant)

**Pas de conflits détectés** - tous les fichiers existent et suivent les conventions du projet.

### Testing Standards

**Unit Tests:**
- `tests/frontend/graphStore.test.ts`: Tester `acceptNode()` et `rejectNode()` logique
- Vérifier que status "pending" est ajouté lors génération
- Vérifier que accept change status à "accepted"
- Vérifier que reject supprime nœud

**Integration Tests:**
- `tests/api/test_graph_accept_reject.py`: Tester endpoints API
- Tester accept: vérifier dialogue JSON mis à jour avec status "accepted"
- Tester reject: vérifier nœud supprimé du dialogue JSON
- Tester erreurs: nœud inexistant, dialogue inexistant

**E2E Tests (Playwright):**
- `e2e/graph-node-accept-reject.spec.ts`: Workflow complet
- Générer nœud → voir boutons accept/reject → accepter → vérifier status
- Générer nœud → rejeter → vérifier suppression
- Session recovery: générer nœud pending → reload page → vérifier restauration

### References

- **FR4:** Accepter ou rejeter nœuds générés inline
- **Story 1.1:** Génération single (dépendance)
- **Story 1.2:** Génération batch (dépendance)
- **Story 1.9:** Auto-link (connexions préservées)
- **Story 1.10:** Régénération (bloquée par cette story)
- **Epic 0 Story 0.5:** Auto-save (intégration session recovery)
- **Epic 0 Story 0.2:** Progress Modal (génération en cours)
- **Source:** `_bmad-output/planning-artifacts/epics/epic-01.md#story-14`

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
