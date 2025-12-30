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

export type ImportanceLevel =
  | 'Majeur'
  | 'Important'
  | 'Modéré'
  | 'Secondaire'
  | 'Mineur'
  | 'Anecdotique'

interface VocabularyState {
  // État du vocabulaire
  vocabularyMinImportance: ImportanceLevel | null
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
  setMinImportance: (level: ImportanceLevel | null) => void
  toggleGuides: () => void
  loadVocabulary: (minImportance?: ImportanceLevel) => Promise<void>
  loadNarrativeGuides: (skipLastSyncUpdate?: boolean) => Promise<void>
  syncFromNotion: () => Promise<void>
  loadStats: () => Promise<void>
  clearError: () => void
  error: string | null
}

export const useVocabularyStore = create<VocabularyState>((set, get) => ({
  vocabularyMinImportance: 'Important',
  includeNarrativeGuides: true,
  vocabularyTerms: [],
  vocabularyStats: null,
  totalTerms: 0,
  narrativeGuides: null,
  lastSyncTime: null,
  isSyncing: false,
  error: null,

  setMinImportance: (level) => {
    set({ vocabularyMinImportance: level })
    // Recharger le vocabulaire avec le nouveau niveau
    if (level) {
      get().loadVocabulary(level).catch(console.error)
    }
  },

  toggleGuides: () => {
    set((state) => ({
      includeNarrativeGuides: !state.includeNarrativeGuides,
    }))
  },

  loadVocabulary: async (minImportance) => {
    try {
      set({ error: null })
      const level = minImportance || get().vocabularyMinImportance
      if (!level) return

      const response = await vocabularyAPI.getVocabulary(level)
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
          by_importance: stats.by_importance,
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

