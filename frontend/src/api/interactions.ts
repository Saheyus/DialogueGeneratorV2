/**
 * API client pour les interactions.
 */
import apiClient from './client'
import type { InteractionResponse, InteractionListResponse } from '../types/api'

/**
 * Liste toutes les interactions.
 */
export async function listInteractions(): Promise<InteractionListResponse> {
  const response = await apiClient.get<InteractionListResponse>('/api/v1/interactions')
  return response.data
}

/**
 * Récupère une interaction par son ID.
 */
export async function getInteraction(interactionId: string): Promise<InteractionResponse> {
  const response = await apiClient.get<InteractionResponse>(`/api/v1/interactions/${interactionId}`)
  return response.data
}

/**
 * Crée une nouvelle interaction.
 */
export async function createInteraction(
  interaction: Partial<InteractionResponse>
): Promise<InteractionResponse> {
  const response = await apiClient.post<InteractionResponse>('/api/v1/interactions', interaction)
  return response.data
}

/**
 * Met à jour une interaction existante.
 */
export async function updateInteraction(
  interactionId: string,
  interaction: Partial<InteractionResponse>
): Promise<InteractionResponse> {
  const response = await apiClient.put<InteractionResponse>(
    `/api/v1/interactions/${interactionId}`,
    interaction
  )
  return response.data
}

/**
 * Supprime une interaction.
 */
export async function deleteInteraction(interactionId: string): Promise<void> {
  await apiClient.delete(`/api/v1/interactions/${interactionId}`)
}

/**
 * Récupère les interactions parentes d'une interaction.
 */
export async function getInteractionParents(interactionId: string): Promise<{ parents: string[] }> {
  const response = await apiClient.get(`/api/v1/interactions/${interactionId}/parents`)
  return response.data
}

/**
 * Récupère les interactions enfants d'une interaction.
 */
export async function getInteractionChildren(interactionId: string): Promise<{ children: string[] }> {
  const response = await apiClient.get(`/api/v1/interactions/${interactionId}/children`)
  return response.data
}

