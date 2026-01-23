## Epic 8: Gestion des dialogues et recherche

Les utilisateurs peuvent gérer, rechercher, filtrer et organiser leurs dialogues efficacement. Le système permet listing, recherche avancée (nom, personnage, lieu, thème), filtrage par métadonnées, tri, collections/dossiers, indexation rapide (1000+ dialogues), visualisation métadonnées, validation batch et génération batch.

**FRs covered:** FR80-88 (listing, recherche, filtrage, tri, collections, indexation, métadonnées, validation batch, génération batch)

**NFRs covered:** NFR-SC1 (Dialogue Storage Scalability 1000+), NFR-P3 (API Response <200ms), NFR-P5 (Initial Page Load <3s)

**Valeur utilisateur:** Navigation et gestion efficace de centaines de dialogues pour production narrative à grande échelle.

**Dépendances:** Epic 1 (génération dialogues), Epic 4 (validation), Epic 7 (RBAC pour filtrage par auteur)

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

### Story 8.1: Lister tous les dialogues du système (FR80)

As a **utilisateur gérant des dialogues**,
I want **voir la liste de tous mes dialogues dans le système**,
So that **je peux naviguer rapidement entre mes dialogues et accéder à celui que je cherche**.

**Acceptance Criteria:**

**Given** j'ai créé plusieurs dialogues dans le système
**When** j'accède à la page "Dialogues"
**Then** une liste de tous mes dialogues s'affiche avec : nom, date création, date modification, nombre de nœuds
**And** la liste se charge en <200ms (NFR-P3)
**And** je peux cliquer sur un dialogue pour l'ouvrir dans l'éditeur

**Given** j'ai créé plus de 100 dialogues
**When** la liste s'affiche
**Then** la pagination est activée (50 dialogues par page par défaut)
**And** je peux naviguer entre les pages
**And** un indicateur affiche "Page X sur Y - Total: Z dialogues"

**Given** je consulte la liste de dialogues
**When** la liste est chargée
**Then** les dialogues sont triés par date de modification (plus récent en premier) par défaut
**And** je peux changer le tri (voir Story 8.4)

**Given** je suis connecté avec rôle Viewer (voir Epic 7)
**When** j'accède à la liste de dialogues
**Then** seuls les dialogues partagés avec moi sont affichés
**And** les dialogues privés des autres utilisateurs ne sont pas visibles

**Given** un dialogue est supprimé
**When** je rafraîchis la liste
**Then** le dialogue disparaît de la liste
**And** un message de confirmation s'affiche "Dialogue supprimé"

**Technical Requirements:**
- Backend : Endpoint `/api/v1/dialogues` (GET) retourne liste dialogues avec pagination (existant partiellement)
- Service : `DialogueManagementService` avec méthode `list_dialogues(user_id, page, limit)` pour récupération liste
- Base de données : Table `dialogues` (id, name, owner_id, created_at, modified_at, node_count, metadata)
- Frontend : Composant `DialogueList.tsx` avec liste paginée + métadonnées (existant partiellement `UnityDialogueList.tsx`)
- RBAC : Filtrage par `owner_id` ou `dialogue_shares` selon rôle utilisateur (voir Epic 7)
- Performance : Pagination côté backend, cache résultats (optionnel) pour <200ms
- Tests : Unit (listing logique), Integration (API list), E2E (workflow navigation)

**References:** FR80 (listing dialogues), Story 8.4 (tri), Story 7.4 (permissions Writer), NFR-P3 (API Response <200ms), NFR-SC1 (1000+ dialogues)

---

### Story 8.2: Rechercher des dialogues (nom, personnage, lieu, thème) (FR81)

As a **utilisateur gérant des dialogues**,
I want **rechercher des dialogues par nom, personnage, lieu, ou thème**,
So that **je peux trouver rapidement un dialogue spécifique parmi des centaines**.

**Acceptance Criteria:**

**Given** j'ai créé plusieurs dialogues avec différents personnages, lieux, et thèmes
**When** je saisis "Akthar" dans la barre de recherche
**Then** tous les dialogues contenant "Akthar" (nom ou personnage) sont affichés
**And** la recherche est insensible à la casse
**And** la recherche se déclenche en temps réel (pas besoin de cliquer "Rechercher")

**Given** je recherche par lieu (ex: "Port de Valdris")
**When** je saisis le nom du lieu
**Then** tous les dialogues référençant ce lieu sont affichés
**And** la recherche s'effectue dans les métadonnées du dialogue (personnages, lieux, thèmes)

