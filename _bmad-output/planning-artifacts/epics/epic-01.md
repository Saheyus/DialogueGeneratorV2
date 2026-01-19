### Epic 1: Génération de dialogues assistée par IA

Les utilisateurs peuvent générer des nœuds de dialogue de qualité professionnelle avec assistance LLM, gérer les coûts et itérer rapidement. Le système permet la génération single/batch, l'édition manuelle, l'auto-link, et fournit transparence complète sur les coûts et prompts utilisés.

**FRs covered:** FR1-10 (génération, édition, auto-link, régénération), FR72-79 (estimation coûts, logs, fallback provider)

**NFRs covered:** NFR-P2 (LLM Generation <30s single, <2min batch), NFR-I2 (LLM API Reliability >99%), NFR-R4 (Error Recovery LLM >95%)

**Valeur utilisateur:** Produire des dialogues CRPG qualité Disco Elysium en 1H au lieu de 1 semaine, avec contrôle total sur la qualité et les coûts.

**Dépendances:** Epic 0 (infrastructure), Epic 3 (contexte GDD requis pour génération)

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

### Story 1.1: Générer un nœud de dialogue single avec LLM (FR1)

As a **utilisateur créant des dialogues**,
I want **générer un nœud de dialogue unique avec assistance LLM basé sur le contexte GDD sélectionné**,
So that **je peux créer rapidement des dialogues de qualité professionnelle sans écrire manuellement chaque ligne**.

**Acceptance Criteria:**

**Given** j'ai sélectionné un contexte GDD (personnages, lieux, région) et saisi des instructions
**When** je clique sur "Générer"
**Then** un nœud de dialogue est généré avec texte, speaker, et choix (si applicable)
**And** le nœud apparaît dans le graphe avec un stableID unique
**And** la génération se termine en <30 secondes (NFR-P2)

**Given** je lance une génération single
**When** la génération est en cours
**Then** la modal de progression (Epic 0 Story 0.2) affiche le streaming en temps réel
**And** je peux interrompre la génération si nécessaire

**Given** la génération réussit
**When** le nœud est créé
**Then** le nœud est automatiquement lié au graphe (auto-link, voir Story 1.9)
**And** je peux accepter ou rejeter le nœud (voir Story 1.4)

**Given** je spécifie des instructions de génération (tone, style, theme)
**When** le nœud est généré
**Then** le nœud respecte les instructions (tone cohérent, style demandé, theme présent)
**And** les instructions sont incluses dans le prompt LLM

**Technical Requirements:**
- Backend : Endpoint `/api/v1/dialogues/generate/unity-dialogue` (existant, à améliorer)
- Service : `UnityDialogueGenerationService.generate_dialogue_node()` avec Structured Output
- LLM : Utilise provider sélectionné (OpenAI/Mistral via Epic 0 Story 0.3)
- Frontend : Composant `GenerationPanel.tsx` avec bouton "Générer"
- Integration : Epic 0 Story 0.2 (Progress Modal) pour feedback streaming
- Tests : Unit (génération nœud), Integration (API génération), E2E (workflow complet)

**References:** FR1 (génération single), FR3 (instructions), NFR-P2 (LLM Generation <30s), Epic 0 Story 0.2 (Progress Modal)

---

### Story 1.2: Générer batch de nœuds (3-8) depuis choix existants (FR2)

As a **utilisateur créant des dialogues**,
I want **générer plusieurs nœuds (3-8) en une seule requête depuis des choix joueur existants**,
So that **je peux créer rapidement des branches de dialogue complètes sans générer chaque nœud individuellement**.

**Acceptance Criteria:**

**Given** j'ai un nœud avec des choix joueur (ex: "Accepter", "Refuser", "Questionner")
**When** je sélectionne "Générer batch" et choisis 3-8 choix
**Then** un nœud est généré pour chaque choix sélectionné
**And** tous les nœuds sont générés en <2 minutes (NFR-P2 batch)
**And** chaque nœud est automatiquement lié au nœud parent (connexion parent→enfant)

**Given** je lance une génération batch
**When** la génération est en cours
**Then** la modal de progression affiche "Génération batch : 3/8 nœuds" avec progression
**And** je peux interrompre la génération batch (tous les nœuds en cours sont annulés)

**Given** la génération batch réussit partiellement (5/8 nœuds générés, 3 échecs)
**When** les résultats sont affichés
**Then** les 5 nœuds réussis sont ajoutés au graphe
**And** un message d'erreur liste les 3 choix qui ont échoué
**And** je peux régénérer individuellement les choix échoués

**Given** je génère un batch avec contexte GDD
**When** les nœuds sont générés
**Then** chaque nœud utilise le même contexte GDD (cohérence narrative)
**And** les nœuds sont variés (pas de répétition, chaque choix mène à un dialogue unique)

