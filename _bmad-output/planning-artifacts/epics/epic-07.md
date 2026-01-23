## Epic 7: Collaboration et contrôle d'accès

Les utilisateurs peuvent travailler en équipe avec authentification sécurisée et rôles (Admin, Writer, Viewer). Le système gère accounts, login/logout, RBAC, partage dialogues, audit logs (V1.5+).

**FRs covered:** FR64-71 (auth, RBAC, partage, audit logs)

**NFRs covered:** NFR-S2 (Auth Security JWT), NFR-S3 (Data Protection RBAC), NFR-SC2 (Concurrent Users 3-5 MVP, 10+ V2.0+)

**Valeur utilisateur:** Collaboration équipe narrative (Marc + Mathieu + writer + Unity dev) avec contrôle accès approprié.

**Dépendances:** Epic 0 (infrastructure auth), Epic 8 (partage dialogues)

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

### Story 7.1: Créer comptes utilisateurs avec authentification username/password (FR64)

As a **nouvel utilisateur**,
I want **créer un compte avec username/password**,
So that **je peux accéder au système et travailler sur des dialogues**.

**Acceptance Criteria:**

**Given** je suis sur l'écran de connexion
**When** je clique sur "Créer un compte"
**Then** un formulaire d'inscription s'affiche avec champs : username, email, password, confirm password
**And** des règles de validation sont affichées (password min 8 caractères, etc.)

**Given** je remplis le formulaire d'inscription
**When** je saisis un username, email valide, et password conforme
**Then** le compte est créé avec succès
**And** je suis automatiquement connecté (tokens JWT générés)
**And** un message de bienvenue s'affiche "Compte créé avec succès"

**Given** je saisis un username déjà utilisé
**When** je tente de créer le compte
**Then** une erreur s'affiche "Username déjà utilisé - choisir un autre nom"
**And** le compte n'est pas créé

**Given** je saisis un password faible (<8 caractères)
**When** je tente de créer le compte
**Then** une erreur s'affiche "Password doit contenir au moins 8 caractères"
**And** le compte n'est pas créé

**Given** je saisis un email invalide
**When** je tente de créer le compte
**Then** une erreur s'affiche "Email invalide"
**And** le compte n'est pas créé

**Technical Requirements:**
- Backend : Endpoint `/api/v1/auth/register` (POST) avec validation username/email/password
- Service : `AuthService` avec méthode `create_user(username, email, password)` pour création compte
- Hash : Password hashé avec bcrypt avant stockage (sécurité)
- Base de données : Table `users` (id, username, email, hashed_password, role, created_at)
- Validation : Vérification username unique, email valide, password fort (min 8 caractères)
- Frontend : Composant `RegisterForm.tsx` avec formulaire inscription + validation
- Auto-login : Après création compte, générer tokens JWT et connecter automatiquement
- Tests : Unit (création compte), Integration (API register), E2E (workflow inscription)

**References:** FR64 (créer comptes), Story 7.2 (login/logout), NFR-S2 (Auth Security JWT)

---

### Story 7.2: Se connecter et se déconnecter du système (FR65)

As a **utilisateur avec compte**,
I want **me connecter et me déconnecter du système**,
So that **je peux accéder à mes dialogues et travailler en équipe**.

**Acceptance Criteria:**

**Given** j'ai un compte utilisateur
**When** je saisis mon username et password sur l'écran de connexion
**Then** je suis authentifié avec succès
**And** des tokens JWT sont générés (access token 15min, refresh token 7 jours)
**And** je suis redirigé vers le dashboard

**Given** je me connecte avec succès
**When** les tokens sont générés
**Then** l'access token est stocké dans localStorage (frontend)
**And** le refresh token est stocké dans un cookie httpOnly (sécurité)
**And** les tokens sont utilisés pour authentifier les requêtes API

**Given** mon access token expire (15 minutes)
**When** je fais une requête API
**Then** le système détecte l'expiration et utilise le refresh token pour générer un nouveau access token
**And** la requête continue sans interruption (refresh automatique)

**Given** je me déconnecte
**When** je clique sur "Déconnexion"
**Then** les tokens sont supprimés (localStorage + cookie)
**And** je suis redirigé vers l'écran de connexion
**And** toutes les requêtes API suivantes échouent (non authentifiées)

