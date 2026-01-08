# Fonctionnalités manquantes dans l'API REST

Ce document liste les fonctionnalités qui étaient présentes dans l'ancienne interface desktop mais qui ne sont pas encore implémentées dans l'API REST, ainsi que les fonctionnalités mentionnées dans le README qui sont partiellement ou non implémentées.

**Note** : Ce document a été mis à jour le 2025-12-25. Unity n'utilise plus le format Yarn (.yarn) mais le format JSON (voir spécification dans ce dossier).

**Dernière vérification** : 2026-01-02 - La plupart des fonctionnalités sont maintenant implémentées.

**Vérification approfondie** : 2026-01-02 - Vérification complète de l'existant pour identifier les fonctionnalités réellement manquantes.

## Résumé exécutif

L'API REST couvre les fonctionnalités principales. La plupart des fonctionnalités de l'ancienne interface sont implémentées. Quelques fonctionnalités avancées mentionnées dans le README restent à implémenter.

---

## 1. Catégories GDD manquantes

### Espèces (Species)
- **Ancienne UI** : Liste complète des espèces avec détails
- **API REST** : ✅ Implémenté - `GET /api/v1/context/species`, `GET /api/v1/context/species/{name}`
- **Impact** : Fonctionnalité disponible via l'API

**Endpoints nécessaires** :
```
GET /api/v1/context/species           # Liste toutes les espèces
GET /api/v1/context/species/{name}    # Détails d'une espèce
```

### Communautés (Communities)
- **Ancienne UI** : Liste complète des communautés avec détails
- **API REST** : ✅ Implémenté - `GET /api/v1/context/communities`, `GET /api/v1/context/communities/{name}`
- **Impact** : Fonctionnalité disponible via l'API

**Endpoints nécessaires** :
```
GET /api/v1/context/communities           # Liste toutes les communautés
GET /api/v1/context/communities/{name}    # Détails d'une communauté
```

**Note** : Les schémas Pydantic (`api/schemas/dialogue.py`) incluent déjà `species` et `communities` dans `ContextSelection`, donc la structure est prête côté client, mais les endpoints pour récupérer ces données manquent.

---

## 2. Linked Selector (Éléments liés)

### Suggestion automatique d'éléments liés
- **Ancienne UI** : 
  - Bouton "Lier Éléments Connexes" (`ui/generation_panel/handlers.py:4-30`)
  - Service `LinkedSelectorService` qui suggère automatiquement des éléments liés (`services/linked_selector.py`)
  - Utilise `ContextBuilder.get_linked_elements()` pour trouver les relations
- **API REST** : ✅ Implémenté - `POST /api/v1/context/linked-elements`
- **Impact** : Fonctionnalité disponible via l'API

**Endpoint nécessaire** :
```
POST /api/v1/context/linked-elements      # Suggère des éléments liés
Body: {
  "character_a": "string (optional)",
  "character_b": "string (optional)",
  "scene_region": "string (optional)",
  "sub_location": "string (optional)"
}
Response: {
  "linked_elements": {
    "characters": ["..."],
    "locations": ["..."],
    "items": ["..."],
    "species": ["..."],
    "communities": ["..."],
    "quests": ["..."]
  }
}
```

**Services existants à réutiliser** :
- `services.linked_selector.LinkedSelectorService.get_elements_to_select()`
- `context_builder.ContextBuilder.get_linked_elements()`

---

## 3. Régions et sous-lieux

### Hiérarchie des lieux
- **Ancienne UI** : 
  - Sélection de région avec mise à jour dynamique des sous-lieux (`ui/generation_panel/scene_selection_widget.py:117-154`)
  - Méthodes `ContextBuilder.get_regions()` et `ContextBuilder.get_sub_locations(region_name)`
- **API REST** : ✅ Implémenté - `GET /api/v1/context/locations/regions`, `GET /api/v1/context/locations/regions/{name}/sub-locations`
- **Impact** : Fonctionnalité disponible via l'API

**Endpoints nécessaires** :
```
GET /api/v1/context/locations/regions              # Liste toutes les régions
GET /api/v1/context/locations/regions/{name}/sub-locations  # Sous-lieux d'une région
```

**Services existants à réutiliser** :
- `context_builder.ContextBuilder.get_regions()`
- `context_builder.ContextBuilder.get_sub_locations(region_name)`

---

## 4. Continuité (Previous Interactions Context)

### Sélection d'interactions précédentes pour le contexte
- **Ancienne UI** : 
  - Onglet "Continuité" avec widget `PreviousDialogueSelectorWidget` (`ui/left_panel/previous_dialogue_selector_widget.py`)
  - Récupération du chemin complet d'une interaction (parents jusqu'à la racine)
  - Méthode `ContextBuilder.set_previous_dialogue_context()` pour définir le contexte
  - Le contexte précédent est inclus dans `build_context()` via `_format_previous_dialogue_for_context()`
