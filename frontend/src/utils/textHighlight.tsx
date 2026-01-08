/**
 * Utilitaires pour mettre en surbrillance du texte dans les résultats de recherche.
 */
import React from 'react'
import { theme } from '../theme'

/**
 * Met en surbrillance les occurrences d'une requête dans un texte.
 * @param text - Le texte à mettre en surbrillance
 * @param query - La requête de recherche (sera utilisée case-insensitive)
 * @returns Un élément React avec les parties en surbrillance
 */
export function highlightText(text: string, query: string): React.ReactNode {
  if (!query.trim()) {
    return text
  }

  const parts = text.split(new RegExp(`(${escapeRegex(query)})`, 'gi'))
  
  return parts.map((part, index) => {
    if (part.toLowerCase() === query.toLowerCase()) {
      return (
        <mark
          key={index}
          style={{
            backgroundColor: theme.border.focus,
            color: theme.text.primary,
            padding: '0 2px',
            borderRadius: '2px',
          }}
        >
          {part}
        </mark>
      )
    }
    return <span key={index}>{part}</span>
  })
}

/**
 * Échappe les caractères spéciaux pour une utilisation dans une regex.
 */
function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}
