## Epic 9: Variables et intégration systèmes de jeu

Les utilisateurs peuvent définir des variables et flags dans les dialogues pour créer des branches conditionnelles dynamiques. Le système permet conditions de visibilité, effets déclenchés par choix joueur, preview de scénarios, validation références, et intégration stats de jeu (V3.0+).

**FRs covered:** FR89-94 (variables/flags, conditions, effets, preview, validation, intégration stats)

**NFRs covered:** NFR-P3 (API Response <200ms), NFR-I3 (Game System Integration V3.0+)

**Valeur utilisateur:** Créer des dialogues réactifs qui s'adaptent aux choix et état du joueur, permettant des expériences narratives dynamiques et personnalisées.

**Dépendances:** Epic 1 (dialogues), Epic 2 (éditeur graphe), Epic 4 (validation)

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

### Story 9.1: Définir variables et flags dans dialogues (V1.0+) (FR89)

As a **utilisateur créant des dialogues**,
I want **définir des variables et flags dans mes dialogues**,
So that **je peux créer des branches conditionnelles qui réagissent à l'état du jeu et aux choix du joueur**.

**Acceptance Criteria:**

**Given** j'ai un dialogue ouvert dans l'éditeur
**When** j'ouvre "Variables et flags" dans le panneau de configuration
**Then** je peux voir la liste des flags disponibles depuis le catalogue (existant `InGameFlagsModal`)
**And** je peux sélectionner des flags booléens, numériques, ou string
**And** les flags sélectionnés sont associés au dialogue

**Given** je sélectionne un flag booléen (ex: "hasMetAkthar")
**When** le flag est sélectionné
**Then** le flag apparaît dans la liste "Flags utilisés dans ce dialogue"
**And** je peux définir sa valeur initiale (true/false)
**And** le flag est sauvegardé avec le dialogue

**Given** je sélectionne un flag numérique (ex: "reputationAkthar")
**When** le flag est sélectionné
**Then** je peux définir sa valeur initiale (ex: 50)
**And** je peux définir des plages de valeurs (min/max) pour validation

**Given** je sélectionne un flag string (ex: "playerName")
**When** le flag est sélectionné
**Then** je peux définir sa valeur initiale (ex: "Joueur")
**And** le flag est sauvegardé avec le dialogue

**Given** je définis plusieurs flags pour un dialogue
**When** je sauvegarde le dialogue
**Then** tous les flags sont persistés dans les métadonnées du dialogue
**And** les flags sont disponibles pour conditions et effets (voir Stories 9.2-9.3)

**Given** je consulte un dialogue existant
**When** j'ouvre "Variables et flags"
**Then** les flags déjà définis sont affichés avec leurs valeurs
**And** je peux modifier les valeurs ou ajouter/supprimer des flags

**Technical Requirements:**
- Backend : Endpoint `/api/v1/dialogues/{id}/flags` (GET liste, POST ajouter, PUT modifier, DELETE supprimer)
- Service : `DialogueFlagsService` avec méthodes CRUD flags pour dialogues
- Catalogue : Réutiliser `FlagCatalogService` (existant) pour liste flags disponibles
- Base de données : Table `dialogue_flags` (dialogue_id, flag_id, value, type) ou JSON dans métadonnées dialogue
- Frontend : Composant `DialogueFlagsPanel.tsx` avec intégration `InGameFlagsModal` (existant) pour sélection flags
- Types : Support bool, number, string flags (déjà implémenté dans `InGameFlag` type)
- Tests : Unit (gestion flags), Integration (API flags), E2E (workflow flags)

**References:** FR89 (variables/flags V1.0+), Story 9.2 (conditions), Story 9.3 (effets), Epic 1 (dialogues)

---

### Story 9.2: Définir conditions de visibilité sur nœuds (si variable X = Y, afficher nœud) (FR90)

As a **utilisateur créant des dialogues**,
I want **définir des conditions de visibilité sur les nœuds (si variable X = Y, afficher nœud)**,
So that **je peux créer des branches de dialogue qui ne s'affichent que si certaines conditions sont remplies**.

