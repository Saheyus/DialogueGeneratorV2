/**
 * Composant pour afficher une liste d'éléments de contexte (personnages, lieux, objets).
 */
import { useState } from 'react'
import type { CharacterResponse, LocationResponse, ItemResponse } from '../../types/api'
import { theme } from '../../theme'

type ContextItem = CharacterResponse | LocationResponse | ItemResponse

interface ContextListProps {
  items: ContextItem[]
  selectedItems: string[]
  onItemClick: (name: string) => void
  onItemToggle: (name: string) => void
  selectedDetail: string | null
  onSelectDetail: (name: string | null) => void
  isLoading?: boolean
}

export function ContextList({
  items,
  selectedItems,
  onItemClick,
  onItemToggle,
  selectedDetail,
  onSelectDetail: _onSelectDetail, // eslint-disable-line @typescript-eslint/no-unused-vars
  isLoading = false,
}: ContextListProps) {
  const [searchQuery, setSearchQuery] = useState('')

  const filteredItems = items.filter((item) =>
    item.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  if (isLoading) {
    return (
      <div style={{ padding: '1rem', textAlign: 'center', color: theme.text.secondary }}>
        <div>Chargement...</div>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ padding: '0.5rem', borderBottom: `1px solid ${theme.border.primary}` }}>
        <input
          type="text"
          placeholder="Rechercher..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            width: '100%',
            padding: '0.5rem',
            border: `1px solid ${theme.input.border}`,
            borderRadius: '4px',
            backgroundColor: theme.input.background,
            color: theme.input.color,
          }}
        />
      </div>
      <div style={{ flex: 1, overflowY: 'auto', padding: '0.5rem' }}>
        {filteredItems.length === 0 ? (
          <div style={{ padding: '1rem', textAlign: 'center', color: theme.text.secondary }}>
            {searchQuery ? 'Aucun résultat' : 'Aucun élément'}
          </div>
        ) : (
          filteredItems.map((item) => {
            const isSelected = selectedItems.includes(item.name)
            const isDetailSelected = selectedDetail === item.name

            return (
              <div
                key={item.name}
                style={{
                  padding: '0.75rem',
                  marginBottom: '0.5rem',
                  border: isSelected 
                    ? `2px solid ${theme.button.primary.background}` 
                    : `1px solid ${theme.border.primary}`,
                  borderRadius: '4px',
                  backgroundColor: isSelected 
                    ? theme.state.selected.background 
                    : isDetailSelected 
                      ? theme.background.tertiary 
                      : theme.background.panel,
                  color: theme.text.primary,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                }}
                onClick={() => onItemClick(item.name)}
                onMouseEnter={(e) => {
                  if (!isSelected && !isDetailSelected) {
                    e.currentTarget.style.backgroundColor = theme.state.hover.background
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isSelected && !isDetailSelected) {
                    e.currentTarget.style.backgroundColor = theme.background.panel
                  }
                }}
              >
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={(e) => {
                    e.stopPropagation()
                    onItemToggle(item.name)
                  }}
                  onClick={(e) => e.stopPropagation()}
                />
                <span style={{ flex: 1, fontWeight: isSelected ? 'bold' : 'normal' }}>
                  {item.name}
                </span>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}

