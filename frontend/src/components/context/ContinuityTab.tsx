/**
 * Onglet Continuité pour sélectionner une interaction précédente comme contexte.
 */
import { memo, useState, useEffect, useCallback } from 'react'
import * as interactionsAPI from '../../api/interactions'
import { getErrorMessage } from '../../types/errors'
import { theme } from '../../theme'
import type { InteractionResponse, InteractionContextPathResponse } from '../../types/api'

export interface ContinuityTabProps {
  onSelectContext?: (interactionId: string | null, path: InteractionResponse[]) => void
}

export const ContinuityTab = memo(function ContinuityTab({
  onSelectContext,
}: ContinuityTabProps) {
  const [interactions, setInteractions] = useState<InteractionResponse[]>([])
  const [selectedInteractionId, setSelectedInteractionId] = useState<string | null>(null)
  const [path, setPath] = useState<InteractionResponse[]>([])
  const [contextPreview, setContextPreview] = useState<string>('')
  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingPath, setIsLoadingPath] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadInteractions = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await interactionsAPI.listInteractions()
      setInteractions(response.interactions)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadInteractions()
  }, [loadInteractions])

  const loadPath = useCallback(async (interactionId: string) => {
    setIsLoadingPath(true)
    try {
      const response: InteractionContextPathResponse = await interactionsAPI.getInteractionContextPath(interactionId)
      setPath(response.path || [])
      
      // Générer un aperçu du contexte formaté
      const preview = response.path
        .map((interaction, index) => {
          const dialogueLines = interaction.elements
            .filter((el: any) => el.element_type === 'dialogue_line')
            .map((el: any) => `${el.speaker || 'NPC'}: ${el.text}`)
            .join('\n')
          return `${index + 1}. ${interaction.title || interaction.interaction_id}\n${dialogueLines}`
        })
        .join('\n\n---\n\n')
      setContextPreview(preview)
    } catch (err) {
      console.error('Erreur lors du chargement du chemin:', err)
      setPath([])
      setContextPreview('')
    } finally {
      setIsLoadingPath(false)
    }
  }, [])

  useEffect(() => {
    if (selectedInteractionId) {
      loadPath(selectedInteractionId)
    } else {
      setPath([])
      setContextPreview('')
    }
  }, [selectedInteractionId, loadPath])

  const handleUseContext = useCallback(() => {
    if (selectedInteractionId && path.length > 0) {
      onSelectContext?.(selectedInteractionId, path)
    }
  }, [selectedInteractionId, path, onSelectContext])

  if (isLoading) {
    return (
      <div style={{ padding: '1rem', textAlign: 'center', color: theme.text.secondary }}>
        Chargement des interactions...
      </div>
    )
  }

  if (error) {
    return (
      <div
        style={{
          padding: '1rem',
          color: theme.state.error.color,
          backgroundColor: theme.state.error.background,
          borderRadius: '4px',
        }}
      >
        {error}
        <button
          onClick={loadInteractions}
          style={{
            marginTop: '0.5rem',
            padding: '0.5rem 1rem',
            border: `1px solid ${theme.border.primary}`,
            borderRadius: '4px',
            backgroundColor: theme.button.default.background,
            color: theme.button.default.color,
            cursor: 'pointer',
          }}
        >
          Réessayer
        </button>
      </div>
    )
  }

  return (
    <div style={{ padding: '1rem', height: '100%', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div>
        <h4 style={{ marginTop: 0, marginBottom: '0.5rem', color: theme.text.primary }}>Interactions Existantes</h4>
        <div style={{ maxHeight: '200px', overflowY: 'auto', border: `1px solid ${theme.border.primary}`, borderRadius: '4px' }}>
          {interactions.length === 0 ? (
            <div style={{ padding: '1rem', textAlign: 'center', color: theme.text.secondary }}>
              Aucune interaction
            </div>
          ) : (
            interactions.map((interaction) => (
              <div
                key={interaction.interaction_id}
                onClick={() => setSelectedInteractionId(interaction.interaction_id)}
                style={{
                  padding: '0.75rem',
                  borderBottom: `1px solid ${theme.border.primary}`,
                  backgroundColor:
                    selectedInteractionId === interaction.interaction_id
                      ? theme.state.selected.background
                      : 'transparent',
                  color: theme.text.primary,
                  cursor: 'pointer',
                }}
                onMouseEnter={(e) => {
                  if (selectedInteractionId !== interaction.interaction_id) {
                    e.currentTarget.style.backgroundColor = theme.state.hover.background
                  }
                }}
                onMouseLeave={(e) => {
                  if (selectedInteractionId !== interaction.interaction_id) {
                    e.currentTarget.style.backgroundColor = 'transparent'
                  }
                }}
              >
                {interaction.title || interaction.interaction_id}
                <div style={{ fontSize: '0.85rem', color: theme.text.secondary, marginTop: '0.25rem' }}>
                  ID: {interaction.interaction_id.substring(0, 8)}...
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {selectedInteractionId && (
        <>
          <div>
            <h4 style={{ marginTop: 0, marginBottom: '0.5rem', color: theme.text.primary }}>
              Chemin de Dialogue (vers l'interaction sélectionnée)
            </h4>
            {isLoadingPath ? (
              <div style={{ padding: '1rem', textAlign: 'center', color: theme.text.secondary }}>
                Chargement du chemin...
              </div>
            ) : path.length === 0 ? (
              <div style={{ padding: '1rem', color: theme.text.secondary }}>
                Aucun chemin disponible
              </div>
            ) : (
              <div
                style={{
                  padding: '1rem',
                  backgroundColor: theme.background.secondary,
                  border: `1px solid ${theme.border.primary}`,
                  borderRadius: '4px',
                  maxHeight: '150px',
                  overflowY: 'auto',
                }}
              >
                {path.map((interaction, index) => (
                  <div key={interaction.interaction_id} style={{ marginBottom: '0.5rem' }}>
                    <strong style={{ color: theme.text.primary }}>
                      {index + 1}. {interaction.title || interaction.interaction_id}
                    </strong>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div>
            <h4 style={{ marginTop: 0, marginBottom: '0.5rem', color: theme.text.primary }}>
              Aperçu du contexte injecté dans le LLM
            </h4>
            <pre
              style={{
                padding: '1rem',
                backgroundColor: theme.background.secondary,
                border: `1px solid ${theme.border.primary}`,
                borderRadius: '4px',
                fontFamily: 'monospace',
                fontSize: '0.85rem',
                color: theme.text.secondary,
                maxHeight: '200px',
                overflowY: 'auto',
                whiteSpace: 'pre-wrap',
                wordWrap: 'break-word',
              }}
            >
              {contextPreview || 'Sélectionnez une interaction pour voir l\'aperçu du contexte'}
            </pre>
          </div>

          <button
            onClick={handleUseContext}
            disabled={!selectedInteractionId || path.length === 0}
            style={{
              padding: '0.75rem 1.5rem',
              border: 'none',
              borderRadius: '4px',
              backgroundColor: theme.button.primary.background,
              color: theme.button.primary.color,
              cursor: !selectedInteractionId || path.length === 0 ? 'not-allowed' : 'pointer',
              opacity: !selectedInteractionId || path.length === 0 ? 0.6 : 1,
            }}
          >
            Utiliser comme Contexte de Départ
          </button>
        </>
      )}
    </div>
  )
})

