/**
 * API client pour la configuration.
 */
import apiClient from './client'
import type { LLMModelsListResponse } from '../types/api'

/**
 * Liste tous les modèles LLM disponibles.
 */
export async function listLLMModels(): Promise<LLMModelsListResponse> {
  const response = await apiClient.get<LLMModelsListResponse>('/api/v1/config/llm/models')
  return response.data
}

