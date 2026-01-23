# Architecture : Construction du Prompt dans estimate-tokens

## Point d'entrée

**Endpoint** : `POST /api/v1/dialogues/estimate-tokens`  
**Fichier** : `api/routers/dialogues.py::estimate_tokens()` (ligne 97)

## Flux de construction du prompt

### 1. Construction du contexte GDD (optionnel)

```python
# api/routers/dialogues.py:147
context_text = context_builder.build_context(
    selected_elements=context_selections_dict,
    scene_instruction=request_data.user_instructions,
    max_tokens=request_data.max_context_tokens
)
```

**Résultat** :
- Si `context_selections = {}` → `context_text = ""` (vide)
- Si sélections présentes → contenu GDD (personnages, lieux, objets)

**Important** : Le contexte GDD est **optionnel**. Avec `context_selections = {}`, on obtient `context_tokens = 0`.

### 2. Construction du prompt complet

```python
# api/routers/dialogues.py:328
full_prompt, prompt_tokens = prompt_engine.build_unity_dialogue_prompt(
    user_instructions=request_data.user_instructions,
    npc_speaker_id=npc_speaker_id,
    player_character_id="URESAIR",
    skills_list=skills_list,
    traits_list=traits_list,
    context_summary=context_text,  # ← Peut être vide
    scene_location=scene_location_dict,
    max_choices=None,
    narrative_tags=None,
    author_profile=None,
    vocabulary_config=request_data.vocabulary_config,  # ← Peut être None
    include_narrative_guides=request_data.include_narrative_guides  # ← Défaut: True
)
```

**Fichier** : `prompt_engine.py::build_unity_dialogue_prompt()` (ligne 220)

### 3. Structure du prompt généré

Le prompt est construit en **sections principales** avec des sous-sections explicites :

#### SECTION 0. CONTRAT GLOBAL
- Directives d'auteur (si `author_profile` fourni)
- Ton narratif (si `narrative_tags` fourni)
- Règles de priorité
- Format de sortie / Interdictions

#### SECTION 1. INSTRUCTIONS TECHNIQUES
- Instructions de génération (speaker, choix, tests)
- Compétences disponibles (si `skills_list` fourni)
- Traits disponibles (si `traits_list` fourni)

#### SECTION 2A. CONTEXTE GDD
- **CONTEXTE GÉNÉRAL DE LA SCÈNE** : `context_summary` (peut être vide)
- **LIEU DE LA SCÈNE** : `scene_location` (si fourni)

#### SECTION 2B. GUIDES NARRATIFS
- Guides narratifs injectés si `include_narrative_guides=True` (défaut)
- Format : `[GUIDES NARRATIFS]` + contenu

#### SECTION 2C. VOCABULAIRE ALTEIR
- Vocabulaire injecté si `vocabulary_config` fourni
- Format : `[VOCABULAIRE ALTEIR]` + termes filtrés

#### SECTION 3. INSTRUCTIONS DE SCÈNE
- Brief de scène (local) : `user_instructions`

### 4. Injection des GUIDES NARRATIFS (SECTION 2B)

**Fichier** : `prompt_engine.py::_inject_narrative_guides()` (ligne 138)  
**Section** : `prompt_engine.py` ligne ~490 (après SECTION 2A)

```python
# prompt_engine.py:490
guides_parts = []
guides_parts = self._inject_narrative_guides(
    guides_parts, 
    include_narrative_guides,  # ← Défaut: True
    format_style="unity"
)

if guides_parts:
    prompt_parts.append("### SECTION 2B. GUIDES NARRATIFS")
    prompt_parts.extend(guides_parts)
```

**Service** : `services/narrative_guides_service.py::format_for_prompt()` (ligne 100)

**Résultat** :
```python
# services/narrative_guides_service.py:109
lines = ["[GUIDES NARRATIFS]"]
# + Guide des dialogues
# + Guide de narration
```

