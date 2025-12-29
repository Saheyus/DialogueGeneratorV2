/**
 * Composant pour afficher une liste d'éléments de contexte (personnages, lieux, objets).
 */
import { useState } from 'react'
import type { CharacterResponse, LocationResponse, ItemResponse, ElementMode } from '../../types/api'
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
  getElementMode?: (name: string) => ElementMode | null
  onModeChange?: (name: string, mode: ElementMode) => void
}

export function ContextList({
  items,
  selectedItems,
  onItemClick,
  onItemToggle,
  selectedDetail,
  onSelectDetail: _onSelectDetail, // eslint-disable-line @typescript-eslint/no-unused-vars
  isLoading = false,
  getElementMode,
  onModeChange,
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
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0 }}>
      <div style={{ flexShrink: 0, padding: '0.5rem', borderBottom: `1px solid ${theme.border.primary}` }}>
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
      <div style={{ flex: 1, overflowY: 'auto', padding: '0.5rem', minHeight: 0 }}>
        {filteredItems.length === 0 ? (
          <div style={{ padding: '1rem', textAlign: 'center', color: theme.text.secondary }}>
            {searchQuery ? 'Aucun résultat' : 'Aucun élément'}
          </div>
        ) : (
          filteredItems.map((item) => {
            const isSelected = selectedItems.includes(item.name)
            const isDetailSelected = selectedDetail === item.name
            const currentMode = getElementMode ? getElementMode(item.name) : null

            const handleModeClick = (e: React.MouseEvent) => {
              e.stopPropagation()
              if (onModeChange && isSelected && currentMode) {
                const newMode: ElementMode = currentMode === 'full' ? 'excerpt' : 'full'
                onModeChange(item.name, newMode)
              }
            }

            return (
              <div
                key={item.name}
                style={{
                  padding: '0.75rem',
                  marginBottom: '0.5rem',
                  border: isSelected 
                    ? `2px solid ${currentMode === 'excerpt' ? theme.state.warning.border || theme.border.primary : theme.button.primary.background}` 
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
                {isSelected && currentMode && onModeChange && (
                  <button
                    type="button"
                    onClick={handleModeClick}
                    title={currentMode === 'full' ? 'Complet - Cliquer pour passer en Extrait' : 'Extrait - Cliquer pour passer en Complet'}
                    style={{
                      padding: '0.25rem 0.5rem',
                      border: `1px solid ${currentMode === 'excerpt' ? theme.state.warning.border || theme.border.primary : theme.border.primary}`,
                      borderRadius: '4px',
                      backgroundColor: currentMode === 'excerpt' 
                        ? theme.state.warning.background || theme.background.secondary
                        : theme.background.secondary,
                      color: currentMode === 'excerpt' 
                        ? theme.state.warning.color || theme.text.secondary
                        : theme.text.secondary,
                      cursor: 'pointer',
                      fontSize: '0.75rem',
                      fontWeight: 'bold',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.25rem',
                      minWidth: '60px',
                      justifyContent: 'center',
                    }}
                  >
                    {currentMode === 'full' ? '📄' : '✂️'}
                    <span style={{ fontSize: '0.7rem' }}>
                      {currentMode === 'full' ? 'Complet' : 'Extrait'}
                    </span>
                  </button>
                )}
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}

