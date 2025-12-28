/**
 * Composant pour afficher un résumé des sélections de contexte actives.
 */
import { memo, useState, useCallback } from 'react'
import type { ContextSelection } from '../../types/api'
import { theme } from '../../theme'
import * as contextAPI from '../../api/context'
import { useContextStore } from '../../store/contextStore'
import { useGenerationStore } from '../../store/generationStore'
import { getErrorMessage } from '../../types/errors'

interface SelectedContextSummaryProps {
  selections: ContextSelection
  onClear: () => void
  onError?: (error: string) => void
  onSuccess?: (message: string) => void
}

export const SelectedContextSummary = memo(function SelectedContextSummary({
  selections,
  onClear,
  onError,
  onSuccess,
}: SelectedContextSummaryProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const { sceneSelection } = useGenerationStore()
  const { applyLinkedElements } = useContextStore()

  const handleLinkElements = useCallback(async () => {
    try {
      const response = await contextAPI.getLinkedElements({
        character_a: sceneSelection.characterA || undefined,
        character_b: sceneSelection.characterB || undefined,
        scene_region: sceneSelection.sceneRegion || undefined,
        sub_location: sceneSelection.subLocation || undefined,
      })
      
      // Les listes sont déjà dans le store (chargées par ContextSelector)
      applyLinkedElements(response.linked_elements)
      onSuccess?.(`${response.total} éléments liés ajoutés`)
    } catch (err) {
      const errorMsg = getErrorMessage(err)
      onError?.(errorMsg)
    }
  }, [sceneSelection, applyLinkedElements, onError, onSuccess])
  
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

  const renderCategory = (
    label: string,
    items: string[],
    count: number
  ) => {
    if (count === 0) return null
    
    return (
      <div style={{ marginTop: '0.5rem' }}>
        <strong style={{ color: theme.text.primary }}>{label}:</strong> {count}
        {isExpanded && (
          <div style={{ marginLeft: '1rem', marginTop: '0.25rem' }}>
            {items.join(', ')}
          </div>
        )}
      </div>
    )
  }

  return (
    <div style={{ padding: '1rem', paddingBottom: isExpanded ? '1.5rem' : '1rem', borderTop: `1px solid ${theme.border.primary}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: 1, cursor: 'pointer' }} onClick={() => setIsExpanded(!isExpanded)}>
          <span style={{ fontSize: '0.8rem', color: theme.text.secondary, userSelect: 'none' }}>
            {isExpanded ? '▼' : '▶'}
          </span>
          <strong style={{ fontSize: '0.9rem', color: theme.text.primary }}>Sélections actives ({totalSelected})</strong>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <button
            onClick={(e) => {
              e.stopPropagation()
              handleLinkElements()
            }}
            disabled={!sceneSelection.characterA && !sceneSelection.characterB && !sceneSelection.sceneRegion}
            style={{
              padding: '0.25rem 0.5rem',
              fontSize: '0.8rem',
              border: `1px solid ${theme.border.primary}`,
              borderRadius: '4px',
              backgroundColor: theme.button.default.background,
              color: theme.button.default.color,
              cursor:
                !sceneSelection.characterA && !sceneSelection.characterB && !sceneSelection.sceneRegion
                  ? 'not-allowed'
                  : 'pointer',
              opacity:
                !sceneSelection.characterA && !sceneSelection.characterB && !sceneSelection.sceneRegion
                  ? 0.5
                  : 1,
            }}
            title="Coche automatiquement les éléments (personnages, lieux) liés aux personnages A/B et à la scène sélectionnés"
          >
            Lier Éléments Connexes
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation()
              onClear()
            }}
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
      </div>
      {isExpanded && (
        <div style={{ fontSize: '0.85rem', color: theme.text.secondary, marginTop: '0.75rem' }}>
          {renderCategory('Personnages', selections.characters, selections.characters.length)}
          {renderCategory('Lieux', selections.locations, selections.locations.length)}
          {renderCategory('Objets', selections.items, selections.items.length)}
          {renderCategory('Espèces', selections.species, selections.species.length)}
          {renderCategory('Communautés', selections.communities, selections.communities.length)}
          {renderCategory('Exemples de dialogues', selections.dialogues_examples, selections.dialogues_examples.length)}
        </div>
      )}
    </div>
  )
})

