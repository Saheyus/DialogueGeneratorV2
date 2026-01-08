/**
 * Hook pour gérer la commande palette (recherche globale).
 * Utilise un store Zustand global pour partager l'état entre tous les composants.
 */
import { useCommandPaletteStore } from '../store/commandPaletteStore'

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
  return useCommandPaletteStore()
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

