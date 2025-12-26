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
  SpeciesResponse,
  SpeciesListResponse,
  CommunityResponse,
  CommunityListResponse,
  RegionListResponse,
  SubLocationListResponse,
  LinkedElementsRequest,
  LinkedElementsResponse,
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

/**
 * Liste toutes les espèces disponibles.
 */
export async function listSpecies(): Promise<SpeciesListResponse> {
  const response = await apiClient.get<SpeciesListResponse>('/api/v1/context/species')
  return response.data
}

/**
 * Récupère une espèce par son nom.
 */
export async function getSpecies(name: string): Promise<SpeciesResponse> {
  const response = await apiClient.get<SpeciesResponse>(`/api/v1/context/species/${encodeURIComponent(name)}`)
  return response.data
}

/**
 * Liste toutes les communautés disponibles.
 */
export async function listCommunities(): Promise<CommunityListResponse> {
  const response = await apiClient.get<CommunityListResponse>('/api/v1/context/communities')
  return response.data
}

/**
 * Récupère une communauté par son nom.
 */
export async function getCommunity(name: string): Promise<CommunityResponse> {
  const response = await apiClient.get<CommunityResponse>(`/api/v1/context/communities/${encodeURIComponent(name)}`)
  return response.data
}

/**
 * Liste toutes les régions disponibles.
 */
export async function listRegions(): Promise<RegionListResponse> {
  const response = await apiClient.get<RegionListResponse>('/api/v1/context/locations/regions')
  return response.data
}

/**
 * Récupère les sous-lieux d'une région.
 */
export async function getSubLocations(regionName: string): Promise<SubLocationListResponse> {
  const response = await apiClient.get<SubLocationListResponse>(
    `/api/v1/context/locations/regions/${encodeURIComponent(regionName)}/sub-locations`
  )
  return response.data
}

/**
 * Suggère des éléments liés à partir de personnages et lieux.
 */
export async function getLinkedElements(request: LinkedElementsRequest): Promise<LinkedElementsResponse> {
  const response = await apiClient.post<LinkedElementsResponse>('/api/v1/context/linked-elements', request)
  return response.data
}

