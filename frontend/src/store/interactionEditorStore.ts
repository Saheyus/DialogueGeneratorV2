/**
 * Store Zustand pour gérer l'état de l'éditeur d'interactions.
 */
import { create } from 'zustand'
import type { InteractionResponse } from '../types/api'

interface InteractionEditorState {
  currentInteraction: InteractionResponse | null
  isDirty: boolean
  
  // Actions
  setCurrentInteraction: (interaction: InteractionResponse | null) => void
  setDirty: (dirty: boolean) => void
  reset: () => void
}

export const useInteractionEditorStore = create<InteractionEditorState>((set) => ({
  currentInteraction: null,
  isDirty: false,

  setCurrentInteraction: (interaction) =>
    set({ currentInteraction: interaction, isDirty: false }),

  setDirty: (dirty) =>
    set({ isDirty: dirty }),

  reset: () =>
    set({ currentInteraction: null, isDirty: false }),
}))

