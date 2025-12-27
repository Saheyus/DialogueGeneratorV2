/**
 * API client pour la configuration.
 */
import apiClient from './client'
import type { LLMModelsListResponse, UnityDialoguesPathResponse } from '../types/api'
import type {
  ContextFieldsResponse,
  ContextFieldSuggestionsResponse,
  ContextPreviewResponse,
} from '../store/contextConfigStore'

export interface DefaultSystemPromptResponse {
  prompt: string
}

export interface ContextPreviewRequest {
  selected_elements: Record<string, string[]>
  field_configs: Record<string, string[]>
  organization_mode?: string
  scene_instruction?: string
  max_tokens?: number
}

/**
 * Liste tous les modèles LLM disponibles.
 */
export async function listLLMModels(): Promise<LLMModelsListResponse> {
  const response = await apiClient.get<LLMModelsListResponse>('/api/v1/config/llm/models')
  return response.data
}

/**
 * Récupère le chemin configuré des dialogues Unity.
 */
export async function getUnityDialoguesPath(): Promise<UnityDialoguesPathResponse> {
  const response = await apiClient.get<UnityDialoguesPathResponse>('/api/v1/config/unity-dialogues-path')
  return response.data
}

/**
 * Configure le chemin des dialogues Unity.
 */
export async function setUnityDialoguesPath(path: string): Promise<UnityDialoguesPathResponse> {
  const response = await apiClient.put<UnityDialoguesPathResponse>('/api/v1/config/unity-dialogues-path', { path })
  return response.data
}

/**
 * Récupère le system prompt par défaut.
 * TODO: Endpoint à ajouter côté backend
 */
export async function getDefaultSystemPrompt(): Promise<DefaultSystemPromptResponse> {
  // Pour l'instant, retourner une valeur par défaut
  // TODO: Implémenter l'endpoint API /api/v1/config/default-system-prompt
  return {
    prompt: "Tu es un assistant expert en écriture de dialogues pour jeux de rôle (RPG).\nTa tâche est de générer un dialogue cohérent avec le contexte fourni et l'instruction utilisateur.\nSi une structure de dialogue spécifique est demandée (ex: PNJ suivi d'un choix PJ), respecte cette structure."
  }
}

/**
 * Récupère les champs disponibles pour un type d'élément.
 */
export async function getContextFields(elementType: string): Promise<ContextFieldsResponse> {
  const response = await apiClient.get<ContextFieldsResponse>(`/api/v1/config/context-fields/${elementType}`)
  return response.data
}

/**
 * Récupère les suggestions de champs selon le contexte.
 */
export async function getFieldSuggestions(
  elementType: string,
  context?: string
): Promise<ContextFieldSuggestionsResponse> {
  const response = await apiClient.post<ContextFieldSuggestionsResponse>(
    '/api/v1/config/context-fields/suggestions',
    {
      element_type: elementType,
      context: context || null,
    }
  )
  return response.data
}

/**
 * Prévisualise le contexte avec une configuration personnalisée.
 */
export async function previewContext(
  request: ContextPreviewRequest
): Promise<ContextPreviewResponse> {
  const response = await apiClient.post<ContextPreviewResponse>(
    '/api/v1/config/context-fields/preview',
    request
  )
  return response.data
}

/**
 * Récupère la configuration par défaut des champs.
 */
export async function getDefaultFieldConfig(): Promise<{
  essential_fields: Record<string, string[]>
  default_fields: Record<string, string[]>
}> {
  const response = await apiClient.get<{
    essential_fields: Record<string, string[]>
    default_fields: Record<string, string[]>
  }>('/api/v1/config/context-fields/default')
  return response.data
}

/**
 * Invalide le cache des champs de contexte.
 */
export async function invalidateContextFieldsCache(elementType?: string): Promise<void> {
  const url = elementType
    ? `/api/v1/config/context-fields/invalidate-cache?element_type=${elementType}`
    : '/api/v1/config/context-fields/invalidate-cache'
  await apiClient.post(url)
}