- **API REST** : ✅ Partiellement implémenté
  - Les endpoints de génération acceptent `previous_dialogue_preview` (texte formaté) dans `BasePromptRequest`
  - Endpoint `POST /api/v1/unity-dialogues/preview` pour générer un preview texte depuis un dialogue Unity JSON
  - ⚠️ Pas d'endpoint pour récupérer le chemin complet d'une interaction (parents/enfants)
- **Impact** : La continuité est possible via preview texte, mais pas de gestion automatique des relations parent/enfant

**Endpoints disponibles** :
```
POST /api/v1/unity-dialogues/preview  # Génère un preview texte depuis un dialogue Unity JSON
Body: { "json_content": "..." }
Response: { "preview_text": "...", "node_count": 5 }
```

**Champ dans les requêtes de génération** :
- `previous_dialogue_preview: Optional[str]` dans `BasePromptRequest` (utilisé par tous les endpoints de génération)

---

## 5. Configuration Unity Dialogues Path

### Configuration du chemin des dialogues Unity
- **Ancienne UI** : 
  - Menu "Configure Unity Dialogues Path..." (`ui/main_window.py:226-251`)
  - Stocké via `ConfigurationService.set_unity_dialogues_path()`
  - Utilisé pour référencer le dossier où Unity stocke les fichiers de dialogues JSON
- **API REST** : ✅ Implémenté - `GET /api/v1/config/unity-dialogues-path`, `PUT /api/v1/config/unity-dialogues-path`
- **Impact** : Fonctionnalité disponible via l'API

**Endpoints nécessaires** :
```
GET /api/v1/config/unity-dialogues-path    # Récupère le chemin configuré
PUT /api/v1/config/unity-dialogues-path    # Configure le chemin
Body: { "path": "string" }
```

**Services existants à réutiliser** :
- `services.configuration_service.ConfigurationService.get_unity_dialogues_path()`
- `services.configuration_service.ConfigurationService.set_unity_dialogues_path()`

**Note** : Unity utilise maintenant le format JSON pour les dialogues (tableau de nœuds `[{...}, {...}]`), voir la spécification dans ce dossier pour plus de détails.

---

## 6. Dialogue Structure

### Structure de dialogue personnalisable
- **Ancienne UI** : 
  - Widget `DialogueStructureWidget` permettant de définir la structure du dialogue (`ui/generation_panel/dialogue_structure_widget.py`)
  - La structure est transmise au service de génération
- **API REST** : ✅ Déjà supporté
  - La structure de dialogue peut être transmise via `generation_settings.dialogue_structure` dans `ContextSelection`
  - Le service `DialogueGenerationService` récupère cette structure depuis `context_selections.get("generation_settings", {}).get("dialogue_structure", "")`

---

## 7. System Prompt Override

### Personnalisation du system prompt
- **Ancienne UI** : 
  - Widget `InstructionsWidget` avec possibilité de modifier le system prompt (`ui/generation_panel/instructions_widget.py`)
  - Bouton "Restore Default System Prompt"
- **API REST** : ✅ Déjà supporté
  - Les endpoints de génération acceptent `system_prompt_override` dans les schémas

---

## 8. Sélection multiple de personnages

### Sélection explicite de plusieurs personnages (Acteur A, Acteur B)
- **Ancienne UI** : 
  - Sélection de plusieurs personnages pour définir les protagonistes de la scène
- **API REST** : ✅ **DÉJÀ IMPLÉMENTÉ**
  - Le frontend utilise `characterA` et `characterB` dans `SceneSelection`
  - Ces valeurs sont transmises via `scene_protagonists` dans `ContextSelection`
  - Le champ `npc_speaker_id` permet de spécifier le PNJ interlocuteur
  - Référence : `frontend/src/components/generation/GenerationPanel.tsx:270-278`, `api/schemas/dialogue.py:45`

**Implémentation** :
- `ContextSelection.scene_protagonists` : Dictionnaire avec `personnage_a` et `personnage_b`
- `BasePromptRequest.npc_speaker_id` : ID du PNJ interlocuteur (par défaut : premier personnage sélectionné)
- Frontend : `SceneSelectionWidget` avec sélecteurs pour `characterA` et `characterB`

---

## 9. Paramètres de génération avancés

### Contrôle du ton, style, température, et autres paramètres LLM
- **Ancienne UI** : 
  - Interface pour configurer température, ton, style, etc.
