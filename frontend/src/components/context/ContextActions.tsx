/**
 * Composant pour les actions de contexte (Lier Éléments Connexes, Décocher tout).
 */
import { memo, useCallback } from 'react'
import * as contextAPI from '../../api/context'
import { useContextStore } from '../../store/contextStore'
import { useGenerationStore } from '../../store/generationStore'
import { getErrorMessage } from '../../types/errors'
import { theme } from '../../theme'

export interface ContextActionsProps {
  onError?: (error: string) => void
  onSuccess?: (message: string) => void
}

export const ContextActions = memo(function ContextActions({
  onError,
  onSuccess,
}: ContextActionsProps) {
  const { sceneSelection } = useGenerationStore()
  const { applyLinkedElements, clearSelections } = useContextStore()

  const handleLinkElements = useCallback(async () => {
    try {
      const response = await contextAPI.getLinkedElements({
        character_a: sceneSelection.characterA || undefined,
        character_b: sceneSelection.characterB || undefined,
        scene_region: sceneSelection.sceneRegion || undefined,
        sub_location: sceneSelection.subLocation || undefined,
      })
      
      applyLinkedElements(response.linked_elements)
      onSuccess?.(`${response.total} éléments liés ajoutés`)
    } catch (err) {
      const errorMsg = getErrorMessage(err)
      onError?.(errorMsg)
    }
  }, [sceneSelection, applyLinkedElements, onError, onSuccess])

  const handleClearAll = useCallback(() => {
    if (confirm('Êtes-vous sûr de vouloir décocher tous les éléments ?')) {
      clearSelections()
      onSuccess?.('Tous les éléments ont été décochés')
    }
  }, [clearSelections, onSuccess])

  return (
    <div
      style={{
        padding: '1rem',
        border: `1px solid ${theme.border.primary}`,
        borderRadius: '4px',
        backgroundColor: theme.background.panel,
        marginBottom: '1rem',
      }}
    >
      <h3
        style={{
          marginTop: 0,
          marginBottom: '0.75rem',
          fontSize: '1rem',
          fontWeight: 'bold',
          color: theme.text.primary,
        }}
      >
        Actions de Contexte
      </h3>
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        <button
          onClick={handleLinkElements}
          disabled={!sceneSelection.characterA && !sceneSelection.characterB && !sceneSelection.sceneRegion}
          style={{
            padding: '0.5rem 1rem',
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
            fontSize: '0.9rem',
          }}
          title="Coche automatiquement les éléments (personnages, lieux) liés aux personnages A/B et à la scène sélectionnés"
        >
          Lier Éléments Connexes
        </button>
        <button
          onClick={handleClearAll}
          style={{
            padding: '0.5rem 1rem',
            border: `1px solid ${theme.border.primary}`,
            borderRadius: '4px',
            backgroundColor: theme.button.default.background,
            color: theme.button.default.color,
            cursor: 'pointer',
            fontSize: '0.9rem',
          }}
          title="Décoche tous les éléments dans toutes les listes"
        >
          Décocher Tout
        </button>
      </div>
    </div>
  )
})

