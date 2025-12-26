/**
 * Store Zustand pour l'authentification avec persistance de session.
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { UserResponse } from '../types/api'
import * as authAPI from '../api/auth'

export interface AuthState {
  user: UserResponse | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  fetchCurrentUser: () => Promise<void>
  initialize: () => Promise<void>
}

export type UseAuthStoreReturn = ReturnType<typeof useAuthStore>

const STORAGE_KEY = 'auth-storage'

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (username: string, password: string) => {
        set({ isLoading: true })
        try {
          await authAPI.login({ username, password })
          const user = await authAPI.getCurrentUser()
          set({ user, isAuthenticated: true, isLoading: false })
        } catch (error) {
          set({ isLoading: false })
          throw error
        }
      },

      logout: async () => {
        try {
          await authAPI.logout()
        } catch (error) {
          // Ignorer les erreurs de déconnexion
        } finally {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          set({ user: null, isAuthenticated: false })
        }
      },

      fetchCurrentUser: async () => {
        set({ isLoading: true })
        try {
          const user = await authAPI.getCurrentUser()
          set({ user, isAuthenticated: true, isLoading: false })
        } catch (error: any) {
          // Si le token est invalide ou utilisateur non connecté, nettoyer la session
          // Ne pas logger les erreurs 401 normales (utilisateur non connecté)
          if (error?.response?.status !== 401) {
            // Logger seulement les erreurs non-401
            console.error('Erreur lors de la récupération de l\'utilisateur:', error)
          }
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          set({ user: null, isAuthenticated: false, isLoading: false })
        }
      },

      // Initialise la session depuis le localStorage
      initialize: async () => {
        const token = localStorage.getItem('access_token')
        if (token) {
          // Vérifier que le token est encore valide
          await useAuthStore.getState().fetchCurrentUser()
        }
      },
    }),
    {
      name: STORAGE_KEY,
      partialize: (state) => ({
        // Ne persister que l'user et l'état d'authentification
        // Les tokens restent dans localStorage via le client API
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)

