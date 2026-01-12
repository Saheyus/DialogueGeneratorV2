# Analyse de Refactoring - Janvier 2026

## Problèmes Structurels Identifiés

### 1. Imports Dépréciés Non Migrés (Priorité: Haute)
**Problème** : 54 fichiers utilisent encore les imports dépréciés (`from context_builder import`, `from prompt_engine import`, etc.) au lieu des nouveaux chemins dans `core/`.

**Impact** :
- Warnings de dépréciation à chaque import
- Risque de rupture lors de la suppression des wrappers (v2.0)
- Incohérence dans le codebase

**Fichiers concernés** :
- `services/context_field_validator.py`
- `tests/api/test_prompt_structured_parsing.py`
- `tests/api/test_character_extraction_tokens.py`
- `services/context_builder_factory.py`
- Et 50+ autres fichiers

---

### 2. Initialisation Complexe de ContextBuilder (Priorité: Moyenne)
**Problème** : `ContextBuilder.__init__` accepte 12+ dépendances optionnelles avec logique de création conditionnelle. La logique d'initialisation est dupliquée entre `ContextBuilderFactory` et `ContextBuilder.__init__`.

**Impact** :
- Code difficile à maintenir (initialisation conditionnelle)
- Duplication de logique entre Factory et constructeur
- Tests complexes (beaucoup de mocks nécessaires)

**Exemple** :
```python
# Dans ContextBuilder.__init__ (lignes 97-220)
if gdd_loader is None:
    from services.gdd_loader import GDDLoader
    self._gdd_loader = GDDLoader(...)
else:
    self._gdd_loader = gdd_loader

# Logique similaire dans ContextBuilderFactory.create()
```

---

### 3. Imports Conditionnels dans Services (Priorité: Moyenne)
**Problème** : Plusieurs services utilisent des try/except pour gérer les imports avec fallback, créant de la complexité inutile.

**Exemple** (`services/linked_selector.py`) :
```python
try:
    from ..context_builder import ContextBuilder
except ImportError:
    # Fallback complexe avec manipulation de sys.path
    from core.context.context_builder import ContextBuilder
```

**Impact** :
- Code verbeux et difficile à lire
- Risque d'erreurs silencieuses
- Incohérence avec le reste du codebase (qui utilise directement les imports `core/`)

---

### 4. Wrappers de Compatibilité Non Supprimés (Priorité: Basse)
**Problème** : Les wrappers à la racine (`context_builder.py`, `prompt_engine.py`, `llm_client.py`, `config_manager.py`) sont encore présents et génèrent des warnings.

**Impact** :
- Warnings à chaque utilisation
- Confusion pour les nouveaux développeurs
- Code mort qui sera supprimé en v2.0

**Note** : Ces wrappers sont nécessaires pour la compatibilité jusqu'à la migration complète, mais leur utilisation devrait être minimisée.

---

### 5. Services avec Responsabilités Floues (Priorité: Basse)
**Problème** : Certains services ont des responsabilités qui se chevauchent ou des noms peu clairs.

**Exemples** :
- `context_construction_service.py` vs `context_builder.py` (orchestration)
- `context_serializer/` avec 9 fichiers pour la sérialisation
- `context_field_manager.py` vs `context_field_validator.py` vs `context_field_detector.py`

**Impact** :
- Difficulté à trouver le bon service
- Risque de duplication
- Architecture moins claire

---

## Pistes de Refactoring

### Piste 1 : Migration Complète des Imports (Quick Win)
**Objectif** : Migrer tous les imports dépréciés vers les nouveaux chemins dans `core/`.

**Actions** :
1. Identifier tous les fichiers avec `grep`
2. Remplacer systématiquement :
   - `from context_builder import` → `from core.context.context_builder import`
   - `from prompt_engine import` → `from core.prompt.prompt_engine import`
   - `from llm_client import` → `from core.llm.llm_client import`
   - `from config_manager import` → Utiliser `ConfigurationService` ou `services.config_manager`
3. Exécuter les tests après chaque batch
4. Supprimer les imports conditionnels inutiles

**Avantages** :
- ✅ Élimine tous les warnings de dépréciation
- ✅ Prépare la suppression des wrappers (v2.0)
- ✅ Codebase plus cohérent
- ✅ Impact limité (changements mécaniques)

**Coûts** :
- ⚠️ 54 fichiers à modifier
- ⚠️ Risque de régression si imports mal gérés
- ⚠️ Tests à exécuter après chaque modification

