/**
 * Store Zustand pour gérer l'état de génération.
 */
import { create } from 'zustand'
import type { SceneSelection } from '../types/generation'
import type { GenerateUnityDialogueResponse, RawPrompt } from '../types/api'
import type { PromptStructure } from '../types/prompt'

interface GenerationState {
  // Sélection de scène
  sceneSelection: SceneSelection
  
  // Structure de dialogue
  dialogueStructure: string[]
  
  // System prompt
  systemPromptOverride: string | null
  defaultSystemPrompt: string | null
  
  // Source de vérité unique pour le prompt
  rawPrompt: RawPrompt | null
  structuredPrompt: PromptStructure | null
  promptHash: string | null
  tokenCount: number | null
  isEstimating: boolean
  
  // Résultats de génération
  unityDialogueResponse: GenerateUnityDialogueResponse | null
  tokensUsed: number | null
  
  // Actions
  setSceneSelection: (selection: Partial<SceneSelection>) => void
  setDialogueStructure: (structure: string[]) => void
  setSystemPromptOverride: (prompt: string | null) => void
  setDefaultSystemPrompt: (prompt: string | null) => void
  resetSystemPrompt: () => void
  setRawPrompt: (prompt: RawPrompt | null, tokens: number | null, hash: string | null, isEstimating: boolean, structuredPrompt?: PromptStructure | null) => void
  setUnityDialogueResponse: (response: GenerateUnityDialogueResponse | null) => void
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
  rawPrompt: null,
  structuredPrompt: null,
  promptHash: null,
  tokenCount: null,
  isEstimating: false,
  unityDialogueResponse: null,
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

  setRawPrompt: (prompt, tokens, hash, isEstimating, structuredPrompt = null) =>
    set({ rawPrompt: prompt, structuredPrompt, tokenCount: tokens, promptHash: hash, isEstimating }),

  setUnityDialogueResponse: (response) =>
    set({ unityDialogueResponse: response }),

  setTokensUsed: (tokens) =>
    set({ tokensUsed: tokens }),

  clearGenerationResults: () =>
    set({ unityDialogueResponse: null, tokensUsed: null }),
}))