**Given** je saisis des identifiants incorrects
**When** je tente de me connecter
**Then** une erreur s'affiche "Nom d'utilisateur ou mot de passe incorrect"
**And** le compte n'est pas verrouillé après plusieurs tentatives (pas de lockout V1.0)

**Technical Requirements:**
- Backend : Endpoints `/api/v1/auth/login` (POST), `/api/v1/auth/logout` (POST), `/api/v1/auth/refresh` (POST) (existants)
- Service : `AuthService.authenticate_user()`, `create_access_token()`, `create_refresh_token()` (existants)
- JWT : Access token 15min, refresh token 7 jours (configuré dans `AuthService`)
- Frontend : Composant `LoginForm.tsx` avec formulaire connexion + gestion tokens
- Store : `useAuthStore` pour stockage tokens + état authentification (existant)
- Refresh : Intercepteur API pour refresh automatique token expiré (axios interceptor)
- Tests : Unit (authentification), Integration (API login/logout), E2E (workflow connexion)

**References:** FR65 (login/logout), Story 7.1 (créer comptes), NFR-S2 (Auth Security JWT), Epic 0 (infrastructure)

---

### Story 7.3: Administrateurs assignent rôles aux utilisateurs (Admin, Writer, Viewer) (FR66)

As a **administrateur**,
I want **assigner des rôles aux utilisateurs (Admin, Writer, Viewer)**,
So that **je peux contrôler les permissions d'accès et les actions autorisées**.

**Acceptance Criteria:**

**Given** je suis connecté en tant qu'administrateur
**When** j'ouvre "Gestion utilisateurs"
**Then** une liste de tous les utilisateurs s'affiche avec leurs rôles actuels
**And** je peux modifier le rôle de chaque utilisateur

**Given** je modifie le rôle d'un utilisateur
**When** je sélectionne un utilisateur et change son rôle (ex: Viewer → Writer)
**Then** le rôle est mis à jour immédiatement
**And** l'utilisateur voit ses nouvelles permissions lors de sa prochaine action
**And** un message de confirmation s'affiche "Rôle mis à jour : [username] est maintenant [rôle]"

**Given** j'essaie d'assigner le rôle Admin à un utilisateur
**When** je change le rôle vers Admin
**Then** une confirmation supplémentaire s'affiche "Confirmer promotion Admin ? (permissions élevées)"
**And** je dois confirmer explicitement avant que le changement soit appliqué

**Given** un utilisateur non-admin essaie d'assigner des rôles
**When** l'utilisateur tente d'accéder à "Gestion utilisateurs"
**Then** l'accès est refusé avec message "Accès réservé aux administrateurs"
**And** la page n'est pas accessible

**Given** je consulte l'historique des changements de rôles
**When** j'ouvre "Historique rôles"
**Then** une timeline s'affiche montrant tous les changements de rôles (qui, quand, quel changement)
**And** les changements sont tracés pour audit (voir Story 7.8)

**Technical Requirements:**
- Backend : Endpoint `/api/v1/users/{id}/role` (PUT) pour modifier rôle utilisateur
- Service : `UserManagementService` avec méthode `assign_role(user_id, role)` avec vérification admin
- RBAC : Vérification rôle admin avant modification (middleware ou dependency)
- Base de données : Table `users` avec champ `role` (enum: "admin", "writer", "viewer")
- Frontend : Composant `UserManagementPanel.tsx` avec liste utilisateurs + sélecteur rôle
- Permissions : Vérification côté frontend + backend (double vérification sécurité)
- Audit : Log changement rôle dans audit logs (voir Story 7.8)
- Tests : Unit (assignation rôle), Integration (API role), E2E (workflow gestion utilisateurs)

**References:** FR66 (assigner rôles), Story 7.4 (permissions Writer), Story 7.5 (permissions Viewer), Story 7.8 (audit logs)

---

### Story 7.4: Writers peuvent créer, éditer, et supprimer dialogues (FR67)

As a **utilisateur avec rôle Writer**,
I want **créer, éditer, et supprimer des dialogues**,
So that **je peux produire du contenu narratif pour le jeu**.

**Acceptance Criteria:**

**Given** je suis connecté avec rôle Writer
**When** j'accède à l'éditeur de dialogues
**Then** je peux créer de nouveaux dialogues (bouton "Nouveau dialogue")
**And** je peux éditer les dialogues existants (bouton "Éditer")
**And** je peux supprimer les dialogues (bouton "Supprimer")

