# ADR-005: RLM Context Selector (Autonomous Context Selection)

**Date:** 2026-01-17  
**Status:** ✅ Proposed  
**Deciders:** Architecture Team  
**Tags:** #context-selection #llm #rlm #gdd #optimization

---

## Context

Sélection manuelle de contexte GDD est **cognitivement coûteuse et error-prone** :

- Scène "minimale" (2 personnages + 1 lieu) fait déjà **15-20k tokens** en mode full
- Utilisateur doit décider manuellement quelles fiches inclure et en quel mode (full/excerpt)
- Risque d'oublier éléments pertinents (liens cosmologiques, factions, objets rituels)
- Granularité trop grossière : fiche "full" = 6-8k tokens, même si seule une section est pertinente

**Problème fondamental :** Avec des contextes de 20k+ tokens, même avec fenêtres 128k, les effets de dégradation OOLONG apparaissent (attention diluée, dépendances longues brouillées, rappel précis dégradé). Le vrai problème n'est pas "comment choisir quelles fiches charger" mais **"comment raisonner sur un univers dont la scène active pèse déjà 20k tokens"**.

**Référence académique :** Recursive Language Models (RLM) - arXiv:2512.24601 - Paradigme où le LLM ne "voit" jamais tout le contexte, mais navigue, lit par tranches, résume, ré-interroge, vérifie localement, agrège récursivement.

---

## Decision

Implémenter une **couche optionnelle (on/off) de LLM "sélecteur autonome de contexte"** inspirée du paradigme **Recursive Language Models (RLM)** :

- Le système devient l'agent de sélection (exploration programmatique + déductions)
- L'utilisateur devient superviseur (valide/ajuste, avec mode override)
- Réduction contextuelle intelligente : 20k+ tokens → 12-15k tokens sans perte de pertinence

---

## Technical Design

### Phase 1. Context Selection (RLM Agent)

**Service Backend:**
```python
# services/rlm_context_selector.py
class RLMContextSelector:
    async def select_context(
        self,
        user_instructions: str,  # Instructions de Scène
        hints: Optional[Dict[str, List[str]]] = None,  # Optionnel : verrouiller éléments
        hints_mode: Optional[Dict[str, str]] = None,  # {"character_A": "full"}
        exclude: Optional[List[str]] = None,  # IDs à exclure
        expansion_radius: int = 1,  # 0=aucune, 1=graphe direct, 2=indirect
        max_tokens_target: int = 15000,  # Budget global
        seed: Optional[int] = None,  # Reproductibilité
    ) -> ContextSelectionResult:
        # 1. Parse user_instructions pour extraire entités explicites
        # 2. Exploration outillée (search_bm25, get_related, get_snippet, etc.)
        # 3. Déductions (liens cosmologiques, factions, objets rituels, etc.)
        # 4. Décision full/excerpt + section_filters pour chaque fiche
        # 5. Budget check (si dépassement, passer plus en excerpt ou exclure)
        # 6. Retourner selected_elements + justifications + trace
```

**Outils GDD (exposés au LLM via function calling via `GDDToolsProvider`):**
```python
# Outils de navigation JSON
- get_node(id) -> json
- get_fields(id, fields[]) -> json
- list_ids(type=None, where_field_exists=None, limit=...)
- schema_overview() -> stats + exemples

# Outils de recherche
- search_bm25(query, top_k=20, filter_type=None) -> [{id, score, snippet}]
- search_regex(pattern, field=None, top_k=20) -> matches
- search_by_key_value(key, value, exact=True)

# Outils d'extraction contrôlée
- get_snippet(id, field, max_chars=2000, around=None)
- get_related(id, relation_keys=[...], depth=1)
- get_relation_chunks(source_id, target_id, relation_field="Relations") -> Dict[str, Any]  # <-- NOUVEAU: Chunks ciblés

# Outils d'agrégation
- count(filter...)
- group_by(field, filter...)
- build_table(ids, columns) -> rows
- diff(id_a, id_b, fields)
```

**Limites RLM Agent:**
```python
MAX_TOOL_CALLS = 50  # Limite absolue appels outils
MAX_EXPLORATION_TOKENS = 100000  # Budget max exploration (modèle mini, coût faible)
```

