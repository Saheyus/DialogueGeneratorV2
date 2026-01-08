# Analyse des paramètres OpenAI utilisés dans l'application

**Date**: 2026-01-02  
**Modèle par défaut**: GPT-5.2  
**API utilisée**: Chat Completions (pas Responses API)

## Résumé exécutif

L'application utilise l'API **Chat Completions** d'OpenAI avec GPT-5.2 comme modèle par défaut. Les paramètres actuellement utilisés sont limités à `temperature` et `max_tokens`/`max_completion_tokens`. Plusieurs paramètres avancés disponibles dans l'API OpenAI ne sont pas utilisés, et certains ne sont disponibles que via la Responses API.

---

## Paramètres actuellement utilisés

### ✅ Temperature
- **Statut**: ✅ Utilisé conditionnellement
- **Source**: `llm_config.json` (défaut: 0.7) ou configuration par modèle
- **Code**: `llm_client.py:146, 292-295`
- **Comportement**: 
  - Ajouté seulement si le modèle le supporte
  - Exclu pour `gpt-5-mini` et `gpt-5-nano` (voir `constants.py:56`)
  - Vérification: `ModelNames.MODELS_WITHOUT_CUSTOM_TEMPERATURE`
- **Exposition API/UI**: ❌ Non exposé (valeur statique dans config)

### ✅ Max Tokens / Max Completion Tokens
- **Statut**: ✅ Utilisé
- **Source**: `llm_config.json` (défaut: 2000) ou `max_completion_tokens` dans les requêtes
- **Code**: `llm_client.py:147, 297-315`
- **Comportement**:
  - Pour modèles GPT-5.x: utilise `max_completion_tokens`
  - Pour modèles thinking (mini, nano): minimum 10k tokens par défaut
  - Pour anciens modèles: utilise `max_tokens`
- **Exposition API/UI**: ✅ Exposé via `GenerateUnityDialogueRequest.max_completion_tokens`

### ✅ Tools / Function Calling (Structured Output)
- **Statut**: ✅ Utilisé pour structured output
- **Code**: `llm_client.py:216-246`
- **Comportement**:
  - Convertit le modèle Pydantic en JSON Schema
  - Utilise `tools` et `tool_choice` pour forcer l'appel de fonction
  - Garantit la structure JSON de la réponse

---

## Paramètres disponibles mais non utilisés

### ❌ Top P
- **Statut**: ❌ Non implémenté
- **Disponibilité**: 
  - Chat Completions: ✅ Disponible pour tous les modèles
  - Responses API: ✅ Disponible uniquement avec `reasoning.effort: "none"`
- **Utilité**: Contrôle la diversité des réponses (alternative/complément à temperature)
- **Impact**: Faible (temperature suffit généralement)

### ❌ Frequency Penalty
- **Statut**: ❌ Non implémenté
- **Disponibilité**: 
  - Chat Completions: ✅ Disponible pour tous les modèles
  - Responses API: ❌ Non disponible
- **Utilité**: Réduit la répétition de tokens
- **Impact**: Moyen (utile pour éviter les répétitions dans les dialogues)

### ❌ Presence Penalty
- **Statut**: ❌ Non implémenté
- **Disponibilité**: 
  - Chat Completions: ✅ Disponible pour tous les modèles
  - Responses API: ❌ Non disponible
- **Utilité**: Encourage l'utilisation de nouveaux tokens
- **Impact**: Moyen (utile pour la créativité)

### ❌ Logprobs
- **Statut**: ❌ Non implémenté
- **Disponibilité**: 
  - Chat Completions: ✅ Disponible pour certains modèles
  - Responses API: ✅ Disponible uniquement avec `reasoning.effort: "none"`
- **Utilité**: Retourne les probabilités des tokens (debug, analyse)
- **Impact**: Faible (principalement pour debug)

---

## Paramètres disponibles uniquement via Responses API

### ❌ Reasoning Effort
- **Statut**: ❌ Non disponible (Chat Completions uniquement)
- **Disponibilité**: Responses API uniquement
- **Valeurs**: `"none" | "low" | "medium" | "high" | "xhigh"`
- **Utilité**: Contrôle la profondeur de raisonnement du modèle
- **Impact**: Élevé (améliorerait la qualité pour tâches complexes)
- **Note**: L'application utilise Chat Completions, donc ce paramètre n'est pas accessible

### ❌ Verbosity
- **Statut**: ❌ Non disponible (Chat Completions uniquement)
- **Disponibilité**: Responses API uniquement
- **Valeurs**: `"low" | "medium" | "high"`
- **Utilité**: Contrôle la longueur des réponses (alternative à max_tokens)
- **Impact**: Moyen (utile pour contrôler la verbosité sans limiter strictement)

### ❌ Previous Response ID (CoT)
- **Statut**: ❌ Non disponible (Chat Completions uniquement)
- **Disponibilité**: Responses API uniquement
- **Utilité**: Passe le chain-of-thought précédent pour éviter re-raisonnement
- **Impact**: Élevé (améliorerait la latence et le cache hit rate)
- **Note**: L'application utilise `previous_dialogue_context` mais pas le CoT optimisé

