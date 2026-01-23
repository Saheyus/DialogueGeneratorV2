# Diagnostic : Extraction de fiches - Comptage de tokens

## Problème identifié

Lors de l'extraction de la fiche "Akthar-Neth Amatru" (environ 5357 tokens bruts), le compteur de tokens ne bouge que de ~100 tokens au lieu des ~5300 tokens attendus.

## Cause racine

Le problème vient de la façon dont les `field_configs` sont utilisés dans l'extraction :

1. **Sans field_configs** (`field_configs = None`) : **5301 tokens** extraits (presque tout)
2. **Avec field_configs vides** (`field_configs = {}` ou `{'character': []}`) : **5301 tokens** extraits (presque tout)
3. **Avec field_configs limités** (`field_configs = {'character': ['Nom']}`) : **49 tokens** extraits (seulement le nom)

### Comportement actuel

- Si `field_configs` est `None` ou vide → Le backend utilise le fallback (`_get_prioritized_info`) qui extrait presque tous les champs
- Si `field_configs` contient des champs spécifiques → Seulement ces champs sont extraits

### Problème dans le frontend

Le frontend envoie toujours `field_configs` avec les champs essentiels ajoutés (ligne 319-323 de `GenerationPanel.tsx`). Si les champs essentiels ne sont pas chargés ou contiennent seulement quelques champs, alors seulement ces champs seront extraits.

## Solution

### Solution 1 : Vérifier les champs essentiels

Vérifier que les champs essentiels sont correctement chargés dans le store :

1. Ouvrir la console du navigateur
2. Vérifier `useContextConfigStore.getState().essentialFields`
3. Vérifier que `essentialFields.character` contient les champs attendus

### Solution 2 : Ne pas envoyer field_configs si vide

Modifier le frontend pour ne pas envoyer `field_configs` si tous les types d'éléments ont des listes vides (après ajout des champs essentiels).

### Solution 3 : Utiliser tous les champs par défaut

Modifier le backend pour que si `field_configs` contient des listes vides, utiliser le fallback (tous les champs) au lieu de n'extraire rien.

## Tests effectués

### Test d'extraction complète

```python
# Données brutes : 5357 tokens
# Extraction sans field_configs : 5301 tokens (99%)
# Extraction avec tous les champs configurés : 2370 tokens (44%)
```

### Test de comportement field_configs

| field_configs | Tokens extraits | Comportement |
|---------------|-----------------|--------------|
| `None` | 5301 | Fallback (presque tout) |
| `{}` | 5301 | Fallback (presque tout) |
| `{'character': []}` | 5301 | Fallback (presque tout) |
| `{'character': ['Nom']}` | 49 | Seulement le nom |
| `{'character': ['Nom', 'Résumé']}` | 49 | Seulement le nom (Résumé invalide) |

## Recommandation

**Solution recommandée** : Modifier le backend pour que si `field_configs[element_type]` est une liste vide, utiliser le fallback (tous les champs) au lieu de passer au fallback uniquement si `fields_for_element` est `None`.

Actuellement, le code vérifie `if fields_for_element:` à la ligne 779 de `context_builder.py`, ce qui fait que si `fields_for_element` est une liste vide `[]`, on passe au fallback. C'est correct, mais le problème est que si `field_configs` contient des champs spécifiques (même peu), alors seulement ces champs sont extraits.

## Fichiers à modifier

1. `context_builder.py` : Améliorer la logique de fallback pour les listes vides
2. `frontend/src/components/generation/GenerationPanel.tsx` : Ne pas envoyer `field_configs` si tous les types sont vides
3. `frontend/src/store/contextConfigStore.ts` : S'assurer que les champs essentiels sont correctement chargés
