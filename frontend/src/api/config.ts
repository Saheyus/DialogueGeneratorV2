/**
 * API client pour la configuration.
 */
import apiClient from './client'
import type { LLMModelsListResponse, UnityDialoguesPathResponse } from '../types/api'

export interface DefaultSystemPromptResponse {
  prompt: string
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

