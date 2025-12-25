/**
 * Onglet Interactions intégré dans le panneau de génération.
 */
import { memo, useState, useCallback } from 'react'
import * as interactionsAPI from '../../api/interactions'
import { InteractionSequence } from './InteractionSequence'
import { InteractionEditor } from './InteractionEditor'
import { theme } from '../../theme'
import type { InteractionResponse } from '../../types/api'

export interface InteractionsTabProps {
  onSelectInteraction?: (interaction: InteractionResponse | null) => void
}

export const InteractionsTab = memo(function InteractionsTab({
  onSelectInteraction,
}: InteractionsTabProps) {
  const [selectedInteractionId, setSelectedInteractionId] = useState<string | null>(null)
  const [selectedInteraction, setSelectedInteraction] = useState<InteractionResponse | null>(null)

  const handleSelectInteraction = useCallback(
    async (interaction: InteractionResponse | null) => {
      setSelectedInteractionId(interaction?.interaction_id || null)
      if (interaction) {
        try {
          const fullInteraction = await interactionsAPI.getInteraction(interaction.interaction_id)
          setSelectedInteraction(fullInteraction)
        } catch (err) {
          console.error('Erreur lors du chargement de l\'interaction:', err)
          setSelectedInteraction(interaction)
        }
      } else {
        setSelectedInteraction(null)
      }
      onSelectInteraction?.(interaction)
    },
    [onSelectInteraction]
  )

  const handleSave = useCallback(
    async (updatedInteraction: InteractionResponse) => {
      setSelectedInteraction(updatedInteraction)
      // Optionnel: rafraîchir la liste
    },
    []
  )

  return (
    <div style={{ display: 'flex', height: '100%', gap: '1rem' }}>
      <div style={{ flex: '0 0 300px', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <InteractionSequence
          onSelectInteraction={handleSelectInteraction}
          selectedInteractionId={selectedInteractionId}
        />
      </div>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {selectedInteraction ? (
          <InteractionEditor interaction={selectedInteraction} onSave={handleSave} />
        ) : (
          <div style={{ padding: '2rem', textAlign: 'center', color: theme.text.secondary }}>
            Sélectionnez une interaction pour la modifier
          </div>
        )}
      </div>
    </div>
  )
})

