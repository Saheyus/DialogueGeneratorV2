/**
 * Store Zustand pour gérer les sélections de contexte.
 */
import { create } from 'zustand'
import type { 
  ContextSelection,
  CharacterResponse,
  LocationResponse,
  ItemResponse,
  SpeciesResponse,
  CommunityResponse,
} from '../types/api'

interface ContextState {
  selections: ContextSelection
  selectedRegion: string | null
  selectedSubLocations: string[]
  // Listes des éléments disponibles (chargées depuis ContextSelector)
  characters: CharacterResponse[]
  locations: LocationResponse[]
  items: ItemResponse[]
  species: SpeciesResponse[]
  communities: CommunityResponse[]
  setSelections: (selections: ContextSelection) => void
  setElementLists: (lists: {
    characters: CharacterResponse[]
    locations: LocationResponse[]
    items: ItemResponse[]
    species: SpeciesResponse[]
    communities: CommunityResponse[]
  }) => void
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

export const useContextStore = create<ContextState>((set, get) => ({
  selections: defaultSelections,
  selectedRegion: null,
  selectedSubLocations: [],
  characters: [],
  locations: [],
  items: [],
  species: [],
  communities: [],

  setSelections: (selections: ContextSelection) => {
    set({ selections })
  },

  setElementLists: (lists) => {
    set({
      characters: lists.characters,
      locations: lists.locations,
      items: lists.items,
      species: lists.species,
      communities: lists.communities,
    })
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
      const newSelections = { ...state.selections }
      
      // Déterminer le type de chaque élément en cherchant dans les listes du store
      for (const elementName of elements) {
        // Chercher dans chaque catégorie (ordre important)
        if (state.characters.some((char) => char.name === elementName)) {
          if (!newSelections.characters.includes(elementName)) {
            newSelections.characters = [...newSelections.characters, elementName]
          }
        } else if (state.locations.some((loc) => loc.name === elementName)) {
          if (!newSelections.locations.includes(elementName)) {
            newSelections.locations = [...newSelections.locations, elementName]
          }
        } else if (state.items.some((item) => item.name === elementName)) {
          if (!newSelections.items.includes(elementName)) {
            newSelections.items = [...newSelections.items, elementName]
          }
        } else if (state.species.some((spec) => spec.name === elementName)) {
          if (!newSelections.species.includes(elementName)) {
            newSelections.species = [...newSelections.species, elementName]
          }
        } else if (state.communities.some((comm) => comm.name === elementName)) {
          if (!newSelections.communities.includes(elementName)) {
            newSelections.communities = [...newSelections.communities, elementName]
          }
        } else {
          console.warn(`Élément "${elementName}" non trouvé dans les listes, ignoré`)
        }
      }
      
      return {
        selections: newSelections,
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

