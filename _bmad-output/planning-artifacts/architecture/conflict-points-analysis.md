# Conflict Points Analysis

### Critical Conflict Points (Where AI Agents Could Diverge)

**1. SSE Event Naming**
- ❌ **Bad:** `{"event": "chunk"}`, `{"eventType": "chunk"}`, `{"msg_type": "chunk"}`
- ✅ **Good:** `{"type": "chunk"}` (MANDATORY)

**2. Preset File Naming**
- ❌ **Bad:** Human-readable names, sequential IDs
- ✅ **Good:** UUID only

**3. Cost Check Timing**
- ❌ **Bad:** Check after LLM call (too late)
- ✅ **Good:** Check before (middleware)

**4. Validation Strictness**
- ❌ **Bad:** Blocking errors on invalid preset refs
- ✅ **Good:** Warning modal with "Load anyway"

**5. Auto-save During Generation**
- ❌ **Bad:** Auto-save interrupts streaming
- ✅ **Good:** Suspend auto-save while `isGenerating === true`

**6. Error Response Format**
- ❌ **Bad:** Different formats per endpoint
- ✅ **Good:** Consistent HTTPException + detail

**7. JSON Field Casing**
- ❌ **Bad:** Mixed `snake_case` and `camelCase` in same API
- ✅ **Good:** `snake_case` backend, `camelCase` frontend, Pydantic auto-converts

**8. Component File Naming**
- ❌ **Bad:** `generationModal.tsx`, `generation-modal.tsx`
- ✅ **Good:** `GenerationModal.tsx` (PascalCase)

**9. Test Structure**
- ❌ **Bad:** Co-located tests (`GenerationModal.test.tsx` next to `GenerationModal.tsx`)
- ✅ **Good:** Mirror structure (`tests/components/generation/GenerationModal.test.tsx`)

**10. State Updates (Zustand)**
- ❌ **Bad:** Direct mutation `state.nodes.push(newNode)`
- ✅ **Good:** Immutable `nodes: [...state.nodes, newNode]`

**11. Logging Levels**
- ❌ **Bad:** Inconsistent (INFO for errors, DEBUG for critical)
- ✅ **Good:** ERROR (exceptions), WARNING (90% quota), INFO (operations), DEBUG (verbose)

**12. Date Format in JSON**
- ❌ **Bad:** Timestamps (1736866830), localized strings
- ✅ **Good:** ISO 8601 UTC (`2026-01-14T13:45:30.123Z`)

**13. LLM Provider Selection** 🆕
- ❌ **Bad:** Code provider-spécifique dans routers, pas d'abstraction
- ✅ **Good:** Factory pattern + interface `IGenerator`, normalisation uniforme

---