**Estimation** : 4-6h (modifications + tests)

---

### Piste 2 : Simplification de l'Initialisation ContextBuilder (Architecture)
**Objectif** : Simplifier l'initialisation de `ContextBuilder` en utilisant uniquement la Factory et en supprimant la logique conditionnelle du constructeur.

**Actions** :
1. Rendre toutes les dépendances obligatoires dans `ContextBuilder.__init__` (supprimer les `if None`)
2. Centraliser toute la création dans `ContextBuilderFactory`
3. Supprimer la duplication entre Factory et constructeur
4. Créer un `ContextBuilderConfig` dataclass pour les paramètres
5. Mettre à jour tous les appels directs à `ContextBuilder()` pour utiliser la Factory

**Avantages** :
- ✅ Code plus simple et prévisible
- ✅ Suppression de la duplication
- ✅ Tests plus faciles (dépendances explicites)
- ✅ Meilleure séparation des responsabilités

**Coûts** :
- ⚠️ Refactoring plus profond (touche l'architecture)
- ⚠️ Tous les tests doivent être mis à jour
- ⚠️ Risque de régression si Factory mal utilisée

**Estimation** : 8-12h (refactoring + tests + validation)

---

### Piste 3 : Consolidation des Services Context (Architecture Majeure)
**Objectif** : Réorganiser les services liés au contexte pour clarifier les responsabilités et réduire la complexité.

**Actions** :
1. **Audit des services context** :
   - Identifier les responsabilités exactes de chaque service
   - Détecter les chevauchements et duplications
   - Créer un diagramme de dépendances

2. **Regroupement logique** :
   - Groupe "Field Management" : `context_field_manager`, `context_field_validator`, `context_field_detector` → Unifier ou clarifier les rôles
   - Groupe "Serialization" : `context_serializer/` (9 fichiers) → Vérifier si consolidation possible
   - Groupe "Construction" : `context_construction_service` vs `context_builder` → Clarifier l'orchestration

3. **Refactoring progressif** :
   - Créer des interfaces/classe abstraites si nécessaire
   - Déplacer la logique dupliquée
   - Supprimer les services obsolètes

**Avantages** :
- ✅ Architecture plus claire et maintenable
- ✅ Réduction de la complexité cognitive
- ✅ Meilleure testabilité
- ✅ Documentation implicite via structure

**Coûts** :
- ⚠️ Refactoring majeur (touche plusieurs services)
- ⚠️ Risque élevé de régression
- ⚠️ Nécessite une analyse approfondie avant action
- ⚠️ Tests complets à réécrire

**Estimation** : 20-30h (analyse + refactoring + tests)

---

## Évaluation des Pistes

### Piste 1 : Migration des Imports
- **Avantages** : 9/10 (impact immédiat, faible risque, prépare v2.0)
- **Coûts** : 2/10 (modifications mécaniques, tests simples)
- **Score global** : **7/10** (excellent rapport bénéfice/coût)

### Piste 2 : Simplification ContextBuilder
- **Avantages** : 8/10 (améliore la maintenabilité, réduit la complexité)
- **Coûts** : 5/10 (refactoring modéré, tests à mettre à jour)
- **Score global** : **6.5/10** (bon investissement)

### Piste 3 : Consolidation Services
- **Avantages** : 9/10 (améliore significativement l'architecture)
- **Coûts** : 8/10 (refactoring majeur, risque élevé)
- **Score global** : **5.5/10** (investissement important, à planifier)

---

## Recommandation

**Piste sélectionnée : Piste 1 (Migration Complète des Imports)**

**Justification** :
1. **Quick Win** : Impact immédiat avec effort modéré
2. **Préparation v2.0** : Nécessaire avant suppression des wrappers
3. **Faible risque** : Modifications mécaniques, tests existants suffisent
4. **Fondation** : Facilite les refactorings futurs (Pistes 2 et 3)

**Plan d'exécution** :
1. Phase 1 : Migration des imports dans `services/` (2h)
2. Phase 2 : Migration des imports dans `tests/` (2h)
3. Phase 3 : Migration des imports dans `scripts/` et autres (1h)
4. Phase 4 : Validation complète avec `pytest tests/` (1h)

**Total estimé** : 6h

**Prochaines étapes** (après Piste 1) :
- Piste 2 peut être entreprise avec moins de risques (imports déjà migrés)
- Piste 3 nécessite une analyse plus approfondie avant action