**Acceptance Criteria:**

**Given** j'ai un nœud dans le graphe
**When** je sélectionne le nœud et ouvre "Conditions"
**Then** un panneau s'affiche avec champ "Condition de visibilité"
**And** je peux saisir une condition (ex: "hasMetAkthar", "reputationAkthar >= 50", "playerName == 'Marc'")

**Given** je définis une condition booléenne (ex: "hasMetAkthar")
**When** la condition est sauvegardée
**Then** le nœud n'est visible que si le flag `hasMetAkthar` est true
**And** la condition est affichée visuellement sur le nœud (badge "Condition: hasMetAkthar")

**Given** je définis une condition numérique (ex: "reputationAkthar >= 50")
**When** la condition est sauvegardée
**Then** le nœud n'est visible que si `reputationAkthar` est >= 50
**And** la condition est validée syntaxiquement (voir Story 9.5)

**Given** je définis une condition sur un choix joueur
**When** je sélectionne un choix et définis sa condition
**Then** le choix n'est visible que si la condition est remplie
**And** la condition est affichée sur le choix (ex: "[Si reputationAkthar >= 50] Accepter l'alliance")

**Given** un nœud a une condition non remplie
**When** je preview le dialogue (voir Story 9.4)
**Then** le nœud est grisé ou masqué dans le preview
**And** un indicateur affiche "Condition non remplie: hasMetAkthar = false"

**Given** je définis plusieurs conditions (AND/OR)
**When** je saisie "hasMetAkthar AND reputationAkthar >= 50"
**Then** le nœud n'est visible que si TOUTES les conditions sont remplies (AND)
**And** je peux utiliser OR pour conditions alternatives

**Given** je consulte un dialogue avec conditions
**When** j'ouvre le graphe
**Then** les nœuds avec conditions sont marqués visuellement (icône condition, couleur différente)
**And** je peux survoler pour voir la condition complète

**Technical Requirements:**
- Backend : Champ `condition` dans `UnityDialogueNode` (existant) pour conditions nœuds
- Champ `condition` dans `UnityDialogueChoice` (existant) pour conditions choix
- Service : `ConditionParserService` pour parsing et validation conditions (format: "FLAG_NAME", "NOT FLAG_NAME", "flag >= value")
- Frontend : Composant `ConditionEditor.tsx` avec input condition + validation syntaxique
- Validation : Vérifier références flags existent (voir Story 9.5)
- Preview : Intégration avec preview scénarios (voir Story 9.4) pour tester conditions
- Tests : Unit (parsing conditions), Integration (API conditions), E2E (workflow conditions)

**References:** FR90 (conditions visibilité), Story 9.1 (variables/flags), Story 9.4 (preview), Story 9.5 (validation), Epic 2 (éditeur graphe)

---

### Story 9.3: Définir effets déclenchés par choix joueur (set variable, unlock flag) (FR91)

As a **utilisateur créant des dialogues**,
I want **définir des effets déclenchés quand le joueur sélectionne un choix**,
So that **je peux modifier l'état du jeu (variables, flags) en fonction des choix du joueur**.

**Acceptance Criteria:**

**Given** j'ai un choix joueur dans un nœud
**When** je sélectionne le choix et ouvre "Effets"
**Then** un panneau s'affiche avec liste "Effets déclenchés"
**And** je peux ajouter des effets : "Set flag", "Modify variable", "Unlock flag"

**Given** j'ajoute un effet "Set flag" (ex: "hasMetAkthar = true")
**When** l'effet est sauvegardé
**Then** quand le joueur sélectionne ce choix, le flag `hasMetAkthar` est défini à true
**And** l'effet est affiché sur le choix (ex: "[+ hasMetAkthar] Accepter l'alliance")

**Given** j'ajoute un effet "Modify variable" (ex: "reputationAkthar += 10")
**When** l'effet est sauvegardé
**Then** quand le joueur sélectionne ce choix, `reputationAkthar` est augmenté de 10
**And** je peux définir des modifications positives ou négatives (+=, -=, *=, /=)

