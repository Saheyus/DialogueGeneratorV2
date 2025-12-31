/**
 * API client pour le vocabulaire Alteir et les guides narratifs.
 */
import apiClient from './client'

export interface VocabularyTerm {
  term: string
  definition: string
  popularité: string
  category: string
  type: string
  origin: string
}

export interface VocabularyResponse {
  terms: VocabularyTerm[]
  total: number
  filtered_count: number
  min_popularité: string
  statistics: {
    by_popularité: Record<string, number>
    by_category: Record<string, number>
    by_type: Record<string, number>
  }
}

export interface VocabularySyncResponse {
  success: boolean
  terms_count: number
  last_sync: string | null
  error: string | null
}

export interface NarrativeGuideResponse {
  dialogue_guide: string
  narrative_guide: string
  rules: {
    ton: string[]
    structure: string[]
    interdits: string[]
    principes: string[]
  }
  last_sync: string | null
}

export interface NarrativeGuidesSyncResponse {
  success: boolean
  dialogue_guide_length: number
  narrative_guide_length: number
  last_sync: string | null
  error: string | null
}

export interface VocabularyStatsResponse {
  total: number
  by_popularité: Record<string, number>
  by_category: Record<string, number>
  by_type: Record<string, number>
}

/**
 * Récupère le vocabulaire Alteir, filtré par niveau de popularité.
 */
export async function getVocabulary(
  minPopularité?: string
): Promise<VocabularyResponse> {
  const params = minPopularité ? { min_popularité: minPopularité } : {}
  const response = await apiClient.get<VocabularyResponse>('/api/vocabulary', {
    params
  })
  return response.data
}

/**
 * Synchronise le vocabulaire depuis Notion.
 */
export async function syncVocabulary(): Promise<VocabularySyncResponse> {
  const response = await apiClient.post<VocabularySyncResponse>(
    '/api/vocabulary/sync'
  )
  return response.data
}

/**
 * Récupère les statistiques du vocabulaire.
 */
export async function getVocabularyStats(): Promise<VocabularyStatsResponse> {
  const response = await apiClient.get<VocabularyStatsResponse>(
    '/api/vocabulary/stats'
  )
  return response.data
}

/**
 * Récupère les guides narratifs.
 */
export async function getNarrativeGuides(): Promise<NarrativeGuideResponse> {
  const response = await apiClient.get<NarrativeGuideResponse>(
    '/api/narrative-guides'
  )
  return response.data
}

/**
 * Récupère uniquement les règles extraites des guides.
 */
export async function getExtractedRules(): Promise<{
  ton: string[]
  structure: string[]
  interdits: string[]
  principes: string[]
}> {
  const response = await apiClient.get<{
    ton: string[]
    structure: string[]
    interdits: string[]
    principes: string[]
  }>('/api/narrative-guides/rules')
  return response.data
}

/**
 * Synchronise les guides narratifs depuis Notion.
 */
export async function syncNarrativeGuides(): Promise<NarrativeGuidesSyncResponse> {
  const response = await apiClient.post<NarrativeGuidesSyncResponse>(
    '/api/narrative-guides/sync'
  )
  return response.data
}

