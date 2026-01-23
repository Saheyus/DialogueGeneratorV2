# Project Context Analysis

### Requirements Overview

**Functional Requirements (V1.0 MVP):**

DialogueGenerator est un éditeur de dialogues narratifs IA-assisté en **production active** nécessitant des améliorations critiques pour atteindre la production-readiness. Les exigences fonctionnelles se structurent autour de 8 features prioritaires :

1. **Progress Feedback** (Must-have)
   - Modal centrée pendant génération LLM
   - Streaming visible (sortie LLM en temps réel)
   - Étapes de progression + logs détaillés
   - Actions : Interrompre / Réduire

2. **Presets système** (Must-have)
   - Sauvegarde configurations (personnages, lieux, région, instructions)
   - Chargement rapide (dropdown)
   - Métadonnées : nom, icône emoji, aperçu
   - Stockage : fichiers JSON locaux + API backend

3. **Graph Editor opérationnel** (Blocage critique)
   - Correction bugs DisplayName vs stableID
   - Connexion nœuds fonctionnelle (création/édition liens parent/enfant)
   - Visualisation zoom/pan/sélection
   - Auto-layout pour structures complexes

4. **Génération "Continue"** (Cohérence narrative)
   - Générer suite à partir d'un nœud/choix existant
   - Auto-connexion dans graphe (targetNode mis à jour)
   - Cohérence contextuelle maintenue
   - Option : variantes multiples sur un point

5. **Validation structurelle** (Non-LLM)
   - Références cassées, nœuds vides, START manquant
   - Orphans/unreachable nodes
   - Cycles signalés (warning, pas bloquant)
   - Erreurs cliquables pour correction rapide

6. **Export Unity fiable**
   - Format JSON strict (modèles Pydantic)
   - Sauvegarde/chargement dialogue
   - Reproductibilité (pipeline prod)
   - Validation schéma avant export

7. **Cost governance minimal**
   - Estimation coût avant génération
   - Logs coût par génération
   - Plafond budget configurable (soft/hard)
   - Transparence token usage

8. **Aide évaluation LLM** (À la demande)
   - Feedback utilisateur instrumenté (save/regenerate/delete)
   - Évaluation LLM optionnelle sur nœud/sous-arbre
   - Pas de QA globale systématique (scope MVP)

**Non-Functional Requirements:**

- **Performance** : 
  - Graph editor réactif pour centaines de nœuds (virtualisation)
  - Streaming LLM fluide (pas de gel UI)
  - Auto-save 2min sans perturber workflow

- **Quality** :
  - Taux d'acceptation >80% (dialogues enregistrés/générés)
  - Structured outputs garantis (JSON Schema validation)
  - Tests >80% couverture code critique

- **Efficiency** :
  - Objectif business : dialogue complet en ≤1H
  - Cold start réduit (presets = 1 clic)
  - Workflow itératif fluide

- **Cost Management** :
  - Budgets LLM maîtrisés (estimation + plafonds)
  - Optimisation tokens (prompt caching, context selection)
  - Transparence coûts (dashboard usage)

- **Security** :
  - JWT auth (access 15min + refresh 7j)
  - RBAC 3 rôles (admin/writer/viewer)
  - HTTPS production, validation inputs

- **Maintainability** :
  - Architecture modulaire (React/FastAPI/Services)
  - 18 Cursor rules documentent patterns
  - Tests automatisés (pytest + Vitest)
  - Logs structurés persistants

**Scale & Complexity:**

- **Primary domain** : Full-stack web app (React + FastAPI + LLM integration + Unity export)
- **Complexity level** : **Medium-High**
  - Architecture existante mature (pas de greenfield)
  - V1.0 = améliorations UX critiques + robustesse
  - Graph management complexe (centaines nœuds)
  - LLM orchestration sophistiquée (GPT-5.2 + streaming + reasoning)
  - GDD volumineux (500+ pages, context management multi-couches)
- **Estimated architectural components** : 8-10 systèmes principaux
- **Target scale** : 1M+ lignes dialogue d'ici 2028 (Disco Elysium+ scale)

### Technical Constraints & Dependencies

**Existant (à préserver) :**

