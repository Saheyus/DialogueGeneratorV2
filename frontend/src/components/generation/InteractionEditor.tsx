/**
 * Éditeur complet pour les interactions avec support de modification des éléments.
 */
import { memo, useState, useCallback } from 'react'
import * as interactionsAPI from '../../api/interactions'
import { getErrorMessage } from '../../types/errors'
import { theme } from '../../theme'
import type { InteractionResponse, InteractionElement } from '../../types/api'

export interface InteractionEditorProps {
  interaction: InteractionResponse | null
  onSave?: (interaction: InteractionResponse) => void
  onCancel?: () => void
}

export const InteractionEditor = memo(function InteractionEditor({
  interaction,
  onSave,
  onCancel,
}: InteractionEditorProps) {
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!interaction) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: theme.text.secondary }}>
        Aucune interaction sélectionnée
      </div>
    )
  }

  const handleSave = useCallback(async () => {
    if (!interaction) return

    setIsSaving(true)
    setError(null)
    try {
      // S'assurer que tous les champs sont explicitement envoyés, notamment les éléments
      const updateData: Partial<InteractionResponse> = {
        title: interaction.title,
        elements: interaction.elements || [],
        header_commands: interaction.header_commands || [],
        header_tags: interaction.header_tags || [],
        next_interaction_id_if_no_choices: interaction.next_interaction_id_if_no_choices,
      }
      const updated = await interactionsAPI.updateInteraction(interaction.interaction_id, updateData)
      onSave?.(updated)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setIsSaving(false)
    }
  }, [interaction, onSave])

  return (
    <div style={{ padding: '1rem', height: '100%', overflowY: 'auto' }}>
      <div style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0, color: theme.text.primary }}>Éditeur d'Interaction</h3>
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
            disabled={isSaving}
            style={{
              padding: '0.5rem 1rem',
              border: 'none',
              borderRadius: '4px',
              backgroundColor: theme.button.primary.background,
              color: theme.button.primary.color,
              cursor: isSaving ? 'not-allowed' : 'pointer',
              opacity: isSaving ? 0.6 : 1,
            }}
          >
            {isSaving ? 'Sauvegarde...' : 'Sauvegarder'}
          </button>
        </div>
      </div>

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

      {interaction.narrative_warnings && interaction.narrative_warnings.length > 0 && (
        <div
          style={{
            padding: '0.75rem',
            marginBottom: '1rem',
            backgroundColor: theme.state.warning.background,
            color: theme.state.warning.color,
            borderRadius: '4px',
            border: `1px solid ${theme.border.primary}`,
          }}
        >
          <div style={{ fontWeight: 'bold', marginBottom: '0.5rem' }}>
            ⚠️ Avertissements narratifs
          </div>
          <ul style={{ margin: 0, paddingLeft: '1.5rem' }}>
            {interaction.narrative_warnings.map((warning, index) => (
              <li key={index} style={{ marginBottom: '0.25rem' }}>
                {warning}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div style={{ marginBottom: '1rem' }}>
        <label style={{ display: 'block', marginBottom: '0.5rem', color: theme.text.primary }}>
          Titre:
          <input
            type="text"
            value={interaction.title || ''}
            readOnly
            style={{
              width: '100%',
              padding: '0.5rem',
              marginTop: '0.25rem',
              boxSizing: 'border-box',
              backgroundColor: theme.input.background,
              border: `1px solid ${theme.input.border}`,
              color: theme.input.color,
            }}
          />
        </label>
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <label style={{ display: 'block', marginBottom: '0.5rem', color: theme.text.primary }}>
          ID:
          <input
            type="text"
            value={interaction.interaction_id}
            readOnly
            style={{
              width: '100%',
              padding: '0.5rem',
              marginTop: '0.25rem',
              boxSizing: 'border-box',
              backgroundColor: theme.background.secondary,
              border: `1px solid ${theme.input.border}`,
              color: theme.text.secondary,
              fontFamily: 'monospace',
              fontSize: '0.85rem',
            }}
          />
        </label>
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <h4 style={{ marginBottom: '0.5rem', color: theme.text.primary }}>Éléments:</h4>
        <div
          style={{
            border: `1px solid ${theme.border.primary}`,
            borderRadius: '4px',
            backgroundColor: theme.background.tertiary,
          }}
        >
          {interaction.elements.length === 0 ? (
            <div style={{ padding: '1rem', textAlign: 'center', color: theme.text.secondary }}>
              Aucun élément
            </div>
          ) : (
            interaction.elements.map((element: InteractionElement, index: number) => (
              <div
                key={index}
                style={{
                  padding: '1rem',
                  borderBottom:
                    index < interaction.elements.length - 1
                      ? `1px solid ${theme.border.primary}`
                      : 'none',
                }}
              >
                <div style={{ marginBottom: '0.5rem', fontSize: '0.85rem', color: theme.text.secondary }}>
                  <strong>Type:</strong> {(element as any).element_type || 'unknown'}
                </div>
                <pre
                  style={{
                    margin: 0,
                    padding: '0.75rem',
                    backgroundColor: theme.background.secondary,
                    border: `1px solid ${theme.border.primary}`,
                    borderRadius: '4px',
                    fontSize: '0.85rem',
                    color: theme.text.secondary,
                    overflow: 'auto',
                    whiteSpace: 'pre-wrap',
                    wordWrap: 'break-word',
                  }}
                >
                  {JSON.stringify(element, null, 2)}
                </pre>
              </div>
            ))
          )}
        </div>
      </div>

      {interaction.header_tags && interaction.header_tags.length > 0 && (
        <div style={{ marginBottom: '1rem' }}>
          <h4 style={{ marginBottom: '0.5rem', color: theme.text.primary }}>Tags:</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {interaction.header_tags.map((tag, index) => (
              <span
                key={index}
                style={{
                  padding: '0.25rem 0.5rem',
                  backgroundColor: theme.background.secondary,
                  border: `1px solid ${theme.border.primary}`,
                  borderRadius: '4px',
                  fontSize: '0.85rem',
                  color: theme.text.secondary,
                }}
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}

      {interaction.header_commands && interaction.header_commands.length > 0 && (
        <div style={{ marginBottom: '1rem' }}>
          <h4 style={{ marginBottom: '0.5rem', color: theme.text.primary }}>Commandes:</h4>
          <div
            style={{
              padding: '0.75rem',
              backgroundColor: theme.background.secondary,
              border: `1px solid ${theme.border.primary}`,
              borderRadius: '4px',
              fontFamily: 'monospace',
              fontSize: '0.85rem',
              color: theme.text.secondary,
            }}
          >
            {interaction.header_commands.join(', ')}
          </div>
        </div>
      )}
    </div>
  )
})



