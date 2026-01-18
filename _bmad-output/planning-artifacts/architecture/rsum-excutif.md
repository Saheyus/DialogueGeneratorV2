# Résumé Exécutif

### Vue d'Ensemble

**DialogueGenerator** est un éditeur de dialogues narratifs IA-assisté en **production active** (brownfield) nécessitant des améliorations critiques pour atteindre la production-readiness. Ce document d'architecture définit les décisions techniques pour la **V1.0 MVP**, incluant 7 features prioritaires et le support multi-provider LLM.

### Contexte Projet

- **Type** : Application brownfield (architecture existante mature)
- **Stack** : React 18 + FastAPI + Python 3.10+ + OpenAI GPT-5.2 + Mistral Small Creative
- **Objectif V1.0** : Améliorer UX critique (feedback génération, cold start) + robustesse (validation, cost governance)
- **Contraintes** : GDD externe (non modifiable), format Unity strict, Windows-first, 18 Cursor rules

### Décisions Architecturales Clés (V1.0)

**4 Architecture Decision Records (ADRs) :**
1. **ADR-001** : Progress Feedback Modal (streaming SSE) - Résout UI "gel" pendant génération
2. **ADR-002** : Presets système - Réduit cold start friction (10+ clics → 1 clic)
3. **ADR-003** : Graph Editor Fixes (stableID) - Corrige bug critique corruption graphe
4. **ADR-004** : Multi-Provider LLM (Mistral) - Flexibilité + réduction dépendance OpenAI

**5 Implementation Decisions (IDs) :**
1. **ID-001** : Auto-save (2min, LWW) - Sauvegarde automatique dialogues
2. **ID-002** : Validation cycles (warning non-bloquant) - Détection cycles graphe
3. **ID-003** : Cost governance (90% soft + 100% hard) - Protection financière
4. **ID-004** : Streaming cleanup (10s timeout) - Interruption propre génération
5. **ID-005** : Preset validation (warning + "Charger quand même") - Gestion références obsolètes

### Architecture Technique

**Backend (FastAPI) :**
- **API REST** : `/api/v1/*` avec JWT auth, RBAC 3 rôles
- **Services** : Logique métier réutilisable (`services/`), abstraction LLM multi-provider
- **Patterns** : ServiceContainer (DI), Structured Outputs (Pydantic), SSE streaming
- **Tests** : pytest >80% coverage, TestClient FastAPI

**Frontend (React 18) :**
- **Stack** : TypeScript + Vite + Zustand + React Flow 12
- **Components** : Organisation par domaine (auth, generation, graph, presets)
- **State** : Zustand stores (immutable updates), hooks custom
- **Tests** : Vitest + React Testing Library + Playwright E2E

**LLM Integration :**
- **Providers** : OpenAI GPT-5.2 (Responses API) + Mistral Small Creative (Chat Completions)
- **Abstraction** : Interface `IGenerator` + Factory pattern (sélection utilisateur)
- **Streaming** : SSE uniforme (tous providers), structured outputs (JSON Schema)

### Structure Projet

**~40 nouveaux fichiers V1.0** identifiés :
- **Backend** : 3 routers (streaming, presets, cost), 3 services, 2 validators, Mistral client
- **Frontend** : 8 composants (modal, presets, model selector), 5 hooks, 3 stores
- **Tests** : 12 fichiers tests (API, services, components, E2E)

**Organisation** : Domain-based (frontend), Feature-based (backend), Mirror structure (tests)

### Patterns d'Implémentation

**5 Patterns V1.0 documentés :**
1. **SSE Streaming** : Format strict `data: {...}\n\n`, interruption graceful
2. **Preset Storage** : UUID naming, validation lazy, warning modal
3. **Cost Tracking** : Middleware pre-LLM, 90% soft + 100% hard, différencié par provider
4. **Auto-save** : 2min interval, suspend pendant génération, LWW strategy
5. **Multi-Provider Abstraction** : Factory pattern, interface IGenerator, normalisation uniforme

**13 Conflict Points** identifiés avec solutions (naming, structure, communication, process)

### Validation & Readiness

**✅ Architecture validée et prête pour implémentation :**
- **Cohérence** : Toutes décisions compatibles, patterns alignés, structure supporte architecture
- **Couverture** : 7/9 features V1.0 couvertes (2 deferred V2.0 : Undo/Redo, Git auto-commit)
- **Complétude** : 4 ADRs + 5 IDs documentés, ~40 fichiers identifiés, patterns exhaustifs
- **Gaps** : Aucun gap critique (gaps mineurs post-MVP documentés)

### Prochaines Étapes

**Séquence d'implémentation recommandée :**
1. ADR-003 (Graph Fix) - Correction bug critique
2. ADR-001 (Progress Modal) - Amélioration UX critique
3. ADR-002 (Presets) - Réduction friction cold start
4. ADR-004 (Multi-Provider) - Flexibilité LLM
5. IDs (Auto-save, Cost, Validation) - Robustesse

**Document finalisé le :** 2026-01-14  
**Version :** V1.0 MVP  
**Status :** ✅ Prêt pour implémentation

---