- **Architecture React + FastAPI** : Migration web terminée, production-ready
- **GDD externe** : Pipeline Notion intacte (`main.py`/`filter.py` non modifiés)
- **Lien symbolique GDD** : `data/GDD_categories/` pointe vers JSON Notion
- **Format Unity** : JSON custom strict (pas de champs techniques exposés à IA)
- **Windows-first** : PathLib, encodage UTF-8, pas d'hypothèses POSIX
- **Cursor rules** : 18 fichiers `.mdc` définissent patterns (backbone comportement)

**Dépendances clés :**

- **OpenAI API** : GPT-5.2 avec Responses API (reasoning + structured outputs)
  - Contrainte : `reasoning.effort` incompatible avec `temperature`
  - Format requêtes différent Chat Completions (voir `.cursor/rules/llm.mdc`)
- **React Flow** : Éditeur graphe (version 12, SSR/SSG support)
- **Pydantic** : Modèles Unity + validation schémas
- **Zustand** : State management (léger, performant)
- **FastAPI** : Async/await, validation Pydantic, OpenAPI auto

**Limitations identifiées :**

- **Graph editor bugs** : DisplayName vs stableID (blocage critique à corriger V1.0)
- **Pas de feedback génération** : UI "gel" pendant appel LLM (UX critique)
- **Cold start friction** : 10+ clics pour premier dialogue (presets résolvent)
- **Panneau Détails étroit** : 340px insuffisant pour feedback génération → modal recommandée
- **Onglets contexte séquentiels** : Friction navigation (amélioration V1.5, hors scope V1.0)

**Décisions architecturales héritées :**

- Services métier dans `services/` (réutilisables API + tests)
- Injection dépendances via `api/container.py` (ServiceContainer)
- Structured outputs pour garantir format JSON (pas de parsing fragile)
- Logs persistants JSON avec archivage automatique (`data/logs/`)
- Tests unitaires + intégration (pytest) + E2E (Playwright)

### Cross-Cutting Concerns Identified

**1. LLM Orchestration Layer**
- Multi-provider abstraction (MVP: OpenAI uniquement, V2.0: Anthropic fallback)
- Retry logic avec backoff exponentiel
- Streaming avec gestion interruptions
- Structured outputs (JSON Schema validation)
- Cost tracking et quotas

**2. State Management Layer**
- Auto-save 2min (V1.0, upgrade de "nice-to-have")
- Undo/Redo avec Command + Memento patterns
- Sync état entre composants (Zustand)
- Persistence (localStorage + backend)

**3. Validation & Quality Layer**
- **Structure** (non-LLM) : Références, nœuds vides, cycles
- **Quality** (LLM) : Cohérence, caractérisation, agentivité (à la demande)
- **Schema** : Pydantic models + JSON Schema
- **Lore** : Checker GDD (V1.5+)

**4. Graph Management**
- React Flow intégration (visualisation, édition)
- Auto-layout algorithmes (dagre.js)
- Virtualisation pour performance (centaines nœuds)
- Validation topology (orphans, unreachable)

**5. Context Intelligence**
- Field classification (metadata vs narratif)
- Selection intelligente (pertinence, tokens)
- Multi-couches (système, contexte, instructions)
- Estimation tokens/coût avant génération

**6. Export & Integration**
- Unity JSON format (strict, validé)
- Git service (commit automatique optionnel)
- Reproductibilité exports
- Backward compatibility

**7. Monitoring & Observability**
- Logs structurés JSON persistants
- API consultation logs (`/api/v1/logs`)
- Nettoyage automatique (30j rétention)
- Health checks (backend/GDD)

**8. Security & Access Control**
- JWT auth (access + refresh tokens)
- RBAC 3 rôles (admin/writer/viewer)
- Rate limiting API
- Input validation (Pydantic)

### Architectural Implications Summary

Le projet DialogueGenerator présente une **architecture mature en brownfield** nécessitant des **améliorations ciblées** pour la V1.0 MVP. Les décisions architecturales devront :

1. **Préserver l'existant** : Architecture React+FastAPI production-ready
2. **Corriger bugs critiques** : Graph editor (DisplayName/stableID)
3. **Améliorer UX** : Progress feedback (streaming modal) + Presets (cold start)
4. **Renforcer robustesse** : Validation structurelle + Cost governance
5. **Respecter contraintes** : GDD externe, Unity format, Windows-first, 18 Cursor rules

Les 8 cross-cutting concerns identifiés structureront les décisions techniques à venir.

---
