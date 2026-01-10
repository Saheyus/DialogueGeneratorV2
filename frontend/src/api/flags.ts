/**
 * Client API pour les flags in-game.
 */
import apiClient from './client'
import type {
  FlagsCatalogResponse,
  UpsertFlagRequest,
  UpsertFlagResponse,
  ToggleFavoriteRequest,
  ToggleFavoriteResponse
} from '../types/flags'

/**
 * Liste les définitions de flags disponibles.
 */
export async function listFlags(params?: {
  q?: string
  category?: string
  favoritesOnly?: boolean
}): Promise<FlagsCatalogResponse> {
  const response = await apiClient.get<FlagsCatalogResponse>(
    '/api/v1/mechanics/flags',
    { params }
  )
  return response.data
}

/**
 * Crée ou met à jour une définition de flag.
 */
export async function upsertFlag(
  request: UpsertFlagRequest
): Promise<UpsertFlagResponse> {
  const response = await apiClient.post<UpsertFlagResponse>(
    '/api/v1/mechanics/flags',
    request
  )
  return response.data
}

/**
 * Active/désactive le statut favori d'un flag.
 */
export async function toggleFavorite(
  request: ToggleFavoriteRequest
): Promise<ToggleFavoriteResponse> {
  const response = await apiClient.post<ToggleFavoriteResponse>(
    '/api/v1/mechanics/flags/toggle-favorite',
    request
  )
  return response.data
}
