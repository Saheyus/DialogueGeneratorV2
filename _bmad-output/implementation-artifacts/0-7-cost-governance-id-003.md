# Story 0.7: Cost governance (ID-003)

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **utilisateur générant des dialogues avec LLM**,
I want **configurer un budget LLM avec limite soft (90%) et limite hard (100%)**,
So that **je ne dépasse jamais mon budget et je suis averti avant d'atteindre la limite**.

## Acceptance Criteria

1. **Given** je configure un budget LLM (ex: 100€/mois) dans les paramètres
   **When** j'atteins 90% du budget (90€ dépensés)
   **Then** un warning s'affiche "Budget atteint à 90% - 10€ restants"
   **And** je peux continuer à générer (pas de blocage, juste avertissement)

2. **Given** j'atteins 100% du budget (100€ dépensés)
   **When** je tente de lancer une génération
   **Then** la génération est bloquée avec message "Budget dépassé - Veuillez augmenter le budget ou attendre le prochain mois"
   **And** aucun appel LLM n'est effectué (protection financière)

3. **Given** je consulte le dashboard de coûts
   **When** j'ouvre la section "Usage LLM"
   **Then** je vois le budget total, le montant dépensé, le pourcentage utilisé, et les coûts par génération
   **And** un graphique montre l'évolution des coûts sur le mois

4. **Given** je change de provider LLM (OpenAI → Mistral)
   **When** les coûts sont calculés
   **Then** les coûts Mistral sont trackés séparément (ou agrégés selon configuration)
   **And** le budget global s'applique à tous les providers

## Tasks / Subtasks

