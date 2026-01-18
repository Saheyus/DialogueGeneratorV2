## Epic 12: Expérience utilisateur et workflow

Les utilisateurs peuvent optimiser leur workflow avec preview avant génération, comparaison side-by-side de nœuds, et raccourcis clavier pour actions courantes. Le système améliore l'efficacité et réduit la friction dans le processus de création.

**FRs covered:** FR109-111 (preview avant génération, comparaison nœuds, raccourcis clavier)

**NFRs covered:** NFR-U1 (Usability - New user can create first dialogue in <30min), NFR-A1 (Keyboard Navigation)

**Valeur utilisateur:** Améliorer l'efficacité de création de dialogues avec preview avant génération, comparaison de nœuds, et raccourcis clavier pour actions courantes, réduisant la friction et le temps de travail.

**Dépendances:** Epic 1 (dialogues), Epic 2 (éditeur graphe), Epic 3 (génération LLM)

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

### Story 12.1: Prévisualiser structure estimée nœuds avant génération LLM (dry-run mode) (FR109)

As a **utilisateur créant des dialogues**,
I want **prévisualiser la structure estimée des nœuds avant la génération LLM**,
So that **je peux valider mes paramètres et estimer le résultat avant de consommer des tokens LLM**.

**Acceptance Criteria:**

**Given** j'ai configuré les paramètres de génération (contexte, instructions, structure dialogue)
**When** je clique sur "Preview structure" ou active le mode "Dry-run"
**Then** une prévisualisation s'affiche montrant :
- Nombre estimé de nœuds qui seront générés
- Structure estimée (types de nœuds : Dialogue, Test, End)
- Nombre estimé de choix joueur par nœud
- Estimation des tokens qui seront consommés

**Given** je prévisualise la structure
**When** la prévisualisation est chargée
**Then** un graphe schématique s'affiche avec les nœuds estimés (sans contenu texte)
**And** chaque nœud affiche son type (Dialogue, Test, End) et nombre de choix estimés
**And** les connexions estimées entre nœuds sont affichées

**Given** je prévisualise la structure
**When** je consulte les détails
**Then** un panneau affiche :
- Estimation tokens contexte : X tokens
- Estimation tokens génération : Y tokens
- Estimation coût (si configuré) : $Z
- Structure dialogue : [PNJ, PJ, Stop, ...] avec nombre nœuds par étape

**Given** la prévisualisation montre une structure inattendue
**When** je vois que trop de nœuds seront générés (ex: 20 au lieu de 5)
**Then** je peux ajuster les paramètres (max_choices, structure dialogue)
**And** la prévisualisation se met à jour automatiquement

**Given** je prévisualise la structure
**When** je suis satisfait de la structure estimée
**Then** je peux cliquer sur "Générer avec cette structure"
**And** la génération LLM démarre avec les paramètres validés

**Given** je prévisualise la structure
**When** je vois des problèmes (structure trop complexe, trop de tokens)
**Then** je peux ajuster les paramètres et re-prévisualiser
**And** je peux annuler sans consommer de tokens LLM

**Given** le mode dry-run est activé
**When** je lance une génération
**Then** le système simule la génération sans appeler le LLM
**And** un rapport s'affiche "Dry-run : X nœuds estimés, Y tokens, structure validée"
**And** je peux confirmer pour générer réellement ou ajuster

**Technical Requirements:**
- Backend : Endpoint `/api/v1/dialogues/preview-structure` (POST) retourne structure estimée sans génération LLM
- Service : `DialogueStructureEstimatorService` pour estimer structure basée sur paramètres (max_choices, structure dialogue, contexte)
- Estimation : Algorithme heuristique pour estimer nombre nœuds selon structure dialogue et max_choices
- Frontend : Composant `StructurePreviewPanel.tsx` avec graphe schématique + détails estimation
- Intégration : Bouton "Preview structure" dans `GenerationPanel` avant génération
- Dry-run : Flag `dry_run=true` dans requête génération pour simulation sans LLM
- Tests : Unit (estimation structure), Integration (API preview structure), E2E (workflow preview)