- **API REST** : ⚠️ **PARTIELLEMENT IMPLÉMENTÉ**
  - ✅ `narrative_tags` : Tags narratifs pour guider le ton (ex: tension, humour, dramatique)
  - ✅ `author_profile` : Profil d'auteur global (style réutilisable entre scènes)
  - ✅ `max_choices` et `choices_mode` : Contrôle du nombre de choix
  - ✅ `vocabulary_config` : Configuration du vocabulaire par niveau
  - ✅ Sélection de modèle LLM : `llm_model_identifier`
  - ⚠️ `temperature` : **Présent dans la config backend mais non exposé dans l'API/UI**
  - ❌ `top_p`, `frequency_penalty`, `presence_penalty` : Non implémentés

**État actuel** :
- `temperature` est configuré dans `llm_config.json` et utilisé par `OpenAIClient` (`llm_client.py:146, 292-295`)
- La température par défaut est définie par modèle dans `config/llm_config.json`
- **Comportement** : `temperature` est ajoutée seulement si le modèle le supporte (exclu pour `gpt-5-mini` et `gpt-5-nano`)
- **Manque** : Exposition de `temperature` dans les schémas API et l'interface utilisateur pour permettre un contrôle dynamique

**Paramètres disponibles mais non utilisés** (Chat Completions API) :
- `top_p` : Contrôle la diversité (alternative/complément à temperature)
- `frequency_penalty` : Réduit la répétition de tokens (utile pour dialogues)
- `presence_penalty` : Encourage l'utilisation de nouveaux tokens (créativité)

**Paramètres disponibles uniquement via Responses API** (non utilisée actuellement) :
- `reasoning.effort` : Contrôle la profondeur de raisonnement (`none`, `low`, `medium`, `high`, `xhigh`)
- `verbosity` : Contrôle la longueur des réponses (`low`, `medium`, `high`)
- `previous_response_id` : Passe le chain-of-thought précédent (améliore latence et cache)

**Action nécessaire** :
- Ajouter `temperature: Optional[float]` dans `BasePromptRequest` ou `GenerateUnityDialogueRequest`
- Exposer `temperature` dans l'interface utilisateur (slider ou input)
- Passer `temperature` au client LLM lors de la création
- **Optionnel** : Ajouter `frequency_penalty` et `presence_penalty` pour améliorer la qualité des dialogues

**Référence** : Voir `docs/ANALYSE_PARAMETRES_OPENAI.md` pour une analyse détaillée des paramètres disponibles.

---

## 10. Structured Output (Sorties Structurées)

### Utilisation de JSON Schema avec l'API OpenAI pour un output plus fiable
- **README** : Mentionné comme fonctionnalité à explorer
- **API REST** : ✅ **DÉJÀ IMPLÉMENTÉ**
  - Utilise Function Calling avec `tools` et `tool_choice` dans OpenAI API
  - Modèle Pydantic `UnityDialogueGenerationResponse` converti en schéma JSON
  - Implémenté dans `UnityDialogueGenerationService` et `OpenAIClient`
  - Référence : `llm_client.py:219-246`, `services/unity_dialogue_generation_service.py:46-52`
  - Documentation : `docs/STRUCTURED_OUTPUT_EXPLANATION.md`

**Implémentation** :
- Le schéma Pydantic est converti en JSON Schema via `model_json_schema()`
- Le schéma est passé comme paramètre d'une fonction que l'IA doit appeler
- Garantit la structure JSON, les types, et la conformité au schéma

---

## 11. UnityJsonRenderer

### Module pour convertir les Interactions en fichiers JSON Unity
- **README** : Mentionné comme fonctionnalité à implémenter
- **API REST** : ✅ **DÉJÀ IMPLÉMENTÉ**
  - Module `UnityJsonRenderer` dans `services/json_renderer/unity_json_renderer.py`
  - Utilisé pour normaliser et exporter les dialogues Unity JSON
  - Méthode `render_unity_nodes()` pour convertir une liste de nœuds en JSON formaté
  - Référence : `services/json_renderer/unity_json_renderer.py:146-178`

**Implémentation** :
- Normalise les nœuds selon les règles Unity (supprime champs vides, valeurs par défaut)
- Valide les nœuds avant rendu
- Utilisé dans l'endpoint `/api/v1/dialogues/generate/unity-dialogue`

---

## 12. GitService

### Intégration Git pour commit/push automatique des dialogues générés
- **README** : Mentionné comme fonctionnalité à implémenter
- **Spécification technique** : `git add .; git commit -m "Generate …"` via subprocess
- **API REST** : ❌ **NON IMPLÉMENTÉ**
  - Aucun service Git trouvé dans le codebase
  - Aucun endpoint API pour les opérations Git

**Action nécessaire** :
- Créer `services/git_service.py` avec méthodes pour :
  - `commit_dialogue(filename, message)` : Commit un fichier de dialogue
  - `push_changes()` : Push les changements vers le repo distant
  - Gestion des credentials (store Windows ou token)
