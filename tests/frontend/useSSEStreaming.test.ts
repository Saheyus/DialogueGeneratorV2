/**
 * Tests unitaires pour le hook useSSEStreaming.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useSSEStreaming } from '../../frontend/src/hooks/useSSEStreaming'
import { useGenerationStore } from '../../frontend/src/store/generationStore'

// Mock EventSource
class MockEventSource {
  url: string
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  readyState: number = 0
  CONNECTING = 0
  OPEN = 1
  CLOSED = 2

  constructor(url: string) {
    this.url = url
    this.readyState = this.CONNECTING
    // Simuler l'ouverture après un court délai
    setTimeout(() => {
      this.readyState = this.OPEN
    }, 10)
  }

  close() {
    this.readyState = this.CLOSED
  }

  // Méthode helper pour simuler la réception d'un message
  simulateMessage(data: string) {
    if (this.onmessage) {
      const event = new MessageEvent('message', { data })
      this.onmessage(event)
    }
  }

  // Méthode helper pour simuler une erreur
  simulateError() {
    if (this.onerror) {
      const event = new Event('error')
      this.onerror(event)
    }
  }
}

// Remplacer EventSource global par le mock
global.EventSource = MockEventSource as any

describe('useSSEStreaming', () => {
  let mockEventSource: MockEventSource

  beforeEach(() => {
    // Réinitialiser le store
    const store = useGenerationStore.getState()
    if (store.resetStreamingState) {
      store.resetStreamingState()
    }
  })

  afterEach(() => {
    if (mockEventSource) {
      mockEventSource.close()
    }
  })

  it('should connect to SSE endpoint', () => {
    const { result } = renderHook(() => useSSEStreaming('/api/v1/dialogues/generate/jobs/job-123/stream'))

    expect(result.current.isConnected).toBe(false) // Pas encore connecté (CONNECTING)

    // Attendre que la connexion soit établie
    waitFor(() => {
      expect(result.current.isConnected).toBe(true)
    })
  })

  it('should parse chunk events and update store', async () => {
    const { result } = renderHook(() => useSSEStreaming('/api/v1/dialogues/generate/jobs/job-123/stream'))

    // Simuler la réception d'un chunk
    const chunkData = JSON.stringify({ type: 'chunk', content: 'Hello' })
    
    // Attendre que EventSource soit créé
    await waitFor(() => {
      expect(result.current.eventSource).toBeDefined()
    })

    mockEventSource = result.current.eventSource as any
    mockEventSource.simulateMessage(chunkData)

    // Vérifier que le store a été mis à jour
    await waitFor(() => {
      const { streamingContent } = useGenerationStore.getState()
      expect(streamingContent).toBe('Hello')
    })
  })

  it('should parse step events and update store', async () => {
    const { result } = renderHook(() => useSSEStreaming('/api/v1/dialogues/generate/jobs/job-123/stream'))

    await waitFor(() => {
      expect(result.current.eventSource).toBeDefined()
    })

    mockEventSource = result.current.eventSource as any
    
    const stepData = JSON.stringify({ type: 'step', step: 'Generating' })
    mockEventSource.simulateMessage(stepData)

    await waitFor(() => {
      const { currentStep } = useGenerationStore.getState()
      expect(currentStep).toBe('Generating')
    })
  })

  it('should parse complete events and update store', async () => {
    const { result } = renderHook(() => useSSEStreaming('/api/v1/dialogues/generate/jobs/job-123/stream'))

    await waitFor(() => {
      expect(result.current.eventSource).toBeDefined()
    })

    mockEventSource = result.current.eventSource as any
    
    const completeData = JSON.stringify({ type: 'complete' })
    mockEventSource.simulateMessage(completeData)

    await waitFor(() => {
      const { currentStep, isGenerating } = useGenerationStore.getState()
      expect(currentStep).toBe('Complete')
      expect(isGenerating).toBe(false)
    })
  })

  it('should parse error events and update store', async () => {
    const { result } = renderHook(() => useSSEStreaming('/api/v1/dialogues/generate/jobs/job-123/stream'))

    await waitFor(() => {
      expect(result.current.eventSource).toBeDefined()
    })

    mockEventSource = result.current.eventSource as any
    
    const errorData = JSON.stringify({ type: 'error', message: 'Test error' })
    mockEventSource.simulateMessage(errorData)

    await waitFor(() => {
      const { error, isGenerating } = useGenerationStore.getState()
      expect(error).toBe('Test error')
      expect(isGenerating).toBe(false)
    })
  })

  it('should close EventSource on unmount', async () => {
    const { result, unmount } = renderHook(() => useSSEStreaming('/api/v1/dialogues/generate/jobs/job-123/stream'))

    await waitFor(() => {
      expect(result.current.eventSource).toBeDefined()
    })

    mockEventSource = result.current.eventSource as any
    const closeSpy = vi.spyOn(mockEventSource, 'close')

    unmount()

    expect(closeSpy).toHaveBeenCalled()
  })

  it('should handle network errors gracefully', async () => {
    const { result } = renderHook(() => useSSEStreaming('/api/v1/dialogues/generate/jobs/job-123/stream'))

    await waitFor(() => {
      expect(result.current.eventSource).toBeDefined()
    })

    mockEventSource = result.current.eventSource as any
    mockEventSource.simulateError()

    await waitFor(() => {
      const { error } = useGenerationStore.getState()
      expect(error).toBeTruthy()
    })
  })

  it('should ignore invalid JSON messages', async () => {
    const { result } = renderHook(() => useSSEStreaming('/api/v1/dialogues/generate/jobs/job-123/stream'))

    await waitFor(() => {
      expect(result.current.eventSource).toBeDefined()
    })

    mockEventSource = result.current.eventSource as any
    
    // Envoyer un message JSON invalide
    mockEventSource.simulateMessage('invalid json')

    // Le store ne devrait pas être mis à jour
    const { streamingContent } = useGenerationStore.getState()
    expect(streamingContent).toBe('')
  })
})