**Technical Requirements:**
- Backend : Endpoint `/api/v1/dialogues/generate/batch` (nouveau) avec paramètre `choices: List[str]`
- Service : `UnityDialogueGenerationService.generate_batch_nodes()` avec boucle génération + gestion erreurs
- Frontend : Composant `BatchGenerationPanel.tsx` avec sélection choix multiples (checkboxes)
- Progress : Modal affiche progression batch (X/Y nœuds générés)
- Auto-link : Chaque nœud généré est connecté au parent (voir Story 1.9)
- Tests : Unit (batch génération), Integration (API batch), E2E (workflow batch complet)

**References:** FR2 (génération batch), NFR-P2 (LLM Generation <2min batch), Story 1.9 (auto-link)

---

### Story 1.3: Spécifier instructions de génération (tone, style, theme) (FR3)

As a **utilisateur générant des dialogues**,
I want **spécifier des instructions de génération (tone, style, theme) pour chaque génération**,
So that **les dialogues générés correspondent exactement à l'ambiance et au style narratif souhaités**.

**Acceptance Criteria:**

**Given** je suis sur l'écran de génération
**When** je saisis des instructions dans le champ "Instructions" (ex: "Tone: sombre, Style: poétique, Theme: trahison")
**Then** les instructions sont incluses dans le prompt LLM
**And** le nœud généré reflète ces instructions (tone sombre, style poétique, theme trahison)

**Given** j'ai sauvegardé un preset (Epic 0 Story 0.4)
**When** je charge le preset
**Then** les instructions du preset sont pré-remplies dans le champ "Instructions"
**And** je peux modifier les instructions avant génération

**Given** je spécifie des instructions vides
**When** je lance une génération
**Then** des instructions par défaut sont utilisées (tone neutre, style standard)
**And** un message informatif s'affiche "Instructions par défaut utilisées"

**Given** je spécifie des instructions très longues (>500 mots)
**When** je lance une génération
**Then** un warning s'affiche "Instructions longues - peut affecter le budget tokens"
**And** la génération continue normalement (pas de blocage)

**Technical Requirements:**
- Frontend : Champ texte `userInstructions` dans `GenerationPanel.tsx` (existant, à améliorer)
- Backend : Intégration instructions dans `PromptEngine.build_prompt()` (existant)
- Validation : Longueur max instructions (optionnel, warning si >500 mots)
- Presets : Integration avec Epic 0 Story 0.4 (presets incluent instructions)
- Tests : Unit (instructions incluses dans prompt), Integration (génération avec instructions), E2E (instructions appliquées)

**References:** FR3 (instructions génération), Epic 0 Story 0.4 (presets), FR55-63 (templates)

---

### Story 1.4: Accepter ou rejeter nœuds générés inline (FR4)

As a **utilisateur générant des dialogues**,
I want **accepter ou rejeter les nœuds générés directement dans le graphe**,
So that **je peux itérer rapidement sur la qualité des dialogues sans workflow complexe**.

**Acceptance Criteria:**

**Given** un nœud vient d'être généré et apparaît dans le graphe
**When** je survole le nœud
**Then** des boutons "Accepter" (✓) et "Rejeter" (✗) s'affichent sur le nœud
**And** le nœud est en état "pending" (couleur orange/border dashed)

**Given** je clique sur "Accepter"
**When** le nœud est accepté
**Then** le nœud passe en état "accepted" (couleur verte/border solid)
**And** le nœud est sauvegardé dans le dialogue (persisté)
**And** les boutons Accepter/Rejeter disparaissent

**Given** je clique sur "Rejeter"
**When** le nœud est rejeté
**Then** le nœud est supprimé du graphe (pas sauvegardé)
**And** un message "Nœud rejeté" s'affiche
**And** je peux régénérer le nœud avec instructions ajustées (voir Story 1.10)

**Given** j'ai plusieurs nœuds pending dans le graphe
**When** je navigue dans le graphe
**Then** tous les nœuds pending affichent les boutons Accepter/Rejeter
**And** je peux accepter/rejeter chaque nœud indépendamment

**Given** je ferme l'application avec des nœuds pending
**When** je rouvre l'application
**Then** les nœuds pending sont restaurés (session recovery)
**And** je peux toujours accepter/rejeter ces nœuds

**Technical Requirements:**
- Frontend : Composant `DialogueNode.tsx` avec état "pending/accepted/rejected" + boutons inline
- Zustand store : `useGraphStore` avec méthode `acceptNode(nodeId)`, `rejectNode(nodeId)`
- Backend : Endpoint `/api/v1/dialogues/{id}/nodes/{nodeId}/accept` (POST), `/reject` (POST)
- State : Nœuds pending stockés dans dialogue JSON avec flag `status: "pending"`
- Tests : Unit (accept/reject logic), Integration (API accept/reject), E2E (workflow accept/reject)

**References:** FR4 (accepter/rejeter), FR95-101 (session management), Story 1.10 (régénération)

---

### Story 1.5: Éditer manuellement le contenu des nœuds générés (FR5)

