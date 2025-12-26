/**
 * Client HTTP pour l'API REST.
 */
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:4242'

/**
 * Instance axios configurée pour l'API.
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 secondes
  withCredentials: true, // Nécessaire pour envoyer/recevoir les cookies (refresh_token)
})

/**
 * Intercepteur pour ajouter le token d'authentification.
 */
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

/**
 * Verrou anti-tempête pour le refresh token.
 * Si plusieurs requêtes partent simultanément avec token expiré,
 * une seule Promise de refresh est créée et partagée.
 */
let refreshTokenPromise: Promise<string> | null = null

/**
 * Intercepteur pour gérer les erreurs et le rafraîchissement de token.
 */
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // Si erreur 401 et pas déjà retenté
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        // Si un refresh est déjà en cours, attendre cette Promise
        if (refreshTokenPromise) {
          const newAccessToken = await refreshTokenPromise
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
          }
          return apiClient(originalRequest)
        }

        // Sinon, créer une nouvelle Promise de refresh
        refreshTokenPromise = (async () => {
          try {
            // Le refresh token est maintenant dans un cookie httpOnly, pas besoin de le passer dans le body
            const response = await axios.post(
              `${API_BASE_URL}/api/v1/auth/refresh`,
              {}, // Body vide, le cookie est envoyé automatiquement avec withCredentials
              { withCredentials: true }
            )

            const { access_token } = response.data
            localStorage.setItem('access_token', access_token)
            return access_token
          } finally {
            // Nettoyer la Promise après utilisation (succès ou échec)
            refreshTokenPromise = null
          }
        })()

        const newAccessToken = await refreshTokenPromise

        // Réessayer la requête originale avec le nouveau token
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
        }
        return apiClient(originalRequest)
      } catch (refreshError) {
        // Échec du rafraîchissement, nettoyer et déconnexion
        refreshTokenPromise = null
        localStorage.removeItem('access_token')
        // Le refresh_token est dans un cookie, on ne peut pas le supprimer côté client
        // Le serveur le supprimera lors de la redirection vers /login
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient

