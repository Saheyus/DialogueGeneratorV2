/**
 * Hook pour vérifier le budget avant génération LLM.
 * 
 * Affiche des warnings (toast) à 90% et bloque (modal) à 100%.
 */
import { useState, useCallback } from 'react'
import { getBudget, type BudgetResponse } from '../api/costs'
import { useToast } from '../components/shared/Toast'

export interface BudgetCheckResult {
  /** True si génération autorisée, false si bloquée */
  allowed: boolean
  /** Pourcentage du budget utilisé */
  percentage: number
  /** Message d'avertissement ou de blocage */
  message?: string
}

export interface UseCostGovernanceReturn {
  /** Vérifie le budget et retourne le résultat */
  checkBudget: () => Promise<BudgetCheckResult>
  /** État du budget actuel */
  budget: BudgetResponse | null
  /** Charger le budget */
  loadBudget: () => Promise<void>
  /** Indique si le budget est en cours de chargement */
  loading: boolean
}

export function useCostGovernance(): UseCostGovernanceReturn {
  const [budget, setBudget] = useState<BudgetResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const toast = useToast()

  const loadBudget = useCallback(async () => {
    setLoading(true)
    try {
      const budgetData = await getBudget()
      setBudget(budgetData)
    } catch (error) {
      console.error('Erreur lors du chargement du budget:', error)
      // En cas d'erreur, autoriser la génération (ne pas bloquer)
    } finally {
      setLoading(false)
    }
  }, [])

  const checkBudget = useCallback(async (): Promise<BudgetCheckResult> => {
    try {
      const budgetData = await getBudget()
      setBudget(budgetData)

      const percentage = budgetData.percentage

      // Hard block à 100%
      if (percentage >= 100) {
        return {
          allowed: false,
          percentage,
          message: `Budget dépassé (${percentage.toFixed(1)}%) - Veuillez augmenter le budget ou attendre le prochain mois`
        }
      }

      // Soft warning à 90%
      if (percentage >= 90 && percentage < 100) {
        const remaining = budgetData.remaining
        const warningMessage = `Budget atteint à ${percentage.toFixed(1)}% - ${remaining.toFixed(2)}€ restants`
        toast(warningMessage, 'warning', 5000)
        return {
          allowed: true,
          percentage,
          message: warningMessage
        }
      }

      // Pas de warning
      return {
        allowed: true,
        percentage
      }
    } catch (error) {
      console.error('Erreur lors de la vérification du budget:', error)
      // En cas d'erreur, autoriser la génération (ne pas bloquer)
      return {
        allowed: true,
        percentage: 0
      }
    }
  }, [toast])

  return {
    checkBudget,
    budget,
    loadBudget,
    loading
  }
}
