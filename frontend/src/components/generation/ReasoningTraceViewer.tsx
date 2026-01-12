/**
 * Composant pour afficher la phase réflexive (reasoning trace) du modèle GPT-5.2.
 */
import { memo, useState, useCallback, useMemo } from 'react'
import { theme } from '../../theme'
import { useToast } from '../shared'
import type { ReasoningTrace } from '../../types/api'

export interface ReasoningTraceViewerProps {
  /** Le reasoning trace à afficher */
  reasoningTrace: ReasoningTrace | null | undefined
  /** Indique si la génération est en cours */
  isGenerating?: boolean
}

export const ReasoningTraceViewer = memo(function ReasoningTraceViewer({
  reasoningTrace,
  isGenerating = false,
}: ReasoningTraceViewerProps) {
  // #region agent log
  fetch('http://127.0.0.1:7244/ingest/49f0dd36-7e15-4023-914a-f038d74c10fc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'ReasoningTraceViewer.tsx:15',message:'ReasoningTraceViewer props',data:{hasTrace: !!reasoningTrace, isGenerating, traceKeys: reasoningTrace ? Object.keys(reasoningTrace) : null},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'E'})}).catch(()=>{});
  // #endregion
  const toast = useToast()
  const [expandedItems, setExpandedItems] = useState<Set<number>>(new Set())
  const [viewMode, setViewMode] = useState<'summary' | 'items'>('summary')

  const toggleItemExpanded = useCallback((index: number) => {
    setExpandedItems((prev) => {
      const next = new Set(prev)
      if (next.has(index)) {
        next.delete(index)
      } else {
        next.add(index)
      }
      return next
    })
  }, [])

  const handleCopyTrace = useCallback(() => {
    if (!reasoningTrace) return

    const traceText = JSON.stringify(reasoningTrace, null, 2)
    navigator.clipboard.writeText(traceText)
      .then(() => {
        toast('Reasoning trace copié dans le presse-papier', 'success', 2000)
      })
      .catch(() => {
        toast('Erreur lors de la copie', 'error', 2000)
      })
  }, [reasoningTrace, toast])

  const itemsToShow = useMemo(() => {
    if (!reasoningTrace?.items) return []
    // Limiter l'affichage à 50 items pour éviter les performances
    return reasoningTrace.items.slice(0, 50)
  }, [reasoningTrace])

  const hasMoreItems = useMemo(() => {
    return (reasoningTrace?.items_count || 0) > itemsToShow.length
  }, [reasoningTrace, itemsToShow])

  // Si on n'est pas en train de générer et qu'il n'y a pas de trace, ne rien afficher
  if (!reasoningTrace && !isGenerating) {
    return null
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: theme.background.secondary,
        overflow: 'hidden',
      }}
    >
      {/* En-tête compact */}
      <div
        style={{
          padding: '0.75rem 1rem',
          flexShrink: 0,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '1rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '1.1rem' }}>🧠</span>
          <div>
            <div
              style={{
                fontSize: '0.9rem',
                fontWeight: 600,
                color: theme.text.primary,
              }}
            >
              Phase Réflexive (GPT-5.2)
            </div>
            {reasoningTrace?.effort && (
              <div
                style={{
                  fontSize: '0.75rem',
                  color: theme.text.secondary,
                  marginTop: '0.1rem',
                }}
              >
                Effort: <strong>{reasoningTrace.effort}</strong>
              </div>
            )}
          </div>
        </div>
        {reasoningTrace && (
          <button
            type="button"
            onClick={handleCopyTrace}
            style={{
              padding: '0.4rem 0.8rem',
              border: `1px solid ${theme.border.primary}`,
              borderRadius: '4px',
              backgroundColor: theme.background.panel,
              color: theme.text.primary,
              cursor: 'pointer',
              fontSize: '0.8rem',
              transition: 'background-color 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = theme.background.secondary
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = theme.background.panel
            }}
          >
            📋 Copier
          </button>
        )}
      </div>

      {/* Contenu */}
      <div
        style={{
          maxHeight: '300px',
          overflowY: 'auto',
          overflowX: 'hidden',
          padding: '0 1rem 1rem 1rem',
        }}
      >
        {isGenerating && !reasoningTrace ? (
          <div
            style={{
              padding: '1rem',
              textAlign: 'center',
              color: theme.text.secondary,
              fontSize: '0.9rem',
            }}
          >
            <span style={{ display: 'inline-block', animation: 'pulse 1.5s ease-in-out infinite' }}>
              ...
            </span>
            <style>{`
              @keyframes pulse {
                0%, 100% { opacity: 0.3; }
                50% { opacity: 1; }
              }
            `}</style>
          </div>
        ) : reasoningTrace ? (
          <>
            {/* Summary */}
            {reasoningTrace.summary && (
              <div
                style={{
                  marginBottom: '1rem',
                  padding: '0.75rem',
                  backgroundColor: theme.background.panel,
                  borderRadius: '4px',
                  border: `1px solid ${theme.border.primary}`,
                }}
              >
                <h4
                  style={{
                    margin: '0 0 0.5rem 0',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    color: theme.text.primary,
                  }}
                >
                  Résumé du Raisonnement
                </h4>
                <div
                  style={{
                    fontSize: '0.85rem',
                    lineHeight: '1.5',
                    color: theme.text.secondary,
                    whiteSpace: 'pre-wrap',
                  }}
                >
                  {reasoningTrace.summary}
                </div>
              </div>
            )}

            {/* Items */}
            {reasoningTrace.items && reasoningTrace.items.length > 0 && (
              <div>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '0.75rem',
                  }}
                >
                  <h4
                    style={{
                      margin: 0,
                      fontSize: '0.85rem',
                      fontWeight: 600,
                      color: theme.text.primary,
                    }}
                  >
                    Étapes de Raisonnement ({reasoningTrace.items_count || reasoningTrace.items.length})
                  </h4>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {itemsToShow.slice(0, 5).map((item, index) => {
                    const isExpanded = expandedItems.has(index)
                    const itemStr =
                      typeof item === 'string'
                        ? item
                        : JSON.stringify(item, null, 2)

                    return (
                      <div
                        key={index}
                        style={{
                          border: `1px solid ${theme.border.primary}`,
                          borderRadius: '4px',
                          overflow: 'hidden',
                          backgroundColor: theme.background.panel,
                        }}
                      >
                        <button
                          type="button"
                          onClick={() => toggleItemExpanded(index)}
                          style={{
                            width: '100%',
                            padding: '0.5rem 0.75rem',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            backgroundColor: 'transparent',
                            border: 'none',
                            color: theme.text.primary,
                            cursor: 'pointer',
                            fontSize: '0.8rem',
                            textAlign: 'left',
                          }}
                        >
                          <span style={{ fontWeight: 500 }}>
                            Étape {index + 1}
                          </span>
                          <span
                            style={{
                              fontSize: '0.7rem',
                              color: theme.text.secondary,
                            }}
                          >
                            {isExpanded ? '▼' : '▶'}
                          </span>
                        </button>
                        {isExpanded && (
                          <div
                            style={{
                              padding: '0.5rem 0.75rem',
                              borderTop: `1px solid ${theme.border.primary}`,
                              backgroundColor: theme.background.secondary,
                            }}
                          >
                            <pre
                              style={{
                                fontFamily: 'monospace',
                                fontSize: '0.75rem',
                                lineHeight: '1.4',
                                color: theme.text.secondary,
                                margin: 0,
                                whiteSpace: 'pre-wrap',
                                wordWrap: 'break-word',
                                overflowWrap: 'break-word',
                                maxHeight: '200px',
                                overflowY: 'auto',
                              }}
                            >
                              {itemStr.length > 500
                                ? `${itemStr.slice(0, 500)}... (${itemStr.length} caractères)`
                                : itemStr}
                            </pre>
                          </div>
                        )}
                      </div>
                    )
                  })}

                  {hasMoreItems && (
                    <div
                      style={{
                        padding: '0.5rem',
                        textAlign: 'center',
                        color: theme.text.secondary,
                        fontSize: '0.75rem',
                        fontStyle: 'italic',
                      }}
                    >
                      ... et {reasoningTrace.items_count! - Math.min(5, itemsToShow.length)} autres étapes
                    </div>
                  )}
                </div>
              </div>
            )}

            {!reasoningTrace.summary && (!reasoningTrace.items || reasoningTrace.items.length === 0) && (
              <div
                style={{
                  padding: '1rem',
                  textAlign: 'center',
                  color: theme.text.secondary,
                  fontSize: '0.85rem',
                }}
              >
                Aucun détail de reasoning trace disponible.
              </div>
            )}
          </>
        ) : null}
      </div>
    </div>
  )
})