**Comportement** :
- Si `include_narrative_guides=True` (défaut) → SECTION 2B créée avec guides injectés
- Si `include_narrative_guides=False` → SECTION 2B absente
- **Indépendant du contexte GDD** : Les guides sont chargés depuis Notion, pas depuis le contexte

### 5. Injection du VOCABULAIRE ALTEIR (SECTION 2C)

**Fichier** : `prompt_engine.py::_inject_vocabulary()` (ligne 90)  
**Section** : `prompt_engine.py` ligne ~500 (après SECTION 2B)

```python
# prompt_engine.py:500
vocab_parts = []
vocab_parts = self._inject_vocabulary(
    vocab_parts,
    vocabulary_config,  # ← Peut être None
    context_summary,
    format_style="unity"
)

if vocab_parts:
    prompt_parts.append("### SECTION 2C. VOCABULAIRE ALTEIR")
    prompt_parts.extend(vocab_parts)
```

**Service** : `services/vocabulary_service.py`

**Résultat** :
```python
# Format: "[VOCABULAIRE ALTEIR]\nterm1: definition1\n..."
```

**Comportement** :
- Si `vocabulary_config=None` → SECTION 2C absente
- Si `vocabulary_config` fourni → SECTION 2C créée avec vocabulaire filtré selon la config
- **Indépendant du contexte GDD** : Le vocabulaire est chargé depuis Notion, pas depuis le contexte

## Conclusion : Pourquoi `[GUIDES NARRATIFS]` apparaît avec `context_tokens=0`

### Ce qui est injecté systématiquement (si configuré)

1. **GUIDES NARRATIFS** : 
   - Injecté si `include_narrative_guides=True` (défaut dans le schéma)
   - Chargé depuis `services/narrative_guides_service.py`
   - Format : `[GUIDES NARRATIFS]` + contenu

2. **VOCABULAIRE ALTEIR** :
   - Injecté si `vocabulary_config` est fourni (même vide `{}`)
   - Chargé depuis `services/vocabulary_service.py`
   - Format : `[VOCABULAIRE ALTEIR]` + termes filtrés

### Ce qui dépend du contexte GDD

- **CONTEXTE GÉNÉRAL DE LA SCÈNE** : Uniquement si `context_selections` contient des éléments
- Avec `context_selections = {}` → `context_text = ""` → `context_tokens = 0`

### Architecture claire

```
prompt = SECTION 0 (toujours)
      + SECTION 1 (toujours)
      + SECTION 2A. CONTEXTE GDD [
          + CONTEXTE GÉNÉRAL (si context_selections non vide)
          + LIEU (si fourni)
        ]
      + SECTION 2B. GUIDES NARRATIFS (si include_narrative_guides=True) ← INJECTION SYSTÉMATIQUE
      + SECTION 2C. VOCABULAIRE ALTEIR (si vocabulary_config fourni) ← INJECTION SYSTÉMATIQUE
      + SECTION 3 (toujours)
```

**Séparation explicite** :
- **SECTION 2A** : Contexte GDD (optionnel, dépend de `context_selections`)
- **SECTION 2B** : Guides narratifs (systématique si `include_narrative_guides=True`)
- **SECTION 2C** : Vocabulaire Alteir (systématique si `vocabulary_config` fourni)

**Les sections 2B et 2C sont indépendantes du contexte GDD** : elles sont chargées depuis Notion, pas depuis le contexte utilisateur.

## Preuve factuelle

Test avec `context_selections = {}` :
- `context_tokens = 0` ✅ (aucun contexte GDD)
- `total_estimated_tokens = 2860` ✅ (prompt complet avec guides)
- `estimated_prompt` contient `[GUIDES NARRATIFS]` ✅ (injection systématique)

**Conclusion** : Le backend fonctionne correctement. Les guides narratifs sont injectés par défaut, indépendamment du contexte GDD.