**Given** je recherche par thème (ex: "trahison")
**When** je saisis le thème
**Then** tous les dialogues avec ce thème sont affichés
**And** la recherche s'effectue dans les tags/métadonnées du dialogue

**Given** je combine plusieurs critères de recherche (nom + personnage)
**When** je saisis "Akthar Port de Valdris"
**Then** seuls les dialogues contenant à la fois "Akthar" ET "Port de Valdris" sont affichés
**And** la recherche supporte les opérateurs booléens (AND par défaut)

**Given** aucun dialogue ne correspond à ma recherche
**When** je lance la recherche
**Then** un message s'affiche "Aucun dialogue trouvé pour '[terme]'"
**And** un bouton "Réinitialiser recherche" permet de revenir à la liste complète

**Given** la recherche retourne beaucoup de résultats
**When** les résultats sont affichés
**Then** la pagination s'applique aux résultats de recherche
**And** un indicateur affiche "X résultats trouvés"

**Technical Requirements:**
- Backend : Endpoint `/api/v1/dialogues/search` (GET) avec query params `q`, `character`, `location`, `theme`
- Service : `DialogueSearchService` avec méthode `search_dialogues(query, filters)` pour recherche textuelle
- Indexation : Utiliser index de recherche (voir Story 8.6) pour performance sur 1000+ dialogues
- Frontend : Composant `DialogueSearchBar.tsx` avec input recherche + filtres avancés (personnage, lieu, thème)
- Raccourci clavier : Touche "/" pour focus sur barre de recherche (existant partiellement)
- Performance : Recherche <200ms même avec 1000+ dialogues (index requis)
- Tests : Unit (recherche logique), Integration (API search), E2E (workflow recherche)

**References:** FR81 (recherche dialogues), Story 8.6 (indexation), Story 8.1 (listing), NFR-P3 (API Response <200ms)

---

### Story 8.3: Filtrer les dialogues par métadonnées (date, auteur, statut) (FR82)

As a **utilisateur gérant des dialogues**,
I want **filtrer les dialogues par métadonnées (date création, auteur, statut)**,
So that **je peux organiser et trouver des dialogues selon des critères spécifiques**.

**Acceptance Criteria:**

**Given** j'ai créé des dialogues à différentes dates
**When** je sélectionne un filtre "Créés cette semaine"
**Then** seuls les dialogues créés dans les 7 derniers jours sont affichés
**And** les filtres disponibles sont : Aujourd'hui, Cette semaine, Ce mois, Cette année, Tous

**Given** je filtre par auteur
**When** je sélectionne un utilisateur dans le filtre "Auteur"
**Then** seuls les dialogues créés par cet utilisateur sont affichés
**And** le filtre affiche tous les utilisateurs ayant créé des dialogues (liste déroulante)

**Given** je filtre par statut (ex: "Validé", "En cours", "Brouillon")
**When** je sélectionne un statut
**Then** seuls les dialogues avec ce statut sont affichés
**And** le statut est visible dans la liste (badge coloré)

**Given** je combine plusieurs filtres (date + auteur + statut)
**When** je sélectionne "Cette semaine" + "Marc" + "Validé"
**Then** seuls les dialogues correspondant à TOUS les filtres sont affichés
**And** un indicateur affiche "X dialogues trouvés avec filtres appliqués"
**And** je peux réinitialiser tous les filtres d'un clic

**Given** je suis administrateur (voir Epic 7)
**When** je consulte les filtres
**Then** je peux filtrer par n'importe quel utilisateur (pas seulement mes dialogues)
**And** je peux voir tous les dialogues du système

**Given** je filtre les dialogues
**When** les résultats sont affichés
**Then** les filtres actifs sont visibles (badges avec "X" pour supprimer)
**And** je peux supprimer un filtre individuellement en cliquant sur son badge

**Technical Requirements:**
- Backend : Endpoint `/api/v1/dialogues` (GET) avec query params `created_after`, `created_before`, `author_id`, `status`
- Service : `DialogueManagementService` avec méthode `filter_dialogues(filters)` pour application filtres
- Base de données : Requêtes SQL avec WHERE clauses pour filtres (index sur `created_at`, `owner_id`, `status`)
- Frontend : Composant `DialogueFilters.tsx` avec dropdowns date/auteur/statut + badges filtres actifs
- RBAC : Filtrage par auteur limité selon rôle (Viewer voit seulement ses dialogues partagés)
- Performance : Filtres appliqués côté backend (pas de filtrage frontend) pour <200ms
- Tests : Unit (filtrage logique), Integration (API filters), E2E (workflow filtres)

