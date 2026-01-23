## Epic 13: Monitoring et analytics

Les utilisateurs peuvent monitorer les métriques de performance du système (temps génération, latence API) et visualiser les tendances dans un dashboard analytics. Le système fournit visibilité sur la santé et performance de l'application.

**FRs covered:** FR112-113 (monitoring métriques performance, dashboard analytics tendances)

**NFRs covered:** NFR-P1 (Performance - Generation <30s), NFR-P2 (API Latency <200ms), NFR-P3 (API Response <200ms)

**Valeur utilisateur:** Comprendre la performance du système, identifier les goulots d'étranglement, et optimiser l'utilisation des ressources LLM avec visibilité sur coûts, latences, et tendances.

**Dépendances:** Epic 0 (infrastructure), Epic 3 (génération LLM), Epic 6 (coûts)

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

### Story 13.1: Monitorer métriques performance système (temps génération, latence API) (FR112)

As a **utilisateur gérant des dialogues**,
I want **monitorer les métriques de performance du système (temps génération, latence API)**,
So that **je peux identifier les problèmes de performance et optimiser mon workflow**.

**Acceptance Criteria:**

**Given** je consulte le dashboard de monitoring
**When** j'ouvre "Usage/Statistiques"
**Then** un dashboard s'affiche avec métriques de performance :
- Temps moyen génération : X secondes
- Latence API moyenne : Y millisecondes
- Taux de succès : Z%
- Nombre total d'appels LLM : N

**Given** je consulte les métriques de génération
**When** les métriques sont chargées
**Then** je peux voir :
- Temps génération par type (nœud unique, batch, variantes)
- Temps génération par modèle LLM (gpt-4o, gpt-4-turbo, etc.)
- Distribution des temps (min, max, médiane, p95, p99)
- Temps génération sur différentes périodes (jour, semaine, mois)

**Given** je consulte les métriques de latence API
**When** les métriques sont chargées
**Then** je peux voir :
- Latence moyenne par endpoint (generate, preview, validate, etc.)
- Latence par type de requête (GET, POST, PUT, DELETE)
- Latence par période (jour, semaine, mois)
- Distribution des latences (min, max, médiane, p95, p99)

**Given** je consulte les métriques en temps réel
**When** une génération est en cours
**Then** un indicateur s'affiche "Génération en cours - X secondes écoulées"
**And** les métriques sont mises à jour en temps réel (si streaming activé)

**Given** je consulte les métriques détaillées d'une génération
**When** je clique sur un enregistrement dans l'historique
**Then** les détails s'affichent :
- Temps total génération : X secondes
- Temps construction prompt : Y secondes
- Temps appel LLM : Z secondes
- Temps validation : W secondes
- Latence réseau : V millisecondes

**Given** je consulte les métriques de performance
**When** je filtre par période (ex: dernière semaine)
**Then** seules les métriques de cette période sont affichées
**And** je peux comparer avec période précédente (ex: semaine précédente)

**Given** je consulte les métriques de performance
**When** je filtre par modèle LLM (ex: gpt-4o uniquement)
**Then** seules les métriques de ce modèle sont affichées
**And** je peux comparer les performances entre modèles

**Given** une métrique de performance est anormale (ex: temps génération >5min)
**When** je consulte le dashboard
**Then** un warning s'affiche "Temps génération élevé détecté - X générations >5min cette semaine"
**And** je peux cliquer pour voir les détails des générations lentes

**Technical Requirements:**
- Backend : Service `PerformanceMetricsService` pour collecter et agréger métriques performance
- Tracking : Middleware `LoggingMiddleware` (existant) pour mesurer latence API automatiquement
- Métriques : Enregistrement temps génération, latence API, temps par étape (prompt, LLM, validation)
- API : Endpoint `/api/v1/metrics/performance` (GET) retourne métriques agrégées avec filtres période/modèle
- Frontend : Composant `PerformanceMetricsDashboard.tsx` avec graphiques, tableaux, filtres
- Visualisation : Graphiques temps réel (Chart.js ou Recharts) pour tendances performance
- Tests : Unit (calcul métriques), Integration (API metrics), E2E (workflow monitoring)

**References:** FR112 (monitoring métriques performance), Story 6.1 (tracking coûts), Story 6.2 (historique usage), NFR-P1 (Performance <30s), NFR-P2 (API Latency <200ms)

