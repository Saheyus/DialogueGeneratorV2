# V1.0 Architectural Decisions (ADRs)

### ADR-001: Progress Feedback Modal (Streaming LLM)

**Context:**  
UI "gel" pendant génération LLM (30s+), pas de feedback utilisateur → UX critique bloquante

**Decision:**  
Modal centrée avec streaming SSE (Server-Sent Events)

**Technical Design:**

**Frontend:**
- Nouveau composant `GenerationProgressModal.tsx`
- State : Zustand slice `useGenerationStore` (état streaming)
- API : EventSource SSE vers `/api/v1/generate/stream`
- UI : 2 zones (sortie LLM stream + étapes/logs), 2 actions (Interrompre/Réduire)

**Backend:**
- Nouveau router `/api/v1/generate/stream` (SSE endpoint)
- Pattern : `async def` generator avec `yield` (chunks SSE)
- LLM : `stream=True` sur `responses.create()` (GPT-5.2)
- Format : `data: {"type": "chunk", "content": "..."}\n\n`

**Constraints:**
- **DOIT** utiliser Zustand (pattern existant state management)
- **DOIT** respecter format SSE (`data: ...\n\n`)
- **NE DOIT PAS** modifier panneau Détails (trop étroit, modal nécessaire)
- **DOIT** gérer interruption propre (AbortController frontend + cleanup backend)

**Rationale:**
- SSE > WebSocket (unidirectionnel, plus simple, fallback HTTP)
- Modal > panneau intégré (340px insuffisant, focus utilisateur)
- Streaming natif GPT-5.2 Responses API (pas de polling)

**Risks:**
- SSE timeout long génération (mitigation : keep-alive pings)
- Gestion erreurs stream interrompu (mitigation : error events SSE)

**Tests Required:**
- Unit : `useGenerationStore` state transitions
- Integration : `/api/v1/generate/stream` SSE format
- E2E : Modal affichage + interruption mid-stream

**Acceptance Criteria:**
- [ ] Modal visible dès clic "Générer"
- [ ] Sortie LLM streamée en temps réel (<500ms latency)
- [ ] Bouton "Interrompre" arrête génération proprement
- [ ] Fermeture modal restaure UI précédente

---

### ADR-002: Presets système (Configuration sauvegarde/chargement)

**Context:**  
Cold start friction : 10+ clics pour premier dialogue (sélection personnages, lieux, instructions)

**Decision:**  
Système presets avec sauvegarde/chargement configurations complètes

**Technical Design:**

**Data Model:**
```typescript
interface Preset {
  id: string;
  name: string;
  icon: string; // emoji
  metadata: {
    created: Date;
    modified: Date;
  };
  configuration: {
    characters: string[];      // IDs sélectionnés
    locations: string[];
    region: string;
    subLocation?: string;
    sceneType: string;         // "Première rencontre", etc.
    instructions: string;      // Brief scène
  };
}
```

**Frontend:**
- Nouveau composant `PresetBar.tsx` (barre compacte au-dessus "Scène Principale")
- 2 boutons : "📋 Charger preset ▼" (dropdown) + "💾 Sauvegarder preset"
- Modal sauvegarde : nom, icône emoji, aperçu lecture seule
- State : Zustand slice `usePresetStore`

**Backend:**
- Nouveau router `/api/v1/presets` (CRUD)
- Storage : Fichiers JSON locaux `data/presets/{preset_id}.json`
- Service : `PresetService` (validation, persistence)

**Constraints:**
- **DOIT** capturer configuration complète (personnages + lieux + instructions)
- **DOIT** valider IDs références (personnages/lieux existent dans GDD)
- **NE DOIT PAS** stocker contenu GDD (seulement IDs)
- **DOIT** gérer preset obsolète (références GDD supprimées)

**Rationale:**
- Cold start → 1 clic (objectif efficiency V1.0)
- Stockage local (pas besoin DB, Git-friendly)
- Validation lazy (au chargement, pas à la sauvegarde)

**Risks:**
- GDD updates rendent presets obsolètes (mitigation : validation chargement + warning)
- Synchronisation multi-utilisateurs (hors scope MVP, V2.0 RBAC)

**Tests Required:**
- Unit : `PresetService` validation + persistence
- Integration : API `/api/v1/presets` CRUD
- E2E : Workflow complet sauvegarde → chargement → génération

**Acceptance Criteria:**
- [ ] Bouton "Sauvegarder preset" capture configuration actuelle
- [ ] Modal sauvegarde : nom + icône + aperçu
- [ ] Dropdown "Charger preset" liste presets disponibles
- [ ] Chargement preset restaure configuration complète
- [ ] Warning si références GDD invalides

---

### ADR-003: Graph Editor Fixes (DisplayName vs stableID)

**Context:**  
Bug critique : DisplayName utilisé comme ID au lieu de stableID → corruption graphe

**Decision:**  
Correction immédiate + tests régression

**Technical Design:**

**Root Cause:**
- React Flow utilise `node.id` comme identifiant unique
- Code actuel : `node.id = displayName` (peut changer, collisions)
- Correct : `node.id = stableID` (UUID immuable)

**Fix:**
```typescript
// Avant (BUGGY)
const node = {
  id: dialogue.displayName,  // ❌ Mutable, collisions
  data: { ... }
};

// Après (CORRECT)
const node = {
  id: dialogue.stableID,      // ✅ UUID immuable
  data: { 
    displayName: dialogue.displayName,  // Affiché dans UI
    ...
  }
};
```

**Impact Analysis:**
- Fichiers : `frontend/src/components/graph/GraphEditor.tsx`
- Composants : Node rendering, edge connections
- State : Zustand store `useGraphStore`

**Constraints:**
- **DOIT** migrer données existantes (stableID manquants → génération UUID)
- **NE DOIT PAS** casser graphes existants (backward compatibility)
- **DOIT** ajouter tests régression (collision displayName)

**Rationale:**
- Stabilité identifiants = graphe robuste
- Séparation ID technique (UUID) vs display (nom éditable)

**Risks:**
- Migration données existantes (mitigation : script migration + backup)
- Edge cases (nœuds sans stableID) (mitigation : génération UUID automatique)

**Tests Required:**
- Unit : `generateStableID()` unicité
- Integration : Graph serialization/deserialization
- E2E : Renommer dialogue ne casse pas connexions

**Acceptance Criteria:**
- [ ] `node.id` utilise `stableID` (UUID)
- [ ] Renommer dialogue preserve connexions
- [ ] Aucun graphe existant corrompu après migration
- [ ] Tests régression collisions displayName

---

### ADR-004: Multi-Provider LLM Support (Mistral Small Creative)

**Context:**  
Actuellement, DialogueGenerator utilise uniquement OpenAI GPT-5.2. Besoin d'ajouter Mistral Small Creative comme alternative sélectionnable pour offrir plus de flexibilité et réduire la dépendance à un seul provider.

**Decision:**  
Implémenter abstraction multi-provider avec support OpenAI (GPT-5.2) + Mistral (Small Creative) en V1.0. Utilisateur peut sélectionner le modèle via UI.

**Technical Design:**

**Backend Abstraction:**
- Interface `IGenerator` existante étendue pour supporter multiple providers
- Nouveau service `services/llm/mistral_client.py` implémentant `IGenerator`
- Factory pattern : `LLMFactory.create(provider: str, model: str)` retourne client approprié
- Configuration : `config/llm_config.json` définit providers disponibles + modèles

**Provider-Specific Implementations:**
- **OpenAI** : `OpenAIClient` (existant, Responses API GPT-5.2)
- **Mistral** : `MistralClient` (nouveau, Chat Completions API, Small Creative)
  - SDK : `mistralai` Python package
  - Streaming : Support natif via `stream=True`
  - Structured outputs : Via `response_format` (JSON Schema)

**Frontend Model Selection:**
- Nouveau composant `components/generation/ModelSelector.tsx` (dropdown)
- State : Zustand `generationStore.selectedModel` (provider + model)
- Options affichées : "OpenAI GPT-5.2", "Mistral Small Creative"
- Persistence : Préférence sauvegardée dans localStorage

**API Changes:**
- Endpoint `/api/v1/generate/stream` accepte paramètre `model` (optionnel, défaut: OpenAI)
- Format : `?provider=openai&model=gpt-5.2` ou `?provider=mistral&model=small-creative`
- Backward compatible : Si `model` absent, utilise OpenAI (comportement actuel)

**Constraints:**
- **DOIT** maintenir backward compatibility (OpenAI reste défaut)
- **DOIT** utiliser abstraction `IGenerator` (pas de code provider-spécifique dans routers)
- **DOIT** supporter streaming pour tous providers (SSE format identique)
- **DOIT** gérer structured outputs pour tous providers (JSON Schema)
- **NE DOIT PAS** exposer différences providers à l'utilisateur (abstraction complète)

**Rationale:**
- **Flexibilité** : Utilisateur choisit modèle selon besoins (qualité vs coût vs vitesse)
- **Réduction dépendance** : Pas de vendor lock-in, fallback si OpenAI down
- **Cost optimization** : Mistral Small Creative potentiellement moins cher
- **Abstraction propre** : Pattern IGenerator déjà en place, extension naturelle

**Risks:**
- **Différences API** : OpenAI Responses API vs Mistral Chat Completions (mitigation : abstraction IGenerator)
- **Structured outputs** : Formats différents (mitigation : normalisation JSON Schema)
- **Streaming** : Implémentations différentes (mitigation : wrapper uniforme SSE)
- **Cost tracking** : Prix différents par provider (mitigation : cost service multi-provider)

**Tests Required:**
- Unit : `MistralClient` implémente `IGenerator` correctement
- Unit : `LLMFactory` retourne bon client selon provider
- Integration : `/api/v1/generate/stream?provider=mistral` fonctionne
- Integration : Streaming Mistral produit format SSE identique
- E2E : Sélection modèle dans UI → génération avec bon provider

**Acceptance Criteria:**
- [ ] Dropdown "Modèle" dans UI génération
- [ ] Sélection Mistral Small Creative → génération fonctionne
- [ ] Streaming SSE identique pour OpenAI et Mistral
- [ ] Structured outputs fonctionnent pour les deux providers
- [ ] Cost tracking différencié par provider
- [ ] Préférence modèle persistée (localStorage)

---

### ADR-005: RLM Context Selector (Autonomous Context Selection)

**Context:**  
Sélection manuelle de contexte GDD est **cognitivement coûteuse et error-prone** :
- Scène "minimale" (2 personnages + 1 lieu) fait déjà **15-20k tokens** en mode full
- Utilisateur doit décider manuellement quelles fiches inclure et en quel mode (full/excerpt)
- Risque d'oublier éléments pertinents (liens cosmologiques, factions, objets rituels)
- Granularité trop grossière : fiche "full" = 6-8k tokens, même si seule une section est pertinente

**Problème fondamental :** Avec des contextes de 20k+ tokens, même avec fenêtres 128k, les effets de dégradation OOLONG apparaissent (attention diluée, dépendances longues brouillées, rappel précis dégradé). Le vrai problème n'est pas "comment choisir quelles fiches charger" mais **"comment raisonner sur un univers dont la scène active pèse déjà 20k tokens"**.

**Decision:**  
Implémenter une **couche optionnelle (on/off) de LLM "sélecteur autonome de contexte"** inspirée du paradigme **Recursive Language Models (RLM)** (arXiv:2512.24601) :
- Le système devient l'agent de sélection (exploration programmatique + déductions)
- L'utilisateur devient superviseur (valide/ajuste, avec mode override)
- Réduction contextuelle intelligente : 20k+ tokens → 12-15k tokens sans perte de pertinence

**Technical Design:**

**Phase 1. Context Selection (RLM Agent)**

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

**Outils GDD (exposés au LLM via function calling):**
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

# Outils d'agrégation
- count(filter...)
- group_by(field, filter...)
- build_table(ids, columns) -> rows
- diff(id_a, id_b, fields)
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

**Phase 2. Context Build (inchangé mais enrichi)**