---

## Compatibilité avec GPT-5.2

### Chat Completions (API actuelle)
- ✅ `temperature`: Supporté (uniquement si `reasoning.effort: "none"` en Responses API, mais en Chat Completions c'est toujours disponible)
- ✅ `top_p`: Supporté
- ✅ `max_tokens` / `max_completion_tokens`: Supporté
- ✅ `frequency_penalty`: Supporté
- ✅ `presence_penalty`: Supporté
- ✅ `tools` / `tool_choice`: Supporté (structured output)
- ❌ `reasoning.effort`: Non disponible
- ❌ `verbosity`: Non disponible
- ❌ `previous_response_id`: Non disponible

### Responses API (non utilisée)
- ✅ `reasoning.effort`: Disponible (`none`, `low`, `medium`, `high`, `xhigh`)
- ✅ `verbosity`: Disponible (`low`, `medium`, `high`)
- ✅ `previous_response_id`: Disponible (passe CoT entre tours)
- ⚠️ `temperature` / `top_p` / `logprobs`: Uniquement avec `reasoning.effort: "none"`
- ✅ `max_output_tokens`: Disponible (alternative à max_tokens)

---

## Recommandations

### Priorité haute

1. **Exposer `temperature` dans l'API/UI**
   - **Complexité**: Faible
   - **Impact**: Moyen
   - **Action**: Ajouter `temperature: Optional[float]` dans `BasePromptRequest` ou `GenerateUnityDialogueRequest`
   - **Code**: `llm_client.py:292-295` (déjà gère la compatibilité par modèle)

2. **Ajouter `frequency_penalty` et `presence_penalty`**
   - **Complexité**: Faible
   - **Impact**: Moyen (réduit répétitions, améliore créativité)
   - **Action**: Ajouter dans les schémas API et passer à `chat.completions.create()`
   - **Note**: Disponibles dans Chat Completions, pas besoin de Responses API

### Priorité moyenne

3. **Évaluer la migration vers Responses API**
   - **Complexité**: Élevée
   - **Impact**: Élevé (reasoning effort, verbosity, CoT optimisé)
   - **Avantages**:
     - Meilleure intelligence grâce au CoT entre tours
     - Moins de reasoning tokens générés
     - Cache hit rate plus élevé
     - Latence réduite
   - **Inconvénients**:
     - Refactoring nécessaire (`client.responses.create()` au lieu de `client.chat.completions.create()`)
     - Format de réponse différent
     - `temperature`/`top_p` uniquement avec `reasoning.effort: "none"`
   - **Recommandation**: Évaluer après avoir exposé les paramètres Chat Completions

### Priorité basse

4. **Ajouter `top_p`**
   - **Complexité**: Faible
   - **Impact**: Faible (temperature suffit généralement)
   - **Action**: Similaire à `temperature`

5. **Ajouter `logprobs` (debug uniquement)**
   - **Complexité**: Faible
   - **Impact**: Très faible (debug uniquement)
   - **Action**: Optionnel, pour analyse des réponses

---

## État actuel du code

### Fichiers clés

- **`llm_client.py`**: Client OpenAI, gestion des paramètres
- **`config/llm_config.json`**: Configuration par défaut (temperature, max_tokens)
- **`constants.py`**: Modèles et leurs limitations
- **`api/schemas/dialogue.py`**: Schémas de requête API
- **`factories/llm_factory.py`**: Création de clients avec config par modèle

### Points d'extension

1. **Ajout de paramètres dans `llm_client.py`**:
   ```python
   # Ligne 283-295: Zone où les paramètres API sont construits
   api_params = {
       "model": self.model_name,
       "messages": messages,
       "n": 1,
       "tools": [tool_definition] if tool_definition else NOT_GIVEN,
       "tool_choice": tool_choice_option,
   }
   # Ajouter ici: frequency_penalty, presence_penalty, top_p
   ```

2. **Ajout dans les schémas API** (`api/schemas/dialogue.py`):
   ```python
   class BasePromptRequest(BaseModel):
       # ... champs existants ...
       temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Temperature pour la génération")
       frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0, description="Pénalité de fréquence")
       presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0, description="Pénalité de présence")
   ```

3. **Passage au client LLM** (`api/routers/dialogues.py`):
   ```python
   # Ligne 328: Zone où le client est configuré
   if request_data.temperature is not None:
       llm_client.temperature = request_data.temperature
   ```

---

## Conclusion

L'application utilise actuellement une configuration minimale des paramètres OpenAI (temperature, max_tokens, structured output). Plusieurs paramètres utiles sont disponibles dans Chat Completions mais non utilisés (`frequency_penalty`, `presence_penalty`, `top_p`). 

La migration vers Responses API apporterait des avantages significatifs (reasoning effort, verbosity, CoT optimisé) mais nécessite un refactoring important.

**Recommandation immédiate**: Exposer `temperature`, `frequency_penalty`, et `presence_penalty` dans l'API/UI pour un contrôle fin sans migration majeure.
