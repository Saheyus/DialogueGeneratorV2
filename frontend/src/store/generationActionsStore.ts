/**
 * Store Zustand pour exposer les actions du GenerationPanel vers Dashboard.
 */
import { create } from 'zustand'

export interface GenerationPanelActions {
  handleGenerate: (() => void) | null
  handlePreview: (() => void) | null
  handleExportUnity: (() => void) | null
  handleReset: (() => void) | null
  isLoading: boolean
  isDirty: boolean
}

interface GenerationActionsState {
  actions: GenerationPanelActions
  setActions: (actions: GenerationPanelActions) => void
}

export const useGenerationActionsStore = create<GenerationActionsState>((set) => ({
  actions: {
    handleGenerate: null,
    handlePreview: null,
    handleExportUnity: null,
    handleReset: null,
    isLoading: false,
    isDirty: false,
  },
  setActions: (actions) => set({ actions }),
}))