**References:** FR82 (filtrage métadonnées), Story 8.1 (listing), Story 7.3 (rôles RBAC), NFR-P3 (API Response <200ms)

---

### Story 8.4: Trier les dialogues (alpha, date, taille) (FR83)

As a **utilisateur gérant des dialogues**,
I want **trier les dialogues par nom (alphabétique), date, ou taille**,
So that **je peux organiser la liste selon mes besoins (trouver rapidement ou voir les plus récents)**.

**Acceptance Criteria:**

**Given** j'ai une liste de dialogues
**When** je sélectionne "Trier par nom (A-Z)"
**Then** les dialogues sont triés alphabétiquement par nom (ordre croissant)
**And** l'icône de tri indique la direction (flèche ↑)

**Given** je sélectionne "Trier par nom (Z-A)"
**When** le tri est appliqué
**Then** les dialogues sont triés alphabétiquement par nom (ordre décroissant)
**And** l'icône de tri indique la direction (flèche ↓)

**Given** je sélectionne "Trier par date (plus récent)"
**When** le tri est appliqué
**Then** les dialogues sont triés par date de modification (plus récent en premier)
**And** c'est le tri par défaut (voir Story 8.1)

**Given** je sélectionne "Trier par date (plus ancien)"
**When** le tri est appliqué
**Then** les dialogues sont triés par date de modification (plus ancien en premier)

**Given** je sélectionne "Trier par taille (plus grand)"
**When** le tri est appliqué
**Then** les dialogues sont triés par nombre de nœuds (plus grand en premier)
**And** la taille est affichée dans la liste (ex: "45 nœuds")

**Given** je combine tri + recherche/filtres
**When** je recherche "Akthar" et trie par date
**Then** les résultats de recherche sont triés par date
**And** le tri s'applique uniquement aux résultats filtrés

**Given** je change de tri
**When** un nouveau tri est sélectionné
**Then** la liste se met à jour immédiatement (pas de rechargement)
**And** ma sélection de tri est sauvegardée dans localStorage (préférence utilisateur)

**Technical Requirements:**
- Backend : Endpoint `/api/v1/dialogues` (GET) avec query param `sort_by` (name, date, size) et `sort_order` (asc, desc)
- Service : `DialogueManagementService` avec méthode `sort_dialogues(dialogues, sort_by, sort_order)` pour tri
- Base de données : ORDER BY SQL selon critère sélectionné (index sur `name`, `modified_at`, `node_count`)
- Frontend : Composant `DialogueSortSelector.tsx` avec dropdown tri + icônes direction
- Persistence : Sauvegarder préférence tri dans localStorage (`dialogue_sort_preference`)
- Performance : Tri côté backend pour grandes listes (1000+), tri frontend pour petites listes (<50)
- Tests : Unit (tri logique), Integration (API sort), E2E (workflow tri)

**References:** FR83 (tri dialogues), Story 8.1 (listing), Story 8.2 (recherche), NFR-P3 (API Response <200ms)

---

### Story 8.5: Créer des collections/dossiers de dialogues (FR84)

As a **utilisateur gérant des dialogues**,
I want **créer des collections ou dossiers pour organiser mes dialogues**,
So that **je peux regrouper des dialogues par projet, chapitre, ou thème pour une meilleure organisation**.

**Acceptance Criteria:**

**Given** j'ai plusieurs dialogues dans le système
**When** je clique sur "Nouvelle collection"
**Then** un modal s'ouvre me demandant un nom pour la collection
**And** je peux optionnellement ajouter une description et une icône emoji

**Given** je crée une collection "Chapitre 1 - Introduction"
**When** la collection est créée
**Then** la collection apparaît dans la sidebar avec une icône dossier
**And** je peux ouvrir la collection pour voir les dialogues qu'elle contient (vide initialement)

**Given** j'ai créé une collection
**When** je sélectionne des dialogues dans la liste et clique sur "Ajouter à collection"
**Then** un menu déroulant liste toutes mes collections
**And** je peux sélectionner une collection pour y ajouter les dialogues sélectionnés

