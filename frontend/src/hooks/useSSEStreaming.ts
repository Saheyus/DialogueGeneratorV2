/**
 * Hook React pour gérer le streaming SSE (Server-Sent Events).
 * 
 * Connecte à un endpoint SSE, parse les événements JSON,
 * et dispatch les mises à jour vers le store Zustand.
 */
import { useEffect, useRef, useState } from 'react'
import { useGenerationStore } from '../store/generationStore'

export interface UseSSEStreamingReturn {
  /** EventSource instance (pour tests) */
  eventSource: EventSource | null
  /** État de connexion */
  isConnected: boolean
  /** Erreur de connexion */
  connectionError: string | null
}

/**
 * Hook pour streamer la génération LLM via SSE.
 * 
 * Pattern :
 * - Crée EventSource vers l'endpoint SSE
 * - Parse les événements JSON (chunk, step, complete, error)
 * - Dispatch vers le store Zustand
 * - Cleanup automatique sur unmount
 * 
 * @param url - URL de l'endpoint SSE
 * @returns État de connexion et EventSource instance
 * 
 * @example
 * ```tsx
 * const { isConnected } = useSSEStreaming('/api/v1/dialogues/generate/stream')
 * ```
 */
export function useSSEStreaming(url: string): UseSSEStreamingReturn {
  const [eventSource, setEventSource] = useState<EventSource | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [connectionError, setConnectionError] = useState<string | null>(null)
  
  // Ref pour éviter les re-renders inutiles
  const eventSourceRef = useRef<EventSource | null>(null)
  const closedByClientRef = useRef(false)
  
  // Actions du store
  const {
    appendChunk,
    setStep,
    complete,
    setError,
  } = useGenerationStore()

  useEffect(() => {
    // Créer EventSource
    const es = new EventSource(url)
    eventSourceRef.current = es
    setEventSource(es)
    closedByClientRef.current = false

    // Handler pour les messages SSE
    es.onmessage = (event: MessageEvent) => {
      try {
        // Parser le JSON SSE
        const data = JSON.parse(event.data)
        
        // Dispatcher selon le type d'événement
        switch (data.type) {
          case 'chunk':
            // Ajouter le chunk au contenu streaming
            if (data.content) {
              appendChunk(data.content)
            }
            break
            
          case 'step':
            // Mettre à jour l'étape de progression
            if (data.step) {
              setStep(data.step)
            }
            break
            
          case 'metadata':
            // Metadata (tokens, coût) - pour l'instant on log juste
            console.debug('SSE metadata:', data)
            break
            
          case 'complete':
            // Génération terminée avec succès
            complete()
            // Fermer la connexion
            closedByClientRef.current = true
            es.close()
            break
            
          case 'error':
            // Erreur survenue
            if (data.message) {
              setError(data.message)
            }
            // Fermer la connexion
            closedByClientRef.current = true
            es.close()
            break
            
          default:
            console.warn('SSE event type inconnu:', data.type)
        }
      } catch (err) {
        // Ignorer les messages JSON invalides
        console.warn('Erreur parsing SSE message:', err, event.data)
      }
    }

    // Handler pour les erreurs de connexion
    es.onerror = (event: Event) => {
      if (closedByClientRef.current || es.readyState === EventSource.CLOSED) {
        return
      }
      console.error('Erreur EventSource:', event)
      setConnectionError('Erreur de connexion au serveur')
      setError('Erreur de connexion au serveur')
      setIsConnected(false)
      closedByClientRef.current = true
      es.close()
    }

    // Handler pour l'ouverture de connexion
    es.onopen = () => {
      setIsConnected(true)
      setConnectionError(null)
    }

    // Cleanup : fermer EventSource sur unmount
    return () => {
      if (eventSourceRef.current) {
        closedByClientRef.current = true
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
    }
  }, [url, appendChunk, setStep, complete, setError])

  return {
    eventSource,
    isConnected,
    connectionError,
  }
}
