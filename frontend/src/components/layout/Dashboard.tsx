/**
 * Composant Dashboard avec layout 3 panneaux.
 */
import { useState } from 'react'
import { ContextSelector } from '../context/ContextSelector'
import { GenerationPanel } from '../generation/GenerationPanel'
import { InteractionList } from '../interactions/InteractionList'
import { InteractionDetails } from '../interactions/InteractionDetails'
import { UnityConfigDialog } from '../config/UnityConfigDialog'
import type { InteractionResponse } from '../../types/api'
import { theme } from '../../theme'

export function Dashboard() {
  const [selectedInteraction, setSelectedInteraction] = useState<InteractionResponse | null>(null)
  const [isUnityConfigOpen, setIsUnityConfigOpen] = useState(false)

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '300px 1fr 400px',
        height: 'calc(100vh - 60px)', // Ajuster selon la hauteur du header
        overflow: 'hidden',
        backgroundColor: theme.background.primary,
      }}
    >
      {/* Panneau gauche: Sélection de contexte */}
      <div
        style={{
          borderRight: `1px solid ${theme.border.primary}`,
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: theme.background.panel,
        }}
      >
        <div style={{ 
          padding: '0.5rem', 
          borderBottom: `1px solid ${theme.border.primary}`, 
          backgroundColor: theme.background.panelHeader 
        }}>
          <h3 style={{ margin: 0, fontSize: '1rem', color: theme.text.primary }}>Contexte</h3>
        </div>
        <div style={{ flex: 1, overflow: 'hidden' }}>
          <ContextSelector />
        </div>
      </div>

      {/* Panneau central: Génération */}
      <div
        style={{
          borderRight: `1px solid ${theme.border.primary}`,
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: theme.background.panel,
        }}
      >
        <div style={{ 
          padding: '0.5rem', 
          borderBottom: `1px solid ${theme.border.primary}`, 
          backgroundColor: theme.background.panelHeader,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <h3 style={{ margin: 0, fontSize: '1rem', color: theme.text.primary }}>Génération</h3>
          <button
            onClick={() => setIsUnityConfigOpen(true)}
            style={{
              padding: '0.25rem 0.5rem',
              fontSize: '0.85rem',
            backgroundColor: theme.button.default.background,
            color: theme.button.default.color,
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            Config Unity
          </button>
        </div>
        <div style={{ flex: 1, overflow: 'hidden' }}>
          <GenerationPanel />
        </div>
      </div>

      {/* Panneau droit: Interactions */}
      <div
        style={{
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: theme.background.panel,
        }}
      >
        <div style={{ 
          padding: '0.5rem', 
          borderBottom: `1px solid ${theme.border.primary}`, 
          backgroundColor: theme.background.panelHeader 
        }}>
          <h3 style={{ margin: 0, fontSize: '1rem', color: theme.text.primary }}>Interactions</h3>
        </div>
        <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          {selectedInteraction ? (
            <InteractionDetails
              interactionId={selectedInteraction.interaction_id}
              onClose={() => setSelectedInteraction(null)}
            />
          ) : (
            <InteractionList
              onSelectInteraction={setSelectedInteraction}
              selectedInteractionId={null}
            />
          )}
        </div>
      </div>

      <UnityConfigDialog
        isOpen={isUnityConfigOpen}
        onClose={() => setIsUnityConfigOpen(false)}
      />
    </div>
  )
}

