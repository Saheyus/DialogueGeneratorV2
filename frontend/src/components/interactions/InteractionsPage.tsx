/**
 * Page dédiée pour la gestion des interactions.
 */
import { useState } from 'react'
import { InteractionList } from './InteractionList'
import { InteractionDetails } from './InteractionDetails'
import { theme } from '../../theme'
import type { InteractionResponse } from '../../types/api'

export function InteractionsPage() {
  const [selectedInteraction, setSelectedInteraction] = useState<InteractionResponse | null>(null)

  return (
    <div style={{ display: 'flex', height: '100%' }}>
      <div style={{ 
        width: '400px', 
        borderRight: `1px solid ${theme.border.primary}`, 
        overflow: 'hidden',
        backgroundColor: theme.background.panel,
      }}>
        <InteractionList
          onSelectInteraction={setSelectedInteraction}
          selectedInteractionId={selectedInteraction?.interaction_id || null}
        />
      </div>
      <div style={{ flex: 1, overflow: 'hidden', backgroundColor: theme.background.panel }}>
        {selectedInteraction ? (
          <InteractionDetails
            interactionId={selectedInteraction.interaction_id}
            onClose={() => setSelectedInteraction(null)}
          />
        ) : (
          <div style={{ padding: '2rem', textAlign: 'center', color: theme.text.secondary }}>
            Sélectionnez une interaction pour voir ses détails
          </div>
        )}
      </div>
    </div>
  )
}

