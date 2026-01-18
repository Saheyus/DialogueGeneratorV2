# V1.0 New Patterns (Detailed)

### Pattern V1-001: SSE Streaming (ADR-001)

**Context:** Progress Feedback Modal avec streaming LLM temps réel

**Event Format (MANDATORY):**
```typescript
// ✅ CORRECT: SSE format strict
data: {"type": "chunk", "content": "Partial text..."}\n\n
data: {"type": "metadata", "tokens": 150, "cost": 0.003}\n\n
data: {"type": "complete", "total_tokens": 1500}\n\n
data: {"type": "error", "message": "LLM timeout", "code": "TIMEOUT"}\n\n

// ❌ INCORRECT: Non-standard format
{"type": "chunk", "content": "..."}  // Missing "data: " prefix
data: chunk: "..."                   // Not JSON
```

**Backend Implementation:**
```python
# ✅ CORRECT: Generator avec yield
async def stream_generation():
    try:
        async for chunk in llm_client.stream_generate():
            yield f'data: {json.dumps({"type": "chunk", "content": chunk})}\n\n'
        yield f'data: {json.dumps({"type": "complete"})}\n\n'
    except Exception as e:
        yield f'data: {json.dumps({"type": "error", "message": str(e)})}\n\n'
```

**Frontend Implementation:**
```typescript
// ✅ CORRECT: EventSource avec cleanup
const eventSource = new EventSource('/api/v1/generate/stream');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch (data.type) {
    case 'chunk':
      appendContent(data.content);
      break;
    case 'complete':
      setStatus('completed');
      eventSource.close();
      break;
    case 'error':
      showError(data.message);
      eventSource.close();
      break;
  }
};

// Cleanup on component unmount
useEffect(() => {
  return () => eventSource.close();
}, []);
```

**Interruption Pattern:**
```typescript
// Frontend: AbortController
const abortController = new AbortController();

const handleInterrupt = () => {
  abortController.abort();
  eventSource.close();
  setStatus('interrupted');
};

// Backend: Graceful shutdown (10s timeout)
async def stream_generation(request: Request):
    try:
        async with asyncio.timeout(10):  # 10s cleanup
            # ... generation logic
    finally:
        # Write final logs (always executes)
        await write_generation_log(status="interrupted")
```

**RULES:**
- **MUST** use SSE format `data: {...}\n\n`
- **MUST** include `type` field in all events
- **MUST** handle interruption gracefully (10s timeout)
- **MUST** close EventSource on unmount

---

### Pattern V1-002: Preset Storage (ADR-002)

**File Naming (MANDATORY):**
```
data/presets/
├── a1b2c3d4-e5f6-7890-abcd-ef1234567890.json  ✅ UUID
├── my-preset.json                              ❌ Human-readable
└── preset_001.json                             ❌ Sequential
```

**Preset JSON Structure:**
```typescript
// ✅ CORRECT: Complete structure
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "name": "Opening Scene - Akthar",
  "icon": "⚔️",
  "metadata": {
    "created": "2026-01-14T13:45:30.123Z",
    "modified": "2026-01-14T14:20:15.456Z"
  },
  "configuration": {
    "characters": ["char-001", "char-002"],  // IDs only, not full objects
    "locations": ["loc-001"],
    "region": "Avili",
    "subLocation": "Ancienne Forge",
    "sceneType": "Première rencontre",
    "instructions": "Dialogue tendu entre Akthar et Neth..."
  }
}
```

**Validation Pattern (Lazy + Warning):**
```python
# ✅ CORRECT: Validate at load time, warn if invalid
def validate_preset(preset: Preset, gdd: GameDesignDocument) -> ValidationResult:
    invalid_refs = []
    
    for char_id in preset.configuration.characters:
        if char_id not in gdd.characters:
            invalid_refs.append(f"Character '{char_id}' not found")
    
    return ValidationResult(
        valid=len(invalid_refs) == 0,
        warnings=invalid_refs
    )

# Frontend: Show warning modal, allow "Load anyway"
if (!validationResult.valid) {
  showWarningModal({
    title: "⚠️ Preset partiellement obsolète",
    warnings: validationResult.warnings,
    actions: ["Cancel", "Load anyway"]
  });
}
```

**RULES:**
- **MUST** use UUID for file naming
- **MUST** store IDs only (not full GDD objects)
- **MUST** validate lazily (at load time)
- **MUST** show warning modal (not blocking error)

---

### Pattern V1-003: Cost Tracking (ID-003)

**Middleware Pattern:**
```python
# ✅ CORRECT: Pre-LLM middleware check
async def cost_governance_middleware(
    request: Request,
    user_id: str,
    estimated_cost: float
):
    usage = await get_user_cost_usage(user_id)
    
    if usage.amount + estimated_cost >= usage.quota:
        # 100% hard block
        raise HTTPException(
            status_code=429,
            detail="Monthly quota reached"
        )
    elif usage.amount + estimated_cost >= usage.quota * 0.9:
        # 90% soft warning (log but allow)
        logger.warning(f"User {user_id} at 90% quota")
    
    # Proceed with generation
    return await generate_dialogue(...)
```

