# Fonctionnalités manquantes dans l'API REST

Ce document liste les fonctionnalités présentes dans l'interface Python (UI desktop) mais absentes de l'API REST.

## Résumé exécutif

L'API REST couvre les fonctionnalités principales, mais plusieurs fonctionnalités avancées de l'UI Python ne sont pas exposées via l'API.

---

## 1. Catégories GDD manquantes

### Espèces (Species)
- **UI Python** : Liste complète des espèces avec détails (`ui/left_selection_panel.py`)
- **API REST** : ❌ Aucun endpoint pour lister/récupérer les espèces
- **Impact** : Impossible de sélectionner des espèces dans le contexte via l'API

**Endpoints nécessaires** :
```
GET /api/v1/context/species           # Liste toutes les espèces
GET /api/v1/context/species/{name}    # Détails d'une espèce
```

### Communautés (Communities)
- **UI Python** : Liste complète des communautés avec détails (`ui/left_selection_panel.py`)
- **API REST** : ❌ Aucun endpoint pour lister/récupérer les communautés
- **Impact** : Impossible de sélectionner des communautés dans le contexte via l'API

**Endpoints nécessaires** :
```
GET /api/v1/context/communities           # Liste toutes les communautés
GET /api/v1/context/communities/{name}    # Détails d'une communauté
```

**Note** : Les schémas Pydantic (`api/schemas/dialogue.py`) incluent déjà `species` et `communities` dans `ContextSelection`, donc la structure est prête côté client, mais les endpoints pour récupérer ces données manquent.

---

## 2. Fichiers Yarn

### Liste et parsing des fichiers Yarn
- **UI Python** : 
  - Liste des fichiers `.yarn` depuis le dossier Unity (`ui/left_selection_panel.py:314-355`)
  - Parsing et affichage des nœuds Yarn dans le panneau de détails (`ui/details_panel.py:115-142`)
  - Visualisation du contenu d'un nœud Yarn sélectionné
- **API REST** : ❌ Aucun endpoint pour les fichiers Yarn
- **Impact** : Impossible de consulter/analyser les dialogues existants depuis l'API

**Endpoints nécessaires** :
```
GET /api/v1/yarn/files                    # Liste tous les fichiers .yarn
GET /api/v1/yarn/files/{path}             # Détails d'un fichier Yarn (nœuds, métadonnées)
GET /api/v1/yarn/files/{path}/nodes       # Liste des nœuds d'un fichier
GET /api/v1/yarn/files/{path}/nodes/{node_title}  # Contenu d'un nœud spécifique
```

**Services existants à réutiliser** :
- `services.yarn_renderer.yarn_parser.parse_yarn_file()` (déjà utilisé dans `ui/details_panel.py`)
- `config_manager.list_yarn_files()` (déjà utilisé dans `ui/left_selection_panel.py`)

---

## 3. Linked Selector (Éléments liés)

### Suggestion automatique d'éléments liés
- **UI Python** : 
  - Bouton "Lier Éléments Connexes" (`ui/generation_panel/handlers.py:4-30`)
  - Service `LinkedSelectorService` qui suggère automatiquement des éléments liés (`services/linked_selector.py`)
  - Utilise `ContextBuilder.get_linked_elements()` pour trouver les relations
- **API REST** : ❌ Aucun endpoint pour suggérer des éléments liés
- **Impact** : Impossible d'automatiser la sélection d'éléments liés via l'API

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

## 4. Régions et sous-lieux

### Hiérarchie des lieux
- **UI Python** : 
  - Sélection de région avec mise à jour dynamique des sous-lieux (`ui/generation_panel/scene_selection_widget.py:117-154`)
  - Méthodes `ContextBuilder.get_regions()` et `ContextBuilder.get_sub_locations(region_name)`
- **API REST** : ⚠️ Partiellement supporté
  - L'API supporte les lieux mais pas explicitement la hiérarchie régions/sous-lieux
- **Impact** : Pas de moyen simple de récupérer les sous-lieux d'une région via l'API

