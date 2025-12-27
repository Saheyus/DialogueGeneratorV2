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
  }
}

/**
 * Type d'erreur API avec réponse.
 */
export type APIError = AxiosError<APIErrorResponse>

/**
 * Extrait le message d'erreur d'une erreur API.
 */
export function getErrorMessage(error: unknown): string {
  if (error && typeof error === 'object' && 'response' in error) {
    const axiosError = error as APIError
    return (
      axiosError.response?.data?.error?.message ||
      axiosError.message ||
      'Une erreur est survenue'
    )
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'Une erreur est survenue'
}