**References:** FR109 (preview structure avant génération), Story 3.1 (génération nœud unique), Story 3.2 (génération batch), Epic 3 (génération LLM)

---

### Story 12.2: Comparer deux nœuds dialogue côte à côte (FR110)

As a **utilisateur éditant des dialogues**,
I want **comparer deux nœuds de dialogue côte à côte**,
So that **je peux voir les différences entre versions, variantes, ou nœuds similaires**.

**Acceptance Criteria:**

**Given** j'ai plusieurs nœuds dans mon dialogue
**When** je sélectionne deux nœuds (Ctrl+clic ou menu contextuel "Comparer avec...")
**Then** un panneau de comparaison s'affiche avec les deux nœuds côte à côte
**And** les différences sont surlignées (vert = ajouté, rouge = supprimé, orange = modifié)

**Given** je compare deux nœuds
**When** le panneau de comparaison est ouvert
**Then** chaque nœud est affiché dans une colonne (gauche/droite)
**And** les champs sont alignés pour comparaison facile :
- Speaker (personnage)
- Line (texte dialogue)
- Choices (choix joueur)
- Conditions, effets, métadonnées

**Given** je compare deux nœuds avec différences
**When** les différences sont détectées
**Then** les champs différents sont surlignés :
- Texte modifié : surligné orange avec indication avant/après
- Choix ajouté : surligné vert
- Choix supprimé : surligné rouge (barré)
- Condition modifiée : surligné orange

**Given** je compare deux nœuds
**When** je consulte les détails
**Then** un résumé s'affiche "X différences détectées : Y ajouts, Z suppressions, W modifications"
**And** je peux cliquer sur une différence pour naviguer directement au champ concerné

**Given** je compare un nœud avec une version précédente
**When** je sélectionne "Comparer avec version précédente"
**Then** le nœud actuel est comparé avec la dernière version sauvegardée
**And** les différences depuis la dernière sauvegarde sont affichées

**Given** je compare deux nœuds de dialogues différents
**When** je sélectionne deux nœuds depuis deux dialogues ouverts
**Then** la comparaison fonctionne normalement
**And** un indicateur affiche "Comparaison inter-dialogues"

**Given** je compare deux nœuds
**When** je modifie un nœud pendant la comparaison
**Then** la comparaison se met à jour automatiquement
**And** les nouvelles différences sont surlignées

**Given** je ferme le panneau de comparaison
**When** je clique sur "Fermer"
**Then** le panneau se ferme et je reviens à l'éditeur normal
**And** les sélections de nœuds sont conservées

**Technical Requirements:**
- Frontend : Composant `NodeComparisonPanel.tsx` avec vue side-by-side + détection différences
- Diff : Service `NodeDiffService` pour calcul différences entre deux nœuds (champs, choix, conditions)
- Sélection : Extension sélection multiple dans `GraphEditor` pour sélectionner deux nœuds (Ctrl+clic)
- Menu contextuel : Option "Comparer avec..." dans menu contextuel nœud
- Highlighting : Système de surlignage différences (vert/rouge/orange) avec indication avant/après
- Tests : Unit (diff nœuds), Integration (comparaison UI), E2E (workflow comparaison)

**References:** FR110 (comparaison nœuds side-by-side), Story 2.1 (éditeur graphe), Story 5.1 (édition nœuds), Epic 2 (éditeur graphe)

---

### Story 12.3: Accéder raccourcis clavier pour actions courantes (FR111)

As a **utilisateur créant des dialogues**,
I want **utiliser des raccourcis clavier pour les actions courantes**,
So that **je peux travailler plus rapidement sans utiliser la souris pour chaque action**.

**Acceptance Criteria:**