**Given** je crée un nouveau dialogue
**When** le dialogue est créé
**Then** je suis automatiquement défini comme propriétaire du dialogue
**And** le dialogue apparaît dans ma liste de dialogues
**And** je peux partager le dialogue avec d'autres utilisateurs (voir Story 7.6)

**Given** j'édite un dialogue existant
**When** je modifie le dialogue
**Then** les modifications sont sauvegardées avec mon nom comme auteur de la modification
**And** l'historique des modifications est tracé (voir Story 7.8)

**Given** je supprime un dialogue
**When** je confirme la suppression
**Then** le dialogue est supprimé définitivement
**And** un message de confirmation s'affiche "Dialogue supprimé"
**And** l'action de suppression est tracée dans les audit logs

**Given** un utilisateur Viewer essaie d'éditer un dialogue
**When** l'utilisateur tente d'accéder à l'édition
**Then** l'accès est refusé avec message "Permission refusée - rôle Viewer ne peut pas éditer"
**And** les boutons d'édition/suppression sont désactivés ou cachés

**Technical Requirements:**
- Backend : Middleware RBAC vérifiant rôle "writer" pour endpoints création/édition/suppression dialogues
- Permissions : Vérification `user.role in ["admin", "writer"]` avant actions CRUD dialogues
- Propriétaire : Champ `owner_id` dans table `dialogues` pour traçabilité
- API : Endpoints `/api/v1/dialogues` (POST créer, PUT éditer, DELETE supprimer) avec vérification rôle
- Frontend : Composants conditionnels (afficher boutons édition/suppression uniquement si rôle Writer/Admin)
- Store : `useAuthStore` avec méthode `hasPermission(action)` pour vérification permissions frontend
- Tests : Unit (permissions Writer), Integration (API RBAC), E2E (workflow Writer complet)

**References:** FR67 (permissions Writer), Story 7.5 (permissions Viewer), Story 7.3 (assigner rôles), Story 7.8 (audit logs)

---

### Story 7.5: Viewers peuvent lire dialogues mais ne peuvent pas éditer (FR68)

As a **utilisateur avec rôle Viewer**,
I want **lire les dialogues mais ne pas pouvoir les éditer**,
So that **je peux consulter le contenu narratif sans risque de modification accidentelle**.

**Acceptance Criteria:**

**Given** je suis connecté avec rôle Viewer
**When** j'accède à l'éditeur de dialogues
**Then** je peux voir tous les dialogues partagés avec moi (voir Story 7.6)
**And** je peux ouvrir et lire le contenu des dialogues
**And** les boutons d'édition/suppression sont désactivés ou cachés

**Given** j'ouvre un dialogue en mode Viewer
**When** le dialogue s'affiche
**Then** le contenu est en lecture seule (pas de modification possible)
**And** un indicateur visuel s'affiche "Mode lecture seule - Rôle Viewer"
**And** je peux exporter le dialogue (voir Epic 5)

**Given** j'essaie d'éditer un dialogue en tant que Viewer
**When** je tente de modifier un nœud ou créer une connexion
**Then** l'action est bloquée avec message "Permission refusée - rôle Viewer ne peut pas éditer"
**And** aucun changement n'est sauvegardé

**Given** un dialogue est partagé avec moi en tant que Viewer
**When** je consulte le dialogue
**Then** je peux voir qui a créé le dialogue et qui l'a modifié en dernier
**And** je peux voir l'historique des modifications (lecture seule)

**Given** je consulte les permissions d'un dialogue
**When** j'ouvre "Permissions dialogue"
**Then** je vois mon rôle (Viewer) et les autres utilisateurs avec accès
**And** je ne peux pas modifier les permissions (réservé au propriétaire ou Admin)

**Technical Requirements:**
- Backend : Middleware RBAC vérifiant rôle "viewer" pour endpoints lecture uniquement
- Permissions : Vérification `user.role in ["admin", "writer", "viewer"]` pour lecture, `["admin", "writer"]` pour écriture
- Frontend : Mode lecture seule dans `GraphEditor.tsx` avec désactivation édition si rôle Viewer
- UI : Indicateur visuel "Mode lecture seule" + désactivation boutons édition/suppression
- Store : `useAuthStore.hasPermission("edit")` retourne false pour Viewer
- Tests : Unit (permissions Viewer), Integration (API RBAC), E2E (workflow Viewer lecture seule)

