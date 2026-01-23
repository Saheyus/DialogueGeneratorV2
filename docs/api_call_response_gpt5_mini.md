# Documentation API OpenAI - GPT-5 Mini Reasoning

## Date
2025-01-22

## Modèle
`gpt-5-mini-2025-08-07`

## Appel API Complet

### Endpoint
`POST /v1/responses`

### Paramètres de la requête

```json
{
  "model": "gpt-5-mini",
  "input": [
    {
      "role": "system",
      "content": "Tu es un dialoguiste expert en jeux de rôle narratifs.\n\nRÈGLES D'INTERPRÉTATION DU CONTEXTE :\n- Si une section \"VOIX ET STYLE\" est présente dans le contexte, respecte strictement le profil de voix fourni\n- Si une section \"CARACTÉRISATION\" est présente, exploite les qualités, défauts, désirs et faiblesses pour enrichir les dialogues\n\nPRINCIPES FONDAMENTAUX :\n- Tu écris directement les dialogues.\n- Uniquement lorsque c'est nécessaire, tu utilises des didascalies minimales et purement fonctionnelles..."
    },
    {
      "role": "user",
      "content": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<prompt>...</prompt>"
    }
  ],
  "tools": [
    {
      "type": "function",
      "name": "generate_interaction",
      "description": "Génère une interaction de dialogue structurée.",
      "parameters": {
        "type": "object",
        "properties": {
          "title": {
            "type": "string",
            "description": "Titre descriptif du dialogue"
          },
          "node": {
            "$ref": "#/$defs/UnityDialogueNodeContent",
            "description": "Un seul nœud de dialogue généré par l'IA"
          }
        },
        "required": ["title", "node"],
        "additionalProperties": false
      }
    }
  ],
  "tool_choice": {
    "type": "allowed_tools",
    "mode": "required",
    "tools": [
      {
        "type": "function",
        "name": "generate_interaction"
      }
    ]
  },
  "max_output_tokens": 15100,
  "reasoning": {
    "effort": "low",
    "summary": "detailed"
  }
}
```

## Réponse API Complète

### Structure générale

```json
{
  "id": "resp_07c9c6ba91c2c55d0069713ca8b5dc8196b1a9c8cfc4eca96e",
  "created_at": 1769028776.0,
  "model": "gpt-5-mini-2025-08-07",
  "object": "response",
  "status": "completed",
  "reasoning": {
    "effort": "low",
    "summary": "detailed",
    "generate_summary": null
  },
  "output": [
    {
      "id": "rs_07c9c6ba91c2c55d0069713ca91f888196a2576468c0c49a25",
      "type": "reasoning",
      "summary": [],
      "content": null,
      "encrypted_content": null,
      "status": null
    },
    {
      "id": "fc_07c9c6ba91c2c55d0069713cad6a588196a036cf1acb94b308",
      "type": "function_call",
      "name": "generate_interaction",
      "call_id": "call_wgtVDRTM0NBBZnrL8SzrvYVc",
      "status": "completed",
      "arguments": "{...JSON du dialogue généré...}"
    }
  ],
  "usage": {
    "input_tokens": 6604,
    "input_tokens_details": {
      "cached_tokens": 5504
    },
    "output_tokens": 579,
    "output_tokens_details": {
      "reasoning_tokens": 256
    },
    "total_tokens": 7183
  }
}
```