**Integration avec ContextFieldManager:**
```python
# services/context_field_manager.py
def filter_fields_by_section_filters(
    self,
    element_type: str,
    fields_to_include: List[str],
    section_filters: Optional[Dict[str, List[str]]] = None  # <-- NOUVEAU
) -> List[str]:
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

**Constraints:**
- **DOIT** être optionnel (on/off), avec fallback vers sélection manuelle
- **DOIT** rester compatible avec `ContextFieldManager`, `ContextTruncator`, `ContextSerializer`
- **NE DOIT PAS** bypasser `build_context_json()` (Option A, pas Option B)
- **DOIT** produire `selected_elements` avec `section_filters` enrichis
- **DOIT** inclure `justification` et `trace` pour traçabilité
- **DOIT** respecter hints explicites (toujours inclus, mode full par défaut)
- **DOIT** être reproductible (seed optionnel) ou au minimum traçable
- **DOIT** gérer fallback gracieux (si RLM échoue, retourner hints uniquement, pas d'erreur)

**Rationale:**
- **Réduction friction** : Plus besoin de sélection manuelle laborieuse (10+ clics → 1 clic "Auto")
- **Amélioration recall** : RLM trouve éléments pertinents que l'utilisateur aurait oubliés
- **Granularité adaptative** : Sélection fine de sous-sections (ex: Uresaïr 6k → 2-3k tokens) sans perte pertinence
- **Paradigme RLM** : Navigation programmatique du GDD, lecture récursive, mémoire de travail compacte, agrégation progressive
- **Compatible existant** : S'intègre proprement avec `ContextBuilder` sans casser invariants

**Risks:**
- **Non-déterminisme** : Agent peut choisir trajectoire différente (mitigation : seed + cache + traçabilité)
- **Sélection inattendue** : RLM peut inclure éléments non souhaités (mitigation : override + lock + exclusions)
- **Coût LLM** : Exploration outillée = plusieurs appels LLM (mitigation : budget séparé + cache + modèle "cheap" pour sélection)
- **Latence** : Sélection automatique ajoute délai avant génération (mitigation : cache + streaming progress)
- **Tests** : Agent loop difficile à tester sans fixtures synthétiques (mitigation : tests avec mini-GDD + mocks LLM)

**Tests Required:**
- Unit : `RLMContextSelector.select_context()` avec mocks LLM
- Unit : `ContextFieldManager.filter_fields_by_section_filters()` combine règles
- Integration : `/api/v1/context/select-context` avec vrai LLM (tests coûteux, limiter)
- Integration : Fallback gracieux si RLM échoue
- E2E : Workflow complet auto-selection → build_context → génération

**Acceptance Criteria:**
- [ ] Toggle "Auto Selection" dans UI contexte
- [ ] RLM produit `selected_elements` avec `section_filters`
- [ ] Phase 2 `build_context_json()` utilise `section_filters` correctement
- [ ] Réduction tokens : 20k+ → 12-15k sans perte pertinence
- [ ] Justifications affichées (utilisateur peut comprendre pourquoi élément inclus)
- [ ] Mode override fonctionne (ajout/force éléments même en auto)
- [ ] Fallback gracieux si RLM échoue (pas d'erreur, retourne hints uniquement)
- [ ] Traçabilité complète (trace contient trajectoire agent)

**Open Questions:**
- Modèle LLM pour sélection ? (GPT-5-mini pour coût vs GPT-5.2 pour qualité)
- Budget exploration ? (5-10k tokens max pour phase 1 vs budget global génération)
- Cache sélections ? (même `user_instructions` + `hints` = résultat identique)
- Section filters granularité ? (niveau champ vs niveau sous-section vs niveau paragraphe)

---

### Integration Patterns (V1.0 ↔ Baseline)

#### Pattern 1: New API Endpoints (Streaming, Presets)

**Integration:**
- Nouveau router dans `api/routers/` (ex: `streaming.py`, `presets.py`)
- Enregistrement dans `api/main.py` : `app.include_router(streaming_router)`
- Service backend dans `services/` si logique métier (ex: `PresetService`)
- Tests dans `tests/api/test_<router>.py`

**Follows Baseline:**
- ✅ RESTful conventions (`/api/v1/*`)
- ✅ Pydantic schemas (`api/schemas/`)
- ✅ Dependency injection (`api/dependencies.py`)
- ✅ Error handling (exceptions hiérarchisées)

#### Pattern 2: New React Components (Modal, PresetBar)

**Integration:**
- Nouveaux composants dans `frontend/src/components/<domain>/`
- State management via Zustand (nouveaux slices si nécessaire)
- API calls via `frontend/src/api/<domain>.ts`
- Tests dans `frontend/src/components/<domain>/<Component>.test.tsx`

**Follows Baseline:**
- ✅ TypeScript strict
- ✅ Zustand pour state global
- ✅ API client modulaire (axios + intercepteurs)
- ✅ Tests unitaires (Vitest + RTL)

#### Pattern 3: Graph Editor Fixes (Refactoring)

**Integration:**
- Modifications dans `frontend/src/components/graph/`
- Migration données si nécessaire (script `scripts/migrate-stableIDs.ts`)
- Tests régression dans `frontend/src/components/graph/GraphEditor.test.tsx`

**Follows Baseline:**
- ✅ Pas de breaking changes API
- ✅ Backward compatibility (migrations gracieuses)
- ✅ Tests couvrent edge cases

---

