/**
 * Store Zustand pour gérer les sélections de contexte.
 */
import { create } from 'zustand'
import type { ContextSelection } from '../types/api'

interface ContextState {
  selections: ContextSelection
  setSelections: (selections: ContextSelection) => void
  toggleCharacter: (name: string) => void
  toggleLocation: (name: string) => void
  toggleItem: (name: string) => void
  clearSelections: () => void
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

  clearSelections: () => {
    set({ selections: defaultSelections })
  },
}))