As a **utilisateur créant des dialogues**,
I want **éditer manuellement le contenu des nœuds générés (texte, speaker, metadata)**,
So that **je peux affiner et personnaliser les dialogues générés par l'IA**.

**Acceptance Criteria:**

**Given** un nœud est généré et accepté dans le graphe
**When** je double-clique sur le nœud (ou clic droit → "Éditer")
**Then** un panneau d'édition s'ouvre avec les champs : texte, speaker, metadata
**And** je peux modifier chaque champ

**Given** je modifie le texte d'un nœud
**When** je sauvegarde (Ctrl+S ou bouton "Sauvegarder")
**Then** les modifications sont persistées dans le dialogue
**And** un indicateur "Modifié" s'affiche sur le nœud (icône étoile)
**And** l'auto-save (Epic 0 Story 0.5) sauvegarde les modifications dans les 2 minutes

**Given** je modifie le speaker d'un nœud
**When** le speaker n'existe pas dans le GDD
**Then** un warning s'affiche "Speaker 'X' non trouvé dans GDD"
**And** je peux quand même sauvegarder (speaker custom autorisé)

**Given** je modifie les metadata d'un nœud (tags, conditions, effets)
**When** je sauvegarde
**Then** les metadata sont validées (format JSON Unity)
**And** les erreurs de validation sont affichées avant sauvegarde

**Given** j'annule l'édition (Escape ou bouton "Annuler")
**When** je ferme le panneau d'édition
**Then** les modifications non sauvegardées sont perdues
**And** un message de confirmation s'affiche si modifications non sauvegardées

**Technical Requirements:**
- Frontend : Composant `NodeEditorPanel.tsx` avec formulaires texte/speaker/metadata
- Zustand store : `useGraphStore` avec méthode `updateNode(nodeId, updates)`
- Backend : Endpoint `/api/v1/dialogues/{id}/nodes/{nodeId}` (PUT) pour mise à jour nœud
- Validation : Format Unity JSON (Pydantic models) avant sauvegarde
- Integration : Epic 0 Story 0.5 (auto-save) pour sauvegarde automatique
- Tests : Unit (édition nœud), Integration (API update), E2E (workflow édition complet)

**References:** FR5 (édition manuelle), FR48 (validation JSON Unity), Epic 0 Story 0.5 (auto-save)

---

### Story 1.6: Créer manuellement des nœuds sans LLM (FR6)

As a **utilisateur créant des dialogues**,
I want **créer des nœuds de dialogue manuellement sans génération LLM**,
So that **je peux ajouter des dialogues spécifiques ou corriger des nœuds sans utiliser l'IA**.

**Acceptance Criteria:**

**Given** je suis dans l'éditeur de graphe
**When** je clique sur "Nouveau nœud" (bouton + ou menu contextuel)
**Then** un nœud vide est créé dans le graphe avec stableID unique
**And** le panneau d'édition s'ouvre automatiquement pour remplir le contenu

**Given** je crée un nœud manuellement
**When** je remplis les champs (texte, speaker, metadata)
**Then** le nœud est sauvegardé avec le même format que les nœuds générés
**And** le nœud est immédiatement visible dans le graphe

**Given** je crée un nœud manuellement sans texte
**When** je sauvegarde
**Then** un warning s'affiche "Nœud vide - ajouter du texte"
**And** je peux quand même sauvegarder (nœud placeholder autorisé)

**Given** je crée un nœud manuellement
**When** je crée le nœud
**Then** je peux immédiatement créer des connexions vers d'autres nœuds (drag-and-drop)
**And** le nœud peut recevoir des connexions depuis d'autres nœuds

**Given** je crée plusieurs nœuds manuellement rapidement
**When** les nœuds sont créés
**Then** chaque nœud a un stableID unique (pas de collision)
**And** les nœuds sont positionnés automatiquement dans le graphe (auto-layout)

**Technical Requirements:**
- Frontend : Bouton "Nouveau nœud" dans `GraphEditor.tsx` + menu contextuel
- Zustand store : `useGraphStore` avec méthode `createEmptyNode()` retournant nœud avec stableID
- Backend : Endpoint `/api/v1/dialogues/{id}/nodes` (POST) pour créer nœud vide
- Auto-layout : Positionnement automatique nouveau nœud (React Flow auto-layout)
- Integration : Même format Unity JSON que nœuds générés (cohérence)
- Tests : Unit (création nœud vide), Integration (API create node), E2E (workflow création manuelle)

**References:** FR6 (création manuelle), FR22-35 (graph editor), Epic 0 Story 0.1 (stableID)

---

### Story 1.7: Dupliquer des nœuds existants pour créer des variantes (FR7)

As a **utilisateur créant des dialogues**,
I want **dupliquer des nœuds existants pour créer des variantes rapidement**,
So that **je peux itérer sur des versions alternatives sans recréer le nœud depuis zéro**.

**Acceptance Criteria:**

