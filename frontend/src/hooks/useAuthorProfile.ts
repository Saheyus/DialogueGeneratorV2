/**
 * Hook personnalisé pour gérer le profil d'auteur (global, réutilisable).
 */
import { useState, useCallback, useEffect } from 'react'

const SAVED_AUTHOR_PROFILE_KEY = 'dialogue_generator_saved_author_profile'

export function useAuthorProfile() {
  const [authorProfile, setAuthorProfile] = useState<string>('')
  const [savedProfile, setSavedProfile] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Charger le profil sauvegardé depuis localStorage au montage
  useEffect(() => {
    try {
      const saved = localStorage.getItem(SAVED_AUTHOR_PROFILE_KEY)
      if (saved) {
        setSavedProfile(saved)
        setAuthorProfile(saved)
      }
    } catch (err) {
      console.warn('Impossible de charger le profil d\'auteur sauvegardé depuis localStorage:', err)
    }
  }, [])

  const saveProfile = useCallback((profile: string) => {
    try {
      localStorage.setItem(SAVED_AUTHOR_PROFILE_KEY, profile)
      setSavedProfile(profile)
    } catch (err) {
      console.error('Erreur lors de la sauvegarde du profil d\'auteur:', err)
      throw new Error('Impossible de sauvegarder le profil d\'auteur')
    }
  }, [])

  const restore = useCallback(() => {
    // Lire le profil sauvegardé depuis localStorage
    let saved: string | null = null
    try {
      saved = localStorage.getItem(SAVED_AUTHOR_PROFILE_KEY)
    } catch (err) {
      console.warn('Impossible de lire le profil d\'auteur sauvegardé:', err)
    }
    
    // Restaurer la dernière version sauvegardée, ou vide si rien n'est sauvegardé
    if (saved) {
      setSavedProfile(saved)
      setAuthorProfile(saved)
    } else {
      setAuthorProfile('')
    }
  }, [])

  const updateProfile = useCallback((profile: string) => {
    setAuthorProfile(profile)
  }, [])

  return {
    authorProfile,
    savedProfile,
    isLoading,
    error,
    saveProfile,
    restore,
    updateProfile,
  }
}

