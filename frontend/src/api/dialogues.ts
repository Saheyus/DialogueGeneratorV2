/**
 * API client pour la génération de dialogues.
 */
import apiClient from './client'
import type {
  GenerateDialogueVariantsRequest,
  GenerateDialogueVariantsResponse,
  ContextSelection,
  GenerateUnityDialogueRequest,
  GenerateUnityDialogueResponse,
  ExportUnityDialogueRequest,
  ExportUnityDialogueResponse,
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

// NOTE: generateInteractionVariants a été supprimé. Utiliser generateUnityDialogue à la place.

/**
 * Génère un nœud de dialogue au format Unity JSON.
 */
export async function generateUnityDialogue(
  request: GenerateUnityDialogueRequest
): Promise<GenerateUnityDialogueResponse> {
  const response = await apiClient.post<GenerateUnityDialogueResponse>(
    '/api/v1/dialogues/generate/unity-dialogue',
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
  maxContextTokens: number,
  systemPromptOverride?: string | null,
  fieldConfigs?: Record<string, string[]> | null,
  organizationMode?: string | null
): Promise<{ context_tokens: number; total_estimated_tokens: number; estimated_prompt?: string | null }> {
  const response = await apiClient.post('/api/v1/dialogues/estimate-tokens', {
    context_selections: contextSelections,
    user_instructions: userInstructions,
    max_context_tokens: maxContextTokens,
    system_prompt_override: systemPromptOverride || undefined,
    field_configs: fieldConfigs || undefined,
    organization_mode: organizationMode || undefined,
  })
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