**Given** j'ai un nœud dans le graphe
**When** je sélectionne le nœud et clique sur "Dupliquer" (menu contextuel ou bouton)
**Then** une copie du nœud est créée avec un nouveau stableID unique
**And** le nœud dupliqué est positionné à côté du nœud original (offset visuel)
**And** le panneau d'édition s'ouvre pour modifier la copie

**Given** je duplique un nœud avec des connexions
**When** le nœud est dupliqué
**Then** le nœud dupliqué n'a PAS de connexions (copie isolée)
**And** je peux créer de nouvelles connexions pour la variante

**Given** je duplique un nœud avec metadata (tags, conditions, effets)
**When** le nœud est dupliqué
**Then** toutes les metadata sont copiées dans le nœud dupliqué
**And** je peux modifier les metadata indépendamment

**Given** je duplique plusieurs nœuds en sélection multiple
**When** je sélectionne 3 nœuds et clique "Dupliquer"
**Then** 3 copies sont créées (une par nœud sélectionné)
**And** chaque copie a un stableID unique
**And** les copies sont positionnées en groupe à côté des originaux

**Given** je duplique un nœud
**When** je modifie le nœud dupliqué
**Then** les modifications n'affectent pas le nœud original
**And** les deux nœuds sont indépendants (pas de lien de dépendance)

**Technical Requirements:**
- Frontend : Action "Dupliquer" dans menu contextuel `DialogueNode.tsx` + sélection multiple
- Zustand store : `useGraphStore` avec méthode `duplicateNode(nodeId)` retournant nouveau nœud
- Backend : Endpoint `/api/v1/dialogues/{id}/nodes/{nodeId}/duplicate` (POST) pour duplication
- Positionnement : Offset visuel (ex: +50px x, +50px y) pour distinguer copie de l'original
- Metadata : Copie profonde (deep copy) de toutes les propriétés sauf stableID et connexions
- Tests : Unit (duplication logique), Integration (API duplicate), E2E (workflow duplication)

**References:** FR7 (duplication), FR31-32 (sélection multiple), Epic 0 Story 0.1 (stableID)

---

### Story 1.8: Supprimer des nœuds du dialogue (FR8)

As a **utilisateur créant des dialogues**,
I want **supprimer des nœuds du dialogue**,
So that **je peux nettoyer et réorganiser le graphe en supprimant les nœuds non désirés**.

**Acceptance Criteria:**

**Given** j'ai un nœud dans le graphe
**When** je sélectionne le nœud et clique sur "Supprimer" (menu contextuel ou touche Delete)
**Then** une confirmation s'affiche "Supprimer ce nœud ? Les connexions seront également supprimées"
**And** j'ai les options "Supprimer" et "Annuler"

**Given** je confirme la suppression
**When** le nœud est supprimé
**Then** le nœud disparaît du graphe
**And** toutes les connexions (entrantes et sortantes) sont également supprimées
**And** le nœud est supprimé du dialogue (persisté)

**Given** je supprime un nœud avec plusieurs connexions
**When** le nœud est supprimé
**Then** un warning s'affiche "Nœud supprimé - X connexions supprimées"
**And** les nœuds orphelins sont détectés (validation structurelle, voir Epic 4)

**Given** je supprime plusieurs nœuds en sélection multiple
**When** je sélectionne 3 nœuds et appuie sur Delete
**Then** une confirmation s'affiche "Supprimer 3 nœuds ?"
**And** tous les nœuds sélectionnés sont supprimés en une seule action

**Given** je supprime un nœud par erreur
**When** je supprime le nœud
**Then** je peux annuler avec Ctrl+Z (undo, voir FR35)
**And** le nœud et ses connexions sont restaurés

**Technical Requirements:**
- Frontend : Action "Supprimer" dans menu contextuel `DialogueNode.tsx` + touche Delete keyboard
- Zustand store : `useGraphStore` avec méthode `deleteNode(nodeId)` + confirmation modal
- Backend : Endpoint `/api/v1/dialogues/{id}/nodes/{nodeId}` (DELETE) pour suppression
- Connexions : Suppression cascade des connexions (orphans détectés par validation)
- Undo/Redo : Integration avec système undo/redo (FR35, Epic 2)
- Tests : Unit (suppression logique), Integration (API delete), E2E (workflow suppression + undo)

**References:** FR8 (suppression), FR35 (undo/redo), FR40 (orphans), Epic 4 (validation structurelle)

---

### Story 1.9: Auto-link des nœuds générés au graphe existant (FR9)

As a **utilisateur générant des dialogues**,
I want **que les nœuds générés soient automatiquement liés à la structure du graphe existante**,
So that **je n'ai pas à créer manuellement les connexions après chaque génération**.

**Acceptance Criteria:**

**Given** je génère un nœud depuis un nœud parent existant
**When** le nœud est généré
**Then** une connexion automatique est créée du nœud parent vers le nouveau nœud
**And** la connexion est visible dans le graphe (flèche parent→enfant)

