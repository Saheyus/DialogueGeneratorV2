/**
 * Composant pour afficher et gérer une séquence d'interactions.
 */
import { memo, useState, useEffect, useCallback } from 'react'
import * as interactionsAPI from '../../api/interactions'
import { getErrorMessage } from '../../types/errors'
import { theme } from '../../theme'
import type { InteractionResponse } from '../../types/api'

export interface InteractionSequenceProps {
  onSelectInteraction?: (interaction: InteractionResponse | null) => void
  selectedInteractionId?: string | null
}

export const InteractionSequence = memo(function InteractionSequence({
  onSelectInteraction,
  selectedInteractionId,
}: InteractionSequenceProps) {
  const [interactions, setInteractions] = useState<InteractionResponse[]>([])
  const [isLoading, setIsLoading] = useState(true)
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

  const handleItemClick = useCallback(
    (interaction: InteractionResponse) => {
      if (selectedInteractionId === interaction.interaction_id) {
        onSelectInteraction?.(null)
      } else {
        onSelectInteraction?.(interaction)
      }
    },
    [selectedInteractionId, onSelectInteraction]
  )

  const handleDelete = useCallback(
    async (interactionId: string, e: React.MouseEvent) => {
      e.stopPropagation()
      if (!confirm('Êtes-vous sûr de vouloir supprimer cette interaction de la séquence ?')) {
        return
      }

      try {
        await interactionsAPI.deleteInteraction(interactionId)
        await loadInteractions()
        if (selectedInteractionId === interactionId) {
          onSelectInteraction?.(null)
        }
      } catch (err) {
        alert(getErrorMessage(err))
      }
    },
    [loadInteractions, selectedInteractionId, onSelectInteraction]
  )

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
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ padding: '0.5rem', borderBottom: `1px solid ${theme.border.primary}` }}>
        <h4 style={{ margin: 0, fontSize: '1rem', fontWeight: 'bold', color: theme.text.primary }}>
          Séquence d'Interactions
        </h4>
        <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: theme.text.secondary }}>
          {interactions.length} interaction{interactions.length !== 1 ? 's' : ''}
        </div>
      </div>
      <div style={{ flex: 1, overflowY: 'auto', padding: '0.5rem' }}>
        {interactions.length === 0 ? (
          <div style={{ padding: '1rem', textAlign: 'center', color: theme.text.secondary }}>
            Aucune interaction
          </div>
        ) : (
          interactions.map((interaction, index) => (
            <div
              key={interaction.interaction_id}
              onClick={() => handleItemClick(interaction)}
              style={{
                padding: '0.75rem',
                marginBottom: '0.5rem',
                border: `1px solid ${theme.border.primary}`,
                borderRadius: '4px',
                backgroundColor:
                  selectedInteractionId === interaction.interaction_id
                    ? theme.state.selected.background
                    : theme.background.tertiary,
                color: theme.text.primary,
                cursor: 'pointer',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
              onMouseEnter={(e) => {
                if (selectedInteractionId !== interaction.interaction_id) {
                  e.currentTarget.style.backgroundColor = theme.state.hover.background
                }
              }}
              onMouseLeave={(e) => {
                if (selectedInteractionId !== interaction.interaction_id) {
                  e.currentTarget.style.backgroundColor = theme.background.tertiary
                }
              }}
            >
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 'bold', marginBottom: '0.25rem' }}>
                  {index + 1}. {interaction.title || interaction.interaction_id}
                </div>
                <div style={{ fontSize: '0.85rem', color: theme.text.secondary }}>
                  {interaction.elements.length} élément{interaction.elements.length !== 1 ? 's' : ''}
                </div>
              </div>
              <button
                onClick={(e) => handleDelete(interaction.interaction_id, e)}
                style={{
                  padding: '0.25rem 0.5rem',
                  fontSize: '0.85rem',
                  border: `1px solid ${theme.state.error.color}`,
                  borderRadius: '4px',
                  backgroundColor: 'transparent',
                  color: theme.state.error.color,
                  cursor: 'pointer',
                }}
                title="Supprimer de la séquence"
              >
                ✕
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  )
})

