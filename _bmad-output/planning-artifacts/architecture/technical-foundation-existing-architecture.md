# Technical Foundation (Existing Architecture)

### Architecture Overview

DialogueGenerator est un **projet brownfield production-ready** avec une architecture mature établie. Les décisions techniques documentées ci-dessous constituent la **baseline architecturale** sur laquelle les features V1.0 s'appuieront.

**Source de vérité comportementale :** 18 Cursor rules (`.cursor/rules/*.mdc`) définissent les patterns, conventions et contraintes pour les agents IA développeurs.

### Stack Decisions (Already Made)

#### Frontend Architecture

**Technology Stack:**
- **React 18** + **TypeScript** + **Vite**
  - Rationale : Migration web terminée, production-ready, HMR performant
  - Pattern : Component-based SPA, composants réutilisables modulaires
- **Zustand** (State management)
  - Rationale : Léger, performant, moins verbeux que Redux
  - Usage : Auth, état global, pas de prop drilling
- **React Flow 12** (Graph editor)
  - Rationale : SSR/SSG support, dark mode natif, reactive flows
  - Usage : Visualisation/édition graphes de dialogues (centaines nœuds)
- **Vitest** + **React Testing Library** (Tests)
  - Rationale : Fast, compatible Vite, patterns modernes
  - Coverage : Tests unitaires composants + hooks

**Project Structure:**
```
frontend/
├── src/
│   ├── api/          # API client (axios + intercepteurs)
│   ├── components/   # Composants React (layout, auth, generation)
│   ├── hooks/        # Custom hooks
│   ├── store/        # Zustand stores
│   ├── types/        # TypeScript types (alignés Pydantic backend)
│   └── main.tsx      # Entry point
```

**Key Patterns:**
- API client modulaire par domaine (`auth.ts`, `dialogues.ts`, `interactions.ts`)
- Routes protégées avec `ProtectedRoute`
- JWT en localStorage (access_token), refresh automatique
- Proxy API en dev (`vite.config.ts`), build production dans `dist/`

#### Backend Architecture

**Technology Stack:**
- **FastAPI** (Python 3.10+)
  - Rationale : Async/await natif, validation Pydantic, OpenAPI auto
  - Pattern : RESTful API, versioning `/api/v1/`
- **Pydantic** (Validation + models)
  - Rationale : Type safety, validation schémas, génération JSON Schema
  - Usage : API DTOs, Unity dialogue models, structured outputs LLM
- **pytest** + **pytest-asyncio** (Tests)
  - Rationale : Standard Python, async support, fixtures puissantes
  - Coverage : >80% code critique (services, API)

**Project Structure:**
```
api/
├── routers/          # Routes HTTP (dialogues, config, logs, etc.)
├── schemas/          # Pydantic DTOs (request/response)
├── services/         # Adaptateurs API vers services métier
├── dependencies.py   # Injection dépendances FastAPI
├── container.py      # ServiceContainer (cycle de vie services)
└── main.py           # Entry point

services/             # Logique métier réutilisable
├── context/          # ContextBuilder, FieldValidator
├── prompt/           # PromptEngine, estimation tokens
├── llm/              # LLMClient (OpenAI, structured outputs)
├── json_renderer/    # UnityJsonRenderer
└── configuration/    # ConfigurationService
```

**Key Patterns:**
- **SOLID** : Routers = routes uniquement, Services API = adaptation, Services métier = logique pure
- **Dependency Injection** : Via `api/container.py` (ServiceContainer), pas de singletons globaux
- **Service-oriented** : Logique dans `services/` (réutilisable API + tests)
- **Structured outputs** : Pydantic models → JSON Schema → LLM validation garantie

#### LLM Integration

**Technology Stack:**
- **Multi-Provider Support** (V1.0)
  - **OpenAI API** (GPT-5.2)
    - API : **Responses API** (`client.responses.create`) pour GPT-5.2
    - Contrainte : `reasoning.effort` incompatible avec `temperature`
    - Format : `input` (vs `messages`), `max_output_tokens`, tools plat
  - **Mistral API** (Small Creative) 🆕
    - API : **Chat Completions API** (`client.chat.completions.create`)
    - SDK : `mistralai` Python package
    - Streaming : Support natif via `stream=True`
    - Format : `messages` (role/content), `response_format` pour structured outputs
- **Structured Outputs**
  - Pattern : Pydantic → `model_json_schema()` → `response_model`
  - Garanties : Structure JSON, types corrects, conformité schéma
  - Non-garanties : Logique métier, formats spécifiques (instructions prompt)
  - Multi-provider : Normalisation JSON Schema (OpenAI + Mistral)

**Key Patterns:**
- Abstraction `IGenerator` (interface) : Support multi-provider via factory pattern
- Factory : `LLMFactory.create(provider, model)` retourne client approprié
- Clients : `OpenAIClient` (existant), `MistralClient` 🆕 (nouveau)
- Retry logic avec backoff exponentiel (par provider)
- Streaming avec gestion interruptions (V1.0, format SSE uniforme)
- Cost tracking et quotas (V1.0, différencié par provider)

