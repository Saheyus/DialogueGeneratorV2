# Story 0.12: UI Refactoring - Generation Panel (Sliders, Tooltips, Templates)

Status: done

<!-- Note: Refactorisation UI du panneau de génération - Harmonisation sliders, tooltips et templates -->

## Story

As a **utilisateur de l'application DialogueGenerator**,
I want **que l'interface du panneau de génération soit cohérente et visuellement harmonisée**,
so that **je puisse utiliser les contrôles (sliders, tooltips, templates) de manière intuitive et que l'interface soit visuellement cohérente**.

## Acceptance Criteria

1. **Given** je regarde la section "Templates de scène" dans l'éditeur de prompt système
   **When** je vois le dropdown de sélection
   **Then** le label "Templates de scène:" et le dropdown sont sur une seule ligne
   **And** la largeur du dropdown est réduite à 220px (au lieu de 250px)

2. **Given** je regarde la section "Modèle" et "Niveau de raisonnement" dans le panneau de génération
   **When** je vois les labels avec leurs icônes d'aide
   **Then** les icônes "?" ont le même style que celle de "Structure de dialogue" (24x24px, fontSize 14px)
   **And** les informations sont accessibles via tooltip (attribut `title`)
   **And** "Niveau de raisonnement" est aligné au même niveau que "Modèle" (deux colonnes côte à côte)

3. **Given** je regarde les sliders "Max tokens contexte" et "Max tokens génération"
   **When** je vois les deux sliders
   **Then** les deux sliders ont exactement le même style (handle centré, même apparence)
   **And** les barres bleues de progression sont visibles sur les deux sliders
   **And** le gradient de progression est appliqué dynamiquement selon la valeur

4. **Given** je modifie la valeur d'un slider (contexte ou génération)
   **When** je déplace le handle
   **Then** la barre bleue de progression se met à jour en temps réel
   **And** le gradient reste visible et cohérent

## Tasks / Subtasks

