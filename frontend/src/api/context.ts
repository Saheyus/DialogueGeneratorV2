/**
 * API client pour le contexte GDD (personnages, lieux, objets).
 */
import apiClient from './client'
import type {
  CharacterResponse,
  CharacterListResponse,
  LocationResponse,
  LocationListResponse,
  ItemResponse,
  ItemListResponse,
} from '../types/api'

/**
 * Liste tous les personnages disponibles.
 */
export async function listCharacters(): Promise<CharacterListResponse> {
  const response = await apiClient.get<CharacterListResponse>('/api/v1/context/characters')
  return response.data
}

/**
 * Récupère un personnage par son nom.
 */
export async function getCharacter(name: string): Promise<CharacterResponse> {
  const response = await apiClient.get<CharacterResponse>(`/api/v1/context/characters/${encodeURIComponent(name)}`)
  return response.data
}

/**
 * Liste tous les lieux disponibles.
 */
export async function listLocations(): Promise<LocationListResponse> {
  const response = await apiClient.get<LocationListResponse>('/api/v1/context/locations')
  return response.data
}

/**
 * Récupère un lieu par son nom.
 */
export async function getLocation(name: string): Promise<LocationResponse> {
  const response = await apiClient.get<LocationResponse>(`/api/v1/context/locations/${encodeURIComponent(name)}`)
  return response.data
}

/**
 * Liste tous les objets disponibles.
 */
export async function listItems(): Promise<ItemListResponse> {
  const response = await apiClient.get<ItemListResponse>('/api/v1/context/items')
  return response.data
}

/**
 * Récupère un objet par son nom.
 * Note: L'endpoint API n'existe pas encore, on filtre depuis la liste.
 */
export async function getItem(name: string): Promise<ItemResponse> {
  const listResponse = await listItems()
  const item = listResponse.items.find((item) => item.name === name)
  if (!item) {
    throw new Error(`Item "${name}" not found`)
  }
  return item
}

