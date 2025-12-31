/**
 * API client pour la génération de dialogues.
 */
import apiClient from './client'
import { API_TIMEOUTS } from '../constants'
import type {
  ContextSelection,
  GenerateUnityDialogueRequest,
  GenerateUnityDialogueResponse,
  ExportUnityDialogueRequest,
  ExportUnityDialogueResponse,
  EstimateTokensRequest,
  EstimateTokensResponse
} from '../types/api'

// NOTE: generateDialogueVariants et generateInteractionVariants ont été supprimés. Utiliser generateUnityDialogue à la place.

/**
 * Génère un nœud de dialogue au format Unity JSON.
 * 
 * Utilise un timeout étendu (5 minutes) pour permettre aux générations LLM longues de se terminer.
 */
export async function generateUnityDialogue(
  request: GenerateUnityDialogueRequest
): Promise<GenerateUnityDialogueResponse> {
  const response = await apiClient.post<GenerateUnityDialogueResponse>(
    '/api/v1/dialogues/generate/unity-dialogue',
    request,
    {
      timeout: API_TIMEOUTS.LLM_GENERATION, // 5 minutes pour les générations LLM
    }
  )
  return response.data
}

/**
 * Estime le nombre de tokens pour un contexte donné.
 */
export async function estimateTokens(
  request: EstimateTokensRequest
): Promise<EstimateTokensResponse> {
  const response = await apiClient.post<EstimateTokensResponse>('/api/v1/dialogues/estimate-tokens', request)
  return response.data
}


/**
 * Exporte un dialogue Unity JSON vers un fichier.
 */
export async function exportUnityDialogue(
  request: ExportUnityDialogueRequest
): Promise<ExportUnityDialogueResponse> {
  const response = await apiClient.post<ExportUnityDialogueResponse>(
    '/api/v1/dialogues/unity/export',
    request
  )
  return response.data
}

