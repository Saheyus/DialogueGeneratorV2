/**
 * Store Zustand pour la gestion des flags in-game.
 */
import { create } from 'zustand'
import type { FlagDefinition, InGameFlag, FlagValue } from '../types/flags'
import * as flagsAPI from '../api/flags'

interface FlagsState {
  // Catalogue des définitions disponibles
  catalog: FlagDefinition[]
  
  // Flags sélectionnés avec leurs valeurs
  selectedFlags: Map<string, InGameFlag>
  
  // Filtres de recherche
  query: string
  favoritesOnly: boolean
  selectedCategories: Set<string>
  
  // Loading state
  isLoading: boolean
  error: string | null
  
  // Actions
  loadCatalog: () => Promise<void>
  searchFlags: (q: string) => void
  toggleFavoritesFilter: () => void
  toggleCategoryFilter: (category: string) => void
  clearFilters: () => void
  
  // Sélection des flags
  toggleBoolFlag: (flagId: string) => void
  setNumericFlag: (flagId: string, value: number) => void
  setStringFlag: (flagId: string, value: string) => void
  clearFlags: () => void
  getSelectedFlagsArray: () => InGameFlag[]
  
  // Gestion du catalogue
  upsertDefinition: (def: FlagDefinition) => Promise<void>
  toggleFavoriteInCatalog: (flagId: string) => Promise<void>
}

export const useFlagsStore = create<FlagsState>((set, get) => ({
  catalog: [],
  selectedFlags: new Map(),
  query: '',
  favoritesOnly: false,
  selectedCategories: new Set(),
  isLoading: false,
  error: null,
  
  loadCatalog: async () => {
    set({ isLoading: true, error: null })
    try {
      const response = await flagsAPI.listFlags()
      set({ catalog: response.flags, isLoading: false })
    } catch (err: any) {
      set({ error: err?.message || 'Erreur lors du chargement du catalogue', isLoading: false })
    }
  },
  
  searchFlags: (q: string) => {
    set({ query: q })
  },
  
  toggleFavoritesFilter: () => {
    set(state => ({ favoritesOnly: !state.favoritesOnly }))
  },
  
  toggleCategoryFilter: (category: string) => {
    set(state => {
      const newCategories = new Set(state.selectedCategories)
      if (newCategories.has(category)) {
        newCategories.delete(category)
      } else {
        newCategories.add(category)
      }
      return { selectedCategories: newCategories }
    })
  },
  
  clearFilters: () => {
    set({ query: '', favoritesOnly: false, selectedCategories: new Set() })
  },
  
  toggleBoolFlag: (flagId: string) => {
    set(state => {
      const newSelectedFlags = new Map(state.selectedFlags)
      const flagDef = state.catalog.find(f => f.id === flagId)
      
      if (!flagDef) return state
      
      if (newSelectedFlags.has(flagId)) {
        // Déselectionner
        newSelectedFlags.delete(flagId)
      } else {
        // Sélectionner avec valeur par défaut (toggle entre true/false)
        const currentValue = newSelectedFlags.get(flagId)?.value
        const newValue = typeof currentValue === 'boolean' ? !currentValue : true
        
        newSelectedFlags.set(flagId, {
          id: flagId,
          value: newValue,
          category: flagDef.category,
          timestamp: new Date().toISOString()
        })
      }
      
      return { selectedFlags: newSelectedFlags }
    })
  },
  
  setNumericFlag: (flagId: string, value: number) => {
    set(state => {
      const newSelectedFlags = new Map(state.selectedFlags)
      const flagDef = state.catalog.find(f => f.id === flagId)
      
      if (!flagDef) return state
      
      newSelectedFlags.set(flagId, {
        id: flagId,
        value,
        category: flagDef.category,
        timestamp: new Date().toISOString()
      })
      
      return { selectedFlags: newSelectedFlags }
    })
  },
  
  setStringFlag: (flagId: string, value: string) => {
    set(state => {
      const newSelectedFlags = new Map(state.selectedFlags)
      const flagDef = state.catalog.find(f => f.id === flagId)
      
      if (!flagDef) return state
      
      newSelectedFlags.set(flagId, {
        id: flagId,
        value,
        category: flagDef.category,
        timestamp: new Date().toISOString()
      })
      
      return { selectedFlags: newSelectedFlags }
    })
  },
  
  clearFlags: () => {
    set({ selectedFlags: new Map() })
  },
  
  removeFlag: (flagId: string) => {
    set(state => {
      const newSelectedFlags = new Map(state.selectedFlags)
      newSelectedFlags.delete(flagId)
      return { selectedFlags: newSelectedFlags }
    })
  },
  
  getSelectedFlagsArray: () => {
    return Array.from(get().selectedFlags.values())
  },
  
  upsertDefinition: async (def: FlagDefinition) => {
    set({ isLoading: true, error: null })
    try {
      await flagsAPI.upsertFlag({
        id: def.id,
        type: def.type,
        category: def.category,
        label: def.label,
        description: def.description,
        defaultValue: def.defaultValue,
        tags: def.tags,
        isFavorite: def.isFavorite
      })
      
      // Recharger le catalogue
      await get().loadCatalog()
    } catch (err: any) {
      set({ error: err?.message || 'Erreur lors de la sauvegarde', isLoading: false })
      throw err
    }
  },
  
  toggleFavoriteInCatalog: async (flagId: string) => {
    const flagDef = get().catalog.find(f => f.id === flagId)
    if (!flagDef) return
    
    set({ isLoading: true, error: null })
    try {
      await flagsAPI.toggleFavorite({
        flag_id: flagId,
        is_favorite: !flagDef.isFavorite
      })
      
      // Recharger le catalogue
      await get().loadCatalog()
    } catch (err: any) {
      set({ error: err?.message || 'Erreur lors du toggle favori', isLoading: false })
      throw err
    }
  }
}))
