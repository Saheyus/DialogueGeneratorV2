# Technology Stack Analysis

## Part 1: Frontend (Web Application)

| Category | Technology | Version | Justification |
|----------|-----------|---------|---------------|
| **Framework** | React | 18.2.0 | UI library principale |
| **Language** | TypeScript | 5.2.0 | Typage statique pour sécurité et maintenabilité |
| **Build Tool** | Vite | 4.4.0 | Bundler moderne et rapide |
| **State Management** | Zustand | 4.4.0 | State management léger et performant |
| **Routing** | React Router | 6.20.0 | Navigation SPA |
| **Data Fetching** | React Query (TanStack) | 5.90.12 | Gestion des requêtes API avec cache |
| **Forms** | React Hook Form | 7.69.0 | Gestion de formulaires performante |
| **Validation** | Zod | 4.2.1 | Validation de schémas TypeScript-first |
| **HTTP Client** | Axios | 1.6.0 | Client HTTP pour appels API |
| **Graph Visualization** | ReactFlow | 11.11.4 | Éditeur de graphes pour dialogues |
| **Layout** | Dagre | 0.8.5 | Algorithmes de layout pour graphes |
| **Testing** | Vitest | 4.0.16 | Framework de tests unitaires |
| **E2E Testing** | Playwright | 1.57.0 | Tests end-to-end |
| **Linting** | ESLint | 8.45.0 | Linter JavaScript/TypeScript |

**Architecture Pattern:** Component-based architecture avec séparation claire entre:
- Components (UI réutilisables)
- Pages (routes)
- Store (state management Zustand)
- API client (couche d'abstraction API)
- Hooks (logique réutilisable)

**Entry Points:**
- `src/main.tsx` - Point d'entrée React
- `index.html` - HTML de base

---

## Part 2: Backend API

| Category | Technology | Version | Justification |
|----------|-----------|---------|---------------|
| **Framework** | FastAPI | 0.104.0+ | Framework web moderne et performant |
| **Language** | Python | 3.10+ | Langage backend principal |
| **ASGI Server** | Uvicorn | 0.24.0+ | Serveur ASGI haute performance |
| **Validation** | Pydantic | 2.0+ | Validation de données et modèles |
| **LLM Integration** | OpenAI SDK | 1.15+ | Intégration avec API OpenAI |
| **Token Counting** | Tiktoken | 0.4+ | Comptage de tokens pour LLM |
| **Templating** | Jinja2 | 3.0+ | Génération de prompts |
| **Authentication** | Python-JOSE | 3.3.0+ | JWT tokens |
| **Password Hashing** | Passlib + Bcrypt | 1.7.4+ / 4.0.0+ | Hachage sécurisé des mots de passe |
| **Rate Limiting** | SlowAPI | 0.1.9+ | Limitation de débit |
| **Monitoring** | Prometheus | 6.0.0+ | Métriques et observabilité |
| **Error Tracking** | Sentry | 1.32.0+ | Suivi des erreurs en production |
| **Retry Logic** | Tenacity | 8.2.0+ | Logique de retry pour appels externes |
| **Circuit Breaker** | PyBreaker | 1.0.0+ | Protection contre pannes en cascade |
| **Caching** | Cachetools | 5.3.0+ | Cache en mémoire |
| **HTTP Client** | HTTPX | 0.25.0+ | Client HTTP async pour Notion API |
| **Schema Validation** | JSONSchema | 4.0.0+ | Validation JSON Schema pour Unity |
| **Testing** | Pytest | 7.0+ | Framework de tests Python |
| **Test Coverage** | Pytest-cov | 2.12+ | Couverture de code |
| **Test Mocking** | Pytest-mock | 3.6+ | Mocks pour tests |

**Architecture Pattern:** Layered architecture avec:
- **Routers** (`api/routers/`) - Endpoints REST
- **Schemas** (`api/schemas/`) - Modèles Pydantic pour validation
- **Services** (`api/services/`, `services/`) - Logique métier
- **Middleware** (`api/middleware/`) - Cross-cutting concerns (logging, rate limiting, CORS)
- **Dependencies** (`api/dependencies.py`) - Injection de dépendances FastAPI
- **Container** (`api/container.py`) - ServiceContainer pour gestion du cycle de vie

**Entry Points:**
- `api/main.py` - Point d'entrée FastAPI

---

## Shared Technologies

| Category | Technology | Usage |
|----------|-----------|-------|
| **Package Management** | npm (Frontend) / pip (Backend) | Gestion des dépendances |
| **Version Control** | Git | Contrôle de version |
| **Environment Config** | .env files | Configuration par environnement |
| **Documentation** | Markdown | Documentation technique |

---

## Architecture Patterns Summary

### Frontend
- **Pattern:** Component-based SPA avec state management centralisé
- **Data Flow:** Unidirectional (React Query → Zustand → Components)
- **Styling:** CSS modules / inline styles (à vérifier)

### Backend
- **Pattern:** RESTful API avec architecture en couches
- **Data Flow:** Request → Router → Service → Repository/External API → Response
- **Dependency Injection:** ServiceContainer pattern pour gestion des dépendances

### Integration
- **Communication:** REST API (Frontend → Backend via `/api/*`)
- **Protocol:** HTTP/HTTPS
- **Data Format:** JSON
- **Authentication:** JWT tokens (probablement, à vérifier dans auth.py)
