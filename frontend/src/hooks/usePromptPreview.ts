/**
 * Hook personnalisé pour formater et afficher le prompt.
 */
import { useMemo } from 'react'
import { hasJsonContent } from '../utils/jsonPrettifier'

export interface PromptSection {
  title: string
  content: string
  hasJson: boolean
}

/**
 * Parse le prompt en sections délimitées par --- SECTION ---
 */
export function parsePromptSections(prompt: string): PromptSection[] {
  if (!prompt) return []
  
  const sections: PromptSection[] = []
  const sectionRegex = /^--- (.+?) ---$/gm
  
  // Trouver toutes les positions des sections
  const sectionMatches: Array<{ index: number; title: string }> = []
  let match
  while ((match = sectionRegex.exec(prompt)) !== null) {
    sectionMatches.push({
      index: match.index,
      title: match[1].trim(),
    })
  }
  
  if (sectionMatches.length === 0) {
    // Pas de sections, tout le contenu est une seule section "System Prompt"
    return [{
      title: 'System Prompt',
      content: prompt.trim(),
      hasJson: hasJsonContent(prompt),
    }]
  }
  
  // Extraire le contenu avant la première section (System Prompt)
  if (sectionMatches[0].index > 0) {
    const systemPromptContent = prompt.substring(0, sectionMatches[0].index).trim()
    if (systemPromptContent) {
      sections.push({
        title: 'System Prompt',
        content: systemPromptContent,
        hasJson: hasJsonContent(systemPromptContent),
      })
    }
  }
  
  // Extraire chaque section
  for (let i = 0; i < sectionMatches.length; i++) {
    const sectionStart = sectionMatches[i].index
    const sectionEnd = i < sectionMatches.length - 1 
      ? sectionMatches[i + 1].index 
      : prompt.length
    
    // Extraire le contenu de la section (après le marqueur)
    const sectionHeaderMatch = prompt.substring(sectionStart).match(/^--- (.+?) ---\s*\n?/m)
    if (sectionHeaderMatch) {
      const contentStart = sectionStart + sectionHeaderMatch[0].length
      const content = prompt.substring(contentStart, sectionEnd).trim()
      
      if (content) {
        sections.push({
          title: sectionMatches[i].title,
          content,
          hasJson: hasJsonContent(content),
        })
      }
    }
  }
  
  return sections
}

export function usePromptPreview(promptText: string | null | undefined) {
  const formattedPrompt = useMemo(() => {
    if (!promptText) return ''
    // Pour l'instant, on retourne le texte tel quel
    // On pourrait ajouter de la coloration syntaxique ou du formatage ici
    return promptText
  }, [promptText])
  
  const sections = useMemo(() => {
    if (!promptText) return []
    return parsePromptSections(promptText)
  }, [promptText])

  return {
    formattedPrompt,
    sections,
    isEmpty: !promptText || promptText.trim().length === 0,
  }
}