**Endpoints nécessaires** :
```
GET /api/v1/context/locations/regions              # Liste toutes les régions
GET /api/v1/context/locations/regions/{name}/sub-locations  # Sous-lieux d'une région
```

**Services existants à réutiliser** :
- `context_builder.ContextBuilder.get_regions()`
- `context_builder.ContextBuilder.get_sub_locations(region_name)`

---

## 5. Continuité (Previous Interactions Context)

### Sélection d'interactions précédentes pour le contexte
- **UI Python** : 
  - Onglet "Continuité" avec widget `PreviousDialogueSelectorWidget` (`ui/left_panel/previous_dialogue_selector_widget.py`)
  - Récupération du chemin complet d'une interaction (parents jusqu'à la racine)
  - Méthode `ContextBuilder.set_previous_dialogue_context()` pour définir le contexte
  - Le contexte précédent est inclus dans `build_context()` via `_format_previous_dialogue_for_context()`
- **API REST** : ⚠️ Partiellement supporté
  - L'API permet de récupérer les interactions (`GET /api/v1/interactions/{id}`)
  - L'API permet de récupérer les parents/enfants (`GET /api/v1/interactions/{id}/parents|children`)
  - Mais **pas de moyen d'utiliser une interaction précédente comme contexte** pour la génération
- **Impact** : Impossible de maintenir la continuité narrative via l'API

**Endpoints nécessaires** :
```
GET /api/v1/interactions/{id}/context-path         # Récupère le chemin complet (parents)
POST /api/v1/dialogues/generate/interactions       # Doit accepter previous_interaction_id dans le body
```

**Note** : Le service `DialogueGenerationService` utilise déjà `ContextBuilder` qui supporte `previous_dialogue_context`, mais cette fonctionnalité n'est pas exposée via l'API.

---

## 6. Configuration Unity Dialogues Path

### Configuration du chemin des dialogues Unity
- **UI Python** : 
  - Menu "Configure Unity Dialogues Path..." (`ui/main_window.py:226-251`)
  - Stocké via `ConfigurationService.set_unity_dialogues_path()`
  - Utilisé pour lister les fichiers Yarn
- **API REST** : ❌ Aucun endpoint pour configurer/gérer ce chemin
- **Impact** : Le frontend ne peut pas configurer où trouver les fichiers Yarn

**Endpoints nécessaires** :
```
GET /api/v1/config/unity-dialogues-path    # Récupère le chemin configuré
PUT /api/v1/config/unity-dialogues-path    # Configure le chemin
```

**Services existants à réutiliser** :
- `services.configuration_service.ConfigurationService.get_unity_dialogues_path()`
- `services.configuration_service.ConfigurationService.set_unity_dialogues_path()`

---

## 7. Dialogue Structure

### Structure de dialogue personnalisable
- **UI Python** : 
  - Widget `DialogueStructureWidget` permettant de définir la structure du dialogue (`ui/generation_panel/dialogue_structure_widget.py`)
  - La structure est transmise au service de génération
- **API REST** : ⚠️ Vérification nécessaire
  - Les endpoints de génération acceptent probablement une structure, mais à vérifier dans les schémas

**À vérifier** : Les schémas `GenerateInteractionVariantsRequest` incluent-ils `dialogue_structure` ?

---

## 8. System Prompt Override

### Personnalisation du system prompt
- **UI Python** : 
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
   - Configuration Unity Dialogues Path (nécessaire pour Yarn)

3. **Basse priorité** (fonctionnalités avancées) :
   - Fichiers Yarn (consultation, pas critique pour la génération)
   - Continuité (previous interactions) - déjà partiellement supporté, manque juste l'intégration

---

## Notes techniques

- Tous les services backend nécessaires existent déjà dans le codebase Python
- Il s'agit principalement de créer des routers FastAPI qui exposent ces services
- Les schémas Pydantic existants peuvent être réutilisés/étendus
- Aucune modification du code métier n'est nécessaire, seulement l'exposition via l'API

