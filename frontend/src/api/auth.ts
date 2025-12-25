/**
 * API client pour l'authentification.
 */
import apiClient from './client'
import type { LoginRequest, TokenResponse, UserResponse } from '../types/api'

/**
 * Connexion utilisateur.
 */
export async function login(credentials: LoginRequest): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>('/api/v1/auth/login', credentials)
  const { access_token } = response.data
  
  // Stocker le token
  localStorage.setItem('access_token', access_token)
  
  return response.data
}

/**
 * Déconnexion utilisateur.
 */
export async function logout(): Promise<void> {
  await apiClient.post('/api/v1/auth/logout')
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

/**
 * Rafraîchir le token d'accès.
 */
export async function refreshToken(refreshToken: string): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>('/api/v1/auth/refresh', {
    refresh_token: refreshToken,
  })
  
  const { access_token } = response.data
  localStorage.setItem('access_token', access_token)
  
  return response.data
}

/**
 * Récupérer les informations de l'utilisateur courant.
 */
export async function getCurrentUser(): Promise<UserResponse> {
  const response = await apiClient.get<UserResponse>('/api/v1/auth/me')
  return response.data
}

