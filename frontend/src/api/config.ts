/**
 * API client pour la configuration.
 */
import apiClient from './client'
import type { LLMModelsListResponse, UnityDialoguesPathResponse } from '../types/api'

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

