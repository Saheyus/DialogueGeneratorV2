/**
 * Hook pour gérer la commande palette (recherche globale).
 */
import { useState, useCallback } from 'react'

export interface CommandPaletteItem {
  id: string
  label: string
  description?: string
  category: 'action' | 'character' | 'location' | 'item' | 'dialogue' | 'navigation'
  action: () => void
  keywords?: string[]
}

export interface UseCommandPaletteReturn {
  isOpen: boolean
  open: () => void
  close: () => void
  toggle: () => void
}

export function useCommandPalette(): UseCommandPaletteReturn {
  const [isOpen, setIsOpen] = useState(false)

  const open = useCallback(() => {
    setIsOpen(true)
  }, [])

  const close = useCallback(() => {
    setIsOpen(false)
  }, [])

  const toggle = useCallback(() => {
    setIsOpen((prev) => !prev)
  }, [])

  return { isOpen, open, close, toggle }
}

/**
 * Fonction utilitaire pour filtrer les items de la commande palette.
 */
export function filterCommandPaletteItems(
  items: CommandPaletteItem[],
  query: string
): CommandPaletteItem[] {
  if (!query.trim()) {
    return items
  }

  const lowerQuery = query.toLowerCase()
  
  return items.filter((item) => {
    // Rechercher dans le label
    if (item.label.toLowerCase().includes(lowerQuery)) {
      return true
    }
    
    // Rechercher dans la description
    if (item.description?.toLowerCase().includes(lowerQuery)) {
      return true
    }
    
    // Rechercher dans les mots-clés
    if (item.keywords?.some(keyword => keyword.toLowerCase().includes(lowerQuery))) {
      return true
    }
    
    return false
  })
}

