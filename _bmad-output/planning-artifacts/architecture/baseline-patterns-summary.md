# Baseline Patterns Summary

### Naming Patterns (Existing)

**Backend (Python)**
- **Modules/Files** : `snake_case.py` (ex: `context_builder.py`)
- **Classes** : `PascalCase` (ex: `ContextBuilder`, `LLMClient`)
- **Functions/Variables** : `snake_case` (ex: `build_context()`, `user_id`)
- **Constants** : `UPPER_SNAKE_CASE` (ex: `MAX_TOKENS`, `DEFAULT_TITLE`)

**Frontend (TypeScript)**
- **Components** : `PascalCase.tsx` (ex: `GenerationModal.tsx`)
- **Functions/Variables** : `camelCase` (ex: `buildPrompt()`, `userId`)
- **Types/Interfaces** : `PascalCase` (ex: `DialogueNode`, `UserConfig`)
- **Files (non-components)** : `camelCase.ts` (ex: `apiClient.ts`, `useAuth.ts`)

**API (REST)**
- **Endpoints** : `/api/v1/resource` (kebab-case, plural)
- **Path parameters** : `{id}` (ex: `/dialogues/{dialogue_id}`)
- **Query parameters** : `snake_case` (ex: `?user_id=123&include_metadata=true`)
- **JSON fields** : `snake_case` backend ↔ `camelCase` frontend (auto-conversion via Pydantic `alias_generator`)

**Example (JSON transformation):**
```python
# Backend Pydantic model
class UserProfile(BaseModel):
    user_id: int
    display_name: str
    
    class Config:
        alias_generator = to_camel  # Produces: userId, displayName
```

```typescript
// Frontend TypeScript type
interface UserProfile {
  userId: number;
  displayName: string;
}
```

### Structure Patterns (Existing)

**Backend Structure**
```
api/
├── routers/          # HTTP routes (thin layer)
├── schemas/          # Pydantic DTOs (request/response)
├── services/         # API adapters (call services/)
├── dependencies.py   # FastAPI dependency injection
└── container.py      # ServiceContainer (lifecycle)

services/             # Business logic (reusable)
├── context/          # ContextBuilder, FieldValidator
├── prompt/           # PromptEngine, token estimation
├── llm/              # LLMClient, structured outputs
└── json_renderer/    # UnityJsonRenderer

tests/                # Mirror source structure
├── api/              # API integration tests (TestClient)
└── services/         # Service unit tests (mocks)
```

**Frontend Structure**
```
frontend/src/
├── api/              # API client (axios, by domain)
├── components/       # React components (by domain)
│   ├── auth/         # Login, Register, etc.
│   ├── generation/   # GenerationModal, PromptBuilder
│   ├── graph/        # GraphEditor, NodeRenderer
│   └── layout/       # Header, Sidebar, etc.
├── hooks/            # Custom hooks (useAuth, useGeneration)
├── store/            # Zustand stores (by domain)
├── types/            # TypeScript types
└── main.tsx          # Entry point

tests/
└── components/       # Vitest + RTL (co-located or separate)
```

**RULE** : Tests mirror source structure (not co-located)  
**RULE** : Components organized by domain (not by type)

### Format Patterns (Existing)

**API Response Format**
```typescript
// ✅ CORRECT: Direct response (no wrapper)
GET /api/v1/dialogues/123
{
  "stableID": "abc-123",
  "displayName": "Opening Scene",
  "nodes": [...]
}

// ❌ INCORRECT: Wrapped response
{
  "data": { "stableID": "abc-123", ... },
  "meta": { "timestamp": ... }
}
```

**Error Response Format**
```typescript
// ✅ CORRECT: Exception + HTTP status
{
  "detail": "Dialogue not found",
  "status_code": 404
}

// Backend: raise HTTPException(status_code=404, detail="Dialogue not found")
```

**Date/Time Format**
```typescript
// ✅ CORRECT: ISO 8601 strings
{
  "created_at": "2026-01-14T13:45:30.123Z",
  "updated_at": "2026-01-14T14:20:15.456Z"
}
```

### Process Patterns (Existing)

**Error Handling**
```python
# ✅ CORRECT: Hierarchical exceptions + logging
class DialogueGenerationError(Exception):
    """Base exception for dialogue generation"""
    pass

class LLMTimeoutError(DialogueGenerationError):
    """LLM request timeout"""
    pass

# Usage
try:
    result = await llm_client.generate(...)
except LLMTimeoutError as e:
    logger.error(f"LLM timeout: {e}", exc_info=True)
    raise HTTPException(status_code=504, detail="Generation timeout")
```

**State Management (Zustand)**
```typescript
// ✅ CORRECT: Immutable updates
const useDialogueStore = create<DialogueState>((set) => ({
  nodes: [],
  addNode: (node) => set((state) => ({
    nodes: [...state.nodes, node]  // Immutable
  })),
  updateNode: (id, updates) => set((state) => ({
    nodes: state.nodes.map(n => 
      n.id === id ? { ...n, ...updates } : n
    )
  }))
}));
```

---
