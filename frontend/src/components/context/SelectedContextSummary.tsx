/**
 * Composant pour afficher un résumé des sélections de contexte actives.
 */
import { memo } from 'react'
import type { ContextSelection } from '../../types/api'
import { theme } from '../../theme'

interface SelectedContextSummaryProps {
  selections: ContextSelection
  onClear: () => void
}

export const SelectedContextSummary = memo(function SelectedContextSummary({
  selections,
  onClear,
}: SelectedContextSummaryProps) {
  const totalSelected =
    selections.characters.length +
    selections.locations.length +
    selections.items.length +
    selections.species.length +
    selections.communities.length +
    selections.dialogues_examples.length

  if (totalSelected === 0) {
    return (
      <div style={{ padding: '1rem', textAlign: 'center', color: theme.text.secondary, fontSize: '0.9rem' }}>
        Aucune sélection
      </div>
    )
  }

  return (
    <div style={{ padding: '1rem', borderTop: `1px solid ${theme.border.primary}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
        <strong style={{ fontSize: '0.9rem', color: theme.text.primary }}>Sélections actives ({totalSelected})</strong>
        <button
          onClick={onClear}
          style={{
            padding: '0.25rem 0.5rem',
            fontSize: '0.8rem',
            border: `1px solid ${theme.border.primary}`,
            borderRadius: '4px',
            backgroundColor: theme.button.default.background,
            color: theme.button.default.color,
            cursor: 'pointer',
          }}
        >
          Tout effacer
        </button>
      </div>
      <div style={{ fontSize: '0.85rem', color: theme.text.secondary }}>
        {selections.characters.length > 0 && (
          <div>
            <strong style={{ color: theme.text.primary }}>Personnages:</strong> {selections.characters.length}
            <div style={{ marginLeft: '1rem', marginTop: '0.25rem' }}>
              {selections.characters.slice(0, 3).join(', ')}
              {selections.characters.length > 3 && ` +${selections.characters.length - 3}`}
            </div>
          </div>
        )}
        {selections.locations.length > 0 && (
          <div style={{ marginTop: '0.5rem' }}>
            <strong style={{ color: theme.text.primary }}>Lieux:</strong> {selections.locations.length}
            <div style={{ marginLeft: '1rem', marginTop: '0.25rem' }}>
              {selections.locations.slice(0, 3).join(', ')}
              {selections.locations.length > 3 && ` +${selections.locations.length - 3}`}
            </div>
          </div>
        )}
        {selections.items.length > 0 && (
          <div style={{ marginTop: '0.5rem' }}>
            <strong style={{ color: theme.text.primary }}>Objets:</strong> {selections.items.length}
            <div style={{ marginLeft: '1rem', marginTop: '0.25rem' }}>
              {selections.items.slice(0, 3).join(', ')}
              {selections.items.length > 3 && ` +${selections.items.length - 3}`}
            </div>
          </div>
        )}
      </div>
    </div>
  )
})