**Given** j'ajoute un effet "Unlock flag" (ex: "unlockQuestAkthar")
**When** l'effet est sauvegardé
**Then** quand le joueur sélectionne ce choix, le flag `unlockQuestAkthar` est défini à true
**And** l'effet est persistant (flag reste true après le dialogue)

**Given** je définis plusieurs effets sur un même choix
**When** le choix est sélectionné
**Then** tous les effets sont exécutés dans l'ordre défini
**And** un résumé s'affiche "Effets appliqués: hasMetAkthar=true, reputationAkthar+=10"

**Given** je consulte un dialogue avec effets
**When** j'ouvre le graphe
**Then** les choix avec effets sont marqués visuellement (icône effet, couleur différente)
**And** je peux survoler pour voir tous les effets du choix

**Given** je preview un dialogue avec effets (voir Story 9.4)
**When** je sélectionne un choix avec effets
**Then** les effets sont simulés dans le preview
**And** l'état des flags est mis à jour pour les nœuds suivants

**Technical Requirements:**
- Backend : Champ `consequences` dans `UnityDialogueNode` (existant) pour effets nœuds
- Champ `actions` dans `UnityDialogueChoice` (existant partiellement) pour effets choix
- Service : `EffectParserService` pour parsing effets (format: "flag=value", "flag+=delta", "flag-=delta")
- Frontend : Composant `EffectEditor.tsx` avec liste effets + ajout/suppression/modification
- Exécution : Service `EffectExecutionService` pour appliquer effets lors sélection choix (runtime Unity)
- Preview : Intégration avec preview scénarios (voir Story 9.4) pour simuler effets
- Tests : Unit (parsing effets), Integration (API effets), E2E (workflow effets)

**References:** FR91 (effets choix joueur), Story 9.1 (variables/flags), Story 9.4 (preview), Epic 1 (génération dialogues)

---

### Story 9.4: Preview scénarios avec différents états de variables (FR92)

As a **utilisateur créant des dialogues**,
I want **preview des scénarios avec différents états de variables**,
So that **je peux tester comment le dialogue se comporte selon les valeurs des flags et variables**.

**Acceptance Criteria:**

**Given** j'ai un dialogue avec conditions et effets sur les flags
**When** j'ouvre "Preview scénario"
**Then** un panneau s'affiche avec liste des flags du dialogue
**And** je peux définir les valeurs initiales des flags pour le preview

**Given** je définis les valeurs des flags (ex: hasMetAkthar=true, reputationAkthar=50)
**When** je lance le preview
**Then** le graphe s'affiche avec les nœuds visibles selon les conditions
**And** les nœuds avec conditions non remplies sont grisés ou masqués
**And** un indicateur affiche "Preview mode - État: hasMetAkthar=true, reputationAkthar=50"

**Given** je navigue dans le preview en sélectionnant des choix
**When** je sélectionne un choix avec effets
**Then** les effets sont appliqués (flags mis à jour)
**And** les nœuds suivants sont mis à jour selon les nouvelles valeurs de flags
**And** un historique s'affiche "Effets appliqués: reputationAkthar += 10 (50 → 60)"

**Given** je change les valeurs initiales des flags dans le preview
**When** je modifie "reputationAkthar" de 50 à 30
**Then** le graphe se met à jour immédiatement
**And** les nœuds avec condition "reputationAkthar >= 50" deviennent invisibles

**Given** je compare deux scénarios
**When** j'ouvre "Comparer scénarios"
**Then** je peux définir deux états de flags différents (scénario A et B)
**And** les deux graphes sont affichés côte à côte
**And** les différences sont surlignées (nœuds visibles dans A mais pas B, etc.)

**Given** je preview un dialogue complexe avec plusieurs branches conditionnelles
**When** le preview est lancé
**Then** un rapport s'affiche "X nœuds accessibles, Y nœuds masqués par conditions"
**And** je peux voir quels nœuds sont inaccessibles et pourquoi (condition non remplie)