- [x] Task 1: Réduire largeur dropdown Templates de scène (AC: #1)
  - [x] Modifier `frontend/src/components/generation/SystemPromptEditor.tsx`
  - [x] Réduire largeur dropdown de 250px à 220px
  - [x] Vérifier que le layout reste sur une seule ligne (déjà en place)

- [x] Task 2: Harmoniser tooltips Modèle et Niveau de raisonnement (AC: #2)
  - [x] Modifier `frontend/src/components/generation/GenerationPanel.tsx`
  - [x] Uniformiser taille icônes "?" : 24x24px (au lieu de 20x20px)
  - [x] Uniformiser fontSize : 14px (au lieu de 12px)
  - [x] Vérifier que les tooltips fonctionnent (attribut `title` présent)
  - [x] Vérifier que "Niveau de raisonnement" est bien en colonne à côté de "Modèle"

- [x] Task 3: Harmoniser style des sliders avec gradient visible (AC: #3, #4)
  - [x] Modifier `frontend/src/components/generation/GenerationPanel.tsx`
  - [x] Créer fonction `applyRangeGradient` pour calculer et appliquer le gradient
  - [x] Ajouter refs séparées : `maxContextSliderRef` et `maxCompletionSliderRef`
  - [x] Ajouter `useEffect` pour appliquer gradient sur slider contexte
  - [x] Ajouter `useEffect` pour appliquer gradient sur slider génération
  - [x] Ajouter classe CSS `token-slider` aux deux inputs
  - [x] Modifier CSS pour utiliser variable CSS `--range-track-bg` pour le gradient
  - [x] Appliquer `padding: 0` et `margin: 0` sur les deux inputs pour centrage parfait
  - [x] Vérifier que les barres bleues sont visibles sur les deux sliders

## Dev Notes

### Architecture Patterns

**Harmonisation UI :**
- **Pattern cohérence visuelle** : Tous les tooltips utilisent le même style (24x24px, fontSize 14px) pour cohérence avec "Structure de dialogue"
- **Pattern layout flex** : "Modèle" et "Niveau de raisonnement" en colonnes côte à côte (`display: flex, gap: 1rem`)
- **Pattern CSS variables** : Utilisation de `--range-track-bg` pour appliquer le gradient dynamique sur les pistes de slider

**Sliders avec gradient :**
- **Pattern refs multiples** : Chaque slider a sa propre ref pour appliquer le gradient indépendamment
- **Pattern gradient dynamique** : Calcul du pourcentage basé sur `(value - min) / (max - min) * 100`
- **Pattern CSS variables** : Le gradient est stocké dans `--range-track-bg` et utilisé par les pseudo-éléments `::-webkit-slider-runnable-track`, `::-moz-range-track`, `::-ms-track`
- **Pattern fallback** : Le gradient est aussi appliqué directement sur `el.style.background` pour les navigateurs qui ne supportent pas les variables CSS

### Source Tree Components

**Frontend (TypeScript) :**
- `frontend/src/components/generation/SystemPromptEditor.tsx` : **MODIFIER**
  - Ligne 233 : Réduction largeur dropdown de `250px` à `220px`
  - Layout déjà en ligne (pas de changement nécessaire)

- `frontend/src/components/generation/GenerationPanel.tsx` : **MODIFIER**
  - Lignes 137-138 : Ajout refs `maxContextSliderRef` et `maxCompletionSliderRef`
  - Lignes 1113-1130 : Création fonction `applyRangeGradient` et `useEffect` pour appliquer gradients
  - Lignes 1199-1207 : Harmonisation icône tooltip "Modèle" (24x24px, fontSize 14px)
  - Lignes 1240-1248 : Harmonisation icône tooltip "Niveau de raisonnement" (24x24px, fontSize 14px)
  - Lignes 1306-1327 : Ajout `className="token-slider"` et `padding: 0, margin: 0` sur slider contexte
  - Lignes 1351-1374 : Ajout `className="token-slider"` et `padding: 0, margin: 0` sur slider génération
  - Lignes 1387-1447 : Modification CSS pour utiliser `--range-track-bg` avec classe `.token-slider`

### Technical Constraints

**Tooltips :**
- Taille icône : 24x24px (cohérent avec `DialogueStructureWidget`)
- FontSize : 14px (cohérent avec `DialogueStructureWidget`)
- BorderRadius : 12px (50% de 24px)
- Utilisation attribut `title` pour tooltip natif (pas de composant custom)

**Sliders :**
- Classe CSS : `token-slider` pour cibler les deux sliders
- Variable CSS : `--range-track-bg` pour gradient dynamique
- Gradient : `linear-gradient(to right, ${theme.border.focus} 0%, ${theme.border.focus} ${percentage}%, ${theme.input.background} ${percentage}%, ${theme.input.background} 100%)`
- Pseudo-éléments : `::-webkit-slider-runnable-track`, `::-moz-range-track`, `::-ms-track` utilisent `var(--range-track-bg)`
- Padding/Margin : `0` sur les inputs pour centrage parfait du handle

**Layout Modèle/Niveau de raisonnement :**
- Container : `display: flex, gap: 1rem, alignItems: flex-start`
- Colonnes : `flex: 1` sur chaque colonne pour répartition égale
- Visibilité conditionnelle : "Niveau de raisonnement" visible uniquement si `llmModel === "gpt-5.2" || llmModel === "gpt-5.2-pro"`

### Testing Standards

**Visual Tests :**
- Templates de scène : Vérifier dropdown sur une ligne, largeur 220px
- Tooltips : Vérifier taille icônes 24x24px, fontSize 14px, tooltips fonctionnent au survol
- Sliders : Vérifier barres bleues visibles, handles centrés, gradients se mettent à jour

**Manual Testing Checklist :**
- [x] Dropdown Templates de scène : Largeur réduite, layout en ligne
- [x] Tooltips Modèle/Niveau de raisonnement : Style cohérent, informations accessibles
- [x] Slider contexte : Barre bleue visible, handle centré, gradient se met à jour
- [x] Slider génération : Barre bleue visible, handle centré, gradient se met à jour
- [x] Layout Modèle/Niveau de raisonnement : Deux colonnes côte à côte

### Project Structure Notes

**Alignment :**
- ✅ Utilise structure existante : `frontend/src/components/generation/` pour composants
- ✅ Suit patterns React : Hooks (`useState`, `useEffect`, `useRef`), composants fonctionnels
- ✅ Suit patterns CSS : Variables CSS pour dynamisme, pseudo-éléments pour style sliders
- ✅ Suit patterns cohérence UI : Style tooltips aligné avec `DialogueStructureWidget`

**Modified Files :**
- `frontend/src/components/generation/SystemPromptEditor.tsx` : Réduction largeur dropdown
- `frontend/src/components/generation/GenerationPanel.tsx` : Harmonisation tooltips, sliders avec gradient

### Previous Story Intelligence

**Learnings from Story 0.11 (Header Refactoring) :**
- **Pattern cohérence visuelle** : Harmonisation des styles entre composants (tooltips, boutons)
- **Pattern CSS variables** : Utilisation de variables CSS pour dynamisme (réutilisé pour gradients)
- **Pattern refs multiples** : Utilisation de refs séparées pour éléments similaires (sliders)

**Files Created/Modified in Story 0.11 :**
- `frontend/src/components/layout/Header.tsx` : Pattern tooltip avec icône "?" (réutilisé comme référence)
- `frontend/src/components/generation/DialogueStructureWidget.tsx` : Style tooltip 24x24px, fontSize 14px (réutilisé comme référence)

### References

- **Epic 0 Story 0.12** : UI Refactoring - Generation Panel (Sliders, Tooltips, Templates)
- **NFR-UX1** : Interface cohérente et intuitive - Harmonisation améliore cohérence visuelle
- **Pattern Tooltip** : [Source: `frontend/src/components/generation/DialogueStructureWidget.tsx`] - Style tooltip 24x24px, fontSize 14px
- **Pattern Slider** : [Source: `frontend/src/components/generation/GenerationPanel.tsx`] - Slider avec gradient dynamique via CSS variables

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5

### Debug Log References

Session (2025-01-15) : Refactorisation progressive avec validation visuelle à chaque étape.

### Completion Notes List

✅ **Task 1 - Réduire largeur dropdown Templates de scène** (2025-01-15)
- Réduit largeur dropdown de 250px à 220px dans `SystemPromptEditor.tsx`
- Layout déjà en ligne (pas de changement nécessaire)
- Dropdown plus compact et visuellement harmonisé

✅ **Task 2 - Harmoniser tooltips Modèle et Niveau de raisonnement** (2025-01-15)
- Uniformisé taille icônes "?" : 24x24px (au lieu de 20x20px)
- Uniformisé fontSize : 14px (au lieu de 12px)
- Style cohérent avec `DialogueStructureWidget`
- Tooltips fonctionnent via attribut `title`
- Layout en deux colonnes côte à côte (déjà en place)

✅ **Task 3 - Harmoniser style des sliders avec gradient visible** (2025-01-15)
- Créé fonction `applyRangeGradient` pour calculer et appliquer le gradient
- Ajouté refs séparées : `maxContextSliderRef` et `maxCompletionSliderRef`
- Ajouté `useEffect` pour appliquer gradient sur slider contexte
- Ajouté `useEffect` pour appliquer gradient sur slider génération
- Ajouté classe CSS `token-slider` aux deux inputs
- Modifié CSS pour utiliser variable CSS `--range-track-bg` pour le gradient
- Appliqué `padding: 0` et `margin: 0` sur les deux inputs pour centrage parfait
- Barres bleues maintenant visibles sur les deux sliders
- Gradient se met à jour dynamiquement selon la valeur

**Décisions techniques :**
- Utilisation de variables CSS `--range-track-bg` pour appliquer le gradient sur les pseudo-éléments (meilleure compatibilité navigateurs)
- Fallback : Gradient aussi appliqué directement sur `el.style.background` pour navigateurs qui ne supportent pas les variables CSS
- Classe CSS `.token-slider` pour cibler les deux sliders de manière cohérente
- Padding/Margin à 0 pour centrage parfait du handle

**Notes pour itérations futures :**
- TODO : Ajouter tests unitaires pour vérifier application du gradient
- TODO : Ajouter tests visuels pour vérifier cohérence des tooltips
- TODO : Considérer composant Tooltip réutilisable si besoin d'animations ou de styles custom

### File List

**Fichiers modifiés :**
- `frontend/src/components/generation/SystemPromptEditor.tsx` - Réduction largeur dropdown Templates de scène
- `frontend/src/components/generation/GenerationPanel.tsx` - Harmonisation tooltips, sliders avec gradient visible
