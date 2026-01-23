### Epic 15: RLM Context Selector (Sélection Automatique Contexte GDD)

**CONTEXTE CRITIQUE** : La sélection manuelle de sous-sections et sous-parties de fiches GDD est cognitivement coûteuse et error-prone. Les contextes de 20k+ tokens causent "context rot" (dégradation attention, dépendances longues brouillées, rappel précis dégradé) observé en test. Cette Epic implémente un service optionnel RLM (Recursive Language Models) qui explore programmatiquement le GDD via function calling, sélectionne intelligemment les éléments pertinents (fiches, sous-sections, sous-parties), et réduit le contexte de 20k+ → 12-15k tokens (Phase 1) → 6-10k tokens (Phase 2) sans perte de pertinence.

Les utilisateurs peuvent activer/désactiver la sélection automatique via toggle "Auto Selection" (à gauche du bouton "Générer", panneau de droite), voir les justifications des sélections (format compact, détails on-demand), et utiliser override/lock pour forcer/ajouter des éléments même en auto. Le service est optionnel (fallback sélection manuelle si désactivé) et s'intègre avec `ContextBuilder` sans casser invariants.

**FRs covered:** FR1-FR8 (RLM Context Selector - Toggle UI, Service RLM, Outils GDD, Extension ContextFieldManager, Endpoint API, Affichage Justifications, Mode Override, Fallback Gracieux)

**NFRs covered:** NFR1-NFR6 (Performance <5s latence, Usability justifications claires, Reliability fallback gracieux, Testability mocks LLM, Reproducibility seed optionnel, Compatibility ContextBuilder préservé)

**Valeur utilisateur:** Réduction friction sélection contexte (10+ clics → 1 clic), réduction tokens contexte (20k+ → 12-15k Phase 1, 6-10k Phase 2) sans perte pertinence, expliquabilité (justifications claires), contrôle utilisateur (override/lock).

**Dépendances:** Aucune (service optionnel, peut être développé indépendamment). Compatible Epic 3 (Gestion contexte narratif GDD) mais ne bloque pas.

**Implementation Priority:** Epic 15 Story 1 = Service RLM `RLMContextSelector` + Outils GDD `GDDToolsProvider` - **FONDATION** pour toutes les autres stories

**Related ADR:** ADR-005 (RLM Context Selector - Autonomous Context Selection)

---

## ⚠️ GARDE-FOUS - Vérification de l'Existant (Scrum Master)

**OBLIGATOIRE avant création de chaque story de cet epic :**

### Checklist de Vérification

1. **Fichiers mentionnés dans les stories :**
   - [ ] Vérifier existence avec `glob_file_search` ou `grep`
   - [ ] Vérifier chemins corrects (ex: `services/` vs `core/context/`)
   - [ ] Si existe : **DÉCISION** - Étendre ou remplacer ? (documenter dans story)

2. **Composants/Services similaires :**
   - [ ] Rechercher composants React similaires (`codebase_search` dans `frontend/src/components/`)
   - [ ] Rechercher stores Zustand similaires (`codebase_search` dans `frontend/src/store/`)
   - [ ] Rechercher services Python similaires (`codebase_search` dans `services/`, `core/context/`)
   - [ ] Si similaire existe : **DÉCISION** - Réutiliser ou créer nouveau ? (documenter dans story)

3. **Endpoints API :**
   - [ ] Vérifier namespace cohérent (`/api/v1/context/*` vs `/api/v1/dialogues/*`)
   - [ ] Vérifier si endpoint similaire existe (`grep` dans `api/routers/`)
   - [ ] Si endpoint similaire : **DÉCISION** - Étendre ou créer nouveau ? (documenter dans story)

4. **Patterns existants :**
   - [ ] Vérifier patterns Zustand (immutable updates, structure stores)
   - [ ] Vérifier patterns FastAPI (routers, dependencies, schemas)
   - [ ] Vérifier patterns React (composants, hooks, toggles)
   - [ ] Respecter conventions de nommage et structure dossiers

5. **Documentation des décisions :**
   - Si remplacement : Documenter **POURQUOI** dans story "Dev Notes"
   - Si extension : Documenter **COMMENT** (quels champs/méthodes ajouter)
   - Si nouveau : Documenter **POURQUOI** pas de réutilisation

### Fichiers/Composants Spécifiques Epic 15

