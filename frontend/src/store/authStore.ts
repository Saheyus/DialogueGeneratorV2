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

// Flag pour éviter les appels multiples simultanés à initialize()
let isInitializing = false

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
          // Rejeter l'erreur pour que l'appelant puisse la gérer
          throw error
        }
      },

      // Initialise la session depuis le localStorage
      initialize: async () => {
        // Éviter les appels multiples simultanés
        if (isInitializing) {
          // #region agent log
          fetch('http://127.0.0.1:7244/ingest/49f0dd36-7e15-4023-914a-f038d74c10fc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'authStore.ts:77',message:'initialize() already in progress, skipping',data:{timestamp:Date.now()},timestamp:Date.now(),sessionId:'debug-session',runId:'post-fix',hypothesisId:'D'})}).catch(()=>{});
          // #endregion
          return
        }
        
        isInitializing = true
        // #region agent log
        fetch('http://127.0.0.1:7244/ingest/49f0dd36-7e15-4023-914a-f038d74c10fc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'authStore.ts:82',message:'initialize() entry',data:{timestamp:Date.now()},timestamp:Date.now(),sessionId:'debug-session',runId:'post-fix',hypothesisId:'A,D'})}).catch(()=>{});
        // #endregion
        const stateBefore = useAuthStore.getState()
        // #region agent log
        fetch('http://127.0.0.1:7244/ingest/49f0dd36-7e15-4023-914a-f038d74c10fc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'authStore.ts:78',message:'State before set isLoading=true',data:{isLoading:stateBefore.isLoading,isAuthenticated:stateBefore.isAuthenticated},timestamp:Date.now(),sessionId:'debug-session',runId:'run2',hypothesisId:'C'})}).catch(()=>{});
        // #endregion
        set({ isLoading: true })
        // #region agent log
        fetch('http://127.0.0.1:7244/ingest/49f0dd36-7e15-4023-914a-f038d74c10fc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'authStore.ts:81',message:'set isLoading=true called',data:{timestamp:Date.now()},timestamp:Date.now(),sessionId:'debug-session',runId:'run2',hypothesisId:'C'})}).catch(()=>{});
        // #endregion
        
        try {
          const token = localStorage.getItem('access_token')
          // #region agent log
          fetch('http://127.0.0.1:7244/ingest/49f0dd36-7e15-4023-914a-f038d74c10fc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'authStore.ts:85',message:'Token check',data:{hasToken:!!token},timestamp:Date.now(),sessionId:'debug-session',runId:'run2',hypothesisId:'B'})}).catch(()=>{});
          // #endregion
          if (token) {
            // Vérifier que le token est encore valide
            try {
              // #region agent log
              fetch('http://127.0.0.1:7244/ingest/49f0dd36-7e15-4023-914a-f038d74c10fc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'authStore.ts:89',message:'Calling getCurrentUser',data:{timestamp:Date.now()},timestamp:Date.now(),sessionId:'debug-session',runId:'run2',hypothesisId:'A'})}).catch(()=>{});
              // #endregion
              const user = await authAPI.getCurrentUser()
              // #region agent log
              fetch('http://127.0.0.1:7244/ingest/49f0dd36-7e15-4023-914a-f038d74c10fc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'authStore.ts:92',message:'getCurrentUser success, setting isLoading=false',data:{hasUser:!!user,timestamp:Date.now()},timestamp:Date.now(),sessionId:'debug-session',runId:'run2',hypothesisId:'A'})}).catch(()=>{});
              // #endregion
              set({ user, isAuthenticated: true, isLoading: false })
              // #region agent log
              const stateAfter = useAuthStore.getState()
              fetch('http://127.0.0.1:7244/ingest/49f0dd36-7e15-4023-914a-f038d74c10fc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'authStore.ts:95',message:'State after set isLoading=false (success path)',data:{isLoading:stateAfter.isLoading,isAuthenticated:stateAfter.isAuthenticated},timestamp:Date.now(),sessionId:'debug-session',runId:'run2',hypothesisId:'A,C'})}).catch(()=>{});
              // #endregion
              return // Sortir immédiatement, isLoading déjà à false
            } catch (error: any) {
              // Erreur 401 attendue si token invalide, nettoyer et continuer
              // Ne pas logger les erreurs 401 normales (utilisateur non connecté)
              // #region agent log
              fetch('http://127.0.0.1:7244/ingest/49f0dd36-7e15-4023-914a-f038d74c10fc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'authStore.ts:100',message:'getCurrentUser error caught',data:{status:error?.response?.status,errorType:error?.constructor?.name,timestamp:Date.now()},timestamp:Date.now(),sessionId:'debug-session',runId:'run2',hypothesisId:'A'})}).catch(()=>{});
              // #endregion
              if (error?.response?.status !== 401) {
                console.error('Erreur lors de la récupération de l\'utilisateur:', error)
              }
              localStorage.removeItem('access_token')
              localStorage.removeItem('refresh_token')
              // #region agent log
              fetch('http://127.0.0.1:7244/ingest/49f0dd36-7e15-4023-914a-f038d74c10fc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'authStore.ts:108',message:'About to set isLoading=false in catch',data:{timestamp:Date.now()},timestamp:Date.now(),sessionId:'debug-session',runId:'run2',hypothesisId:'A'})}).catch(()=>{});
              // #endregion
              set({ user: null, isAuthenticated: false, isLoading: false })
              // #region agent log
              const stateAfter = useAuthStore.getState()
              fetch('http://127.0.0.1:7244/ingest/49f0dd36-7e15-4023-914a-f038d74c10fc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'authStore.ts:108',message:'State after set isLoading=false (error path)',data:{isLoading:stateAfter.isLoading,isAuthenticated:stateAfter.isAuthenticated},timestamp:Date.now(),sessionId:'debug-session',runId:'run2',hypothesisId:'A,C'})}).catch(()=>{});
              // #endregion
              return // Sortir immédiatement, isLoading déjà à false
            }
          } else {
            // Pas de token, utilisateur non connecté
            // #region agent log
            fetch('http://127.0.0.1:7244/ingest/49f0dd36-7e15-4023-914a-f038d74c10fc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'authStore.ts:115',message:'No token, setting isLoading=false',data:{timestamp:Date.now()},timestamp:Date.now(),sessionId:'debug-session',runId:'run2',hypothesisId:'B'})}).catch(()=>{});
            // #endregion
            set({ isLoading: false, isAuthenticated: false, user: null })
            // #region agent log
            const stateAfter = useAuthStore.getState()
            fetch('http://127.0.0.1:7244/ingest/49f0dd36-7e15-4023-914a-f038d74c10fc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'authStore.ts:118',message:'State after set isLoading=false (no token path)',data:{isLoading:stateAfter.isLoading,isAuthenticated:stateAfter.isAuthenticated},timestamp:Date.now(),sessionId:'debug-session',runId:'run2',hypothesisId:'B,C'})}).catch(()=>{});
            // #endregion
            return // Sortir immédiatement, isLoading déjà à false
          }
        } catch (error) {
          // En cas d'erreur inattendue, s'assurer que isLoading est false
          // #region agent log
          fetch('http://127.0.0.1:7244/ingest/49f0dd36-7e15-4023-914a-f038d74c10fc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'authStore.ts:124',message:'Unexpected error in initialize',data:{error:error?.toString(),timestamp:Date.now()},timestamp:Date.now(),sessionId:'debug-session',runId:'run2',hypothesisId:'E'})}).catch(()=>{});
          // #endregion
          console.error('Erreur lors de l\'initialisation:', error)
          set({ isLoading: false, isAuthenticated: false, user: null })
        } finally {
          // Double sécurité : s'assurer que isLoading est toujours false à la fin
          // #region agent log
          fetch('http://127.0.0.1:7244/ingest/49f0dd36-7e15-4023-914a-f038d74c10fc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'authStore.ts:131',message:'finally block entered',data:{timestamp:Date.now()},timestamp:Date.now(),sessionId:'debug-session',runId:'post-fix',hypothesisId:'A,B,E'})}).catch(()=>{});
          // #endregion
          const stateInFinally = useAuthStore.getState()
          // #region agent log
          fetch('http://127.0.0.1:7244/ingest/49f0dd36-7e15-4023-914a-f038d74c10fc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'authStore.ts:134',message:'State in finally before setting isLoading=false',data:{isLoading:stateInFinally.isLoading,isAuthenticated:stateInFinally.isAuthenticated},timestamp:Date.now(),sessionId:'debug-session',runId:'post-fix',hypothesisId:'A,E'})}).catch(()=>{});
          // #endregion
          // S'assurer que isLoading est toujours false, mais seulement si ce n'est pas déjà le cas
          // (pour éviter d'écraser un state déjà correct)
          if (stateInFinally.isLoading) {
            // #region agent log
            fetch('http://127.0.0.1:7244/ingest/49f0dd36-7e15-4023-914a-f038d74c10fc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'authStore.ts:137',message:'Setting isLoading=false in finally (was true)',data:{timestamp:Date.now()},timestamp:Date.now(),sessionId:'debug-session',runId:'post-fix',hypothesisId:'A,E'})}).catch(()=>{});
            // #endregion
            set({ isLoading: false })
            // #region agent log
            const stateAfterFinally = useAuthStore.getState()
            fetch('http://127.0.0.1:7244/ingest/49f0dd36-7e15-4023-914a-f038d74c10fc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'authStore.ts:140',message:'State after finally set isLoading=false',data:{isLoading:stateAfterFinally.isLoading,isAuthenticated:stateAfterFinally.isAuthenticated},timestamp:Date.now(),sessionId:'debug-session',runId:'post-fix',hypothesisId:'A,E'})}).catch(()=>{});
            // #endregion
          }
          // Libérer le flag d'initialisation
          isInitializing = false
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