---

### Story 13.2: Voir tendances performance dans le temps (dashboard analytics) (FR113)

As a **utilisateur gérant des dialogues**,
I want **voir les tendances de performance dans le temps dans un dashboard analytics**,
So that **je peux identifier les évolutions, optimisations, et problèmes récurrents**.

**Acceptance Criteria:**

**Given** je consulte le dashboard analytics
**When** j'ouvre "Analytics" ou "Tendances"
**Then** un dashboard s'affiche avec graphiques de tendances :
- Évolution temps génération (ligne temporelle)
- Évolution latence API (ligne temporelle)
- Évolution coûts LLM (ligne temporelle)
- Évolution taux de succès (ligne temporelle)

**Given** je consulte les tendances de temps génération
**When** le graphique est chargé
**Then** une ligne temporelle s'affiche avec :
- Points de données par jour/semaine/mois (selon période sélectionnée)
- Ligne de tendance (moyenne mobile)
- Zones de performance (vert = bon, orange = acceptable, rouge = problème)
- Annotations pour événements importants (ex: changement modèle LLM)

**Given** je consulte les tendances de latence API
**When** le graphique est chargé
**Then** une ligne temporelle s'affiche avec :
- Latence moyenne par jour
- Latence p95 et p99 (percentiles)
- Comparaison avec objectif NFR (<200ms)
- Indicateurs de dégradation (spikes, tendance haussière)

**Given** je consulte les tendances de coûts
**When** le graphique est chargé
**Then** une ligne temporelle s'affiche avec :
- Coût total par jour/semaine/mois
- Coût par modèle LLM (stacked area chart)
- Projection coût futur (basée sur tendance)
- Budget vs réel (si budget configuré)

**Given** je consulte les tendances de taux de succès
**When** le graphique est chargé
**Then** une ligne temporelle s'affiche avec :
- Taux de succès par jour (%)
- Nombre d'erreurs par jour
- Types d'erreurs (stacked bar chart)
- Corrélation avec changements système (annotations)

**Given** je compare deux périodes
**When** je sélectionne "Comparer périodes"
**Then** deux lignes temporelles sont affichées côte à côte (période A vs période B)
**And** les différences sont surlignées (amélioration = vert, dégradation = rouge)
**And** un résumé affiche "Amélioration de X% en temps génération, dégradation de Y% en latence"

**Given** je consulte les tendances
**When** je filtre par modèle LLM
**Then** seules les tendances de ce modèle sont affichées
**And** je peux comparer plusieurs modèles simultanément (multi-lignes)

**Given** je consulte les tendances
**When** je survole un point de données
**Then** un tooltip s'affiche avec :
- Date/heure précise
- Valeur exacte
- Contexte (nombre appels, événements ce jour)
- Lien vers détails (cliquer pour voir enregistrements)

**Given** je consulte les tendances
**When** je détecte une anomalie (ex: pic de latence)
**Then** je peux cliquer sur le point pour voir les détails
**And** une liste s'affiche avec les appels concernés (timestamp, endpoint, durée, erreur si applicable)

**Given** j'exporte les données analytics
**When** je clique sur "Exporter données" (CSV ou JSON)
**Then** un fichier est téléchargé avec toutes les métriques de tendances
**And** le fichier inclut : dates, métriques, annotations, événements

**Technical Requirements:**
- Backend : Service `AnalyticsService` pour calculer tendances et agrégations temporelles
- Agrégation : Calcul métriques par jour/semaine/mois (grouping par timestamp)
- API : Endpoint `/api/v1/analytics/trends` (GET) retourne données tendances avec filtres période/modèle
- Frontend : Composant `AnalyticsDashboard.tsx` avec graphiques temporels (Chart.js ou Recharts)
- Visualisation : Lignes temporelles, stacked area charts, bar charts pour comparaisons
- Annotations : Système d'annotations pour marquer événements importants (changements config, incidents)
- Projection : Algorithme de projection tendance pour prévoir coûts/performance futurs
- Tests : Unit (calcul tendances), Integration (API analytics), E2E (workflow analytics)

**References:** FR113 (dashboard analytics tendances), Story 13.1 (monitoring métriques), Story 6.1 (tracking coûts), Story 6.2 (historique usage), NFR-P1 (Performance), NFR-P2 (API Latency)

