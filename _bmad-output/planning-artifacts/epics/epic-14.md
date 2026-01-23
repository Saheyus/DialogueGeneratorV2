## Epic 14: Accessibilité

Les utilisateurs peuvent naviguer l'éditeur de graphe entièrement au clavier avec indicateurs de focus visibles. Le système supporte personnalisation contraste couleurs (WCAG AA), et lecteurs d'écran avec ARIA labels (V2.0+).

**FRs covered:** FR114-117 (navigation clavier, indicateurs focus, contraste couleurs, support lecteurs d'écran)

**NFRs covered:** NFR-A1 (Keyboard Navigation 100%), NFR-A2 (Color Contrast WCAG AA), NFR-A3 (Screen Reader Support V2.0+)

**Valeur utilisateur:** Rendre l'application accessible à tous les utilisateurs, y compris ceux utilisant le clavier uniquement ou des technologies d'assistance, garantissant une expérience inclusive et conforme aux standards d'accessibilité.

**Dépendances:** Epic 2 (éditeur graphe), Epic 12 (raccourcis clavier)

---

## ⚠️ GARDE-FOUS - Vérification de l'Existant (Scrum Master)

**OBLIGATOIRE avant création de chaque story de cet epic :**

### Checklist de Vérification

1. **Fichiers mentionnés dans les stories :**
   - [ ] Vérifier existence avec `glob_file_search` ou `grep`
   - [ ] Vérifier chemins corrects (ex: `core/llm/` vs `services/llm/`)
   - [ ] Si existe : **DÉCISION** - Étendre ou remplacer ? (documenter dans story)

2. **Composants/Services similaires :**
   - [ ] Rechercher composants React similaires (`codebase_search` dans `frontend/src/components/`)
   - [ ] Rechercher stores Zustand similaires (`codebase_search` dans `frontend/src/store/`)
   - [ ] Rechercher services Python similaires (`codebase_search` dans `services/`, `core/`)
   - [ ] Si similaire existe : **DÉCISION** - Réutiliser ou créer nouveau ? (documenter dans story)

3. **Endpoints API :**
   - [ ] Vérifier namespace cohérent (`/api/v1/dialogues/*` vs autres)
   - [ ] Vérifier si endpoint similaire existe (`grep` dans `api/routers/`)
   - [ ] Si endpoint similaire : **DÉCISION** - Étendre ou créer nouveau ? (documenter dans story)

4. **Patterns existants :**
   - [ ] Vérifier patterns Zustand (immutable updates, structure stores)
   - [ ] Vérifier patterns FastAPI (routers, dependencies, schemas)
   - [ ] Vérifier patterns React (composants, hooks, modals)
   - [ ] Respecter conventions de nommage et structure dossiers

5. **Documentation des décisions :**
   - Si remplacement : Documenter **POURQUOI** dans story "Dev Notes"
   - Si extension : Documenter **COMMENT** (quels champs/méthodes ajouter)
   - Si nouveau : Documenter **POURQUOI** pas de réutilisation

---

### Story 14.1: Naviguer éditeur graphe avec clavier (Tab, Arrow keys, Enter, Escape) (FR114)

As a **utilisateur utilisant uniquement le clavier**,
I want **naviguer l'éditeur de graphe entièrement au clavier**,
So that **je peux créer et éditer des dialogues sans utiliser la souris**.

**Acceptance Criteria:**

**Given** je consulte l'éditeur de graphe
**When** j'utilise la navigation clavier
**Then** je peux naviguer entre nœuds avec Tab (nœud suivant) et Shift+Tab (nœud précédent)
**And** le focus se déplace visuellement d'un nœud à l'autre

**Given** un nœud est sélectionné (focus clavier)
**When** j'utilise les flèches directionnelles
**Then** les flèches déplacent le nœud dans le graphe :
- **Flèche gauche** : Déplace nœud vers la gauche
- **Flèche droite** : Déplace nœud vers la droite
- **Flèche haut** : Déplace nœud vers le haut
- **Flèche bas** : Déplace nœud vers le bas

**Given** un nœud est sélectionné
**When** je presse Enter ou Espace
**Then** le panneau d'édition du nœud s'ouvre
**And** le focus se déplace vers le premier champ éditable du panneau

**Given** le panneau d'édition est ouvert
**When** je presse Escape
**Then** le panneau se ferme
**And** le focus revient au nœud sélectionné

**Given** je navigue dans le graphe
**When** je presse Ctrl+F
**Then** la recherche de nœuds s'ouvre
**And** je peux taper pour rechercher un nœud par texte ou ID

**Given** je navigue dans le graphe
**When** je presse les raccourcis clavier (voir Story 12.3)
**Then** les raccourcis fonctionnent :
- **Ctrl+G** : Générer nœud depuis nœud sélectionné
- **Ctrl+L** : Auto-layout graphe
- **Ctrl+Z/Shift+Z** : Undo/Redo
- **Delete** : Supprimer nœud sélectionné
- **Ctrl+D** : Dupliquer nœud sélectionné

**Given** je navigue dans le graphe
**When** je sélectionne un nœud avec Tab
**Then** le nœud est visuellement mis en évidence (bordure focus, voir Story 14.2)
**And** je peux voir quel nœud a le focus

**Given** je navigue dans le graphe
**When** je presse Tab sur le dernier nœud
**Then** le focus revient au premier nœud (navigation cyclique)
**And** je peux continuer à naviguer sans interruption

**Given** je navigue dans le graphe avec beaucoup de nœuds (>50)
**When** je navigue avec Tab
**Then** la vue se déplace automatiquement pour garder le nœud focalisé visible
**And** le défilement est fluide (pas de saut brusque)

**Technical Requirements:**
- Frontend : Extension `GraphEditor` avec gestion focus clavier (tabindex, onKeyDown handlers)
- Navigation : Service `KeyboardNavigationService` pour gérer navigation Tab entre nœuds
- Déplacement : Gestionnaires flèches directionnelles pour déplacer nœuds sélectionnés
- Focus : Gestion état focus avec `useState` et `useRef` pour nœud actuellement focalisé
- Auto-scroll : Fonction `scrollIntoView` pour garder nœud focalisé visible lors navigation
- Intégration : Réutiliser `useKeyboardShortcuts` (existant) pour raccourcis clavier
- Tests : Unit (navigation clavier), Integration (navigation graphe), E2E (workflow clavier complet)

**References:** FR114 (navigation clavier éditeur graphe), Story 12.3 (raccourcis clavier), Story 14.2 (indicateurs focus), NFR-A1 (Keyboard Navigation 100%)

---

### Story 14.2: Afficher indicateurs focus visibles pour navigation clavier (FR115)

As a **utilisateur utilisant uniquement le clavier**,
I want **voir clairement quel élément a le focus**,
So that **je peux savoir où je suis dans l'interface et naviguer efficacement**.

**Acceptance Criteria:**

**Given** je navigue dans l'interface avec Tab
**When** un élément reçoit le focus
**Then** un indicateur de focus visible s'affiche :
- Bordure visible (ex: 2px bleu ou orange)
- Ombre portée (box-shadow)
- Contraste suffisant (WCAG AA, voir Story 14.3)

**Given** je navigue dans l'éditeur de graphe
**When** un nœud reçoit le focus
**Then** le nœud affiche :
- Bordure focus visible (2-3px, couleur contrastée)
- Fond légèrement modifié (opacité ou couleur différente)
- Indicateur visuel clair (ex: icône focus ou badge)

**Given** je navigue dans les formulaires
**When** un champ reçoit le focus
**Then** le champ affiche :
- Bordure focus visible (2px, couleur contrastée)
- Fond légèrement modifié (si applicable)
- Label mis en évidence (couleur ou poids police)

**Given** je navigue dans les boutons
**When** un bouton reçoit le focus
**Then** le bouton affiche :
- Bordure focus visible (outline ou ring)
- Fond légèrement modifié
- Indicateur clair que le bouton est focalisé

**Given** je navigue dans les listes (ex: liste dialogues, liste personnages)
**When** un élément de liste reçoit le focus
**Then** l'élément affiche :
- Fond modifié (couleur de surbrillance)
- Bordure focus visible
- Indicateur visuel clair (ex: icône sélection)

**Given** je navigue dans les modals
**When** un élément dans le modal reçoit le focus
**Then** l'indicateur de focus est visible même dans le contexte du modal
**And** le focus est clairement distinguable du reste du modal

**Given** je navigue rapidement (Tab répété)
**When** le focus se déplace rapidement
**Then** les indicateurs de focus apparaissent immédiatement (pas de délai)
**And** l'animation de transition est fluide (si applicable)

**Given** je consulte les paramètres d'accessibilité
**When** j'active "Indicateurs focus renforcés"
**Then** les indicateurs de focus deviennent plus visibles :
- Bordure plus épaisse (3-4px au lieu de 2px)
- Contraste plus élevé
- Animation plus prononcée

**Technical Requirements:**
- Frontend : Styles CSS pour `:focus` et `:focus-visible` sur tous les éléments interactifs
- Thème : Variables CSS dans `theme.ts` pour couleurs focus (ex: `focus.border`, `focus.shadow`)
- Composants : Props `focusVisible` ou classes CSS pour indicateurs focus personnalisés
- Graphique : Styles spécifiques pour nœuds graphe avec focus (bordure, ombre, fond)
- Contraste : Vérifier contraste indicateurs focus (WCAG AA, voir Story 14.3)
- Tests : Unit (styles focus), Integration (indicateurs focus), E2E (navigation clavier avec focus visible)

**References:** FR115 (indicateurs focus visibles), Story 14.1 (navigation clavier), Story 14.3 (contraste couleurs), NFR-A1 (Keyboard Navigation), NFR-A2 (Color Contrast)

---

### Story 14.3: Personnaliser contraste couleurs (WCAG AA minimum) (FR116)

As a **utilisateur avec besoins d'accessibilité visuelle**,
I want **personnaliser le contraste des couleurs**,
So that **je peux utiliser l'application avec un contraste suffisant pour mes besoins**.

**Acceptance Criteria:**

**Given** je consulte les paramètres d'accessibilité
**When** j'ouvre "Contraste couleurs"
**Then** un panneau s'affiche avec options :
- Contraste standard (WCAG AA minimum)
- Contraste élevé (WCAG AAA)
- Mode sombre (si disponible)
- Personnalisation avancée

**Given** je sélectionne "Contraste standard (WCAG AA)"
**When** le contraste est appliqué
**Then** tous les textes respectent un ratio de contraste ≥4.5:1 (texte normal) ou ≥3:1 (texte large)
**And** tous les éléments UI (boutons, bordures) respectent un ratio ≥3:1
**And** les couleurs sont validées automatiquement

**Given** je sélectionne "Contraste élevé (WCAG AAA)"
**When** le contraste élevé est appliqué
**Then** tous les textes respectent un ratio de contraste ≥7:1 (texte normal) ou ≥4.5:1 (texte large)
**And** les éléments UI ont un contraste encore plus élevé
**And** les couleurs sont optimisées pour lisibilité maximale

**Given** je personnalise les couleurs manuellement
**When** je modifie une couleur dans "Personnalisation avancée"
**Then** un indicateur s'affiche montrant le ratio de contraste calculé
**And** un warning s'affiche si le contraste est insuffisant (<WCAG AA)
**And** je peux voir un aperçu en temps réel des changements

**Given** je consulte l'interface avec contraste personnalisé
**When** les couleurs sont appliquées
**Then** tous les éléments respectent le contraste configuré :
- Textes (titres, paragraphes, labels)
- Boutons (texte + fond)
- Bordures et séparateurs
- Indicateurs de focus (voir Story 14.2)
- Graphiques et diagrammes (si applicable)

**Given** je change le contraste
**When** le nouveau contraste est appliqué
**Then** les changements sont immédiats (pas de rechargement)
**And** les préférences sont sauvegardées (localStorage ou backend)
**And** le contraste est restauré à la prochaine connexion

**Given** je consulte un dialogue avec contraste personnalisé
**When** le dialogue est affiché
**Then** le contraste est appliqué à tous les éléments du dialogue :
- Texte des nœuds
- Choix joueur
- Métadonnées
- Indicateurs de validation

**Given** je consulte l'éditeur de graphe avec contraste personnalisé
**When** le graphe est affiché
**Then** le contraste est appliqué à :
- Nœuds (bordure, fond, texte)
- Connexions (lignes)
- Indicateurs de focus
- Légendes et labels

**Technical Requirements:**
- Frontend : Système de thèmes avec variables CSS pour contraste (ex: `theme.contrast.standard`, `theme.contrast.high`)
- Validation : Service `ColorContrastValidator` pour calculer ratios de contraste (algorithme WCAG)
- Thème : Extension `theme.ts` avec palettes de couleurs pour chaque niveau de contraste
- Personnalisation : Composant `ContrastSettingsPanel.tsx` avec sélecteur contraste + aperçu
- Persistence : Sauvegarder préférences contraste dans localStorage ou backend (profil utilisateur)
- Tests : Unit (calcul contraste), Integration (application contraste), E2E (workflow contraste)

**References:** FR116 (personnalisation contraste WCAG AA), Story 14.2 (indicateurs focus), NFR-A2 (Color Contrast WCAG AA)

---

### Story 14.4: Supporter lecteurs d'écran avec ARIA labels (V2.0+) (FR117)

As a **utilisateur utilisant un lecteur d'écran**,
I want **que l'application supporte les lecteurs d'écran avec ARIA labels**,
So that **je peux utiliser l'application efficacement avec ma technologie d'assistance**.

**Acceptance Criteria:**

**Given** le support lecteurs d'écran est disponible (V2.0+)
**When** j'utilise un lecteur d'écran (NVDA, JAWS, VoiceOver)
**Then** tous les éléments interactifs ont des labels ARIA appropriés :
- Boutons : `aria-label` ou texte visible
- Champs de formulaire : `aria-label` ou `aria-labelledby`
- Liens : texte descriptif ou `aria-label`
- Images : `alt` text ou `aria-label`

**Given** je navigue dans l'interface avec un lecteur d'écran
**When** je consulte la structure de la page
**Then** les landmarks ARIA sont correctement définis :
- `<nav>` ou `role="navigation"` pour navigation principale
- `<main>` ou `role="main"` pour contenu principal
- `<header>` ou `role="banner"` pour en-tête
- `<footer>` ou `role="contentinfo"` pour pied de page

**Given** je navigue dans l'éditeur de graphe avec un lecteur d'écran
**When** je consulte les nœuds
**Then** chaque nœud a des attributs ARIA appropriés :
- `role="button"` ou `role="article"` selon contexte
- `aria-label` avec description du nœud (speaker, texte, type)
- `aria-describedby` pour métadonnées supplémentaires
- `aria-expanded` pour nœuds avec contenu pliable

**Given** je consulte un formulaire avec un lecteur d'écran
**When** je navigue dans les champs
**Then** chaque champ a :
- `aria-label` ou `aria-labelledby` pour label
- `aria-required` si champ obligatoire
- `aria-invalid` si erreur de validation
- `aria-describedby` pour messages d'aide ou d'erreur

**Given** je consulte des messages dynamiques avec un lecteur d'écran
**When** un message s'affiche (ex: "Génération terminée", "Erreur de validation")
**Then** le message est annoncé par le lecteur d'écran :
- `role="alert"` pour messages critiques (erreurs)
- `role="status"` ou `aria-live="polite"` pour messages informatifs
- `aria-live="assertive"` pour messages urgents

**Given** je navigue dans l'interface avec un lecteur d'écran
**When** je consulte les liens de navigation
**Then** des "skip links" sont disponibles :
- "Aller au contenu principal" (skip navigation)
- "Aller à la recherche" (skip header)
**And** les skip links sont visibles au focus clavier

**Given** je consulte un dialogue avec un lecteur d'écran
**When** le dialogue est généré ou modifié
**Then** les changements sont annoncés :
- Nouveau nœud ajouté : annoncé avec `aria-live="polite"`
- Nœud modifié : annoncé avec contexte
- Erreur détectée : annoncée avec `role="alert"`

**Given** je consulte l'historique d'utilisation avec un lecteur d'écran
**When** je navigue dans les tableaux
**Then** les tableaux ont des attributs ARIA appropriés :
- `role="table"` avec `aria-label` descriptif
- En-têtes de colonnes avec `scope="col"`
- En-têtes de lignes avec `scope="row"`
- `aria-sort` pour colonnes triables

**Given** je teste l'accessibilité
**When** j'utilise un outil d'audit (Lighthouse, axe-core)
**Then** l'application passe les tests d'accessibilité WCAG AA
**And** aucun problème critique d'ARIA n'est détecté

**Technical Requirements:**
- Frontend : Attributs ARIA sur tous les éléments interactifs (aria-label, aria-describedby, roles)
- Sémantique : Utilisation HTML sémantique (`<nav>`, `<main>`, `<header>`, `<footer>`, `<button>`, `<input>`)
- Live regions : Composants avec `aria-live` pour annonces dynamiques (génération, erreurs, succès)
- Skip links : Liens de saut vers contenu principal (visibles au focus, masqués sinon)
- Tableaux : Attributs ARIA appropriés pour tableaux (`role="table"`, `scope`, `aria-sort`)
- Validation : Outils d'audit accessibilité (axe-core, Lighthouse) intégrés dans tests
- Tests : Unit (attributs ARIA), Integration (lecteurs d'écran simulation), E2E (tests lecteurs d'écran réels)

**References:** FR117 (support lecteurs d'écran V2.0+), Story 14.1 (navigation clavier), Story 14.2 (indicateurs focus), NFR-A3 (Screen Reader Support V2.0+)