**Storage Pattern:**
```sql
-- Table: cost_usage
CREATE TABLE cost_usage (
    user_id UUID PRIMARY KEY,
    month VARCHAR(7),  -- "2026-01"
    amount DECIMAL(10, 4),
    quota DECIMAL(10, 4),
    updated_at TIMESTAMP
);
```

**Frontend Toast/Modal:**
```typescript
// 90% soft warning: Toast
if (costStatus.percentage >= 90) {
  showToast({
    type: 'warning',
    message: `⚠️ Quota à ${costStatus.percentage}%, ${costStatus.remaining}€ restants`
  });
}

// 100% hard block: Modal
if (costStatus.percentage >= 100) {
  showModal({
    title: '🚫 Quota mensuel atteint',
    message: `Impossible de générer. Options : Attendre reset ou contacter admin.`,
    actions: ['Close']  // No "Generate anyway"
  });
  throw new Error('QUOTA_EXCEEDED');
}
```

**RULES:**
- **MUST** check cost BEFORE LLM call
- **MUST** block at 100% (no bypass except admin)
- **MUST** warn at 90% (toast, not blocking)
- **MUST** log all quota-exceeded attempts

---

### Pattern V1-004: Auto-save (ID-001)

**Timer Pattern:**
```typescript
// ✅ CORRECT: Hook with interval
const useAutoSave = (data: DialogueGraph) => {
  const [lastSaveTime, setLastSaveTime] = useState<Date | null>(null);
  
  useEffect(() => {
    const interval = setInterval(async () => {
      if (isGenerating) return; // Suspend during generation
      
      await saveDialogue(data);
      setLastSaveTime(new Date());
    }, 2 * 60 * 1000); // 2min
    
    return () => clearInterval(interval);
  }, [data, isGenerating]);
  
  return { lastSaveTime };
};

// UI indicator
<div>Sauvegardé il y a {formatRelative(lastSaveTime)}</div>
```

**Conflict Resolution (LWW):**
```python
# ✅ CORRECT: Last Write Wins (no merge)
async def save_dialogue(dialogue_id: str, data: DialogueGraph):
    # Simply overwrite existing file
    with open(f"data/interactions/{dialogue_id}.json", "w") as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Auto-saved dialogue {dialogue_id}")
```

**RULES:**
- **MUST** auto-save every 2min (configurable)
- **MUST** suspend during generation
- **MUST** use LWW (no merge logic)
- **MUST** show "Sauvegardé il y a Xs" indicator

---

### Pattern V1-005: Multi-Provider LLM Abstraction (ADR-004)

**Context:** Support de multiples providers LLM (OpenAI + Mistral) avec sélection utilisateur

**Interface Pattern (MANDATORY):**
```python
# ✅ CORRECT: Interface IGenerator unifiée
from abc import ABC, abstractmethod

class IGenerator(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt"""
        pass
    
    @abstractmethod
    async def stream_generate(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Stream generation chunks"""
        pass
    
    @abstractmethod
    async def generate_structured(
        self, prompt: str, schema: dict, **kwargs
    ) -> dict:
        """Generate structured output (JSON Schema)"""
        pass
```

**Factory Pattern:**
```python
# ✅ CORRECT: Factory pour sélection provider
class LLMFactory:
    @staticmethod
    def create(provider: str, model: str) -> IGenerator:
        if provider == "openai":
            return OpenAIClient(model=model)
        elif provider == "mistral":
            return MistralClient(model=model)
        else:
            raise ValueError(f"Unknown provider: {provider}")
```

**Provider Implementation:**
```python
# ✅ CORRECT: MistralClient implémente IGenerator
class MistralClient(IGenerator):
    def __init__(self, model: str = "small-creative"):
        self.client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
        self.model = model
    
    async def stream_generate(self, prompt: str, **kwargs):
        # Normalise vers format SSE uniforme
        async for chunk in self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            response_format={"type": "json_object"} if kwargs.get("structured") else None
        ):
            yield chunk.choices[0].delta.content  # Normalisé identique OpenAI
```

**Frontend Model Selection:**
```typescript
// ✅ CORRECT: Dropdown sélection modèle
const ModelSelector = () => {
  const { selectedModel, setModel } = useGenerationStore();
  
  return (
    <select 
      value={selectedModel} 
      onChange={(e) => setModel(e.target.value)}
    >
      <option value="openai:gpt-5.2">OpenAI GPT-5.2</option>
      <option value="mistral:small-creative">Mistral Small Creative</option>
    </select>
  );
};
```

**API Parameter:**
```python
# ✅ CORRECT: Endpoint accepte provider/model
@router.get("/generate/stream")
async def stream_generation(
    provider: str = "openai",  # Default backward compatible
    model: str = "gpt-5.2",
    ...
):
    llm_client = LLMFactory.create(provider, model)
    # ... reste identique (abstraction)
```

**RULES:**
- **MUST** utiliser interface `IGenerator` (pas de code provider-spécifique dans routers)
- **MUST** normaliser streaming vers format SSE uniforme (tous providers)
- **MUST** normaliser structured outputs (JSON Schema pour tous)
- **MUST** maintenir backward compatibility (OpenAI défaut si param absent)
- **MUST** différencier cost tracking par provider (prix différents)

---
