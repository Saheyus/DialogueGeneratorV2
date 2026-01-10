/**
 * Tableau d'historique d'utilisation LLM.
 */
import { useState, useEffect, useCallback } from 'react'
import { getUsageHistory, type LLMUsageRecord } from '../../api/llmUsage'
import { getErrorMessage } from '../../types/errors'
import './UsageHistoryTable.css'

interface UsageHistoryTableProps {
  startDate?: string | null
  endDate?: string | null
  model?: string | null
}

export function UsageHistoryTable({
  startDate,
  endDate,
  model,
}: UsageHistoryTableProps) {
  const [records, setRecords] = useState<LLMUsageRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(0)
  const pageSize = 50

  const loadHistory = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await getUsageHistory(startDate, endDate, model, page, pageSize)
      setRecords(response.records)
      setTotal(response.total)
      setTotalPages(response.total_pages)
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [startDate, endDate, model, page])

  useEffect(() => {
    void loadHistory()
  }, [loadHistory])

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('fr-FR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const formatCost = (cost: number) => {
    return `$${cost.toFixed(6)}`
  }

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(2)}s`
  }

  if (loading) {
    return <div className="usage-history-loading">Chargement...</div>
  }

  if (error) {
    return <div className="usage-history-error">Erreur: {error}</div>
  }

  return (
    <div className="usage-history-table">
      <div className="usage-history-table__header">
        <h3>Historique des appels LLM</h3>
        <div className="usage-history-table__pagination-info">
          Page {page} sur {totalPages} ({total} enregistrements)
        </div>
      </div>

      {records.length === 0 ? (
        <div className="usage-history-empty">Aucun enregistrement trouvé</div>
      ) : (
        <>
          <table className="usage-history-table__table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Modèle</th>
                <th>Endpoint</th>
                <th>Tokens</th>
                <th>Coût</th>
                <th>Durée</th>
                <th>Variantes</th>
                <th>Statut</th>
              </tr>
            </thead>
            <tbody>
              {records.map((record) => (
                <tr key={record.request_id} className={record.success ? '' : 'error-row'}>
                  <td>{formatDate(record.timestamp)}</td>
                  <td>{record.model_name}</td>
                  <td className="endpoint-cell">{record.endpoint}</td>
                  <td>{record.total_tokens.toLocaleString()}</td>
                  <td>{formatCost(record.estimated_cost)}</td>
                  <td>{formatDuration(record.duration_ms)}</td>
                  <td>{record.k_variants}</td>
                  <td>
                    <span className={`status-badge ${record.success ? 'success' : 'error'}`}>
                      {record.success ? '✓' : '✗'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="usage-history-table__pagination">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="pagination-button"
            >
              Précédent
            </button>
            <span className="pagination-page">
              Page {page} / {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="pagination-button"
            >
              Suivant
            </button>
          </div>
        </>
      )}
    </div>
  )
}




