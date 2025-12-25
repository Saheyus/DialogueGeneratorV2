/**
 * Hook personnalisé pour formater et afficher le prompt.
 */
import { useMemo } from 'react'

export function usePromptPreview(promptText: string | null | undefined) {
  const formattedPrompt = useMemo(() => {
    if (!promptText) return ''
    // Pour l'instant, on retourne le texte tel quel
    // On pourrait ajouter de la coloration syntaxique ou du formatage ici
    return promptText
  }, [promptText])

  return {
    formattedPrompt,
    isEmpty: !promptText || promptText.trim().length === 0,
  }
}

