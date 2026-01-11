/**
 * API client pour les endpoints de gestion de graphes.
 */
import axios from 'axios'
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

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:4242'

/**
 * Charge un dialogue Unity JSON et le convertit en graphe.
 */
export async function loadGraph(request: LoadGraphRequest): Promise<LoadGraphResponse> {
  const response = await axios.post<LoadGraphResponse>(
    `${API_BASE_URL}/api/v1/unity-dialogues/graph/load`,
    request
  )
  return response.data
}

/**
 * Sauvegarde un graphe modifié (reconvertit en Unity JSON).
 */
export async function saveGraph(request: SaveGraphRequest): Promise<SaveGraphResponse> {
  const response = await axios.post<SaveGraphResponse>(
    `${API_BASE_URL}/api/v1/unity-dialogues/graph/save`,
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
  const response = await axios.post<GenerateNodeResponse>(
    `${API_BASE_URL}/api/v1/unity-dialogues/graph/generate-node`,
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
  const response = await axios.post<ValidateGraphResponse>(
    `${API_BASE_URL}/api/v1/unity-dialogues/graph/validate`,
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
  const response = await axios.post<CalculateLayoutResponse>(
    `${API_BASE_URL}/api/v1/unity-dialogues/graph/calculate-layout`,
    request
  )
  return response.data
}
