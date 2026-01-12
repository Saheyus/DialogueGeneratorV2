# OpenAI API pour GPT-5+ (GPT-5.2, GPT-5.2-pro)

Documentation complète de l'utilisation de l'API OpenAI pour les modèles GPT-5.2 et GPT-5.2-pro dans DialogueGenerator.

## Vue d'ensemble

Les modèles GPT-5.2 et GPT-5.2-pro utilisent une **API différente** de celle utilisée par les modèles précédents (Chat Completions). Ils utilisent la **Responses API**, qui offre des fonctionnalités supplémentaires comme la phase réflexive (reasoning) et un format de réponse structuré.

**Modèles concernés**: `gpt-5.2`, `gpt-5.2-pro`

**Détermination automatique**: Le code détecte automatiquement si un modèle commence par `gpt-5.2` et utilise alors Responses API au lieu de Chat Completions.

## Choix de l'API

### Responses API (GPT-5.2/+)

Utilisée pour tous les modèles commençant par `gpt-5.2`:
- `client.responses.create(**params)`
- Endpoint: `/v1/responses`

### Chat Completions API (Legacy)

Utilisée pour tous les autres modèles (GPT-4, GPT-3.5, GPT-5 mini/nano):
- `client.chat.completions.create(**params)`
- Endpoint: `/v1/chat/completions`

**Code de détermination**:
```python
use_responses_api = bool(self.model_name and self.model_name.startswith("gpt-5.2"))
```

## Format de requête

### Différences principales

| Paramètre | Chat Completions | Responses API |
|-----------|------------------|---------------|
| Messages | `messages` (liste) | `input` (liste, même structure) |
| Tokens max | `max_tokens` ou `max_completion_tokens` | `max_output_tokens` |
| Tools | `{"type": "function", "function": {...}}` | `{"type": "function", "name": "...", "parameters": {...}}` |
| Tool choice | `{"type": "function", "function": {...}}` | `{"type": "allowed_tools", "mode": "required", "tools": [...]}` |
| Temperature | Toujours supportée | Uniquement si `reasoning.effort == "none"` |
| Reasoning | Non disponible | `reasoning.effort` et `reasoning.summary` |

### Exemple de requête Responses API

```python
responses_params = {
    "model": "gpt-5.2",
    "input": [
        {"role": "system", "content": "Tu es un assistant expert..."},
        {"role": "user", "content": "Génère un dialogue..."}
    ],
    "tools": [
        {
            "type": "function",
            "name": "generate_interaction",
            "description": "Génère une interaction de dialogue structurée.",
            "parameters": {
                "type": "object",
                "properties": {...},
                "required": [...]
            }
        }
    ],
    "tool_choice": {
        "type": "allowed_tools",
        "mode": "required",
        "tools": [{"type": "function", "name": "generate_interaction"}]
    },
    "max_output_tokens": 1500,
    "reasoning": {
        "effort": "medium",
        "summary": "auto"
    }
}

response = await client.responses.create(**responses_params)
```

### Exemple de requête Chat Completions (pour comparaison)

```python
chat_params = {
    "model": "gpt-5-mini",
    "messages": [
        {"role": "system", "content": "Tu es un assistant expert..."},
        {"role": "user", "content": "Génère un dialogue..."}
    ],
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "generate_interaction",
                "description": "Génère une interaction de dialogue structurée.",
                "parameters": {...}
            }
        }
    ],
    "tool_choice": {
        "type": "function",
        "function": {"name": "generate_interaction"}
    },
    "max_completion_tokens": 1500,
    "temperature": 0.7
}

response = await client.chat.completions.create(**chat_params)
```

## Reasoning (Phase réflexive)

La phase réflexive (reasoning) est une fonctionnalité exclusive aux modèles GPT-5.2/+ via Responses API. Elle permet au modèle de "réfléchir" avant de générer sa réponse.

### Paramètres

- **`reasoning.effort`**: Niveau d'effort de raisonnement
  - `"none"`: Pas de phase réflexive (rapide)
  - `"low"`: Raisonnement léger
  - `"medium"`: Raisonnement modéré (recommandé)
  - `"high"`: Raisonnement approfondi
  - `"xhigh"`: Raisonnement très approfondi (plus lent, plus coûteux)

- **`reasoning.summary`**: Format du résumé de la phase réflexive
  - `None`: Pas de résumé
  - `"auto"`: Résumé automatique (recommandé)
  - `"detailed"`: Résumé détaillé

### Comportement automatique

Si `reasoning.effort` est défini mais `reasoning.summary` est `None`, alors `summary="auto"` est activé automatiquement.

### Extraction du reasoning trace

Le reasoning trace est extrait depuis deux sources dans la réponse:

