## Epic 11: Onboarding et guidance

Les nouveaux utilisateurs peuvent accéder à un wizard d'onboarding pour leur première création de dialogue. Le système fournit documentation in-app, tutoriels, aide contextuelle, dialogues d'exemple, et détection du niveau de compétence pour adapter l'UI (mode guidé vs mode avancé). Inclut variantes optimisées pour persona Mathieu (détection automatique, wizard simplifié 4 étapes, assistance contextuelle renforcée, validation premier run <30min).

**FRs covered:** FR102-108 (wizard onboarding, documentation, aide contextuelle, dialogues d'exemple, détection compétence, mode power/guided)

**NFRs covered:** NFR-U1 (Usability - New user can create first dialogue in <30min), NFR-A1 (Keyboard Navigation), NFR-R3 (Data Loss Prevention 100% pour premier run)

**Valeur utilisateur:** Permettre aux nouveaux utilisateurs de créer leur premier dialogue rapidement (<30min) sans support externe, avec guidance progressive et adaptation selon le niveau de compétence. Optimisé pour persona Mathieu (utilisateur occasionnel) avec expérience premier run simplifiée.

**Dépendances:** Epic 0 (auto-save), Epic 1 (dialogues), Epic 2 (éditeur graphe), Epic 3 (génération LLM), Epic 8 (recherche)

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

### Story 11.1: Accéder wizard onboarding pour première création dialogue (V1.0+) (FR102)

As a **nouvel utilisateur**,
I want **accéder à un wizard d'onboarding pour ma première création de dialogue**,
So that **je peux créer mon premier dialogue guidé étape par étape sans être submergé par toutes les options**.

**Acceptance Criteria:**

**Given** je suis un nouvel utilisateur (première connexion ou aucun dialogue créé)
**When** j'ouvre l'application pour la première fois
**Then** un modal d'onboarding s'affiche "Bienvenue dans DialogueGenerator - Créons votre premier dialogue"
**And** je peux choisir "Commencer le wizard" ou "Passer l'onboarding"

**Given** je choisis "Commencer le wizard"
**When** le wizard démarre
**Then** une série d'étapes guidées s'affiche :
- **Étape 1** : "Quel lieu pour ce dialogue ?" (sélecteur avec recherche)
- **Étape 2** : "Quel personnage parle ?" (sélecteur personnages)
- **Étape 3** : "Contexte ou thème ?" (input texte libre)
- **Étape 4** : "Instructions spéciales ?" (template pré-rempli avec suggestions)
- **Étape 5** : "Générer le dialogue" (bouton final)

**Given** je complète chaque étape du wizard
**When** je passe d'une étape à l'autre
**Then** un indicateur de progression s'affiche "Étape X/5"
**And** je peux revenir en arrière pour modifier les étapes précédentes
**And** les valeurs saisies sont conservées

**Given** je complète toutes les étapes du wizard
**When** je clique sur "Générer le dialogue"
**Then** le dialogue est généré avec les paramètres du wizard
**And** le wizard se ferme et l'éditeur de graphe s'ouvre avec le dialogue généré
**And** un message s'affiche "Premier dialogue créé ! Vous pouvez maintenant explorer l'éditeur"

**Given** je choisis "Passer l'onboarding"
**When** je ferme le modal
**Then** l'application s'ouvre normalement (dashboard ou éditeur)
**And** je peux accéder au wizard plus tard via "Aide > Wizard onboarding"

**Given** j'ai déjà créé un dialogue
**When** j'ouvre l'application
**Then** le wizard d'onboarding ne s'affiche plus automatiquement
**And** je peux toujours accéder au wizard via "Aide > Wizard onboarding" si besoin

**Technical Requirements:**
- Frontend : Composant `OnboardingWizard.tsx` avec étapes progressives (React state machine ou stepper)
- Détection : Flag `hasCompletedOnboarding` dans localStorage ou backend (première création dialogue)
- Intégration : Wizard pré-remplit les champs du `GenerationPanel` (personnages, lieux, contexte)
- Navigation : Boutons "Précédent" / "Suivant" / "Passer" pour navigation entre étapes
- Persistence : Sauvegarder progression wizard dans localStorage (récupération si fermeture accidentelle)
- Tests : Unit (wizard logique), Integration (wizard + génération), E2E (workflow onboarding complet)

**References:** FR102 (wizard onboarding V1.0+), Story 11.2 (documentation), Story 11.8 (mode guidé), NFR-U1 (Usability <30min)

---

### Story 11.2: Accéder documentation et tutoriels in-app (FR103)

As a **utilisateur**,
I want **accéder à la documentation et tutoriels directement dans l'application**,
So that **je peux apprendre à utiliser les fonctionnalités sans quitter l'application**.

**Acceptance Criteria:**

**Given** je consulte l'interface
**When** je clique sur "Aide" ou "?" dans la barre de navigation
**Then** un panneau s'affiche avec sections : Documentation, Tutoriels, Raccourcis clavier, FAQ

**Given** j'ouvre "Documentation"
**When** la documentation est chargée
**Then** une liste de sujets s'affiche : Création dialogue, Éditeur graphe, Génération LLM, Variables et flags, Export Unity
**And** je peux cliquer sur un sujet pour voir la documentation complète
**And** la documentation est formatée avec exemples de code, captures d'écran, schémas

**Given** j'ouvre "Tutoriels"
**When** les tutoriels sont chargés
**Then** une liste de tutoriels vidéo ou interactifs s'affiche :
- "Créer votre premier dialogue" (5min)
- "Utiliser l'éditeur de graphe" (10min)
- "Gérer les variables et flags" (8min)
- "Exporter vers Unity" (3min)
**And** je peux lancer un tutoriel (vidéo ou guide interactif)

**Given** je consulte un tutoriel interactif
**When** le tutoriel démarre
**Then** des étapes guidées s'affichent avec highlights sur les éléments UI concernés
**And** je peux suivre les étapes en cliquant sur les éléments mis en évidence
**And** je peux passer une étape ou quitter le tutoriel à tout moment

**Given** je recherche dans la documentation
**When** je saisis un terme dans la barre de recherche
**Then** les résultats pertinents s'affichent (sujets, tutoriels, FAQ)
**And** je peux cliquer sur un résultat pour accéder directement au contenu

**Given** je consulte la FAQ
**When** la FAQ est chargée
**Then** une liste de questions fréquentes s'affiche avec réponses détaillées
**And** je peux rechercher dans la FAQ par mots-clés

**Technical Requirements:**
- Frontend : Composant `HelpPanel.tsx` avec onglets Documentation/Tutoriels/FAQ
- Documentation : Fichiers Markdown dans `docs/` ou contenu structuré JSON
- Tutoriels : Composant `TutorialPlayer.tsx` pour tutoriels interactifs (highlights UI, étapes guidées)
- Recherche : Service `HelpSearchService` pour recherche full-text dans documentation
- API : Endpoint `/api/v1/help/docs` (GET) retourne documentation, `/api/v1/help/tutorials` (GET) retourne tutoriels
- Tests : Unit (recherche documentation), Integration (API help), E2E (workflow documentation)

**References:** FR103 (documentation in-app), Story 11.1 (wizard onboarding), Story 11.3 (aide contextuelle)

---

### Story 11.3: Recevoir aide contextuelle basée sur actions utilisateur (FR104)

As a **utilisateur**,
I want **recevoir de l'aide contextuelle basée sur mes actions**,
So that **je peux obtenir des conseils pertinents au moment où j'en ai besoin**.

**Acceptance Criteria:**

**Given** je survole un élément UI (bouton, champ, panneau)
**When** je laisse le curseur quelques secondes
**Then** un tooltip contextuel s'affiche avec description courte de l'élément
**And** le tooltip disparaît quand je déplace le curseur

**Given** je consulte un champ complexe (ex: "Instructions spéciales")
**When** je clique sur l'icône "?" à côté du champ
**Then** un panneau d'aide contextuelle s'affiche avec :
- Description du champ
- Exemples d'utilisation
- Bonnes pratiques
- Liens vers documentation complète

**Given** je tente une action qui peut échouer (ex: générer sans contexte)
**When** l'action est détectée comme risquée
**Then** un message contextuel s'affiche "⚠️ Aucun contexte sélectionné - la génération sera moins précise. Voulez-vous continuer ?"
**And** je peux voir un lien "En savoir plus" vers la documentation contexte

**Given** je reste inactif sur une page complexe (ex: éditeur graphe) pendant 30 secondes
**When** je n'ai pas encore interagi avec les fonctionnalités principales
**Then** un hint contextuel discret s'affiche "💡 Astuce : Cliquez sur un nœud pour l'éditer"
**And** le hint disparaît après 5 secondes ou quand j'interagis

**Given** je rencontre une erreur (ex: validation échoue)
**When** l'erreur est affichée
**Then** un lien "Comment corriger ?" s'affiche à côté du message d'erreur
**And** je peux cliquer pour voir des conseils spécifiques à cette erreur

**Given** je consulte un dialogue avec beaucoup de nœuds (>50)
**When** je navigue dans le graphe
**Then** un hint contextuel s'affiche "💡 Astuce : Utilisez Ctrl+F pour rechercher un nœud"
**And** le hint disparaît après interaction

**Given** je consulte l'aide contextuelle
**When** je clique sur "Ne plus afficher ce hint"
**Then** le hint est masqué pour cette fonctionnalité
**And** je peux réactiver les hints via "Paramètres > Aide > Réactiver hints"

**Technical Requirements:**
- Frontend : Composant `ContextualHelp.tsx` avec système de tooltips, hints, et panneaux d'aide
- Détection : Service `UserActionTracker` pour détecter actions utilisateur et déclencher aide contextuelle
- Tooltips : Réutiliser composant `Tooltip` (existant) avec contenu contextuel dynamique
- Hints : Système de hints intelligents basés sur état UI (inactivité, complexité, erreurs)
- Configuration : Préférences utilisateur pour activer/désactiver hints (localStorage)
- Tests : Unit (détection actions), Integration (aide contextuelle), E2E (workflow hints)

**References:** FR104 (aide contextuelle), Story 11.2 (documentation), Story 11.4 (dialogues d'exemple)

---

### Story 11.4: Accéder dialogues d'exemple pour apprentissage (FR105)

As a **nouvel utilisateur**,
I want **accéder à des dialogues d'exemple**,
So that **je peux voir des exemples concrets et apprendre les bonnes pratiques**.

**Acceptance Criteria:**

**Given** je consulte l'application
**When** j'ouvre "Dialogues d'exemple" depuis le menu Aide
**Then** une liste de dialogues d'exemple s'affiche avec :
- Titre du dialogue
- Description (contexte, personnages, objectif)
- Complexité (Simple, Moyen, Avancé)
- Nombre de nœuds
- Tags (ex: "Première rencontre", "Quête", "Commerce")

**Given** je consulte un dialogue d'exemple
**When** je clique sur "Ouvrir dans l'éditeur"
**Then** le dialogue s'ouvre dans l'éditeur de graphe en mode lecture seule
**And** un badge s'affiche "Exemple - Mode lecture seule"
**And** je peux explorer la structure, les nœuds, les connexions

**Given** je consulte un dialogue d'exemple
**When** je clique sur "Créer une copie"
**Then** une copie du dialogue est créée avec un nouveau nom (ex: "Mon dialogue - basé sur [Exemple]")
**And** je peux modifier la copie librement
**And** le dialogue original reste intact

**Given** je filtre les dialogues d'exemple
**When** je sélectionne "Complexité : Simple"
**Then** seuls les dialogues simples sont affichés
**And** je peux filtrer par tags, nombre de nœuds, personnages

**Given** je consulte un dialogue d'exemple
**When** j'ouvre les détails
**Then** une description s'affiche expliquant :
- Pourquoi cet exemple est utile
- Ce qu'il illustre (ex: gestion variables, branches conditionnelles)
- Comment l'adapter à mon propre dialogue

**Given** je consulte plusieurs dialogues d'exemple
**When** je compare leurs structures
**Then** je peux voir les différences (approches différentes pour même objectif)
**And** des annotations expliquent les choix de design

**Technical Requirements:**
- Backend : Endpoint `/api/v1/examples/dialogues` (GET) retourne liste dialogues d'exemple
- Stockage : Dossier `data/examples/` avec dialogues JSON d'exemple (lecture seule)
- Métadonnées : Fichier `examples_metadata.json` avec descriptions, tags, complexité pour chaque exemple
- Frontend : Composant `ExampleDialoguesPanel.tsx` avec liste + filtres + ouverture/copie
- Mode lecture : Flag `isExample` pour empêcher modifications dialogues d'exemple
- Tests : Unit (chargement exemples), Integration (API examples), E2E (workflow exemples)

**References:** FR105 (dialogues d'exemple), Story 11.1 (wizard onboarding), Story 11.2 (documentation), Epic 1 (dialogues)

---

### Story 11.5: Détecter niveau compétence utilisateur et adapter UI (power vs guided mode) (V1.5+) (FR106)

As a **utilisateur**,
I want **que l'UI s'adapte à mon niveau de compétence**,
So that **je reçois une interface guidée si je suis débutant, ou une interface complète si je suis expérimenté**.

**Acceptance Criteria:**

**Given** le système de détection de compétence est disponible (V1.5+)
**When** je me connecte pour la première fois
**Then** un questionnaire s'affiche "Quel est votre niveau d'expérience ?"
**And** je peux choisir : Débutant, Intermédiaire, Avancé

**Given** je choisis "Débutant"
**When** l'interface se charge
**Then** le mode "Guided" est activé automatiquement
**And** l'interface affiche :
- Moins d'options visibles (options avancées masquées)
- Hints contextuels fréquents
- Wizard pour actions complexes
- Tooltips détaillés sur tous les éléments

**Given** je choisis "Avancé"
**When** l'interface se charge
**Then** le mode "Power" est activé automatiquement
**And** l'interface affiche :
- Toutes les options visibles (pas de masquage)
- Raccourcis clavier prioritaires
- Pas de hints automatiques (sauf si activés manuellement)
- Accès direct aux fonctionnalités avancées

**Given** je suis en mode "Guided" et j'utilise l'application régulièrement
**When** j'ai créé 5+ dialogues et utilisé toutes les fonctionnalités de base
**Then** un message s'affiche "Vous maîtrisez bien l'application - Voulez-vous passer en mode Avancé ?"
**And** je peux accepter ou refuser

**Given** je suis en mode "Power" mais je rencontre des difficultés
**When** je consulte l'aide plusieurs fois ou je fais des erreurs fréquentes
**Then** un message s'affiche "Vous semblez rencontrer des difficultés - Voulez-vous activer le mode Guidé ?"
**And** je peux accepter ou refuser

**Given** je change de mode manuellement
**When** je vais dans "Paramètres > Mode interface"
**Then** je peux basculer entre "Guided", "Standard", "Power"
**And** l'interface s'adapte immédiatement

**Technical Requirements:**
- Backend : Service `UserSkillLevelService` pour détecter niveau compétence (nombre dialogues créés, utilisation fonctionnalités, erreurs)
- Stockage : Champ `skill_level` et `ui_mode` dans profil utilisateur (localStorage ou backend)
- Frontend : Hook `useUIMode` pour gérer mode interface (Guided/Standard/Power)
- Adaptation : Composants conditionnels selon mode (masquer/afficher options, hints, tooltips)
- Détection : Algorithme heuristique pour suggérer changement de mode (usage patterns, erreurs, aide consultée)
- Tests : Unit (détection compétence), Integration (adaptation UI), E2E (workflow changement mode)

**References:** FR106 (détection compétence V1.5+), Story 11.6 (mode power), Story 11.7 (mode guided), NFR-U1 (Usability)

---

### Story 11.6: Activer mode avancé pour contrôle complet (power users) (FR107)

As a **utilisateur expérimenté**,
I want **activer le mode avancé pour avoir un contrôle complet**,
So that **je peux accéder à toutes les fonctionnalités sans limitations ni guidance**.

**Acceptance Criteria:**

**Given** je suis un utilisateur expérimenté
**When** j'active le mode "Power" (via Paramètres > Mode interface)
**Then** toutes les options avancées sont visibles et accessibles
**And** aucun élément n'est masqué pour simplification

**Given** je suis en mode "Power"
**When** je consulte l'éditeur de graphe
**Then** toutes les options avancées sont disponibles :
- Édition directe JSON
- Options LLM avancées (temperature, top_p, etc.)
- Paramètres de validation stricts
- Debug mode (logs détaillés)
- Raccourcis clavier étendus

**Given** je suis en mode "Power"
**When** je génère un dialogue
**Then** je peux accéder à tous les paramètres LLM (pas de valeurs par défaut cachées)
**And** je peux modifier le prompt système directement
**And** je peux configurer des paramètres expérimentaux

**Given** je suis en mode "Power"
**When** je consulte l'interface
**Then** les hints contextuels sont désactivés par défaut (pas de tooltips automatiques)
**And** je peux activer les hints manuellement si besoin (Paramètres > Aide > Afficher hints)

**Given** je suis en mode "Power"
**When** j'utilise les raccourcis clavier
**Then** tous les raccourcis avancés sont disponibles (pas seulement les basiques)
**And** je peux voir la liste complète via Ctrl+Shift+? (raccourcis avancés)

**Given** je suis en mode "Power"
**When** je consulte les paramètres
**Then** toutes les options de configuration sont visibles (pas de "Options avancées" masquées)
**And** je peux modifier des paramètres système (ex: timeouts, retry logic)

**Technical Requirements:**
- Frontend : Flag `uiMode === 'power'` pour conditionner affichage options avancées
- Composants : Props `showAdvanced` ou `mode` pour afficher/masquer options selon mode
- Raccourcis : Extension `useKeyboardShortcuts` avec raccourcis avancés (mode power uniquement)
- Paramètres : Panneau "Options avancées" toujours visible en mode power
- Tests : Unit (mode power logique), Integration (options avancées), E2E (workflow mode power)

**References:** FR107 (mode power), Story 11.5 (détection compétence), Story 11.7 (mode guided), Epic 0 (infrastructure)

---

### Story 11.7: Activer mode guidé avec wizard étape par étape (nouveaux utilisateurs) (FR108)

As a **nouvel utilisateur**,
I want **activer le mode guidé avec wizard étape par étape**,
So that **je peux créer des dialogues sans être submergé par toutes les options**.

**Acceptance Criteria:**

**Given** je suis un nouvel utilisateur
**When** j'active le mode "Guided" (via Paramètres > Mode interface ou détection automatique)
**Then** l'interface passe en mode guidé avec :
- Options avancées masquées (bouton "Afficher options avancées" disponible)
- Hints contextuels fréquents
- Wizards pour actions complexes
- Tooltips détaillés sur tous les éléments

**Given** je suis en mode "Guided"
**When** je crée un nouveau dialogue
**Then** le wizard d'onboarding s'affiche automatiquement (voir Story 11.1)
**And** je suis guidé étape par étape pour sélectionner contexte, personnages, lieux

**Given** je suis en mode "Guided"
**When** j'utilise l'éditeur de graphe
**Then** des hints contextuels s'affichent pour m'expliquer :
- Comment ajouter un nœud
- Comment connecter des nœuds
- Comment éditer un nœud
- Comment générer des choix joueur

**Given** je suis en mode "Guided"
**When** je tente une action complexe (ex: définir variables)
**Then** un wizard s'affiche pour me guider étape par étape
**And** chaque étape explique ce que je dois faire et pourquoi
**And** je peux annuler le wizard et revenir à l'interface normale

**Given** je suis en mode "Guided"
**When** je consulte les options de génération
**Then** seules les options essentielles sont visibles (modèle LLM, nombre nœuds)
**And** les options avancées sont masquées (bouton "Options avancées" pour les afficher)

**Given** je suis en mode "Guided"
**When** je rencontre une erreur
**Then** un message d'aide contextuelle s'affiche expliquant :
- Ce qui s'est passé
- Pourquoi l'erreur s'est produite
- Comment la corriger (étapes détaillées)
- Lien vers documentation complète

**Given** je suis en mode "Guided" et je deviens plus expérimenté
**When** j'ai créé plusieurs dialogues avec succès
**Then** un message s'affiche "Vous maîtrisez bien l'application - Voulez-vous passer en mode Standard ?"
**And** je peux accepter ou continuer en mode guidé

**Technical Requirements:**
- Frontend : Flag `uiMode === 'guided'` pour conditionner affichage simplifié et hints
- Composants : Props `showAdvanced={false}` pour masquer options avancées en mode guided
- Wizards : Réutiliser `OnboardingWizard` (Story 11.1) pour actions complexes en mode guided
- Hints : Système de hints contextuels activé par défaut en mode guided (voir Story 11.3)
- Détection : Algorithme pour suggérer passage mode standard après maîtrise (voir Story 11.5)
- Tests : Unit (mode guided logique), Integration (wizards guidés), E2E (workflow mode guided)

**References:** FR108 (mode guided), Story 11.1 (wizard onboarding), Story 11.5 (détection compétence), Story 11.6 (mode power), NFR-U1 (Usability <30min)

---

### Story 11.8: Détecter automatiquement persona Mathieu et activer mode guidé optimisé (V1.0)

As a **nouvel utilisateur occasionnel (persona Mathieu)**,
I want **que le système détecte automatiquement mon profil et active le mode guidé optimisé**,
So that **je n'ai pas à configurer manuellement l'interface et je peux commencer immédiatement avec une expérience simplifiée**.

**Acceptance Criteria:**

**Given** je suis un nouvel utilisateur (première connexion, aucun dialogue créé)
**When** j'ouvre l'application pour la première fois
**Then** le système détecte automatiquement que je suis un nouvel utilisateur
**And** un questionnaire court s'affiche "Quel est votre niveau d'expérience ?"
**And** les options sont : "Débutant - Je veux être guidé", "Intermédiaire", "Avancé"

**Given** je sélectionne "Débutant - Je veux être guidé" (profil Mathieu)
**When** je confirme ma sélection
**Then** le mode "Guided" est activé automatiquement
**And** le wizard d'onboarding démarre immédiatement (voir Story 11.1 - variante optimisée 4 étapes)
**And** l'interface est simplifiée (options avancées masquées)
**And** les fonctionnalités suivantes sont activées automatiquement :
- Mode guidé (voir Story 11.7)
- Hints contextuels fréquents (voir Story 11.3 - version renforcée)
- Auto-save toutes les 2 minutes (voir Epic 0, Story 0.5)
- Wizard pour actions complexes

**Given** je suis détecté comme persona Mathieu
**When** l'interface se charge
**Then** un indicateur discret s'affiche "Mode guidé activé - Assistance disponible"
**And** je peux désactiver le mode guidé si je deviens plus expérimenté (via Paramètres)

**Given** je crée mon premier dialogue avec succès
**When** j'ai terminé le dialogue (génération + export)
**Then** un message s'affiche "Félicitations ! Premier dialogue créé en X minutes"
**And** le système suggère "Voulez-vous continuer en mode guidé ou passer en mode standard ?"
**And** je peux choisir de rester en mode guidé ou passer en mode standard

**Given** je deviens plus expérimenté (5+ dialogues créés)
**When** j'utilise régulièrement l'application
**Then** le système détecte ma progression
**And** un message s'affiche "Vous maîtrisez bien l'application - Voulez-vous passer en mode standard ?"
**And** je peux accepter ou refuser

**Technical Requirements:**
- Frontend : Détection nouvel utilisateur via localStorage ou backend (flag `isNewUser`, `dialogueCount`)
- Profil : Service `UserProfileService` pour détecter persona (Mathieu vs Marc) basé sur usage patterns
- Auto-activation : Activation automatique mode guidé si `isNewUser === true` ou `dialogueCount === 0`
- Questionnaire : Composant `FirstRunQuestionnaire.tsx` avec questions courtes pour détecter niveau
- Persistence : Sauvegarder préférences mode dans localStorage ou backend (profil utilisateur)
- Tests : Unit (détection persona), Integration (activation mode guidé), E2E (workflow premier run)

**References:** Story 11.5 (détection compétence), Story 11.7 (mode guidé), Story 11.1 (wizard onboarding), Story 11.9 (wizard optimisé Mathieu), NFR-U1 (Usability <30min)

---

### Story 11.9: Wizard optimisé pour création premier dialogue (persona Mathieu) (V1.0)

As a **nouvel utilisateur occasionnel (persona Mathieu)**,
I want **un wizard optimisé pour créer mon premier dialogue**,
So that **je peux créer un dialogue complet en <30min sans support externe**.

**Note:** Cette story est une variante optimisée de Story 11.1, spécifiquement pour persona Mathieu avec 4 étapes simplifiées au lieu de 5.

**Acceptance Criteria:**

**Given** je suis détecté comme persona Mathieu (voir Story 11.8)
**When** le wizard démarre automatiquement
**Then** un wizard step-by-step s'affiche avec 4 étapes simples :
- **Étape 1** : "Quel lieu pour ce dialogue ?" (recherche avec autocomplétion)
- **Étape 2** : "Quel personnage parle ?" (liste filtrée par lieu sélectionné)
- **Étape 3** : "Contexte ou thème ?" (input texte libre avec suggestions)
- **Étape 4** : "Instructions spéciales ?" (template pré-rempli avec exemples)

**Given** je complète l'étape 1 (lieu)
**When** je tape "Taverne" dans le champ de recherche
**Then** une liste filtrée s'affiche avec lieux correspondants (ex: "Taverne des Poutres Brisées")
**And** je peux sélectionner un lieu en cliquant ou avec Enter
**And** l'étape suivante se débloque automatiquement

**Given** je complète l'étape 2 (personnage)
**When** je sélectionne un personnage
**Then** la liste est filtrée par le lieu sélectionné (personnages liés au lieu)
**And** je peux voir une description courte du personnage
**And** l'étape suivante se débloque automatiquement

**Given** je complète l'étape 3 (contexte)
**When** je saisis un thème (ex: "Légende Avili Éternel Retour")
**Then** des suggestions contextuelles s'affichent basées sur le lieu et personnage sélectionnés
**And** je peux utiliser une suggestion ou continuer avec mon texte
**And** l'étape suivante se débloque automatiquement

**Given** je complète l'étape 4 (instructions)
**When** je consulte les templates pré-remplis
**Then** des templates contextuels s'affichent (ex: "Ton informel, ambiance taverne, révélation progressive lore")
**And** je peux sélectionner un template ou personnaliser
**And** un bouton "Générer dialogue" devient actif

**Given** je complète toutes les étapes du wizard
**When** je clique sur "Générer dialogue"
**Then** le dialogue est généré avec les paramètres du wizard
**And** le wizard se ferme et l'éditeur de graphe s'ouvre avec le dialogue généré
**And** un message s'affiche "Premier dialogue créé ! Vous pouvez maintenant explorer l'éditeur"

**Given** je complète le wizard en <30 minutes
**When** le dialogue est généré
**Then** un message de succès s'affiche "Premier dialogue créé en X minutes - Objectif <30min atteint !"
**And** des statistiques s'affichent (nombre nœuds générés, temps total, qualité estimée)

**Technical Requirements:**
- Frontend : Composant `FirstDialogueWizard.tsx` avec 4 étapes optimisées pour persona Mathieu (variante de `OnboardingWizard.tsx`)
- Intégration : Wizard pré-remplit `GenerationPanel` avec valeurs sélectionnées (personnages, lieux, contexte)
- Templates : Service `ContextualTemplatesService` pour générer templates pré-remplis basés sur lieu/personnage
- Suggestions : Service `ContextualSuggestionsService` pour suggestions contextuelles (thèmes, instructions)
- Navigation : Boutons "Précédent" / "Suivant" / "Passer" pour navigation fluide
- Persistence : Sauvegarder progression wizard dans localStorage (récupération si fermeture accidentelle)
- Tests : Unit (wizard logique), Integration (wizard + génération), E2E (workflow premier dialogue <30min)

**References:** Story 11.1 (wizard onboarding général), Story 11.8 (détection persona Mathieu), Story 1.1 (génération dialogue), NFR-U1 (Usability <30min)

---

### Story 11.10: Assistance contextuelle renforcée pour persona Mathieu (V1.0)

As a **nouvel utilisateur occasionnel (persona Mathieu)**,
I want **recevoir une assistance contextuelle renforcée**,
So that **je comprends chaque étape et je peux progresser sans hésitation**.

**Note:** Cette story est une version renforcée de Story 11.3, spécifiquement pour persona Mathieu avec messages simplifiés et hints plus fréquents.

**Acceptance Criteria:**

**Given** je suis en mode guidé (persona Mathieu détecté)
**When** je consulte l'interface
**Then** des hints contextuels fréquents s'affichent :
- Au démarrage : "Bienvenue ! Commencez par sélectionner un lieu pour votre dialogue"
- Sur chaque champ : Tooltip explicatif avec exemples
- Sur chaque action : Indication claire de ce qui va se passer

**Given** je consulte un champ complexe (ex: "Instructions spéciales")
**When** je survole le champ ou clique sur "?"
**Then** un panneau d'aide contextuelle s'affiche avec :
- Description du champ (langage simple, non-technique)
- Exemples concrets (ex: "Ton informel, ambiance taverne")
- Bonnes pratiques
- Lien vers documentation complète (optionnel)

**Given** je génère mon premier dialogue
**When** la génération est en cours
**Then** un message contextuel s'affiche "Génération en cours... Cela peut prendre 30-60 secondes"
**And** un indicateur de progression s'affiche (si disponible)
**And** des conseils s'affichent pendant l'attente (ex: "Pendant l'attente, vous pouvez préparer vos choix joueur")

**Given** je génère mon premier dialogue
**When** la génération est terminée
**Then** un message contextuel s'affiche "Dialogue généré ! Voici ce que vous pouvez faire maintenant :"
**And** une liste d'actions suggérées s'affiche :
- "Ajouter des choix joueur" (avec lien vers fonctionnalité)
- "Générer des nœuds suivants" (avec lien vers batch generation)
- "Exporter vers Unity" (avec lien vers export)

**Given** je rencontre une erreur (ex: validation échoue)
**When** l'erreur est affichée
**Then** un message d'aide contextuelle s'affiche expliquant :
- Ce qui s'est passé (langage simple, non-technique)
- Pourquoi l'erreur s'est produite
- Comment la corriger (étapes détaillées avec exemples)
- Lien "En savoir plus" vers documentation (optionnel)

**Technical Requirements:**
- Frontend : Système de hints contextuels renforcé pour mode guidé (composant `EnhancedContextualHelp.tsx` - variante de `ContextualHelp.tsx`)
- Détection : Service `UserActionTracker` pour détecter inactivité, erreurs, premières utilisations
- Messages : Messages d'aide simplifiés (langage non-technique) pour persona Mathieu
- Tooltips : Tooltips détaillés sur tous les champs et actions en mode guidé
- Suggestions : Suggestions d'actions après chaque étape importante (génération, export, etc.)
- Configuration : Préférences utilisateur pour activer/désactiver hints (localStorage)
- Tests : Unit (détection actions), Integration (assistance contextuelle), E2E (workflow assistance)

**References:** Story 11.3 (aide contextuelle générale), Story 11.8 (détection persona Mathieu), Story 11.9 (wizard premier dialogue), NFR-U1 (Usability <30min)

---

### Story 11.11: Valider expérience premier run complète (objectif <30min) (V1.0)

As a **nouvel utilisateur occasionnel (persona Mathieu)**,
I want **créer mon premier dialogue complet en <30 minutes**,
So that **je peux valider que l'expérience premier run fonctionne end-to-end**.

**Acceptance Criteria:**

**Given** je suis un nouvel utilisateur (persona Mathieu)
**When** je démarre l'application pour la première fois
**Then** l'expérience complète premier run est validée :
- Détection automatique persona Mathieu (<1min)
- Activation mode guidé automatique (<10s)
- Wizard premier dialogue (<5min)
- Génération premier nœud (<2min)
- Ajout choix joueur (<2min)
- Génération batch nœuds suivants (<5min)
- Validation qualité (<2min)
- Export Unity (<1min)
- **Total : <30min** (objectif NFR-U1)

**Given** je complète le premier run
**When** je termine mon premier dialogue
**Then** un rapport de succès s'affiche :
- Temps total : X minutes
- Objectif <30min : ✅ Atteint ou ⚠️ Presque (avec suggestions)
- Nombre nœuds créés : Y
- Qualité estimée : Z/10
- Actions suivantes suggérées

**Given** je dépasse 30 minutes pour le premier run
**When** le temps dépasse 30 minutes
**Then** un message s'affiche "Vous avez dépassé l'objectif de 30 minutes. Besoin d'aide ?"
**And** des suggestions s'affichent pour accélérer (ex: "Utilisez les templates pré-remplis", "Générez en batch")
**And** je peux accéder à l'aide ou continuer

**Given** je complète le premier run avec succès (<30min)
**When** le dialogue est exporté
**Then** un message de félicitations s'affiche "🎉 Premier dialogue créé avec succès en X minutes !"
**And** des statistiques s'affichent :
- Temps par étape (wizard, génération, édition, export)
- Nombre nœuds créés
- Qualité estimée
- Suggestions d'amélioration pour prochain dialogue

**Given** je complète le premier run
**When** je consulte les métriques
**Then** un dashboard "Premier run" s'affiche avec :
- Timeline de l'expérience (étapes complétées)
- Temps passé par étape
- Points de friction identifiés (si >30min)
- Suggestions d'optimisation

**Technical Requirements:**
- Frontend : Service `FirstRunTracker` pour tracker temps et étapes du premier run
- Métriques : Enregistrement temps par étape (wizard, génération, édition, export)
- Validation : Vérification objectif <30min avec alertes si dépassement
- Rapport : Composant `FirstRunReport.tsx` avec statistiques et suggestions
- Dashboard : Vue "Premier run" avec timeline et métriques détaillées
- Persistence : Sauvegarder métriques premier run dans localStorage ou backend
- Tests : Unit (tracking premier run), Integration (métriques), E2E (workflow complet <30min)

**References:** Story 11.8 (détection persona), Story 11.9 (wizard premier dialogue), Story 11.10 (assistance contextuelle), NFR-U1 (Usability <30min), NFR-R3 (Data Loss Prevention)