**References:** FR68 (permissions Viewer), Story 7.4 (permissions Writer), Story 7.3 (assigner rôles), Story 7.6 (partage dialogues)

---

### Story 7.6: Utilisateurs peuvent partager dialogues avec membres équipe spécifiques (FR69)

As a **utilisateur créant des dialogues**,
I want **partager mes dialogues avec des membres spécifiques de l'équipe**,
So that **nous pouvons collaborer sur le contenu narratif avec contrôle d'accès précis**.

**Acceptance Criteria:**

**Given** j'ai créé un dialogue (voir Story 7.4)
**When** je sélectionne le dialogue et clique sur "Partager"
**Then** un modal s'affiche avec liste des membres de l'équipe
**And** je peux sélectionner les membres avec qui partager et leur rôle (Writer ou Viewer)

**Given** je partage un dialogue avec un membre en tant que Writer
**When** le partage est confirmé
**Then** le membre peut éditer le dialogue (voir Story 7.4)
**And** le dialogue apparaît dans la liste de dialogues du membre
**And** le membre est notifié du partage (optionnel, V1.5+)

**Given** je partage un dialogue avec un membre en tant que Viewer
**When** le partage est confirmé
**Then** le membre peut lire le dialogue mais pas l'éditer (voir Story 7.5)
**And** le dialogue apparaît dans la liste de dialogues du membre

**Given** je retire le partage d'un dialogue
**When** je clique sur "Arrêter le partage" pour un membre
**Then** le membre perd l'accès au dialogue
**And** le dialogue disparaît de la liste du membre
**And** un message de confirmation s'affiche "Partage retiré"

**Given** je consulte les permissions d'un dialogue
**When** j'ouvre "Permissions dialogue"
**Then** je vois : propriétaire, membres avec accès, rôles (Writer/Viewer)
**And** je peux modifier les permissions (ajouter/retirer membres, changer rôles)

**Technical Requirements:**
- Backend : Endpoints `/api/v1/dialogues/{id}/share` (POST partager, DELETE retirer partage) avec liste membres + rôles
- Service : `DialogueSharingService` avec méthodes `share_dialogue(dialogue_id, user_id, role)`, `revoke_share(dialogue_id, user_id)`
- Base de données : Table `dialogue_shares` (dialogue_id, user_id, role, shared_by, timestamp)
- Frontend : Composant `DialogueSharingModal.tsx` avec sélection membres équipe + rôles + gestion partage
- Permissions : Vérification propriétaire ou Admin pour modifier partage
- Notifications : Intégration avec système notifications (optionnel, V1.5+) pour notifier partage
- Tests : Unit (partage logique), Integration (API sharing), E2E (workflow partage)

**References:** FR69 (partage dialogues), Story 7.4 (permissions Writer), Story 7.5 (permissions Viewer), Story 7.7 (voir accès)

---

### Story 7.7: Utilisateurs peuvent voir qui a accès à chaque dialogue (FR70)

As a **utilisateur gérant des dialogues**,
I want **voir qui a accès à chaque dialogue**,
So that **je peux gérer les permissions et identifier les collaborateurs**.

**Acceptance Criteria:**

**Given** j'ai créé ou partagé des dialogues
**When** j'ouvre "Permissions dialogue" pour un dialogue
**Then** une liste s'affiche avec : propriétaire, membres avec accès, rôles (Writer/Viewer)
**And** chaque membre affiche : nom, email, rôle, date partage

**Given** je consulte les permissions d'un dialogue
**When** le panneau s'affiche
**Then** je peux voir qui a créé le dialogue (propriétaire)
**And** je peux voir qui a modifié le dialogue en dernier (dernière modification)
**And** je peux voir l'historique des partages (qui a partagé, quand)

**Given** un dialogue est partagé avec plusieurs membres
**When** je consulte les permissions
**Then** tous les membres sont listés avec leurs rôles
**And** je peux filtrer par rôle (afficher uniquement Writers ou Viewers)
**And** je peux rechercher un membre spécifique

**Given** je consulte les permissions d'un dialogue partagé avec moi
**When** le panneau s'affiche
**Then** je vois mon rôle (Writer ou Viewer) et les autres membres avec accès
**And** je ne peux pas modifier les permissions (réservé au propriétaire ou Admin)

