/**
 * Store Zustand pour gérer le vocabulaire Alteir et les guides narratifs.
 */
import { create } from 'zustand'
import * as vocabularyAPI from '../api/vocabulary'
import type {
  VocabularyTerm,
  VocabularyResponse,
  NarrativeGuideResponse,
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
  includeNarrativeGuides: boolean
  vocabularyTerms: VocabularyTerm[]
  vocabularyStats: VocabularyResponse['statistics'] | null
  totalTerms: number
  
  // État des guides
  narrativeGuides: NarrativeGuideResponse | null
  
  // État de synchronisation
  lastSyncTime: string | null
  isSyncing: boolean
  
  // Actions
  setVocabularyConfig: (config: VocabularyConfig) => void
  setLevelMode: (level: PopularityLevel, mode: VocabularyMode) => void
  toggleGuides: () => void
  loadVocabulary: () => Promise<void>
  loadNarrativeGuides: (skipLastSyncUpdate?: boolean) => Promise<void>
  syncFromNotion: () => Promise<void>
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

export const useVocabularyStore = create<VocabularyState>((set, get) => ({
  vocabularyConfig: DEFAULT_VOCABULARY_CONFIG,
  includeNarrativeGuides: true,
  vocabularyTerms: [],
  vocabularyStats: null,
  totalTerms: 0,
  narrativeGuides: null,
  lastSyncTime: null,
  isSyncing: false,
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

  toggleGuides: () => {
    set((state) => ({
      includeNarrativeGuides: !state.includeNarrativeGuides,
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

  loadNarrativeGuides: async (skipLastSyncUpdate: boolean = false) => {
    try {
      set({ error: null })
      const response = await vocabularyAPI.getNarrativeGuides()
      const updates: Partial<VocabularyState> = {
        narrativeGuides: response,
      }
      // Ne pas écraser lastSyncTime si skipLastSyncUpdate est true
      // (utilisé après une synchronisation pour éviter d'écraser la valeur mise à jour)
      if (!skipLastSyncUpdate) {
        updates.lastSyncTime = response.last_sync
      }
      set(updates)
    } catch (err) {
      const errorMessage =
        err instanceof Error
          ? err.message
          : 'Erreur lors du chargement des guides narratifs'
      set({ error: errorMessage })
      console.error('Erreur lors du chargement des guides narratifs:', err)
    }
  },

  syncFromNotion: async () => {
    try {
      set({ isSyncing: true, error: null })
      
      // Synchroniser vocabulaire et guides en parallèle
      const [vocabResult, guidesResult] = await Promise.all([
        vocabularyAPI.syncVocabulary(),
        vocabularyAPI.syncNarrativeGuides(),
      ])

      if (vocabResult.success && guidesResult.success) {
        // Recharger les données après synchronisation
        // Ne pas mettre à jour lastSyncTime dans loadNarrativeGuides pour éviter d'écraser la valeur
        await Promise.all([
          get().loadVocabulary(),
          get().loadNarrativeGuides(true), // skipLastSyncUpdate = true
        ])
        // Utiliser la valeur la plus récente entre les deux synchronisations
        const latestSync = vocabResult.last_sync && guidesResult.last_sync
          ? (vocabResult.last_sync > guidesResult.last_sync ? vocabResult.last_sync : guidesResult.last_sync)
          : (vocabResult.last_sync || guidesResult.last_sync)
        set({
          lastSyncTime: latestSync,
        })
      } else {
        const errors = [
          vocabResult.error,
          guidesResult.error,
        ]
          .filter(Boolean)
          .join('; ')
        set({ error: errors || 'Erreur lors de la synchronisation' })
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error
          ? err.message
          : 'Erreur lors de la synchronisation depuis Notion'
      set({ error: errorMessage })
      console.error('Erreur lors de la synchronisation:', err)
    } finally {
      set({ isSyncing: false })
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
}))

