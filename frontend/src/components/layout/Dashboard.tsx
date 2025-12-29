/**
 * Composant Dashboard avec layout 3 panneaux redimensionnables.
 */
import { useState, useEffect, useRef, useMemo } from 'react'
import { ContextSelector } from '../context/ContextSelector'
import { GenerationPanel } from '../generation/GenerationPanel'
import { GenerationOptionsModal } from '../generation/GenerationOptionsModal'
import { EstimatedPromptPanel } from '../generation/EstimatedPromptPanel'
import { UnityDialogueEditor } from '../generation/UnityDialogueEditor'
import { ContextDetail } from '../context/ContextDetail'
import { UsageStatsModal } from '../usage/UsageStatsModal'
import { ResizablePanels } from '../shared/ResizablePanels'
import { Tabs, type Tab } from '../shared/Tabs'
import { UnityDialogueList, type UnityDialogueListRef } from '../unityDialogues/UnityDialogueList'
import { UnityDialogueDetails } from '../unityDialogues/UnityDialogueDetails'
import { KeyboardShortcutsHelp } from '../shared/KeyboardShortcutsHelp'
import { CommandPalette } from '../shared/CommandPalette'
import { useGenerationStore } from '../../store/generationStore'
import { useGenerationActionsStore } from '../../store/generationActionsStore'
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts'
import { useCommandPalette } from '../../hooks/useCommandPalette'
import type { CharacterResponse, LocationResponse, ItemResponse, SpeciesResponse, CommunityResponse, UnityDialogueMetadata } from '../../types/api'
import { theme } from '../../theme'

type ContextItem = CharacterResponse | LocationResponse | ItemResponse | SpeciesResponse | CommunityResponse

