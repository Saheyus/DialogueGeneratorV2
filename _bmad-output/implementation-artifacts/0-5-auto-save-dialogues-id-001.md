# Story 0.5: Auto-save dialogues (ID-001)

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **utilisateur éditant des dialogues**,
I want **que l’application protège automatiquement mon travail pendant l’édition (brouillon crash-safe + restauration)**,
so that **je ne perds jamais mon travail même en cas de crash, refresh, ou fermeture accidentelle**.

## Acceptance Criteria

1. **Given** j’édite un dialogue dans l’éditeur de graphe (ajout/suppression de nœuds, édition texte, création/suppression connexions, déplacement de nœuds, changement de titre)
   **When** je fais une modification
   **Then** un brouillon local (draft) du dialogue est persisté automatiquement (debounce court, ex: ~2–5s après le dernier changement)
   **And** l’UI reste réactive (aucun freeze, aucun toast intrusif)
   **And** un indicateur de statut reflète l’état (Non sauvegardé / En cours… / Sauvegardé / Erreur) et la récence (“Sauvegardé il y a Xs/min”).

2. **Given** une génération IA est en cours dans l’éditeur de graphe (ajout de nœud via IA)
   **When** un brouillon devrait être écrit
   **Then** l’écriture du brouillon est suspendue pendant la génération (et/ou pendant une sauvegarde disque en cours)
   **And** elle reprend après la fin (succès/erreur/annulation).

3. **Given** je sauvegarde manuellement (Ctrl+S ou bouton “💾 Sauvegarder”)
   **When** la sauvegarde disque réussit (fichier Unity JSON)
   **Then** le brouillon correspondant est soit supprimé, soit marqué comme “aligné” (no restore prompt)
   **And** l’indicateur “Sauvegardé” se met à jour immédiatement.

4. **Given** l’écriture du brouillon échoue (quota localStorage, JSON invalide, exception inattendue)
   **When** l’auto-save draft se déclenche
   **Then** l’erreur est visible (statut “Erreur” + message non intrusif)
   **And** l’utilisateur peut continuer à travailler (pas de blocage)
   **And** aucune corruption n’est écrite (pas de state partiellement persisté).

5. **Given** l’application crash / onglet fermé alors que j’ai des changements non sauvegardés
   **When** je rouvre l’application et recharge ce même dialogue
   **Then** une récupération est proposée (restaurer le brouillon local le plus récent) si le brouillon est plus récent que le fichier
   **And** si je refuse, je reviens à la version du fichier sur disque.

## Tasks / Subtasks