**OBLIGATOIRE avant création de chaque story de cet epic :**

### Checklist Spécifique Epic 15

1. **Fichiers existants à vérifier :**
   - [ ] `core/context/context_builder.py` (existe déjà, gère build_context_json)
   - [ ] `services/context_field_manager.py` (existe déjà, gère filtrage champs)
   - [ ] `frontend/src/store/generationStore.ts` (existe déjà, gère sceneSelection)
   - [ ] `api/routers/context.py` ou similaire (vérifier existence)
   - [ ] `config/context_config.json` (existe déjà, règles statiques champs)

2. **Patterns existants à respecter :**
   - [ ] Zustand stores : Immutable updates, pattern `set((state) => ({ ...state, newValue }))`
   - [ ] FastAPI routers : Namespace `/api/v1/context/*` (cohérent avec autres routers)
   - [ ] React toggles : Pattern existant (vérifier composants similaires)
   - [ ] Context builder : Ne pas bypasser `build_context_json()`, utiliser section_filters

3. **Décisions de remplacement :**
   - Si story propose de créer un fichier qui existe : **DOCUMENTER** décision (étendre vs remplacer)
   - Si story propose un chemin incorrect : **CORRIGER** avant création
   - Si story propose un pattern différent : **JUSTIFIER** dans "Dev Notes"

---

### Story 15.1: Service RLM ContextSelector + Outils GDD GDDToolsProvider (Fondation)

As a **utilisateur générant des dialogues**,
I want **qu'un agent LLM explore automatiquement le GDD et sélectionne intelligemment les éléments pertinents (fiches, sous-sections)**,
So that **je réduis la friction de sélection manuelle et j'obtiens un contexte optimisé (20k+ → 12-15k tokens) sans perte de pertinence**.

**Acceptance Criteria:**

**Given** un service `RLMContextSelector` existe
**When** j'appelle `select_context(user_instructions, hints, hints_mode, exclude, expansion_radius, max_tokens_target, seed)`
**Then** le service explore le GDD via outils `GDDToolsProvider` (search_bm25, get_related, get_snippet, etc.)
**And** le service produit `ContextSelectionResult` avec `selected_elements` (fiches + modes + `section_filters`), `justifications` (raison + preuve), `trace` (outils appelés, décisions)

