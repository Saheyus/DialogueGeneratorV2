# Story 0.10: Tests avec 4 résultats (échec critique, échec, réussite, réussite critique)

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **auteur de dialogues**,
I want **quand une réponse d'un PJ inclut un "test", avoir 4 réponses possibles du PNJ (échec critique, échec, réussite, réussite critique) au lieu d'une seule**,
So that **je peux créer des dialogues plus nuancés avec des résultats de test variés selon le niveau de réussite/échec**.

## Acceptance Criteria

1. **Given** je crée un choix de joueur avec un attribut `test` (ex: "Raison+Diplomatie:8")
   **When** je génère le nœud suivant avec l'IA
   **Then** l'IA génère 4 réponses possibles du PNJ : échec critique, échec, réussite, réussite critique
   **And** chaque réponse est connectée à un nœud distinct dans le graphe

2. **Given** un choix avec `test` dans le graphe
   **When** je visualise le nœud de test dans l'éditeur
   **Then** je vois 4 handles de sortie distincts : échec critique (rouge foncé), échec (rouge), réussite (vert), réussite critique (vert foncé)
   **And** chaque handle est étiqueté clairement

3. **Given** je génère un nœud suivant depuis un choix avec test
   **When** la génération est complète
   **Then** 4 nœuds sont créés automatiquement (un pour chaque résultat)
   **And** les connexions sont établies correctement entre le choix et les 4 nœuds de résultat

4. **Given** j'exporte un dialogue vers Unity JSON
   **When** un choix contient un test avec 4 résultats
   **Then** le JSON Unity contient les 4 champs de nœuds cibles : `testCriticalFailureNode`, `testFailureNode`, `testSuccessNode`, `testCriticalSuccessNode` (pour les choix) ou `criticalFailureNode`, `failureNode`, `successNode`, `criticalSuccessNode` (pour les nœuds)
   **And** le schéma JSON est valide selon les spécifications Unity (`docs/resources/JsonDocUnity/Documentation/dialogue-format.schema.json`)
   **And** la logique de fallback est respectée : `testCriticalSuccessNode` → `testSuccessNode`, `testCriticalFailureNode` → `testFailureNode`

5. **Given** je charge un dialogue Unity JSON existant
   **When** un choix contient les 4 résultats de test
   **Then** le graphe affiche correctement les 4 connexions
   **And** chaque nœud de résultat est visible et accessible

## Tasks / Subtasks

