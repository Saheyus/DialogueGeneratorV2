/**
 * Store Zustand pour gérer l'état de génération.
 */
import { create } from 'zustand'
import type { SceneSelection } from '../types/generation'

interface GenerationState {
  // Sélection de scène
  sceneSelection: SceneSelection
  
  // Structure de dialogue
  dialogueStructure: string[]
  
  // System prompt
  systemPromptOverride: string | null
  defaultSystemPrompt: string | null
  
  // Actions
  setSceneSelection: (selection: Partial<SceneSelection>) => void
  setDialogueStructure: (structure: string[]) => void
  setSystemPromptOverride: (prompt: string | null) => void
  setDefaultSystemPrompt: (prompt: string | null) => void
  resetSystemPrompt: () => void
}

const defaultSceneSelection: SceneSelection = {
  characterA: null,
  characterB: null,
  sceneRegion: null,
  subLocation: null,
}

const defaultDialogueStructure: string[] = ['PNJ', 'PJ', 'Stop', '', '', '']

export const useGenerationStore = create<GenerationState>((set) => ({
  sceneSelection: defaultSceneSelection,
  dialogueStructure: defaultDialogueStructure,
  systemPromptOverride: null,
  defaultSystemPrompt: null,

  setSceneSelection: (selection) =>
    set((state) => ({
      sceneSelection: { ...state.sceneSelection, ...selection },
    })),

  setDialogueStructure: (structure) =>
    set({ dialogueStructure: structure }),

  setSystemPromptOverride: (prompt) =>
    set({ systemPromptOverride: prompt }),

  setDefaultSystemPrompt: (prompt) =>
    set({ defaultSystemPrompt: prompt }),

  resetSystemPrompt: () =>
    set((state) => ({
      systemPromptOverride: state.defaultSystemPrompt,
    })),
}))