**Given** un dialogue est ajouté à une collection
**When** je consulte la collection
**Then** le dialogue apparaît dans la liste de la collection
**And** le dialogue peut appartenir à plusieurs collections (pas de restriction unique)

**Given** je consulte un dialogue
**When** le dialogue est affiché
**Then** les collections auxquelles il appartient sont affichées (badges "Chapitre 1", "Thème: Trahison")
**And** je peux cliquer sur un badge pour naviguer vers la collection

**Given** je supprime une collection
**When** je confirme la suppression
**Then** la collection est supprimée
**And** les dialogues ne sont PAS supprimés (seulement retirés de la collection)
**And** un message de confirmation s'affiche "Collection supprimée - X dialogues retirés"

**Given** je modifie une collection (renommer, changer description)
**When** je sauvegarde les modifications
**Then** la collection est mise à jour
**And** les dialogues de la collection ne sont pas affectés

**Technical Requirements:**
- Backend : Endpoints `/api/v1/collections` (GET liste, POST créer, PUT modifier, DELETE supprimer)
- Service : `CollectionService` avec méthodes CRUD collections + `add_dialogues_to_collection()`, `remove_dialogues_from_collection()`
- Base de données : Tables `collections` (id, name, description, icon, owner_id, created_at) et `collection_dialogues` (collection_id, dialogue_id)
- Frontend : Composant `CollectionManager.tsx` avec sidebar collections + modal création/édition
- Drag-and-drop : Optionnel, permettre glisser-déposer dialogues dans collections (V1.5+)
- RBAC : Collections privées par défaut, partage possible (voir Epic 7)
- Tests : Unit (gestion collections), Integration (API collections), E2E (workflow collections)

**References:** FR84 (collections dialogues), Story 8.1 (listing), Story 7.6 (partage), NFR-SC1 (1000+ dialogues)

---

### Story 8.6: Indexer les dialogues pour recherche rapide (1000+) (FR85)

As a **utilisateur recherchant des dialogues**,
I want **que la recherche soit rapide même avec 1000+ dialogues**,
So that **je peux trouver des dialogues instantanément sans attendre plusieurs secondes**.

**Acceptance Criteria:**

**Given** le système contient 1000+ dialogues
**When** je lance une recherche
**Then** la recherche se termine en <200ms (NFR-P3)
**And** les résultats sont affichés instantanément

**Given** les dialogues sont indexés
**When** un nouveau dialogue est créé
**Then** le dialogue est automatiquement ajouté à l'index de recherche
**And** il devient immédiatement recherchable

**Given** un dialogue est modifié (nom, métadonnées)
**When** le dialogue est sauvegardé
**Then** l'index est automatiquement mis à jour
**And** la recherche reflète les modifications immédiatement

**Given** un dialogue est supprimé
**When** le dialogue est supprimé
**Then** le dialogue est retiré de l'index
**And** il n'apparaît plus dans les résultats de recherche

**Given** l'index est corrompu ou obsolète
**When** je détecte un problème de recherche
**Then** je peux forcer une réindexation complète (bouton "Réindexer" admin)
**And** la réindexation se fait en arrière-plan sans bloquer l'application

**Given** je consulte les statistiques de l'index
**When** j'ouvre "Statistiques recherche" (admin)
**Then** je vois : nombre dialogues indexés, dernière mise à jour, taille index
**And** je peux voir les performances de recherche (temps moyen, requêtes récentes)

**Technical Requirements:**
- Backend : Service `DialogueIndexService` avec indexation automatique (création, modification, suppression)
- Index : Utiliser moteur de recherche (ex: Whoosh, Elasticsearch, ou SQL full-text search selon scale)
- Indexation : Indexer champs : nom, personnages, lieux, thèmes, métadonnées (tags, description)
- Performance : Index en mémoire ou disque rapide (SSD), requêtes optimisées pour <200ms
- Auto-update : Écouter événements création/modification/suppression dialogues pour mise à jour index
- Réindexation : Endpoint `/api/v1/admin/reindex` (POST) pour réindexation complète (admin uniquement)
- Tests : Unit (indexation logique), Integration (API search performance), E2E (recherche 1000+ dialogues)

**References:** FR85 (indexation 1000+), Story 8.2 (recherche), NFR-P3 (API Response <200ms), NFR-SC1 (Dialogue Storage Scalability 1000+)

---

### Story 8.7: Afficher les métadonnées d'un dialogue (nodes, coût, last edited) (FR86)

