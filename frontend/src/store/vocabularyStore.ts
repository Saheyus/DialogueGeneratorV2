/**
 * Store Zustand pour gérer le vocabulaire Alteir.
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import * as vocabularyAPI from '../api/vocabulary'
import type {
  VocabularyTerm,
  VocabularyResponse,
} from '../api/vocabulary'

export type PopularityLevel =
  | 'Mondialement'
  | 'Régionalement'
  | 'Localement'
  | 'Communautaire'
  | 'Occulte'

export type VocabularyMode = 'all' | 'auto' | 'none'

export interface VocabularyConfig {
  Mondialement: VocabularyMode
  Régionalement: VocabularyMode
  Localement: VocabularyMode
  Communautaire: VocabularyMode
  Occulte: VocabularyMode
}

interface VocabularyState {
  // État du vocabulaire
  vocabularyConfig: VocabularyConfig
  vocabularyTerms: VocabularyTerm[]
  vocabularyStats: VocabularyResponse['statistics'] | null
  totalTerms: number
  
  // Actions
  setVocabularyConfig: (config: VocabularyConfig) => void
  setLevelMode: (level: PopularityLevel, mode: VocabularyMode) => void
  loadVocabulary: () => Promise<void>
  loadStats: () => Promise<void>
  clearError: () => void
  error: string | null
}

const DEFAULT_VOCABULARY_CONFIG: VocabularyConfig = {
  Mondialement: 'all',
  Régionalement: 'all',
  Localement: 'none',
  Communautaire: 'none',
  Occulte: 'none',
}

const STORAGE_KEY = 'vocabulary_store'

export const useVocabularyStore = create<VocabularyState>()(
  persist(
    (set) => ({
      vocabularyConfig: DEFAULT_VOCABULARY_CONFIG,
      vocabularyTerms: [],
      vocabularyStats: null,
      totalTerms: 0,
      error: null,

      setVocabularyConfig: (config) => {
        set({ vocabularyConfig: config })
      },

      setLevelMode: (level, mode) => {
        set((state) => ({
          vocabularyConfig: {
            ...state.vocabularyConfig,
            [level]: mode,
          },
        }))
      },

      loadVocabulary: async () => {
        try {
          set({ error: null })
          // Charger tous les termes (le filtrage sera fait côté backend lors de la génération)
          const response = await vocabularyAPI.getVocabulary()
          set({
            vocabularyTerms: response.terms,
            totalTerms: response.total,
            vocabularyStats: response.statistics,
          })
        } catch (err) {
          const errorMessage =
            err instanceof Error ? err.message : 'Erreur lors du chargement du vocabulaire'
          set({ error: errorMessage })
          console.error('Erreur lors du chargement du vocabulaire:', err)
        }
      },

      loadStats: async () => {
        try {
          set({ error: null })
          const stats = await vocabularyAPI.getVocabularyStats()
          set({
            vocabularyStats: {
              by_popularité: stats.by_popularité,
              by_category: stats.by_category,
              by_type: stats.by_type,
            },
            totalTerms: stats.total,
          })
        } catch (err) {
          const errorMessage =
            err instanceof Error
              ? err.message
              : 'Erreur lors du chargement des statistiques'
          set({ error: errorMessage })
          console.error('Erreur lors du chargement des statistiques:', err)
        }
      },

      clearError: () => {
        set({ error: null })
      },
    }),
    {
      name: STORAGE_KEY,
      // Ne persister que vocabularyConfig, pas les autres états temporaires
      partialize: (state) => ({
        vocabularyConfig: state.vocabularyConfig,
      }),
    }
  )
)