1. **`response.reasoning`**: Métadonnées (effort, summary configuré)
2. **`response.output`**: Contenu réel (chercher l'item avec `type="reasoning"`)

**Structure du reasoning trace**:
```python
reasoning_trace = {
    "effort": "medium",  # Effort configuré
    "summary": "Résumé textuel de la phase réflexive...",  # Texte extrait
    "items": [...],  # Items structurés du raisonnement (si disponibles)
    "items_count": 5  # Nombre d'items
}
```

**Code d'extraction**:
```python
# Depuis response.reasoning (métadonnées)
reasoning_data = getattr(response, "reasoning", None)
if reasoning_data:
    reasoning_effort = getattr(reasoning_data, "effort", None)
    reasoning_summary = getattr(reasoning_data, "summary", None)

# Depuis response.output (contenu réel)
output_items = getattr(response, "output", None) or []
for item in output_items:
    if getattr(item, "type", None) == "reasoning":
        reasoning_content_item = item
        summary_raw = getattr(reasoning_content_item, "summary", None)
        # Traitement du summary (peut être liste, string, etc.)
        break
```

## Temperature

**Contrainte importante**: Temperature est supportée uniquement si `reasoning.effort == "none"` (ou non spécifié).

Si `reasoning.effort` est défini avec une valeur autre que `"none"`, le paramètre `temperature` est ignoré par l'API.

**Code de gestion**:
```python
if use_responses_api and (self.reasoning_effort in (None, "none")):
    responses_params["temperature"] = self.temperature
elif use_responses_api and (self.reasoning_effort not in (None, "none")):
    # Temperature omise car reasoning.effort est défini
    pass
```

## Parsing de réponse

### Responses API

La réponse utilise un format structuré avec une liste d'items dans `response.output`:

```python
output_items = getattr(response, "output", None) or []

# Chercher l'appel de fonction (structured output)
for item in output_items:
    item_type = getattr(item, "type", None)
    if item_type in ("function_call", "tool_call", "function"):
        name = getattr(item, "name", None)
        args = getattr(item, "arguments", None)
        
        # Gestion de l'encapsulation sous item.function
        if name is None and getattr(item, "function", None) is not None:
            name = getattr(item.function, "name", None)
            args = getattr(item.function, "arguments", None)
        
        if name == "generate_interaction" and args:
            function_args_raw = args
            # Parser avec Pydantic
            parsed_output = response_model.model_validate_json(function_args_raw)
            break
```

**Types d'items dans `output`**:
- `"reasoning"`: Phase réflexive (contenu)
- `"function_call"` / `"tool_call"` / `"function"`: Appel de fonction (structured output)
- `"text"`: Réponse texte simple

### Chat Completions

Format classique avec `choices[0].message`:

```python
if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    if tool_call.function.name == "generate_interaction":
        function_args_raw = tool_call.function.arguments
        parsed_output = response_model.model_validate_json(function_args_raw)
```

## Gestion des tokens

### Responses API

- **Input tokens**: `response.usage.input_tokens`
- **Output tokens**: `response.usage.output_tokens`
- **Total**: `input_tokens + output_tokens` (pas de champ séparé)
- **Paramètre**: `max_output_tokens` (au lieu de `max_tokens`)

### Chat Completions

- **Prompt tokens**: `response.usage.prompt_tokens`
- **Completion tokens**: `response.usage.completion_tokens`
- **Total**: `response.usage.total_tokens`
- **Paramètre**: `max_tokens` ou `max_completion_tokens` (pour GPT-5)

**Code d'extraction**:
```python
if hasattr(response.usage, "input_tokens"):
    # Responses API
    prompt_tokens = getattr(response.usage, "input_tokens", 0) or 0
    completion_tokens = getattr(response.usage, "output_tokens", 0) or 0
    total_tokens = prompt_tokens + completion_tokens
elif hasattr(response.usage, "prompt_tokens"):
    # Chat Completions
    prompt_tokens = response.usage.prompt_tokens or 0
    completion_tokens = response.usage.completion_tokens or 0
    total_tokens = response.usage.total_tokens or 0
```

## Structured Output

Les deux APIs supportent le structured output via function calling, mais avec des formats différents.

### Responses API

**Format tool**:
```python
tool_definition_responses = {
    "type": "function",
    "name": "generate_interaction",
    "description": "Génère une interaction de dialogue structurée.",
    "parameters": {
        "type": "object",
        "properties": {...},
        "required": [...],
        "$defs": {...}  # Si références
    }
}
```

**Tool choice**:
```python
tool_choice = {
    "type": "allowed_tools",
    "mode": "required",
    "tools": [{"type": "function", "name": "generate_interaction"}]
}
```

### Chat Completions

**Format tool**:
```python
tool_definition = {
    "type": "function",
    "function": {
        "name": "generate_interaction",
        "description": "Génères une interaction de dialogue structurée.",
        "parameters": {...}
    }
}
```

**Tool choice**:
```python
tool_choice = {
    "type": "function",
    "function": {"name": "generate_interaction"}
}
```

## Modèles concernés

### Modèles GPT-5.2 (Responses API)

- **`gpt-5.2`**: Modèle principal, bon équilibre performance/coût
- **`gpt-5.2-pro`**: Version avec plus de compute pour raisonnement approfondi

**Caractéristiques**:
- Supportent Responses API
- Supportent reasoning (effort, summary)
- Supportent structured output
- Temperature uniquement si `reasoning.effort == "none"`
- Utilisent `max_output_tokens`

### Modèles GPT-5 (Chat Completions)

- **`gpt-5-mini`**: Version économique et rapide
- **`gpt-5-nano`**: Version compacte

**Caractéristiques**:
- Utilisent Chat Completions API
- Ne supportent **pas** reasoning
- Supportent structured output (mais peuvent avoir des problèmes)
- Supportent temperature
- Utilisent `max_completion_tokens`

**Note**: Les modèles GPT-5 (mini/nano) peuvent avoir des problèmes avec le structured output. Utiliser `gpt-5.2` si des erreurs surviennent.

## Exemple complet

```python
from openai import AsyncOpenAI
from typing import Optional
import os

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configuration pour GPT-5.2 avec reasoning
model_name = "gpt-5.2"
use_responses_api = model_name.startswith("gpt-5.2")

if use_responses_api:
    # Responses API
    response = await client.responses.create(
        model=model_name,
        input=[
            {"role": "system", "content": "Tu es un assistant expert..."},
            {"role": "user", "content": "Génère un dialogue..."}
        ],
        tools=[{
            "type": "function",
            "name": "generate_interaction",
            "description": "Génère une interaction de dialogue structurée.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "node": {
                        "type": "object",
                        "properties": {
                            "line": {"type": "string"},
                            "choices": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "text": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                },
                "required": ["title", "node"]
            }
        }],
        tool_choice={
            "type": "allowed_tools",
            "mode": "required",
            "tools": [{"type": "function", "name": "generate_interaction"}]
        },
        max_output_tokens=1500,
        reasoning={
            "effort": "medium",
            "summary": "auto"
        }
    )
    
    # Extraction du reasoning trace
    reasoning_trace = None
    if hasattr(response, "reasoning"):
        reasoning_data = response.reasoning
        reasoning_trace = {
            "effort": getattr(reasoning_data, "effort", None),
            "summary": getattr(reasoning_data, "summary", None),
            "items": [],
            "items_count": 0
        }
    
    # Extraction depuis output
    output_items = getattr(response, "output", None) or []
    for item in output_items:
        if getattr(item, "type", None) == "reasoning":
            summary_raw = getattr(item, "summary", None)
            if isinstance(summary_raw, list):
                reasoning_trace["summary"] = "\n".join(str(p) for p in summary_raw)
            elif isinstance(summary_raw, str):
                reasoning_trace["summary"] = summary_raw
            break
        elif getattr(item, "type", None) in ("function_call", "tool_call", "function"):
            name = getattr(item, "name", None)
            args = getattr(item, "arguments", None)
            if name == "generate_interaction" and args:
                # Parser avec Pydantic
                parsed_output = response_model.model_validate_json(args)
                break
    
    # Métriques
    input_tokens = getattr(response.usage, "input_tokens", 0) or 0
    output_tokens = getattr(response.usage, "output_tokens", 0) or 0
    total_tokens = input_tokens + output_tokens
else:
    # Chat Completions (pour les autres modèles)
    response = await client.chat.completions.create(
        model=model_name,
        messages=[...],
        tools=[...],
        tool_choice={...},
        max_completion_tokens=1500,
        temperature=0.7
    )
    
    # Extraction classique
    if response.choices[0].message.tool_calls:
        tool_call = response.choices[0].message.tool_calls[0]
        parsed_output = response_model.model_validate_json(tool_call.function.arguments)
    
    # Métriques
    prompt_tokens = response.usage.prompt_tokens or 0
    completion_tokens = response.usage.completion_tokens or 0
    total_tokens = response.usage.total_tokens or 0
```

## Références

- Code d'implémentation: `llm_client.py::OpenAIClient.generate_variants()`
- Configuration des modèles: `llm_config.json`, `constants.py::ModelNames`
- Schémas API: `api/schemas/dialogue.py::GenerateUnityDialogueRequest`
- Interface frontend: `frontend/src/components/generation/ReasoningTraceViewer.tsx`
