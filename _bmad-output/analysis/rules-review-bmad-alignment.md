# Review des règles .mdc — Alignement avec process BMAD

**Date** : 2026-01-17  
**Objectif** : Aligner les règles `.cursor/rules/*.mdc` avec le process BMAD et réduire si possible

---

## 📊 État actuel

**19 fichiers de règles** dans `.cursor/rules/` :
- 16 règles techniques (toujours pertinentes)
- 3 règles organisationnelles (à réviser)

---

## ✅ Règles à CONSERVER (techniques, indépendantes de BMAD)

Ces règles sont toujours pertinentes et n'ont pas besoin de changements majeurs :

### Architecture & Code
- ✅ `python.mdc` - Conventions Python, architecture, Windows-first
- ✅ `backend_api.mdc` - Architecture FastAPI, SOLID, RESTful
- ✅ `frontend.mdc` - Architecture React, TypeScript, Vite
- ✅ `llm.mdc` - SDK OpenAI, GPT-5+, Responses API
- ✅ `structured_output.mdc` - Structured Output, garanties/non-garanties
- ✅ `unity_dialogue_generation.mdc` - Modèles Unity, champs techniques exclus

### Tests
- ✅ `tests.mdc` - Structure, framework pytest, bonnes pratiques
- ✅ `tests_patterns.mdc` - Patterns de mock, fixtures
- ✅ `tests_integration.mdc` - Tests intégration avec données réelles
- ✅ `frontend_testing.mdc` - Tests frontend, Vitest, Playwright

### Configuration & Données
- ✅ `gdd_paths.mdc` - Chemins GDD (lien symbolique, Vision.json)
- ✅ `field_classification.mdc` - Classification métadonnées vs contexte

### Opérationnel
- ✅ `workflow.mdc` - Commandes essentielles (`npm run dev`, `pytest`, etc.)
- ✅ `logging.mdc` - Système de logs complet (archivage, API, rotation)
- ✅ `debugging.mdc` - Niveaux de logs, flags de verbosité
- ✅ `prompt_structure.mdc` - Parsing prompt structuré (frontend)

---

## 🔄 Règles à RÉDUIRE/ALIGNER

### 1. `cursor_rules.mdc` ⚠️ À RÉDUIRE

**Problème** : Contient des instructions générales sur la création de règles qui peuvent être condensées.

**Recommandation** : Réduire à l'essentiel (format, quand créer, maintenance). Supprimer la redondance avec BMAD.

**Action** : Réduire de ~15 lignes à ~8 lignes.

### 2. `application_role.mdc` ✅ À CONSERVER (mais peut être réduit)

**Statut** : Utile pour contexte rapide, mais peut être condensé.

**Recommandation** : Garder mais réduire si possible. Référencer le README pour détails.

**Action** : Réduire de ~12 lignes à ~8 lignes.

### 3. `ui.mdc` ⚠️ À SUPPRIMER ou GARDER MINIMAL

**Problème** : UI PySide6 est dépréciée (déjà marquée comme telle).

**Recommandation** : 
- Option A : Supprimer complètement (si plus aucun usage)
- Option B : Garder une note minimale (1-2 lignes) : "UI PySide6 dépréciée, utiliser React"

**Action** : Vérifier usage dans codebase. Si zéro usage → supprimer. Sinon → réduire à note minimale.

---

## 🎯 Alignement avec BMAD

### Ce que BMAD gère (ne pas dupliquer dans les règles)

- ✅ **Planning** : PRD, Architecture, Epics, Stories (dans `_bmad-output/planning-artifacts/`)
- ✅ **Documentation détaillée** : Spécifications, architecture détaillée (dans `docs/` et `_bmad-output/`)
- ✅ **Workflow de développement** : Commands BMAD (`/bmad:...`) pour planification

### Ce que les règles .mdc doivent couvrir (guidance quotidienne)

- ✅ **Conventions de code** : Python, TypeScript, architecture
- ✅ **Patterns techniques** : Tests, mocks, structured output
- ✅ **Commandes pratiques** : `npm run dev`, `pytest`, etc.
- ✅ **Configuration** : Chemins, classification champs

**Conclusion** : Les règles `.mdc` sont complémentaires à BMAD (guidance quotidienne), pas redondantes.

---

## 📋 Plan d'action

### ✅ Phase 1 : Réduction rapide (TERMINÉ)
1. ✅ **Réduire `cursor_rules.mdc`** : Réduit de 15 → 8 lignes. Gardé format, quand créer, maintenance.
2. ✅ **Réduire `application_role.mdc`** : Réduit de 12 → 8 lignes. Gardé essence (rôle, architecture, données).

### ✅ Phase 2 : Décision `ui.mdc` (TERMINÉ)
3. ✅ **Vérifier usage PySide6** : Répertoire `ui/` n'existe pas → **réduit à note minimale** (1 ligne d'avertissement).

### Phase 3 : Vérification finale
4. **Valider cohérence** : Toutes les règles référencent-elles bien `README*.md` et `docs/` pour détails ?
5. **Vérifier redondances** : Aucune règle ne duplique-t-elle BMAD ?

---

## 📝 Recommandations finales

### Structure idéale des règles

1. **Règles générales** (`alwaysApply: true`) :
   - `workflow.mdc` - Commandes pratiques
   - `cursor_rules.mdc` (réduit) - Création/maintenance règles
   - `application_role.mdc` (réduit) - Rôle application
   - `python.mdc` - Conventions Python

2. **Règles spécifiques** (`alwaysApply: false`, `globs` définis) :
   - Architecture : `backend_api.mdc`, `frontend.mdc`
   - Domaine : `llm.mdc`, `unity_dialogue_generation.mdc`, `structured_output.mdc`
   - Tests : `tests.mdc`, `tests_patterns.mdc`, `tests_integration.mdc`, `frontend_testing.mdc`
   - Config : `gdd_paths.mdc`, `field_classification.mdc`
   - Opérationnel : `logging.mdc`, `debugging.mdc`, `prompt_structure.mdc`

### Principe de réduction

- **Conserver** : Patterns techniques, conventions de code, commandes pratiques
- **Réduire** : Instructions générales qui dupliquent BMAD ou docs détaillées
- **Supprimer** : Règles obsolètes (PySide6 si non utilisé)

---

## ✅ Validation

**Après réduction, les règles doivent** :
- ✅ Guider le développement quotidien (code, tests, commandes)
- ✅ Référencer `README*.md` et `docs/` pour détails
- ✅ Ne pas dupliquer la planification BMAD (PRD, Architecture, Stories)
- ✅ Rester concises (< 100 lignes par fichier, idéalement < 50)

**Total estimé après réduction** : 18 fichiers (ou 17 si `ui.mdc` supprimé)
