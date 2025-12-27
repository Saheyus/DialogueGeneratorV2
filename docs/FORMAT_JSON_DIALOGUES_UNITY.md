**Note** : Ce document est une recommandation architecturale datée du 2025-12-25.
Il reflète l'état du système de dialogue et les décisions prises à cette date.

# Format JSON des dialogues Alteir - Recommandation pour outil d'auteur

## Structure de base

Le format est un **tableau de nœuds à la racine** :

```json
[
  {
    "id": "NODE_ID",
    "speaker": "CHARACTER_ID",
    "line": "Texte du dialogue",
    "nextNode": "NEXT_NODE_ID",
    "choices": [...],
    ...
  }
]
```

## Modèle de données complet

### DialogueNodeJson (nœud de dialogue)

- **id** (string, requis) : Identifiant unique du nœud
- **speaker** (string, optionnel) : ID du personnage qui parle
- **line** (string, optionnel) : Texte du dialogue
- **nextNode** (string, optionnel) : ID du nœud suivant (si pas de choix)
- **choices** (DialogueChoiceJson[], optionnel) : Liste des choix disponibles
- **cutsceneMode** (bool, défaut: false) : Active le mode cutscene
- **cutsceneImageId** (string, optionnel) : ID de l'image cutscene
- **cutsceneId** (string, optionnel) : ID de la cutscene à lancer
- **exitCutsceneMode** (bool, défaut: false) : Sort du mode cutscene
- **test** (string, optionnel) : Format "Attribute+SkillId:DD" (ex: "Puissance+Rhétorique:5")
- **successNode** / **failureNode** (string, optionnel) : Redirection selon résultat du test
- **isLongRest** (bool, défaut: false) : Déclenche un repos long
- **startState** (int, défaut: 0) : État de démarrage pour dialogues multi-entrées
- **consequences** (DialogueConsequencesJson, optionnel) : Flags narratifs à activer

### DialogueChoiceJson (choix)

- **text** (string, requis) : Texte du choix
- **targetNode** (string, requis) : ID du nœud cible
- **traitRequirements** (TraitRequirementData[], optionnel) : Exigences de traits
- **influenceThreshold** (int, défaut: 0) : Seuil d'influence requis
- **allowInfluenceForcing** (bool, défaut: false) : Permet le forcing avec influence
- **influenceDelta** / **respectDelta** (int, défaut: 0) : Modifications de stats
- **test** (string, optionnel) : Format "Attribute+SkillId:DD" pour test d'attribut au niveau du choix
- **testSuccessNode** / **testFailureNode** (string, optionnel) : Redirection selon test
- **condition** (string, optionnel) : Format "FLAG_NAME" ou "NOT FLAG_NAME" pour afficher/masquer

### DialogueConsequencesJson (conséquences)

- **flag** (string, requis) : Nom du flag narratif
- **description** (string, optionnel) : Description pour debug

## Normalisation automatique (Unity)

Unity normalise automatiquement les fichiers JSON :

- Supprime les champs vides (`""`, `null`)
- Supprime les booléens à `false` et nombres à `0` (valeurs par défaut)
- Supprime les tableaux/objets vides
- Conserve toujours `id` et `targetNode` même s'ils sont vides

## Validation (Unity)

Unity valide :

- Syntaxe JSON valide
- **Structure : tableau à la racine uniquement** `[{"id": "...", ...}, ...]`
- IDs uniques
- Références de nœuds valides (`nextNode`, `targetNode`, `successNode`, etc.)
- Au moins un nœud présent

**Note importante** : Le format wrapper `{"nodes": [...]}` n'est **PAS accepté** et sera rejeté avec une erreur.

## Recommandation architecturale

### Option 1 : Format final normalisé (recommandé)

L'outil produit directement le format final (tableau de nœuds normalisé).

**Avantages :**
- Simplicité : pas de conversion côté Unity
- Cohérence : format identique à ce qui est utilisé
- Validation directe : l'outil peut valider avant export
- Moins de couches = moins de risques d'erreurs

**Inconvénients :**
- L'outil doit gérer la normalisation (champs vides, etc.)

### Option 2 : Format intermédiaire enrichi

L'outil produit un format enrichi (métadonnées, commentaires, format libre), Unity convertit.

**Avantages :**
- Flexibilité : métadonnées non-JSON possibles
- Séparation des responsabilités : l'outil génère, Unity normalise

**Inconvénients :**
- Complexité supplémentaire
- Risque de perte d'informations lors de la conversion
- Maintenance de deux formats

### Recommandation finale

**Option 1** : l'outil doit produire le format final normalisé.

## Ce que l'outil doit fournir

### Format de sortie

- **Format** : tableau JSON `[{...}, {...}]`
- **Normalisation minimale** :
  - Ne pas inclure les champs à valeurs par défaut (`false`, `0`, `""`, `null`)
  - Conserver `id` et `targetNode` même s'ils sont vides
- **Validation avant export** :
  - IDs uniques
  - Références de nœuds valides
  - Au moins un nœud présent
- **Pretty-print** : JSON indenté (2 espaces recommandé)

### Exemple de sortie attendue

```json
[
  {
    "id": "START",
    "speaker": "URESAÏR",
    "line": "Bienvenue...",
    "choices": [
      {
        "text": "Continuer",
        "targetNode": "NEXT_NODE"
      }
    ]
  },
  {
    "id": "NEXT_NODE",
    "speaker": "URESAÏR",
    "line": "Suite du dialogue",
    "nextNode": "END"
  }
]
```

## Notes importantes

- **Format unique** : Seul le format tableau `[{...}, {...}]` est accepté. Le format wrapper `{"nodes": [...]}` est explicitement rejeté.
- **Normalisation** : Unity normalise automatiquement les fichiers JSON lors de l'import, mais l'outil devrait produire un format déjà normalisé pour éviter les diffs inutiles.
- **Validation** : L'outil doit valider les références de nœuds avant export pour éviter les erreurs runtime.

## Source de vérité : JSON Schema Unity

Le format exact est défini par le **JSON Schema Unity** disponible dans `docs/JsonDocUnity/Documentation/dialogue-format.schema.json`.

Ce schéma est la source de vérité pour :
- La structure exacte des nœuds et choix
- Les patterns de validation (IDs SCREAMING_SNAKE_CASE, format des tests, etc.)
- Les contraintes (maxItems pour choices, champs requis, etc.)

**Utilisation** :
- Les tests de contrat (`tests/services/test_unity_schema_contract.py`) valident automatiquement les exports contre ce schéma
- Le schéma n'est disponible qu'en développement (pas en production)
- Si le schéma est absent, l'outil fonctionne normalement mais sans validation stricte (graceful degradation)

**Version du schéma** : Voir `dialogue-format.schema.json` pour la version actuelle (actuellement `1.0.0`).



