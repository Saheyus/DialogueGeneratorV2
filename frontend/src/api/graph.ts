/**
 * API client pour les endpoints de gestion de graphes.
 */
import apiClient from './client'
import type {
  LoadGraphRequest,
  LoadGraphResponse,
  SaveGraphRequest,
  SaveGraphResponse,
  GenerateNodeRequest,
  GenerateNodeResponse,
  ValidateGraphRequest,
  ValidateGraphResponse,
  CalculateLayoutRequest,
  CalculateLayoutResponse,
} from '../types/graph'

/**
 * Charge un dialogue Unity JSON et le convertit en graphe.
 */
export async function loadGraph(request: LoadGraphRequest): Promise<LoadGraphResponse> {
  const response = await apiClient.post<LoadGraphResponse>(
    `/api/v1/unity-dialogues/graph/load`,
    request
  )
  return response.data
}

/**
 * Sauvegarde un graphe modifié (reconvertit en Unity JSON).
 */
export async function saveGraph(request: SaveGraphRequest): Promise<SaveGraphResponse> {
  const response = await apiClient.post<SaveGraphResponse>(
    `/api/v1/unity-dialogues/graph/save`,
    request
  )
  return response.data
}

/**
 * Génère un nœud en contexte avec l'IA.
 */
export async function generateNode(
  request: GenerateNodeRequest
): Promise<GenerateNodeResponse> {
  const response = await apiClient.post<GenerateNodeResponse>(
    `/api/v1/unity-dialogues/graph/generate-node`,
    request
  )
  return response.data
}

/**
 * Valide un graphe (nœuds orphelins, références cassées, cycles).
 */
export async function validateGraph(
  request: ValidateGraphRequest
): Promise<ValidateGraphResponse> {
  const response = await apiClient.post<ValidateGraphResponse>(
    `/api/v1/unity-dialogues/graph/validate`,
    request
  )
  return response.data
}

/**
 * Calcule un layout automatique pour le graphe.
 */
export async function calculateLayout(
  request: CalculateLayoutRequest
): Promise<CalculateLayoutResponse> {
  const response = await apiClient.post<CalculateLayoutResponse>(
    `/api/v1/unity-dialogues/graph/calculate-layout`,
    request
  )
  return response.data
}
