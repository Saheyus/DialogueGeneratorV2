/**
 * Composant Dashboard avec layout 3 panneaux redimensionnables.
 */
import { useState } from 'react'
import { ContextSelector } from '../context/ContextSelector'
import { GenerationPanel } from '../generation/GenerationPanel'
import { InteractionDetails } from '../interactions/InteractionDetails'
import { EstimatedPromptPanel } from '../generation/EstimatedPromptPanel'
import { ContextDetail } from '../context/ContextDetail'
import { UnityConfigDialog } from '../config/UnityConfigDialog'
import { ResizablePanels } from '../shared/ResizablePanels'
import { Tabs, type Tab } from '../shared/Tabs'
import { useGenerationStore } from '../../store/generationStore'
import { useGenerationActionsStore } from '../../store/generationActionsStore'
import type { InteractionResponse, CharacterResponse, LocationResponse, ItemResponse, SpeciesResponse, CommunityResponse } from '../../types/api'
import { theme } from '../../theme'

type ContextItem = CharacterResponse | LocationResponse | ItemResponse | SpeciesResponse | CommunityResponse

export function Dashboard() {
  const [selectedInteraction, setSelectedInteraction] = useState<InteractionResponse | null>(null)
  const [selectedContextItem, setSelectedContextItem] = useState<ContextItem | null>(null)
  const [isUnityConfigOpen, setIsUnityConfigOpen] = useState(false)
  const [rightPanelTab, setRightPanelTab] = useState<'prompt' | 'details'>('prompt')
  const { estimatedPrompt, estimatedTokens, isEstimating } = useGenerationStore()
  const { actions } = useGenerationActionsStore()

  const rightPanelTabs: Tab[] = [
    {
      id: 'prompt',
      label: 'Prompt Estimé',
      content: (
        <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <EstimatedPromptPanel
            estimatedPrompt={estimatedPrompt}
            isEstimating={isEstimating}
            estimatedTokens={estimatedTokens}
          />
        </div>
      ),
    },
    {
      id: 'details',
      label: 'Détails',
      content: (
        <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          {selectedInteraction ? (
            <InteractionDetails
              interactionId={selectedInteraction.interaction_id}
              onClose={() => {
                setSelectedInteraction(null)
                setRightPanelTab('prompt')
              }}
            />
          ) : selectedContextItem ? (
            <ContextDetail item={selectedContextItem} />
          ) : (
            <div style={{ 
              padding: '2rem', 
              textAlign: 'center', 
              color: theme.text.secondary,
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              Sélectionnez un élément de contexte ou une interaction pour voir ses détails
            </div>
          )}
        </div>
      ),
    },
  ]

  return (
    <ResizablePanels
      storageKey="dashboard_panels"
      defaultSizes={[20, 50, 30]}
      minSizes={[200, 400, 250]}
      direction="horizontal"
      style={{
        height: 'calc(100vh - 60px)',
        backgroundColor: theme.background.primary,
      }}
    >
      {/* Panneau gauche: Sélection du contexte */}
      <div
        style={{
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: theme.background.panel,
          height: '100%',
        }}
      >
        <ContextSelector 
          onItemSelected={(item) => {
            setSelectedContextItem(item)
            if (item) {
              setRightPanelTab('details')
              setSelectedInteraction(null)
            }
          }}
        />
      </div>

      {/* Panneau central: Génération */}
      <div
        style={{
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: theme.background.panel,
          height: '100%',
        }}
      >
        <GenerationPanel />
      </div>

      {/* Panneau droit: Prompt Estimé / Détails */}
      <div
        style={{
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: theme.background.panel,
          height: '100%',
        }}
      >
        {/* Barre d'options en haut (toujours visible) */}
        {actions.handleGenerate && (
          <div
            style={{
              padding: '0.5rem',
              borderBottom: `1px solid ${theme.border.primary}`,
              backgroundColor: theme.background.panelHeader,
              display: 'flex',
              gap: '0.5rem',
              flexWrap: 'wrap',
              alignItems: 'center',
            }}
          >
            <button
              onClick={actions.handlePreview || (() => {})}
              disabled={actions.isLoading}
              style={{
                padding: '0.4rem 0.8rem',
                fontSize: '0.85rem',
                backgroundColor: theme.button.default.background,
                color: theme.button.default.color,
                border: `1px solid ${theme.border.primary}`,
                borderRadius: '4px',
                cursor: actions.isLoading ? 'not-allowed' : 'pointer',
                opacity: actions.isLoading ? 0.6 : 1,
              }}
            >
              Prévisualiser
            </button>
            <button
              onClick={actions.handleExportUnity || (() => {})}
              disabled={actions.isLoading}
              style={{
                padding: '0.4rem 0.8rem',
                fontSize: '0.85rem',
                backgroundColor: theme.button.default.background,
                color: theme.button.default.color,
                border: `1px solid ${theme.border.primary}`,
                borderRadius: '4px',
                cursor: actions.isLoading ? 'not-allowed' : 'pointer',
                opacity: actions.isLoading ? 0.6 : 1,
              }}
            >
              Exporter (Unity)
            </button>
            <button
              onClick={() => setIsUnityConfigOpen(true)}
              style={{
                padding: '0.4rem 0.8rem',
                fontSize: '0.85rem',
                backgroundColor: theme.button.default.background,
                color: theme.button.default.color,
                border: `1px solid ${theme.border.primary}`,
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              Config Unity
            </button>
            <button
              onClick={actions.handleReset || (() => {})}
              disabled={actions.isLoading}
              style={{
                padding: '0.4rem 0.8rem',
                fontSize: '0.85rem',
                backgroundColor: theme.button.default.background,
                color: theme.button.default.color,
                border: `1px solid ${theme.border.primary}`,
                borderRadius: '4px',
                cursor: actions.isLoading ? 'not-allowed' : 'pointer',
                opacity: actions.isLoading ? 0.6 : 1,
              }}
            >
              Reset
            </button>
            {actions.isDirty && (
              <div
                style={{
                  fontSize: '0.85rem',
                  color: theme.state.info.color,
                  fontStyle: 'italic',
                  marginLeft: 'auto',
                }}
              >
                ● Brouillon non sauvegardé
              </div>
            )}
          </div>
        )}
        <Tabs
          tabs={rightPanelTabs}
          activeTabId={rightPanelTab}
          onTabChange={(tabId) => setRightPanelTab(tabId as 'prompt' | 'details')}
        />
        {/* Gros bouton Générer en bas (uniquement pour l'onglet Prompt) */}
        {actions.handleGenerate && rightPanelTab === 'prompt' && (
          <div
            style={{
              padding: '1rem',
              borderTop: `2px solid ${theme.border.primary}`,
              backgroundColor: theme.background.panelHeader,
            }}
          >
            <button
              onClick={actions.handleGenerate}
              disabled={actions.isLoading}
              style={{
                width: '100%',
                padding: '1rem',
                fontSize: '1.1rem',
                fontWeight: 'bold',
                backgroundColor: theme.button.primary.background,
                color: theme.button.primary.color,
                border: 'none',
                borderRadius: '6px',
                cursor: actions.isLoading ? 'not-allowed' : 'pointer',
                opacity: actions.isLoading ? 0.6 : 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem',
                transition: 'all 0.2s',
              }}
              title="Générer (Ctrl+Enter)"
            >
              <span>Générer</span>
              <span
                style={{
                  fontSize: '0.75rem',
                  opacity: 0.8,
                  fontWeight: 'normal',
                }}
              >
                Ctrl+Enter
              </span>
            </button>
          </div>
        )}
      </div>

      <UnityConfigDialog
        isOpen={isUnityConfigOpen}
        onClose={() => setIsUnityConfigOpen(false)}
      />
    </ResizablePanels>
  )
}