**Given** je consulte les permissions depuis la liste de dialogues
**When** je survole un dialogue
**Then** un tooltip s'affiche "Partagé avec X membres" ou "Privé"
**And** je peux cliquer pour voir les détails complets

**Technical Requirements:**
- Backend : Endpoint `/api/v1/dialogues/{id}/permissions` (GET) retourne liste membres avec accès + rôles
- Service : `DialogueSharingService` avec méthode `get_dialogue_permissions(dialogue_id)` retournant permissions
- Base de données : Requête join `dialogue_shares` + `users` pour obtenir détails membres
- Frontend : Composant `DialoguePermissionsPanel.tsx` avec liste membres + rôles + historique
- Tooltip : Composant `DialogueTooltip.tsx` avec aperçu permissions au survol
- Permissions : Vérification propriétaire ou Admin pour modifier permissions (lecture pour tous)
- Tests : Unit (récupération permissions), Integration (API permissions), E2E (workflow permissions)

**References:** FR70 (voir accès dialogues), Story 7.6 (partage dialogues), Story 7.3 (assigner rôles)

---

### Story 7.8: Système track actions utilisateurs pour audit logs (V1.5+) (FR71)

As a **administrateur**,
I want **voir les audit logs des actions utilisateurs (V1.5+)**,
So that **je peux tracer l'activité et identifier les problèmes de sécurité ou d'utilisation**.

**Acceptance Criteria:**

**Given** le système d'audit logs est disponible (V1.5+)
**When** un utilisateur effectue une action (créer dialogue, modifier, supprimer, partager)
**Then** l'action est enregistrée dans les audit logs avec : timestamp, utilisateur, action, ressource, détails
**And** les logs sont stockés de manière sécurisée (non modifiables)

**Given** je consulte les audit logs en tant qu'administrateur
**When** j'ouvre "Audit logs"
**Then** une liste chronologique de toutes les actions s'affiche (plus récent → plus ancien)
**And** chaque entrée affiche : date, utilisateur, action, ressource (dialogue ID), détails

**Given** je filtre les audit logs par utilisateur
**When** je sélectionne un utilisateur
**Then** seuls les logs de cet utilisateur sont affichés
**And** un résumé s'affiche "X actions par [username]"

**Given** je filtre les audit logs par action (créer, modifier, supprimer, partager)
**When** je sélectionne une action
**Then** seuls les logs de cette action sont affichés
**And** je peux identifier les patterns d'utilisation (ex: beaucoup de suppressions)

**Given** je filtre les audit logs par période (aujourd'hui, cette semaine, ce mois)
**When** je sélectionne une période
**Then** seuls les logs de cette période sont affichés
**And** un résumé s'affiche "X actions dans cette période"

**Given** je consulte les détails d'un log d'audit
**When** je clique sur une entrée de log
**Then** les détails complets s'affichent : timestamp précis, utilisateur, action, ressource, IP (si disponible), user agent
**And** je peux voir le contexte de l'action (ex: dialogue modifié, modifications apportées)

**Given** j'exporte les audit logs
**When** je clique sur "Exporter logs" (CSV ou JSON)
**Then** un fichier est téléchargé avec tous les logs (format structuré)
**And** les logs incluent : timestamp, utilisateur, action, ressource, détails, IP

**Technical Requirements:**
- Backend : Service `AuditLogService` avec méthode `log_action(user_id, action, resource, details)` pour enregistrement logs
- Stockage : Table `audit_logs` (id, user_id, action, resource_type, resource_id, details, ip_address, user_agent, timestamp)
- Middleware : Intercepteur API pour logging automatique actions (créer, modifier, supprimer, partager)
- API : Endpoint `/api/v1/audit-logs` (GET) avec filtres utilisateur/action/période retourne logs
- Frontend : Composant `AuditLogsPanel.tsx` avec liste chronologique + filtres + export (réservé Admin)
- Sécurité : Logs non modifiables (append-only), accès réservé Admin uniquement
- Tests : Unit (logging logique), Integration (API audit logs), E2E (workflow audit logs)

**References:** FR71 (audit logs V1.5+), Story 7.3 (assigner rôles), Story 7.4 (permissions Writer), Story 7.6 (partage dialogues)

---