**Output Phase 1:**
```python
{
  "selected_elements": {
    "characters": {
      "Uresaïr": {
        "mode": "full",
        "section_filters": {
          "include": ["Psychologie", "Arc.Actuel", "Relations.Akthar"],
          "exclude": ["Rôle cosmologique complet", "Histoire complète"],
          "reason": "Focus sur dynamique relationnelle et état émotionnel"
        },
        "field_filters": {  # <-- NOUVEAU: Granularité chunks ciblés (Phase 2)
          "Relations": {
            "mode": "intersection",
            "related_elements": ["Akthar"],
            "reason": "Extrait uniquement relations communes entre Uresaïr et Akthar"
          }
        },
        "justification": {
          "reason": "hint_explicit",
          "proof": None
        }
      },
      "Akthar": {
        "mode": "full",
        "section_filters": {
          "include": ["Psychologie", "Relations.Uresaïr", "Croyances"],
          "exclude": ["Rôle cosmologique complet"]
        },
        "justification": {
          "reason": "hint_explicit",
          "proof": None
        }
      }
    },
    "locations": {
      "Nef Centrale": {
        "mode": "full",
        "section_filters": {...},
        "justification": {
          "reason": "mentioned_explicitly",
          "proof": "Scène se déroule dans la Nef Centrale"
        }
      },
      "Léviathan Pétrifié": {
        "mode": "excerpt",
        "justification": {
          "reason": "deduction_context_cosmologique",
          "proof": "Léviathan mentionné comme cadre cosmologique dans Uresaïr.sections.Rôle",
          "search_trace": ["get_related('Uresaïr')", "search_by_key_value('type', 'lieu_cosmologique')"]
        }
      }
    }
  },
  "trace": {
    "tools_called": ["search_bm25", "get_related", "get_snippet", ...],
    "decisions": [...],
    "total_tokens_estimated": 12000  # Optimisé vs 20k+ en manuel
  }
}
```

### Phase 2. Context Build (inchangé mais enrichi)

**Integration avec ContextFieldManager:**
```python
# services/context_field_manager.py
def filter_fields_by_section_filters(
    self,
    element_type: str,
    fields_to_include: List[str],
    section_filters: Optional[Dict[str, Any]] = None  # <-- ENRICHI: include/exclude + field_filters
) -> List[str]:
    """
    section_filters peut contenir:
    {
      "include": ["Relations.Akthar"],      # Sous-sections à inclure
      "exclude": ["Rôle cosmologique"],     # Sous-sections à exclure
      "field_filters": {                     # NOUVEAU (Phase 2): Chunks ciblés
        "Relations": {
          "mode": "intersection",            # Relations communes
          "related_elements": ["Akthar"]
        }
      }
    }
    """
    # 1. Appliquer include/exclude (niveau sous-section) ✅
    # 2. Appliquer field_filters (niveau chunk) si présent 🆕
    # 3. Extraire chunks ciblés via get_relation_chunks() si field_filters 🆕
    # Combine règles statiques (context_config.json) + règles dynamiques (section_filters)
    # Sans bypasser le DSL de champs existant
```

**Backend API:**
```python
# api/routers/context.py
@router.post("/select-context", response_model=SelectContextResponse)
async def select_context_auto(
    request_data: SelectContextRequest,
    rlm_selector: Annotated[RLMContextSelector, Depends(get_rlm_context_selector)],
) -> SelectContextResponse:
    # Phase 1 : RLM sélection automatique
    selection_result = await rlm_selector.select_context(
        user_instructions=request_data.user_instructions,
        hints=request_data.hints,
        ...
    )
    # Phase 2 : build_context_json (inchangé)
    structured_context = context_builder.build_context_json(
        selected_elements=selection_result.selected_elements,
        scene_instruction=request_data.user_instructions,
        ...
    )
    return SelectContextResponse(
        selected_elements=selection_result.selected_elements,
        context=structured_context,
        trace=selection_result.trace
    )
```

**Frontend UI:**
- Toggle "Auto Selection" (on/off) dans panneau contexte
- Affichage "Contexte auto-sélectionné" avec justifications cliquables
- Mode "Override" : utilisateur peut forcer/ajouter des éléments même en auto
- Mode "Lock" : utilisateur peut verrouiller certains éléments (toujours inclus)

---

## Constraints

