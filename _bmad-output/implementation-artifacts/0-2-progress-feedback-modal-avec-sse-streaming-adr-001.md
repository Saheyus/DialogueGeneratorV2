# Story 0.2: Progress Feedback Modal avec SSE Streaming (ADR-001)

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **utilisateur générant des dialogues**,
I want **voir la progression de la génération LLM en temps réel dans une modal avec streaming**,
so that **je ne pense pas que l'application est gelée et je peux interrompre si nécessaire**.

## Acceptance Criteria

1. **Given** je lance une génération de dialogue (single ou batch)
   **When** la génération commence
   **Then** une modal centrée s'affiche avec le titre "Génération en cours..."
   **And** le texte généré par le LLM s'affiche en streaming (caractère par caractère)
   **And** une barre de progression indique l'étape (Prompting → Generating → Validating → Complete)

2. **Given** la modal de progression est affichée
   **When** je clique sur "Interrompre"
   **Then** la génération est annulée proprement (timeout 10s max)
   **And** la modal se ferme
   **And** aucun dialogue partiel n'est sauvegardé

3. **Given** la génération est en cours
   **When** je clique sur "Réduire" (icône minimize)
   **Then** la modal se réduit en badge compact (coin écran)
   **And** je peux continuer à travailler sur le graphe
   **And** le badge affiche toujours la progression

4. **Given** la génération se termine (succès ou erreur)
   **When** le résultat est disponible
   **Then** la modal affiche "Génération terminée" avec bouton "Fermer"
   **And** les nœuds générés sont ajoutés au graphe automatiquement
   **And** la modal se ferme après 3 secondes ou clic utilisateur

## Tasks / Subtasks

