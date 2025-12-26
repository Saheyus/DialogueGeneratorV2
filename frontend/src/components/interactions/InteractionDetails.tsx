/**
 * Composant pour afficher les détails d'une interaction.
 */
import { useState, useEffect, useCallback } from 'react'
import * as interactionsAPI from '../../api/interactions'
import { getErrorMessage } from '../../types/errors'
import { theme } from '../../theme'
import type { InteractionResponse } from '../../types/api'

interface InteractionDetailsProps {
  interactionId: string | null
  onClose: () => void
}

export function InteractionDetails({ interactionId, onClose }: InteractionDetailsProps) {
  const [interaction, setInteraction] = useState<InteractionResponse | null>(null)
  const [parents, setParents] = useState<string[]>([])
  const [children, setChildren] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  const loadInteraction = useCallback(async () => {
    if (!interactionId) return

    setIsLoading(true)
    setError(null)
    try {
      const data = await interactionsAPI.getInteraction(interactionId)
      setInteraction(data)
    } catch (err) {
      setError(getErrorMessage(err))
      setInteraction(null)
    } finally {
      setIsLoading(false)
    }
  }, [interactionId])

  const loadRelations = useCallback(async () => {
    if (!interactionId) return

    try {
      const [parentsRes, childrenRes] = await Promise.all([
        interactionsAPI.getInteractionParents(interactionId),
        interactionsAPI.getInteractionChildren(interactionId),
      ])
      setParents(parentsRes.parents || [])
      setChildren(childrenRes.children || [])
    } catch (err) {
      // Ignorer les erreurs pour les relations
      console.error('Erreur lors du chargement des relations:', err)
    }
  }, [interactionId])

  useEffect(() => {
    if (interactionId) {
      loadInteraction()
      loadRelations()
    } else {
      setInteraction(null)
      setParents([])
      setChildren([])
    }
  }, [interactionId, loadInteraction, loadRelations])

  const handleDelete = async () => {
    if (!interactionId) return

    if (!confirm('Êtes-vous sûr de vouloir supprimer cette interaction ?')) {
      return
    }

    setIsDeleting(true)
    try {
      await interactionsAPI.deleteInteraction(interactionId)
      onClose()
      // Optionnel: recharger la liste (nécessiterait un callback parent)
    } catch (err) {
      alert(getErrorMessage(err))
    } finally {
      setIsDeleting(false)
    }
  }

  if (!interactionId) {
    return (
      <div style={{ padding: '1rem', color: theme.text.secondary, textAlign: 'center' }}>
        Sélectionnez une interaction pour voir ses détails
      </div>
    )
  }

  if (isLoading) {
    return (
      <div style={{ padding: '1rem', textAlign: 'center', color: theme.text.secondary }}>
        <div>Chargement...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ 
        padding: '1rem', 
        color: theme.state.error.color, 
        backgroundColor: theme.state.error.background, 
        borderRadius: '4px' 
      }}>
        {error}
        <button
          onClick={loadInteraction}
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

  if (!interaction) {
    return null
  }

  return (
    <div style={{ 
      padding: '1rem', 
      height: '100%', 
      minHeight: 0,
      overflowY: 'auto',
      boxSizing: 'border-box',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3 style={{ margin: 0, color: theme.text.primary }}>{interaction.title}</h3>
        <button
          onClick={onClose}
          style={{
            padding: '0.25rem 0.5rem',
            border: `1px solid ${theme.border.primary}`,
            borderRadius: '4px',
            backgroundColor: theme.button.default.background,
            color: theme.button.default.color,
            cursor: 'pointer',
          }}
        >
          ✕
        </button>
      </div>

      <div style={{ marginBottom: '1rem', fontSize: '0.9rem', color: theme.text.secondary }}>
        <div>
          <strong style={{ color: theme.text.primary }}>ID:</strong> {interaction.interaction_id}
        </div>
        {interaction.header_tags && interaction.header_tags.length > 0 && (
          <div style={{ marginTop: '0.5rem' }}>
            <strong style={{ color: theme.text.primary }}>Tags:</strong> {interaction.header_tags.join(', ')}
          </div>
        )}
        {interaction.header_commands && interaction.header_commands.length > 0 && (
          <div style={{ marginTop: '0.5rem' }}>
            <strong style={{ color: theme.text.primary }}>Commandes:</strong> {interaction.header_commands.join(', ')}
          </div>
        )}
        {interaction.next_interaction_id_if_no_choices && (
          <div style={{ marginTop: '0.5rem' }}>
            <strong style={{ color: theme.text.primary }}>Suivante (si pas de choix):</strong> {interaction.next_interaction_id_if_no_choices}
          </div>
        )}
      </div>

      {(parents.length > 0 || children.length > 0) && (
        <div style={{ 
          marginBottom: '1rem', 
          padding: '0.75rem', 
          backgroundColor: theme.state.info.background, 
          borderRadius: '4px',
          color: theme.state.info.color,
        }}>
          <strong>Relations:</strong>
          {parents.length > 0 && (
            <div style={{ marginTop: '0.5rem' }}>
              <strong>Parents:</strong> {parents.join(', ')}
            </div>
          )}
          {children.length > 0 && (
            <div style={{ marginTop: '0.5rem' }}>
              <strong>Enfants:</strong> {children.join(', ')}
            </div>
          )}
        </div>
      )}

      <div style={{ marginBottom: '1rem' }}>
        <strong style={{ color: theme.text.primary }}>Éléments:</strong>
        <pre
          style={{
            marginTop: '0.5rem',
            padding: '1rem',
            backgroundColor: theme.background.secondary,
            border: `1px solid ${theme.border.primary}`,
            borderRadius: '4px',
            overflow: 'auto',
            fontSize: '0.9rem',
            color: theme.text.secondary,
          }}
        >
          {JSON.stringify(interaction.elements, null, 2)}
        </pre>
      </div>

      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
        <button
          onClick={handleDelete}
          disabled={isDeleting}
          style={{
            padding: '0.5rem 1rem',
            border: `1px solid ${theme.state.error.color}`,
            borderRadius: '4px',
            backgroundColor: theme.state.error.color,
            color: '#fff',
            cursor: isDeleting ? 'not-allowed' : 'pointer',
            opacity: isDeleting ? 0.6 : 1,
          }}
        >
          {isDeleting ? 'Suppression...' : 'Supprimer'}
        </button>
      </div>
    </div>
  )
}

