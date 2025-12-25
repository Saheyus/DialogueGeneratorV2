/**
 * Store Zustand pour l'authentification.
 */
import { create } from 'zustand'
import type { UserResponse } from '../types/api'
import * as authAPI from '../api/auth'

interface AuthState {
  user: UserResponse | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  fetchCurrentUser: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
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
      set({ user: null, isAuthenticated: false })
    }
  },

  fetchCurrentUser: async () => {
    set({ isLoading: true })
    try {
      const user = await authAPI.getCurrentUser()
      set({ user, isAuthenticated: true, isLoading: false })
    } catch (error) {
      set({ user: null, isAuthenticated: false, isLoading: false })
    }
  },
}))

