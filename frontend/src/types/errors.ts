/**
 * Types pour la gestion des erreurs API.
 */
import type { AxiosError } from 'axios'

/**
 * Structure d'erreur API standard.
 */
export interface APIErrorResponse {
  error?: {
    message?: string
    details?: unknown
    code?: string
    request_id?: string
  }
}

/**
 * Type d'erreur API avec réponse.
 */
export type APIError = AxiosError<APIErrorResponse>

/**
 * Extrait le message d'erreur d'une erreur API avec détails si disponibles.
 * 
 * Améliore l'affichage des erreurs de validation backend (ValidationException).
 */
export function getErrorMessage(error: unknown): string {
  if (error && typeof error === 'object' && 'response' in error) {
    const axiosError = error as APIError
    const errorData = axiosError.response?.data?.error
    
    if (errorData) {
      let message = errorData.message || axiosError.message || 'Une erreur est survenue'
      
      // Parser les erreurs de validation (ValidationException)
      if (errorData.details) {
        const details = errorData.details as Record<string, unknown>
        
        // Si c'est une erreur de validation Unity, afficher les erreurs de validation
        if (details.validation_errors && Array.isArray(details.validation_errors)) {
          const validationErrors = details.validation_errors as string[]
          if (validationErrors.length > 0) {
            // Prendre les 3 premières erreurs pour éviter un message trop long
            const errorsToShow = validationErrors.slice(0, 3)
            message += '\n\nErreurs de validation:'
            errorsToShow.forEach((err, i) => {
              message += `\n${i + 1}. ${err}`
            })
            if (validationErrors.length > 3) {
              message += `\n... et ${validationErrors.length - 3} autre(s) erreur(s)`
            }
          }
        }
        
        // En développement, ajouter des détails supplémentaires
        const isDevelopment = import.meta.env.DEV || import.meta.env.MODE === 'development'
        if (isDevelopment) {
          // Ajouter le type d'erreur si disponible
          if (details.error_type) {
            message += ` [Type: ${details.error_type}]`
          }
          
          // Ajouter le message d'erreur détaillé si disponible et différent
          if (details.error && typeof details.error === 'string' && details.error !== message) {
            const errorDetail = details.error
            // Limiter la longueur pour éviter des messages trop longs
            if (errorDetail.length < 300) {
              message += ` - ${errorDetail}`
            } else {
              message += ` - ${errorDetail.substring(0, 300)}...`
            }
          }
          
          // Ajouter le code d'erreur si disponible
          if (errorData.code) {
            message += ` [Code: ${errorData.code}]`
          }
        }
      }
      
      return message
    }
    return axiosError.message || 'Une erreur est survenue'
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'Une erreur est survenue'
}



