/**
 * Composant pour afficher les détails d'un élément de contexte.
 */
import type { 
  CharacterResponse, 
  LocationResponse, 
  ItemResponse,
  SpeciesResponse,
  CommunityResponse,
} from '../../types/api'
import { theme } from '../../theme'

type ContextItem = CharacterResponse | LocationResponse | ItemResponse | SpeciesResponse | CommunityResponse

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

  // Extraction des champs importants pour les personnages
  const isCharacter = 'name' in item
  const data = item.data as Record<string, unknown>
  
  const getField = (key: string) => data[key] as string | undefined
  const getArrayField = (key: string) => {
    const val = data[key]
    return Array.isArray(val) ? val : undefined
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
    <div style={{ 
      flex: 1,
      minHeight: 0,
      maxHeight: '100%',
      display: 'flex',
      flexDirection: 'column',
      backgroundColor: theme.background.panel,
      overflow: 'hidden',
    }}>
      <div 
        style={{ 
          flex: '1 1 0%',
          minHeight: 0,
          height: 0,
          overflowY: 'auto',
          overflowX: 'hidden',
          padding: '1rem',
          boxSizing: 'border-box',
          scrollbarGutter: 'stable',
        }}
      >
        <h3 style={{ marginTop: 0, marginBottom: '1rem', color: theme.text.primary }}>{item.name}</h3>
      
      {isCharacter && (
        <>
          {/* Section résumé pour personnages */}
          <div style={{ 
            marginBottom: '1rem', 
            padding: '0.75rem', 
            backgroundColor: theme.background.tertiary, 
            borderRadius: '4px',
            border: `1px solid ${theme.border.primary}`,
          }}>
            {getField('portrait') && (
              <div style={{ marginBottom: '0.5rem', fontSize: '0.85rem' }}>
                <strong style={{ color: theme.text.primary }}>Portrait:</strong>{' '}
                <span style={{ color: theme.text.secondary }}>{getField('portrait')}</span>
              </div>
            )}
            {getArrayField('tags') && getArrayField('tags')!.length > 0 && (
              <div style={{ marginBottom: '0.5rem', fontSize: '0.85rem' }}>
                <strong style={{ color: theme.text.primary }}>Tags:</strong>{' '}
                <span style={{ color: theme.text.secondary }}>
                  {getArrayField('tags')!.join(', ')}
                </span>
              </div>
            )}
            {getArrayField('traits') && getArrayField('traits')!.length > 0 && (
              <div style={{ marginBottom: '0.5rem', fontSize: '0.85rem' }}>
                <strong style={{ color: theme.text.primary }}>Traits:</strong>{' '}
                <span style={{ color: theme.text.secondary }}>
                  {getArrayField('traits')!.join(', ')}
                </span>
              </div>
            )}
            {getField('rôle_narratif') && (
              <div style={{ marginBottom: '0.5rem', fontSize: '0.85rem' }}>
                <strong style={{ color: theme.text.primary }}>Rôle narratif:</strong>{' '}
                <span style={{ color: theme.text.secondary }}>{getField('rôle_narratif')}</span>
              </div>
            )}
          </div>
        </>
      )}

      <div style={{ borderTop: `1px solid ${theme.border.primary}`, paddingTop: '1rem' }}>
        <h4 style={{ marginTop: 0, marginBottom: '0.75rem', fontSize: '0.9rem', color: theme.text.primary }}>
          Détails complets
        </h4>
        {renderData(data)}
      </div>
      </div>
    </div>
  )
}