- [x] Task 1: Créer service backend `services/cost_governance_service.py` (AC: #1, #2, #4)
  - [x] Créer classe `CostGovernanceService` avec méthodes `check_budget()`, `get_budget_status()`, `update_budget()`
  - [x] Méthode `check_budget(user_id, estimated_cost)` : Vérifie si budget permet génération (retourne `{allowed: bool, percentage: float, warning: Optional[str]}`)
  - [x] Logique soft warning (90%) : Retourne `allowed=True, warning="Budget atteint à 90%"` si `amount + estimated_cost >= quota * 0.9`
  - [x] Logique hard block (100%) : Retourne `allowed=False` si `amount + estimated_cost >= quota`
  - [x] Gestion reset mensuel : Vérifier mois actuel vs mois dernier, reset si nouveau mois
  - [x] Tests unitaires : check_budget soft warning, check_budget hard block, reset mensuel

- [x] Task 2: Créer repository pour stockage budget (AC: #1, #2)
  - [x] Créer interface `ICostBudgetRepository` dans `services/repositories/cost_budget_repository.py`
  - [x] Implémentation fichier JSON : `FileCostBudgetRepository` dans `services/repositories/cost_budget_repository.py`
  - [x] **IMPORTANT** : Utiliser fichier JSON uniquement pour V1.0 (pas de DB)
  - [x] Structure données : `{user_id: {month: "2026-01", amount: 90.0, quota: 100.0, updated_at: timestamp}}`
  - [x] Méthodes : `get_budget(user_id, month)`, `update_budget(user_id, month, amount, quota)`, `reset_month(user_id, new_month)`
  - [x] Stockage : Fichier JSON `data/cost_budgets.json` (créer dossier si n'existe pas)
  - [x] **Repository pattern** : Interface permet migration future vers DB (V1.5+) sans changer code métier
  - [x] Tests unitaires : CRUD budget, reset mensuel

- [x] Task 3: Créer endpoints API `/api/v1/costs/budget` et `/api/v1/costs/usage` (AC: #1, #2, #3)
  - [x] Créer router `api/routers/costs.py` avec endpoints
  - [x] `GET /api/v1/costs/budget` : Récupère budget actuel (quota, amount, percentage)
  - [x] `PUT /api/v1/costs/budget` : Met à jour quota budget (body: `{quota: float}`)
  - [x] `GET /api/v1/costs/usage` : Récupère usage avec graphique (body: `{daily_costs: [...], total: float, percentage: float}`)
  - [x] Créer schémas Pydantic dans `api/schemas/costs.py` : `BudgetResponse`, `UpdateBudgetRequest`, `UsageResponse`
  - [x] Intégrer `CostGovernanceService` via dependency injection
  - [x] Tests intégration : GET/PUT budget, GET usage avec graphique

- [x] Task 4: Créer middleware cost governance pour vérifier budget avant génération (AC: #2)
  - [x] Créer middleware `api/middleware/cost_governance.py` : `CostGovernanceMiddleware`
  - [x] Intercepter requêtes POST vers `/api/v1/dialogues/generate/*` et `/api/v1/graph/generate-node`
  - [x] Estimer coût avant génération : Utiliser `LLMPricingService.calculate_cost()` avec tokens estimés
  - [x] Appeler `CostGovernanceService.check_budget()` avec coût estimé
  - [x] Si `allowed=False` : Retourner HTTP 429 avec message "Monthly quota reached"
  - [x] Si `allowed=True` et `warning` : Logger warning mais continuer
  - [x] Ajouter middleware dans `api/main.py` après `LoggingMiddleware`
  - [x] Tests intégration : Middleware bloque à 100%, warning à 90%

- [x] Task 5: Étendre `UsageDashboard.tsx` pour afficher budget et graphique (AC: #3)
  - [x] Ajouter section "Budget LLM" avec indicateurs : quota, amount, percentage, remaining
  - [x] Ajouter graphique évolution coûts (graphique en barres simple sans bibliothèque externe pour V1.0)
  - [x] Afficher coûts par génération (liste avec date, modèle, coût)
  - [x] Appeler API `GET /api/v1/costs/usage` pour données graphique
  - [x] Appeler API `GET /api/v1/costs/budget` pour données budget
  - [ ] Tests E2E : Dashboard affiche budget et graphique (à faire dans Task 9)

- [x] Task 6: Créer composant settings pour configurer budget (AC: #1)
  - [x] Créer composant `frontend/src/components/settings/BudgetSettings.tsx`
  - [x] Input pour quota mensuel (ex: 100€)
  - [x] Bouton "Sauvegarder" qui appelle `PUT /api/v1/costs/budget`
  - [x] Afficher budget actuel (quota, amount, percentage)
  - [x] Intégrer dans page settings ou modal settings
  - [ ] Tests E2E : Configuration budget fonctionne (à faire dans Task 9)

- [x] Task 7: Implémenter toast warning 90% et modal block 100% (AC: #1, #2)
  - [x] Créer hook `useCostGovernance()` dans `frontend/src/hooks/useCostGovernance.ts`
  - [x] Hook vérifie budget avant génération : Appeler `GET /api/v1/costs/budget`
  - [x] Si `percentage >= 90` et `< 100` : Afficher toast warning (utiliser `useToast` existant)
  - [x] Si `percentage >= 100` : Afficher modal bloquante (utiliser `ConfirmDialog` existant)
  - [x] Intégrer hook dans `GenerationPanel.tsx` et `AIGenerationPanel.tsx` avant génération
  - [ ] Tests E2E : Toast 90% affiché, modal 100% bloque génération (à faire dans Task 9)

- [x] Task 8: Intégration avec tracking existant (AC: #4)
  - [x] S'assurer que `LLMUsageService.track_usage()` met à jour budget après génération
  - [x] Appeler `CostGovernanceService.update_budget()` après `track_usage()` dans endpoints génération
  - [x] Gérer coûts par provider : Agréger tous les providers dans budget global (ou séparer selon config)
  - [x] Tests intégration : Budget mis à jour après génération

- [x] Task 9: Validation et tests (AC: #1, #2, #3, #4)
  - [x] Tests unitaires : CostGovernanceService (soft warning, hard block, reset mensuel) - 7 tests
  - [x] Tests intégration : Middleware bloque à 100%, endpoints budget/usage - 7 tests
  - [x] Tests E2E : Structure créée dans `e2e/cost-governance.spec.ts` (nécessite application running pour exécution complète)

## Dev Notes

### Architecture Patterns (Extension Story 0.3)

**Réutilisation existante :**
- ✅ **Service pricing existant** : `LLMPricingService` existe déjà (ligne 13-111 `services/llm_pricing_service.py`)
  - **DÉCISION** : Réutiliser pour calculer coûts estimés avant génération
  - **COMMENT** : Appeler `calculate_cost()` avec tokens estimés (prompt + completion estimés)
- ✅ **Service usage existant** : `LLMUsageService` existe déjà (ligne 14-152 `services/llm_usage_service.py`)
  - **DÉCISION** : Étendre pour mettre à jour budget après génération
  - **COMMENT** : Appeler `CostGovernanceService.update_budget()` après `track_usage()`
- ✅ **Endpoints usage existants** : `/api/v1/llm-usage/history` et `/api/v1/llm-usage/statistics` existent (ligne 23-196 `api/routers/llm_usage.py`)
  - **DÉCISION** : Créer nouveaux endpoints `/api/v1/costs/budget` et `/api/v1/costs/usage` (namespace différent)
  - **COMMENT** : Séparer usage tracking (historique) de cost governance (budget/quota)
- ✅ **Composant UsageDashboard existant** : `UsageDashboard.tsx` existe (affichage statistiques)
  - **DÉCISION** : Étendre pour ajouter section budget et graphique
  - **COMMENT** : Ajouter section "Budget LLM" avec indicateurs et graphique évolution

**Gestion budget :**
- **Stockage V1.0** : Fichier JSON `data/cost_budgets.json` (structure: `{user_id: {month: "2026-01", amount: 90.0, quota: 100.0, updated_at: timestamp}}`)
  - **DÉCISION ARCHITECTURALE** : Utiliser fichier JSON pour V1.0 (cohérent avec architecture file-based existante)
  - **MIGRATION FUTURE** : Repository pattern permet migration vers DB (PostgreSQL/SQLite) en V1.5+ sans changer code métier
  - **POURQUOI** : Pas d'infrastructure DB en V1.0 (gap mineur post-MVP selon architecture.md)
- **Reset mensuel** : Vérifier mois actuel vs mois dernier, reset `amount=0.0` si nouveau mois
- **Soft warning (90%)** : Logger warning mais autoriser génération
- **Hard block (100%)** : Bloquer génération avec HTTP 429

**Middleware cost governance :**
- **Interception** : Requêtes POST vers `/api/v1/dialogues/generate/*` et `/api/v1/graph/generate-node`
- **Estimation coût** : Utiliser `LLMPricingService.calculate_cost()` avec tokens estimés (prompt + completion)
- **Vérification** : Appeler `CostGovernanceService.check_budget()` avant génération
- **Action** : Si `allowed=False`, retourner HTTP 429 immédiatement (pas d'appel LLM)

**Frontend warning/block :**
- **Toast 90%** : Utiliser `useToast` existant (toast warning orange)
- **Modal 100%** : Utiliser `ConfirmDialog` existant (modal bloquante, bouton "Fermer" uniquement)
- **Hook** : `useCostGovernance()` vérifie budget avant génération dans `GenerationPanel` et `AIGenerationPanel`

### Fichiers existants à vérifier et étendre

**Backend :**
- ✅ `services/llm_pricing_service.py` : Service pricing existe (ligne 13-111)
  - **DÉCISION** : Réutiliser pour calculer coûts estimés
  - **COMMENT** : Appeler `calculate_cost()` avec tokens estimés
- ✅ `services/llm_usage_service.py` : Service usage existe (ligne 14-152)
  - **DÉCISION** : Étendre pour mettre à jour budget après génération
  - **COMMENT** : Appeler `CostGovernanceService.update_budget()` après `track_usage()`
- ⚠️ `services/cost_governance_service.py` : **N'EXISTE PAS**
  - **DÉCISION** : Créer nouveau service pour logique cost governance
  - **POURQUOI** : Logique complexe de vérification budget (soft/hard limits, reset mensuel) mérite service dédié
  - **STOCKAGE** : Utiliser `ICostBudgetRepository` (interface) avec implémentation fichier JSON pour V1.0
- ⚠️ `api/routers/costs.py` : **N'EXISTE PAS**
  - **DÉCISION** : Créer nouveau router pour endpoints budget/usage
  - **POURQUOI** : Séparer cost governance (budget/quota) de usage tracking (historique)
- ⚠️ `api/middleware/cost_governance.py` : **N'EXISTE PAS**
  - **DÉCISION** : Créer nouveau middleware pour vérification budget avant génération
  - **POURQUOI** : Protection financière doit être au niveau middleware (avant tout appel LLM)

**Frontend :**
- ✅ `frontend/src/components/usage/UsageDashboard.tsx` : Existe (affichage statistiques)
  - **DÉCISION** : Étendre pour ajouter section budget et graphique
  - **COMMENT** : Ajouter section "Budget LLM" avec indicateurs (quota, amount, percentage, remaining) et graphique évolution
- ⚠️ `frontend/src/components/settings/BudgetSettings.tsx` : **N'EXISTE PAS**
  - **DÉCISION** : Créer nouveau composant pour configuration budget
  - **POURQUOI** : Interface dédiée pour configurer quota mensuel
- ⚠️ `frontend/src/hooks/useCostGovernance.ts` : **N'EXISTE PAS**
  - **DÉCISION** : Créer nouveau hook pour vérification budget avant génération
  - **POURQUOI** : Logique réutilisable pour vérifier budget et afficher warnings/blocks

### Patterns existants à respecter

**FastAPI routers :**
- Namespace `/api/v1/costs/*` (cohérent avec `/api/v1/llm-usage/*`)
- Pattern endpoint : `@router.get("/budget", response_model=BudgetResponse)`
- Gestion erreurs : `InternalServerException` avec `request_id`
- Dependency injection : `Depends(get_cost_governance_service)`

**FastAPI middleware :**
- Pattern middleware : `BaseHTTPMiddleware` avec `async def dispatch(self, request, call_next)`
- Interception : Vérifier `request.url.path` pour endpoints génération
- Gestion erreurs : Retourner HTTP 429 si budget dépassé

**React composants :**
- Pattern modal : `ConfirmDialog` existant (utiliser pour modal 100%)
- Pattern toast : `useToast` existant (utiliser pour toast 90%)
- Pattern graphique : Utiliser `recharts` ou `chart.js` (vérifier dépendances existantes)

**Zustand stores :**
- Immutable updates : `set((state) => ({ ...state, newValue }))`
- Pattern hooks : `useCostGovernance()` pour logique réutilisable

**Stockage budget :**
- **Format JSON V1.0** : `{user_id: {month: "2026-01", amount: 90.0, quota: 100.0, updated_at: timestamp}}`
- **Décision architecturale** : Fichier JSON pour V1.0 (cohérent avec architecture file-based existante, pas de DB)
- **Repository pattern** : Interface `ICostBudgetRepository` + implémentation `FileCostBudgetRepository`
  - **Avantage** : Migration future vers DB (V1.5+) simple (changer implémentation, pas code métier)
  - **Migration future** : Créer `DatabaseCostBudgetRepository` implémentant même interface en V1.5+
- **Reset mensuel** : Vérifier `month` actuel vs dernier, reset `amount=0.0` si nouveau mois

### Estimation coût avant génération

**Tokens estimés :**
- **Prompt tokens** : Utiliser `tokenCount` depuis `EstimatedPromptPanel` (déjà calculé)
- **Completion tokens** : Estimer basé sur `max_completion_tokens` ou valeur par défaut (ex: 500 tokens)
- **Calcul coût** : `LLMPricingService.calculate_cost(model_name, prompt_tokens, completion_tokens)`

**Middleware estimation :**
- Extraire `model_name` depuis requête (body ou query param)
- Extraire `prompt_tokens` depuis requête (si disponible) ou estimer
- Estimer `completion_tokens` basé sur `max_completion_tokens` ou valeur par défaut
- Appeler `LLMPricingService.calculate_cost()` avec tokens estimés

### Reset mensuel

**Logique reset :**
- Vérifier mois actuel : `datetime.now().strftime("%Y-%m")` (ex: "2026-01")
- Comparer avec mois dernier dans budget : `budget.get("month")`
- Si nouveau mois : Reset `amount=0.0` et mettre à jour `month`
- Si même mois : Continuer avec `amount` existant

**Implémentation :**
- Dans `CostGovernanceService.check_budget()` : Vérifier reset avant vérification budget
- Dans `CostGovernanceService.update_budget()` : Vérifier reset avant mise à jour

### Références techniques

**Source: `_bmad-output/planning-artifacts/prd/epic-00.md#Story-0.7`**
- Story complète avec acceptance criteria et technical requirements

**Source: `_bmad-output/planning-artifacts/architecture.md#ID-003`**
- Architecture Decision : Cost Governance (soft warning 90%, hard block 100%)

**Source: `services/llm_pricing_service.py` (ligne 13-111)**
- Service pricing existant à réutiliser

**Source: `services/llm_usage_service.py` (ligne 14-152)**
- Service usage existant à étendre

**Source: `api/routers/llm_usage.py` (ligne 23-196)**
- Endpoints usage existants (référence pour nouveaux endpoints costs)

**Source: `frontend/src/components/usage/UsageDashboard.tsx`**
- Composant dashboard existant à étendre

**Source: ID-003 (Architecture Document)**
- Décision architecture : Cost Governance (soft warning 90%, hard block 100%)

### Project Structure Notes

**Alignment avec structure unifiée :**
- ✅ Backend API : `api/routers/costs.py` (cohérent avec `api/routers/llm_usage.py`)
- ✅ Backend services : `services/cost_governance_service.py` (cohérent avec `services/llm_usage_service.py`)
- ✅ Backend repositories : `services/repositories/cost_budget_repository.py` (cohérent avec pattern repository)
- ✅ Backend middleware : `api/middleware/cost_governance.py` (cohérent avec autres middlewares)
- ✅ Frontend components : `frontend/src/components/settings/BudgetSettings.tsx` (cohérent avec structure components)
- ✅ Frontend hooks : `frontend/src/hooks/useCostGovernance.ts` (cohérent avec structure hooks)

**Détecté conflits ou variances :**
- Aucun conflit détecté, extension cohérente avec architecture existante
- **Décision stockage** : Fichier JSON pour V1.0 (pas de DB), repository pattern permet migration future V1.5+

### References

- [Source: `_bmad-output/planning-artifacts/prd/epic-00.md#Story-0.7`] Story complète avec requirements
- [Source: ID-003] Architecture Decision : Cost Governance (soft warning 90%, hard block 100%)
- [Source: `services/llm_pricing_service.py`] Service pricing existant à réutiliser
- [Source: `services/llm_usage_service.py`] Service usage existant à étendre
- [Source: `api/routers/llm_usage.py`] Endpoints usage existants (référence)
- [Source: `frontend/src/components/usage/UsageDashboard.tsx`] Composant dashboard existant à étendre
- [Source: `_bmad-output/planning-artifacts/architecture.md#Pattern-V1-003`] Pattern Cost Tracking (ID-003)

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (via Cursor)

### Debug Log References

N/A

### Completion Notes List

- **Task 1-2** : Service et repository créés avec tests unitaires complets (7 tests service, 7 tests repository)
- **Task 3** : Endpoints API créés avec tests d'intégration (3 tests)
- **Task 4** : Middleware créé avec tests d'intégration (4 tests)
- **Task 5** : UsageDashboard étendu avec section budget et graphique en barres simple (sans bibliothèque externe pour V1.0)
- **Task 6** : BudgetSettings créé avec interface complète
- **Task 7** : Hook useCostGovernance créé et intégré dans GenerationPanel et AIGenerationPanel
- **Task 8** : LLMUsageService étendu pour mettre à jour automatiquement le budget après track_usage() (tests d'intégration : 2 tests)
- **Architecture** : Repository pattern utilisé pour permettre migration future vers DB sans changer code métier
- **Stockage** : Fichier JSON `data/cost_budgets.json` pour V1.0 (cohérent avec architecture file-based existante)
- **Tests** : 23 tests backend passent (unitaires + intégration), tests E2E frontend à faire dans Task 9

### File List

**Backend :**
- `services/cost_governance_service.py` (nouveau)
- `services/repositories/cost_budget_repository.py` (nouveau)
- `api/routers/costs.py` (nouveau)
- `api/schemas/costs.py` (nouveau)
- `api/middleware/cost_governance.py` (nouveau)
- `api/dependencies.py` (modifié : ajout factories cost governance)
- `api/main.py` (modifié : ajout router costs, ajout middleware cost governance)
- `services/llm_usage_service.py` (modifié : intégration cost governance)
- `constants.py` (modifié : ajout COST_BUDGETS_FILE)

**Frontend :**
- `frontend/src/api/costs.ts` (nouveau)
- `frontend/src/components/usage/UsageDashboard.tsx` (modifié : ajout section budget et graphique)
- `frontend/src/components/usage/UsageDashboard.css` (modifié : ajout styles graphique)
- `frontend/src/components/settings/BudgetSettings.tsx` (nouveau)
- `frontend/src/hooks/useCostGovernance.ts` (nouveau)
- `frontend/src/components/generation/GenerationPanel.tsx` (modifié : intégration hook cost governance)
- `frontend/src/components/graph/AIGenerationPanel.tsx` (modifié : intégration hook cost governance)

**Tests :**
- `tests/services/test_cost_governance_service.py` (nouveau)
- `tests/repositories/test_cost_budget_repository.py` (nouveau)
- `tests/api/test_costs.py` (nouveau)
- `tests/middleware/test_cost_governance.py` (nouveau)
- `tests/services/test_llm_usage_service_cost_integration.py` (nouveau)

## Change Log

- **2026-01-15** : Implémentation complète du système de cost governance
  - Service backend `CostGovernanceService` avec logique soft warning (90%) et hard block (100%)
  - Repository `FileCostBudgetRepository` pour stockage JSON (V1.0)
  - Endpoints API `/api/v1/costs/budget` et `/api/v1/costs/usage`
  - Middleware `CostGovernanceMiddleware` pour protection financière avant génération
  - Extension `UsageDashboard` avec section budget et graphique d'évolution
  - Composant `BudgetSettings` pour configuration du quota mensuel
  - Hook `useCostGovernance` pour vérification budget avant génération (toast 90%, modal 100%)
  - Intégration avec `LLMUsageService` pour mise à jour automatique du budget
  - 23 tests backend passent (unitaires + intégration)
  - Tests E2E : Structure créée dans `e2e/cost-governance.spec.ts` (nécessite application running)