**Given** je génère un batch de nœuds depuis des choix joueur
**When** les nœuds sont générés
**Then** chaque nœud est automatiquement lié au nœud parent (connexion depuis le choix vers le nouveau nœud)
**And** chaque connexion utilise le texte du choix comme label (ex: "Accepter" → nœud généré)

**Given** je génère un nœud "Continue" (suite d'un dialogue existant)
**When** le nœud est généré
**Then** le nœud est automatiquement lié au nœud cible spécifié (targetNode mis à jour)
**And** la connexion est créée dans le bon sens (parent→nouveau nœud)

**Given** je génère un nœud sans contexte parent (génération standalone)
**When** le nœud est généré
**Then** le nœud est créé sans connexion automatique (nœud isolé)
**And** je peux créer manuellement des connexions vers ce nœud

**Given** je génère un nœud qui crée un cycle (A → B → C → A)
**When** le nœud est généré
**Then** le cycle est détecté par la validation (Epic 0 Story 0.6)
**And** un warning s'affiche "Cycle détecté" (non-bloquant)
**And** la connexion est créée quand même (cycles autorisés pour dialogues récursifs)

**Technical Requirements:**
- Backend : Service `UnityDialogueGenerationService` avec méthode `autoLinkNode(parentNodeId, newNodeId, choiceText?)`
- Frontend : Hook `useAutoLink` dans `GenerationPanel.tsx` qui crée connexion après génération
- Zustand store : `useGraphStore` avec méthode `createConnection(fromNodeId, toNodeId, label?)`
- Connexions : Format React Flow edge avec `source`, `target`, `label` (texte choix)
- Validation : Integration avec Epic 0 Story 0.6 (détection cycles)
- Tests : Unit (auto-link logique), Integration (connexion créée), E2E (workflow auto-link complet)

**References:** FR9 (auto-link), Story 1.1 (génération single), Story 1.2 (génération batch), Epic 0 Story 0.6 (validation cycles)

---

### Story 1.10: Régénérer des nœuds rejetés avec instructions ajustées (FR10)

As a **utilisateur générant des dialogues**,
I want **régénérer des nœuds rejetés avec des instructions ajustées**,
So that **je peux itérer sur la qualité des dialogues sans perdre le contexte de la génération précédente**.

**Acceptance Criteria:**

**Given** j'ai rejeté un nœud généré (voir Story 1.4)
**When** je sélectionne le nœud rejeté et clique sur "Régénérer"
**Then** un panneau s'ouvre avec les instructions originales pré-remplies
**And** je peux modifier les instructions avant régénération

**Given** je modifie les instructions (ex: "Tone plus sombre, moins de répétition")
**When** je lance la régénération
**Then** un nouveau nœud est généré avec les instructions ajustées
**And** le nœud rejeté est remplacé par le nouveau nœud (même position dans graphe)
**And** les connexions du nœud rejeté sont préservées (même parent/enfant)

**Given** je régénère un nœud plusieurs fois
**When** je régénère 3 fois le même nœud
**Then** l'historique des instructions est sauvegardé (3 versions)
**And** je peux voir les instructions précédentes dans un dropdown "Historique"

**Given** je régénère un nœud batch (partie d'un batch de 5 nœuds)
**When** je régénère un seul nœud du batch
**Then** seul ce nœud est régénéré (pas tout le batch)
**And** les autres nœuds du batch restent inchangés

**Given** je régénère un nœud avec un contexte GDD modifié
**When** le contexte GDD a changé depuis la génération originale
**Then** le nouveau contexte GDD est utilisé pour la régénération
**And** un message informatif s'affiche "Contexte GDD mis à jour depuis la génération originale"

**Technical Requirements:**
- Frontend : Bouton "Régénérer" dans menu contextuel `DialogueNode.tsx` pour nœuds rejetés
- Composant : `RegenerateNodeModal.tsx` avec champ instructions pré-rempli + historique
- Backend : Endpoint `/api/v1/dialogues/{id}/nodes/{nodeId}/regenerate` (POST) avec instructions ajustées
- Historique : Stockage instructions précédentes dans metadata nœud (`regenerationHistory: [...]`)
- Connexions : Préservation connexions lors remplacement nœud (même stableID ou mapping)
- Tests : Unit (régénération logique), Integration (API regenerate), E2E (workflow régénération)

**References:** FR10 (régénération), Story 1.4 (rejeter nœuds), FR3 (instructions), Story 1.1 (génération)

---

### Story 1.11: Estimer le coût LLM avant génération (FR72)

As a **utilisateur générant des dialogues**,
I want **voir une estimation du coût LLM avant de lancer la génération**,
So that **je peux gérer mon budget et décider si je veux procéder avec la génération**.

**Acceptance Criteria:**

**Given** j'ai configuré un contexte GDD et des instructions
**When** je clique sur "Estimer le coût" (bouton avant "Générer")
**Then** une estimation s'affiche avec : coût estimé (€), tokens estimés (prompt + completion), provider sélectionné
**And** l'estimation se calcule en <1 seconde (pas de latence perceptible)

**Given** je modifie le contexte GDD (ajout personnage)
**When** le contexte change
**Then** l'estimation est recalculée automatiquement
**And** le nouveau coût estimé s'affiche (mise à jour en temps réel)

**Given** je change de provider LLM (OpenAI → Mistral)
**When** le provider change
**Then** l'estimation est recalculée avec les prix du nouveau provider
**And** la différence de coût est affichée (ex: "Mistral: -30% vs OpenAI")

**Given** je lance une génération batch (5 nœuds)
**When** j'estime le coût
**Then** l'estimation affiche le coût total (5 × coût single nœud)
**And** un breakdown par nœud est disponible (déplier pour voir détails)

**Given** l'estimation dépasse mon budget (90% ou 100%)
**When** j'estime le coût
**Then** un warning s'affiche "Budget atteint à 90%" ou "Budget dépassé - génération bloquée" (voir Epic 0 Story 0.7)
**And** le bouton "Générer" est désactivé si budget 100% dépassé

**Technical Requirements:**
- Backend : Endpoint `/api/v1/dialogues/estimate-cost` (POST) avec contexte + instructions, retourne estimation
- Service : `CostEstimationService` calcule tokens (prompt builder) + prix provider (config)
- Frontend : Composant `CostEstimationBadge.tsx` affiche estimation + bouton "Estimer" dans `GenerationPanel.tsx`
- Cache : Estimation mise en cache (hash prompt) pour éviter recalculs inutiles
- Integration : Epic 0 Story 0.7 (cost governance) pour vérification budget
- Tests : Unit (calcul estimation), Integration (API estimation), E2E (workflow estimation)

**References:** FR72 (estimation coût), Epic 0 Story 0.7 (cost governance), FR77 (prompt transparency)

---

### Story 1.12: Afficher breakdown des coûts par dialogue (FR73)

As a **utilisateur générant des dialogues**,
I want **voir le breakdown détaillé des coûts par dialogue (coût total, coût par nœud)**,
So that **je peux analyser où mes coûts LLM sont concentrés et optimiser mes générations**.

**Acceptance Criteria:**

**Given** j'ai généré plusieurs nœuds dans un dialogue
**When** j'ouvre le panneau "Coûts" du dialogue
**Then** je vois : coût total dialogue (€), nombre de nœuds générés, coût moyen par nœud
**And** un graphique montre la distribution des coûts (bar chart par nœud)

**Given** je consulte le breakdown de coûts
**When** je clique sur un nœud dans le graphique
**Then** les détails du nœud s'affichent : tokens prompt, tokens completion, coût exact, timestamp génération
**And** je peux voir le prompt utilisé pour ce nœud (voir Story 1.14)

**Given** j'ai plusieurs dialogues dans le système
**When** je compare les coûts entre dialogues
**Then** je peux trier les dialogues par coût total (plus cher → moins cher)
**And** un indicateur visuel montre les dialogues les plus coûteux (rouge = cher, vert = économique)

**Given** je génère un nouveau nœud dans un dialogue existant
**When** le nœud est généré
**Then** le breakdown de coûts est mis à jour automatiquement
**And** le coût total dialogue augmente du coût du nouveau nœud

**Given** je supprime un nœud d'un dialogue
**When** le nœud est supprimé
**Then** le coût du nœud supprimé reste dans l'historique (pas supprimé du breakdown)
**And** un indicateur "Nœud supprimé" s'affiche à côté du coût dans le breakdown

**Technical Requirements:**
- Backend : Endpoint `/api/v1/dialogues/{id}/costs` (GET) retourne breakdown détaillé
- Service : `CostTrackingService` agrège coûts par dialogue depuis `cost_logs` (table Epic 0 Story 0.7)
- Frontend : Composant `DialogueCostBreakdown.tsx` avec graphique (Chart.js ou Recharts) + tableau détaillé
- Graphique : Bar chart coût par nœud, tooltip avec détails au survol
- Integration : Epic 0 Story 0.7 (cost governance) pour données coûts
- Tests : Unit (agrégation coûts), Integration (API costs), E2E (affichage breakdown)

**References:** FR73 (breakdown coûts), Epic 0 Story 0.7 (cost governance), Story 1.14 (logs génération)

---

### Story 1.13: Afficher coûts LLM cumulatifs (daily, monthly) (FR74)

As a **utilisateur générant des dialogues**,
I want **voir mes coûts LLM cumulatifs (quotidien, mensuel)**,
So that **je peux suivre mon budget global et identifier les tendances de consommation**.

**Acceptance Criteria:**

**Given** je consulte le dashboard de coûts
**When** j'ouvre la section "Coûts cumulatifs"
**Then** je vois : coût aujourd'hui (€), coût ce mois (€), coût total (tous temps)
**And** un graphique linéaire montre l'évolution des coûts sur les 30 derniers jours

**Given** je consulte les coûts cumulatifs
**When** je change la période (quotidien → mensuel → annuel)
**Then** le graphique se met à jour avec les données de la période sélectionnée
**And** les totaux sont recalculés (ex: "Janvier 2026: 45€")

**Given** je consulte les coûts par provider (OpenAI vs Mistral)
**When** j'ouvre le breakdown par provider
**Then** je vois : coût OpenAI (€), coût Mistral (€), pourcentage de chaque provider
**And** un graphique en camembert montre la répartition (ex: "OpenAI 70%, Mistral 30%")

**Given** je dépense plus que d'habitude un jour
**When** le coût quotidien dépasse la moyenne (ex: +50%)
**Then** un indicateur visuel s'affiche "Dépense élevée aujourd'hui"
**And** un tooltip explique la raison (ex: "5 générations batch aujourd'hui")

**Given** je configure un budget mensuel (Epic 0 Story 0.7)
**When** je consulte les coûts cumulatifs
**Then** un indicateur de progression s'affiche "Budget: 45€ / 100€ (45%)"
**And** une barre de progression visuelle montre l'avancement (vert <90%, orange 90-100%, rouge >100%)

**Technical Requirements:**
- Backend : Endpoint `/api/v1/costs/cumulative` (GET) avec paramètre `period: daily/monthly/yearly`
- Service : `CostTrackingService` agrège coûts depuis `cost_logs` par période (SQL GROUP BY date)
- Frontend : Composant `CumulativeCostsDashboard.tsx` avec graphique linéaire (Chart.js) + indicateurs
- Graphique : Ligne temporelle coûts quotidiens/mensuels avec tooltip détails
- Integration : Epic 0 Story 0.7 (cost governance) pour budget + données coûts
- Tests : Unit (agrégation périodes), Integration (API cumulative), E2E (affichage dashboard)

**References:** FR74 (coûts cumulatifs), Epic 0 Story 0.7 (cost governance), FR76 (budgets)

---

### Story 1.14: Afficher prompt transparency (prompt exact envoyé au LLM) (FR77)

As a **utilisateur générant des dialogues**,
I want **voir le prompt exact envoyé au LLM pour chaque génération**,
So that **je peux comprendre comment le contexte GDD et les instructions sont utilisés et déboguer les générations**.

**Acceptance Criteria:**

**Given** un nœud a été généré
**When** je sélectionne le nœud et clique sur "Voir le prompt" (menu contextuel ou panneau détails)
**Then** un modal s'ouvre affichant le prompt complet envoyé au LLM
**And** le prompt est formaté avec syntaxe highlight (markdown ou code block)
**And** les sections sont clairement délimitées (System prompt, Context GDD, Instructions, etc.)

**Given** je consulte le prompt d'une génération
**When** le prompt est affiché
**Then** je peux copier le prompt (bouton "Copier") pour l'utiliser ailleurs
**And** je peux voir les tokens utilisés (prompt tokens, completion tokens, total)

**Given** je génère un nouveau nœud
**When** la génération se termine
**Then** le prompt est automatiquement sauvegardé dans les logs (voir Story 1.15)
**And** je peux consulter le prompt immédiatement après génération

**Given** je consulte le prompt d'une génération batch
**When** le prompt est affiché
**Then** je vois le prompt de base (identique pour tous les nœuds du batch)
**And** je peux voir les variations spécifiques par nœud (ex: "Choix 1: Accepter", "Choix 2: Refuser")

**Given** je modifie le contexte GDD après une génération
**When** je consulte le prompt d'une génération ancienne
**Then** le prompt affiché est celui utilisé à l'époque (pas le contexte actuel)
**And** un message informatif s'affiche "Prompt historique - contexte GDD depuis modifié"

**Technical Requirements:**
- Backend : Stockage prompt dans `generation_logs` (table) avec chaque génération (timestamp, prompt, tokens, cost)
- API : Endpoint `/api/v1/dialogues/{id}/nodes/{nodeId}/prompt` (GET) retourne prompt historique
- Frontend : Composant `PromptViewerModal.tsx` avec syntaxe highlight (react-syntax-highlighter) + bouton copier
- Format : Prompt formaté avec sections (System, Context, Instructions) + line numbers
- Integration : Story 1.15 (generation logs) pour stockage prompts
- Tests : Unit (formatage prompt), Integration (API prompt), E2E (affichage prompt)

**References:** FR77 (prompt transparency), Story 1.15 (generation logs), FR78 (logs)

---

### Story 1.15: Afficher logs de génération (prompts, réponses, coûts) (FR78)

As a **utilisateur générant des dialogues**,
I want **consulter les logs de génération (prompts, réponses LLM, coûts) pour chaque nœud**,
So that **je peux analyser l'historique des générations et comprendre les patterns de coûts/qualité**.

**Acceptance Criteria:**

**Given** j'ai généré plusieurs nœuds dans un dialogue
**When** j'ouvre le panneau "Logs de génération"
**Then** je vois une liste chronologique de toutes les générations (plus récent → plus ancien)
**And** chaque entrée affiche : timestamp, nœud généré, coût (€), tokens, provider, statut (succès/échec)

**Given** je consulte les logs de génération
**When** je clique sur une entrée de log
**Then** les détails s'affichent : prompt complet, réponse LLM brute, coût détaillé, durée génération
**And** je peux voir le prompt (voir Story 1.14) et la réponse formatée

**Given** je filtre les logs par période (aujourd'hui, cette semaine, ce mois)
**When** je sélectionne une période
**Then** seuls les logs de cette période sont affichés
**And** un résumé s'affiche "X générations, Y€ total"

**Given** je filtre les logs par provider (OpenAI vs Mistral)
**When** je sélectionne un provider
**Then** seuls les logs de ce provider sont affichés
**And** un résumé s'affiche "X générations OpenAI, Y€ total"

**Given** une génération a échoué (erreur LLM API)
**When** je consulte le log de cette génération
**Then** le statut affiche "Échec" avec message d'erreur détaillé
**And** le coût affiché est 0€ (pas de coût pour génération échouée)
**And** je peux voir la tentative de prompt (si disponible)

**Given** j'exporte les logs de génération
**When** je clique sur "Exporter logs" (CSV ou JSON)
**Then** un fichier est téléchargé avec tous les logs (format structuré)
**And** les logs incluent : timestamp, nœud, prompt, réponse, coût, tokens, provider, statut

**Technical Requirements:**
- Backend : Table `generation_logs` (timestamp, dialogue_id, node_id, prompt, response, tokens, cost, provider, status)
- API : Endpoint `/api/v1/dialogues/{id}/generation-logs` (GET) avec filtres période/provider
- Frontend : Composant `GenerationLogsPanel.tsx` avec liste chronologique + filtres + export
- Format : Logs formatés avec timestamps lisibles, coûts en €, statuts colorés (vert=succès, rouge=échec)
- Export : Fonction export CSV/JSON côté frontend (download blob)
- Tests : Unit (filtrage logs), Integration (API logs), E2E (affichage + export logs)

**References:** FR78 (generation logs), Story 1.14 (prompt transparency), FR72-74 (coûts), Epic 0 Story 0.7 (cost governance)

---

### Story 1.16: Fallback vers provider LLM alternatif en cas d'échec (FR79)

As a **utilisateur générant des dialogues**,
I want **que le système bascule automatiquement vers un provider LLM alternatif si le provider principal échoue**,
So that **mes générations ne sont pas interrompues par des pannes temporaires d'un provider**.

**Acceptance Criteria:**

**Given** j'ai configuré OpenAI comme provider principal et Mistral comme fallback
**When** OpenAI API échoue (erreur 500, timeout, quota dépassé)
**Then** le système bascule automatiquement vers Mistral
**And** la génération continue sans interruption visible pour l'utilisateur
**And** un message informatif s'affiche "OpenAI indisponible - bascule vers Mistral"

**Given** le fallback vers Mistral est activé
**When** la génération réussit avec Mistral
**Then** le nœud est généré normalement (même format Unity JSON)
**And** le log de génération indique "Provider: Mistral (fallback depuis OpenAI)"
**And** le coût Mistral est tracké séparément (voir Story 1.13)

**Given** les deux providers (OpenAI et Mistral) échouent
**When** la génération est tentée
**Then** la génération échoue avec message "Tous les providers LLM sont indisponibles"
**And** aucun coût n'est facturé (pas de tentative facturée)
**And** l'utilisateur peut réessayer manuellement plus tard

**Given** je configure les providers de fallback dans les paramètres
**When** je définis l'ordre de fallback (ex: OpenAI → Mistral → Anthropic)
**Then** l'ordre est sauvegardé dans mes préférences
**And** le système respecte cet ordre lors des fallbacks automatiques

**Given** un fallback est déclenché
**When** je consulte les logs de génération
**Then** le log affiche clairement "Fallback: OpenAI → Mistral" avec raison (ex: "Timeout OpenAI")
**And** les métriques de fallback sont trackées (nombre de fallbacks par provider)

**Technical Requirements:**
- Backend : Service `LLMFallbackService` avec logique retry + fallback (provider1 → provider2 → échec)
- Factory : `LLMClientFactory` avec méthode `createWithFallback(primary, fallback)` retournant client avec retry
- Retry : Backoff exponentiel (3 tentatives) avant fallback vers provider alternatif
- Logs : Événement "llm_fallback" dans `generation_logs` avec provider source → provider destination + raison
- Frontend : Message toast informatif "Fallback vers [provider]" (non-bloquant, 5s timeout)
- Configuration : Paramètres utilisateur pour ordre fallback (localStorage + backend preferences)
- Tests : Unit (logique fallback), Integration (API fallback), E2E (workflow fallback complet)

**References:** FR79 (fallback provider), Epic 0 Story 0.3 (Multi-Provider LLM), NFR-R4 (Error Recovery LLM >95%), NFR-I2 (LLM API Reliability >99%)

---

