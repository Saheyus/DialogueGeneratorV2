# Project Structure & Boundaries

### Complete Project Directory Structure

Cette section documente la structure complète de DialogueGenerator, incluant l'architecture existante (brownfield) et les nouveaux fichiers nécessaires pour V1.0 MVP.

**Légende:**
- ✅ : Fichiers/dossiers existants
- 🆕 : Nouveaux fichiers nécessaires pour V1.0
- 📁 : Dossiers critiques

```
f:\Projets\Notion_Scrapper\DialogueGenerator\
│
├── 📁 api/                                    ✅ Backend API (FastAPI)
│   ├── routers/                               ✅ HTTP routes
│   │   ├── auth.py                            ✅ Authentication endpoints
│   │   ├── config.py                          ✅ Configuration management
│   │   ├── dialogues.py                       ✅ Dialogue CRUD
│   │   ├── gdd.py                             ✅ GDD data access
│   │   ├── interactions.py                    ✅ Interaction management
│   │   ├── logs.py                            ✅ Log access API
│   │   ├── streaming.py                       🆕 SSE streaming generation (ADR-001)
│   │   ├── presets.py                         🆕 Preset CRUD (ADR-002)
│   │   └── cost.py                            🆕 Cost tracking/governance (ID-003)
│   ├── schemas/                               ✅ Pydantic DTOs
│   │   ├── auth.py                            ✅ Auth request/response models
│   │   ├── dialogue.py                        ✅ Dialogue DTOs
│   │   ├── config.py                          ✅ Configuration DTOs
│   │   ├── streaming.py                       🆕 SSE event schemas
│   │   ├── preset.py                          🆕 Preset DTOs
│   │   └── cost.py                            🆕 Cost tracking DTOs
│   ├── services/                              ✅ API service adapters
│   │   ├── dialogue_service.py                ✅ Dialogue operations
│   │   ├── gdd_service.py                     ✅ GDD data access
│   │   ├── streaming_service.py               🆕 Streaming generation coordination
│   │   ├── preset_service.py                  🆕 Preset management
│   │   └── cost_service.py                    🆕 Cost tracking/governance
│   ├── middleware/                            ✅ FastAPI middleware
│   │   ├── auth.py                            ✅ JWT validation
│   │   ├── logging.py                         ✅ Request logging
│   │   └── cost_governance.py                 🆕 Pre-LLM cost check (ID-003)
│   ├── dependencies.py                        ✅ Dependency injection
│   ├── container.py                           ✅ ServiceContainer (lifecycle)
│   ├── main.py                                ✅ FastAPI app entry point
│   └── exceptions.py                          ✅ Custom exceptions
│
├── 📁 services/                               ✅ Business logic (reusable)
│   ├── llm/                                   ✅ LLM integration
│   │   ├── llm_client.py                      ✅ OpenAI client (existant)
│   │   ├── mistral_client.py                  🆕 Mistral client (ADR-004)
│   │   ├── llm_factory.py                     🆕 Factory pattern (provider selection)
│   │   ├── interfaces.py                      ✅ IGenerator interface
│   │   └── structured_output.py               ✅ JSON Schema validation
```


**Document d'architecture complet avec arbre de structure détaillé ci-dessus.**

Les sections Architectural Boundaries, Requirements Mapping, Integration Points, et Workflow Integration ont été couvertes dans les sections précédentes :
- **Boundaries** : Voir "V1.0 Architectural Decisions" et "Implementation Patterns"
- **Requirements → Structure** : Chaque feature V1.0 est mappée dans l'arbre (marquée 🆕)
- **Integration Points** : Couverts dans "Integration Patterns" et "Technical Foundation"
- **Workflows** : Documentés dans Cursor rules (workflow.mdc) et scripts/

---