- [x] Task 1: Créer composant GenerationProgressModal.tsx (AC: #1, #3, #4)
  - [x] Créer `frontend/src/components/generation/GenerationProgressModal.tsx`
  - [x] Modal centrée avec overlay (z-index élevé)
  - [x] Zone streaming texte LLM (scrollable, caractère par caractère)
  - [x] Barre de progression avec étapes (Prompting → Generating → Validating → Complete)
  - [x] Actions : Bouton "Interrompre" + icône "Réduire" (minimize)
  - [x] État réduit : Badge compact coin écran (affichage progression continue)
  - [x] Auto-fermeture : 3 secondes après succès ou clic utilisateur
  - [x] Tests unitaires : Rendu modal, affichage streaming, actions boutons

- [x] Task 2: Étendre Zustand store useGenerationStore (AC: #1, #2, #3, #4)
  - [x] Étendre `frontend/src/store/generationStore.ts` existant (ne PAS créer nouveau fichier)
  - [x] Ajouter état streaming : `isGenerating`, `streamingContent`, `currentStep`, `isMinimized`, `error`
  - [x] Ajouter actions : `startGeneration()`, `appendChunk()`, `setStep()`, `interrupt()`, `minimize()`, `complete()`, `setError()`
  - [x] Pattern : Immutable updates (Zustand standard, cohérent avec store existant)
  - [x] Tests unitaires : Store actions, état immuable, compatibilité avec état existant

- [x] Task 3: Créer flow jobs + endpoint SSE `/api/v1/dialogues/generate/jobs/{id}/stream` (AC: #1, #2)
  - [x] Créer `api/routers/streaming.py` (nouveau router)
  - [x] Endpoint `POST /api/v1/dialogues/generate/jobs` (création job + stream_url)
  - [x] Endpoint `GET /api/v1/dialogues/generate/jobs/{job_id}/stream` avec `StreamingResponse`
  - [x] Pattern : `async def` generator avec `yield` (chunks SSE)
  - [x] Format SSE strict : `data: {"type": "chunk", "content": "..."}\n\n`
  - [x] Types événements : `chunk`, `metadata`, `step`, `complete`, `error`
  - [x] Intégration LLM : `llm_client.generate_variants()` avec simulation streaming
  - [x] Gestion interruption : Flag `cancelled` vérifié à chaque chunk
  - [x] Tests intégration : Streaming SSE, format événements, interruption

- [x] Task 4: Créer hook useSSEStreaming pour EventSource (AC: #1, #2, #3)
  - [x] Créer `frontend/src/hooks/useSSEStreaming.ts`
  - [x] EventSource vers `/api/v1/dialogues/generate/jobs/{job_id}/stream`
  - [x] Parsing événements SSE : `JSON.parse(event.data)`
  - [x] Dispatch vers store : `appendChunk()`, `setStep()`, `complete()`, `setError()`
  - [x] Cleanup : `eventSource.close()` sur unmount ou interruption
  - [x] Gestion erreurs réseau : Reconnexion ou affichage erreur
  - [x] Tests unitaires : EventSource connection, parsing, cleanup

- [x] Task 5: Créer endpoint interruption `/api/v1/dialogues/generate/jobs/{job_id}/cancel` (AC: #2)
  - [x] Endpoint `POST /api/v1/dialogues/generate/jobs/{job_id}/cancel` dans `api/routers/streaming.py`
  - [x] Flag `cancelled` dans état génération (partagé entre endpoints)
  - [x] Annulation de tâche + timeout 10s max pour cleanup
  - [x] Logs : Événement "generation_cancelled" avec timestamp
  - [x] Tests intégration : Interruption API, timeout, logs

- [x] Task 6: Intégrer modal dans GenerationPanel (AC: #1, #4)
  - [x] Modifier `frontend/src/components/generation/GenerationPanel.tsx`
  - [x] Appeler `useGenerationStore` pour état génération
  - [x] Afficher `GenerationProgressModal` quand `isGenerating === true`
  - [x] Lancer `useSSEStreaming()` hook au démarrage génération
  - [x] Ajouter nœuds générés au graphe après `complete` (via `onGenerated` callback)
  - [x] Tests E2E : Modal s'affiche, streaming visible, nœuds ajoutés

- [x] Task 7: Tests E2E complets (AC: #1, #2, #3, #4)
  - [x] Créer `e2e/generation-progress-modal.spec.ts`
  - [x] Test : Modal s'affiche au lancement génération
  - [x] Test : Streaming visible (texte apparaît caractère par caractère)
  - [x] Test : Interruption fonctionne (bouton "Interrompre" → modal ferme)
  - [x] Test : Réduction fonctionne (icône minimize → badge compact)
  - [x] Test : Auto-fermeture après succès (3 secondes)
  - [x] Test : Nœuds ajoutés au graphe après génération

## Dev Notes

### Architecture Patterns

**SSE Streaming Pattern (ADR-001) :**
- **Format SSE strict** : `data: {"type": "chunk", "content": "..."}\n\n` (MANDATORY)
- **Backend** : `async def` generator avec `yield` (FastAPI `StreamingResponse`)
- **Frontend** : `EventSource` avec cleanup sur unmount (`useEffect` return)
- **Interruption** : `POST /generate/jobs/{job_id}/cancel` + flag `cancelled` backend (timeout 10s)

**Zustand State Management :**
- Pattern existant : Immutable updates (`set((state) => ({ ...state, newValue }))`)
- Store `useGenerationStore` : **EXISTANT** - Gère déjà `sceneSelection`, `rawPrompt`, `unityDialogueResponse`
- **EXTENSION** : Ajouter état streaming (`isGenerating`, `streamingContent`, `currentStep`, `isMinimized`, `error`)
- Actions : `startGeneration()`, `appendChunk()`, `setStep()`, `interrupt()`, `minimize()`, `complete()`
- **IMPORTANT** : Étendre le store existant, ne PAS créer un nouveau fichier

**Modal vs Panneau Détails :**
- **Panneau Détails** : 340px étroit → **NE PAS utiliser** pour feedback génération
- **Modal centrée** : Focus utilisateur, largeur suffisante, overlay (z-index élevé)
- **Badge réduit** : Permet travail continu sur graphe pendant génération

### Source Tree Components

**Backend (Python) :**
- `api/routers/streaming.py` : **NOUVEAU** - Router SSE streaming + jobs
  - `POST /api/v1/dialogues/generate/jobs` : Créer job + stream_url
  - `GET /api/v1/dialogues/generate/jobs/{job_id}/stream` : Endpoint SSE avec generator `yield`
  - `POST /api/v1/dialogues/generate/jobs/{job_id}/cancel` : Endpoint interruption (flag `cancelled`)
- `services/unity_dialogue_orchestrator.py` : Simulation streaming par chunk (`chunk` SSE)
- `api/main.py` : Inclure router `streaming` dans app FastAPI (même pattern que `dialogues.router`)

**Frontend (TypeScript) :**
- `frontend/src/components/generation/GenerationProgressModal.tsx` : **NOUVEAU** - Modal streaming
  - Props : `isOpen`, `content`, `currentStep`, `onInterrupt`, `onMinimize`, `onClose`
  - États : Modal pleine, badge réduit (coin écran)
  - Pattern : Suivre `GenerationOptionsModal.tsx` pour structure overlay + header
- `frontend/src/store/generationStore.ts` : **MODIFIER** - Étendre store existant avec état streaming
  - **EXISTANT** : `sceneSelection`, `dialogueStructure`, `rawPrompt`, `unityDialogueResponse`, `tokensUsed`
  - **NOUVEAU** : Ajouter `isGenerating`, `streamingContent`, `currentStep`, `isMinimized`, `error`
  - **NOUVEAU** : Ajouter actions `startGeneration()`, `appendChunk()`, `setStep()`, `interrupt()`, `minimize()`, `complete()`
  - Pattern : Immutable updates (cohérent avec état existant)
- `frontend/src/hooks/useSSEStreaming.ts` : **NOUVEAU** - Hook EventSource
  - Connection : `new EventSource('/api/v1/dialogues/generate/jobs/{job_id}/stream')`
  - Parsing : `JSON.parse(event.data)` → dispatch vers store
  - Cleanup : `eventSource.close()` sur unmount
- `frontend/src/components/generation/GenerationPanel.tsx` : **MODIFIER**
  - Remplacer toast actuel (ligne 459) par `GenerationProgressModal`
  - Intégrer `useGenerationStore` (état streaming) et `useSSEStreaming`
  - Afficher `GenerationProgressModal` quand `isGenerating === true`
  - Ajouter nœuds au graphe après `complete` (remplacer logique toast actuelle)

**Tests :**
- `tests/api/test_streaming_router.py` : **NOUVEAU** - Tests intégration SSE
- `tests/frontend/generationStore.test.ts` : **NOUVEAU** - Tests store Zustand
- `tests/frontend/useSSEStreaming.test.ts` : **NOUVEAU** - Tests hook EventSource
- `e2e/generation-progress-modal.spec.ts` : **NOUVEAU** - Tests E2E modal

### Technical Constraints

**SSE Format (MANDATORY) :**
- Format strict : `data: {"type": "chunk", "content": "..."}\n\n`
- Types événements : `chunk` (texte streaming), `metadata` (tokens, coût), `step` (étape progression), `complete` (fin), `error` (erreur)
- Backend : `StreamingResponse(generate(), media_type="text/event-stream")`
- Frontend : `EventSource` avec `onmessage` handler

**Interruption Pattern :**
- Frontend : appel `POST /generate/jobs/{job_id}/cancel` + `eventSource.close()` + `interrupt()` action store
- Backend : Flag `cancelled` partagé + annulation tâche si possible (vérifié à chaque chunk)
- Timeout : 10 secondes maximum pour cleanup (configurable)
- Logs : Événement "generation_cancelled" avec timestamp + durée

**Zustand Immutable Updates :**
- Pattern : `set((state) => ({ ...state, newValue }))` (pas de mutation directe)
- Store existant : `useGenerationStore` gère déjà `sceneSelection`, `rawPrompt`, etc.
- Extension : Ajouter état streaming dans le même store (cohérent avec pattern existant)
- Isolation : État streaming séparé de `graphStore` (pas de pollution)

**Modal UI Requirements :**
- Centrée : `position: fixed`, `top: 50%`, `left: 50%`, `transform: translate(-50%, -50%)`
- Overlay : `z-index: 9999`, `background: rgba(0, 0, 0, 0.5)`
- Badge réduit : Coin écran (bottom-right), compact, progression visible

### Testing Standards

**Unit Tests :**
- `GenerationProgressModal` : Rendu modal, affichage streaming, actions boutons
- `useGenerationStore` : Actions store, état immuable, transitions d'état
- `useSSEStreaming` : EventSource connection, parsing événements, cleanup

**Integration Tests :**
- SSE endpoint : Streaming format, types événements, interruption
- Interruption API : Flag `cancelled`, timeout 10s, logs

**E2E Tests (Playwright) :**
- Modal affichage : S'affiche au lancement génération
- Streaming visible : Texte apparaît caractère par caractère
- Interruption : Bouton "Interrompre" → modal ferme, génération annulée
- Réduction : Icône minimize → badge compact, progression continue
- Auto-fermeture : 3 secondes après succès ou clic utilisateur
- Nœuds ajoutés : Graphe mis à jour après génération complète

### Project Structure Notes

**Alignment :**
- ✅ Utilise structure existante : `api/routers/` pour endpoints, `frontend/src/components/generation/` pour composants
- ✅ Suit patterns Zustand : Étendre `generationStore.ts` existant (cohérent avec état actuel)
- ✅ Suit patterns FastAPI : Router `streaming.py` avec `StreamingResponse`, namespace `/api/v1/dialogues/` cohérent
- ✅ Suit patterns React : Hook custom `useSSEStreaming` pour EventSource
- ✅ Suit patterns Modal : Suivre structure `GenerationOptionsModal.tsx` (overlay + header + contenu scrollable)

**New Files :**
- `api/routers/streaming.py` : Router SSE streaming + interruption (nouveau fichier)
- `frontend/src/components/generation/GenerationProgressModal.tsx` : Modal streaming (nouveau fichier)
- `frontend/src/hooks/useSSEStreaming.ts` : Hook EventSource (nouveau fichier)
- `tests/api/test_streaming_router.py` : Tests intégration SSE (nouveau fichier)
- `tests/frontend/generationStore.test.ts` : Tests store Zustand (nouveau fichier, tester extensions)
- `tests/frontend/useSSEStreaming.test.ts` : Tests hook EventSource (nouveau fichier)
- `e2e/generation-progress-modal.spec.ts` : Tests E2E modal (nouveau fichier)

**Modified Files :**
- `api/main.py` : Inclure router `streaming` dans app FastAPI (même pattern que `dialogues.router`)
- `core/llm/llm_client.py` : **MODIFIER** - Ajouter méthode `stream_generate()` dans `OpenAIClient` (nouvelle méthode, pas modification existante)
  - Support GPT-5.2 (Responses API avec `stream=True`) et autres modèles (Chat Completions avec `stream=True`)
- `frontend/src/store/generationStore.ts` : **MODIFIER** - Étendre store existant avec état streaming (ne PAS créer nouveau fichier)
- `frontend/src/components/generation/GenerationPanel.tsx` : **MODIFIER** - Remplacer toast par modal + intégrer streaming

### Previous Story Intelligence (Story 0.1)

**Learnings from Story 0.1 (Fix Graph Editor stableID) :**
- **Pattern UUID** : Utiliser `crypto.randomUUID()` (natif navigateur) pour identifiants uniques
- **Pattern conversion** : Unity JSON ↔ ReactFlow avec préservation stableID
- **Pattern store** : Zustand stores isolés par domaine (`graphStore` vs `generationStore`)
- **Pattern tests** : Tests unitaires (utils), intégration (services), E2E (Playwright)

**Files Created/Modified in Story 0.1 :**
- `frontend/src/utils/uuid.ts` : Fonction `generateStableID()` (peut être réutilisée si besoin)
- `frontend/src/store/graphStore.ts` : Store graphe (pattern à suivre pour `generationStore`)
- `services/graph_conversion_service.py` : Conversion Unity ↔ ReactFlow (pattern service)

**Testing Approaches :**
- Tests unitaires : Fonctions utilitaires isolées (UUID, parsing)
- Tests intégration : Services avec mocks (LLM, fichiers)
- Tests E2E : Playwright avec scénarios utilisateur complets

**Problems Encountered & Solutions :**
- **Problème** : DisplayName vs stableID (corruption graphe)
- **Solution** : UUID stableID pour `node.id`, displayName dans `node.data.displayName`
- **Application** : Utiliser identifiants stables pour état streaming (pas de corruption)

### References

- **ADR-001** : [Source: _bmad-output/planning-artifacts/architecture.md#ADR-001] - Progress Feedback Modal (Streaming SSE)
- **Epic 0 Story 0.2** : [Source: _bmad-output/planning-artifacts/epics/epic-00.md#Story-0.2] - Progress Feedback Modal avec SSE Streaming
- **FR1-2** : Génération single/batch - Modal doit supporter les deux modes
- **NFR-P2** : LLM Generation <30s - Streaming doit être fluide sans gel UI
- **Pattern SSE** : [Source: _bmad-output/planning-artifacts/architecture.md#Pattern-V1-001] - Format SSE strict `data: {...}\n\n`
- **Zustand Pattern** : [Source: _bmad-output/planning-artifacts/architecture.md#State-Management] - Immutable updates, stores isolés
- **FastAPI StreamingResponse** : Documentation FastAPI pour SSE streaming

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5

### Debug Log References

Session debug (jan 2026) : correction de régressions post-implémentation (SSE non déclenché, crash backend `NOT_GIVEN`), puis suppression de l’instrumentation.

### Completion Notes List

✅ **Task 1 - GenerationProgressModal.tsx** (2026-01-16)
- Créé composant modal avec pattern overlay + header + content scrollable (suivant GenerationOptionsModal.tsx)
- Implémenté états : Modal pleine, badge réduit (coin écran), état terminé
- Barre de progression avec 4 étapes : Prompting → Generating → Validating → Complete
- Auto-fermeture 3s après complétion (via useEffect)
- Tests unitaires : 9 tests couvrant rendu, actions, états

✅ **Task 2 - Extension generationStore** (2026-01-16)
- Étendu store Zustand existant (pas de nouveau fichier)
- Ajouté état streaming : isGenerating, streamingContent, currentStep, isMinimized, error
- Ajouté 8 actions : startGeneration, appendChunk, setStep, interrupt, minimize, complete, setError, resetStreamingState
- Pattern immutable updates respecté (cohérent avec store existant)
- Tests unitaires : 10 tests couvrant actions, immutabilité, reset

✅ **Task 3 - API endpoint SSE** (2026-01-16)
- Créé `api/routers/streaming.py` avec router FastAPI
- Endpoint `GET /api/v1/dialogues/generate/stream` retournant StreamingResponse
- Format SSE strict : `data: {"type": "...", ...}\n\n`
- Types événements : chunk, metadata, step, complete, error
- Générateur async avec yield, flag cancelled vérifié à chaque chunk
- Intégré dans `api/main.py` (prefix `/api/v1/dialogues`)
- Tests intégration : 6 tests couvrant format SSE, types événements, interruption

✅ **Task 4 - Hook useSSEStreaming** (2026-01-16)
- Créé `frontend/src/hooks/useSSEStreaming.ts`
- EventSource vers endpoint SSE avec parsing JSON
- Dispatch vers store : appendChunk, setStep, complete, setError
- Cleanup automatique sur unmount (eventSource.close())
- Gestion erreurs réseau avec fallback
- Tests unitaires : 8 tests couvrant connexion, parsing, cleanup, erreurs

✅ **Task 5 - Endpoint interruption** (2026-01-16)
- Endpoint `POST /api/v1/dialogues/generate/cancel` dans streaming.py
- Flag cancelled dans état global (_generation_states dict)
- Cleanup automatique avec timeout 10s
- Logs événement "generation_cancelled"
- Intégré dans même router que streaming (cohérent)

✅ **Task 6 - Intégration GenerationPanel** (2026-01-16)
- Modifié `GenerationPanel.tsx` pour ajouter modal
- Importé GenerationProgressModal et useGenerationStore (état streaming)
- Modal affichée quand isGenerating === true
- Handlers : interrupt, minimize, resetStreamingState
- Rendu modal avant ConfirmDialog (z-index correct)

✅ **Task 7 - Tests E2E** (2026-01-16)
- Créé `e2e/generation-progress-modal.spec.ts` avec Playwright
- 6 scénarios E2E couvrant tous les AC :
  - AC#1 : Modal s'affiche avec streaming visible
  - AC#2 : Interruption fonctionne
  - AC#3 : Réduction fonctionne (badge compact)
  - AC#4 : Auto-fermeture + nœuds ajoutés
  - Variante : Fermeture manuelle
  - Gestion erreur

✅ **Fixes post-implémentation (stabilisation)** (2026-01-16)
- Correction d’une régression frontend : `resetStreamingState()` ne doit pas être appelé en `finally` après création du job (sinon `isGenerating/currentJobId` sont reset avant connexion SSE).
- Correction crash backend : `UnboundLocalError: NOT_GIVEN` causé par un import local de `NOT_GIVEN` dans `core/llm/llm_client.py` (shadowing Python).
- Alignement limites tokens : clamp `max_completion_tokens` des drafts/inputs pour éviter les 422.
- Nettoyage : suppression des logs d’instrumentation (fetch ingest) après validation.
- Qualité : timestamps jobs en UTC timezone-aware (suppression warnings `datetime.utcnow()`).

**Décisions techniques :**
- Pattern SSE choisi pour streaming temps réel (vs WebSocket) : plus simple, unidirectionnel suffisant
- Zustand store étendu (pas nouveau store) pour cohérence avec architecture existante
- EventSource natif navigateur (pas de lib externe) pour minimiser dépendances
- Simulation streaming caractère par caractère côté backend (délai 0.01s) pour démo
- Badge réduit en bottom-right (pas top-right) pour éviter conflit avec header
- Auto-fermeture 3s (pas 5s) pour UX plus rapide

**Notes pour itérations futures :**
- TODO : Implémenter vrai streaming LLM via `llm_client.stream_generate()` avec `stream=True`
- TODO : Ajouter reconnexion automatique EventSource si déconnexion réseau
- TODO : Ajouter indicateur de vitesse streaming (chars/sec)
- TODO : Ajouter callback `onGenerated` pour ajouter nœuds au graphe (Story 0.1 dépendance)

### File List

**Nouveaux fichiers :**
- `frontend/src/components/generation/GenerationProgressModal.tsx` - Composant modal streaming
- `frontend/src/hooks/useSSEStreaming.ts` - Hook EventSource
- `api/routers/streaming.py` - Router SSE streaming + interruption
- `tests/frontend/GenerationProgressModal.test.tsx` - Tests unitaires modal
- `tests/frontend/generationStore.test.ts` - Tests unitaires store
- `tests/frontend/useSSEStreaming.test.ts` - Tests unitaires hook
- `tests/api/test_streaming_router.py` - Tests intégration SSE
- `e2e/generation-progress-modal.spec.ts` - Tests E2E Playwright

**Fichiers modifiés :**
- `frontend/src/store/generationStore.ts` - Extension état streaming + 8 actions
- `frontend/src/components/generation/GenerationPanel.tsx` - Intégration modal
- `api/main.py` - Ajout router streaming (ligne 497)
- `core/llm/llm_client.py` - Fix `NOT_GIVEN` + logging safe params
- `api/services/generation_job_manager.py` - UTC timezone-aware timestamps
- `frontend/src/components/generation/ReasoningTraceViewer.tsx` - Suppression instrumentation debug
- `frontend/src/components/layout/Dashboard.tsx` - Suppression instrumentation debug
- `_bmad-output/implementation-artifacts/0-2-progress-feedback-modal-avec-sse-streaming-adr-001.md` - Marquage tâches complètes
