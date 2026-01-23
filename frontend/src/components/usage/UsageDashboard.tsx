/**
 * Dashboard de suivi d'utilisation LLM.
 */
import { useState, useEffect, useCallback, useMemo } from 'react'
import { getUsageStatistics, type LLMUsageStatistics } from '../../api/llmUsage'
import { getBudget, getUsage, type BudgetResponse, type UsageResponse } from '../../api/costs'
import { UsageStatsCard } from './UsageStatsCard'
import { UsageHistoryTable } from './UsageHistoryTable'
import { getErrorMessage } from '../../types/errors'
import './UsageDashboard.css'

export function UsageDashboard() {
  const defaultDates = useMemo(() => {
    const today = new Date()
    const thirtyDaysAgo = new Date(today)
    thirtyDaysAgo.setDate(today.getDate() - 30)
    return {
      start: thirtyDaysAgo.toISOString().split('T')[0],
      end: today.toISOString().split('T')[0],
    }
  }, [])

  const [statistics, setStatistics] = useState<LLMUsageStatistics | null>(null)
  const [budget, setBudget] = useState<BudgetResponse | null>(null)
  const [usage, setUsage] = useState<UsageResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [startDate, setStartDate] = useState<string | null>(() => defaultDates.start)
  const [endDate, setEndDate] = useState<string | null>(() => defaultDates.end)
  const [model, setModel] = useState<string | null>(null)

  const loadStatistics = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [stats, budgetData, usageData] = await Promise.all([
        getUsageStatistics(startDate, endDate, model),
        getBudget(),
        getUsage(),
      ])
      setStatistics(stats)
      setBudget(budgetData)
      setUsage(usageData)
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [startDate, endDate, model])

  useEffect(() => {
    void loadStatistics()
  }, [loadStatistics])

  const formatCost = (cost: number) => {
    if (cost < 0.01) return `$${cost.toFixed(6)}`
    return `$${cost.toFixed(2)}`
  }

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${Math.round(ms)}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }

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
          {/* Section Budget LLM */}
          {budget && (
            <div className="usage-dashboard__budget-section">
              <h2 style={{ marginTop: 0, marginBottom: '1.5rem', color: 'rgba(255, 255, 255, 0.95)' }}>
                Budget LLM
              </h2>
              <div className="usage-dashboard__stats-grid">
                <UsageStatsCard
                  title="Quota mensuel"
                  value={formatCost(budget.quota)}
                  subtitle="Budget total"
                />
                <UsageStatsCard
                  title="Montant dépensé"
                  value={formatCost(budget.amount)}
                  subtitle={`${budget.percentage.toFixed(1)}% utilisé`}
                />
                <UsageStatsCard
                  title="Montant restant"
                  value={formatCost(budget.remaining)}
                  subtitle="Disponible ce mois"
                />
                <UsageStatsCard
                  title="Pourcentage utilisé"
                  value={budget.percentage.toFixed(1)}
                  unit="%"
                  subtitle={budget.percentage >= 90 ? '⚠️ Approche de la limite' : budget.percentage >= 100 ? '🚫 Budget dépassé' : '✅ Dans les limites'}
                />
              </div>
            </div>
          )}

          {/* Graphique d'évolution des coûts */}
          {usage && usage.daily_costs.length > 0 && (
            <div className="usage-dashboard__chart-section">
              <h2 style={{ marginTop: '2rem', marginBottom: '1.5rem', color: 'rgba(255, 255, 255, 0.95)' }}>
                Évolution des coûts (mois actuel)
              </h2>
              <div className="usage-dashboard__chart">
                <div className="usage-dashboard__chart-bars">
                  {usage.daily_costs.map((daily) => {
                    const maxCost = Math.max(...usage.daily_costs.map(d => d.cost), 1)
                    const heightPercent = (daily.cost / maxCost) * 100
                    return (
                      <div key={daily.date} className="usage-dashboard__chart-bar-container">
                        <div
                          className="usage-dashboard__chart-bar"
                          style={{ height: `${heightPercent}%` }}
                          title={`${daily.date}: ${formatCost(daily.cost)}`}
                        />
                        <div className="usage-dashboard__chart-label">
                          {new Date(daily.date).getDate()}
                        </div>
                      </div>
                    )
                  })}
                </div>
                <div className="usage-dashboard__chart-summary">
                  <div>Total du mois: {formatCost(usage.total)}</div>
                  <div>Pourcentage du budget: {usage.percentage.toFixed(1)}%</div>
                </div>
              </div>
            </div>
          )}

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




