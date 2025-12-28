/**
 * Page dédiée pour la gestion des dialogues Unity JSON.
 */
import { useState } from 'react'
import { UnityDialogueList } from './UnityDialogueList'
import { UnityDialogueDetails } from './UnityDialogueDetails'
import { theme } from '../../theme'
import type { UnityDialogueMetadata } from '../../types/api'

export function UnityDialoguesPage() {
  const [selectedDialogue, setSelectedDialogue] = useState<UnityDialogueMetadata | null>(null)

  return (
    <div style={{ display: 'flex', height: '100%' }}>
      <div
        style={{
          width: '400px',
          borderRight: `1px solid ${theme.border.primary}`,
          overflow: 'hidden',
          backgroundColor: theme.background.panel,
        }}
      >
        <UnityDialogueList
          onSelectDialogue={setSelectedDialogue}
          selectedFilename={selectedDialogue?.filename || null}
        />
      </div>
      <div style={{ flex: 1, overflow: 'hidden', backgroundColor: theme.background.panel }}>
        {selectedDialogue ? (
          <UnityDialogueDetails
            filename={selectedDialogue.filename}
            onClose={() => setSelectedDialogue(null)}
            onDeleted={() => setSelectedDialogue(null)}
          />
        ) : (
          <div style={{ padding: '2rem', textAlign: 'center', color: theme.text.secondary }}>
            Sélectionnez un dialogue Unity pour le voir et l'éditer
          </div>
        )}
      </div>
    </div>
  )
}