- Créer endpoint API `POST /api/v1/dialogues/git/commit` (optionnel, peut être appelé depuis le frontend après export)

**Référence** : `docs/Spécification technique.md:113-117`

---

## 13. Événements Notables (Stratégie Avancée)

### Génération de variantes basée sur des événements narratifs et leurs états
- **README** : Concept détaillé dans la section "Stratégie Avancée de Génération de Variantes"
- **API REST** : ❌ **NON IMPLÉMENTÉ**
  - Concept décrit mais aucun code trouvé
  - Aucun endpoint pour gérer les événements notables
  - Aucun système de génération combinatoire de variantes

**Concept** :
- Chaque événement narratif (ex: `decision_guilde_voleurs`) peut avoir plusieurs états
- Chaque état a une description textuelle pour le LLM
- Le système génère automatiquement une variante pour chaque combinaison d'états
- Exemple : 1 événement avec 3 états → 3 variantes, 2 événements (3×2 états) → 6 variantes

**Action nécessaire** :
- Créer un système de gestion des événements notables :
  - Modèle de données pour les événements et leurs états
  - Endpoint pour définir/gérer les événements
  - Logique de génération combinatoire dans `UnityDialogueGenerationService`
  - Interface utilisateur pour sélectionner les événements et leurs états
- **Défi** : Explosion combinatoire des variantes (nécessite une UI pour limiter les combinaisons)

**Référence** : `README.md:147-178`

---

## Priorités recommandées

### ✅ Fonctionnalités déjà implémentées

1. **Catégories GDD** :
   - ✅ Espèces et communautés (endpoints API)
   - ✅ Régions et sous-lieux (hiérarchie des lieux)
   - ✅ Linked Selector (suggestion d'éléments liés)
   - ✅ Configuration Unity Dialogues Path
   - ✅ Sélection multiple de personnages (characterA/characterB)
   - ✅ Structured Output (via Function Calling OpenAI)
   - ✅ UnityJsonRenderer (normalisation et export JSON Unity)
   - ✅ System Prompt Override
   - ✅ Dialogue Structure personnalisable

### 🔧 Fonctionnalités à compléter (priorité haute)

1. **Exposition de `temperature` dans l'API/UI** :
   - Impact : Contrôle fin de la créativité des réponses LLM
   - Complexité : Faible (ajout d'un champ dans les schémas et l'UI)
   - Référence : Section 9 ci-dessus

### 🚀 Fonctionnalités à implémenter (priorité moyenne)

2. **GitService** :
   - Impact : Complète le pipeline de production (génération → export → commit → Unity)
   - Complexité : Moyenne (service Git + gestion credentials)
   - Référence : Section 12 ci-dessus

3. **Continuité complète (relations parent/enfant)** :
   - Impact : Gestion automatique des arbres de dialogues
   - Complexité : Moyenne (endpoint pour récupérer le chemin complet d'une interaction)
   - Référence : Section 4 ci-dessus

### 🎯 Fonctionnalités avancées (priorité basse)

4. **Paramètres LLM avancés** (`top_p`, `frequency_penalty`, `presence_penalty`) :
   - Impact : Contrôle encore plus fin des réponses LLM
   - Complexité : Faible (similaire à `temperature`)
   - Référence : Section 9 ci-dessus

5. **Événements Notables** :
   - Impact : Génération de variantes contextuelles basées sur les événements narratifs
   - Complexité : Élevée (système complet de gestion d'événements + génération combinatoire)
   - Référence : Section 13 ci-dessus

---

## Notes techniques

- **Services backend existants** : La plupart des services backend nécessaires existent déjà dans le codebase Python. Pour les nouvelles fonctionnalités (GitService, Événements Notables), il faudra créer de nouveaux services.

- **Exposition via API** : Pour les fonctionnalités partiellement implémentées (temperature, continuité), il s'agit principalement de créer des routers FastAPI qui exposent ces services ou d'étendre les schémas existants.

- **Schémas Pydantic** : Les schémas Pydantic existants peuvent être réutilisés/étendus. Pour `temperature`, ajouter un champ optionnel dans `BasePromptRequest` ou `GenerateUnityDialogueRequest`.

- **Format Unity** : Unity utilise maintenant le format JSON (tableau de nœuds `[{...}, {...}]`), pas Yarn. Voir la spécification dans ce dossier pour les détails du format attendu.

- **Structured Output** : Déjà implémenté via Function Calling OpenAI. Le système garantit la structure JSON mais nécessite toujours des instructions explicites pour la logique métier (voir `docs/STRUCTURED_OUTPUT_EXPLANATION.md`).

- **Frontend** : L'interface React (`frontend/`) est l'interface principale. Les fonctionnalités manquantes doivent être exposées via l'API REST puis intégrées dans l'interface React.
