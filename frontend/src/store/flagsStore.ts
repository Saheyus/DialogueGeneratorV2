/**
 * Store Zustand pour la gestion des flags in-game.
 */
import { create } from 'zustand'
import type { FlagDefinition, InGameFlag, FlagSnapshot } from '../types/flags'
import * as flagsAPI from '../api/flags'
import { getErrorMessage } from '../types/errors'

const FLAGS_SELECTION_STORAGE_KEY = 'flags_selection'

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
  removeFlag: (flagId: string) => void
  clearFlags: () => void
  getSelectedFlagsArray: () => InGameFlag[]
  
  // Gestion du catalogue
  upsertDefinition: (def: FlagDefinition) => Promise<void>
  toggleFavoriteInCatalog: (flagId: string) => Promise<void>
  
  // Import/Export snapshots
  importFromSnapshot: (snapshot: FlagSnapshot) => void
  exportToSnapshot: () => FlagSnapshot
  
  // Persistance localStorage
  saveSelection: () => void
  loadSelection: () => void
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
      // Charger la sélection sauvegardée après le chargement du catalogue
      get().loadSelection()
    } catch (err: unknown) {
      set({ error: getErrorMessage(err), isLoading: false })
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
        // Sélectionner avec valeur par défaut (utiliser defaultValueParsed si disponible)
        const currentValue = newSelectedFlags.get(flagId)?.value
        let newValue: boolean
        if (typeof currentValue === 'boolean') {
          // Toggle si déjà sélectionné
          newValue = !currentValue
        } else {
          // Utiliser la valeur par défaut parsée ou true par défaut
          newValue = typeof flagDef.defaultValueParsed === 'boolean' 
            ? flagDef.defaultValueParsed 
            : true
        }
        
        newSelectedFlags.set(flagId, {
          id: flagId,
          value: newValue,
          category: flagDef.category,
          timestamp: new Date().toISOString()
        })
      }
      
      const newState = { selectedFlags: newSelectedFlags }
      // Sauvegarder dans localStorage
      get().saveSelection()
      return newState
    })
  },
  
  setNumericFlag: (flagId: string, value: number) => {
    set(state => {
      const newSelectedFlags = new Map(state.selectedFlags)
      const flagDef = state.catalog.find(f => f.id === flagId)
      
      if (!flagDef) return state
      
      // Sélectionner le flag automatiquement si modifié
      newSelectedFlags.set(flagId, {
        id: flagId,
        value,
        category: flagDef.category,
        timestamp: new Date().toISOString()
      })
      
      const newState = { selectedFlags: newSelectedFlags }
      // Sauvegarder dans localStorage
      get().saveSelection()
      return newState
    })
  },
  
  setStringFlag: (flagId: string, value: string) => {
    set(state => {
      const newSelectedFlags = new Map(state.selectedFlags)
      const flagDef = state.catalog.find(f => f.id === flagId)
      
      if (!flagDef) return state
      
      // Sélectionner le flag si pas déjà sélectionné
      newSelectedFlags.set(flagId, {
        id: flagId,
        value,
        category: flagDef.category,
        timestamp: new Date().toISOString()
      })
      
      const newState = { selectedFlags: newSelectedFlags }
      // Sauvegarder dans localStorage
      get().saveSelection()
      return newState
    })
  },
  
  clearFlags: () => {
    set({ selectedFlags: new Map() })
    get().saveSelection()
  },
  
  removeFlag: (flagId: string) => {
    set(state => {
      const newSelectedFlags = new Map(state.selectedFlags)
      newSelectedFlags.delete(flagId)
      const newState = { selectedFlags: newSelectedFlags }
      // Sauvegarder dans localStorage
      get().saveSelection()
      return newState
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
    } catch (err: unknown) {
      set({ error: getErrorMessage(err), isLoading: false })
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
    } catch (err: unknown) {
      set({ error: getErrorMessage(err), isLoading: false })
      throw err
    }
  },
  
  importFromSnapshot: (snapshot: FlagSnapshot) => {
    set(state => {
      const newSelectedFlags = new Map<string, InGameFlag>()
      
      // Charger le catalogue pour obtenir les catégories
      for (const [flagId, value] of Object.entries(snapshot.flags)) {
        const flagDef = state.catalog.find(f => f.id === flagId)
        if (flagDef) {
          newSelectedFlags.set(flagId, {
            id: flagId,
            value,
            category: flagDef.category,
            timestamp: new Date().toISOString()
          })
        }
      }
      
      const newState = { selectedFlags: newSelectedFlags }
      // Sauvegarder dans localStorage
      get().saveSelection()
      return newState
    })
  },
  
  exportToSnapshot: () => {
    const state = get()
    const flags: Record<string, boolean | number | string> = {}
    
    for (const flag of state.selectedFlags.values()) {
      flags[flag.id] = flag.value
    }
    
    return {
      version: '1.0',
      timestamp: new Date().toISOString(),
      flags
    } as FlagSnapshot
  },
  
  saveSelection: () => {
    try {
      const state = get()
      const selectionArray = Array.from(state.selectedFlags.values())
      localStorage.setItem(FLAGS_SELECTION_STORAGE_KEY, JSON.stringify(selectionArray))
    } catch (err) {
      console.error('Erreur lors de la sauvegarde de la sélection de flags:', err)
    }
  },
  
  loadSelection: () => {
    try {
      const saved = localStorage.getItem(FLAGS_SELECTION_STORAGE_KEY)
      if (saved) {
        const selectionArray = JSON.parse(saved) as InGameFlag[]
        const newSelectedFlags = new Map<string, InGameFlag>()
        
        for (const flag of selectionArray) {
          newSelectedFlags.set(flag.id, flag)
        }
        
        set({ selectedFlags: newSelectedFlags })
      }
    } catch (err) {
      console.error('Erreur lors du chargement de la sélection de flags:', err)
    }
  }
}))