**Given** je consulte l'interface
**When** j'utilise les raccourcis clavier
**Then** les raccourcis suivants fonctionnent :
- **Ctrl+G** : Générer un nœud avec l'IA (si nœud sélectionné)
- **Ctrl+S** : Sauvegarder le dialogue
- **Ctrl+Z** : Annuler (undo)
- **Ctrl+Shift+Z** : Refaire (redo)
- **Ctrl+E** : Exporter dialogue Unity
- **Ctrl+N** : Nouveau dialogue (réinitialiser)
- **Ctrl+K** : Ouvrir palette de commandes
- **Ctrl+/** : Afficher aide raccourcis clavier
- **Ctrl+L** : Auto-layout graphe
- **Ctrl+F** : Rechercher nœud dans graphe
- **Escape** : Fermer modals/panneaux

**Given** je consulte l'éditeur de graphe
**When** j'utilise les raccourcis spécifiques au graphe
**Then** les raccourcis suivants fonctionnent :
- **Ctrl+G** : Générer nœud depuis nœud sélectionné
- **Ctrl+L** : Auto-layout graphe
- **Ctrl+F** : Rechercher nœud
- **Ctrl+Z/Shift+Z** : Undo/Redo modifications graphe
- **Delete** : Supprimer nœud sélectionné
- **Ctrl+D** : Dupliquer nœud sélectionné

**Given** je consulte le panneau de génération
**When** j'utilise les raccourcis spécifiques à la génération
**Then** les raccourcis suivants fonctionnent :
- **Ctrl+Enter** : Générer dialogue
- **Alt+S** : Échanger personnages (swap)
- **Ctrl+N** : Réinitialiser formulaire

**Given** je consulte la navigation
**When** j'utilise les raccourcis de navigation
**Then** les raccourcis suivants fonctionnent :
- **Ctrl+1** : Naviguer vers Dashboard
- **Ctrl+2** : Naviguer vers Dialogues Unity
- **Ctrl+3** : Naviguer vers Usage/Statistiques

**Given** je consulte l'aide des raccourcis
**When** je presse Ctrl+/
**Then** un modal s'affiche listant tous les raccourcis disponibles
**And** les raccourcis sont groupés par catégorie (Génération, Édition, Navigation, etc.)
**And** je peux voir les raccourcis spécifiques au contexte actuel (éditeur graphe vs génération)

**Given** un raccourci est désactivé (ex: Ctrl+G si aucun nœud sélectionné)
**When** je presse le raccourci
**Then** rien ne se passe (pas d'erreur)
**And** un hint discret s'affiche "Sélectionnez un nœud pour générer" (optionnel)

**Given** je tape dans un champ de saisie (input, textarea)
**When** je presse un raccourci
**Then** certains raccourcis fonctionnent même dans les inputs (Ctrl+S, Ctrl+E, Escape)
**And** les autres raccourcis sont ignorés (pour permettre saisie normale)

**Given** je consulte les raccourcis dans l'interface
**When** je survole un bouton ou action
**Then** un tooltip affiche le raccourci clavier associé (ex: "Sauvegarder (Ctrl+S)")
**And** le raccourci est visible dans les menus et barres d'outils

**Technical Requirements:**
- Frontend : Hook `useKeyboardShortcuts` (existant) pour gestion centralisée raccourcis
- Registre : Système de registre global pour éviter conflits entre composants
- Priorité : Gestion priorité raccourcis (raccourcis contextuels > globaux)
- Détection : Détection contexte (éditeur graphe vs génération) pour activer raccourcis appropriés
- Tooltips : Affichage raccourcis dans tooltips boutons (composant `Tooltip` existant)
- Aide : Modal `KeyboardShortcutsHelp` (existant) avec liste complète raccourcis
- Tests : Unit (raccourcis logique), Integration (raccourcis UI), E2E (workflow raccourcis)

**References:** FR111 (raccourcis clavier), Story 11.2 (documentation), Story 11.3 (aide contextuelle), NFR-A1 (Keyboard Navigation)

