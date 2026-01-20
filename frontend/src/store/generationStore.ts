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
  
  // État streaming (Task 2 - Story 0.2)
  isGenerating: boolean
  streamingContent: string
  currentStep: 'Prompting' | 'Generating' | 'Validating' | 'Complete'
  isMinimized: boolean
  error: string | null
  currentJobId: string | null
  isInterrupting: boolean  // Task 4 - Story 0.8
  
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
  
  // Actions streaming (Task 2 - Story 0.2)
  startGeneration: (jobId: string) => void
  appendChunk: (chunk: string) => void
  setStep: (step: 'Prompting' | 'Generating' | 'Validating' | 'Complete') => void
  interrupt: () => void
  minimize: () => void
  complete: () => void
  setError: (error: string) => void
  resetStreamingState: () => void
  setInterrupting: (isInterrupting: boolean) => void  // Task 4 - Story 0.8
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

  // État streaming initial (Task 2 - Story 0.2)
  isGenerating: false,
  streamingContent: '',
  currentStep: 'Prompting',
  isMinimized: false,
  error: null,
  currentJobId: null,
  isInterrupting: false,  // Task 4 - Story 0.8

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

  // Actions streaming (Task 2 - Story 0.2)
  startGeneration: (jobId) =>
    set({
      isGenerating: true,
      streamingContent: '',
      currentStep: 'Prompting',
      isMinimized: false,
      error: null,
      currentJobId: jobId,
    }),

  appendChunk: (chunk) =>
    set((state) => ({
      streamingContent: state.streamingContent + chunk,
    })),

  setStep: (step) =>
    set({ currentStep: step }),

  interrupt: () =>
    set({
      isGenerating: false,
      streamingContent: '',
      currentStep: 'Prompting',
      error: null,
      currentJobId: null,
    }),

  minimize: () =>
    set((state) => ({
      isMinimized: !state.isMinimized,
    })),

  complete: () =>
    set({
      isGenerating: false,
      currentStep: 'Complete',
    }),

  setError: (error) =>
    set({
      isGenerating: false,
      error,
    }),

  resetStreamingState: () =>
    set({
      isGenerating: false,
      streamingContent: '',
      currentStep: 'Prompting',
      isMinimized: false,
      error: null,
      currentJobId: null,
      isInterrupting: false,
    }),

  setInterrupting: (isInterrupting) =>
    set({ isInterrupting }),  // Task 4 - Story 0.8
}))


