/**
 * API client pour la génération de dialogues.
 */
import apiClient from './client'
import type {
  GenerateDialogueVariantsRequest,
  GenerateDialogueVariantsResponse,
  GenerateInteractionVariantsRequest,
  InteractionResponse,
  ContextSelection,
} from '../types/api'

/**
 * Génère des variantes de dialogue texte.
 */
export async function generateDialogueVariants(
  request: GenerateDialogueVariantsRequest
): Promise<GenerateDialogueVariantsResponse> {
  const response = await apiClient.post<GenerateDialogueVariantsResponse>(
    '/api/v1/dialogues/generate/variants',
    request
  )
  return response.data
}

/**
 * Génère des interactions structurées.
 */
export async function generateInteractionVariants(
  request: GenerateInteractionVariantsRequest
): Promise<InteractionResponse[]> {
  const response = await apiClient.post<InteractionResponse[]>(
    '/api/v1/dialogues/generate/interactions',
    request
  )
  return response.data
}

/**
 * Estime le nombre de tokens pour un contexte donné.
 */
export async function estimateTokens(
  contextSelections: ContextSelection,
  userInstructions: string,
  maxContextTokens: number
): Promise<{ context_tokens: number; total_estimated_tokens: number }> {
  const response = await apiClient.post('/api/v1/dialogues/estimate-tokens', {
    context_selections: contextSelections,
    user_instructions: userInstructions,
    max_context_tokens: maxContextTokens,
  })
  return response.data
}

