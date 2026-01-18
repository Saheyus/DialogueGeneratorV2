# Validation des Champs GDD

## Vue d'ensemble

Le système de validation garantit que `context_config.json` ne référence que des champs réellement présents dans les données GDD. Cela évite les erreurs silencieuses où des champs sont référencés mais n'existent pas dans les données source.

## Architecture

### Source de vérité : Détection automatique

Les champs disponibles sont détectés automatiquement depuis les données GDD réelles via `ContextFieldDetector`. Cette détection :

- Parcourt toutes les fiches GDD pour chaque type d'élément (character, location, etc.)
- Extrait tous les chemins de champs (y compris imbriqués)
- Calcule la fréquence de chaque champ
- Identifie les métadonnées (champs avant "Introduction")
- Catégorise les champs (identity, characterization, voice, background, mechanics)

**Fichier**: `services/context_field_detector.py`

### Validation : Comparaison config vs détection

`ContextFieldValidator` compare `context_config.json` avec les champs détectés et :

- Identifie les champs référencés mais absents
- Propose des corrections automatiques (mapping de champs similaires)
- Génère des rapports de validation

**Fichier**: `services/context_field_validator.py`

## Validation au démarrage

L'application valide automatiquement la configuration au démarrage dans `api/main.py::lifespan()` :

- **Mode développement** : Affiche des warnings pour les champs invalides
- **Mode production** : Fail-fast si des erreurs critiques sont détectées

```python
# Dans api/main.py::lifespan()
validator = ContextFieldValidator(context_builder)
validation_results = validator.validate_all_configs(context_config)

if validation_results.has_critical_errors():
    # En production, bloquer le démarrage
    raise ValueError("Configuration invalide")
```

## Filtrage automatique à l'exécution

Même si des champs invalides sont référencés, ils sont automatiquement filtrés :

1. **Dans `context_builder.py`** :
   - `_filter_fields_by_condition_flags()` valide l'existence des champs avant de filtrer par `condition_flag`
   - Les champs invalides sont ignorés avec un log warning

2. **Dans `services/context_organizer.py`** :
   - `organize_context()` vérifie que chaque champ peut être extrait des données
   - Les champs non trouvés sont ignorés silencieusement

## API d'inspection

### Endpoint : `/api/v1/config/context-fields/{element_type}`

Retourne tous les champs détectés avec des flags de validation :

- `is_in_config` : Si le champ est référencé dans `context_config.json`
- `is_valid` : Si le champ existe réellement (toujours `true` pour les champs détectés)

**Exemple de réponse** :
```json
{
  "element_type": "character",
  "fields": {
    "Nom": {
      "path": "Nom",
      "label": "Nom",
      "is_in_config": true,
      "is_valid": true,
      "frequency": 1.0
    },
    "Dialogue Type.Registre de langage du personnage": {
      "path": "Dialogue Type.Registre de langage du personnage",
      "is_in_config": true,
      "is_valid": false,
      "frequency": 0.0
    }
  }
}
```

### Endpoint : `/api/v1/config/context-fields/validate`

Retourne un rapport de validation complet pour tous les types d'éléments.

**Exemple de réponse** :
```json
{
  "summary": {
    "total_element_types": 5,
    "total_errors": 3,
    "total_warnings": 2
  },
  "results": {
    "character": {
      "total_fields_in_config": 15,
      "total_fields_detected": 108,
      "valid_fields_count": 12,
      "invalid_fields_count": 3,
      "invalid_fields": [
        {
          "path": "Dialogue Type.Registre de langage du personnage",
          "issue_type": "similar_found",
          "severity": "warning",
          "message": "Champ 'Dialogue Type.Registre de langage du personnage' non trouvé dans les données GDD. Suggestion: 'Registre de langage du personnage'",
          "suggested_path": "Registre de langage du personnage"
        }
      ]
    }
  },
  "text_report": "=== RAPPORT DE VALIDATION...\n"
}
```

## Script CLI de validation

### Utilisation

```bash
# Validation complète
python scripts/validate_fields.py

# Rapport détaillé
python scripts/validate_fields.py --report

# Suggestions de corrections
python scripts/validate_fields.py --fix

# Valider un seul type d'élément
python scripts/validate_fields.py --element-type character
```

### Exemples de sortie

**Validation réussie** :
```
=== RÉSUMÉ DE VALIDATION ===
✅ character: 15/15 valides
✅ location: 8/8 valides
✅ item: 6/6 valides

Total: 0 erreur(s), 0 avertissement(s)

✅ Tous les champs sont valides!
```

**Problèmes détectés** :
```
=== RÉSUMÉ DE VALIDATION ===
❌ character: 12/15 valides
   3 erreur(s), 0 avertissement(s)
✅ location: 8/8 valides

Total: 3 erreur(s), 0 avertissement(s)

⚠️  Des problèmes ont été détectés. Utilisez --report pour plus de détails.
```

## Workflow de maintenance

### Quand les données GDD changent

1. Les champs sont automatiquement re-détectés au prochain démarrage
2. La validation au démarrage signale les champs obsolètes
3. Utiliser `scripts/validate_fields.py --fix` pour voir les suggestions

### Quand context_config.json est modifié

1. La validation au démarrage vérifie immédiatement
2. Les champs invalides sont automatiquement filtrés à l'exécution
3. Utiliser l'API `/context-fields/validate` pour un rapport détaillé

### Correction manuelle

1. Identifier les champs invalides via le script ou l'API
2. Vérifier les suggestions automatiques
3. Mettre à jour `context_config.json` avec les vrais chemins
4. Vérifier aussi `services/context_organizer.py::ESSENTIAL_CONTEXT_FIELDS` si nécessaire

## Exemples de corrections

### Avant (invalide)
```json
{
  "path": "Dialogue Type.Registre de langage du personnage",
  "label": "Style de dialogue"
}
```

### Après (valide)
```json
{
  "path": "Registre de langage du personnage",
  "label": "Style de dialogue"
}
```

Ou, si le champ n'existe pas du tout :
```json
{
  "path": "Langage",
  "label": "Langage"
}
```

## Bonnes pratiques

1. **Toujours valider après modification de `context_config.json`** :
   ```bash
   python scripts/validate_fields.py
   ```

2. **Utiliser l'API pour lister les champs réels** :
   ```bash
   curl http://localhost:4243/api/v1/config/context-fields/character
   ```

3. **Vérifier les suggestions automatiques** :
   ```bash
   python scripts/validate_fields.py --fix
   ```

4. **En développement, surveiller les warnings au démarrage** pour détecter les problèmes tôt

5. **En production, la validation fail-fast garantit** qu'aucun champ invalide n'est utilisé

## Dépannage

### "Champ X non trouvé"

1. Vérifier que le champ existe dans les données GDD :
   ```bash
   python scripts/validate_fields.py --element-type character
   ```

2. Vérifier l'orthographe exacte (sensible à la casse)

3. Vérifier la structure imbriquée (ex: `Background.Relations` et non `BackgroundRelations`)

### "Suggestion proposée mais ne fonctionne pas"

1. Vérifier la fréquence du champ suggéré (peut être très rare)
2. Vérifier que le champ suggéré contient bien les données attendues
3. Considérer utiliser un champ plus fréquent si disponible
