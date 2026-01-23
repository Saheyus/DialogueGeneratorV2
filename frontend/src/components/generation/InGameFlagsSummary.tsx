/**
 * Composant compact affichant un résumé des flags in-game sélectionnés.
 */
import { useState } from 'react'
import { useFlagsStore } from '../../store/flagsStore'
import { theme } from '../../theme'
import { InGameFlagsModal } from './InGameFlagsModal'

export function InGameFlagsSummary() {
  const { selectedFlags, getSelectedFlagsArray, removeFlag, catalog } = useFlagsStore()
  const [isModalOpen, setIsModalOpen] = useState(false)
  
  // Obtenir la liste des flags sélectionnés pour l'affichage
  const selectedFlagsArray = getSelectedFlagsArray()
  
  // Format de la valeur pour affichage
  const formatValue = (value: boolean | number | string): string => {
    if (typeof value === 'boolean') {
      return value ? 'true' : 'false'
    }
    return String(value)
  }
  
  // Récupérer les labels depuis le catalogue
  const getFlagLabel = (flagId: string): string => {
    const flagDef = catalog.find(f => f.id === flagId)
    return flagDef?.label || flagId
  }
  
  return (
    <>
      <div style={{ marginBottom: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
          <label style={{ color: theme.text.primary, fontWeight: 'bold' }}>
            Flags In-Game
          </label>
          <button
            onClick={() => setIsModalOpen(true)}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: theme.button.default.background,
              color: theme.button.default.color,
              border: `1px solid ${theme.border.primary}`,
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '0.9rem'
            }}
            title="Ouvrir le sélecteur de flags"
          >
            {selectedFlags.size > 0 
              ? `🔗 ${selectedFlags.size} flag${selectedFlags.size > 1 ? 's' : ''} sélectionné${selectedFlags.size > 1 ? 's' : ''}`
              : '🔗 Sélectionner des flags...'
            }
          </button>
        </div>
        
        {/* Afficher les flags sélectionnés sous forme de chips */}
        {selectedFlagsArray.length > 0 && (
          <div 
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '0.5rem',
              padding: '0.75rem',
              backgroundColor: theme.background.secondary,
              border: `1px solid ${theme.border.primary}`,
              borderRadius: '4px',
              minHeight: '3rem',
              alignItems: 'flex-start'
            }}
          >
            {selectedFlagsArray.map(flag => (
              <div
                key={flag.id}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.375rem 0.75rem',
                  backgroundColor: theme.button.primary.background,
                  color: theme.button.primary.color,
                  border: `1px solid ${theme.border.focus}`,
                  borderRadius: '4px',
                  fontSize: '0.85rem',
                  maxWidth: '100%'
                }}
              >
                <span style={{ fontWeight: 'bold' }}>
                  {getFlagLabel(flag.id)}
                </span>
                <span style={{ opacity: 0.8, fontFamily: 'monospace', fontSize: '0.75rem' }}>
                  = {formatValue(flag.value)}
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    removeFlag(flag.id)
                  }}
                  style={{
                    marginLeft: '0.25rem',
                    padding: '0 0.25rem',
                    backgroundColor: 'transparent',
                    border: 'none',
                    color: theme.button.primary.color,
                    cursor: 'pointer',
                    fontSize: '1rem',
                    lineHeight: '1',
                    opacity: 0.7
                  }}
                  title="Retirer ce flag"
                  onMouseEnter={(e) => {
                    e.currentTarget.style.opacity = '1'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.opacity = '0.7'
                  }}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}
        
        {selectedFlagsArray.length === 0 && (
          <div 
            style={{
              padding: '0.75rem',
              backgroundColor: theme.background.secondary,
              border: `1px solid ${theme.border.primary}`,
              borderRadius: '4px',
              color: theme.text.secondary,
              fontSize: '0.85rem',
              fontStyle: 'italic',
              textAlign: 'center'
            }}
          >
            Aucun flag sélectionné. Cliquez sur "Sélectionner des flags..." pour ajouter des flags in-game.
          </div>
        )}
      </div>
      
      <InGameFlagsModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
      />
    </>
  )
}
