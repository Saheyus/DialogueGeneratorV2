# Story 0.11: Header Refactoring - UI Consolidation

Status: done

<!-- Note: Refactorisation de l'interface - Consolidation des actions dans la barre supérieure -->

## Story

As a **utilisateur de l'application DialogueGenerator**,
I want **que les actions principales (Options, Actions, Compte) soient accessibles depuis la barre supérieure**,
so that **l'interface soit plus cohérente, épurée et que je puisse accéder aux fonctionnalités depuis n'importe quelle page**.

## Acceptance Criteria

1. **Given** je suis sur n'importe quelle page de l'application
   **When** je regarde la barre supérieure (Header)
   **Then** je vois les boutons "Options" et "Actions" à droite, avant l'avatar utilisateur
   **And** ces boutons sont visibles uniquement si je suis authentifié et que les actions de génération sont disponibles

2. **Given** je clique sur le bouton "Options"
   **When** la modal Options s'ouvre
   **Then** je peux accéder à l'onglet "Usage IA" dans la modal
   **And** l'onglet "Usage IA" affiche les statistiques d'utilisation LLM (même contenu que l'ancienne modal séparée)

3. **Given** je clique sur le dropdown "Actions"
   **When** le menu s'ouvre
   **Then** je vois deux options : "Exporter (Unity)" et "Reset"
   **And** les actions sont désactivées pendant le chargement ou la génération
   **And** le menu se ferme automatiquement après sélection d'une action ou au clic extérieur

4. **Given** je suis connecté avec un compte utilisateur
   **When** je regarde la barre supérieure
   **Then** je vois un avatar rond avec la première lettre de mon nom d'utilisateur
   **And** quand je clique sur l'avatar, un panneau s'ouvre avec mon nom d'utilisateur et le bouton "Déconnexion"
   **And** le panneau se ferme au clic extérieur ou après déconnexion

5. **Given** j'utilise le raccourci clavier `Ctrl+,`
   **When** je suis sur n'importe quelle page
   **Then** la modal Options s'ouvre avec l'onglet "Contexte" actif
   **And** le raccourci fonctionne depuis le Header

## Tasks / Subtasks

- [x] Task 1: Déplacer boutons Options et Actions dans Header (AC: #1, #3)
  - [x] Modifier `frontend/src/components/layout/Header.tsx`
  - [x] Ajouter bouton "Options" qui ouvre `GenerationOptionsModal`
  - [x] Créer dropdown "Actions" avec "Exporter (Unity)" et "Reset"
  - [x] Positionner les boutons à droite, avant l'avatar utilisateur
  - [x] Gérer visibilité conditionnelle (authentifié + actions disponibles)
  - [x] Gérer fermeture dropdown au clic extérieur
  - [x] Tests unitaires : Rendu boutons, ouverture dropdown, actions

- [x] Task 2: Intégrer "Usage IA" dans modal Options (AC: #2)
  - [x] Modifier `frontend/src/components/generation/GenerationOptionsModal.tsx`
  - [x] Ajouter onglet "Usage IA" dans la liste des onglets
  - [x] Créer composant `UsageTab` qui affiche `UsageDashboard`
  - [x] Ajouter prop `initialTab` pour ouvrir directement un onglet spécifique
  - [x] Mettre à jour type `TabId` pour inclure 'usage'
  - [x] Tests unitaires : Rendu onglet, affichage UsageDashboard

- [x] Task 3: Créer avatar utilisateur avec menu (AC: #4)
  - [x] Modifier `frontend/src/components/layout/Header.tsx`
  - [x] Remplacer texte "Connecté en tant que: {username}" et bouton "Déconnexion" par avatar rond
  - [x] Avatar : Afficher première lettre du nom d'utilisateur en majuscule
  - [x] Créer panneau déroulant avec nom d'utilisateur et bouton déconnexion
  - [x] Gérer ouverture/fermeture du panneau (clic avatar, clic extérieur)
  - [x] Ajouter effets de survol (zoom, ombre)
  - [x] Tests unitaires : Rendu avatar, ouverture panneau, déconnexion

- [x] Task 4: Nettoyage Dashboard (AC: #1)
  - [x] Modifier `frontend/src/components/layout/Dashboard.tsx`
  - [x] Supprimer barre d'options complète (boutons Options, Actions)
  - [x] Conserver uniquement indicateur "Brouillon non sauvegardé" (sans boutons)
  - [x] Supprimer états inutilisés : `isOptionsModalOpen`, `optionsModalInitialTab`, `isActionsDropdownOpen`, `actionsDropdownRef`
  - [x] Supprimer import `GenerationOptionsModal`
  - [x] Supprimer `useEffect` pour fermeture dropdowns
  - [x] Mettre à jour raccourcis clavier (retirer gestion modal Options)

- [x] Task 5: Raccourci clavier Header (AC: #5)
  - [x] Modifier `frontend/src/components/layout/Header.tsx`
  - [x] Ajouter hook `useKeyboardShortcuts` pour `Ctrl+,`
  - [x] Ouvrir modal Options avec onglet "Contexte" par défaut
  - [x] Tests : Vérifier raccourci fonctionne depuis Header

- [x] Task 6: Tests E2E complets (AC: #1, #2, #3, #4, #5)
  - [x] Créer `e2e/header-refactoring.spec.ts`
  - [x] Test : Boutons Options et Actions visibles dans Header
  - [x] Test : Modal Options s'ouvre, onglet Usage IA accessible
  - [x] Test : Dropdown Actions fonctionne (Exporter, Reset)
  - [x] Test : Avatar utilisateur et menu fonctionnent
  - [x] Test : Raccourci clavier `Ctrl+,` fonctionne

## Dev Notes

### Architecture Patterns

**Consolidation UI dans Header :**
- **Pattern centralisation** : Toutes les actions principales accessibles depuis Header (cohérent avec navigation globale)
- **Visibilité conditionnelle** : Boutons visibles uniquement si `isAuthenticated && user && actions.handleGenerate`
- **Dropdown pattern** : Réutilise pattern existant (similaire à `PresetSelector`) avec `useRef` et `useEffect` pour fermeture au clic extérieur

**Intégration Usage IA dans Options :**
- **Pattern modal multi-onglets** : Extension de `GenerationOptionsModal` existante (cohérent avec architecture)
- **Prop `initialTab`** : Permet ouverture directe sur onglet spécifique (UX améliorée)
- **Composant réutilisé** : `UsageDashboard` intégré directement (pas de duplication)

**Avatar utilisateur :**
- **Pattern dropdown** : Menu déroulant aligné à droite (cohérent avec autres dropdowns)
- **Affichage initiale** : Première lettre du nom d'utilisateur en majuscule (avatar simple, pas d'image)
- **Style cohérent** : Utilise `theme.button.primary` pour couleur, effets de survol similaires aux autres boutons

### Source Tree Components

**Frontend (TypeScript) :**
- `frontend/src/components/layout/Header.tsx` : **MODIFIER**
  - Ajout boutons "Options" et "Actions" dans section droite
  - Remplacement texte utilisateur + bouton déconnexion par avatar avec menu
  - Gestion états : `isOptionsModalOpen`, `optionsModalInitialTab`, `isActionsDropdownOpen`, `isUserMenuOpen`
  - Refs : `actionsDropdownRef`, `userMenuRef`
  - Raccourci clavier `Ctrl+,` via `useKeyboardShortcuts`
  - Import : `GenerationOptionsModal`, `useGenerationActionsStore`, `useGraphStore`, `useKeyboardShortcuts`

- `frontend/src/components/generation/GenerationOptionsModal.tsx` : **MODIFIER**
  - Ajout onglet "Usage IA" dans liste `tabs`
  - Ajout type `'usage'` dans `TabId`
  - Ajout prop `initialTab?: TabId` (optionnel)
  - Création composant `UsageTab()` qui affiche `UsageDashboard`
  - Import : `UsageDashboard`
  - `useEffect` pour mettre à jour `activeTab` quand `initialTab` change

- `frontend/src/components/layout/Dashboard.tsx` : **MODIFIER**
  - Suppression barre d'options complète (lignes 665-813)
  - Conservation indicateur "Brouillon non sauvegardé" uniquement
  - Suppression états : `isOptionsModalOpen`, `optionsModalInitialTab`, `isActionsDropdownOpen`, `actionsDropdownRef`
  - Suppression `useEffect` pour fermeture dropdowns
  - Suppression import `GenerationOptionsModal`
  - Mise à jour raccourcis clavier (retirer gestion modal Options)

**Tests :**
- `tests/frontend/Header.test.tsx` : **NOUVEAU** - Tests unitaires Header (boutons, dropdowns, avatar)
- `tests/frontend/GenerationOptionsModal.test.tsx` : **MODIFIER** - Tests onglet Usage IA
- `e2e/header-refactoring.spec.ts` : **NOUVEAU** - Tests E2E complets

### Technical Constraints

**Dropdown Pattern :**
- Utilise `useRef` pour référencer élément DOM
- `useEffect` avec `mousedown` listener pour détecter clic extérieur
- Cleanup : `removeEventListener` dans return de `useEffect`
- Z-index : 1000 pour s'assurer que dropdowns apparaissent au-dessus

**Modal Options :**
- Prop `initialTab` optionnel (défaut : 'context')
- `useEffect` pour synchroniser `activeTab` avec `initialTab` quand modal s'ouvre
- Pattern cohérent avec modal existante (overlay + header + tabs + content)

**Avatar utilisateur :**
- Taille : 36x36px (cohérent avec autres boutons)
- Style : `borderRadius: '50%'` pour forme ronde
- Couleur : `theme.button.primary.background` (cohérent avec thème)
- Effets : `transform: scale(1.05)` au survol, `boxShadow` pour profondeur

**Visibilité conditionnelle :**
- Boutons Options/Actions : `isAuthenticated && user && actions.handleGenerate`
- Avatar : `isAuthenticated && user` (toujours visible si connecté)

### Testing Standards

**Unit Tests :**
- Header : Rendu boutons, ouverture dropdowns, gestion états, avatar et menu
- GenerationOptionsModal : Rendu onglet Usage IA, prop initialTab, affichage UsageDashboard

**Integration Tests :**
- Dropdown Actions : Ouverture, sélection action, fermeture au clic extérieur
- Modal Options : Ouverture avec initialTab, navigation entre onglets

**E2E Tests (Playwright) :**
- Boutons visibles dans Header : Vérifier présence et position
- Modal Options : Ouvrir, vérifier onglet Usage IA accessible
- Dropdown Actions : Ouvrir, sélectionner action, vérifier comportement
- Avatar utilisateur : Cliquer, vérifier menu, déconnexion
- Raccourci clavier : `Ctrl+,` ouvre modal Options

### Project Structure Notes

**Alignment :**
- ✅ Utilise structure existante : `frontend/src/components/layout/` pour Header
- ✅ Suit patterns React : Hooks (`useState`, `useEffect`, `useRef`), composants fonctionnels
- ✅ Suit patterns Zustand : Utilise `useGenerationActionsStore` pour actions
- ✅ Suit patterns Modal : Extension de `GenerationOptionsModal` existante
- ✅ Suit patterns Dropdown : Réutilise pattern `PresetSelector` pour dropdowns

**New Files :**
- `tests/frontend/Header.test.tsx` : Tests unitaires Header (nouveau fichier)
- `e2e/header-refactoring.spec.ts` : Tests E2E (nouveau fichier)

**Modified Files :**
- `frontend/src/components/layout/Header.tsx` : Ajout boutons, avatar, dropdowns
- `frontend/src/components/generation/GenerationOptionsModal.tsx` : Ajout onglet Usage IA
- `frontend/src/components/layout/Dashboard.tsx` : Suppression barre d'options
- `tests/frontend/GenerationOptionsModal.test.tsx` : Tests onglet Usage IA

### Previous Story Intelligence

**Learnings from Story 0.2 (Progress Feedback Modal) :**
- **Pattern Modal** : Structure overlay + header + content scrollable (réutilisé pour Options)
- **Pattern Zustand** : Stores isolés par domaine (`generationStore` vs `graphStore`)
- **Pattern Dropdown** : `useRef` + `useEffect` pour fermeture au clic extérieur

**Files Created/Modified in Story 0.2 :**
- `frontend/src/components/generation/GenerationProgressModal.tsx` : Pattern modal (réutilisé comme référence)
- `frontend/src/store/generationStore.ts` : Store Zustand (pattern à suivre)

**Testing Approaches :**
- Tests unitaires : Composants isolés avec React Testing Library
- Tests E2E : Playwright avec scénarios utilisateur complets

### References

- **Epic 0 Story 0.11** : Header Refactoring - UI Consolidation
- **NFR-UX1** : Interface cohérente et intuitive - Consolidation améliore cohérence
- **NFR-UX2** : Accessibilité actions principales - Header accessible depuis toutes les pages
- **Pattern Dropdown** : [Source: `frontend/src/components/generation/PresetSelector.tsx`] - Pattern dropdown avec `useRef` et `useEffect`
- **Pattern Modal** : [Source: `frontend/src/components/generation/GenerationOptionsModal.tsx`] - Structure modal multi-onglets

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5

### Debug Log References

Session (2025-01-15) : Refactorisation progressive avec validation à chaque étape.

### Completion Notes List

✅ **Task 1 - Déplacer boutons dans Header** (2025-01-15)
- Ajouté boutons "Options" et "Actions" dans Header, section droite
- Créé dropdown "Actions" avec "Exporter (Unity)" et "Reset"
- Gestion visibilité conditionnelle et fermeture au clic extérieur
- Style cohérent avec reste de l'interface

✅ **Task 2 - Intégrer Usage IA dans Options** (2025-01-15)
- Ajouté onglet "Usage IA" dans `GenerationOptionsModal`
- Créé composant `UsageTab` qui affiche `UsageDashboard`
- Ajouté prop `initialTab` pour ouverture directe sur onglet spécifique
- Supprimé modal `UsageStatsModal` séparée (fonctionnalité intégrée)

✅ **Task 3 - Avatar utilisateur** (2025-01-15)
- Remplacé texte "Connecté en tant que: {username}" et bouton "Déconnexion" par avatar rond
- Avatar affiche première lettre du nom d'utilisateur en majuscule
- Créé panneau déroulant avec nom d'utilisateur et bouton déconnexion
- Ajouté effets de survol (zoom, ombre) pour meilleure UX

✅ **Task 4 - Nettoyage Dashboard** (2025-01-15)
- Supprimé barre d'options complète du Dashboard
- Conservé uniquement indicateur "Brouillon non sauvegardé"
- Nettoyé états et imports inutilisés
- Code plus simple et maintenable

✅ **Task 5 - Raccourci clavier** (2025-01-15)
- Ajouté gestion raccourci `Ctrl+,` dans Header
- Ouvrir modal Options avec onglet "Contexte" par défaut
- Fonctionne depuis n'importe quelle page

✅ **Task 6 - Tests** (2025-01-15)
- Tests unitaires : Header, GenerationOptionsModal
- Tests E2E : Scénarios complets de refactorisation

**Décisions techniques :**
- Pattern dropdown réutilisé depuis `PresetSelector` (cohérence)
- Avatar simple avec initiale (pas d'image, plus léger)
- Modal Options étendue (pas de nouvelle modal, cohérence)
- Header comme point d'accès unique (meilleure UX)

**Notes pour itérations futures :**
- TODO : Ajouter icône ou image pour avatar (si besoin)
- TODO : Ajouter notifications dans Header (si besoin)
- TODO : Ajouter menu contextuel pour avatar (paramètres, préférences)

### File List

**Nouveaux fichiers :**
- `tests/frontend/Header.test.tsx` - Tests unitaires Header
- `e2e/header-refactoring.spec.ts` - Tests E2E refactorisation

**Fichiers modifiés :**
- `frontend/src/components/layout/Header.tsx` - Ajout boutons, avatar, dropdowns
- `frontend/src/components/generation/GenerationOptionsModal.tsx` - Ajout onglet Usage IA
- `frontend/src/components/layout/Dashboard.tsx` - Suppression barre d'options
- `tests/frontend/GenerationOptionsModal.test.tsx` - Tests onglet Usage IA

**Diagrammes Excalidraw mis à jour :**
- `wireframe-app-shell-graph-editor-existing-empty-20260119-182000.excalidraw` - Header mis à jour avec boutons Options/Actions et avatar `[Options] [Actions ▾] [A]`, barre d'actions du panneau droit marquée comme déplacée (opacité réduite, style dashed)
- `wireframe-app-shell-graph-editor-existing-node-selected-details-panel-20260119-183000.excalidraw` - Barre d'actions du panneau détails marquée comme déplacée dans Header (opacité réduite, style dashed)
- `wireframe-app-shell-graph-editor-existing-dialogue-selected-20260119-183000.excalidraw` - Header mis à jour avec boutons Options/Actions et avatar `[Options] [Actions ▾] [A]`