**Given** je quitte le preview
**When** je ferme le panneau preview
**Then** le graphe revient à l'état normal (tous nœuds visibles)
**And** les modifications de flags dans le preview ne sont pas sauvegardées

**Technical Requirements:**
- Backend : Endpoint `/api/v1/dialogues/{id}/preview` (POST) avec état flags initial retourne graphe avec visibilité nœuds
- Service : `DialoguePreviewService` avec méthode `preview_dialogue(dialogue_id, flag_states)` pour simulation
- Évaluation conditions : `ConditionEvaluatorService` pour évaluer conditions selon état flags
- Exécution effets : `EffectExecutionService` pour appliquer effets et mettre à jour état flags
- Frontend : Composant `DialoguePreviewPanel.tsx` avec sélecteur flags + graphe preview + historique effets
- Comparaison : Mode side-by-side pour comparer deux scénarios (optionnel, V1.5+)
- Performance : Preview <200ms pour dialogues <100 nœuds, <1s pour 500+ nœuds
- Tests : Unit (évaluation conditions), Integration (API preview), E2E (workflow preview)

**References:** FR92 (preview scénarios), Story 9.2 (conditions), Story 9.3 (effets), Story 9.1 (variables/flags), NFR-P3 (API Response <200ms)

---

### Story 9.5: Valider références variables (détecter variables non définies) (FR93)

As a **utilisateur créant des dialogues**,
I want **valider que toutes les références de variables dans les conditions et effets sont définies**,
So that **je peux détecter les erreurs avant export et éviter des bugs runtime dans Unity**.

**Acceptance Criteria:**

**Given** j'ai un dialogue avec conditions et effets utilisant des flags
**When** je lance une validation
**Then** toutes les références de flags dans conditions et effets sont vérifiées
**And** les flags non définis sont détectés et listés

**Given** un nœud a une condition "hasMetAkthar" mais le flag n'est pas défini dans le dialogue
**When** la validation est lancée
**Then** une erreur s'affiche "Nœud [stableID] : Condition référence flag non défini 'hasMetAkthar'"
**And** le nœud est surligné dans le graphe (couleur orange)
**And** je peux cliquer sur l'erreur pour éditer le nœud

**Given** un choix a un effet "reputationAkthar += 10" mais le flag n'est pas défini
**When** la validation est lancée
**Then** une erreur s'affiche "Choix [text] : Effet référence flag non défini 'reputationAkthar'"
**And** le choix est surligné dans le graphe

**Given** un flag est défini mais jamais utilisé (ni condition ni effet)
**When** la validation est lancée
**Then** un warning (non-bloquant) s'affiche "Flag 'unusedFlag' défini mais jamais utilisé"
**And** je peux décider de le supprimer ou le garder pour usage futur

**Given** un flag est référencé avec une typo (ex: "hasMetAkthar" vs "hasMetAkhtar")
**When** la validation est lancée
**Then** une erreur s'affiche "Flag 'hasMetAkhtar' non défini - suggestion: 'hasMetAkthar'?"
**And** je peux corriger automatiquement avec la suggestion

**Given** tous les flags référencés sont définis
**When** la validation est lancée
**Then** un message de succès s'affiche "Validation flags : 0 erreurs, X flags utilisés"
**And** la validation se termine en <200ms (NFR-P3)

**Given** je corrige une référence de flag invalide
**When** je modifie la condition/effet pour utiliser un flag valide
**Then** la validation est automatiquement relancée
**And** l'erreur disparaît si la référence est maintenant valide

**Technical Requirements:**
- Backend : Service `FlagValidationService` avec méthode `validate_flag_references(dialogue)` pour détection références invalides
- Parsing : Extraire toutes les références flags depuis conditions et effets (regex ou parser)
- Catalogue : Vérifier références contre flags définis dans dialogue + flags disponibles dans catalogue global
- Suggestions : Algorithme de distance (Levenshtein) pour suggestions typo
- API : Endpoint `/api/v1/dialogues/{id}/validate-flags` (POST) retourne erreurs références flags
- Frontend : Composant `FlagValidationPanel.tsx` affiche erreurs avec navigation vers nœuds/choix concernés
- Auto-fix : Option correction automatique pour suggestions typo (bouton "Corriger")
- Tests : Unit (détection références), Integration (API validation), E2E (workflow validation)

