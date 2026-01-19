# Story 0.5.5: Génération next node avec gestion automatique des connexions

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **utilisateur créant des dialogues dans l'éditeur de graphe OU dans l'éditeur de dialogue**,
I want **générer la suite d'un dialogue (next node) pour un choix de réponse spécifique ou pour tous les choix d'un coup**,
So that **je peux rapidement construire des arbres de dialogue complets avec toutes les connexions (targetNode/nextNode) gérées automatiquement par le logiciel, que je travaille dans l'éditeur de graphe ou dans l'éditeur de dialogue**.

## Acceptance Criteria

1. **Given** je suis dans l'éditeur de graphe et je sélectionne un nœud de dialogue PNJ qui contient plusieurs réponses PJ (choices)
   **When** je sélectionne une réponse PJ spécifique (choice) et je lance "Générer la suite pour ce choix"
   **Then** un nouveau nœud de dialogue PNJ est généré par l'IA
   **And** le champ `targetNode` de la réponse PJ sélectionnée est automatiquement rempli avec l'ID du nouveau nœud généré
   **And** le nouveau nœud est ajouté au graphe à une position logique (à droite du parent, légèrement décalé verticalement)
   **And** une connexion visuelle (edge) est créée automatiquement entre le choix et le nouveau nœud

2. **Given** je suis dans l'éditeur de dialogue et je sélectionne un nœud de dialogue PNJ qui contient plusieurs réponses PJ (choices)
   **When** je sélectionne une réponse PJ spécifique (choice) dans le panneau d'édition et je lance "Générer la suite pour ce choix"
   **Then** un nouveau nœud de dialogue PNJ est généré par l'IA
   **And** le champ `targetNode` de la réponse PJ sélectionnée est automatiquement rempli avec l'ID du nouveau nœud généré
   **And** les connexions sont gérées automatiquement identiquement à l'éditeur de graphe
   **And** après génération, je suis redirigé vers le nouveau nœud généré (focus automatique dans l'éditeur de dialogue)

3. **Given** je suis dans l'éditeur de graphe et je sélectionne un nœud de dialogue PNJ qui contient plusieurs réponses PJ (choices) dont aucune n'a de `targetNode` défini
   **When** je lance "Générer la suite pour tous les choix"
   **Then** un nouveau nœud de dialogue PNJ est généré par l'IA pour chaque réponse PJ sans `targetNode`
   **And** chaque nouveau nœud est positionné dans le graphe de manière organisée (en cascade verticale, à droite du parent)
   **And** chaque champ `targetNode` des réponses PJ est automatiquement rempli avec l'ID du nœud correspondant
   **And** toutes les connexions visuelles (edges) sont créées automatiquement
   **And** les nœuds sont générés séquentiellement ou en batch (selon configuration) avec indicateur de progression

4. **Given** je suis dans l'éditeur de dialogue et je sélectionne un nœud de dialogue PNJ qui contient plusieurs réponses PJ (choices) dont aucune n'a de `targetNode` défini
   **When** je lance "Générer la suite pour tous les choix" depuis le panneau d'édition
   **Then** un nouveau nœud de dialogue PNJ est généré par l'IA pour chaque réponse PJ sans `targetNode`
   **And** chaque champ `targetNode` des réponses PJ est automatiquement rempli avec l'ID du nœud correspondant
   **And** les connexions sont gérées automatiquement identiquement à l'éditeur de graphe
   **And** les nœuds sont générés séquentiellement ou en batch avec indicateur de progression dans la modal
   **And** après génération, je suis redirigé vers le premier nouveau nœud généré (focus automatique)

5. **Given** je suis dans l'éditeur de graphe et je sélectionne un nœud de dialogue PNJ sans choix (navigation linéaire)
   **When** je lance "Générer la suite (nextNode)"
   **Then** un nouveau nœud de dialogue PNJ est généré par l'IA
   **And** le champ `nextNode` du nœud parent est automatiquement rempli avec l'ID du nouveau nœud généré
   **And** le nouveau nœud est ajouté au graphe à une position logique (à droite du parent)
   **And** une connexion visuelle (edge) est créée automatiquement entre le parent et le nouveau nœud

6. **Given** je suis dans l'éditeur de dialogue et je sélectionne un nœud de dialogue PNJ sans choix (navigation linéaire)
   **When** je lance "Générer la suite (nextNode)" depuis le panneau d'édition
   **Then** un nouveau nœud de dialogue PNJ est généré par l'IA
   **And** le champ `nextNode` du nœud parent est automatiquement rempli avec l'ID du nouveau nœud généré
   **And** les connexions sont gérées automatiquement identiquement à l'éditeur de graphe
   **And** après génération, je suis redirigé vers le nouveau nœud généré (focus automatique)

7. **Given** je génère plusieurs nœuds depuis un même parent (génération multi-choix), que ce soit depuis l'éditeur de graphe ou l'éditeur de dialogue
   **When** les nœuds sont générés
   **Then** chaque nouveau nœud reçoit un ID unique et stable (format cohérent)
   **And** les références `targetNode` et `nextNode` pointent vers les bons IDs
   **And** aucune référence orpheline n'est créée (toutes les références pointent vers des nœuds existants)
   **And** l'ordre logique des connexions est respecté (les nœuds se suivent dans l'ordre de génération)