**Given** le service respecte limites `MAX_TOOL_CALLS = 50` et `MAX_EXPLORATION_TOKENS = 100000`
**When** une exploration dépasse ces limites
**Then** le service retourne fallback gracieux (hints uniquement, pas d'erreur)
**And** un warning est loggé ("Budget exploration dépassé, utilisation hints uniquement")

**Given** le service reçoit hints explicites (personnages/lieux mentionnés)
**When** le service sélectionne les éléments
**Then** les hints sont toujours inclus (mode full par défaut)
**And** les hints sont marqués `justification.reason = "hint_explicit"`

**Given** un service `GDDToolsProvider` existe
**When** le service expose outils GDD au LLM via function calling
**Then** les outils suivants sont disponibles : `get_node(id)`, `get_fields(id, fields[])`, `list_ids(type, where_field_exists, limit)`, `schema_overview()`, `search_bm25(query, top_k, filter_type)`, `search_regex(pattern, field, top_k)`, `search_by_key_value(key, value, exact)`, `get_snippet(id, field, max_chars, around)`, `get_related(id, relation_keys, depth)`, `count(filter)`, `group_by(field, filter)`, `build_table(ids, columns)`, `diff(id_a, id_b, fields)`

**Given** le service utilise modèle GPT-5-mini pour sélection (coût réduit)
**When** le service explore le GDD
**Then** le budget exploration est séparé du budget génération (100k tokens max, modèle mini)
**And** les coûts exploration sont trackés séparément

**Technical Requirements:**
- Backend : Créer `services/rlm_context_selector.py` avec classe `RLMContextSelector`
  - Méthode `async def select_context(...) -> ContextSelectionResult`
  - Implémentation paradigme RLM : Navigation programmatique GDD, lecture récursive, mémoire de travail compacte, agrégation progressive
  - Limites : `MAX_TOOL_CALLS = 50`, `MAX_EXPLORATION_TOKENS = 100000`
  - Fallback : Si limites dépassées ou erreur LLM → retourner hints uniquement (pas d'erreur)
  - Modèle LLM : GPT-5-mini (coût réduit, qualité suffisante pour sélection)
  - Seed optionnel : Pour reproductibilité (même sélection pour mêmes inputs)
- Backend : Créer `services/gdd_tools_provider.py` avec classe `GDDToolsProvider`
  - Abstraction pour exposer outils GDD au LLM via function calling
  - Outils disponibles : `get_node`, `get_fields`, `list_ids`, `schema_overview`, `search_bm25`, `search_regex`, `search_by_key_value`, `get_snippet`, `get_related`, `count`, `group_by`, `build_table`, `diff`
  - Injection dépendances : `ElementRepository` pour accès GDD
- Backend : Schémas Pydantic `api/schemas/context.py`
  - `SelectContextRequest` (user_instructions, hints, hints_mode, exclude, expansion_radius, max_tokens_target, seed)
  - `SelectContextResponse` (selected_elements, context, trace)
  - `ContextSelectionResult` (selected_elements avec section_filters, justifications, trace)
- Tests : Unit (RLMContextSelector avec mocks LLM, GDDToolsProvider avec mocks repository), Integration (exploration GDD réel avec mini-GDD)

**Dev Notes:**

**Architecture Patterns:**
- **Paradigme RLM** : Le service utilise Recursive Language Models (arXiv:2512.24601) - navigation programmatique GDD, lecture récursive, mémoire de travail compacte, agrégation progressive
- **Function Calling** : `GDDToolsProvider` expose outils GDD au LLM via function calling (OpenAI tools/tool_choice)
- **Limites sécurité** : `MAX_TOOL_CALLS = 50` et `MAX_EXPLORATION_TOKENS = 100000` pour éviter boucles infinies et coûts excessifs
- **Fallback gracieux** : Si RLM échoue (budget dépassé, erreur LLM, limite tool calls), retourner hints uniquement (pas d'erreur, sélection manuelle préservée)

**Réutilisation Code:**
- **ElementRepository** : `GDDToolsProvider` utilise `ElementRepository` existant pour accès GDD (pas de duplication)
- **LLM Client** : `RLMContextSelector` utilise `ILLMClient` existant (via factory) pour appels LLM
- **Modèle GPT-5-mini** : Utiliser modèle mini pour sélection (coût réduit, qualité suffisante vs génération GPT-5.2)

**References:** ADR-005 (RLM Context Selector), FR2-FR3 (Service RLM, Outils GDD), NFR1 (Performance <5s), NFR3 (Reliability fallback gracieux), NFR4 (Testability mocks LLM)

---

### Story 15.2: Extension ContextFieldManager avec section_filters

As a **système de génération de dialogues**,
I want **que `ContextFieldManager` puisse filtrer les champs par sous-sections (include/exclude)**,
So that **les sélections RLM (section_filters) sont correctement appliquées lors du build_context_json()**.

**Acceptance Criteria:**

**Given** une méthode `ContextFieldManager.filter_fields_by_section_filters()` existe
**When** j'appelle la méthode avec `section_filters = {"include": ["Relations.Akthar"], "exclude": ["Rôle cosmologique"]}`
**Then** la méthode combine règles statiques (`context_config.json`) + règles dynamiques (`section_filters`)
**And** seules les sous-sections incluses sont conservées (exclusions appliquées)
**And** le DSL de champs existant n'est pas bypassé (règles statiques préservées)

**Given** `section_filters` contient `include` (sous-sections à inclure)
**When** la méthode filtre les champs
**Then** uniquement les sous-sections listées dans `include` sont conservées
**And** les autres sous-sections sont exclues (sauf si dans règles statiques obligatoires)

**Given** `section_filters` contient `exclude` (sous-sections à exclure)
**When** la méthode filtre les champs
**Then** les sous-sections listées dans `exclude` sont supprimées
**And** les autres sous-sections sont conservées (selon règles statiques)

**Given** `section_filters` est `None` ou vide
**When** la méthode filtre les champs
**Then** seule la logique statique (`context_config.json`) est appliquée (pas de changement comportement existant)
**And** aucun filtrage dynamique n'est appliqué

**Technical Requirements:**
- Backend : Étendre `services/context_field_manager.py` avec méthode `filter_fields_by_section_filters(element_type, fields_to_include, section_filters)`
  - Paramètre `section_filters: Optional[Dict[str, Any]]` avec `include` (list sous-sections), `exclude` (list sous-sections)
  - Combiner règles statiques (`context_config.json`) + règles dynamiques (`section_filters`)
  - Ne pas bypasser le DSL de champs existant (règles statiques préservées)
  - Retourner `List[str]` champs filtrés
- Backend : Intégration avec `ContextBuilder.build_context_json()`
  - Passer `section_filters` depuis `ContextSelectionResult` à `ContextFieldManager`
  - Appliquer filtrage lors de l'extraction des champs pour chaque élément
- Tests : Unit (filter_fields_by_section_filters avec include/exclude/None), Integration (build_context_json avec section_filters)

**Dev Notes:**

**Architecture Patterns:**
- **Extension vs Remplacement** : Étendre `ContextFieldManager` existant (ne pas créer nouveau service)
- **Compatibilité** : Si `section_filters` est `None`, comportement identique à avant (pas de breaking change)
- **DSL préservé** : Les règles statiques `context_config.json` sont toujours appliquées en premier, puis `section_filters` applique filtrage supplémentaire

**Réutilisation Code:**
- **ContextFieldManager** : Étendre classe existante (pas de duplication)
- **context_config.json** : Continuer à utiliser règles statiques existantes (pas de migration)

**References:** ADR-005 (RLM Context Selector - Phase 2 Context Build), FR4 (Extension ContextFieldManager), NFR6 (Compatibility ContextBuilder préservé)

---

### Story 15.3: Endpoint API /select-context

As a **frontend React**,
I want **un endpoint API `/api/v1/context/select-context` qui exécute sélection automatique RLM puis build_context_json()**,
So that **je peux obtenir un contexte optimisé avec sélection automatique en un seul appel**.

**Acceptance Criteria:**

**Given** un endpoint POST `/api/v1/context/select-context` existe
**When** j'envoie `SelectContextRequest` (user_instructions, hints, hints_mode, exclude, expansion_radius, max_tokens_target, seed)
**Then** l'endpoint exécute Phase 1 (RLM sélection automatique via `RLMContextSelector.select_context()`)
**And** l'endpoint exécute Phase 2 (`build_context_json()` avec `selected_elements` et `section_filters`)
**And** l'endpoint retourne `SelectContextResponse` (selected_elements, context, trace)

**Given** le RLM échoue (budget dépassé, erreur LLM, limite tool calls)
**When** l'endpoint reçoit erreur RLM
**Then** l'endpoint retourne fallback gracieux (hints uniquement, `context` construit avec hints, pas d'erreur HTTP)
**And** le code HTTP est 200 (succès avec fallback, pas d'erreur 500)

**Given** l'endpoint reçoit une requête invalide (user_instructions manquant)
**When** la validation Pydantic échoue
**Then** l'endpoint retourne erreur 422 (Validation Error) avec détails champs manquants

**Given** l'endpoint s'intègre avec `ContextBuilder`
**When** l'endpoint appelle `build_context_json()`
**Then** `build_context_json()` utilise `selected_elements` et `section_filters` depuis `ContextSelectionResult`
**And** `build_context_json()` ne bypass pas l'invariant existant (logique préservée)

**Technical Requirements:**
- Backend : Créer ou étendre `api/routers/context.py` avec endpoint POST `/api/v1/context/select-context`
  - Dépendances : `RLMContextSelector` (via `Depends(get_rlm_context_selector)`), `ContextBuilder` (via `Depends(get_context_builder)`)
  - Validation : `SelectContextRequest` (Pydantic schema)
  - Phase 1 : Appeler `rlm_selector.select_context(...)`
  - Phase 2 : Appeler `context_builder.build_context_json(selected_elements, scene_instruction, section_filters)`
  - Réponse : `SelectContextResponse` (Pydantic schema)
  - Gestion erreurs : Fallback gracieux si RLM échoue (hints uniquement, HTTP 200)
- Backend : Injection dépendances `api/dependencies.py`
  - Fonction `get_rlm_context_selector() -> RLMContextSelector`
  - Fonction `get_context_builder() -> ContextBuilder` (existe déjà ou créer)
- Tests : Integration (endpoint avec mocks RLM + ContextBuilder), E2E (endpoint avec vrai RLM mini-GDD)

**Dev Notes:**

**Architecture Patterns:**
- **Namespace cohérent** : `/api/v1/context/*` (cohérent avec autres routers `/api/v1/dialogues/*`)
- **Two-Phase Execution** : Phase 1 (RLM sélection) → Phase 2 (build_context_json) - pas de bypass
- **Fallback gracieux** : HTTP 200 avec fallback (pas d'erreur 500) → service optionnel, pas de casse si RLM indisponible

**Réutilisation Code:**
- **ContextBuilder** : Réutiliser `ContextBuilder` existant (pas de duplication)
- **Dependencies** : Utiliser `api/dependencies.py` pour injection (pattern FastAPI existant)

**References:** ADR-005 (RLM Context Selector - Backend API), FR5 (Endpoint API /select-context), NFR6 (Compatibility ContextBuilder préservé)

---

### Story 15.4: Toggle Auto Selection UI + Affichage Justifications

As a **utilisateur générant des dialogues**,
I want **un toggle "Auto Selection" dans le panneau de droite (à gauche du bouton "Générer") et voir les justifications des sélections automatiques**,
So that **je peux activer/désactiver la sélection automatique et comprendre pourquoi les éléments sont sélectionnés**.

**Acceptance Criteria:**

**Given** je suis sur l'écran de génération (panneau de droite)
**When** je regarde le panneau de contexte
**Then** je vois un toggle "Auto Selection" positionné à gauche du bouton "Générer"
**And** le toggle est désactivé par défaut (sélection manuelle préservée)

**Given** je active le toggle "Auto Selection"
**When** je lance une sélection de contexte
**Then** l'API `/api/v1/context/select-context` est appelée avec mes `user_instructions` et `hints`
**And** un indicateur de progression s'affiche ("Exploration du GDD... 2/50 appels outils")
**And** après sélection, les justifications s'affichent dans le panneau contexte (format compact)

**Given** les justifications sont affichées (format compact par défaut)
**When** je clique sur une justification
**Then** les détails s'affichent on-demand (raison + preuve + trace exploratoire)
**And** les justifications incluent icône visuelle du type de raison (hint_explicit, deduction_context_cosmologique, mentioned_explicitly, etc.)

**Given** je désactive le toggle "Auto Selection"
**When** je lance une sélection de contexte
**Then** la sélection manuelle existante est utilisée (comportement inchangé)
**And** aucune API RLM n'est appelée

**Technical Requirements:**
- Frontend : Composant `frontend/src/components/generation/ContextSelector.tsx` (modifier ou créer)
  - Ajouter toggle "Auto Selection" à gauche du bouton "Générer"
  - Toggle synchronisé avec `generationStore.autoSelection` (boolean)
  - Affichage justifications : Format compact par défaut, détails on-demand au clic
  - Icônes visuelles : Type de raison (hint_explicit → ✅, deduction_context_cosmologique → 🔍, mentioned_explicitly → 📝, etc.)
- Frontend : Zustand store `frontend/src/store/generationStore.ts` (étendre)
  - État `autoSelection: boolean` (défaut false)
  - Action `setAutoSelection(enabled: boolean)`
  - Action `selectContextAuto(request: SelectContextRequest)` pour appeler API `/api/v1/context/select-context`
- Frontend : API call `frontend/src/api/context.ts` (créer ou étendre)
  - Fonction `selectContextAuto(request: SelectContextRequest): Promise<SelectContextResponse>`
  - Appel POST `/api/v1/context/select-context`
  - Gestion erreurs : Fallback gracieux (afficher message non-bloquant si RLM indisponible)
- Frontend : Indicateur progression pendant sélection RLM
  - Affichage "Exploration du GDD... X/50 appels outils" (mise à jour temps réel via polling ou SSE si disponible)
- Tests : Unit (toggle synchronisé avec store), Integration (API call fonctionne), E2E (toggle activé → sélection auto → justifications affichées)

**Dev Notes:**

**Architecture Patterns:**
- **Toggle position** : À gauche du bouton "Générer" (panneau de droite) - spécification utilisateur
- **Format compact** : Justifications par défaut (pas de surcharge visuelle), détails on-demand (click pour expand)
- **Icônes visuelles** : Type de raison avec icône distincte (UX claire)

**Réutilisation Code:**
- **generationStore** : Étendre store existant (pas de créer nouveau)
- **ContextSelector** : Modifier composant existant ou créer nouveau selon architecture actuelle

**References:** ADR-005 (RLM Context Selector - Frontend UI), FR1 (Toggle Auto Selection UI), FR6 (Affichage Justifications UI), NFR2 (Usability justifications claires)

---

### Story 15.5: Mode Override + Lock

As a **utilisateur générant des dialogues**,
I want **pouvoir forcer/ajouter des éléments même en mode auto-selection et verrouiller des éléments critiques**,
So that **je garde le contrôle sur les sélections automatiques et je peux ajuster selon mes besoins**.

**Acceptance Criteria:**

**Given** j'ai activé le toggle "Auto Selection"
**When** la sélection automatique propose une sélection
**Then** je peux ajouter un élément manquant via mode override (bouton "Ajouter élément" ou similaire)
**And** l'élément ajouté est marqué comme "override" (inclus même si non sélectionné par RLM)

**Given** j'ai ajouté un élément via override
**When** je relance une sélection automatique (même `user_instructions`)
**Then** l'élément override est toujours inclus (préservé entre sélections)
**And** le RLM peut toujours sélectionner d'autres éléments (override n'empêche pas RLM)

**Given** un élément est critique (mentionné fréquemment)
**When** je verrouille l'élément (lock)
**Then** l'élément est toujours inclus dans toutes les sélections futures (même si toggle désactivé puis réactivé)
**And** l'élément est marqué visuellement comme "verrouillé" (icône 🔒)

**Given** je désactive le toggle "Auto Selection"
**When** je réactive le toggle
**Then** les éléments verrouillés (lock) sont toujours inclus
**And** les éléments override sont préservés (si toujours pertinents)

**Given** je déverrouille un élément (unlock)
**When** je relance une sélection automatique
**Then** l'élément n'est plus forcé inclus (RLM peut décider de l'inclure ou non)

**Technical Requirements:**
- Frontend : Extension `ContextSelector.tsx`
  - Bouton "Ajouter élément" en mode override (ajouter élément à sélection auto)
  - Bouton "Verrouiller" (lock) pour chaque élément sélectionné (forcer inclusion permanente)
  - Bouton "Déverrouiller" (unlock) pour éléments verrouillés
  - Affichage visuel : Icône 🔒 pour éléments verrouillés, badge "Override" pour éléments ajoutés manuellement
- Frontend : Zustand store `generationStore.ts` (étendre)
  - État `lockedElements: string[]` (IDs éléments verrouillés)
  - État `overrideElements: string[]` (IDs éléments ajoutés via override)
  - Action `lockElement(id: string)`
  - Action `unlockElement(id: string)`
  - Action `addOverrideElement(id: string)`
  - Action `removeOverrideElement(id: string)`
- Frontend : Intégration avec API `/api/v1/context/select-context`
  - Passer `lockedElements` et `overrideElements` dans `SelectContextRequest`
  - Backend doit toujours inclure locked/override elements (même si non sélectionnés par RLM)
- Backend : Extension `RLMContextSelector.select_context()`
  - Paramètre `locked_elements: Optional[List[str]]` (IDs éléments verrouillés)
  - Paramètre `override_elements: Optional[List[str]]` (IDs éléments ajoutés via override)
  - Toujours inclure locked/override elements dans `selected_elements` (mode full par défaut)
- Tests : Unit (lock/unlock/override state), Integration (API avec locked/override), E2E (verrouiller élément → toujours inclus)

**Dev Notes:**

**Architecture Patterns:**
- **Override vs Lock** : Override = ajout temporaire pour sélection actuelle, Lock = inclusion permanente pour toutes sélections futures
- **Persistance** : Locked elements persistés dans localStorage (ou backend si disponible) pour survie entre sessions
- **Backend respect** : RLM doit toujours inclure locked/override elements (contrainte forte, pas option)

**Réutilisation Code:**
- **generationStore** : Étendre store existant (pas de créer nouveau)
- **ContextSelector** : Modifier composant existant

**References:** ADR-005 (RLM Context Selector - Mode Override), FR7 (Mode Override), NFR2 (Usability contrôle utilisateur)

---

### Story 15.6: Fallback Gracieux + Tests E2E

As a **utilisateur générant des dialogues**,
I want **que le système gère gracieusement les échecs RLM (budget dépassé, erreur LLM, limite tool calls)**,
So that **je peux continuer à travailler même si la sélection automatique est indisponible**.

**Acceptance Criteria:**

**Given** le RLM échoue (budget exploration dépassé, erreur LLM, limite tool calls atteinte)
**When** l'API `/api/v1/context/select-context` est appelée
**Then** l'API retourne HTTP 200 (succès avec fallback, pas d'erreur 500)
**And** la réponse contient `selected_elements` avec hints uniquement (pas d'erreur)
**And** un message non-bloquant s'affiche "Sélection automatique indisponible, utilisation hints uniquement"

**Given** le RLM échoue avec erreur réseau (timeout, connexion perdue)
**When** l'API est appelée
**Then** l'API retourne fallback gracieux (hints uniquement, HTTP 200)
**And** un message s'affiche "Erreur réseau, utilisation hints uniquement"
**And** l'utilisateur peut réessayer ou basculer vers sélection manuelle

**Given** le RLM échoue mais l'utilisateur a des hints explicites
**When** le fallback gracieux est activé
**Then** les hints sont utilisés pour construire `context` (via `build_context_json()`)
**And** le `context` généré est utilisable (pas de contexte vide)
**And** l'utilisateur peut lancer une génération normale

**Given** le RLM échoue et l'utilisateur n'a pas de hints
**When** le fallback gracieux est activé
**Then** le `context` retourné est minimal (structure vide mais valide)
**And** un message s'affiche "Aucune sélection disponible, veuillez ajouter des hints ou utiliser sélection manuelle"
**And** l'utilisateur peut ajouter hints ou basculer vers sélection manuelle

**Technical Requirements:**
- Backend : Extension `RLMContextSelector.select_context()`
  - Try/except autour de toute la logique RLM
  - Si exception (budget dépassé, erreur LLM, limite tool calls) → retourner `ContextSelectionResult` avec hints uniquement (pas d'erreur)
  - Logging : Logger warning avec détails erreur (pour debug, pas exposé à utilisateur)
- Backend : Extension endpoint `/api/v1/context/select-context`
  - Try/except autour de `rlm_selector.select_context()`
  - Si exception → construire fallback `ContextSelectionResult` avec hints uniquement
  - Toujours retourner HTTP 200 (succès avec fallback)
  - Message fallback dans `trace` ("RLM unavailable, using hints only")
- Frontend : Gestion erreurs `ContextSelector.tsx`
  - Afficher message non-bloquant si fallback activé (toast ou banner, pas modal bloquante)
  - Permettre utilisateur de continuer (pas de blocage)
- Tests : Unit (RLM échoue → fallback gracieux), Integration (API avec erreur RLM → HTTP 200 fallback), E2E (workflow complet auto-selection → build_context → génération avec fallback)

**Dev Notes:**

**Architecture Patterns:**
- **Fallback gracieux** : Toujours retourner HTTP 200 avec fallback (pas d'erreur 500) → service optionnel, pas de casse
- **Hints comme fallback** : Si RLM indisponible, utiliser hints uniquement (sélection manuelle préservée)
- **Message non-bloquant** : Toast ou banner (pas modal) → utilisateur peut continuer

**Réutilisation Code:**
- **ContextBuilder** : `build_context_json()` fonctionne avec hints uniquement (pas de changement requis)

**References:** ADR-005 (RLM Context Selector - Fallback Gracieux), FR8 (Fallback Gracieux), NFR3 (Reliability fallback gracieux)

---

## Epic Summary

**Epic 15** implémente un service optionnel RLM (Recursive Language Models) pour sélection automatique intelligente de contexte GDD, réduisant friction utilisateur (10+ clics → 1 clic) et tokens contexte (20k+ → 12-15k Phase 1) sans perte pertinence. Le service est optionnel (toggle on/off), s'intègre avec `ContextBuilder` sans casser invariants, et gère gracieusement les échecs RLM (fallback hints uniquement).

**Stories** : 15.1 (Service RLM + Outils GDD), 15.2 (Extension ContextFieldManager), 15.3 (Endpoint API), 15.4 (Toggle UI + Justifications), 15.5 (Mode Override + Lock), 15.6 (Fallback Gracieux + Tests E2E).

**Valeur utilisateur** : Réduction friction sélection contexte, réduction tokens contexte sans perte pertinence, expliquabilité (justifications claires), contrôle utilisateur (override/lock).

**Priorité** : Nice-to-have (service optionnel, pas de dépendances bloquantes).
