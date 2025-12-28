/**
 * Composant pour afficher visuellement un dialogue Unity JSON.
 * Parse le JSON Unity et affiche chaque nœud de manière claire et lisible.
 */
import { memo, useMemo, useState, useCallback } from 'react'
import { theme } from '../../theme'
import type { GenerateUnityDialogueResponse } from '../../types/api'
import * as dialoguesAPI from '../../api/dialogues'
import { getErrorMessage } from '../../types/errors'
import { useToast } from '../shared'

interface UnityNode {
  id: string
  speaker?: string
  line?: string
  choices?: Array<{
    text: string
    targetNode?: string
    test?: string
    condition?: string
    [key: string]: unknown
  }>
  nextNode?: string
  test?: string
  successNode?: string
  failureNode?: string
  [key: string]: unknown
}

interface UnityDialogueViewerProps {
  response: GenerateUnityDialogueResponse
  onExport?: (filename: string) => void
}

export const UnityDialogueViewer = memo(function UnityDialogueViewer({
  response,
  onExport,
}: UnityDialogueViewerProps) {
  const toast = useToast()
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())

  // Parser le JSON Unity
  const nodes = useMemo<UnityNode[]>(() => {
    try {
      const parsed = JSON.parse(response.json_content)
      if (!Array.isArray(parsed)) {
        throw new Error('Le JSON Unity doit être un tableau de nœuds')
      }
      return parsed as UnityNode[]
    } catch (error) {
      console.error('Erreur lors du parsing du JSON Unity:', error)
      return []
    }
  }, [response.json_content])

  const toggleNodeExpanded = useCallback((nodeId: string) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev)
      if (next.has(nodeId)) {
        next.delete(nodeId)
      } else {
        next.add(nodeId)
      }
      return next
    })
  }, [])

  const handleExport = useCallback(async () => {
    try {
      const result = await dialoguesAPI.exportUnityDialogue({
        json_content: response.json_content,
        title: response.title || 'Dialogue Unity',
      })
      toast(`Dialogue Unity exporté avec succès: ${result.filename}`, 'success', 5000)
      onExport?.(result.filename)
    } catch (err) {
      toast(`Erreur lors de l'export: ${getErrorMessage(err)}`, 'error')
    }
  }, [response, toast, onExport])

  const handleCopyJson = useCallback(() => {
    navigator.clipboard.writeText(response.json_content)
    toast('JSON copié dans le presse-papier', 'success', 2000)
  }, [response.json_content, toast])

  if (nodes.length === 0) {
    return (
      <div
        style={{
          padding: '2rem',
          textAlign: 'center',
          color: theme.text.secondary,
        }}
      >
        Aucun dialogue à afficher (JSON invalide ou vide)
      </div>
    )
  }

  return (
    <div
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: theme.background.panel,
      }}
    >
      {/* En-tête avec titre et actions */}
      <div
        style={{
          padding: '1rem',
          borderBottom: `1px solid ${theme.border.primary}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: theme.background.secondary,
        }}
      >
        <h3 style={{ margin: 0, color: theme.text.primary }}>
          {response.title || 'Dialogue Unity'}
        </h3>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            onClick={handleCopyJson}
            style={{
              padding: '0.5rem 1rem',
              border: `1px solid ${theme.border.primary}`,
              borderRadius: '4px',
              backgroundColor: theme.button.default.background,
              color: theme.button.default.color,
              cursor: 'pointer',
              fontSize: '0.9rem',
            }}
          >
            Copier JSON
          </button>
          <button
            onClick={handleExport}
            style={{
              padding: '0.5rem 1rem',
              border: `1px solid ${theme.border.primary}`,
              borderRadius: '4px',
              backgroundColor: theme.button.primary.background,
              color: theme.button.primary.color,
              cursor: 'pointer',
              fontSize: '0.9rem',
              fontWeight: 'bold',
            }}
          >
            Exporter vers Unity
          </button>
        </div>
      </div>

      {/* Liste des nœuds */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '1rem',
        }}
      >
        {nodes.map((node, index) => {
          const isExpanded = expandedNodes.has(node.id)
          const hasAdvancedOptions =
            node.test ||
            node.successNode ||
            node.failureNode ||
            node.choices?.some((c) => c.test || c.condition)

          return (
            <div
              key={node.id}
              style={{
                marginBottom: '1.5rem',
                border: `1px solid ${theme.border.primary}`,
                borderRadius: '8px',
                backgroundColor: theme.background.tertiary,
                overflow: 'hidden',
              }}
            >
              {/* En-tête du nœud */}
              <div
                style={{
                  padding: '0.75rem 1rem',
                  backgroundColor: theme.background.secondary,
                  borderBottom: `1px solid ${theme.border.primary}`,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span
                    style={{
                      fontFamily: 'monospace',
                      fontSize: '0.85rem',
                      fontWeight: 'bold',
                      color: theme.text.secondary,
                      backgroundColor: theme.background.panel,
                      padding: '0.25rem 0.5rem',
                      borderRadius: '4px',
                    }}
                  >
                    {node.id}
                  </span>
                  {node.speaker && (
                    <span
                      style={{
                        padding: '0.25rem 0.75rem',
                        backgroundColor: theme.button.primary.background,
                        color: theme.button.primary.color,
                        borderRadius: '12px',
                        fontSize: '0.85rem',
                        fontWeight: '500',
                      }}
                    >
                      {node.speaker}
                    </span>
                  )}
                </div>
                {hasAdvancedOptions && (
                  <button
                    onClick={() => toggleNodeExpanded(node.id)}
                    style={{
                      padding: '0.25rem 0.5rem',
                      border: `1px solid ${theme.border.primary}`,
                      borderRadius: '4px',
                      backgroundColor: 'transparent',
                      color: theme.text.secondary,
                      cursor: 'pointer',
                      fontSize: '0.8rem',
                    }}
                  >
                    {isExpanded ? '▼' : '▶'} Options
                  </button>
                )}
              </div>

              {/* Contenu du nœud */}
              <div style={{ padding: '1rem' }}>
                {/* Ligne de dialogue */}
                {node.line && (
                  <div
                    style={{
                      marginBottom: node.choices && node.choices.length > 0 ? '1rem' : '0',
                      padding: '1rem',
                      backgroundColor: theme.background.panel,
                      borderRadius: '4px',
                      borderLeft: `4px solid ${theme.button.primary.background}`,
                    }}
                  >
                    <div
                      style={{
                        fontSize: '1rem',
                        lineHeight: '1.6',
                        color: theme.text.primary,
                        whiteSpace: 'pre-wrap',
                        wordWrap: 'break-word',
                      }}
                    >
                      {node.line}
                    </div>
                  </div>
                )}

                {/* Choix du joueur */}
                {node.choices && node.choices.length > 0 && (
                  <div style={{ marginTop: '1rem' }}>
                    <div
                      style={{
                        fontSize: '0.85rem',
                        fontWeight: 'bold',
                        color: theme.text.secondary,
                        marginBottom: '0.5rem',
                      }}
                    >
                      Choix du joueur :
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      {node.choices.map((choice, choiceIndex) => (
                        <div
                          key={choiceIndex}
                          style={{
                            padding: '0.75rem 1rem',
                            backgroundColor: theme.background.panel,
                            border: `1px solid ${theme.border.primary}`,
                            borderRadius: '4px',
                            borderLeft: `4px solid ${theme.accent?.primary || theme.button.primary.background}`,
                          }}
                        >
                          <div
                            style={{
                              fontSize: '0.95rem',
                              color: theme.text.primary,
                              marginBottom: choice.targetNode || choice.test || choice.condition ? '0.5rem' : '0',
                            }}
                          >
                            {choice.text}
                          </div>
                          {(choice.targetNode || choice.test || choice.condition) && (
                            <div
                              style={{
                                fontSize: '0.75rem',
                                color: theme.text.secondary,
                                fontFamily: 'monospace',
                                marginTop: '0.5rem',
                                paddingTop: '0.5rem',
                                borderTop: `1px solid ${theme.border.primary}`,
                              }}
                            >
                              {choice.targetNode && (
                                <div>→ {choice.targetNode}</div>
                              )}
                              {choice.test && <div>Test: {choice.test}</div>}
                              {choice.condition && <div>Condition: {choice.condition}</div>}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Navigation linéaire (nextNode) */}
                {!node.choices && node.nextNode && (
                  <div
                    style={{
                      marginTop: '1rem',
                      padding: '0.5rem',
                      backgroundColor: theme.background.panel,
                      borderRadius: '4px',
                      fontSize: '0.85rem',
                      color: theme.text.secondary,
                      fontFamily: 'monospace',
                    }}
                  >
                    → Suivant: {node.nextNode}
                  </div>
                )}

                {/* Options avancées (collapsible) */}
                {hasAdvancedOptions && isExpanded && (
                  <div
                    style={{
                      marginTop: '1rem',
                      padding: '1rem',
                      backgroundColor: theme.background.panel,
                      borderRadius: '4px',
                      border: `1px solid ${theme.border.primary}`,
                      fontSize: '0.85rem',
                    }}
                  >
                    <div style={{ fontWeight: 'bold', color: theme.text.secondary, marginBottom: '0.5rem' }}>
                      Options avancées :
                    </div>
                    {node.test && (
                      <div style={{ marginBottom: '0.5rem' }}>
                        <strong>Test d'attribut:</strong> {node.test}
                      </div>
                    )}
                    {node.successNode && (
                      <div style={{ marginBottom: '0.5rem' }}>
                        <strong>Nœud succès:</strong>{' '}
                        <span style={{ fontFamily: 'monospace' }}>{node.successNode}</span>
                      </div>
                    )}
                    {node.failureNode && (
                      <div style={{ marginBottom: '0.5rem' }}>
                        <strong>Nœud échec:</strong>{' '}
                        <span style={{ fontFamily: 'monospace' }}>{node.failureNode}</span>
                      </div>
                    )}
                  </div>
                )}

                {/* Fin de dialogue (pas de choix ni nextNode) */}
                {!node.choices && !node.nextNode && (
                  <div
                    style={{
                      marginTop: '1rem',
                      padding: '0.5rem',
                      textAlign: 'center',
                      fontSize: '0.85rem',
                      color: theme.text.secondary,
                      fontStyle: 'italic',
                    }}
                  >
                    Fin du dialogue
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Footer avec infos */}
      {(response.prompt_used || response.estimated_tokens || response.warning) && (
        <div
          style={{
            padding: '0.75rem 1rem',
            borderTop: `1px solid ${theme.border.primary}`,
            backgroundColor: theme.background.secondary,
            fontSize: '0.85rem',
            color: theme.text.secondary,
          }}
        >
          {response.warning && (
            <div style={{ color: theme.error?.color || '#ff6b6b', marginBottom: '0.25rem' }}>
              ⚠️ {response.warning}
            </div>
          )}
          {response.estimated_tokens && (
            <div>Tokens estimés: {response.estimated_tokens.toLocaleString()}</div>
          )}
        </div>
      )}
    </div>
  )
})