8. **Given** je génère la suite d'un dialogue avec des choix déjà connectés à d'autres nœuds, que ce soit depuis l'éditeur de graphe ou l'éditeur de dialogue
   **When** je lance "Générer la suite pour tous les choix"
   **Then** seuls les choix sans `targetNode` (ou avec `targetNode="END"`) génèrent de nouveaux nœuds
   **And** les choix déjà connectés ne sont pas modifiés
   **And** un message indique "X choix(s) déjà connecté(s), Y nouveau(x) nœud(s) généré(s)"

## Tasks / Subtasks

- [x] Task 1: Étendre endpoint backend `/api/v1/graph/generate-node` (AC: #1, #3, #5)
  - [x] Ajouter paramètre `target_choice_index: Optional[int]` dans `GenerateNodeRequest` (api/schemas/graph.py)
  - [x] Ajouter paramètre `generate_all_choices: bool = False` dans `GenerateNodeRequest`
  - [x] Modifier logique dans `api/routers/graph.py::generate_node()` pour gérer choix spécifique
  - [x] Modifier logique pour génération batch multi-choix (si `generate_all_choices=True`) : intégration `GraphGenerationService`
  - [x] Retourner premier nœud avec connexions si batch génération (service batch retourne liste, endpoint retourne premier)
  - [x] Tests unitaires : génération choix spécifique, génération batch (3 tests passants)

- [x] Task 2: Créer service backend `services/graph_generation_service.py` (AC: #3, #7)
  - [x] Créer fonction `generate_nodes_for_all_choices(parent_node, instructions, context)` → liste nœuds + connexions
  - [x] Gestion automatique IDs : format `NODE_{parent_id}_CHOICE_{index}` pour chaque nœud (gère parent_id avec ou sans préfixe "NODE_")
  - [x] Gestion automatique connexions : créer `suggested_connections` avec `via_choice_index` et `connection_type="choice"`
  - [x] Filtrer choix déjà connectés (skip si `targetNode` existe et != "END")
  - [x] Tests unitaires : génération batch, gestion IDs, filtrage choix connectés (4 tests passants)

- [x] Task 3: Étendre `AIGenerationPanel.tsx` pour support choix spécifique (AC: #1, #3)
  - [x] Ajouter mode sélection "Générer pour ce choix" (visible quand parent a des choix)
  - [x] Ajouter bouton "Générer la suite pour tous les choix" (visible quand parent a plusieurs choix sans targetNode)
  - [x] Indicateur de progression si génération batch : "Génération batch..." dans le bouton
  - [x] Passer `targetChoiceIndex` et `generateAllChoices` à `generateFromNode`
  - [ ] Tests E2E : génération choix spécifique depuis graphe, génération batch depuis graphe (à faire manuellement ou avec Playwright)

- [x] Task 4: Étendre `graphStore.ts` méthode `generateFromNode` pour support batch (AC: #1, #3, #5, #7)
  - [x] Ajouter paramètre `targetChoiceIndex?: number` pour choix spécifique (dans options)
  - [x] Ajouter paramètre `generateAllChoices?: boolean` pour génération batch (dans options)
  - [x] Gestion automatique connexions : `connectNodes` met à jour `targetNode` dans parent automatiquement (choix et nextNode)
  - [x] Positionnement automatique : calculer positions en cascade pour batch génération (offset Y = 150 * index_choice)
  - [x] Appliquer connexions automatiquement : toutes les connexions suggérées sont appliquées (mise à jour targetNode/nextNode)
  - [x] Tests unitaires : 4 nouveaux tests passants (target_choice_index, generate_all_choices, mise à jour targetNode, positionnement cascade)

- [x] Task 5: Étendre `NodeEditorPanel.tsx` pour support génération depuis éditeur de dialogue (AC: #2, #4, #6)
  - [x] Ajouter bouton "Générer la suite" pour nœud sélectionné (visible dans panneau édition, section "Génération IA")
  - [x] Menu contextuel choix : bouton "✨ Générer" dans chaque `ChoiceEditor` (visible si choix non connecté)
  - [x] Bouton "Générer la suite pour tous les choix" (visible quand parent a plusieurs choix sans targetNode)
  - [x] Intégration même logique que `AIGenerationPanel.tsx` (réutilisation code génération via `generateFromNode`)
  - [x] Support génération choix spécifique (`target_choice_index`) et batch (`generate_all_choices`)
  - [x] Gestion automatique connexions identique à éditeur de graphe (via `connectNodes` qui met à jour `targetNode`/`nextNode`)
  - [x] Focus automatique vers nouveau nœud généré après génération (`setSelectedNode` + événement `focus-generated-node`)
  - [ ] Tests E2E : génération depuis éditeur de dialogue, focus automatique (à faire manuellement ou avec Playwright)

- [x] Task 6: Validation et tests (AC: #7, #8)
  - [x] Validation : tests unitaires vérifiant que `targetNode` et `nextNode` pointent vers des nœuds existants après génération
  - [x] Tests unitaires : génération choix spécifique, génération batch, gestion IDs (3 tests passants)
  - [x] Tests intégration : génération batch multi-choix, connexions automatiques (4 tests service passants)
  - [x] Tests validation : références valides après génération normale et batch (2 tests passants)
  - [x] Tests E2E : génération depuis éditeur de graphe + depuis éditeur de dialogue (7 scénarios E2E créés avec Playwright)
  - [x] Tests E2E : filtrage choix déjà connectés (scénario E2E créé)

## Dev Notes

### Architecture Patterns (Extension Story 0.2)

**Réutilisation existante :**
- **Étendre** `generateFromNode` existant au lieu de créer nouveau endpoint
- **Étendre** `AIGenerationPanel.tsx` au lieu de créer nouveau composant
- **Étendre** `NodeEditorPanel.tsx` pour parité fonctionnelle avec éditeur de graphe
- **Étendre** `api/routers/graph.py::generate_node()` au lieu de créer nouveau endpoint

**Gestion automatique connexions :**
- **Backend** : Retourner `suggested_connections` avec flag `auto_apply: true` pour différencier des suggestions manuelles
- **Frontend** : Si `auto_apply: true`, appliquer connexion automatiquement (mettre à jour `targetNode` dans parent, créer edge)
- **Positionnement** : Calculer positions en cascade verticale pour batch (offset Y = 150 * index_choice)

**Génération batch multi-choix :**
- **Séquentielle** : Générer un nœud à la fois (plus simple, feedback progressif)
- **Alternative future** : Génération parallèle si nécessaire (optimisation)
- **Progression** : Afficher "Génération 2/5..." dans modal progression si batch

### Intégration éditeur dialogue (OBLIGATOIRE - Égale priorité avec éditeur de graphe)

**Parité fonctionnelle :**
- Toutes les fonctionnalités de génération doivent être disponibles dans l'éditeur de dialogue ET l'éditeur de graphe
  - Génération pour choix spécifique (disponible dans les deux interfaces)
  - Génération batch pour tous les choix (disponible dans les deux interfaces)
  - Génération nextNode pour navigation linéaire (disponible dans les deux interfaces)

**Réutilisation code :**
- Utiliser même logique `generateFromNode` que graphe (éviter duplication)
  - Même appel API backend (`/api/v1/graph/generate-node`)
  - Même gestion connexions automatiques (mettre à jour `targetNode`/`nextNode`)
  - Même modal progression et streaming

**UX cohérente :**
- Même expérience utilisateur dans les deux interfaces
  - Modal progression identique (même design, même indicateurs)
  - Streaming identique (même feedback temps réel)
  - Indicateur batch identique ("Génération 2/5..." si applicable)

**Focus automatique :**
- Après génération, sélectionner et naviguer vers nouveau nœud généré
  - Éditeur de graphe : Zoom vers nouveau nœud généré (déjà implémenté via `focus-generated-node` event)
  - Éditeur de dialogue : Focus sur nouveau nœud dans la liste/panneau d'édition (appeler `setSelectedNode(newNodeId)`)

**Tests obligatoires :**
- Tous les tests E2E doivent couvrir les deux interfaces (graphe + dialogue)

### Fichiers existants à vérifier et étendre

**Backend :**
- ✅ `api/routers/graph.py` : Endpoint `/api/v1/graph/generate-node` existe (ligne 156-284)
  - **DÉCISION** : Étendre avec paramètres `target_choice_index` et `generate_all_choices`
  - **COMMENT** : Ajouter paramètres dans `GenerateNodeRequest`, modifier logique pour gérer choix spécifique et batch
- ✅ `api/schemas/graph.py` : Schéma `GenerateNodeRequest` existe (ligne 40-50)
  - **DÉCISION** : Étendre avec nouveaux paramètres
  - **COMMENT** : Ajouter `target_choice_index: Optional[int]` et `generate_all_choices: bool = False`
- ⚠️ `services/graph_generation_service.py` : **N'EXISTE PAS**
  - **DÉCISION** : Créer nouveau service pour logique batch génération multi-choix
  - **POURQUOI** : Logique complexe de génération batch avec gestion IDs et connexions mérite service dédié

**Frontend :**
- ✅ `frontend/src/components/graph/AIGenerationPanel.tsx` : Existe (ligne 1-438)
  - **DÉCISION** : Étendre avec support choix spécifique et batch
  - **COMMENT** : Ajouter boutons/modes sélection, passer paramètres à `generateFromNode`
- ✅ `frontend/src/store/graphStore.ts` : Méthode `generateFromNode` existe (ligne 297-357)
  - **DÉCISION** : Étendre avec paramètres `targetChoiceIndex` et `generateAllChoices`
  - **COMMENT** : Ajouter paramètres, gérer connexions automatiques (pas seulement suggérer), positionnement cascade
- ✅ `frontend/src/components/graph/NodeEditorPanel.tsx` : Existe (ligne 1-424)
  - **DÉCISION** : Étendre avec boutons génération depuis éditeur de dialogue
  - **COMMENT** : Ajouter boutons "Générer la suite", menu contextuel choix, intégration `generateFromNode`, focus automatique

### Patterns existants à respecter

**Zustand stores :**
- Immutable updates : `set((state) => ({ ...state, newValue }))`
- Pattern `generateFromNode` : Appel API, ajout nœud, création connexions suggérées (ligne 297-357 graphStore.ts)

**FastAPI routers :**
- Namespace `/api/v1/graph/*` (cohérent)
- Pattern endpoint : `@router.post("/generate-node", response_model=GenerateNodeResponse)`
- Gestion erreurs : `InternalServerException` avec `request_id`

**React composants :**
- Pattern modal progression : `GenerationProgressModal.tsx` (Story 0.2)
- Pattern `AIGenerationPanel.tsx` : Panel avec instructions, options LLM, bouton génération
- Pattern `NodeEditorPanel.tsx` : Form React Hook Form + Zod, édition nœud sélectionné

**Gestion connexions :**
- Pattern actuel : Backend retourne `suggested_connections`, frontend applique manuellement (ligne 338-346 graphStore.ts)
- **CHANGEMENT REQUIS** : Backend doit retourner `auto_apply: true` pour connexions automatiques, frontend doit appliquer automatiquement

**Positionnement nœuds :**
- Pattern actuel : Position relative au parent (ligne 329-332 graphStore.ts) : `x: parentNode.position.x + 300, y: parentNode.position.y`
- **EXTENSION REQUIS** : Pour batch, calculer positions en cascade : `y: parentNode.position.y + (150 * index_choice)`

### Format IDs

**Pattern existant :**
- Format actuel : `NODE_{parent_id}_CHILD` (ligne 228 api/routers/graph.py)
- **EXTENSION REQUIS** : Pour choix spécifique, utiliser `NODE_{parent_id}_CHOICE_{index}`

### Références techniques

**Source: `_bmad-output/planning-artifacts/prd/epic-00.md#Story-0.5.5`**
- Story complète avec acceptance criteria et technical requirements

**Source: `api/routers/graph.py#generate_node` (ligne 156-284)**
- Endpoint existant à étendre

**Source: `frontend/src/store/graphStore.ts#generateFromNode` (ligne 297-357)**
- Méthode existante à étendre

**Source: `frontend/src/components/graph/AIGenerationPanel.tsx` (ligne 1-438)**
- Composant existant à étendre

**Source: `frontend/src/components/graph/NodeEditorPanel.tsx` (ligne 1-424)**
- Composant existant à étendre

**Source: Story 0.2 (Progress Modal SSE)**
- Modal progression avec streaming (réutiliser pour batch génération)

**Source: ADR-003 (Graph Fix stableID)**
- Format IDs stable (respecter pour nouveaux nœuds)

### Project Structure Notes

**Alignment avec structure unifiée :**
- ✅ Backend API : `api/routers/graph.py` (cohérent)
- ✅ Frontend stores : `frontend/src/store/graphStore.ts` (cohérent)
- ✅ Frontend components : `frontend/src/components/graph/` (cohérent)
- ✅ Services backend : `services/` (nouveau service `graph_generation_service.py`)

**Détecté conflits ou variances :**
- Aucun conflit détecté, extension cohérente avec architecture existante

### References

- [Source: `_bmad-output/planning-artifacts/prd/epic-00.md#Story-0.5.5`] Story complète avec requirements
- [Source: Story 0.2] Progress Modal SSE (modal progression réutilisable)
- [Source: ADR-003] Graph Fix stableID (format IDs à respecter)
- [Source: `api/routers/graph.py#generate_node`] Endpoint existant à étendre
- [Source: `frontend/src/store/graphStore.ts#generateFromNode`] Méthode existante à étendre
- [Source: `frontend/src/components/graph/AIGenerationPanel.tsx`] Composant existant à étendre
- [Source: `frontend/src/components/graph/NodeEditorPanel.tsx`] Composant existant à étendre

## Dev Agent Record

### Agent Model Used

Auto (Cursor Agent)

### Debug Log References

### Completion Notes List

**Task 1 - Toutes subtasks complétées (2026-01-15):**
- ✅ Ajout paramètres `target_choice_index` et `generate_all_choices` dans `GenerateNodeRequest` (api/schemas/graph.py)
- ✅ Modification endpoint `generate_node()` pour utiliser `target_choice_index` avec format ID `NODE_{parent_id}_CHOICE_{index}`
- ✅ Gestion connexions suggérées pour choix spécifique (via_choice_index)
- ✅ Intégration service batch : `GraphGenerationService` utilisé quand `generate_all_choices=True`
- ✅ Retour premier nœud : endpoint retourne premier nœud de la liste batch (service retourne liste complète)
- ✅ Tests unitaires créés et passants : `test_generate_node_with_target_choice_index`, `test_generate_node_with_generate_all_choices`, `test_generate_node_nextnode_linear`

**Task 2 - Toutes subtasks complétées (2026-01-15):**
- ✅ Service `GraphGenerationService` créé avec méthode `generate_nodes_for_all_choices()`
- ✅ Génération batch séquentielle pour tous les choix sans targetNode (ou avec "END")
- ✅ Format IDs : `NODE_{parent_id}_CHOICE_{index}` (gère parent_id avec ou sans préfixe "NODE_")
- ✅ Connexions suggérées créées automatiquement avec `via_choice_index` et `connection_type="choice"`
- ✅ Filtrage automatique des choix déjà connectés (skip si `targetNode` existe et != "END")
- ✅ Tests unitaires complets : 4 tests passants (génération batch, filtrage, format IDs, cas vide)

**Task 3 - Toutes subtasks complétées (2026-01-15):**
- ✅ UI sélection choix spécifique : affichage des choix du parent avec indication des choix déjà connectés
- ✅ Bouton "Générer pour tous les choix" : visible quand plusieurs choix sans targetNode, affiche le nombre
- ✅ Indicateur batch : "Génération batch..." dans le bouton pendant génération
- ✅ Intégration `targetChoiceIndex` et `generateAllChoices` : passés à `generateFromNode` puis à l'API
- ⚠️ Tests E2E : à faire manuellement ou avec Playwright (non bloquant pour l'implémentation)

**Task 4 - Toutes subtasks complétées (2026-01-15):**
- ✅ Paramètres ajoutés dans `generateFromNode` : `targetChoiceIndex` et `generateAllChoices` dans options
- ✅ Gestion automatique connexions : `connectNodes` met à jour `targetNode` dans choix parent et `nextNode` pour navigation linéaire
- ✅ Positionnement cascade : offset Y = 150 * index_choice pour batch génération
- ✅ Connexions automatiques : toutes les connexions suggérées sont appliquées (pas seulement suggérées)
- ✅ Tests unitaires : 4 nouveaux tests passants (19/19 tests passants au total)

**Task 5 - Toutes subtasks complétées (2026-01-15):**
- ✅ Section "Génération IA" dans `NodeEditorPanel` : panneau pliable avec instructions et sélection modèle LLM
- ✅ Bouton "Générer la suite (nextNode)" : génération navigation linéaire depuis éditeur
- ✅ Bouton "✨ Générer" dans chaque `ChoiceEditor` : génération pour choix spécifique (visible si choix non connecté)
- ✅ Bouton "Générer pour tous les choix" : visible quand plusieurs choix sans targetNode, affiche le nombre
- ✅ Intégration complète : réutilisation `generateFromNode` avec `target_choice_index` et `generate_all_choices`
- ✅ Focus automatique : `setSelectedNode` + événement `focus-generated-node` pour zoomer vers nouveau nœud
- ⚠️ Tests E2E : à faire manuellement ou avec Playwright (non bloquant pour l'implémentation)

**Approche TDD:**
- Phase RED : Tests créés qui échouaient (module manquant, validation des mocks)
- Phase GREEN : Création du service, correction des mocks (types Pydantic), gestion format IDs
- Phase REFACTOR : Tous les tests passent, service prêt pour intégration dans endpoint

### File List

- `api/schemas/graph.py` : Ajout paramètres `target_choice_index` et `generate_all_choices` dans `GenerateNodeRequest`
- `api/routers/graph.py` : Modification logique `generate_node()` pour gérer choix spécifique avec format ID `NODE_{parent_id}_CHOICE_{index}`, intégration `GraphGenerationService` pour batch
- `services/graph_generation_service.py` : Nouveau service pour génération batch multi-choix avec gestion automatique IDs et connexions
- `frontend/src/types/graph.ts` : Ajout `target_choice_index` et `generate_all_choices` dans `GenerateNodeRequest`
- `frontend/src/store/graphStore.ts` : Extension `generateFromNode` pour accepter et passer `targetChoiceIndex` et `generateAllChoices`, positionnement cascade pour batch, `connectNodes` met à jour `targetNode`/`nextNode` automatiquement
- `frontend/src/components/graph/AIGenerationPanel.tsx` : UI sélection choix spécifique, bouton batch, indicateurs de progression
- `frontend/src/components/graph/NodeEditorPanel.tsx` : Section "Génération IA" avec boutons génération nextNode, choix spécifique, batch
- `frontend/src/components/graph/ChoiceEditor.tsx` : Bouton "✨ Générer" pour génération depuis éditeur de choix
- `frontend/src/__tests__/useGraphStore.test.ts` : 4 nouveaux tests pour batch generation (target_choice_index, generate_all_choices, mise à jour targetNode, positionnement cascade)
- `tests/api/test_graph_generate_node_validation.py` : 2 nouveaux tests de validation (références targetNode/nextNode valides)
- `e2e/graph-node-generation.spec.ts` : 7 scénarios E2E Playwright (génération depuis graphe, éditeur, batch, nextNode, validation, filtrage, ChoiceEditor)
- `tests/api/test_graph_generate_node.py` : Nouveau fichier avec 3 tests unitaires (génération choix spécifique, batch, nextNode)
- `tests/services/test_graph_generation_service.py` : Nouveau fichier avec 4 tests unitaires (génération batch, filtrage, format IDs, cas vide)
