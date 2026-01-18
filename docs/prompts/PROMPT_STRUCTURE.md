# Format du Prompt - Spécification

## Vue d'ensemble

Le prompt généré par le système suit une structure hiérarchique stricte avec des marqueurs explicites. Cette structure garantit une source de vérité unique entre le prompt brut et le mode structuré, et facilite le parsing côté frontend.

## Structure hiérarchique

Le prompt suit une hiérarchie à 4 niveaux :

1. **Niveau 1** : Sections principales (`### SECTION 2A. CONTEXTE GDD`)
2. **Niveau 2** : Catégories (`--- CHARACTERS ---`, `--- LOCATIONS ---`)
3. **Niveau 3** : Marqueurs d'éléments (`--- PNJ 1 ---`, `--- LIEU 2 ---`)
4. **Niveau 4** : Sections d'éléments (`--- IDENTITÉ ---`, `--- CARACTÉRISATION ---`) [mode narrative uniquement]

## Marqueurs d'éléments

Chaque élément dans une catégorie est précédé d'un marqueur explicite :

- `--- PNJ 1 ---` : Premier personnage
- `--- PNJ 2 ---` : Deuxième personnage
- `--- LIEU 1 ---` : Premier lieu
- `--- LIEU 2 ---` : Deuxième lieu
- `--- OBJET 1 ---` : Premier objet
- `--- ESPÈCE 1 ---` : Première espèce
- `--- COMMUNAUTÉ 1 ---` : Première communauté
- `--- QUÊTE 1 ---` : Première quête

### Format

**Format** : `--- {LABEL} {NUMÉRO} ---`

**Règles** :
- Les numéros commencent à 1 et sont séquentiels par catégorie
- Le marqueur est sur une ligne complète
- Le contenu de l'élément suit immédiatement après le marqueur
- Les labels sont en majuscules (PNJ, LIEU, OBJET, etc.)

### Mapping des catégories vers les labels

| Catégorie backend | Label marqueur |
|-------------------|----------------|
| `characters`      | `PNJ`          |
| `locations`       | `LIEU`         |
| `items`           | `OBJET`        |
| `species`         | `ESPÈCE`       |
| `communities`     | `COMMUNAUTÉ`   |
| `quests`          | `QUÊTE`        |

## Exemple complet

### Mode "default" (sans sections de niveau 4)

```
--- CHARACTERS ---
--- PNJ 1 ---
Nom: Akthar-Neth Amatru, l'Exégète
Alias: Grand-Père, Le Nœud Éternel
Occupation/Rôle: Interprète des textes, Parfait
Espèce: Van'Doei
--- PNJ 2 ---
Nom: Autre personnage
Alias: Autre alias
```

### Mode "narrative" (avec sections de niveau 4)

```
--- CHARACTERS ---
--- PNJ 1 ---
--- IDENTITÉ ---
Nom: Akthar-Neth Amatru, l'Exégète
Alias: Grand-Père, Le Nœud Éternel
--- CARACTÉRISATION ---
Désir Principal: Accomplir le Dernier Rituel
Faiblesse: Obsession terrifiante du Dernier Rituel
--- PNJ 2 ---
--- IDENTITÉ ---
Nom: Autre personnage
```

## Rétrocompatibilité

Les prompts sans marqueurs explicites sont toujours supportés via un fallback :
- Si aucun marqueur `--- PNJ X ---` n'est détecté, le parser utilise la détection par pattern `Nom:`
- Cela permet une transition en douceur sans casser les prompts existants

## Implémentation

### Backend

Les marqueurs sont ajoutés dans `context_builder.py`, méthode `build_context_with_custom_fields()`, avant chaque appel à `organize_context()`.

### Frontend

Le parsing des marqueurs est effectué dans `frontend/src/hooks/usePromptPreview.ts`, fonction `parseSubSections()`. Le parser détecte d'abord les marqueurs explicites, puis utilise le fallback si aucun marqueur n'est trouvé.

## Bénéfices

- **Source de vérité unique** : Brut et structuré partagent la même structure
- **Robustesse** : Plus de patterns fragiles, marqueurs explicites
- **Maintenabilité** : Format documenté et testé
- **Utilité LLM** : Les marqueurs aident le modèle à comprendre la structure
- **SOLID** : Séparation des responsabilités, contrat explicite

## Références

- Code backend : `context_builder.py` (ligne ~597)
- Code frontend : `frontend/src/hooks/usePromptPreview.ts` (ligne ~173)
- Service d'organisation : `services/context_organizer.py`
