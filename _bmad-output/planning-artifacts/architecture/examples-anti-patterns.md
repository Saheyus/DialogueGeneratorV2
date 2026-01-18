# Examples & Anti-patterns

### Good Example: Complete SSE Implementation

```python
# Backend: api/routers/streaming.py
@router.get("/stream")
async def stream_generation(request: Request):
    async def generate():
        try:
            async for chunk in llm_client.stream_generate():
                if await request.is_disconnected():
                    break
                yield f'data: {json.dumps({"type": "chunk", "content": chunk})}\n\n'
            yield f'data: {json.dumps({"type": "complete"})}\n\n'
        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            yield f'data: {json.dumps({"type": "error", "message": str(e)})}\n\n'
        finally:
            await write_generation_log(status="completed")
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

```typescript
// Frontend: components/generation/GenerationModal.tsx
const GenerationModal = () => {
  const [content, setContent] = useState('');
  const [status, setStatus] = useState<'streaming' | 'completed' | 'error'>('streaming');
  
  useEffect(() => {
    const eventSource = new EventSource('/api/v1/generate/stream');
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'chunk') {
        setContent(prev => prev + data.content);
      } else if (data.type === 'complete') {
        setStatus('completed');
        eventSource.close();
      } else if (data.type === 'error') {
        setStatus('error');
        showError(data.message);
        eventSource.close();
      }
    };
    
    return () => eventSource.close();
  }, []);
  
  return (
    <Modal>
      <div>{content}</div>
      <div>Status: {status}</div>
    </Modal>
  );
};
```

### Anti-pattern: Inconsistent Error Handling

```python
# ❌ BAD: Silent failure
try:
    result = await llm_client.generate()
except Exception:
    pass  # Silent failure, no logging

# ❌ BAD: Generic exception
try:
    result = await llm_client.generate()
except Exception as e:
    print(f"Error: {e}")  # Not logged, print statement

# ✅ GOOD: Proper exception + logging
try:
    result = await llm_client.generate()
except LLMTimeoutError as e:
    logger.error(f"LLM timeout: {e}", exc_info=True)
    raise HTTPException(status_code=504, detail="Generation timeout")
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal error")
```

### Anti-pattern: Mutable State Updates

```typescript
// ❌ BAD: Direct mutation
const useDialogueStore = create<DialogueState>((set, get) => ({
  nodes: [],
  addNode: (node) => {
    get().nodes.push(node);  // Direct mutation
  }
}));

// ✅ GOOD: Immutable update
const useDialogueStore = create<DialogueState>((set) => ({
  nodes: [],
  addNode: (node) => set((state) => ({
    nodes: [...state.nodes, node]  // Immutable
  }))
}));
```

---
