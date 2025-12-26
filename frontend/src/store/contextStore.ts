/**
 * Store Zustand pour gérer les sélections de contexte.
 */
import { create } from 'zustand'
import type { ContextSelection } from '../types/api'

interface ContextState {
  selections: ContextSelection
  selectedRegion: string | null
  selectedSubLocations: string[]
  setSelections: (selections: ContextSelection) => void
  toggleCharacter: (name: string) => void
  toggleLocation: (name: string) => void
  toggleItem: (name: string) => void
  toggleSpecies: (name: string) => void
  toggleCommunity: (name: string) => void
  setRegion: (regionName: string | null) => void
  toggleSubLocation: (name: string) => void
  applyLinkedElements: (elements: string[]) => void
  clearSelections: () => void
  restoreState: (selections: ContextSelection, region: string | null, subLocations: string[]) => void
}

const defaultSelections: ContextSelection = {
  characters: [],
  locations: [],
  items: [],
  species: [],
  communities: [],
  dialogues_examples: [],
}

export const useContextStore = create<ContextState>((set) => ({
  selections: defaultSelections,
  selectedRegion: null,
  selectedSubLocations: [],

  setSelections: (selections: ContextSelection) => {
    set({ selections })
  },

  toggleCharacter: (name: string) => {
    set((state) => {
      const characters = state.selections.characters.includes(name)
        ? state.selections.characters.filter((n) => n !== name)
        : [...state.selections.characters, name]
      return {
        selections: {
          ...state.selections,
          characters,
        },
      }
    })
  },

  toggleLocation: (name: string) => {
    set((state) => {
      const locations = state.selections.locations.includes(name)
        ? state.selections.locations.filter((n) => n !== name)
        : [...state.selections.locations, name]
      return {
        selections: {
          ...state.selections,
          locations,
        },
      }
    })
  },

  toggleItem: (name: string) => {
    set((state) => {
      const items = state.selections.items.includes(name)
        ? state.selections.items.filter((n) => n !== name)
        : [...state.selections.items, name]
      return {
        selections: {
          ...state.selections,
          items,
        },
      }
    })
  },

  toggleSpecies: (name: string) => {
    set((state) => {
      const species = state.selections.species.includes(name)
        ? state.selections.species.filter((n) => n !== name)
        : [...state.selections.species, name]
      return {
        selections: {
          ...state.selections,
          species,
        },
      }
    })
  },

  toggleCommunity: (name: string) => {
    set((state) => {
      const communities = state.selections.communities.includes(name)
        ? state.selections.communities.filter((n) => n !== name)
        : [...state.selections.communities, name]
      return {
        selections: {
          ...state.selections,
          communities,
        },
      }
    })
  },

  setRegion: (regionName: string | null) => {
    set((state) => {
      // Retirer les sous-lieux de la sélection si on change de région
      const locations = regionName === null
        ? state.selections.locations.filter((loc) => !state.selectedSubLocations.includes(loc))
        : state.selections.locations
      
      return {
        selectedRegion: regionName,
        selectedSubLocations: [],
        selections: {
          ...state.selections,
          locations,
        },
      }
    })
  },

  toggleSubLocation: (name: string) => {
    set((state) => {
      const subLocations = state.selectedSubLocations.includes(name)
        ? state.selectedSubLocations.filter((n) => n !== name)
        : [...state.selectedSubLocations, name]
      
      // Mettre à jour aussi la liste des locations dans selections
      const locations = state.selections.locations.includes(name)
        ? state.selections.locations.filter((n) => n !== name)
        : [...state.selections.locations, name]
      
      return {
        selectedSubLocations: subLocations,
        selections: {
          ...state.selections,
          locations,
        },
      }
    })
  },

  applyLinkedElements: (elements: string[]) => {
    set((state) => {
      // Ajouter tous les éléments liés aux sélections appropriées
      // On ne peut pas déterminer automatiquement la catégorie, donc on les ajoute tous aux locations
      // pour l'instant. Dans une implémentation plus sophistiquée, on pourrait avoir une logique
      // pour déterminer la catégorie de chaque élément.
      const newLocations = [...new Set([...state.selections.locations, ...elements])]
      
      return {
        selections: {
          ...state.selections,
          locations: newLocations,
        },
      }
    })
  },

  clearSelections: () => {
    set({ 
      selections: defaultSelections,
      selectedRegion: null,
      selectedSubLocations: [],
    })
  },

  restoreState: (selections: ContextSelection, region: string | null, subLocations: string[]) => {
    set({
      selections,
      selectedRegion: region,
      selectedSubLocations: subLocations,
    })
  },
}))