- [ ] Task 1: Étendre schémas TypeScript pour 4 résultats de test (AC: #1, #2, #4, #5)
  - [ ] Modifier `frontend/src/types/api.ts` : Ajouter `testCriticalFailureNode?`, `testCriticalSuccessNode?` à `UnityDialogueChoice`
  - [ ] Modifier `frontend/src/schemas/nodeEditorSchema.ts` : Étendre `testNodeDataSchema` avec 4 champs optionnels
  - [ ] Vérifier que `[key: string]: unknown` permet extension sans casser types existants
  - [ ] Tests unitaires : Validation schéma avec 2 résultats (rétrocompatibilité) et 4 résultats

- [ ] Task 2: Étendre modèles Pydantic Python pour 4 résultats (AC: #1, #4)
  - [ ] Modifier `models/dialogue_structure/unity_dialogue_node.py` : Ajouter `testCriticalFailureNode?`, `testCriticalSuccessNode?` à `UnityDialogueChoiceContent`
  - [ ] Vérifier rétrocompatibilité : Champs optionnels, anciens JSON avec 2 résultats fonctionnent toujours
  - [ ] Tests unitaires : Sérialisation/désérialisation avec 2 et 4 résultats

- [ ] Task 3: Mettre à jour TestNode React pour afficher 4 handles (AC: #2)
  - [ ] Modifier `frontend/src/components/graph/nodes/TestNode.tsx`
  - [ ] Ajouter 4 handles de sortie : `critical-failure` (rouge foncé #C0392B), `failure` (rouge #E74C3C), `success` (vert #27AE60), `critical-success` (vert foncé #229954)
  - [ ] Positionner handles : critical-failure (gauche 12.5%), failure (gauche 37.5%), success (droite 37.5%), critical-success (droite 12.5%)
  - [ ] Mettre à jour labels : Afficher "Échec critique", "Échec", "Réussite", "Réussite critique" dans footer
  - [ ] Tests visuels : Vérifier affichage 4 handles avec couleurs distinctes

- [ ] Task 4: Mettre à jour génération IA pour créer 4 réponses (AC: #1, #3)
  - [ ] Modifier `services/unity_dialogue_generation_service.py` : Détecter choix avec `test`
  - [ ] Quand choix a `test`, modifier prompt pour demander 4 réponses au lieu d'une
  - [ ] Structure réponse IA : `{critical_failure: "...", failure: "...", success: "...", critical_success: "..."}`
  - [ ] Créer 4 nœuds automatiquement après génération (un par résultat)
  - [ ] Établir connexions : `testCriticalFailureNode`, `testFailureNode`, `testSuccessNode`, `testCriticalSuccessNode` (ordre : critical-failure, failure, success, critical-success)
  - [ ] Tests unitaires : Génération avec test crée 4 nœuds et connexions

- [ ] Task 5: Mettre à jour GraphView pour charger 4 résultats (AC: #5)
  - [ ] Modifier `frontend/src/components/generation/GraphView.tsx` : Fonction `unityJsonToGraph()`
  - [ ] Détecter `testCriticalFailureNode`, `testCriticalSuccessNode` en plus de `testFailureNode`, `testSuccessNode`
  - [ ] Créer edges pour les 4 résultats avec labels et couleurs appropriés
  - [ ] Tests unitaires : Chargement JSON avec 4 résultats affiche 4 connexions

- [ ] Task 6: Mettre à jour ChoiceEditor pour éditer 4 résultats (AC: #2)
  - [ ] Modifier `frontend/src/components/graph/ChoiceEditor.tsx`
  - [ ] Ajouter champs input pour `testCriticalFailureNode`, `testCriticalSuccessNode` (si test présent)
  - [ ] Afficher dropdown de sélection de nœud pour chaque résultat
  - [ ] Interface conditionnelle : Afficher 4 champs seulement si `test` est défini
  - [ ] Tests E2E : Édition choix avec test permet sélection 4 nœuds cibles

- [ ] Task 7: Mettre à jour NodeEditorPanel pour gérer 4 résultats (AC: #2)
  - [ ] Modifier `frontend/src/components/graph/NodeEditorPanel.tsx`
  - [ ] Si nœud est TestNode avec test, afficher 4 champs de connexion
  - [ ] Permettre sélection manuelle des 4 nœuds cibles
  - [ ] Validation : Vérifier que les 4 nœuds cibles existent dans le graphe
  - [ ] Tests E2E : Édition nœud de test permet configuration 4 résultats

- [ ] Task 8: Mettre à jour GraphConversionService pour exporter 4 résultats (AC: #4)
  - [ ] Modifier `services/graph_conversion_service.py` : Méthode `graph_to_unity_json()`
  - [ ] Détecter connexions vers handles `critical-failure`, `critical-success` en plus de `failure`, `success`
  - [ ] Exporter `testCriticalFailureNode`, `testCriticalSuccessNode` dans JSON Unity
  - [ ] Validation : Vérifier que JSON exporté contient les 4 champs si présents
  - [ ] Tests unitaires : Export graphe avec 4 résultats génère JSON valide

- [ ] Task 9: Mettre à jour UnityJsonRenderer pour valider 4 résultats (AC: #4)
  - [ ] Modifier `services/json_renderer/unity_json_renderer.py` : Méthode `validate_nodes()`
  - [ ] Ajouter `testCriticalFailureNode`, `testCriticalSuccessNode` à `reference_fields`
  - [ ] Valider que références pointent vers nœuds existants
  - [ ] Tests unitaires : Validation JSON avec 4 résultats détecte références invalides

- [ ] Task 10: Documentation et validation schéma Unity (AC: #4)
  - [x] **VALIDÉ** : Schéma Unity supporte les 4 champs (confirmé dans `docs/resources/JsonDocUnity/Documentation/dialogue-format.schema.json`)
  - [ ] Documenter format exact attendu par Unity :
    - **Pour les choix** : `testCriticalSuccessNode`, `testSuccessNode`, `testFailureNode`, `testCriticalFailureNode`
    - **Pour les nœuds** : `criticalSuccessNode`, `successNode`, `failureNode`, `criticalFailureNode`
  - [ ] Documenter logique de fallback : `criticalSuccessNode` → `successNode` si non défini, `criticalFailureNode` → `failureNode` si non défini
  - [ ] Documenter seuils de test : Critical success (score >= DD + 5), Success (score >= DD et < DD + 5), Failure (score >= DD - 5 et < DD), Critical failure (score < DD - 5)
  - [ ] Mettre à jour documentation technique avec spécifications Unity
  - [ ] Tests intégration : Export/import cycle avec 4 résultats fonctionne

- [ ] Task 11: Tests E2E complets (AC: #1, #2, #3, #4, #5)
  - [ ] Test E2E : Créer choix avec test, générer 4 nœuds, vérifier connexions
  - [ ] Test E2E : Exporter dialogue avec 4 résultats, importer, vérifier graphe
  - [ ] Test E2E : Éditer manuellement les 4 connexions dans l'éditeur
  - [ ] Test E2E : Rétrocompatibilité : Charger ancien dialogue avec 2 résultats fonctionne

## Dev Notes

### Architecture Patterns

- **Rétrocompatibilité critique** : Les anciens dialogues avec 2 résultats (success/failure) doivent continuer à fonctionner
- **Extension progressive** : Utiliser champs optionnels dans schémas TypeScript/Pydantic
- **Validation Unity** : ✅ **VALIDÉ** - Le schéma Unity supporte les 4 champs (voir `docs/resources/JsonDocUnity/Documentation/dialogue-format.schema.json`)
- **Distinction choix vs nœuds** : 
  - **Pour les choix** (dans `choices[]`) : `testCriticalSuccessNode`, `testSuccessNode`, `testFailureNode`, `testCriticalFailureNode`
  - **Pour les nœuds** (au niveau racine) : `criticalSuccessNode`, `successNode`, `failureNode`, `criticalFailureNode`
  - **Important** : Cette story se concentre sur les **choix avec test**, donc utiliser les champs avec préfixe `test*`

### Fichiers à Modifier

**Frontend:**
- `frontend/src/types/api.ts` - Types TypeScript Unity
- `frontend/src/schemas/nodeEditorSchema.ts` - Schémas validation
- `frontend/src/components/graph/nodes/TestNode.tsx` - Composant nœud de test
- `frontend/src/components/graph/ChoiceEditor.tsx` - Éditeur de choix
- `frontend/src/components/graph/NodeEditorPanel.tsx` - Panel édition nœud
- `frontend/src/components/generation/GraphView.tsx` - Conversion JSON → graphe

**Backend:**
- `models/dialogue_structure/unity_dialogue_node.py` - Modèles Pydantic
- `services/unity_dialogue_generation_service.py` - Génération IA
- `services/graph_conversion_service.py` - Conversion graphe → JSON
- `services/json_renderer/unity_json_renderer.py` - Validation JSON

### Décisions Techniques

1. **Schéma Unity** : **VALIDÉ** - Le schéma Unity (`docs/resources/JsonDocUnity/Documentation/dialogue-format.schema.json`) supporte les 4 champs :
   - **Pour les choix** (dans `choices[]`) : `testCriticalSuccessNode`, `testSuccessNode`, `testFailureNode`, `testCriticalFailureNode`
   - **Pour les nœuds** (au niveau racine) : `criticalSuccessNode`, `successNode`, `failureNode`, `criticalFailureNode`
   - **Focus de cette story** : Les choix avec test, donc utiliser les champs avec préfixe `test*`
   - **Logique de fallback** : Si `testCriticalSuccessNode` non défini → utilise `testSuccessNode`, si `testCriticalFailureNode` non défini → utilise `testFailureNode`
   - **Seuils de test** : 
     - Critical success : score >= DD + 5
     - Success : score >= DD et < DD + 5
     - Failure : score >= DD - 5 et < DD
     - Critical failure : score < DD - 5

2. **Couleurs handles** : 
   - Échec critique : `#C0392B` (rouge foncé)
   - Échec : `#E74C3C` (rouge)
   - Réussite : `#27AE60` (vert)
   - Réussite critique : `#229954` (vert foncé)

3. **Position handles** : Répartir équitablement sur 4 positions (12.5%, 37.5%, 62.5%, 87.5% de la largeur)

4. **Génération IA** : Modifier prompt pour demander explicitement 4 réponses avec contexte de chaque résultat :
   - **Échec critique** (score < DD - 5) : Réponse très négative, conséquence grave
   - **Échec** (score >= DD - 5 et < DD) : Réponse négative, conséquence modérée
   - **Réussite** (score >= DD et < DD + 5) : Réponse positive, conséquence favorable
   - **Réussite critique** (score >= DD + 5) : Réponse très positive, conséquence exceptionnelle

### Références

- **Schéma Unity officiel** : `docs/resources/JsonDocUnity/Documentation/dialogue-format.schema.json` (version 1.0.0)
- Schéma TypeScript actuel : `frontend/src/types/api.ts` lignes 270-308
- Composant TestNode : `frontend/src/components/graph/nodes/TestNode.tsx`
- Modèles Pydantic : `models/dialogue_structure/unity_dialogue_node.py`
- Service génération : `services/unity_dialogue_generation_service.py`

### Questions Résolues

1. **Schéma Unity** : ✅ **RÉSOLU** - Le schéma JSON Unity supporte les 4 champs (confirmé dans `docs/resources/JsonDocUnity/Documentation/dialogue-format.schema.json`)

2. **Rétrocompatibilité** : ✅ **RÉSOLU** - Solution : Champs optionnels, anciens JSON avec 2 résultats fonctionnent toujours grâce au fallback Unity

3. **Génération IA** : ✅ **RÉSOLU** - Solution : Demander explicitement 4 réponses avec contexte de chaque niveau (échec critique = très mauvais, échec = mauvais, réussite = bon, réussite critique = excellent)

## Dev Agent Record

### Agent Model Used

TBD

### Debug Log References

TBD

### Completion Notes List

TBD

### File List

TBD