- **DOIT** être optionnel (on/off), avec fallback vers sélection manuelle
- **DOIT** rester compatible avec `ContextFieldManager`, `ContextTruncator`, `ContextSerializer`
- **NE DOIT PAS** bypasser `build_context_json()` (Option A, pas Option B)
- **DOIT** produire `selected_elements` avec `section_filters` enrichis
- **DOIT** inclure `justification` et `trace` pour traçabilité
- **DOIT** respecter hints explicites (toujours inclus, mode full par défaut)
- **DOIT** être reproductible (seed optionnel) ou au minimum traçable
- **DOIT** gérer fallback gracieux (si RLM échoue, retourner hints uniquement, pas d'erreur)

---

## Rationale

### Réduction friction
- Plus besoin de sélection manuelle laborieuse (10+ clics → 1 clic "Auto")
- Amélioration recall : RLM trouve éléments pertinents que l'utilisateur aurait oubliés

### Granularité adaptative
- **Phase 1 (MVP)** : Sélection fine de sous-sections (ex: Uresaïr 6k → 2-3k tokens) sans perte pertinence
- **Phase 2 (Amélioration)** : Chunks ciblés dans sous-sections (ex: relations communes entre 2 personnages, 200 tokens vs 2000 tokens pour "Relations" complet)
- Réduction contextuelle intelligente : 20k+ → 12-15k tokens (Phase 1) → 6-10k tokens (Phase 2 avec chunks)

### Paradigme RLM
- Navigation programmatique du GDD, lecture récursive, mémoire de travail compacte, agrégation progressive
- Résout problème fondamental : contexte massif → environnement informationnel navigable

### Compatible existant
- S'intègre proprement avec `ContextBuilder` sans casser invariants
- Phase 2 utilise toujours `build_context_json()` (pas de bypass)

---

## Risks

### Non-déterminisme
- Agent peut choisir trajectoire différente (mitigation : seed + cache + traçabilité)

### Sélection inattendue
- RLM peut inclure éléments non souhaités (mitigation : override + lock + exclusions)

### Coût LLM
- Exploration outillée = plusieurs appels LLM (mitigation : budget séparé 100k tokens + cache + modèle GPT-5-mini pour sélection)

### Latence
- Sélection automatique ajoute délai avant génération (mitigation : cache + streaming progress)

### Tests
- Agent loop difficile à tester sans fixtures synthétiques (mitigation : tests avec mini-GDD + mocks LLM)

---

## Tests Required

### Unit
- `RLMContextSelector.select_context()` avec mocks LLM
- `ContextFieldManager.filter_fields_by_section_filters()` combine règles

### Integration
- `/api/v1/context/select-context` avec vrai LLM (tests coûteux, limiter)
- Fallback gracieux si RLM échoue

### E2E
- Workflow complet auto-selection → build_context → génération

---

## Acceptance Criteria

- [ ] Toggle "Auto Selection" dans UI contexte
- [ ] RLM produit `selected_elements` avec `section_filters`
- [ ] Phase 2 `build_context_json()` utilise `section_filters` correctement
- [ ] Réduction tokens : 20k+ → 12-15k sans perte pertinence
- [ ] Justifications affichées (utilisateur peut comprendre pourquoi élément inclus)
- [ ] Mode override fonctionne (ajout/force éléments même en auto)
- [ ] Fallback gracieux si RLM échoue (pas d'erreur, retourne hints uniquement)
- [ ] Traçabilité complète (trace contient trajectoire agent)

---

## Open Questions (Résolues)

1. **Modèle LLM pour sélection ?** ✅ **GPT-5-mini** recommandé (coût réduit, qualité suffisante pour sélection vs génération)
2. **Budget exploration ?** ✅ **100k tokens max** (modèle mini, coût très faible, séparé de budget génération)
3. **Cache sélections ?** ✅ **TTL 24h** recommandé (hash `user_instructions + sorted(hints) + expansion_radius + max_tokens_target`)
4. **Section filters granularité ?** ✅ **Sous-section pour MVP** (Phase 1), **Chunks ciblés pour Phase 2** (field_filters avec get_relation_chunks)
5. **Intégration embeddings ?** ✅ **BM25 suffit pour MVP** (vector search = V2.0 si recall insuffisant)

---

## Alternatives Considered

### Alternative 1 : Sélection manuelle uniquement
- **Rejeté** : Trop cognitivement coûteux, error-prone, ne résout pas problème dilution

### Alternative 2 : RAG classique (embedding + retrieval)
- **Rejeté** : Ne résout pas granularité (fiche complète vs sous-sections), pas de déductions

### Alternative 3 : Agent libre (full RLM avec contexte prêt prompt)
- **Rejeté** : Bypasserait `build_context_json()`, casserait invariants, trop complexe

### Alternative 4 : Pipeline déterministe (rules-based selection)
- **Considéré** : Plus simple, plus testable, mais moins flexible, ne résout pas granularité fine

### Alternative 5 : Granularité paragraphe (chunks à la volée)
- **Considéré** : Trop complexe MVP, granularité sous-section + chunks ciblés (Phase 2) suffit pour réduction tokens

---

## Consequences

### Positives
- Réduction significative friction utilisateur
- Amélioration recall (éléments pertinents non oubliés)
- Réduction tokens contexte (20k+ → 12-15k)
- Compatibilité avec architecture existante

### Négatives
- Complexité ajoutée (nouveau service RLM)
- Coût LLM supplémentaire (exploration outillée)
- Latence ajoutée (sélection automatique)
- Non-déterminisme (mitigation : seed + cache)

---

## Implementation Recommendations

### Architecture

**Abstraction GDDToolsProvider:**
```python
# services/gdd_tools_provider.py (NOUVEAU)
class GDDToolsProvider:
    """Wrapper pour exposer outils GDD au LLM via function calling."""
    def __init__(self, element_repository: ElementRepository):
        self._repo = element_repository
    
    def get_relation_chunks(
        self,
        source_id: str,
        target_id: str,
        relation_field: str = "Relations"
    ) -> Dict[str, Any]:
        """Extrait uniquement les relations communes entre deux personnages.
        
        Exemple: Uresaïr.Relations.Akthar (chunk commun) vs Uresaïr.Relations complet.
        Réduction tokens: 200 tokens vs 2000 tokens pour "Relations" complet.
        """
        # 1. Récupérer source_data et target_data via element_repository
        # 2. Extraire relations communes (intersection)
        # 3. Retourner chunks ciblés uniquement
```

**Limites RLM Agent:**
```python
class RLMContextSelector:
    MAX_TOOL_CALLS = 50  # Limite absolue appels outils (éviter boucles infinies)
    MAX_EXPLORATION_TOKENS = 100000  # Budget max exploration (modèle mini, coût faible)
    
    async def select_context(...) -> ContextSelectionResult:
        tool_call_count = 0
        exploration_tokens = 0
        
        while tool_call_count < MAX_TOOL_CALLS:
            # ... LLM loop ...
            tool_call_count += 1
            exploration_tokens += estimated_tokens
            
            if exploration_tokens > MAX_EXPLORATION_TOKENS:
                logger.warning("Budget exploration dépassé, utilisation hints uniquement")
                return self._fallback_to_hints(hints)
```

### Phase Implementation

**Phase 1 (MVP):**
- RLM service avec granularité **sous-section** (`section_filters.include/exclude`)
- GDDToolsProvider abstraction (outils GDD pour LLM)
- Extension `ContextFieldManager.filter_fields_by_section_filters()`
- Router `/api/v1/context/select-context`
- Frontend toggle "Auto Selection"

**Phase 2 (Amélioration):**
- Granularité **chunks ciblés** (`field_filters` avec `get_relation_chunks()`)
- Validation sections existantes (warnings, pas erreurs)
- Cache sélections (TTL 24h)
- Tests E2E complets

### File Structure

**Backend:**
```
services/
  ├── rlm_context_selector.py        # NEW: RLM orchestration
  ├── gdd_tools_provider.py          # NEW: Outils GDD pour LLM
  └── context_field_manager.py       # MODIFY: filter_fields_by_section_filters()

api/
  ├── routers/
  │   └── context.py                 # MODIFY: /select-context endpoint
  └── schemas/
      └── context.py                 # NEW: SelectContextRequest/Response
```

**Frontend:**
```
frontend/src/
  ├── components/generation/
  │   └── ContextSelector.tsx        # MODIFY: Toggle "Auto Selection"
  ├── store/
  │   └── generationStore.ts         # MODIFY: autoSelection state
  └── api/
      └── context.ts                 # MODIFY: selectContext() API call
```

**Tests:**
```
tests/
  ├── services/
  │   ├── test_rlm_context_selector.py    # NEW
  │   └── test_gdd_tools_provider.py      # NEW
  └── api/
      └── test_context.py                 # MODIFY: /select-context tests
```

## References

- **Recursive Language Models (RLM)** - arXiv:2512.24601 - Alex L. Zhang, Tim Kraska, Omar Khattab
- **Context Rot** - Hong et al., 2025
- **Baleen** - Khattab et al., 2021 (retrieval-augmented generation)
