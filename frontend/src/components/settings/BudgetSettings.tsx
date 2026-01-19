/**
 * Composant pour configurer le budget LLM.
 */
import { useState, useEffect } from 'react'
import { getBudget, updateBudget, type BudgetResponse } from '../../api/costs'
import { getErrorMessage } from '../../types/errors'

interface BudgetSettingsProps {
  onBudgetUpdated?: (budget: BudgetResponse) => void
}

export function BudgetSettings({ onBudgetUpdated }: BudgetSettingsProps) {
  const [budget, setBudget] = useState<BudgetResponse | null>(null)
  const [quota, setQuota] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  useEffect(() => {
    void loadBudget()
  }, [])

  const loadBudget = async () => {
    setLoading(true)
    setError(null)
    try {
      const budgetData = await getBudget()
      setBudget(budgetData)
      setQuota(budgetData.quota.toString())
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    const quotaValue = parseFloat(quota)
    if (isNaN(quotaValue) || quotaValue < 0) {
      setError('Le quota doit être un nombre positif')
      return
    }

    setSaving(true)
    setError(null)
    setSuccess(null)
    try {
      const updatedBudget = await updateBudget(quotaValue)
      setBudget(updatedBudget)
      setSuccess('Budget mis à jour avec succès')
      onBudgetUpdated?.(updatedBudget)
      
      // Effacer le message de succès après 3 secondes
      setTimeout(() => setSuccess(null), 3000)
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const formatCost = (cost: number) => {
    if (cost < 0.01) return `$${cost.toFixed(6)}`
    return `$${cost.toFixed(2)}`
  }

  if (loading) {
    return <div style={{ padding: '1rem', color: 'rgba(255, 255, 255, 0.75)' }}>Chargement du budget...</div>
  }

  return (
    <div style={{ padding: '1.5rem' }}>
      <h2 style={{ marginTop: 0, marginBottom: '1.5rem', color: 'rgba(255, 255, 255, 0.95)' }}>
        Configuration du Budget LLM
      </h2>

      {error && (
        <div style={{
          padding: '0.75rem',
          marginBottom: '1rem',
          backgroundColor: '#3a1a1a',
          border: '1px solid #ff4444',
          borderRadius: '4px',
          color: '#ff6b6b'
        }}>
          Erreur: {error}
        </div>
      )}

      {success && (
        <div style={{
          padding: '0.75rem',
          marginBottom: '1rem',
          backgroundColor: '#1a3a1a',
          border: '1px solid #44ff44',
          borderRadius: '4px',
          color: '#6bff6b'
        }}>
          {success}
        </div>
      )}

      {budget && (
        <>
          <div style={{ marginBottom: '1.5rem' }}>
            <div style={{
              padding: '1rem',
              backgroundColor: 'rgba(255, 255, 255, 0.03)',
              borderRadius: '4px',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}>
              <div style={{ marginBottom: '0.5rem' }}>
                <strong>Budget actuel:</strong> {formatCost(budget.quota)}
              </div>
              <div style={{ marginBottom: '0.5rem' }}>
                <strong>Montant dépensé:</strong> {formatCost(budget.amount)} ({budget.percentage.toFixed(1)}%)
              </div>
              <div>
                <strong>Montant restant:</strong> {formatCost(budget.remaining)}
              </div>
            </div>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label htmlFor="quota" style={{
              display: 'block',
              marginBottom: '0.5rem',
              color: 'rgba(255, 255, 255, 0.87)',
              fontWeight: 500
            }}>
              Quota mensuel (USD):
            </label>
            <input
              id="quota"
              type="number"
              min="0"
              step="0.01"
              value={quota}
              onChange={(e) => setQuota(e.target.value)}
              placeholder="100.00"
              style={{
                width: '100%',
                padding: '0.75rem',
                fontSize: '1rem',
                border: '1px solid #404040',
                borderRadius: '4px',
                backgroundColor: '#2a2a2a',
                color: 'rgba(255, 255, 255, 0.87)',
                boxSizing: 'border-box'
              }}
            />
            <div style={{
              marginTop: '0.25rem',
              fontSize: '0.875rem',
              color: 'rgba(255, 255, 255, 0.6)'
            }}>
              Définissez votre budget mensuel maximum pour les appels LLM.
            </div>
          </div>

          <button
            onClick={handleSave}
            disabled={saving}
            style={{
              padding: '0.75rem 1.5rem',
              fontSize: '1rem',
              fontWeight: 'bold',
              backgroundColor: saving ? '#404040' : '#646cff',
              color: '#ffffff',
              border: 'none',
              borderRadius: '4px',
              cursor: saving ? 'not-allowed' : 'pointer',
              opacity: saving ? 0.6 : 1,
              transition: 'all 0.2s'
            }}
          >
            {saving ? 'Sauvegarde...' : 'Sauvegarder'}
          </button>
        </>
      )}
    </div>
  )
}