export function Dashboard() {
  const [selectedContextItem, setSelectedContextItem] = useState<ContextItem | null>(null)
  const [isOptionsModalOpen, setIsOptionsModalOpen] = useState(false)
  const [isUsageModalOpen, setIsUsageModalOpen] = useState(false)
  const [isHelpModalOpen, setIsHelpModalOpen] = useState(false)
  const [rightPanelTab, setRightPanelTab] = useState<'prompt' | 'dialogue' | 'details'>('prompt')
  const [centerPanelTab, setCenterPanelTab] = useState<'generation' | 'edition'>('generation')
  const [selectedDialogue, setSelectedDialogue] = useState<UnityDialogueMetadata | null>(null)
  const dialogueListRef = useRef<UnityDialogueListRef>(null)
  const { estimatedPrompt, estimatedTokens, isEstimating, unityDialogueResponse } = useGenerationStore()
  const { actions } = useGenerationActionsStore()
  const commandPalette = useCommandPalette()

  // Raccourcis clavier
  useKeyboardShortcuts(
    [
      {
        key: 'ctrl+k',
        handler: () => {
          commandPalette.open()
        },
        description: 'Ouvrir la palette de commandes',
      },
      {
        key: '/',
        handler: () => {
          commandPalette.open()
        },
        description: 'Ouvrir la palette de commandes',
      },
      {
        key: 'ctrl+,',
        handler: () => {
          setIsOptionsModalOpen(true)
        },
        description: 'Ouvrir les options',
      },
      {
        key: 'ctrl+/',
        handler: () => {
          setIsHelpModalOpen(true)
        },
        description: 'Afficher l\'aide des raccourcis',
      },
      {
        key: 'escape',
        handler: () => {
          if (isOptionsModalOpen) {
            setIsOptionsModalOpen(false)
          } else if (isUsageModalOpen) {
            setIsUsageModalOpen(false)
          } else if (isHelpModalOpen) {
            setIsHelpModalOpen(false)
          }
        },
        description: 'Fermer les modals/panels',
        enabled: isOptionsModalOpen || isUsageModalOpen || isHelpModalOpen,
      },
    ],
    [isOptionsModalOpen, isUsageModalOpen, isHelpModalOpen]
  )
  
  // Ref pour suivre l'ID du dernier dialogue pour lequel on a fait le basculement automatique
  const lastAutoSwitchedDialogueRef = useRef<string | null>(null)
  
  // Basculer automatiquement vers l'onglet Dialogue quand un NOUVEAU dialogue Unity est généré
  // (seulement lors de la création, pas à chaque changement d'onglet manuel)
  useEffect(() => {
    if (unityDialogueResponse) {
      // Créer un ID unique pour ce dialogue (basé sur le titre ou le contenu)
      const dialogueId = unityDialogueResponse.title || 
        (unityDialogueResponse.json_content ? 
          JSON.stringify(unityDialogueResponse.json_content).slice(0, 100) : 
          'unknown')
      
      // Basculer seulement si c'est un nouveau dialogue (pas encore traité)
      if (lastAutoSwitchedDialogueRef.current !== dialogueId) {
        setRightPanelTab('dialogue')
        lastAutoSwitchedDialogueRef.current = dialogueId
      }
    } else {
      // Si le dialogue est supprimé, réinitialiser la ref
      lastAutoSwitchedDialogueRef.current = null
    }
    // Ne pas inclure rightPanelTab dans les dépendances pour éviter les basculements
    // lors des changements manuels d'onglet
  }, [unityDialogueResponse])

  const rightPanelTabs: Tab[] = useMemo(() => [
    {
      id: 'prompt',
      label: 'Prompt Estimé',
      content: (
        <EstimatedPromptPanel
          estimatedPrompt={estimatedPrompt}
          isEstimating={isEstimating}
          estimatedTokens={estimatedTokens}
        />
      ),
    },
    {
      id: 'dialogue',
      label: 'Dialogue Unity',
      content: (
        <div style={{ flex: 1, minHeight: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          {unityDialogueResponse ? (
            <UnityDialogueEditor
              json_content={unityDialogueResponse.json_content}
              title={unityDialogueResponse.title}
              onSave={() => {
                // Rafraîchir la liste des dialogues après sauvegarde
                dialogueListRef.current?.refresh()
              }}
            />
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
              Aucun dialogue Unity généré
            </div>
          )}
        </div>
      ),
    },
    {
      id: 'details',
      label: 'Détails',
      content: (
        <div style={{ flex: 1, minHeight: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          {selectedContextItem ? (
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
              Sélectionnez un élément de contexte pour voir ses détails
            </div>
          )}
        </div>
      ),
    },
  ], [unityDialogueResponse, estimatedPrompt, isEstimating, estimatedTokens, selectedContextItem])

  return (
    <ResizablePanels
      storageKey="dashboard_panels"
      defaultSizes={[20, 50, 30]}
      minSizes={[200, 400, 250]}
      direction="horizontal"
      style={{
        height: '100%',
        backgroundColor: theme.background.primary,
      }}
    >
      {/* Panneau gauche: Sélection du contexte */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: theme.background.panel,
          height: '100%',
          minHeight: 0,
          position: 'relative',
        }}
      >
        <ContextSelector 
          onItemSelected={(item) => {
            setSelectedContextItem(item)
            if (item) {
              setRightPanelTab('details')
            }
          }}
        />
      </div>

      {/* Panneau central: Génération / Édition avec onglets */}
      <div
        style={{
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: theme.background.panel,
          height: '100%',
        }}
      >
        <Tabs
          tabs={[
            {
              id: 'generation',
              label: 'Génération de Dialogues',
              content: (
                <div style={{ flex: 1, minHeight: 0, overflow: 'hidden' }}>
                  <GenerationPanel />
                </div>
              ),
            },
            {
              id: 'edition',
              label: 'Édition de Dialogues',
              content: (
                <div style={{ display: 'flex', height: '100%', overflow: 'hidden' }}>
                  <div
                    style={{
                      // Panneau gauche (recherche/liste) volontairement compact pour donner de la place à l'édition
                      width: 'clamp(260px, 22vw, 340px)',
                      minWidth: '240px',
                      borderRight: `1px solid ${theme.border.primary}`,
                      overflow: 'hidden',
                      backgroundColor: theme.background.panel,
                    }}
                  >
                    <UnityDialogueList
                      ref={dialogueListRef}
                      onSelectDialogue={setSelectedDialogue}
                      selectedFilename={selectedDialogue?.filename || null}
                    />
                  </div>
                  <div style={{ flex: 1, overflow: 'hidden', backgroundColor: theme.background.panel }}>
                    {selectedDialogue ? (
                      <UnityDialogueDetails
                        filename={selectedDialogue.filename}
                        onClose={() => setSelectedDialogue(null)}
                        onDeleted={() => {
                          setSelectedDialogue(null)
                          // Rafraîchir la liste après suppression
                          dialogueListRef.current?.refresh()
                        }}
                        onGenerateContinuation={(dialogueJson, dialogueTitle) => {
                          // Basculer vers l'onglet Génération
                          setCenterPanelTab('generation')
                          // TODO: Pré-remplir le contexte avec le dialogue existant pour générer la suite
                          // Pour l'instant, on bascule juste vers l'onglet génération
                        }}
                      />
                    ) : (
                      <div style={{ padding: '2rem', textAlign: 'center', color: theme.text.secondary }}>
                        Sélectionnez un dialogue Unity pour le voir et l'éditer
                      </div>
                    )}
                  </div>
                </div>
              ),
            },
          ]}
          activeTabId={centerPanelTab}
          onTabChange={(tabId) => setCenterPanelTab(tabId as 'generation' | 'edition')}
          style={{ flex: 1, minHeight: 0, overflow: 'hidden' }}
        />
      </div>

      {/* Panneau droit: Prompt Estimé / Détails */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: theme.background.panel,
          height: '100%',
          minHeight: 0,
          maxHeight: '100%',
          overflow: 'hidden',
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
              flexShrink: 0,
              boxSizing: 'border-box',
            }}
          >
            <button
              onClick={() => setIsOptionsModalOpen(true)}
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
              Options
            </button>
            <button
              onClick={() => setIsUsageModalOpen(true)}
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
              Usage IA
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
        {/* Zone de contenu avec scroll (prend l'espace restant, mais laisse toujours de la place pour le bouton) */}
        <div
          style={{
            flex: 1,
            minHeight: 0,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            position: 'relative',
          }}
        >
          <Tabs
            tabs={rightPanelTabs}
            activeTabId={rightPanelTab}
            onTabChange={(tabId) => setRightPanelTab(tabId as 'prompt' | 'variants' | 'details')}
            style={{ flex: 1, minHeight: 0, overflow: 'hidden' }}
          />
        </div>
        {/* Gros bouton Générer en bas (visible sur Prompt et Variantes) */}
        {actions.handleGenerate && (rightPanelTab === 'prompt' || rightPanelTab === 'variants') && (
          <div
            style={{
              padding: '0.75rem 1rem',
              borderTop: `2px solid ${theme.border.primary}`,
              backgroundColor: theme.background.panelHeader,
              flexShrink: 0,
              flexGrow: 0,
              boxSizing: 'border-box',
              position: 'relative',
              zIndex: 10,
            }}
          >
            {/* Barre de progression */}
            {actions.isLoading && (
              <>
                <div
                  style={{
                    width: '100%',
                    height: '4px',
                    backgroundColor: theme.border.primary,
                    borderRadius: '2px',
                    overflow: 'hidden',
                    marginBottom: '0.75rem',
                    position: 'relative',
                  }}
                >
                  <div
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      height: '100%',
                      width: '40%',
                      backgroundColor: theme.button.primary.background,
                      animation: 'loading-slide 1.5s ease-in-out infinite',
                    }}
                  />
                </div>
                <style>{`
                  @keyframes loading-slide {
                    0% {
                      left: -40%;
                    }
                    100% {
                      left: 100%;
                    }
                  }
                `}</style>
              </>
            )}
            <button
              onClick={actions.handleGenerate}
              disabled={actions.isLoading}
              style={{
                width: '100%',
                padding: '0.875rem 1rem',
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
                boxSizing: 'border-box',
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

      <GenerationOptionsModal
        isOpen={isOptionsModalOpen}
        onClose={() => setIsOptionsModalOpen(false)}
      />
      <UsageStatsModal
        isOpen={isUsageModalOpen}
        onClose={() => setIsUsageModalOpen(false)}
      />
      <KeyboardShortcutsHelp
        isOpen={isHelpModalOpen}
        onClose={() => setIsHelpModalOpen(false)}
      />
    </ResizablePanels>
  )
}

