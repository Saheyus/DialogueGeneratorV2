/**
 * Éditeur Unity JSON pour dialogues (édition partielle + round-trip).
 * Permet d'éditer speaker, line, choices[].text, choices[].targetNode.
 * Préserve tous les autres champs en lecture seule.
 */
import { memo, useState, useCallback, useMemo } from 'react'
import * as dialoguesAPI from '../../api/dialogues'
import { getErrorMessage } from '../../types/errors'
import { theme } from '../../theme'
import { useToast } from '../shared'
import type {
  UnityDialogueNode,
  UnityDialogueChoice,
  ExportUnityDialogueRequest,
} from '../../types/api'

export interface UnityDialogueEditorProps {
  json_content: string
  title?: string
  filename?: string
  onSave?: (filename: string) => void
  onCancel?: () => void
}

interface ValidationError {
  nodeId?: string
  choiceIndex?: number
  message: string
}

export const UnityDialogueEditor = memo(function UnityDialogueEditor({
  json_content,
  title,
  filename,
  onSave,
  onCancel,
}: UnityDialogueEditorProps) {
  const toast = useToast()
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expandedAdvanced, setExpandedAdvanced] = useState<Set<string>>(new Set())

  // Parser et état local des nœuds
  const [nodes, setNodes] = useState<UnityDialogueNode[]>(() => {
    try {
      const parsed = JSON.parse(json_content)
      if (!Array.isArray(parsed)) {
        throw new Error('Le JSON Unity doit être un tableau de nœuds')
      }
      return parsed as UnityDialogueNode[]
    } catch (error) {
      console.error('Erreur lors du parsing du JSON Unity:', error)
      return []
    }
  })

  // Validation: IDs uniques et références valides
  const validationErrors = useMemo<ValidationError[]>(() => {
    const errors: ValidationError[] = []
    const nodeIds = new Set<string>()

    // Vérifier IDs uniques
    for (const node of nodes) {
      if (!node.id) {
        errors.push({ nodeId: node.id, message: 'ID manquant' })
        continue
      }
      if (!/^[A-Z][A-Z0-9_]*$/.test(node.id)) {
        errors.push({ nodeId: node.id, message: 'ID doit être en SCREAMING_SNAKE_CASE' })
      }
      if (nodeIds.has(node.id)) {
        errors.push({ nodeId: node.id, message: 'ID dupliqué' })
      }
      nodeIds.add(node.id)
    }

    // Vérifier références
    for (const node of nodes) {
      if (node.nextNode && !nodeIds.has(node.nextNode)) {
        errors.push({
          nodeId: node.id,
          message: `nextNode '${node.nextNode}' n'existe pas`,
        })
      }
      if (node.successNode && !nodeIds.has(node.successNode)) {
        errors.push({
          nodeId: node.id,
          message: `successNode '${node.successNode}' n'existe pas`,
        })
      }
      if (node.failureNode && !nodeIds.has(node.failureNode)) {
        errors.push({
          nodeId: node.id,
          message: `failureNode '${node.failureNode}' n'existe pas`,
        })
      }
      if (node.choices) {
        for (let i = 0; i < node.choices.length; i++) {
          const choice = node.choices[i]
          if (!choice.text || choice.text.trim() === '') {
            errors.push({
              nodeId: node.id,
              choiceIndex: i,
              message: 'Le texte du choix ne peut pas être vide',
            })
          }
          if (!choice.targetNode || choice.targetNode.trim() === '') {
            errors.push({
              nodeId: node.id,
              choiceIndex: i,
              message: 'targetNode est requis',
            })
          } else if (choice.targetNode !== 'END' && !nodeIds.has(choice.targetNode)) {
            // "END" est une valeur spéciale acceptée pour terminer le dialogue
            errors.push({
              nodeId: node.id,
              choiceIndex: i,
              message: `targetNode '${choice.targetNode}' n'existe pas`,
            })
          }
          if (choice.testSuccessNode && !nodeIds.has(choice.testSuccessNode)) {
            errors.push({
              nodeId: node.id,
              choiceIndex: i,
              message: `testSuccessNode '${choice.testSuccessNode}' n'existe pas`,
            })
          }
          if (choice.testFailureNode && !nodeIds.has(choice.testFailureNode)) {
            errors.push({
              nodeId: node.id,
              choiceIndex: i,
              message: `testFailureNode '${choice.testFailureNode}' n'existe pas`,
            })
          }
        }
      }
    }

    return errors
  }, [nodes])

  const isValid = validationErrors.length === 0

  // Mettre à jour un nœud (par ID, pas par index)
  const updateNode = useCallback((nodeId: string, updates: Partial<UnityDialogueNode>) => {
    setNodes((prev) => {
      return prev.map((node) => (node.id === nodeId ? { ...node, ...updates } : node))
    })
  }, [])

  // Mettre à jour le speaker d'un nœud
  const updateNodeSpeaker = useCallback(
    (nodeId: string, speaker: string) => {
      updateNode(nodeId, { speaker: speaker.trim() || undefined })
    },
    [updateNode]
  )

  // Mettre à jour le line d'un nœud
  const updateNodeLine = useCallback(
    (nodeId: string, line: string) => {
      updateNode(nodeId, { line: line.trim() || undefined })
    },
    [updateNode]
  )

  // Mettre à jour un choix (par nodeId, pas par index)
  const updateChoice = useCallback(
    (nodeId: string, choiceIndex: number, updates: Partial<UnityDialogueChoice>) => {
      setNodes((prev) => {
        return prev.map((node) => {
          if (node.id !== nodeId) return node
        const choices = [...(node.choices || [])]
        choices[choiceIndex] = { ...choices[choiceIndex], ...updates }
          return { ...node, choices }
        })
      })
    },
    []
  )

  // Ajouter un choix (par nodeId, pas par index)
  const addChoice = useCallback(
    (nodeId: string) => {
      setNodes((prev) => {
        return prev.map((node) => {
          if (node.id !== nodeId) return node
        const choices = [...(node.choices || [])]
          choices.push({ text: '', targetNode: 'END' })
          return { ...node, choices }
        })
      })
    },
    []
  )

  // Supprimer un choix (par nodeId, pas par index)
  const removeChoice = useCallback((nodeId: string, choiceIndex: number) => {
    setNodes((prev) => {
      return prev.map((node) => {
        if (node.id !== nodeId) return node
      const choices = [...(node.choices || [])]
      choices.splice(choiceIndex, 1)
        return { ...node, choices: choices.length > 0 ? choices : undefined }
      })
    })
  }, [])

  // Sauvegarder
  const handleSave = useCallback(async () => {
    if (!isValid) {
      setError('Corrigez les erreurs de validation avant de sauvegarder')
      return
    }

    setIsSaving(true)
    setError(null)

    try {
      // Reconstruire le JSON (préserver tous les champs, y compris ceux non édités)
      const jsonContent = JSON.stringify(nodes, null, 2)

      const request: ExportUnityDialogueRequest = {
        json_content: jsonContent,
        title: title || 'Dialogue Unity',
        filename: filename, // Si on édite un fichier existant, réutiliser le filename
      }

      const result = await dialoguesAPI.exportUnityDialogue(request)
      toast(`Dialogue sauvegardé: ${result.filename}`, 'success', 5000)
      onSave?.(result.filename)
    } catch (err) {
      const errorMessage = getErrorMessage(err)
      setError(errorMessage)
      toast(`Erreur lors de la sauvegarde: ${errorMessage}`, 'error')
    } finally {
      setIsSaving(false)
    }
  }, [isValid, nodes, title, filename, toast, onSave])

  // Toggle collapse pour options avancées
  const toggleAdvanced = useCallback((nodeId: string) => {
    setExpandedAdvanced((prev) => {
      const next = new Set(prev)
      if (next.has(nodeId)) {
        next.delete(nodeId)
      } else {
        next.add(nodeId)
      }
      return next
    })
  }, [])

  // Obtenir les erreurs pour un nœud spécifique
  const getNodeErrors = useCallback(
    (nodeId: string) => {
      return validationErrors.filter((e) => e.nodeId === nodeId)
    },
    [validationErrors]
  )

  // Obtenir les IDs de nœuds pour autocomplétion (inclut "END" pour terminer le dialogue)
  const nodeIds = useMemo(() => {
    const ids = new Set(nodes.map((n) => n.id))
    ids.add('END') // Ajouter "END" comme option valide pour terminer le dialogue
    return ids
  }, [nodes])

  // Filtrer le nœud "END" de l'affichage : ce n'est pas un vrai nœud éditable,
  // c'est juste un marqueur de fin géré implicitement par Unity
  const displayableNodes = useMemo(() => {
    return nodes.filter((node) => node.id !== 'END')
  }, [nodes])

  if (displayableNodes.length === 0) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: theme.text.secondary }}>
        Aucun dialogue à éditer (JSON invalide ou vide)
      </div>
    )
  }

  return (
    <div style={{ padding: '1rem', height: '100%', overflowY: 'auto' }}>
      {/* En-tête avec actions */}
      <div
        style={{
          marginBottom: '1rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          paddingBottom: '1rem',
          borderBottom: `1px solid ${theme.border.primary}`,
        }}
      >
        <h3 style={{ margin: 0, color: theme.text.primary }}>
          {title || 'Éditeur de Dialogue Unity'}
        </h3>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {onCancel && (
            <button
              onClick={onCancel}
              style={{
                padding: '0.5rem 1rem',
                border: `1px solid ${theme.border.primary}`,
                borderRadius: '4px',
                backgroundColor: theme.button.default.background,
                color: theme.button.default.color,
                cursor: 'pointer',
              }}
            >
              Annuler
            </button>
          )}
          <button
            onClick={handleSave}
            disabled={isSaving || !isValid}
            style={{
              padding: '0.5rem 1rem',
              border: 'none',
              borderRadius: '4px',
              backgroundColor: theme.button.primary.background,
              color: theme.button.primary.color,
              cursor: isValid && !isSaving ? 'pointer' : 'not-allowed',
              opacity: isValid && !isSaving ? 1 : 0.6,
            }}
          >
            {isSaving ? 'Sauvegarde...' : 'Sauvegarder'}
          </button>
        </div>
      </div>

      {/* Erreurs de validation */}
      {!isValid && (
        <div
          style={{
            padding: '0.75rem',
            marginBottom: '1rem',
            backgroundColor: theme.state.error.background,
            color: theme.state.error.color,
            borderRadius: '4px',
            border: `1px solid ${theme.border.primary}`,
          }}
        >
          <div style={{ fontWeight: 'bold', marginBottom: '0.5rem' }}>Erreurs de validation:</div>
          <ul style={{ margin: 0, paddingLeft: '1.5rem' }}>
            {validationErrors.map((err, i) => (
              <li key={i} style={{ marginBottom: '0.25rem' }}>
                {err.nodeId && `[${err.nodeId}] `}
                {err.choiceIndex !== undefined && `Choix ${err.choiceIndex + 1}: `}
                {err.message}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Erreur générale */}
      {error && (
        <div
          style={{
            padding: '0.75rem',
            marginBottom: '1rem',
            backgroundColor: theme.state.error.background,
            color: theme.state.error.color,
            borderRadius: '4px',
            border: `1px solid ${theme.border.primary}`,
          }}
        >
          {error}
        </div>
      )}

      {/* Liste des nœuds (END est filtré car ce n'est pas un vrai nœud éditable) */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {displayableNodes.map((node) => {
          const nodeErrors = getNodeErrors(node.id)
          const isAdvancedExpanded = expandedAdvanced.has(node.id)

          return (
            <div
              key={node.id}
              style={{
                border: `1px solid ${theme.border.primary}`,
                borderRadius: '4px',
                padding: '1rem',
                backgroundColor: theme.background.panel,
              }}
            >
              {/* En-tête du nœud */}
              <div
                style={{
                  marginBottom: '1rem',
                  paddingBottom: '0.5rem',
                  borderBottom: `1px solid ${theme.border.primary}`,
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <div>
                    <span
                      style={{
                        fontFamily: 'monospace',
                        fontSize: '0.9rem',
                        backgroundColor: theme.background.secondary,
                        padding: '0.25rem 0.5rem',
                        borderRadius: '4px',
                        color: theme.text.primary,
                      }}
                    >
                      ID: {node.id}
                    </span>
                    {nodeErrors.length > 0 && (
                      <span
                        style={{
                          marginLeft: '0.5rem',
                          color: theme.state.error.color,
                          fontSize: '0.85rem',
                        }}
                      >
                        ({nodeErrors.length} erreur{nodeErrors.length > 1 ? 's' : ''})
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Speaker (éditable) */}
              <div style={{ marginBottom: '1rem' }}>
                <label
                  style={{
                    display: 'block',
                    marginBottom: '0.5rem',
                    color: theme.text.primary,
                    fontSize: '0.9rem',
                    fontWeight: 500,
                  }}
                >
                  Speaker (ID du personnage):
                </label>
                <input
                  type="text"
                  value={node.speaker || ''}
                  onChange={(e) => updateNodeSpeaker(node.id, e.target.value)}
                  placeholder="ex: NPC_1, Player, Narrator"
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    boxSizing: 'border-box',
                    backgroundColor: theme.input.background,
                    border: `1px solid ${theme.input.border}`,
                    color: theme.input.color,
                    borderRadius: '4px',
                  }}
                />
              </div>

              {/* Line (éditable) */}
              <div style={{ marginBottom: '1rem' }}>
                <label
                  style={{
                    display: 'block',
                    marginBottom: '0.5rem',
                    color: theme.text.primary,
                    fontSize: '0.9rem',
                    fontWeight: 500,
                  }}
                >
                  Dialogue (texte):
                </label>
                <textarea
                  value={node.line || ''}
                  onChange={(e) => updateNodeLine(node.id, e.target.value)}
                  placeholder="Texte du dialogue..."
                  rows={3}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    boxSizing: 'border-box',
                    backgroundColor: theme.input.background,
                    border: `1px solid ${theme.input.border}`,
                    color: theme.input.color,
                    borderRadius: '4px',
                    fontFamily: 'inherit',
                    resize: 'vertical',
                  }}
                />
              </div>

              {/* Choices (éditables) */}
              {node.choices && node.choices.length > 0 && (
                <div style={{ marginBottom: '1rem' }}>
                  <label
                    style={{
                      display: 'block',
                      marginBottom: '0.5rem',
                      color: theme.text.primary,
                      fontSize: '0.9rem',
                      fontWeight: 500,
                    }}
                  >
                    Choix du joueur:
                  </label>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {node.choices.map((choice, choiceIndex) => {
                      const choiceErrors = nodeErrors.filter((e) => e.choiceIndex === choiceIndex)
                      return (
                        <div
                          key={choiceIndex}
                          style={{
                            padding: '0.75rem',
                            border: `1px solid ${theme.border.primary}`,
                            borderRadius: '4px',
                            backgroundColor: theme.background.secondary,
                          }}
                        >
                          <div style={{ marginBottom: '0.5rem' }}>
                            <label
                              style={{
                                display: 'block',
                                marginBottom: '0.25rem',
                                color: theme.text.primary,
                                fontSize: '0.85rem',
                              }}
                            >
                              Texte du choix:
                            </label>
                            <textarea
                              value={choice.text}
                              onChange={(e) =>
                                updateChoice(node.id, choiceIndex, { text: e.target.value })
                              }
                              placeholder="Texte du choix..."
                              rows={2}
                              style={{
                                width: '100%',
                                padding: '0.5rem',
                                boxSizing: 'border-box',
                                backgroundColor: theme.input.background,
                                border: `1px solid ${
                                  choiceErrors.some((e) => e.message.includes('texte'))
                                    ? theme.state.error.border
                                    : theme.input.border
                                }`,
                                color: theme.input.color,
                                borderRadius: '4px',
                                fontFamily: 'inherit',
                                resize: 'vertical',
                              }}
                            />
                          </div>
                          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-end' }}>
                            <div style={{ flex: 1 }}>
                              <label
                                style={{
                                  display: 'block',
                                  marginBottom: '0.25rem',
                                  color: theme.text.primary,
                                  fontSize: '0.85rem',
                                }}
                              >
                                Target Node (ID):
                              </label>
                              <input
                                type="text"
                                value={choice.targetNode}
                                onChange={(e) =>
                                  updateChoice(node.id, choiceIndex, {
                                    targetNode: e.target.value,
                                  })
                                }
                                placeholder="ex: NEXT_NODE, END (termine le dialogue)"
                                list={`node-ids-${node.id}`}
                                style={{
                                  width: '100%',
                                  padding: '0.5rem',
                                  boxSizing: 'border-box',
                                  backgroundColor: theme.input.background,
                                  border: `1px solid ${
                                    choiceErrors.some((e) => e.message.includes('targetNode'))
                                      ? theme.state.error.border
                                      : theme.input.border
                                  }`,
                                  color: theme.input.color,
                                  borderRadius: '4px',
                                  fontFamily: 'monospace',
                                }}
                              />
                              <datalist id={`node-ids-${node.id}`}>
                                {Array.from(nodeIds).map((id) => (
                                  <option key={id} value={id} />
                                ))}
                              </datalist>
                            </div>
                            <button
                              onClick={() => removeChoice(node.id, choiceIndex)}
                              style={{
                                padding: '0.5rem',
                                border: `1px solid ${theme.border.primary}`,
                                borderRadius: '4px',
                                backgroundColor: theme.button.default.background,
                                color: theme.button.default.color,
                                cursor: 'pointer',
                                fontSize: '1.2rem',
                              }}
                              title="Supprimer ce choix"
                            >
                              🗑️
                            </button>
                          </div>
                          {choiceErrors.length > 0 && (
                            <div
                              style={{
                                marginTop: '0.5rem',
                                fontSize: '0.85rem',
                                color: theme.state.error.color,
                              }}
                            >
                              {choiceErrors.map((err, i) => (
                                <div key={i}>{err.message}</div>
                              ))}
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* Bouton ajouter choix */}
              {(!node.choices || node.choices.length < 4) && (
                <div style={{ marginBottom: '1rem' }}>
                  <button
                    onClick={() => addChoice(node.id)}
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
                    + Ajouter un choix
                  </button>
                </div>
              )}

              {/* Options avancées (lecture seule) */}
              <div>
                <button
                  onClick={() => toggleAdvanced(node.id)}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    border: `1px solid ${theme.border.primary}`,
                    borderRadius: '4px',
                    backgroundColor: theme.button.default.background,
                    color: theme.button.default.color,
                    cursor: 'pointer',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <span>{isAdvancedExpanded ? '▼' : '▶'} Options avancées (lecture seule)</span>
                </button>
                {isAdvancedExpanded && (
                  <div
                    style={{
                      marginTop: '0.5rem',
                      padding: '1rem',
                      backgroundColor: theme.background.secondary,
                      borderRadius: '4px',
                      border: `1px solid ${theme.border.primary}`,
                    }}
                  >
                    <pre
                      style={{
                        margin: 0,
                        fontSize: '0.85rem',
                        color: theme.text.secondary,
                        fontFamily: 'monospace',
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                      }}
                    >
                      {JSON.stringify(
                        {
                          ...node,
                          speaker: node.speaker,
                          line: node.line,
                          choices: node.choices,
                        },
                        null,
                        2
                      )}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
})