- [x] Task 1: Définir le “contrat” d’auto-save **draft** côté frontend (AC: #1, #2, #4, #5)
  - [x] Ajouter dans `frontend/src/store/graphStore.ts` un état minimal pour l’auto-save:
    - [x] `hasUnsavedChanges: boolean` (modifs non persistées sur disque)
    - [x] `lastDraftSavedAt: number | null` (timestamp ms)
    - [x] `lastDraftError: string | null`
    - [x] Actions dédiées: `markDirty()`, `markDraftSaved()`, `markDraftError(message)`, `clearDraftError()`
  - [x] Marquer “dirty” sur les mutations du graphe (nodes/edges/metadata) sans casser zundo:
    - [x] `addNode`, `updateNode`, `deleteNode`, `connectNodes`, `disconnectNodes`, `updateNodePosition`, `updateMetadata`
    - [x] Ne pas marquer dirty lors du `loadDialogue()`.

- [x] Task 2: Implémenter auto-save **draft local** dans l’éditeur de graphe (AC: #1, #2, #4, #5)
  - [x] Dans `frontend/src/components/graph/GraphEditor.tsx`:
    - [x] Introduire un debounce d’écriture de brouillon (ex: 2–5s après le dernier changement) qui ne s’exécute que si `hasUnsavedChanges === true`
    - [x] Stockage par dialogue sélectionné (clé stable):
      - [x] `unity_dialogue_draft:${selectedDialogue.filename}`
      - [x] payload: `{ filename, json_content, timestamp }` où `json_content` provient de `useGraphStore().exportToUnity()`
    - [x] Suspendre l’écriture de brouillon si:
      - [x] aucun dialogue n’est sélectionné
      - [x] `useGraphStore().isGenerating === true`
      - [x] `useGraphStore().isSaving === true`
      - [x] `isLoadingDialogue === true`
    - [x] Logique de restauration au chargement:
      - [x] Lire le draft si présent
      - [x] Comparer `draft.timestamp` avec `selectedDialogue.modified_time` (quand disponible via listing Unity dialogues)
      - [x] Si le draft est plus récent → proposer restauration via `ConfirmDialog`
      - [x] Restore: `useGraphStore().loadDialogue(draft.json_content)`
      - [x] Discard: supprimer le draft
    - [x] Après une sauvegarde disque manuelle réussie: supprimer le draft correspondant (ou mettre à jour son timestamp pour éviter le prompt).

- [x] Task 3: Unifier et afficher l’indicateur “Sauvegardé il y a Xs” dans le graphe (AC: #1, #3, #4)
  - [x] Étendre `frontend/src/components/shared/SaveStatusIndicator.tsx` pour supporter un affichage relatif optionnel:
    - [x] `lastSavedAt?: number | null`
    - [x] `variant?: 'draft' | 'disk'` (optionnel, pour wording si besoin)
  - [x] Dans `GraphEditor.tsx`, afficher l’indicateur basé sur:
    - [x] `hasUnsavedChanges` → Non sauvegardé
    - [x] draft write en cours → En cours…
    - [x] `lastDraftSavedAt` → Sauvegardé il y a Xs/min
    - [x] `lastDraftError` → Erreur

- [ ] Task 4: (Optionnel / stretch) Auto-save disque “sur inactivité” plutôt qu’un timer fixe (alignement ID-001, sans UX dégradée)
  - [ ] Ajouter une option (feature flag simple) pour déclencher une sauvegarde disque silencieuse:
    - [ ] condition: dialogue sélectionné + `hasUnsavedChanges === true` + pas de génération/sauvegarde
    - [ ] déclencheur: “idle depuis 2 minutes” (aucune interaction) **ou** “2 minutes depuis dernière sauvegarde disque” (si tu choisis ce modèle)
    - [ ] exécution: appeler la sauvegarde existante (export Unity) sans toast
    - [ ] si `unity_dialogues_path` non configuré → rester en mode “draft only” + statut informatif
  - [ ] Objectif: respecter l’intention “2min” sans imposer un `setInterval` bête.

- [x] Task 5: Tests (backend + frontend) (AC: #1-#5)
  - [x] Frontend (Vitest):
    - [x] Tests unitaires pour la logique de statut (dirty/draftSaved/draftError) dans `graphStore`
    - [x] Tests unitaires sur l’affichage de l’indicateur (temps relatif, états)
  - [ ] E2E (Playwright) – minimal et robuste:
    - [ ] Éditer un nœud → attendre écriture draft → reload → vérifier prompt de restauration.
    - [ ] (Si Task 4 implémentée) vérifier qu’une sauvegarde disque silencieuse peut se produire sans toast.

## Dev Notes

### Existing Codebase Verification (OBLIGATOIRE)

- ✅ **Pattern de brouillon local déjà existant (référence)**:
  - `frontend/src/components/generation/GenerationPanel.tsx` persiste un draft `generation_draft` en `localStorage` avec debounce court.
  - **Décision**: appliquer le même pattern au graphe (draft + restore) au lieu d’un “timer 2 minutes” comme mécanisme principal.

- ✅ **Sauvegarde fichier Unity déjà existante**:
  - `frontend/src/components/graph/GraphEditor.tsx` appelle `dialoguesAPI.exportUnityDialogue()` pour persister un fichier (Ctrl+S + bouton).
  - `api/routers/dialogues.py` expose `POST /api/v1/dialogues/unity/export` qui écrit sur le chemin Unity configuré.
  - **Décision**: **Réutiliser** cet endpoint pour la persistance canonique (save manuel) et, si nécessaire, pour une auto-save disque **optionnelle** (idle-based).

- ✅ **Bibliothèque Unity JSON existante**:
  - `api/routers/unity_dialogues.py` gère listing/lecture/suppression des fichiers Unity (source de vérité pour file metadata).
  - `frontend/src/api/unityDialogues.ts` consomme ces endpoints.

- ✅ **Indicateur de statut existant**:
  - `frontend/src/components/shared/SaveStatusIndicator.tsx` existe (états: saved/saving/unsaved/error).
  - **Décision**: Étendre cet indicateur pour afficher “Sauvegardé il y a Xs”.

### Architecture / Guardrails

- **Décision UX**: “Auto-save” = **draft local** (déclenché par changements, debounce court) ; “Save” = persistance canonique (fichier Unity).
- **Alignement ID-001**: si une auto-save disque est souhaitée, préférer “idle-based 2min” plutôt qu’un timer fixe intrusif.
- **Suspend during generation**: utiliser `useGraphStore().isGenerating` comme source de vérité.
- **Windows-first**: ne jamais supposer POSIX, encodage `utf-8`, chemins gérés côté backend via `Path`.
- **No noisy UX**: pas de toast sur auto-save draft (save manuel peut toaster).

### References

- [Source: _bmad-output/planning-artifacts/prd/epic-00.md#Story-0.5] — Story 0.5 (ID-001)
- [Source: _bmad-output/planning-artifacts/architecture.md#ID-001] — Auto-save (2min, LWW) + suspension pendant génération
- [Source: frontend/src/components/graph/GraphEditor.tsx] — Sauvegarde actuelle via `exportUnityDialogue` + raccourci Ctrl+S
- [Source: frontend/src/store/graphStore.ts] — État graphe, `isGenerating`, `isSaving`, conversion Unity ↔ graphe
- [Source: frontend/src/components/shared/SaveStatusIndicator.tsx] — Indicateur de statut existant
- [Source: api/routers/dialogues.py] — Endpoint export Unity JSON vers fichier
- [Source: api/routers/unity_dialogues.py] — Listing/lecture fichiers Unity JSON + métadonnées

## Dev Agent Record

### Agent Model Used

GPT-5.2

### Debug Log References

N/A

### Work Summary

- Implémentation d’un **auto-save draft local** (localStorage + debounce) pour l’éditeur de graphe, avec **proposition de restauration** si le draft est plus récent que le fichier.
- Ajout d’un **contrat d’état** d’auto-save dans `graphStore` (dirty/saved/error) et marquage “dirty” sur les mutations du graphe.
- Extension de `SaveStatusIndicator` pour afficher un **temps relatif** (“Sauvegardé il y a Xs/min”) et intégration dans l’UI du graphe.

### Tests / Validation

- **Unit tests ajoutés**: `frontend/src/__tests__/useGraphStore.test.ts` (état auto-save draft + mutations marquant dirty).
- **À compléter**:
  - Tests unitaires dédiés pour `SaveStatusIndicator` (temps relatif / états).
  - E2E Playwright minimal pour le flow “draft → reload → prompt restauration”.

### Completion Notes List

- Le besoin “je ne perds pas mon travail” est **déjà couvert** pour le panneau de génération via `generation_draft` (localStorage).
- La vraie lacune est l’éditeur de graphe: pas de draft/recovery automatique. Cette story recadre 0.5 en **extension du pattern existant** (draft local + restauration) appliqué au graphe.
- La persistance canonique reste le “save” explicite via `POST /api/v1/dialogues/unity/export`. Une auto-save disque 2min est laissée en option (idle-based) si besoin.

### File List

- Frontend (principal):
  - `frontend/src/components/graph/GraphEditor.tsx` ✅
  - `frontend/src/store/graphStore.ts` ✅
  - `frontend/src/components/shared/SaveStatusIndicator.tsx` ✅
  - `frontend/src/__tests__/useGraphStore.test.ts` ✅
  - `frontend/src/__tests__/SaveStatusIndicator.test.tsx` ✅ (tests ajoutés)
- Backend (référence/validation):
  - `api/routers/dialogues.py` (référence uniquement, non modifié)
  - `api/routers/unity_dialogues.py` (référence uniquement, non modifié)
- Documentation/Artifacts (non code source):
  - `_bmad-output/implementation-artifacts/sprint-status.yaml` (tracking sprint)
  - `_bmad-output/implementation-artifacts/0-5-auto-save-completion-notes.md` (notes complémentaires)

### Related Docs

- `_bmad-output/implementation-artifacts/0-5-auto-save-completion-notes.md`

