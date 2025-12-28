# Fonctionnalités manquantes dans l'API REST

Ce document liste les fonctionnalités qui étaient présentes dans l'ancienne interface desktop mais qui ne sont pas encore implémentées dans l'API REST.

**Note** : Ce document a été mis à jour le 2025-12-25. Unity n'utilise plus le format Yarn (.yarn) mais le format JSON (voir spécification dans ce dossier).

## Résumé exécutif

L'API REST couvre les fonctionnalités principales, mais plusieurs fonctionnalités avancées de l'ancienne interface ne sont pas encore exposées via l'API.

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
- **API REST** : ✅ Implémenté - `GET /api/v1/interactions/{id}/context-path`, `previous_interaction_id` dans `POST /api/v1/dialogues/generate/interactions`
- **Impact** : Fonctionnalité disponible via l'API

**Endpoints nécessaires** :
```
GET /api/v1/interactions/{id}/context-path         # Récupère le chemin complet (parents)
POST /api/v1/dialogues/generate/interactions       # Doit accepter previous_interaction_id dans le body
```

**Note** : Le service `DialogueGenerationService` utilise déjà `ContextBuilder` qui supporte `previous_dialogue_context`, mais cette fonctionnalité n'est pas exposée via l'API.

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

## Priorités recommandées

1. **Haute priorité** (fonctionnalités bloquantes) :
   - Espèces et communautés (catégories GDD manquantes)
   - Régions et sous-lieux (hiérarchie des lieux)

2. **Moyenne priorité** (fonctionnalités importantes) :
   - Linked Selector (améliore l'UX)
   - Configuration Unity Dialogues Path (utile pour l'intégration Unity)

3. **Basse priorité** (fonctionnalités avancées) :
   - Continuité (previous interactions) - déjà partiellement supporté, manque juste l'intégration

---

## Notes techniques

- Tous les services backend nécessaires existent déjà dans le codebase Python
- Il s'agit principalement de créer des routers FastAPI qui exposent ces services
- Les schémas Pydantic existants peuvent être réutilisés/étendus
- Aucune modification du code métier n'est nécessaire, seulement l'exposition via l'API
- **Format Unity** : Unity utilise maintenant le format JSON (tableau de nœuds `[{...}, {...}]`), pas Yarn. Voir la spécification dans ce dossier pour les détails du format attendu.
