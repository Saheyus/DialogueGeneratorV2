/**
 * Hook personnalisé pour gérer le system prompt.
 */
import { useState, useCallback, useEffect } from 'react'
import * as configAPI from '../api/config'

const SAVED_PROMPT_KEY = 'dialogue_generator_saved_system_prompt'

export function useSystemPrompt() {
  const [systemPrompt, setSystemPrompt] = useState<string>('')
  const [defaultPrompt, setDefaultPrompt] = useState<string | null>(null)
  const [savedPrompt, setSavedPrompt] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Charger le prompt par défaut et la sauvegarde au montage
  useEffect(() => {
    loadDefaultPrompt()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []) // Charger une seule fois au montage

  const loadDefaultPrompt = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await configAPI.getDefaultSystemPrompt()
      setDefaultPrompt(response.prompt)
      
      // Lire le prompt sauvegardé depuis localStorage
      let saved: string | null = null
      try {
        saved = localStorage.getItem(SAVED_PROMPT_KEY)
      } catch (err) {
        console.warn('Impossible de lire le prompt sauvegardé:', err)
      }
      
      // Si un prompt est sauvegardé, l'utiliser, sinon utiliser le défaut
      if (saved) {
        setSavedPrompt(saved)
        setSystemPrompt(saved)
      } else {
        setSystemPrompt(response.prompt)
      }
    } catch (err) {
      setError('Erreur lors du chargement du prompt par défaut')
      console.error('Erreur lors du chargement du prompt par défaut:', err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const savePrompt = useCallback((prompt: string) => {
    try {
      localStorage.setItem(SAVED_PROMPT_KEY, prompt)
      setSavedPrompt(prompt)
    } catch (err) {
      console.error('Erreur lors de la sauvegarde du prompt:', err)
      throw new Error('Impossible de sauvegarder le prompt')
    }
  }, [])

  const restore = useCallback(async (): Promise<string> => {
    // Lire le prompt sauvegardé depuis localStorage
    let saved: string | null = null
    try {
      saved = localStorage.getItem(SAVED_PROMPT_KEY)
    } catch (err) {
      console.warn('Impossible de lire le prompt sauvegardé:', err)
    }
    
    // Restaurer la dernière version sauvegardée, ou le défaut si rien n'est sauvegardé
    if (saved) {
      setSavedPrompt(saved)
      setSystemPrompt(saved)
      return saved
    } else {
      // Si defaultPrompt n'est pas encore chargé, le charger depuis l'API
      if (defaultPrompt === null) {
        setIsLoading(true)
        try {
          const response = await configAPI.getDefaultSystemPrompt()
          setDefaultPrompt(response.prompt)
          setSystemPrompt(response.prompt)
          return response.prompt
        } catch (err) {
          setError('Erreur lors du chargement du prompt par défaut')
          console.error('Erreur lors du chargement du prompt par défaut:', err)
          return ''
        } finally {
          setIsLoading(false)
        }
      } else {
        setSystemPrompt(defaultPrompt)
        return defaultPrompt
      }
    }
  }, [defaultPrompt])

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
    savedPrompt,
    isLoading,
    error,
    loadDefaultPrompt,
    savePrompt,
    restore,
    resetToDefault,
    updatePrompt,
  }
}

