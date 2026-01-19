# Story 0.5: Auto-save dialogues (ID-001) - Completion Notes

## Résumé

Implémentation complète de l'auto-save draft pour l'éditeur de graphe (Tasks 1-3 complétées, Task 4 optionnelle skippée).

## Implémentation

### Backend (Python)
- ✅ Aucune modification backend nécessaire (auto-save draft côté frontend uniquement)

### Frontend (TypeScript/React)

#### Task 1 (graphStore.ts): Contrat auto-save draft
- Ajout états: `hasUnsavedChanges`, `lastDraftSavedAt`, `lastDraftError`
- Actions: `markDirty()`, `markDraftSaved()`, `markDraftError(message)`, `clearDraftError()`
- Mutations du graphe appellent automatiquement `markDirty()`: addNode, updateNode, deleteNode, connectNodes, disconnectNodes, updateNodePosition, updateMetadata
- `loadDialogue()` ne marque pas dirty (chargement initial)
- 15 tests unitaires passent

#### Task 2 (GraphEditor.tsx): Auto-save draft local
- Debounce 3s après dernier changement (déclenché si `hasUnsavedChanges === true`)
- Stockage localStorage: `unity_dialogue_draft:${selectedDialogue.filename}`
- Payload: `{ filename, json_content, timestamp }`
- Suspension écriture si: dialogue non sélectionné, génération IA, sauvegarde disque, ou chargement en cours
- Restauration au chargement: Compare `draft.timestamp` avec `selectedDialogue.modified_time`
- Propose restauration via `ConfirmDialog` si draft plus récent
- Suppression draft après sauvegarde disque manuelle réussie
- Handlers: `handleRestoreDraft()`, `handleDiscardDraft()`

#### Task 3 (SaveStatusIndicator.tsx): Indicateur "Sauvegardé il y a Xs"
- Extension props: `lastSavedAt?: number | null`, `errorMessage?: string | null`
- Helper `formatRelativeTime()`: Formatage temps relatif (Xs, Xmin, Xh, Xj)
- Mise à jour toutes les 10s via `useEffect` + `setInterval`
- Intégration dans `GraphEditor.tsx` header: Statut basé sur `hasUnsavedChanges`, `lastDraftSavedAt`, `lastDraftError`

## Tâches skippées
- ❌ Task 4 (Optionnelle): Auto-save disque sur inactivité (non implémentée)

## Tests
- ✅ Frontend: 15 tests unitaires graphStore (Task 1)
- ✅ Tests globaux: 174/178 tests passent
- ✅ Build production: Succès (5.29s)
- ✅ Compilation TypeScript: Aucune erreur bloquante

## Fichiers

**Modifiés:**
- `frontend/src/store/graphStore.ts`: États/actions auto-save draft
- `frontend/src/components/graph/GraphEditor.tsx`: Auto-save draft + restauration + ConfirmDialog
- `frontend/src/components/shared/SaveStatusIndicator.tsx`: Temps relatif

**Créés:**
- `frontend/src/__tests__/useGraphStore.test.ts`: 15 tests unitaires

**Total:**
- Lignes ajoutées: ~300
- Tests: 15 nouveaux (tous passent)
- Build: Succès