**References:** FR93 (validation références), Story 9.1 (variables/flags), Story 9.2 (conditions), Story 9.3 (effets), Epic 4 (validation), NFR-P3 (API Response <200ms)

---

### Story 9.6: Intégrer stats systèmes de jeu (attributs personnage, réputation) (V3.0+) (FR94)

As a **utilisateur créant des dialogues**,
I want **intégrer les stats des systèmes de jeu (attributs personnage, réputation) dans les conditions et effets**,
So that **je peux créer des dialogues qui réagissent aux capacités et réputation du personnage joueur**.

**Acceptance Criteria:**

**Given** le système d'intégration stats est disponible (V3.0+)
**When** j'ouvre "Intégration systèmes de jeu"
**Then** un panneau s'affiche avec liste des systèmes disponibles : Attributs personnage, Réputation, Compétences, Inventaire
**And** je peux configurer la connexion avec le système de jeu Unity

**Given** je configure l'intégration avec "Attributs personnage"
**When** la connexion est établie
**Then** je peux utiliser les attributs dans les conditions (ex: "strength >= 15", "intelligence < 10")
**And** les attributs sont synchronisés depuis Unity (API ou fichier de configuration)

**Given** je configure l'intégration avec "Réputation"
**When** la connexion est établie
**Then** je peux utiliser la réputation dans les conditions (ex: "reputationAkthar >= 50")
**And** je peux modifier la réputation via effets (ex: "reputationAkthar += 10")

**Given** je définis une condition basée sur attribut personnage (ex: "strength >= 15")
**When** la condition est sauvegardée
**Then** le nœud n'est visible que si l'attribut `strength` du personnage est >= 15
**And** la condition est validée syntaxiquement (voir Story 9.5)

**Given** je définis un effet modifiant réputation (ex: "reputationAkthar += 10")
**When** l'effet est sauvegardé
**Then** quand le joueur sélectionne ce choix, la réputation est modifiée dans Unity
**And** l'effet est synchronisé avec le système de jeu

**Given** je preview un dialogue avec intégration stats
**When** je lance le preview
**Then** je peux définir les valeurs des stats pour le preview (ex: strength=18, reputationAkthar=60)
**And** le preview simule correctement les conditions basées sur stats

**Given** le système de jeu Unity n'est pas disponible
**When** j'essaie d'utiliser des stats dans conditions/effets
**Then** un warning s'affiche "Système de jeu non connecté - conditions/effets stats ne fonctionneront pas en runtime"
**And** je peux quand même définir les conditions/effets (validation syntaxique uniquement)

**Technical Requirements:**
- Backend : Service `GameSystemIntegrationService` pour connexion avec systèmes de jeu Unity
- API Unity : Endpoint ou fichier de configuration pour récupérer stats personnage (attributs, réputation, compétences)
- Synchronisation : Polling ou webhook pour synchroniser stats depuis Unity vers DialogueGenerator
- Conditions : Extension `ConditionEvaluatorService` pour évaluer conditions basées sur stats (ex: "strength >= 15")
- Effets : Extension `EffectExecutionService` pour appliquer effets modifiant stats (ex: "reputation += 10")
- Frontend : Composant `GameSystemIntegrationPanel.tsx` avec configuration connexion + liste stats disponibles
- Preview : Intégration avec preview scénarios (voir Story 9.4) pour tester conditions/effets stats
- Tests : Unit (intégration stats), Integration (API Unity), E2E (workflow intégration stats)

**References:** FR94 (intégration stats V3.0+), Story 9.2 (conditions), Story 9.3 (effets), Story 9.4 (preview), NFR-I3 (Game System Integration V3.0+)

