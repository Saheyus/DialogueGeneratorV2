/**
 * Store Zustand pour gérer l'état de génération.
 */
import { create } from 'zustand'
import type { SceneSelection } from '../types/generation'
import type { GenerateDialogueVariantsResponse, InteractionResponse } from '../types/api'

interface GenerationState {
  // Sélection de scène
  sceneSelection: SceneSelection
  
  // Structure de dialogue
  dialogueStructure: string[]
  
  // System prompt
  systemPromptOverride: string | null
  defaultSystemPrompt: string | null
  
  // Prompt estimé
  estimatedPrompt: string | null
  estimatedTokens: number | null
  isEstimating: boolean
  
  // Résultats de génération
  variantsResponse: GenerateDialogueVariantsResponse | null
  interactionsResponse: InteractionResponse[] | null
  tokensUsed: number | null
  
  // Actions
  setSceneSelection: (selection: Partial<SceneSelection>) => void
  setDialogueStructure: (structure: string[]) => void
  setSystemPromptOverride: (prompt: string | null) => void
  setDefaultSystemPrompt: (prompt: string | null) => void
  resetSystemPrompt: () => void
  setEstimatedPrompt: (prompt: string | null, tokens: number | null, isEstimating: boolean) => void
  setVariantsResponse: (response: GenerateDialogueVariantsResponse | null) => void
  setInteractionsResponse: (response: InteractionResponse[] | null) => void
  setTokensUsed: (tokens: number | null) => void
  clearGenerationResults: () => void
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
  estimatedPrompt: null,
  estimatedTokens: null,
  isEstimating: false,
  variantsResponse: null,
  interactionsResponse: null,
  tokensUsed: null,

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

  setEstimatedPrompt: (prompt, tokens, isEstimating) =>
    set({ estimatedPrompt: prompt, estimatedTokens: tokens, isEstimating }),

  setVariantsResponse: (response) =>
    set({ variantsResponse: response }),

  setInteractionsResponse: (response) =>
    set({ interactionsResponse: response }),

  setTokensUsed: (tokens) =>
    set({ tokensUsed: tokens }),

  clearGenerationResults: () =>
    set({ variantsResponse: null, interactionsResponse: null, tokensUsed: null }),
}))