As a **utilisateur gérant des dialogues**,
I want **voir les métadonnées d'un dialogue (nombre nœuds, coût LLM, dernière modification)**,
So that **je peux évaluer rapidement la taille, le coût, et l'état d'un dialogue sans l'ouvrir**.

**Acceptance Criteria:**

**Given** j'ai créé un dialogue avec plusieurs nœuds
**When** je consulte la liste de dialogues
**Then** chaque dialogue affiche : nombre de nœuds, coût total LLM, date dernière modification
**And** les métadonnées sont visibles dans une vue compacte (tooltip ou colonnes)

**Given** je consulte les détails d'un dialogue
**When** j'ouvre "Métadonnées dialogue"
**Then** un panneau s'affiche avec : nom, auteur, date création, date modification, nombre nœuds, coût total, coût par nœud, statut (Validé/En cours/Brouillon)

**Given** un dialogue a été généré avec LLM
**When** je consulte les métadonnées
**Then** le coût total LLM est affiché (ex: "12.45€")
**And** le coût par nœud est calculé et affiché (ex: "0.15€/nœud")
**And** je peux voir le breakdown par génération (voir Story 1.12)

**Given** un dialogue a été modifié plusieurs fois
**When** je consulte les métadonnées
**Then** la date de dernière modification est affichée avec auteur de la modification
**And** je peux voir l'historique des modifications (voir Story 10.5 pour historique détaillé)

**Given** je consulte les métadonnées depuis la liste
**When** je survole un dialogue
**Then** un tooltip s'affiche avec aperçu métadonnées : "45 nœuds, 8.20€, modifié il y a 2h par Marc"
**And** le tooltip disparaît après 3 secondes ou clic

**Given** je consulte les métadonnées d'un dialogue partagé
**When** le panneau s'affiche
**Then** je vois qui a créé le dialogue et qui l'a modifié en dernier
**And** je vois les permissions (qui a accès, voir Epic 7)

**Technical Requirements:**
- Backend : Endpoint `/api/v1/dialogues/{id}/metadata` (GET) retourne métadonnées complètes
- Service : `DialogueMetadataService` avec méthode `get_dialogue_metadata(dialogue_id)` pour calcul métadonnées
- Calcul coûts : Agréger coûts depuis `cost_logs` (voir Epic 1 Story 1.12-1.13)
- Base de données : Requêtes JOIN `dialogues` + `cost_logs` + `users` pour métadonnées complètes
- Frontend : Composant `DialogueMetadataPanel.tsx` avec affichage métadonnées + tooltip sur liste
- Performance : Métadonnées calculées côté backend, cache optionnel pour <200ms
- Tests : Unit (calcul métadonnées), Integration (API metadata), E2E (affichage métadonnées)

**References:** FR86 (métadonnées dialogue), Story 1.12 (breakdown coûts), Story 8.1 (listing), Story 7.7 (permissions)

---

### Story 8.8: Valider en batch plusieurs dialogues (FR87)

As a **utilisateur gérant des dialogues**,
I want **valider plusieurs dialogues en une seule action**,
So that **je peux vérifier rapidement la qualité et conformité de tous mes dialogues avant export**.

**Acceptance Criteria:**

**Given** j'ai créé plusieurs dialogues
**When** je sélectionne 5 dialogues dans la liste et clique sur "Valider en batch"
**Then** une modal de progression s'affiche "Validation batch : 1/5 dialogues"
**And** chaque dialogue est validé séquentiellement (structure, qualité, conformité)

**Given** la validation batch est en cours
**When** les dialogues sont validés
**Then** la progression est affichée en temps réel (X/Y dialogues validés)
**And** je peux interrompre la validation batch si nécessaire

**Given** la validation batch se termine
**When** tous les dialogues sont validés
**Then** un rapport s'affiche avec : dialogues valides, dialogues avec erreurs, résumé erreurs
**And** chaque dialogue avec erreurs liste les erreurs détectées (orphans, cycles, nœuds vides, etc.)

**Given** un dialogue a des erreurs de validation
**When** je consulte le rapport
**Then** je peux cliquer sur le dialogue pour l'ouvrir dans l'éditeur
**And** les erreurs sont surlignées dans le graphe (voir Epic 4)

**Given** je valide 100+ dialogues en batch
**When** la validation est lancée
**Then** la validation se fait en arrière-plan (pas de blocage UI)
**And** je peux continuer à travailler pendant la validation
**And** une notification s'affiche quand la validation est terminée

