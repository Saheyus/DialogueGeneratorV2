/**
 * Composant pour afficher les détails d'un élément de contexte.
 */
import type { CharacterResponse, LocationResponse, ItemResponse } from '../../types/api'
import { theme } from '../../theme'

type ContextItem = CharacterResponse | LocationResponse | ItemResponse

interface ContextDetailProps {
  item: ContextItem | null
}

export function ContextDetail({ item }: ContextDetailProps) {
  if (!item) {
    return (
      <div style={{ padding: '1rem', color: theme.text.secondary, textAlign: 'center' }}>
        Sélectionnez un élément pour voir ses détails
      </div>
    )
  }

  const renderData = (data: Record<string, unknown>, depth = 0): React.ReactNode => {
    if (depth > 3) {
      return <span style={{ color: theme.text.tertiary }}>...</span>
    }

    return Object.entries(data).map(([key, value]) => {
      if (value === null || value === undefined) {
        return null
      }

      if (typeof value === 'object' && !Array.isArray(value) && value !== null) {
        return (
          <div key={key} style={{ marginLeft: `${depth * 1}rem`, marginBottom: '0.5rem' }}>
            <strong style={{ color: theme.text.primary }}>{key}:</strong>
            <div style={{ marginLeft: '0.5rem' }}>{renderData(value as Record<string, unknown>, depth + 1)}</div>
          </div>
        )
      }

      if (Array.isArray(value)) {
        return (
          <div key={key} style={{ marginLeft: `${depth * 1}rem`, marginBottom: '0.5rem' }}>
            <strong style={{ color: theme.text.primary }}>{key}:</strong>
            <ul style={{ marginLeft: '1rem', marginTop: '0.25rem', color: theme.text.secondary }}>
              {value.map((v, i) => (
                <li key={i}>{String(v)}</li>
              ))}
            </ul>
          </div>
        )
      }

      return (
        <div key={key} style={{ marginLeft: `${depth * 1}rem`, marginBottom: '0.5rem' }}>
          <strong style={{ color: theme.text.primary }}>{key}:</strong>{' '}
          <span style={{ color: theme.text.secondary }}>{String(value)}</span>
        </div>
      )
    })
  }

  return (
    <div style={{ padding: '1rem', height: '100%', overflowY: 'auto' }}>
      <h3 style={{ marginTop: 0, marginBottom: '1rem', color: theme.text.primary }}>{item.name}</h3>
      <div style={{ borderTop: `1px solid ${theme.border.primary}`, paddingTop: '1rem' }}>
        {renderData(item.data)}
      </div>
    </div>
  )
}

