/**
 * Hook personnalisé pour gérer le system prompt.
 */
import { useState, useCallback } from 'react'
import * as configAPI from '../api/config'

export function useSystemPrompt() {
  const [systemPrompt, setSystemPrompt] = useState<string>('')
  const [defaultPrompt, setDefaultPrompt] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadDefaultPrompt = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await configAPI.getDefaultSystemPrompt()
      setDefaultPrompt(response.prompt)
      setSystemPrompt(response.prompt)
    } catch (err) {
      setError('Erreur lors du chargement du prompt par défaut')
      console.error('Erreur lors du chargement du prompt par défaut:', err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const resetToDefault = useCallback(() => {
    if (defaultPrompt !== null) {
      setSystemPrompt(defaultPrompt)
    }
  }, [defaultPrompt])

  const updatePrompt = useCallback((prompt: string) => {
    setSystemPrompt(prompt)
  }, [])

  return {
    systemPrompt,
    defaultPrompt,
    isLoading,
    error,
    loadDefaultPrompt,
    resetToDefault,
    updatePrompt,
  }
}

