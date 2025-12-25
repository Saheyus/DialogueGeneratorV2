/**
 * Composant pour afficher un item d'interaction dans une liste.
 */
import type { InteractionResponse, InteractionElement } from '../../types/api'
import { theme } from '../../theme'

interface InteractionItemProps {
  interaction: InteractionResponse
  onClick: () => void
  isSelected?: boolean
}

export function InteractionItem({ interaction, onClick, isSelected = false }: InteractionItemProps) {
  // L'API retourne element_type: "dialogue_line" avec un champ "text", pas "type: dialogue" avec "content"
  const preview = interaction.elements
    ?.find((el): el is Record<string, unknown> & { element_type: string; text: string } => 
      (el && typeof el === 'object' && 'element_type' in el && el.element_type === 'dialogue_line' && 'text' in el && typeof el.text === 'string')
    )
    ?.text?.substring(0, 100) || 'Aucun contenu'

  return (
    <div
      onClick={onClick}
      style={{
        padding: '1rem',
        marginBottom: '0.5rem',
        border: isSelected 
          ? `2px solid ${theme.button.primary.background}` 
          : `1px solid ${theme.border.primary}`,
        borderRadius: '4px',
        backgroundColor: isSelected 
          ? theme.state.selected.background 
          : theme.background.tertiary,
        color: theme.text.primary,
        cursor: 'pointer',
        transition: 'all 0.2s',
      }}
      onMouseEnter={(e) => {
        if (!isSelected) {
          e.currentTarget.style.backgroundColor = theme.state.hover.background
        }
      }}
      onMouseLeave={(e) => {
        if (!isSelected) {
          e.currentTarget.style.backgroundColor = theme.background.tertiary
        }
      }}
    >
      <h4 style={{ margin: 0, marginBottom: '0.5rem', color: theme.text.primary }}>{interaction.title}</h4>
      <div style={{ fontSize: '0.85rem', color: theme.text.secondary, marginBottom: '0.5rem' }}>
        <span>ID: {interaction.interaction_id}</span>
        {interaction.header_tags && interaction.header_tags.length > 0 && (
          <span style={{ marginLeft: '1rem' }}>
            Tags: {interaction.header_tags.join(', ')}
          </span>
        )}
      </div>
      <p style={{ fontSize: '0.9rem', color: theme.text.secondary, margin: 0, whiteSpace: 'pre-wrap' }}>
        {preview}
        {preview.length >= 100 && '...'}
      </p>
    </div>
  )
}

