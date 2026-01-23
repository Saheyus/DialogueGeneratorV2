/**
 * Client API pour les endpoints de cost governance.
 */
import apiClient from './client'

export interface BudgetResponse {
  quota: number
  amount: number
  percentage: number
  remaining: number
}

export interface UpdateBudgetRequest {
  quota: number
}

export interface DailyCost {
  date: string
  cost: number
}

export interface UsageResponse {
  daily_costs: DailyCost[]
  total: number
  percentage: number
}

/**
 * Récupère le budget actuel.
 */
export async function getBudget(): Promise<BudgetResponse> {
  const response = await apiClient.get('/api/v1/costs/budget')
  return response.data
}

/**
 * Met à jour le quota budget.
 */
export async function updateBudget(quota: number): Promise<BudgetResponse> {
  const response = await apiClient.put('/api/v1/costs/budget', { quota })
  return response.data
}

/**
 * Récupère l'usage avec graphique (coûts quotidiens).
 */
export async function getUsage(): Promise<UsageResponse> {
  const response = await apiClient.get('/api/v1/costs/usage')
  return response.data
}
