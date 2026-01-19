---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8, 9]
inputDocuments:
  - _bmad-output/planning-artifacts/product-brief-DialogueGenerator-2026-01-13.md
  - _bmad-output/planning-artifacts/prd.md
  - docs/features/current-ui-structure.md
  - docs/architecture/GRAPH_EDITOR.md
  - docs/architecture/GRAPH_EDITOR_IMPLEMENTATION.md
date: 2026-01-19
author: Marc
project_name: DialogueGenerator
---

# UX Design Specification DialogueGenerator

**Author:** Marc
**Date:** 2026-01-19

---

<!-- UX design content will be appended sequentially through collaborative workflow steps -->

## Executive Summary

### Project Vision

DialogueGenerator est un outil de génération assistée par IA pour dialogues arborescents (type Disco Elysium), permettant aux auteurs de générer des dialogues complets (centaines de nœuds) en ≤1H. L'éditeur de graphe est le **point critique de l'UI** : interface complexe avec contraintes d'espace importantes (panneaux latéraux réduisent l'espace du canvas).

**Contexte brownfield** : L'interface actuelle fonctionne et sert de baseline. Les améliorations UX doivent itérer progressivement sans casser le workflow existant.

### Target Users

**Primary Users :**
- **Marc** : Power user, 40h+/semaine, développe aussi l'application
- **Mathieu** : Casual user, quelques heures/semaine, besoin d'efficacité optimale

**Workflow actuel (phase test) :** Génération → Sélection → Génération (suite) → Génération (suite)
- Objectif immédiat : Produire un premier dialogue complet
- Graphes actuels : 2 nœuds max (phase test)
- Pas encore à l'échelle 100+ nœuds

### Key Design Challenges

**1. Contraintes d'espace dans le Graph Editor**
- Panneaux latéraux (Contexte gauche + Détails droite) réduisent l'espace du canvas
- Panneaux collapsibles/redimensionnables (min ~100px) mais rarement masqués
- Zone centrale contient beaucoup d'infos (liste dialogues + canvas graphe)
- Besoin d'un mode plein écran pour le canvas (raccourci discret)

**2. Gestion des 4 résultats de test (nouvelle fonctionnalité)**
- Visualisation : Nœud de test (rond orange) → fil → petite barre avec 4 ronds colorés (un par niveau) → chaque rond relié à un nœud de réponse PNJ
- 4 résultats distincts qui envoient dans 4 directions (comme des choix normaux)
- Les résultats sont des nodes normaux (réponses PNJ) édités dans le panel standard

**3. Doublon d'information dans "Édition de Dialogues"**
- Problème : Liste dialogues (gauche) + détails (centre) + panel édition (droite) = doublon
- Solution : Utiliser directement le panel tout à droite au lieu du panneau central

**4. Organisation des panneaux**
- Panel de droite : Visible en permanence (contient onglets génération + détails contexte)
- Liste dialogues à gauche du graphe : Pourrait être masquable pour se concentrer sur le dialogue

### Design Opportunities

