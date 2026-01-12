# Guide de Migration : Refactoring 2026

Ce document décrit les changements structurels effectués lors du refactoring de consolidation progressive (Janvier 2026).

## Changements Importants

### Imports Déplacés

Les modules principaux ont été déplacés vers `core/` :

- `from context_builder import` → `from core.context.context_builder import`
- `from prompt_engine import` → `from core.prompt.prompt_engine import`
- `from llm_client import` → `from core.llm.llm_client import`

**Exemple** :
```python
# Ancien (déprécié, génère un DeprecationWarning)
from context_builder import ContextBuilder

# Nouveau (recommandé)
from core.context.context_builder import ContextBuilder
```

### Configuration

- `config_manager` (racine) est déprécié
- Utiliser `services.configuration_service.ConfigurationService` pour la gestion de configuration
- `services.config_manager` (variables d'environnement via Pydantic Settings) reste valide et complémentaire

**Exemple** :
```python
# Ancien (déprécié)
from config_manager import load_llm_config
config = load_llm_config()

# Nouveau (recommandé)
from services.configuration_service import ConfigurationService
config_service = ConfigurationService()
config = config_service.get_llm_config()
```

### Injection de Dépendances

- Les singletons globaux ont été supprimés
- Tous les services sont maintenant gérés par `ServiceContainer` dans `app.state`
- Les fonctions `get_*` dans `api/dependencies.py` utilisent exclusivement le container

**Impact** : Les fonctions `get_*` lèvent maintenant `RuntimeError` si le container n'est pas initialisé (au lieu de fallback vers singleton).

### Tests

- Fichiers temporaires déplacés vers `tests/manual/`
- Tous les tests automatiques restent dans `tests/`
- Les scripts de debug manuels sont maintenant dans `tests/manual/`

## Compatibilité

Des wrappers de compatibilité sont disponibles jusqu'en version 2.0 :
- `context_builder.py` (racine) → redirige vers `core.context.context_builder`
- `prompt_engine.py` (racine) → redirige vers `core.prompt.prompt_engine`
- `llm_client.py` (racine) → redirige vers `core.llm.llm_client`
- `config_manager.py` (racine) → wrapper avec redirection vers `ConfigurationService`

Ces wrappers émettent des `DeprecationWarning` pour faciliter la migration progressive.

## Migration Progressive

### Étape 1 : Mettre à jour les imports critiques

Les fichiers suivants ont déjà été mis à jour (source de vérité) :
- `api/container.py`
- `api/dependencies.py`
- `factories/llm_factory.py`
- `services/context_builder_factory.py`
- `api/routers/*.py`

### Étape 2 : Mettre à jour les autres imports

Pour les autres fichiers, vous pouvez :
1. Laisser les imports existants (warnings mais fonctionnel)
2. Mettre à jour progressivement vers les nouveaux chemins

### Étape 3 : Supprimer les wrappers (version 2.0)

Les wrappers de compatibilité seront supprimés dans la version 2.0. Planifier la migration complète avant cette version.

## Vérification

Pour vérifier que votre code utilise les nouveaux imports :

```bash
# Chercher les imports dépréciés
grep -r "from context_builder import" --exclude-dir=node_modules --exclude-dir=.git
grep -r "from prompt_engine import" --exclude-dir=node_modules --exclude-dir=.git
grep -r "from llm_client import" --exclude-dir=node_modules --exclude-dir=.git
```

Les fichiers dans `api/`, `factories/`, et `services/context_builder_factory.py` devraient déjà utiliser les nouveaux imports.

## Questions Fréquentes

**Q: Mon code fonctionne encore avec les anciens imports ?**
R: Oui, les wrappers de compatibilité maintiennent la compatibilité. Vous verrez des warnings mais le code fonctionne.

**Q: Quand dois-je migrer ?**
R: Progressivement. Les nouveaux fichiers devraient utiliser les nouveaux imports. Les anciens fichiers peuvent être migrés lors de modifications.

**Q: Les tests passent-ils toujours ?**
R: Oui, tous les tests existants continuent de fonctionner grâce aux wrappers de compatibilité.

**Q: Que se passe-t-il si j'utilise get_* sans Request ?**
R: Les fonctions `get_*` nécessitent maintenant un `Request` pour accéder au container. Si vous appelez ces fonctions hors contexte FastAPI, vous devez créer un container manuellement ou utiliser les services directement.