**Given** je consulte les résultats de validation batch
**When** le rapport s'affiche
**Then** je peux exporter le rapport (CSV ou JSON) pour documentation
**And** le rapport inclut : dialogue ID, statut validation, liste erreurs, timestamp

**Technical Requirements:**
- Backend : Endpoint `/api/v1/dialogues/batch-validate` (POST) avec liste dialogue IDs
- Service : `BatchValidationService` avec méthode `validate_dialogues_batch(dialogue_ids)` pour validation séquentielle
- Validation : Réutiliser `GraphValidationService` (Epic 4) pour chaque dialogue
- Progression : SSE (Server-Sent Events) ou polling pour progression en temps réel
- Frontend : Composant `BatchValidationModal.tsx` avec progression + rapport résultats
- Performance : Validation parallèle (optionnel, V1.5+) pour grandes batches, séquentiel pour MVP
- Tests : Unit (validation batch logique), Integration (API batch validate), E2E (workflow validation batch)

**References:** FR87 (validation batch), Epic 4 (validation dialogues), Story 8.1 (listing), NFR-P3 (API Response <200ms)

---

### Story 8.9: Générer en batch depuis plusieurs nœuds de départ (FR88)

As a **utilisateur créant des dialogues**,
I want **générer des nœuds en batch depuis plusieurs nœuds de départ différents**,
So that **je peux créer rapidement plusieurs branches de dialogue en parallèle depuis différents points du graphe**.

**Acceptance Criteria:**

**Given** j'ai un dialogue avec plusieurs nœuds ayant des choix joueur
**When** je sélectionne 3 nœuds différents dans le graphe
**Then** un menu contextuel s'affiche avec option "Générer batch depuis sélection"
**And** je peux lancer la génération batch pour ces 3 nœuds

**Given** je lance une génération batch depuis 3 nœuds
**When** la génération commence
**Then** pour chaque nœud sélectionné, un batch de nœuds est généré (3-8 nœuds par nœud de départ)
**And** la modal de progression affiche "Génération batch : Nœud 1/3 - 5/8 nœuds générés"
**And** tous les nœuds générés sont automatiquement liés à leurs nœuds parents respectifs

**Given** la génération batch depuis plusieurs nœuds est en cours
**When** un nœud de départ échoue (erreur LLM)
**Then** les autres nœuds de départ continuent à générer
**And** un rapport d'erreur liste les nœuds de départ qui ont échoué
**And** je peux régénérer individuellement les nœuds de départ échoués

**Given** la génération batch se termine avec succès
**When** tous les nœuds sont générés
**Then** un résumé s'affiche "X nœuds générés depuis Y nœuds de départ"
**And** tous les nœuds générés sont visibles dans le graphe
**And** les connexions parent→enfant sont créées automatiquement

**Given** je génère en batch depuis nœuds avec contextes GDD différents
**When** les nœuds sont générés
**Then** chaque batch utilise le contexte GDD approprié pour son nœud de départ
**And** la cohérence narrative est maintenue pour chaque branche

**Given** je génère en batch depuis 10+ nœuds
**When** la génération est lancée
**Then** la génération se fait en arrière-plan (pas de blocage UI)
**And** je peux continuer à travailler pendant la génération
**And** une notification s'affiche quand la génération est terminée

**Technical Requirements:**
- Backend : Endpoint `/api/v1/dialogues/{id}/batch-generate-from-nodes` (POST) avec liste node IDs de départ
- Service : `BatchGenerationService` avec méthode `generate_from_multiple_nodes(dialogue_id, node_ids, context)` pour génération parallèle
- Génération : Réutiliser `UnityDialogueGenerationService` (Epic 1) pour chaque nœud de départ
- Contexte : Chaque nœud de départ peut avoir son propre contexte GDD (personnages, lieux différents)
- Progression : SSE (Server-Sent Events) pour progression en temps réel multi-nœuds
- Frontend : Sélection multiple nœuds (voir Epic 2 Story 2.10) + menu contextuel "Générer batch"
- Performance : Génération parallèle (optionnel, V1.5+) pour plusieurs nœuds, séquentiel pour MVP
- Tests : Unit (génération batch logique), Integration (API batch generate), E2E (workflow génération batch)

**References:** FR88 (génération batch multi-nœuds), Story 1.2 (génération batch), Story 2.10 (sélection multiple), Epic 1 (génération dialogues), NFR-P2 (LLM Generation <2min batch)