**1. Visualisation claire des 4 résultats de test**
- Pattern visuel innovant : Barre intermédiaire avec 4 ronds colorés pour clarifier les connexions
- Couleurs distinctes : Échec critique (rouge foncé #c0392b), Échec (rouge #e74c3c), Réussite (vert #27ae60), Réussite critique (vert foncé #229954)

**2. Optimisation de l'espace canvas**
- Mode plein écran avec raccourci discret (F11 ou ⌘+K)
- Liste dialogues masquable pour focus sur le dialogue
- Panneaux redimensionnables pour ajustement fin

**3. Élimination des doublons**
- Simplifier "Édition de Dialogues" en utilisant uniquement le panel droit
- Réduire la redondance d'information entre panneaux

### Diagrammes Excalidraw Créés

Les diagrammes suivants clarifient l'UI du graph editor :

1. **`wireframe-graph-editor-layout-20260119-150046.excalidraw`**
   - Layout actuel avec contraintes d'espace
   - Visualisation des panneaux latéraux et leur impact sur le canvas

2. **`wireframe-test-4-results-visualization-20260119-150046.excalidraw`**
   - **CRITIQUE** : Visualisation des 4 résultats de test
   - Pattern : Test Node → Fil → Barre avec 4 ronds colorés → Nodes PNJ
   - Couleurs et labels pour chaque niveau

3. **`wireframe-edition-dialogues-duplication-20260119-150046.excalidraw`**
   - Problème de doublon dans "Édition de Dialogues"
   - Solution : Utiliser directement le panel de droite

4. **`wireframe-graph-editor-optimizations-20260119-150046.excalidraw`**
   - Opportunités d'optimisation (mode plein écran, panneaux masquables)
   - Raccourcis et toggles pour maximiser l'espace canvas

## Core User Experience

### Defining Experience

L'expérience cœur du Graph Editor est : **"Generate Next" — prolonger un dialogue à partir d'un point précis du graphe, de façon itérative et rapide**, sans perdre le contexte.

**Core loop (répétée en continu sur le même dialogue) :**
- Sélectionner un nœud "point d'ancrage" dans le graphe
- Lancer **"Generate Next"** (via modal) — action unifiée pour tous les cas
- Choisir la/les cibles PJ auxquelles le PNJ répond (1 choix spécifique / plusieurs / tous)
- Générer le(s) nœud(s) résultat(s) avec **auto-apply des connexions** (`targetNode`/`nextNode` remplis automatiquement)
- Sauvegarder (auto-save toutes les 2min, suspendu pendant génération)
- **Auto-focus** : zoom/center automatique vers nouveau nœud généré (ou premier en batch)
- Reboucler (souvent sans re-sélectionner le dialogue)

**Action critique à rendre fluide :**
**"Generate Next for target(s)"** — générer la suite à partir d'une/plusieurs cibles PJ choisies, en gardant le focus et le contexte.

**Parité fonctionnelle (Story 0.5.5) :**
Toutes les fonctionnalités de génération doivent être disponibles **identiquement** dans l'éditeur de graphe ET l'éditeur de dialogue :
- Génération pour choix spécifique
- Génération batch pour tous les choix
- Génération nextNode pour navigation linéaire
- Même modal progression, même streaming, même auto-apply connexions

### Platform Strategy

**Plateforme :** Web React (architecture existante, pas de changement prévu)

**Mode d'interaction :**
- Souris/clavier (pas de tactile)
- Écran d'ordinateur par défaut
- Pas de contraintes d'accessibilité mobile pour l'instant

**Contraintes techniques :**
- Architecture React existante à respecter
- Pas de refonte majeure, itérations progressives uniquement
- Patterns existants à respecter (Zustand stores, FastAPI routers, React modals)

### Effortless Interactions

**Interaction à rendre quasi automatique : "Generate Next for target(s)"**

**Ciblage PJ explicite (Story 0.5.5) :**
- **Une cible** : Générer pour un choix PJ spécifique
- **Multi-cibles** : Générer pour plusieurs choix sélectionnés
- **Tous** : Générer pour tous les choix sans `targetNode` (mode batch first-class)

**Réduire la friction de sélection :**
- Defaults intelligents : dernière cible réutilisée, "tous" persistent
- Multi-select ergonomique (checkboxes visibles)
- Feedback immédiat : "X choix(s) déjà connecté(s), Y nouveau(x) nœud(s) généré(s)"

**Limiter les changements de contexte :**
- Rester sur le même dialogue (pas de re-sélection)
- Conserver sélection/zoom/panneau/options du modal entre itérations
- Auto-focus après génération : zoom vers nouveau nœud (graphe) ou focus dans liste (dialogue editor)

**Feedback immédiat :**
- Preview de ce qui va être généré (quelles cibles, combien de nœuds)
- Progression lisible ("Génération 2/5..." si batch)
- Annulation/retry clairs

**Barre 4 résultats de test (nouvelle fonctionnalité) :**
- **Mode compact** : 4 ronds colorés seulement (rouge → jaune → vert → bleu), labels en infobulle au survol
- **Mode explicite au hover/selection** : Afficher temporairement les libellés + highlight du chemin
- Traiter comme "fan-out connector" : même comportement que "Generate Next" (auto-apply connexions)

### Critical Success Moments

Basés sur les failure modes du PRD et Epic 0 :

**1. Cible(s) PJ correctement choisie(s)**
- Si erreur → génération "à côté", perte de temps
- Solution : Preview claire avant génération, feedback "X déjà connectés"

**2. Résultat généré utilisable**
- Critère PRD : **80%+ nœuds acceptés sans modification**
- Si échec → re-génération, frustration
- Solution : Qualité prompt + contexte, retry facile

**3. Raccord correct visible**
- L'utilisateur doit voir immédiatement où ça se branche
- Solution : **Auto-apply connexions** (`auto_apply: true`), highlight automatique

**4. Sauvegarde fiable**
- Zero data loss (PRD NFR-R3)
- Solution : Auto-save 2min (suspendu pendant génération), session recovery

**5. Pas d'UI freeze / LLM fail**
- PRD : Génération <30s, pas de freeze
- Solution : Streaming visible, retry clair, statut génération toujours visible

### Experience Principles

**1. Loop-first : "Generate Next" unifié**
   - Toute friction dans "sélection → cible(s) → génération → auto-apply → save → auto-focus" est prioritaire
   - Même terminologie et UX partout : "Generate Next" (pas "créer nœud")

**2. State persistence & continuity**
   - Le focus (dialogue, nœud, zoom, options) ne doit pas se perdre entre itérations
   - Auto-save suspendu pendant génération (ID-001)
   - Session recovery automatique

**3. Targeting clarity**
   - L'utilisateur sait toujours *à quelle(s) cible(s) PJ* le PNJ répond, avant de générer
   - Preview explicite : "Générer pour 3 choix" vs "Générer pour tous (5 choix)"
   - Feedback "X déjà connectés / Y générés"

**4. Auto-apply & trust**
   - Connexions appliquées automatiquement (`auto_apply: true` dans Story 0.5.5)
   - Retry, annulation, pas de duplication
   - L'utilisateur garde confiance dans l'outil

**5. Parité Graphe ↔ Dialogue Editor**
   - Mêmes fonctionnalités des deux côtés (Story 0.5.5)
   - Même UX, même modal, même auto-apply
   - Focus automatique adapté (zoom graphe vs focus liste)

**6. Resilience & feedback**
   - Validation structure non-bloquante mais actionnable (cycles, orphans, stableID)
   - Warnings cliquables → zoom → highlight
   - Retry clair, statut toujours visible

## Desired Emotional Response

### Primary Emotional Goals

**Concentration & Flow (état de travail optimal)**
- L'utilisateur entre dans un état de **concentration profonde** où l'outil disparaît
- Le workflow "Generate Next" devient **fluide et automatique** — pas de friction cognitive
- Sensation de **flow** : l'utilisateur se concentre sur le contenu créatif, pas sur l'outil
- L'outil est un **instrument de travail transparent** qui ne distrait pas de la création narrative

**Satisfaction de la qualité IA (micro-niveau)**
- **Satisfaction immédiate** quand l'IA génère un nœud pertinent et bien écrit
- Sentiment de **collaboration efficace** avec l'IA (80%+ nœuds acceptés sans modification)
- **Confiance** dans la génération : l'utilisateur sait que l'IA comprend le contexte
- **Délice** occasionnel : surprise positive quand l'IA propose quelque chose d'inattendu mais pertinent

**Efficacité productive (macro-niveau)**
- Sentiment d'**accomplissement** : générer des centaines de nœuds en ≤1H
- **Productivité visible** : le graphe se construit rapidement, progression claire
- **Contrôle** : l'utilisateur maîtrise le processus, pas submergé par la complexité
- **Fiabilité** : l'outil ne casse pas, les données ne se perdent pas (zero data loss)

### Emotional Journey Mapping

**Première découverte :**
- **Curiosité** : "Comment ça marche ?" → Interface claire, pas de confusion initiale
- **Confiance** : L'outil semble professionnel et fiable (pas de bugs visibles)

**Pendant le workflow "Generate Next" (boucle principale) :**
- **Concentration** : Focus sur le contenu, l'outil reste en arrière-plan
- **Flow** : Rythme régulier, pas d'interruptions, progression fluide
- **Expectative positive** : Attente confiante de la génération IA (pas d'anxiété)
- **Satisfaction micro** : Plaisir à voir chaque nœud bien généré

**Après complétion d'un dialogue :**
- **Accomplissement** : Fierté d'avoir créé un dialogue complet
- **Satisfaction** : Le travail est bien fait, prêt pour Unity
- **Confiance** : L'export est fiable, pas de corruption

**En cas d'erreur (génération échoue, bug) :**
- **Frustration minimisée** : Retry clair, pas de perte de travail (auto-save)
- **Confiance dans la récupération** : L'outil gère les erreurs gracieusement
- **Pas d'anxiété** : L'utilisateur sait qu'il peut réessayer sans conséquences

**Retour à l'outil :**
- **Familiarité** : L'interface est cohérente, pas besoin de réapprendre
- **Reprise rapide** : Session recovery, l'utilisateur reprend où il en était
- **Efficacité immédiate** : Pas de friction pour recommencer à travailler

### Micro-Emotions

**Confiance vs Confusion :**
- **Confiance** : L'utilisateur sait toujours où il en est dans le graphe (auto-focus, highlight)
- **Confiance** : Les connexions auto-apply sont fiables, pas besoin de vérifier
- **Éviter confusion** : Navigation claire, labels explicites au survol (barre 4 résultats)

**Confiance vs Scepticisme :**
- **Confiance** : L'auto-apply des connexions fonctionne correctement (pas de bugs)
- **Confiance** : L'auto-save protège le travail (zero data loss)
- **Éviter scepticisme** : Feedback visible ("Sauvegardé il y a Xs"), statut génération toujours visible

**Excitement vs Anxiété :**
- **Excitement positif** : La génération IA est un moment intéressant (streaming visible)
- **Éviter anxiété** : Pas d'incertitude sur "est-ce que ça marche ?" (progression claire)
- **Éviter anxiété** : Pas de peur de perdre le travail (auto-save, session recovery)

**Accomplissement vs Frustration :**
- **Accomplissement** : Progression visible (graphe qui grandit, nœuds qui s'ajoutent)
- **Accomplissement** : Critère de succès clair (80%+ nœuds acceptés)
- **Éviter frustration** : Pas de bugs bloquants, retry facile, pas de perte de temps

**Délice vs Satisfaction basique :**
- **Délice occasionnel** : Surprise positive quand l'IA propose quelque chose d'inattendu mais pertinent
- **Satisfaction régulière** : Chaque nœud bien généré apporte une petite satisfaction
- **Éviter satisfaction basique** : L'outil doit dépasser les attentes, pas juste fonctionner

### Design Implications

**Pour favoriser Concentration & Flow :**
- **Minimiser les interruptions** : Auto-save silencieux, pas de modals bloquantes
- **Feedback discret** : Indicateurs visuels subtils (pas de popups agressives)
- **Workflow fluide** : Réduire les clics, defaults intelligents, auto-apply connexions
- **Mode plein écran** : Raccourci discret (F11) pour immersion totale

**Pour créer Satisfaction micro (qualité IA) :**
- **Preview avant génération** : L'utilisateur voit ce qui va être généré (cibles, contexte)
- **Streaming visible** : Voir le texte se construire en temps réel (excitement positif)
- **Feedback qualité** : Indicateur "80%+ acceptés" pour renforcer la confiance
- **Retry facile** : Bouton "Re-générer" visible, pas de friction

**Pour renforcer Efficacité (macro) :**
- **Progression visible** : Graphe qui grandit, compteur de nœuds, indicateurs de complétion
- **Auto-focus après génération** : L'utilisateur voit immédiatement le résultat (satisfaction)
- **Batch génération** : "Générer tous les choix" pour productivité maximale
- **Validation non-bloquante** : Warnings cliquables, pas d'interruption du workflow

**Pour éviter Frustration (erreurs/bugs) :**
- **Retry clair** : Bouton visible, pas de confusion sur comment réessayer
- **Auto-save visible** : "Sauvegardé il y a Xs" pour rassurer
- **Session recovery** : Message "Modifications récupérées" au démarrage
- **Validation actionnable** : Warnings cliquables → zoom → highlight (pas juste des erreurs)

**Pour créer Délice occasionnel :**
- **Surprises positives** : L'IA propose parfois quelque chose d'inattendu mais pertinent
- **Animations subtiles** : Transitions fluides, feedback visuel agréable (pas de flashy)
- **Moments de satisfaction** : Auto-apply connexions "juste fonctionne" (magie invisible)

### Emotional Design Principles

**1. Flow-first : L'outil disparaît**
   - Minimiser toute friction cognitive dans la boucle "Generate Next"
   - L'utilisateur se concentre sur le contenu créatif, pas sur l'outil
   - Auto-apply, defaults intelligents, feedback discret

**2. Satisfaction micro régulière**
   - Chaque nœud bien généré apporte une petite satisfaction
   - Streaming visible pour excitement positif
   - Preview et feedback qualité pour renforcer la confiance

**3. Efficacité visible**
   - Progression claire (graphe qui grandit, nœuds qui s'ajoutent)
   - Batch génération pour productivité maximale
   - Auto-focus pour voir immédiatement les résultats

**4. Confiance & fiabilité**
   - Auto-save visible, session recovery, zero data loss
   - Auto-apply connexions fiables (pas de bugs)
   - Retry facile, pas d'anxiété en cas d'erreur

**5. Délice occasionnel**
   - Surprises positives de l'IA (inattendu mais pertinent)
   - Animations subtiles, transitions fluides
   - Magie invisible : les choses "juste fonctionnent" (auto-apply)

**6. Éviter frustration**
   - Pas de bugs bloquants, retry clair
   - Validation non-bloquante mais actionnable
   - Pas de perte de temps, pas de perte de travail

## UX Pattern Analysis & Inspiration

### Inspiring Products Analysis

**Articy Draft X (Référence principale - Éditeur de dialogue professionnel)**

**Forces UX identifiées :**

1. **Nested Flows & Hierarchy**
   - Structure hiérarchique claire : Flows → Dialogues → Fragments
   - Permet de gérer des dialogues complexes sans surcharge visuelle
   - **Pattern transférable** : Groupement logique, navigation hiérarchique

2. **Pins System (Input/Output)**
   - Pins visibles sur les côtés des dialogues pour connexions
   - Conditions et instructions attachées aux pins
   - **Pattern transférable** : Handles de sortie clairs, connexions conditionnelles

3. **Quick Create & Templates**
   - Menu "Quick Create" pour ajouter plusieurs fragments rapidement
   - Templates avec propriétés par défaut
   - **Pattern transférable** : Génération batch, presets avec defaults intelligents

4. **Hub-Based Dialogue**
   - Hubs comme points de branchement/merge pour réduire la complexité
   - Évite les "spaghetti connections"
   - **Pattern transférable** : Barre intermédiaire 4 résultats (comme hub visuel)

5. **Multiple Views & Workspace Layout**
   - Navigator gauche (hiérarchie) + Content area droite (éditeur)
   - Onglets pour différentes vues
   - **Pattern transférable** : Layout 3 colonnes (Contexte/Liste | Canvas | Détails)

6. **Progressive Disclosure**
   - Détails des nodes seulement sur demande (hover, click)
   - Vue d'ensemble d'abord, drill-down ensuite
   - **Pattern transférable** : Labels barre 4 résultats en infobulle, détails dans panel

**Patterns d'éditeurs de graphes généraux (Miro, Figma, outils node-based)**

**Forces UX identifiées :**

1. **Canvas & Spatial Interaction**
   - Zoom/pan fluides, snapping au grid, minimap pour orientation
   - **Pattern transférable** : Mode plein écran, navigation spatiale claire

2. **Node Creation & Linking**
   - Drag-and-drop depuis palette, quick linking (drag port → port)
   - Preview de connexion pendant le drag, snap-to targets
   - **Pattern transférable** : Génération depuis modal, auto-apply connexions

3. **Visual Feedback & States**
   - Highlight connexions au hover/selection, états visuels (selected, hover, drag-over)
   - Animations subtiles pour transitions
   - **Pattern transférable** : Highlight barre 4 résultats au hover, feedback génération

4. **Inline Editing**
   - Double-click ou context menu pour éditer sans quitter le canvas
   - **Pattern transférable** : Panel droit pour édition sans perdre contexte graphe

5. **Undo/Redo & Safety**
   - Undo/redo essentiel, confirmations pour actions destructives
   - **Pattern transférable** : Auto-save, session recovery, retry facile

### Transferable UX Patterns

**Navigation & Layout Patterns :**

1. **Layout 3 colonnes (inspiré Articy Draft X)**
   - Navigator gauche (Contexte/Liste dialogues) + Canvas centre + Content area droite (Détails/Édition)
   - **Application** : Respecter cette structure, optimiser l'espace canvas

2. **Progressive Disclosure (inspiré patterns généraux)**
   - Vue d'ensemble d'abord, détails sur demande
   - **Application** : Barre 4 résultats compacte (ronds seulement), labels en infobulle

3. **Multiple Views (inspiré Articy Draft X)**
   - Onglets pour différentes vues (Génération, Détails contexte, Édition nœud)
   - **Application** : Panel droit avec onglets, pas de doublon central

**Interaction Patterns :**

4. **Quick Create / Batch Generation (inspiré Articy Draft X)**
   - Menu rapide pour créer plusieurs éléments avec defaults
   - **Application** : "Générer tous les choix" comme first-class, batch génération

5. **Auto-apply Connections (inspiré patterns généraux)**
   - Connexions appliquées automatiquement avec preview
   - **Application** : `auto_apply: true` dans Story 0.5.5, highlight automatique

6. **Inline Editing (inspiré patterns généraux)**
   - Édition sans quitter le canvas, panel contextuel
   - **Application** : Panel droit pour édition, focus automatique après génération

7. **Hub-Based Branching (inspiré Articy Draft X)**
   - Points de branchement visuels pour réduire complexité
   - **Application** : Barre 4 résultats comme "hub visuel" pour tests

**Visual Design Patterns :**

8. **Color Coding & Visual Differentiation**
   - Couleurs distinctes pour types de nodes, états, importance
   - **Application** : Barre 4 résultats (rouge → jaune → vert → bleu), nodes test (orange)

9. **Highlight on Hover/Selection**
   - Connexions et nodes liés highlightés au hover
   - **Application** : Highlight barre 4 résultats au hover, chemin visible

10. **Readable Labels & Adaptive Text**
    - Labels complets en tooltip, texte adaptatif selon zoom
    - **Application** : Infobulles barre 4 résultats, preview avant génération

**Performance & Scalability Patterns :**

11. **Lazy Rendering / Viewport Rendering**
    - Rendre uniquement ce qui est visible
    - **Application** : Graphe 500+ nœuds : rendering <1s (PRD NFR-P1)

12. **Clustering & Grouping**
    - Groupement logique pour réduire complexité visuelle
    - **Application** : Groupement par dialogue, collapse/expand si nécessaire

### Anti-Patterns to Avoid

**1. "Spaghetti Connections" (Hairballs)**
   - Trop de connexions qui se croisent, illisible
   - **À éviter** : Auto-layout intelligent, minimiser croisements, routing propre

**2. "Star-bursts" (Node avec trop de connexions)**
   - Un seul node avec énormément d'edges qui domine la vue
   - **À éviter** : Hub-based branching (barre 4 résultats), clustering

**3. "Snowstorms" (Nodes isolés flottants)**
   - Beaucoup de nodes déconnectés sans structure
   - **À éviter** : Auto-apply connexions, validation structure (orphans)

**4. Modal Overload**
   - Trop de modals qui interrompent le workflow
   - **À éviter** : Panel contextuel plutôt que modal, feedback discret

**5. Perte de Contexte**
   - Navigation qui fait perdre le focus, zoom, sélection
   - **À éviter** : Auto-focus après génération, state persistence

**6. Doublon d'Information**
   - Même info affichée à plusieurs endroits
   - **À éviter** : Panel unique pour édition, pas de duplication centre/droite

**7. Friction Cognitive**
   - Trop de clics, pas de defaults, pas d'auto-apply
   - **À éviter** : Quick create, batch génération, auto-apply connexions

### Design Inspiration Strategy

**What to Adopt (Patterns à adopter directement) :**

1. **Layout 3 colonnes** (Articy Draft X)
   - Structure éprouvée, claire, scalable
   - **Application** : Conserver structure actuelle, optimiser espace canvas

2. **Progressive Disclosure** (Patterns généraux)
   - Barre 4 résultats compacte, labels en infobulle
   - **Application** : Mode compact par défaut, explicite au hover

3. **Quick Create / Batch Generation** (Articy Draft X)
   - "Générer tous les choix" comme first-class
   - **Application** : Bouton visible, pas caché, feedback progression

4. **Auto-apply Connections** (Patterns généraux)
   - Connexions appliquées automatiquement avec `auto_apply: true`
   - **Application** : Story 0.5.5, highlight automatique, pas de confirmation

5. **Inline Editing** (Patterns généraux)
   - Panel contextuel, pas de modal bloquante
   - **Application** : Panel droit pour édition, focus automatique

**What to Adapt (Patterns à adapter pour notre contexte) :**

1. **Hub-Based Branching** (Articy Draft X)
   - **Original** : Hubs comme nodes séparés pour branchement/merge
   - **Adaptation** : Barre 4 résultats comme "hub visuel" intégré (pas de node séparé)
   - **Raison** : Plus compact, moins de nodes dans le graphe

2. **Pins System** (Articy Draft X)
   - **Original** : Pins avec conditions/instructions attachées
   - **Adaptation** : Handles simples pour connexions, conditions dans panel édition
   - **Raison** : Simplifier visuellement, conditions dans panel (moins de clutter)

3. **Nested Flows** (Articy Draft X)
   - **Original** : Hiérarchie Flows → Dialogues → Fragments
   - **Adaptation** : Liste dialogues (gauche) + Canvas graphe (centre)
   - **Raison** : Structure plus plate, focus sur dialogue individuel

**What to Avoid (Anti-patterns à éviter) :**

1. **Spaghetti Connections**
   - Auto-layout intelligent, minimiser croisements
   - Routing propre (courbes, pas de chevauchements)

2. **Modal Overload**
   - Panel contextuel plutôt que modal pour édition
   - Modal uniquement pour génération (workflow principal)

3. **Perte de Contexte**
   - Auto-focus après génération
   - State persistence (zoom, sélection, panneau)

4. **Doublon d'Information**
   - Panel unique pour édition (droite)
   - Pas de duplication centre/droite

5. **Friction Cognitive**
   - Defaults intelligents, auto-apply, batch génération
   - Pas de clics inutiles, workflow fluide

## 2. Core User Experience

### 2.1 Defining Experience

**Expérience centrale globale :**
**"La génération de dialogues à embranchements par IA, pilotée par un auteur"**

**Expérience centrale spécifique au graphe :**
**"La visualisation et la génération de dialogues à embranchements par IA, pilotée par un auteur"**

**Description détaillée :**

DialogueGenerator permet aux auteurs de générer des dialogues complets (centaines de nœuds) en ≤1H grâce à l'assistance IA, tout en conservant le contrôle créatif total. L'expérience centrale est le workflow itératif **"Generate Next"** : prolonger un dialogue à partir d'un point précis du graphe, de façon rapide et fluide, sans perdre le contexte.

**Core loop (répétée en continu sur le même dialogue) :**
1. **Sélection** : Sélectionner un nœud "point d'ancrage" dans le graphe
2. **Génération** : Lancer **"Generate Next"** (via modal) — action unifiée pour tous les cas
3. **Ciblage** : Choisir la/les cibles PJ auxquelles le PNJ répond (1 choix spécifique / plusieurs / tous)
4. **Résultat** : Générer le(s) nœud(s) résultat(s) avec **auto-apply des connexions** (`targetNode`/`nextNode` remplis automatiquement)
5. **Sauvegarde** : Auto-save toutes les 2min (suspendu pendant génération)
6. **Focus** : **Auto-focus** : zoom/center automatique vers nouveau nœud généré (ou premier en batch)
7. **Rebouclage** : Reboucler (souvent sans re-sélectionner le dialogue)

**Action critique à rendre fluide :**
**"Generate Next for target(s)"** — générer la suite à partir d'une/plusieurs cibles PJ choisies, en gardant le focus et le contexte.

### 2.2 User Mental Model

**Comment les auteurs pensent à cette tâche :**

**Avant DialogueGenerator :**
- Création manuelle dans Word/Excel ou outils spécialisés (Articy Draft X)
- Processus lent et itératif (écrire chaque branche manuellement)
- Difficulté à visualiser la structure complète d'un dialogue complexe
- Risque de perdre le fil narratif dans les embranchements multiples

**Attentes avec DialogueGenerator :**
- **Contrôle créatif** : L'auteur garde le contrôle total, l'IA est un assistant
- **Itération rapide** : Générer, sélectionner, générer (suite) — workflow fluide
- **Visualisation claire** : Le graphe aide à comprendre la structure et naviguer
- **Qualité constante** : L'IA propose des dialogues pertinents et cohérents (80%+ acceptés sans modification)

**Modèle mental du workflow :**
- **Sélection contexte** → **Génération** → **Sélection résultat** → **Génération suite**
- L'auteur "pilote" l'IA en choisissant les cibles et validant les résultats
- Le graphe est à la fois un outil de **navigation** (voir où on en est) et d'**édition** (modifier directement)

**Points de confusion potentiels :**
- **Complexité du graphe** : Risque de se perdre dans un graphe avec 100+ nœuds
  - Solution : Auto-focus, minimap, navigation claire
- **Compréhension des suggestions IA** : L'auteur doit comprendre pourquoi l'IA propose tel dialogue
  - Solution : Preview contexte utilisé, feedback clair
- **Navigation entre branches** : Passer d'une branche à l'autre sans perdre le contexte
  - Solution : State persistence, auto-focus adaptatif

### 2.3 Success Criteria

**Critères de succès pour l'expérience centrale :**

**1. Qualité de génération (Priorité #1)**
- **Taux d'acceptation** : >80% nœuds générés acceptés sans re-génération
- **Taux de re-génération** : <20% (indicateur qualité inversé)
- **Cohérence narrative** : L'IA capture la voix du personnage et la lore sans expliciter
- **Critère PRD** : 80%+ nœuds acceptés sans modification

**2. Efficacité productive (Priorité #2)**
- **Temps génération 1 nœud** : <30s (prompt + LLM + validation)
- **Temps génération batch (3-8 nœuds)** : <2min
- **Temps production dialogue complet** : <4H (objectif initial), <2H (optimisé)
- **Critère PRD** : Production dialogue complet (100+ nœuds) en <4H

**3. Fluidité du workflow**
- **"Generate Next" unifié** : Toute friction dans "sélection → cible(s) → génération → auto-apply → save → auto-focus" est prioritaire
- **State persistence** : Le focus (dialogue, nœud, zoom, options) ne se perd pas entre itérations
- **Auto-apply connexions** : Connexions appliquées automatiquement (`auto_apply: true`)
- **Zero data loss** : Auto-save 2min (suspendu pendant génération), session recovery

**4. Contrôle créatif**
- **L'auteur pilote** : Ratio contrôle auteur / suggestions IA = 70/30 (auteur décide, IA suggère)
- **Preview claire** : L'auteur sait toujours *à quelle(s) cible(s) PJ* le PNJ répond, avant de générer
- **Retry facile** : Re-génération simple si résultat non satisfaisant
- **Édition manuelle** : Possibilité de créer/éditer des nœuds sans IA

**5. Visualisation efficace**
- **Graphe lisible** : Graphe 500+ nœuds : rendering <1s (PRD NFR-P1)
- **Navigation claire** : Auto-focus, minimap, zoom/pan fluides
- **Structure visible** : L'auteur comprend la structure du dialogue d'un coup d'œil

**Indicateurs de succès utilisateur :**
- **"Ça fonctionne"** : L'auteur dit "c'est fluide" ou "je produis en 1H ce qui me prenait une semaine"
- **Concentration & Flow** : L'auteur entre dans un état de concentration profonde où l'outil disparaît
- **Confiance** : L'auteur itère rapidement sans craindre de perdre le contrôle ou les données
- **Satisfaction IA** : "L'IA a capturé la voix du personnage !" (émotion ciblée PRD)

### 2.4 Novel UX Patterns

**Patterns établis (familiers, pas d'apprentissage nécessaire) :**

1. **Éditeur de graphe** (comme Articy Draft X, Miro)
   - Nodes, edges, zoom/pan, minimap
   - Familiarité : Les auteurs connaissent les éditeurs de graphes

2. **Génération IA** (comme ChatGPT, Midjourney)
   - Prompt → Génération → Sélection résultat
   - Familiarité : Les auteurs connaissent les outils IA

3. **Workflow itératif** (générer → sélectionner → générer)
   - Pattern classique d'outils créatifs
   - Familiarité : Workflow naturel pour les auteurs

**Patterns novateurs (nécessitent un apprentissage léger) :**

1. **Barre 4 résultats (hub visuel pour tests)**
   - **Nouveauté** : Visualisation compacte des 4 résultats de test (échec critique, échec, réussite, réussite critique)
   - **Apprentissage** : Légère courbe d'apprentissage (labels en infobulle au hover)
   - **Métaphore** : Barre de résultats comme "hub de branchement" (similaire aux hubs Articy Draft X)
   - **Solution** : Progressive disclosure (ronds colorés seulement, labels au hover)

2. **Génération batch ("générer tous les choix")**
   - **Nouveauté** : Générer plusieurs nœuds (3-8) en une passe
   - **Apprentissage** : Minimal (bouton visible, feedback progression)
   - **Métaphore** : "Générer tous" comme action first-class (pas cachée)
   - **Solution** : Bouton visible, preview "Générer pour 3 choix" vs "Générer pour tous (5 choix)"

3. **Auto-apply connections (connexions automatiques)**
   - **Nouveauté** : Connexions appliquées automatiquement sans confirmation
   - **Apprentissage** : Minimal (highlight automatique, feedback clair)
   - **Métaphore** : "L'outil fait le travail pour moi" (trust)
   - **Solution** : Highlight automatique, feedback "X déjà connectés / Y générés"

**Stratégie d'enseignement :**
- **Onboarding léger** : Tooltips contextuels, pas de tutoriel lourd
- **Feedback immédiat** : L'auteur voit immédiatement le résultat (auto-apply, highlight)
- **Découverte progressive** : Patterns novateurs révélés au besoin (hover, contexte)

### 2.5 Experience Mechanics

**Décomposition étape par étape du workflow "Generate Next" :**

**1. Initiation**

**Comment l'auteur démarre :**
- **Sélection contexte** : Sélectionner personnages, lieux, thèmes dans le panneau gauche
- **Sélection dialogue** : Cliquer sur un dialogue dans la liste (ou rester sur le même)
- **Sélection nœud** : Cliquer sur un nœud dans le graphe (point d'ancrage)

**Ce qui invite à commencer :**
- Nœud avec choix PJ non développés (handles visibles, feedback visuel)
- Bouton "Generate Next" visible sur le nœud sélectionné
- Modal de génération s'ouvre avec options claires

**2. Interaction**

**Ce que l'auteur fait :**
- **Choisir cible(s) PJ** : Sélectionner 1 choix spécifique / plusieurs / tous dans la modal
- **Configurer génération** : Instructions optionnelles (tone, style, theme)
- **Lancer génération** : Cliquer "Générer" (ou "Générer tous" pour batch)

**Comment le système répond :**
- **Modal progression** : Affiche progression (streaming visible)
- **Génération en temps réel** : Streaming du texte généré (feedback immédiat)
- **Preview avant validation** : Affiche le nœud généré avant acceptation
- **Auto-apply connexions** : Connexions appliquées automatiquement (`targetNode`/`nextNode`)

**3. Feedback**

**Comment l'auteur sait qu'il progresse :**
- **Progression visible** : Modal affiche "Génération en cours... 2/5 nœuds"
- **Graphe qui grandit** : Nouveaux nœuds apparaissent dans le graphe
- **Indicateur de complétude** : Feedback "X choix connectés / Y restants"
- **Qualité visible** : Nœud généré affiché avec preview

**Que se passe-t-il en cas d'erreur :**
- **Retry facile** : Bouton "Re-générer" visible, pas de friction
- **Message clair** : "Génération échouée : [raison]" avec action suggérée
- **Fallback automatique** : Multi-provider LLM (OpenAI → Anthropic si échec)
- **Statut toujours visible** : Indicateur de génération jamais caché

**4. Completion**

**Comment l'auteur sait qu'il a terminé :**
- **Tous les choix connectés** : Feedback "Tous les choix ont des réponses"
- **Graphe "complet"** : Validation structure (pas d'orphans, cycles détectés)
- **Export Unity réussi** : JSON validé, 0 erreurs

**Qu'est-ce qui vient après :**
- **Auto-focus** : Zoom/center automatique vers nouveau nœud généré
- **Rebouclage** : L'auteur peut immédiatement générer la suite (souvent sans re-sélectionner)
- **Édition optionnelle** : L'auteur peut éditer le nœud généré si besoin

## Visual Design Foundation

### Color System

**Mode sombre comme base (déjà en place)**

Le système de couleurs actuel est optimisé pour le mode sombre, idéal pour un outil de travail intensif (concentration, longues sessions).

**Palette de couleurs sémantiques :**

**Backgrounds (hiérarchie visuelle) :**
- `primary` : `#1a1a1a` - Fond principal (canvas, body)
- `secondary` : `#242424` - Fond secondaire (panneaux, containers)
- `tertiary` : `#2d2d2d` - Fond tertiaire (inputs, éléments interactifs)
- `panel` : `#2a2a2a` - Fond panneaux (graph canvas)
- `panelHeader` : `#333333` - En-têtes de panneaux

**Text (hiérarchie de contenu) :**
- `primary` : `rgba(255, 255, 255, 0.95)` - Texte principal (titres, contenu important)
- `secondary` : `rgba(255, 255, 255, 0.75)` - Texte secondaire (descriptions, métadonnées)
- `tertiary` : `rgba(255, 255, 255, 0.55)` - Texte tertiaire (labels, hints)
- `inverse` : `#213547` - Texte sur fond clair (rare, pour contrastes)

**Borders (séparation et focus) :**
- `primary` : `#505050` - Bordures standard
- `secondary` : `#5a5a5a` - Bordures secondaires
- `focus` : `#646cff` - Bordures focus (accent bleu/violet)

**États sémantiques :**
- `error` : `#ff6b6b` (texte) / `#3a1a1a` (fond) / `#ff4444` (bordure)
- `success` : `#51cf66` (texte) / `#1a3a2a` (fond)
- `info` : `#74c0fc` (texte) / `#1a2a3a` (fond)
- `warning` : `#ffd43b` (texte) / `#3a3a1a` (fond)
- `selected` : `#74c0fc` (texte) / `#1a3a5a` (fond)

**Boutons :**
- `default` : `#333333` (fond) / `rgba(255, 255, 255, 0.87)` (texte)
- `primary` : `#007bff` (fond) / `#ffffff` (texte)
- `selected` : `#1a3a5a` (fond) / `#ffffff` (texte) / `#007bff` (bordure)

**Couleurs spécialisées (Graph Editor) :**
- Dialogue Node : `#4A90E2` (bleu)
- Test Node : `#F5A623` (orange)
- End Node : `#B8B8B8` (gris)
- Barre 4 résultats : Rouge → Jaune → Vert → Bleu (échec critique → réussite critique)

**Accessibilité :**
- Contraste minimum WCAG AA : Tous les textes respectent 4.5:1 minimum
- Focus visible : `#646cff` avec outline `rgba(100, 108, 255, 0.3)`
- États hover : Feedback visuel clair (background `#333333`)

### Typography System

**Recommandation : System Font Stack (performance + familiarité)**

Pour un outil de travail, privilégier les fonts système pour :
- Performance (pas de chargement de font externe)
- Familiarité (fonts natives du système)
- Lisibilité optimale (optimisées pour l'écran)

**Font Stack :**
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
```

**Type Scale (hiérarchie claire) :**

**Headings :**
- `h1` : `1.5rem` (24px) / `font-weight: 700` - Titres principaux (dialogue name, section headers)
- `h2` : `1.2rem` (19.2px) / `font-weight: 600` - Sous-titres (panel headers)
- `h3` : `1rem` (16px) / `font-weight: 600` - Titres de sections

**Body Text :**
- `body` : `0.9rem` (14.4px) / `font-weight: 400` - Texte principal (dialogue content, descriptions)
- `small` : `0.85rem` (13.6px) / `font-weight: 400` - Texte secondaire (labels, métadonnées)
- `tiny` : `0.75rem` (12px) / `font-weight: 400` - Texte tertiaire (hints, tooltips)

**Special Cases :**
- `large` : `1rem` (16px) - Pour éléments importants (boutons, inputs)
- `monospace` : `'Courier New', 'Monaco', monospace` - Pour code, IDs, JSON

**Line Heights (lisibilité) :**
- Headings : `1.2` (compact, hiérarchie claire)
- Body : `1.5` (confortable pour lecture longue)
- Small : `1.4` (équilibré pour texte dense)

**Font Weights :**
- `400` (normal) - Texte standard
- `500` (medium) - Emphase légère
- `600` (semibold) - Titres, labels importants
- `700` (bold) - Titres principaux, éléments critiques

**Usage par contexte :**
- **Graph Nodes** : `0.9rem` body pour dialogue, `0.85rem` small pour speaker
- **Panel Headers** : `1rem` h3 avec `font-weight: 600`
- **Inputs** : `0.9rem` body pour cohérence
- **Labels** : `0.85rem` small avec `font-weight: 600`
- **Tooltips** : `0.75rem` tiny

### Spacing & Layout Foundation

**Recommandation : Système basé sur 4px (granularité fine)**

Système 4px pour flexibilité et cohérence :
- Base : `4px` (0.25rem)
- Scale : 4, 8, 12, 16, 20, 24, 32, 40, 48, 64px

**Spacing Scale :**

**Micro (éléments proches) :**
- `xs` : `4px` (0.25rem) - Espacement minimal (icône ↔ texte, éléments inline)
- `sm` : `8px` (0.5rem) - Espacement petit (éléments liés, padding inputs)

**Standard (éléments normaux) :**
- `md` : `12px` (0.75rem) - Espacement moyen (gap entre éléments de formulaire)
- `base` : `16px` (1rem) - Espacement de base (marges standard, padding panels)
- `lg` : `20px` (1.25rem) - Espacement large (sections, groupes d'éléments)

**Macro (séparation majeure) :**
- `xl` : `24px` (1.5rem) - Espacement extra-large (sections principales)
- `2xl` : `32px` (2rem) - Espacement très large (panels, containers)
- `3xl` : `48px` (3rem) - Espacement maximal (séparation majeure)

**Layout Principles :**

**1. Densité optimisée (outil de travail)**
- Espacement modéré : Pas trop dense (fatigue visuelle), pas trop aéré (perte d'espace)
- Focus sur contenu : Espacement sert la hiérarchie, pas la décoration
- **Application** : Panels avec padding `16px`, gap entre éléments `12px`

**2. Hiérarchie visuelle claire**
- Groupement logique : Éléments liés proches (`8px`), groupes séparés (`16px`)
- Sections distinctes : Séparation claire entre sections (`24px`)
- **Application** : Formulaires avec gap `12px` entre champs, `24px` entre sections

**3. Responsive aux interactions**
- Hover states : Padding suffisant pour zones cliquables (`8px` minimum)
- Focus states : Outline visible (`2px` avec `#646cff`)
- **Application** : Boutons avec padding `8px 16px`, inputs avec padding `8px 12px`

**4. Contraintes d'espace (Graph Editor)**
- Espacement compact : Maximiser l'espace canvas (panels `16px` padding)
- Redimensionnable : Panels collapsibles, mode plein écran
- **Application** : Panels latéraux min `100px`, padding interne `12px`

**Grid System :**

Pas de grid system strict nécessaire (layout flex/panels), mais principes :
- Alignement : Snap to grid `15px` pour nodes ReactFlow (déjà en place)
- Cohérence : Multiples de 4px pour tous les espacements
- **Application** : Canvas avec grid `15px` (proche de `16px` base), nodes alignés

**Component Spacing :**

**Panels :**
- Padding interne : `16px` (base)
- Gap entre sections : `24px` (xl)
- Gap entre éléments : `12px` (md)

**Forms :**
- Gap entre champs : `12px` (md)
- Gap entre groupes : `20px` (lg)
- Padding inputs : `8px 12px` (sm horizontal, md vertical)

**Buttons :**
- Padding : `8px 16px` (sm horizontal, base vertical)
- Gap entre boutons : `8px` (sm)
- Margin groupes : `16px` (base)

**Graph Nodes :**
- Padding interne : `12px` (md)
- Gap contenu : `8px` (sm)
- Espacement entre nodes : Auto (ReactFlow layout)

### Accessibility Considerations

**Contraste (WCAG AA minimum) :**
- Text primary (`rgba(255, 255, 255, 0.95)`) sur background primary (`#1a1a1a`) : **Ratio 12.6:1** ✅
- Text secondary (`rgba(255, 255, 255, 0.75)`) sur background secondary (`#242424`) : **Ratio 7.2:1** ✅
- Text tertiary (`rgba(255, 255, 255, 0.55)`) sur background tertiary (`#2d2d2d`) : **Ratio 4.8:1** ✅
- Tous les textes respectent WCAG AA (4.5:1) et la plupart WCAG AAA (7:1)

**Focus Management :**
- Focus visible : Outline `2px solid #646cff` avec `rgba(100, 108, 255, 0.3)` (déjà en place)
- Navigation clavier : Raccourcis clavier documentés (`useKeyboardShortcuts`)
- Skip links : Non nécessaire (application SPA, pas de navigation complexe)

**Tailles de texte :**
- Minimum : `0.75rem` (12px) pour tooltips (acceptable, usage limité)
- Standard : `0.9rem` (14.4px) pour body (confortable)
- Headings : `1rem`+ (16px+) pour hiérarchie claire

**Couleurs et états :**
- Pas de dépendance à la couleur seule : Icônes, formes, labels textuels
- États visuels clairs : Hover, focus, selected avec feedback visuel
- États sémantiques : Error, success, warning avec couleurs + icônes

**Interactions :**
- Zones cliquables : Minimum `44x44px` (touch targets)
- Feedback immédiat : Hover, click, focus states visibles
- Retry facile : Actions destructives avec confirmation

**Mécaniques spécifiques par type de génération :**

**Génération pour choix spécifique :**
- Initiation : Clic sur handle de choix PJ
- Interaction : Sélection choix → Génération
- Feedback : 1 nœud généré, connexion auto-appliquée
- Completion : Nœud visible, auto-focus

**Génération batch (tous les choix) :**
- Initiation : Clic "Générer tous les choix"
- Interaction : Sélection "Générer pour tous (5 choix)" → Génération batch
- Feedback : Progression "2/5 nœuds générés", streaming visible
- Completion : 5 nœuds générés, connexions auto-appliquées, auto-focus premier nœud

**Génération nextNode (navigation linéaire) :**
- Initiation : Clic "Generate Next" sur nœud terminal
- Interaction : Génération nœud suivant (pas de choix PJ)
- Feedback : 1 nœud généré, connexion `nextNode` auto-appliquée
- Completion : Nœud visible, auto-focus

### Validation Strategy

**Métriques de succès à mesurer :**

1. **Performance & Efficacité**
   - Temps pour générer un dialogue complet (avant/après implémentation)
   - Nombre de clics/interactions nécessaires pour compléter un workflow standard
   - Taux d'erreur (connexions manquantes, nodes orphelins, validations échouées)

2. **Satisfaction Utilisateur**
   - Survey post-usage (NPS, facilité d'utilisation, satisfaction globale)
   - Feedback qualitatif sur les patterns spécifiques (barre 4 résultats, batch génération, auto-apply)
   - Fréquence d'utilisation des features (batch vs génération individuelle)

3. **Adoption des Patterns**
   - Validation que les patterns Articy Draft X sont transférables à notre contexte
   - Identification des patterns qui nécessitent adaptation après tests utilisateurs
   - Confirmation que les simplifications (pins system, nested flows) ne limitent pas la fonctionnalité

**Approche de validation :**

1. **Prototype rapide** : Valider l'UX de la barre 4 résultats avec un prototype interactif avant implémentation complète
2. **Tests utilisateurs** : Sessions avec 3-5 utilisateurs cibles pour valider les patterns "What to Adopt"
3. **Métriques continues** : Tracking des métriques post-déploiement pour itérer rapidement

**Priorisation d'implémentation :**

1. **Phase 1 - Patterns "What to Adopt" (moins risqués)**
   - Layout 3 colonnes (déjà en place, optimiser)
   - Progressive Disclosure (barre 4 résultats compacte)
   - Quick Create / Batch Generation (first-class)
   - Auto-apply Connections (Story 0.5.5)
   - Inline Editing (panel contextuel)

2. **Phase 2 - Patterns "What to Adapt" (après validation Phase 1)**
   - Hub-Based Branching (barre 4 résultats comme hub visuel)
   - Pins System simplifié (handles simples, conditions dans panel)
   - Nested Flows adaptés (structure plate, focus dialogue individuel)

3. **Phase 3 - Anti-patterns mitigation (itérations continues)**
   - Auto-layout intelligent (minimiser croisements)
   - State persistence (zoom, sélection, panneau)
   - Validation structure (détecter orphans, cycles)

## Design System Foundation

### 1.1 Design System Choice

**Custom Design System** - Système de design personnalisé déjà en place, à structurer et documenter davantage.

### Rationale for Selection

**1. Cohérence avec l'existant**
   - Le système de thème custom (`theme.ts`) est déjà fonctionnel et aligné avec l'identité visuelle actuelle
   - Les composants custom (ResizablePanels, Tabs, etc.) sont intégrés dans le workflow
   - Migration vers une bibliothèque externe nécessiterait une refonte majeure, incompatible avec l'approche brownfield

**2. Contrôle total sur l'expérience**
   - Adaptation fine aux contraintes spécifiques (graphes complexes, espace limité, mode sombre)
   - Personnalisation complète des composants pour les besoins uniques (barre 4 résultats, nodes ReactFlow custom)
   - Pas de dépendance à des patterns externes qui pourraient limiter la flexibilité

**3. Itération progressive**
   - Approche brownfield : améliorer l'existant sans casser le workflow
   - Structuration progressive des design tokens et composants
   - Pas de migration risquée, évolution continue

**4. Équipe et maintenance**
   - Petite équipe (Marc + Mathieu) : maintenance maîtrisable d'un système custom
   - Besoin de différenciation : outil spécialisé nécessite une identité visuelle unique
   - Pas de contrainte de vitesse de développement (timeline itérative)

### Implementation Approach

**Phase 1 : Structuration des Design Tokens**

1. **Organisation du fichier `theme.ts`**
   - Séparer les tokens par catégories (couleurs, espacements, typographie, ombres, animations)
   - Créer des tokens sémantiques (primary, secondary, error, success) plutôt que des valeurs brutes
   - Documenter chaque token avec son usage et ses variantes

2. **Extension des tokens existants**
   - Ajouter tokens pour espacements (spacing scale : 4px, 8px, 12px, 16px, 24px, 32px, 48px)
   - Définir typographie (font families, sizes, weights, line heights)
   - Ajouter tokens pour animations (durations, easings)
   - Tokens pour z-index (layers : modal, dropdown, tooltip, base)

3. **Mode sombre comme base**
   - Le thème actuel est optimisé pour le mode sombre (fond #1a1a1a)
   - Conserver cette approche, pas besoin de mode clair pour l'instant
   - Tokens de couleur avec variantes (hover, active, disabled)

**Phase 2 : Bibliothèque de Composants Réutilisables**

1. **Composants de base**
   - Button (variants : default, primary, secondary, danger)
   - Input (text, textarea, select, checkbox, radio)
   - Modal / Dialog (pour génération, confirmations)
   - Tooltip (pour infobulles barre 4 résultats)
   - Toast / Notification (feedback actions)

2. **Composants layout**
   - ResizablePanels (déjà existant, documenter)
   - Tabs (déjà existant, documenter)
   - Card / Panel (conteneurs avec header, body, footer)
   - Divider / Separator

3. **Composants spécialisés**
   - GraphNode (DialogueNode, TestNode, EndNode) - déjà custom pour ReactFlow
   - Barre 4 résultats (hub visuel custom)
   - ContextSelector (sélecteur de contexte)
   - NodeEditorPanel (panel d'édition contextuel)

**Phase 3 : Documentation et Guidelines**

1. **Style Guide**
   - Documenter les patterns de couleur (usage, contrastes, accessibilité)
   - Guidelines d'espacement (marges, paddings, gaps)
   - Typographie (hiérarchie, lisibilité)

2. **Component Library**
   - Storybook ou documentation markdown pour chaque composant
   - Exemples d'usage, props, variantes
   - Do's and Don'ts pour chaque composant

3. **Design Patterns**
   - Patterns d'interaction (hover, selection, focus)
   - Patterns de feedback (loading, success, error)
   - Patterns de navigation (breadcrumbs, tabs, panels)

### Customization Strategy

**1. Design Tokens comme source de vérité**
   - Tous les styles dérivent des tokens (pas de valeurs hardcodées)
   - Tokens accessibles via `theme` object (déjà en place)
   - Facilite les changements globaux (ex: ajuster toutes les couleurs primaires)

**2. Composants comme briques réutilisables**
   - Composants de base pour 80% des cas d'usage
   - Composants spécialisés pour les 20% (graphe, génération IA)
   - Props cohérentes entre composants similaires

**3. Extension progressive**
   - Ajouter de nouveaux tokens/composants au besoin
   - Pas de sur-engineering : créer seulement ce qui est nécessaire
   - Itérer basé sur les besoins réels (stories, feedback utilisateurs)

**4. Intégration avec ReactFlow**
   - ReactFlow a son propre système de styling (nodes, edges, controls)
   - Adapter les tokens du design system pour ReactFlow (couleurs, espacements)
   - Nodes custom utilisent les tokens du design system (couleurs, typographie)

**5. Accessibilité**
   - Contraste suffisant (WCAG AA minimum)
   - Focus visible (outline avec `theme.border.focus`)
   - Navigation clavier (déjà en place via `useKeyboardShortcuts`)
   - Labels ARIA pour composants interactifs

## Design Direction Decision

### Design Directions Explored

**Contexte brownfield :** L'interface Graph Editor existe déjà et fonctionne. La direction de design documente l'état actuel + améliorations proposées (approche itérative, pas de refonte complète).

**Direction actuelle :** Mode sombre professionnel, layout 3 colonnes, densité optimisée pour outil de travail, composants custom.

### Chosen Direction

**Direction : Itération sur l'existant avec améliorations ciblées**

**Style visuel :**
- Mode sombre professionnel (fond #1a1a1a) - conservé
- Densité optimisée (outil de travail, pas trop dense, pas trop aéré)
- Layout 3 colonnes (Contexte/Liste | Canvas | Détails) - conservé
- Composants custom (pas de bibliothèque externe) - conservé

**Améliorations proposées :**
1. Barre 4 résultats compacte (hub visuel pour tests) - nouveau pattern
2. Mode plein écran pour canvas (raccourci discret) - optimisation espace
3. Panels collapsibles optimisés - optimisation espace
4. Progressive disclosure (labels en infobulle) - réduction clutter

### Design Rationale

**Pourquoi itérer sur l'existant :**
- Interface fonctionnelle : L'outil est utilisé en production, pas de refonte risquée
- Workflow établi : Les utilisateurs connaissent l'interface, éviter disruption
- Approche pragmatique : Améliorer les points de friction identifiés, pas tout refaire
- Timeline réaliste : Itérations progressives, pas de big bang

**Pourquoi ces améliorations spécifiques :**
- Barre 4 résultats : Nouvelle fonctionnalité (Story 0-10), nécessite nouveau pattern visuel
- Mode plein écran : Contrainte d'espace identifiée (panneaux latéraux réduisent canvas)
- Progressive disclosure : Réduire clutter visuel (labels barre 4 résultats)
- Panels optimisés : Maximiser espace canvas sans perdre fonctionnalité

### Implementation Approach

**Architecture complète des interfaces Graph Editor :**

**1. Layout Principal (GraphEditor.tsx)**

**Structure 3 colonnes :**
- **Panneau gauche** : `UnityDialogueList` (width: `clamp(260px, 22vw, 340px)`, min: `240px`)
  - Liste des dialogues Unity avec recherche et tri
  - Sélection dialogue → charge dans graphe
  - Border right : `1px solid ${theme.border.primary}`
  - Background : `theme.background.panel`

- **Panneau central** : GraphCanvas + Toolbar
  - **Toolbar (en-tête)** : Titre dialogue, badge validation, auto-save, boutons actions
  - **GraphCanvas** : ReactFlow avec nodes, edges, controls, minimap
  - Background : `theme.background.panel`
  - Flex: 1 (prend tout l'espace restant)

- **Panneau droit** : `NodeEditorPanel` (panel latéral contextuel)
  - S'affiche quand nœud sélectionné
  - Édition propriétés nœud (speaker, line, choices, etc.)
  - Width : Variable (redimensionnable via ResizablePanels si intégré)

**2. Panneau Gauche : UnityDialogueList**

**Composants :**
- **Barre de recherche** : Input avec raccourci `/` pour focus
- **Tri** : Select (name-asc, name-desc, date-asc, date-desc)
- **Liste scrollable** : `UnityDialogueItem` pour chaque dialogue
- **États** : Loading, error (avec retry), empty

**UnityDialogueItem :**
- Affichage : Titre (filename formaté), title (si différent), size, date modifiée
- Sélection : Background `theme.state.selected.background` si sélectionné
- Hover : Background `theme.state.hover.background`
- Highlight : Recherche met en évidence texte correspondant

**3. Panneau Central : GraphCanvas + Toolbar**

**Toolbar (en-tête) :**
- **Titre** : "Éditeur de Graphe - {dialogue.title}" + filename (secondary)
- **Badge validation** : 
  - Vert (✓ Graphe valide) si aucune erreur
  - Rouge (✗ X erreur(s)) si erreurs
  - Jaune (⚠ X avertissement(s)) si warnings uniquement
  - Clic → zoom sur erreurs
- **SaveStatusIndicator** : Auto-save draft (saved/saving/unsaved/error)
- **Boutons actions** :
  - "✓ Valider" : Validation graphe
  - Select layout direction (TB/LR/BT/RL)
  - "🔄 Auto-layout" : Réorganiser graphe
  - "✨ Générer" : Ouvrir AIGenerationPanel (si nœud sélectionné)
  - "📥 Exporter" : Ouvrir dialog format export (PNG/SVG)
  - "💾 Sauvegarder" : Export vers Unity

**GraphCanvas (ReactFlow) :**
- **Background** : Grid `15px` gap, opacity `0.2`
- **Controls** : Zoom, pan, fit view (ReactFlow native)
- **MiniMap** : Vue d'ensemble graphe (bottom-right)
- **Nodes** : DialogueNode (bleu #4A90E2), TestNode (orange #F5A623), EndNode (gris #B8B8B8)
- **Edges** : Smoothstep, stroke `theme.text.secondary`, width `2px`
- **Interactions** : Click node → sélection, drag → reposition, connect handles → créer edge

**4. Panel Overlay : AIGenerationPanel**

**Modal overlay** (centré, z-index élevé) :
- **Header** : Titre "Générer la suite avec l'IA" + bouton fermer
- **Contexte parent** : Affiche speaker + line (tronqué 150 chars) du nœud parent
- **Instructions utilisateur** : Textarea pour instructions optionnelles
- **Mode génération** : Toggle "Suite (nextNode)" / "Branche alternative (choice)"
- **Sélection choix** : 
  - Liste choix disponibles avec preview texte
  - Indicateur "déjà connecté" (grisé, non cliquable)
  - Sélection unique ou "Générer pour tous les choix" (batch)
- **Options avancées** :
  - Sélecteur modèle LLM
  - Tags narratifs (tension, humour, dramatique, etc.)
  - MaxChoices (limite génération batch)
- **Bouton générer** : Lance génération avec progression visible
- **Budget block modal** : ConfirmDialog si budget dépassé

**5. Panel Latéral : NodeEditorPanel**

**Panel contextuel** (s'affiche quand nœud sélectionné) :
- **Header** : Type nœud (Dialogue/Test/End) + bouton fermer
- **Formulaires selon type** :
  - **DialogueNode** : Speaker, Line (textarea), Choices (array), nextNode
  - **TestNode** : Test, Line, successNode, failureNode (→ 4 résultats Story 0-10)
  - **EndNode** : Aucun champ (nœud terminal)
- **ChoiceEditor** : Pour chaque choix
  - Text (textarea)
  - targetNode (input monospace)
  - Condition (input monospace)
  - Test (input monospace)
  - influenceDelta, respectDelta (number inputs)
  - traitRequirements (textarea JSON)
  - Bouton "✨ Générer" (si non connecté)
  - Bouton "🗑️ Supprimer"
- **Actions** :
  - Bouton "Sauvegarder" : Update nœud
  - Bouton "Supprimer nœud" : Delete avec confirmation
  - Bouton "Générer depuis nœud" : Ouvrir AIGenerationPanel

**6. Modals/Dialogs**

**ConfirmDialog (restauration draft) :**
- Message : "Un brouillon plus récent que le fichier a été trouvé..."
- Actions : "Restaurer" / "Ignorer" / "Supprimer brouillon"

**Dialog export format :**
- Sélection format : PNG ou SVG
- Boutons : "Exporter PNG" / "Exporter SVG" / "Annuler"

**ConfirmDialog (budget block) :**
- Message : Budget dépassé (détails dans `budgetBlockMessage`)
- Actions : "OK" (ferme modal)

**7. Validation Errors Panel (Overlay)**

**Panel overlay** (bottom-left, z-index 1000) :
- **Header** : Icône + "X erreur(s)" ou "X avertissement(s)"
- **Groupement par type** :
  - Orphan nodes (🔗)
  - Broken references (🔴)
  - Empty nodes (⚪)
  - Missing tests (❓)
  - Unreachable nodes (📍)
  - Cycles detected (🔄)
- **Liste erreurs** : 
  - Format : `[node_id] message`
  - Clic → zoom sur nœud problématique
  - Hover → highlight
- **Filtrage** : Cycles intentionnels masqués si marqués `intentionalCycles`

**8. Nodes ReactFlow (Custom)**

**DialogueNode :**
- **Shape** : Rectangle arrondi
- **Couleur** : Bleu #4A90E2
- **Contenu** : Speaker (titre), Line (dialogue tronqué), Choices count
- **Handles** : 1 output handle (droite) pour connexions
- **Interactions** : Click → sélection, double-click → ouvrir AIGenerationPanel

**TestNode :**
- **Shape** : Rond orange
- **Couleur** : Orange #F5A623
- **Contenu** : Test (attribut+compétence:DD), Line (dialogue optionnel)
- **Handles** : 2 output handles (success/failure) → **4 handles (Story 0-10)**
- **Interactions** : Click → sélection, double-click → ouvrir AIGenerationPanel

**EndNode :**
- **Shape** : Rectangle arrondi gris
- **Couleur** : Gris #B8B8B8
- **Contenu** : "Fin du dialogue"
- **Handles** : Aucun (nœud terminal)

**9. ChoiceEditor (dans NodeEditorPanel)**

**Composant inline** pour éditer un choix :
- **Header** : "Choix #X" + indicateur "(connecté)" si `targetNode` rempli
- **Champs** :
  - Text (textarea, required)
  - targetNode (input monospace)
  - Condition (input monospace, format: FLAG_NAME, NOT FLAG_NAME, expression)
  - Test (input monospace, format: Attribut+Compétence:DD)
  - influenceDelta, respectDelta (number inputs)
  - traitRequirements (textarea JSON, format: `[{"trait": "Nom", "minValue": 5}]`)
- **Actions** :
  - Bouton "✨ Générer" (si non connecté)
  - Bouton "🗑️ Supprimer"

**10. États et Interactions**

**États visuels :**
- **Sélection** : Nœud sélectionné → highlight, NodeEditorPanel ouvert
- **Hover** : Nodes, edges, boutons → feedback visuel
- **Loading** : "Chargement du graphe..." (centré)
- **Empty** : "Sélectionnez un dialogue Unity" (centré, message guidant)

**Interactions clavier :**
- `/` : Focus recherche (UnityDialogueList)
- `Ctrl+S` : Sauvegarder dialogue
- `Escape` : Fermer modals/panels
- Raccourcis personnalisés via `useKeyboardShortcuts`

**Workflow principal :**
1. Sélection dialogue (liste gauche) → Charge dans graphe
2. Click nœud → Sélection + NodeEditorPanel ouvert
3. Double-click nœud → AIGenerationPanel ouvert
4. Génération → Nœuds créés + auto-apply connexions + auto-focus
5. Édition → NodeEditorPanel → Sauvegarder
6. Validation → Badge + Errors panel (si erreurs)

**Améliorations UX proposées :**

**1. Barre 4 résultats (nouveau pattern)**
- **Visualisation** : DialogueNode → Fil → Barre compacte (4 ronds colorés) → 4 DialogueNodes
- **Couleurs** : Rouge → Jaune → Vert → Bleu (échec critique → réussite critique)
- **Labels** : Infobulle au hover (pas de labels visibles sur barre)
- **Implementation** : Node ReactFlow custom ou overlay SVG

**2. Mode plein écran**
- **Raccourci** : `F11` ou bouton discret dans toolbar
- **Comportement** : Masque panneaux latéraux, canvas prend 100% viewport
- **Exit** : `F11` ou `Escape` pour revenir layout normal

**3. Progressive disclosure**
- **Barre 4 résultats** : Ronds seulement, labels en tooltip
- **Nodes** : Contenu tronqué, détails dans NodeEditorPanel
- **Choices** : Preview dans ChoiceEditor, détails au expand

**4. Panels optimisés**
- **Collapsibles** : Panneaux gauche/droite collapsibles (min ~100px)
- **Redimensionnables** : ResizablePanels pour ajuster largeurs
- **State persistence** : Sauvegarder tailles panels dans localStorage
