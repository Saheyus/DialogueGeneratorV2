# Problème de Parsing Structuré du Prompt

## Résumé

Le prompt brut contient bien SECTION 2A avec le personnage, mais le parsing structuré ne l'affiche pas correctement.

## Analyse

### 1. Bug d'apostrophe (CORRIGÉ)

**Problème** : Le `ContextBuilder` ne trouvait pas les personnages à cause d'une différence d'apostrophe :
- GDD utilise apostrophe typographique : `'` (U+2019)
- Code cherchait avec apostrophe droite : `'` (U+0027)

**Solution** : Ajout de `_normalize_string_for_matching()` qui normalise les apostrophes avant comparaison.

### 2. Test API utilisait le mauvais format (CORRIGÉ)

**Problème** : Le test utilisait `context_selections.characters` alors que le schéma Pydantic attend `characters_full` ou `characters_excerpt`.

**Solution** : Correction du test pour utiliser `characters_full`.

### 3. Format du contexte vs Parsing structuré (PROBLÈME IDENTIFIÉ)

**Format réel du prompt** (mode "default") :
```
### SECTION 2A. CONTEXTE GDD

**CONTEXTE GÉNÉRAL DE LA SCÈNE**
--- CHARACTERS ---
Nom: Akthar-Neth Amatru, l'Exégète
Alias: Grand-Père
Occupation: Interprète des textes
...
```

**Format attendu par le parser** (mode "narrative") :
```
### SECTION 2A. CONTEXTE GDD

**CONTEXTE GÉNÉRAL DE LA SCÈNE**
--- CHARACTERS ---
--- IDENTITÉ ---
Nom: Akthar-Neth Amatru, l'Exégète
Alias: Grand-Père
...

--- CARACTÉRISATION ---
Désir Principal: ...
...
```

**Problème** : 
- Le mode "default" génère un format linéaire sans sections `--- IDENTITÉ ---`
- Le parser frontend (`parseSubSections`) cherchait des sections de niveau 3 (`--- IDENTITÉ ---`, `--- CARACTÉRISATION ---`) après `--- CHARACTERS ---`
- Quand il n'en trouvait pas, il ignorait le contenu de `--- CHARACTERS ---` (ligne 172-175 faisait `continue` sans créer de section)

**Solution** : 
- **CORRIGÉ** : Modification du parser pour toujours créer une section avec le contenu, même s'il n'y a pas de sections de niveau 3. Le contenu est maintenant préservé dans une section `CHARACTERS` avec le contenu direct.
- Utiliser `organization_mode: "narrative"` dans l'API pour générer le format avec sections (optionnel, mais recommandé pour une meilleure structure)

## Tests

### Tests créés

1. `tests/api/test_prompt_raw_verification.py` : Vérifie que SECTION 2A est présente dans le prompt brut
2. `tests/api/test_prompt_structured_parsing.py` : Vérifie que le format est compatible avec le parsing structuré
3. `tests/frontend/test_prompt_parsing_integration.test.ts` : Test frontend avec vraies données (à créer)

### Tests existants

- `frontend/src/hooks/usePromptPreview.test.ts` : Tests unitaires du parser avec données mockées

## Recommandations

1. **Court terme** : Utiliser `organization_mode: "narrative"` par défaut dans l'API pour générer le format attendu par le parser
2. **Long terme** : Adapter le parser pour gérer les deux formats (default et narrative)