#### Data & Integration

**GDD (Game Design Document):**
- Source : Pipeline Notion externe (`main.py`/`filter.py` non modifiés)
- Chemin : Lien symbolique `data/GDD_categories/` + `import/Bible_Narrative/Vision.json`
- Contrainte : GDD externe, aucune modification pipeline

**Unity Export:**
- Format : JSON custom strict (modèles Pydantic `models/dialogue_structure/`)
- Contrainte : Pas de champs techniques exposés à IA (`targetNode`, `nextNode`, etc.)
- Pattern : `enrich_with_ids()` ajoute champs techniques après génération

**Logs & Monitoring:**
- Format : JSON structuré persistant (`data/logs/logs_YYYY-MM-DD.json`)
- Archivage : Rotation quotidienne + intra-jour (>100MB), 30j rétention
- API : `/api/v1/logs` (recherche, stats, nettoyage)

#### Testing Strategy

**Backend:**
- **pytest** : Tests unitaires + intégration, `TestClient` FastAPI (pas de serveur)
- **Mocks** : OpenAI, fichiers GDD, variables env (sauf `tmp_path`)
- **Coverage** : >80% code critique (services, API)
- **Commande** : `pytest tests/` ou `python -m pytest tests/`

**Frontend:**
- **Vitest** : Tests unitaires composants + hooks
- **React Testing Library** : Tests composants isolés
- **Playwright** : Tests E2E (auth, navigation, génération)
- **Commande** : `npm run test:frontend` (build + lint + tests)

#### Development Workflow

**Commands:**
- **Dev** : `npm run dev` (backend 4243 + frontend 3000 auto)
- **Dev debug** : `npm run dev:debug` (console DEBUG)
- **Dev clean** : `npm run dev:clean` (nettoie cache Vite)
- **Tests** : `pytest tests/` (backend) + `npm run test:frontend` (frontend)
- **Status** : `npm run dev:status` (health checks)

**Constraints Inherited:**
- **Windows-first** : PathLib, encodage UTF-8, pas d'hypothèses POSIX
- **Cursor rules** : 18 fichiers `.mdc` = backbone comportemental agents IA

### Architectural Patterns Established

#### 1. Service Container Pattern (Dependency Injection)

**Location:** `api/container.py`

**Pattern:**
```python
class ServiceContainer:
    def __init__(self):
        self._context_builder = None
        self._prompt_engine = None
        # Lazy initialization, singleton lifecycle
    
    def get_context_builder(self) -> ContextBuilder:
        if not self._context_builder:
            self._context_builder = ContextBuilder()
        return self._context_builder
```

**Usage:** `api/dependencies.py` → `get_context_builder()` → injecté dans routers

**Rationale:** Cycle de vie contrôlé, testabilité (mocks), pas de singletons globaux

#### 2. Structured Outputs Pattern (LLM)

**Location:** `services/llm/`, `models/dialogue_structure/`

**Pattern:**
1. Définir modèle Pydantic (`UnityDialogueNode`)
2. Générer JSON Schema (`model_json_schema()`)
3. Passer comme `response_model` au LLM client
4. Validation garantie par OpenAI (structure + types)

**Guarantees:** Structure JSON, types corrects, conformité schéma  
**Non-Guarantees:** Logique métier → instructions prompt explicites

**Rationale:** Pas de parsing fragile, validation côté LLM, robustesse

#### 3. Command + Memento Pattern (Undo/Redo)

**Status:** Prévu V1.0 (state management layer)

**Pattern:**
- **Command** : Encapsule opérations (AddNode, DeleteNode, etc.)
- **Memento** : Capture état avant opération
- **Invoker** : Gère historique commandes (undo/redo)

**Rationale:** Undo/Redo pour graph editor (centaines nœuds)

#### 4. Multi-Layer Prompt Composition

**Location:** `services/prompt/prompt_engine.py`

**Pattern:**
- **Layer 1** : System prompt (format Unity, règles RPG)
- **Layer 2** : Context (personnages, lieux, objets sélectionnés)
- **Layer 3** : Instructions scène (user input)

**Rationale:** Context management sophistiqué, évite "lore dropping", priorité claire

### Constraints & Technical Debt

**Known Bugs (Blockers V1.0):**
- **Graph editor** : DisplayName vs stableID (correction critique)
- **Pas de feedback génération** : UI "gel" pendant LLM (modal streaming V1.0)

**Technical Debt:**
- Pas d'auto-save (upgrade V1.0 : 2min intervals)
- Pas de presets (cold start friction, résolu V1.0)
- Validation structurelle basique (upgrade V1.0 : orphans, cycles)

**Limitations:**
- Multi-provider supporté (OpenAI + Mistral V1.0) ✅
- Pas de collaboration temps réel (V2.0+)
- Panneau Détails étroit (340px, contraint pour feedback)

---
