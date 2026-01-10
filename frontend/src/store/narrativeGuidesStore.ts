/**
 * Store Zustand pour gérer les guides narratifs Alteir.
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import * as vocabularyAPI from '../api/vocabulary'
import type { NarrativeGuideResponse } from '../api/vocabulary'

interface NarrativeGuidesState {
  // État des guides
  narrativeGuides: NarrativeGuideResponse | null
  includeNarrativeGuides: boolean
  
  // Actions
  toggleGuides: () => void
  loadNarrativeGuides: () => Promise<void>
  clearError: () => void
  error: string | null
}

const STORAGE_KEY = 'narrative_guides_store'

export const useNarrativeGuidesStore = create<NarrativeGuidesState>()(
  persist(
    (set) => ({
      narrativeGuides: null,
      includeNarrativeGuides: true,
      error: null,

      toggleGuides: () => {
        set((state) => ({
          includeNarrativeGuides: !state.includeNarrativeGuides,
        }))
      },

      loadNarrativeGuides: async () => {
        try {
          set({ error: null })
          const response = await vocabularyAPI.getNarrativeGuides()
          set({
            narrativeGuides: response,
          })
        } catch (err) {
          const errorMessage =
            err instanceof Error
              ? err.message
              : 'Erreur lors du chargement des guides narratifs'
          set({ error: errorMessage })
          console.error('Erreur lors du chargement des guides narratifs:', err)
        }
      },

      clearError: () => {
        set({ error: null })
      },
    }),
    {
      name: STORAGE_KEY,
      // Ne persister que includeNarrativeGuides, pas les autres états temporaires
      partialize: (state) => ({
        includeNarrativeGuides: state.includeNarrativeGuides,
      }),
    }
  )
)
