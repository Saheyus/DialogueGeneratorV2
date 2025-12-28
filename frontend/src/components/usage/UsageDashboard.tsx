/**
 * Dashboard de suivi d'utilisation LLM.
 */
import { useState, useEffect } from 'react'
import { getUsageStatistics, type LLMUsageStatistics } from '../../api/llmUsage'
import { UsageStatsCard } from './UsageStatsCard'
import { UsageHistoryTable } from './UsageHistoryTable'
import './UsageDashboard.css'

export function UsageDashboard() {
  const [statistics, setStatistics] = useState<LLMUsageStatistics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [startDate, setStartDate] = useState<string | null>(null)
  const [endDate, setEndDate] = useState<string | null>(null)
  const [model, setModel] = useState<string | null>(null)

  useEffect(() => {
    loadStatistics()
  }, [startDate, endDate, model])

  const loadStatistics = async () => {
    setLoading(true)
    setError(null)
    try {
      const stats = await getUsageStatistics(startDate, endDate, model)
      setStatistics(stats)
    } catch (err: any) {
      setError(err.message || 'Erreur lors du chargement des statistiques')
    } finally {
      setLoading(false)
    }
  }

  const formatCost = (cost: number) => {
    if (cost < 0.01) return `$${cost.toFixed(6)}`
    return `$${cost.toFixed(2)}`
  }

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${Math.round(ms)}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }

  // Définir les dates par défaut (30 derniers jours)
  useEffect(() => {
    const today = new Date()
    const thirtyDaysAgo = new Date(today)
    thirtyDaysAgo.setDate(today.getDate() - 30)
    
    if (!endDate) {
      setEndDate(today.toISOString().split('T')[0])
    }
    if (!startDate) {
      setStartDate(thirtyDaysAgo.toISOString().split('T')[0])
    }
  }, [])

  return (
    <div className="usage-dashboard">
      <div className="usage-dashboard__header">
        <h1>Suivi d'utilisation LLM</h1>
        <div className="usage-dashboard__filters">
          <div className="filter-group">
            <label htmlFor="start-date">Date de début:</label>
            <input
              id="start-date"
              type="date"
              value={startDate || ''}
              onChange={(e) => setStartDate(e.target.value || null)}
              className="filter-input"
            />
          </div>
          <div className="filter-group">
            <label htmlFor="end-date">Date de fin:</label>
            <input
              id="end-date"
              type="date"
              value={endDate || ''}
              onChange={(e) => setEndDate(e.target.value || null)}
              className="filter-input"
            />
          </div>
          <div className="filter-group">
            <label htmlFor="model">Modèle:</label>
            <input
              id="model"
              type="text"
              value={model || ''}
              onChange={(e) => setModel(e.target.value || null)}
              placeholder="Tous les modèles"
              className="filter-input"
            />
          </div>
        </div>
      </div>

      {error && (
        <div className="usage-dashboard__error">
          Erreur: {error}
        </div>
      )}

      {loading ? (
        <div className="usage-dashboard__loading">Chargement des statistiques...</div>
      ) : statistics ? (
        <>
          <div className="usage-dashboard__stats-grid">
            <UsageStatsCard
              title="Coût total"
              value={formatCost(statistics.total_cost)}
              subtitle={`${statistics.calls_count} appels`}
            />
            <UsageStatsCard
              title="Tokens totaux"
              value={statistics.total_tokens.toLocaleString()}
              unit="tokens"
              subtitle={`${statistics.total_prompt_tokens.toLocaleString()} prompt + ${statistics.total_completion_tokens.toLocaleString()} completion`}
            />
            <UsageStatsCard
              title="Taux de succès"
              value={statistics.success_rate.toFixed(1)}
              unit="%"
              subtitle={`${statistics.success_count} réussis / ${statistics.error_count} erreurs`}
            />
            <UsageStatsCard
              title="Durée moyenne"
              value={formatDuration(statistics.avg_duration_ms)}
              subtitle="Par appel"
            />
          </div>

          <div className="usage-dashboard__history">
            <UsageHistoryTable
              startDate={startDate}
              endDate={endDate}
              model={model}
            />
          </div>
        </>
      ) : null}
    </div>
  )
}



