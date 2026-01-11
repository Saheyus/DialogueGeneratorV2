/**
 * Composant Dashboard avec layout 3 panneaux redimensionnables.
 */
import { useState, useEffect, useRef, useMemo, useCallback } from 'react'
import { ContextSelector } from '../context/ContextSelector'
import { GenerationPanel } from '../generation/GenerationPanel'
import { GenerationOptionsModal } from '../generation/GenerationOptionsModal'
import { EstimatedPromptPanel } from '../generation/EstimatedPromptPanel'
import { UnityDialogueEditor } from '../generation/UnityDialogueEditor'
import { ContextDetail } from '../context/ContextDetail'
import { UsageStatsModal } from '../usage/UsageStatsModal'
import { ResizablePanels, type ResizablePanelsRef } from '../shared/ResizablePanels'
import { Tabs, type Tab } from '../shared/Tabs'
import { UnityDialogueList, type UnityDialogueListRef } from '../unityDialogues/UnityDialogueList'
import { UnityDialogueDetails } from '../unityDialogues/UnityDialogueDetails'
import { GraphEditor } from '../graph/GraphEditor'
import { NodeEditorPanel } from '../graph/NodeEditorPanel'
import { KeyboardShortcutsHelp } from '../shared/KeyboardShortcutsHelp'
import { useGenerationStore } from '../../store/generationStore'
import { useGenerationActionsStore } from '../../store/generationActionsStore'
import { useContextConfigStore } from '../../store/contextConfigStore'
import { useGraphStore } from '../../store/graphStore'
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts'
import { useCommandPalette } from '../../hooks/useCommandPalette'
import type { CharacterResponse, LocationResponse, ItemResponse, SpeciesResponse, CommunityResponse, UnityDialogueMetadata } from '../../types/api'
import { theme } from '../../theme'

type ContextItem = CharacterResponse | LocationResponse | ItemResponse | SpeciesResponse | CommunityResponse

function ChevronIcon({ direction }: { direction: 'left' | 'right' }) {
  const isLeft = direction === 'left'
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
      focusable="false"
      style={{ display: 'block', transition: 'transform 0.2s ease' }}
    >
      <path
        d={isLeft ? 'M15 18l-6-6 6-6' : 'M9 18l6-6-6-6'}
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export function Dashboard() {
  const [selectedContextItem, setSelectedContextItem] = useState<ContextItem | null>(null)
  const [isOptionsModalOpen, setIsOptionsModalOpen] = useState(false)
  const [isUsageModalOpen, setIsUsageModalOpen] = useState(false)
  const [isHelpModalOpen, setIsHelpModalOpen] = useState(false)
  const [rightPanelTab, setRightPanelTab] = useState<'prompt' | 'dialogue' | 'node' | 'details'>('prompt')
  const [centerPanelTab, setCenterPanelTab] = useState<'generation' | 'edition' | 'graph'>('generation')
  const [selectedDialogue, setSelectedDialogue] = useState<UnityDialogueMetadata | null>(null)
  const dialogueListRef = useRef<UnityDialogueListRef>(null)
  const { rawPrompt, tokenCount, promptHash, isEstimating, unityDialogueResponse } = useGenerationStore()
  const generationState = useGenerationStore((state) => ({
    isEstimating: state.isEstimating,
    unityDialogueResponse: state.unityDialogueResponse,
  }))
  const { actions } = useGenerationActionsStore()

  const { loadDefaultConfig } = useContextConfigStore()
  const commandPalette = useCommandPalette()
  
  // État du graphe pour détecter si un nœud est sélectionné
  const { selectedNodeId } = useGraphStore()

  // Boutons replier/déplier panneaux gauche & droite (layout 3 panneaux)
  const panelsRef = useRef<ResizablePanelsRef>(null)
  const expandedSizesRef = useRef<number[] | null>(null)
  const suppressSizesSyncRef = useRef(false)
  const [isLeftPanelCollapsed, setIsLeftPanelCollapsed] = useState(false)
  const [isRightPanelCollapsed, setIsRightPanelCollapsed] = useState(false)
  
  // Charger la configuration par défaut au démarrage pour initialiser les fieldConfigs
  // Cela garantit que tous les navigateurs ont la même configuration initiale
  useEffect(() => {
    loadDefaultConfig().catch((err) => {
      console.warn('Erreur lors du chargement de la config par défaut au démarrage:', err)
    })
  }, [loadDefaultConfig])

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
      label: 'Prompt',
      content: (
        <div style={{ flex: 1, minHeight: 0, maxHeight: '100%', overflow: 'hidden', display: 'flex', flexDirection: 'column', height: '100%' }}>
          <EstimatedPromptPanel
            raw_prompt={rawPrompt}
            isEstimating={isEstimating}
            tokenCount={tokenCount}
            promptHash={promptHash}
          />
        </div>
      ),
    },

    {
      id: 'dialogue',
      label: 'Dialogue généré',
      content: (
        <div style={{ flex: 1, minHeight: 0, maxHeight: '100%', overflow: 'hidden', display: 'flex', flexDirection: 'column', height: '100%' }}>
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
      id: 'node',
      label: selectedNodeId ? `Édition de nœud (${selectedNodeId})` : 'Édition de nœud',
      content: (
        <div style={{ 
          flex: 1, 
          minHeight: 0, 
          maxHeight: '100%', 
          overflow: 'hidden', 
          display: 'flex', 
          flexDirection: 'column', 
          height: '100%',
          padding: '1rem',
          overflowY: 'auto',
        }}>
          <NodeEditorPanel />
        </div>
      ),
    },
    {
      id: 'details',
      label: 'Détails',
      content: (
        <div style={{ flex: 1, minHeight: 0, maxHeight: '100%', overflow: 'hidden', display: 'flex', flexDirection: 'column', height: '100%' }}>
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
  ], [unityDialogueResponse, rawPrompt, isEstimating, tokenCount, promptHash, selectedContextItem, selectedNodeId])
  
  // Basculer automatiquement vers l'onglet "Édition de nœud" quand un nœud est sélectionné dans le graphe
  useEffect(() => {
    if (selectedNodeId && centerPanelTab === 'graph' && rightPanelTab !== 'node') {
      setRightPanelTab('node')
    }
  }, [selectedNodeId, centerPanelTab, rightPanelTab])

  const applyCollapsedLayout = useCallback(
    (nextLeftCollapsed: boolean, nextRightCollapsed: boolean) => {
      const base = expandedSizesRef.current ?? panelsRef.current?.getSizes()
      if (!base || base.length < 3 || !panelsRef.current) return

      // 0% = panneau réellement replié (bouton sur la barre de séparation)
      const COLLAPSED_PCT = 0
      const leftSize = nextLeftCollapsed ? COLLAPSED_PCT : base[0]
      const rightSize = nextRightCollapsed ? COLLAPSED_PCT : base[2]
      const centerSize = Math.max(0, 100 - leftSize - rightSize)

      suppressSizesSyncRef.current = true
      panelsRef.current.setSizes([leftSize, centerSize, rightSize], { persist: false })
      // libère le verrou après le tick pour éviter d'écraser expandedSizesRef
      setTimeout(() => {
        suppressSizesSyncRef.current = false
      }, 0)
    },
    []
  )

  const toggleLeftPanel = useCallback(() => {
    const next = !isLeftPanelCollapsed
    if (!expandedSizesRef.current && panelsRef.current) {
      expandedSizesRef.current = panelsRef.current.getSizes()
    }
    setIsLeftPanelCollapsed(next)
    applyCollapsedLayout(next, isRightPanelCollapsed)
  }, [applyCollapsedLayout, isLeftPanelCollapsed, isRightPanelCollapsed])

  const toggleRightPanel = useCallback(() => {
    const next = !isRightPanelCollapsed
    if (!expandedSizesRef.current && panelsRef.current) {
      expandedSizesRef.current = panelsRef.current.getSizes()
    }
    setIsRightPanelCollapsed(next)
    applyCollapsedLayout(isLeftPanelCollapsed, next)
  }, [applyCollapsedLayout, isLeftPanelCollapsed, isRightPanelCollapsed])

  const applyToggleHover = useCallback(
    (el: HTMLButtonElement, isHover: boolean) => {
      el.style.backgroundColor = isHover ? 'rgba(60, 60, 60, 0.95)' : 'rgba(45, 45, 45, 0.85)'
      el.style.borderColor = isHover ? theme.button.primary.background : 'rgba(255, 255, 255, 0.1)'
      el.style.transform = isHover ? 'translateY(-50%) scale(1.1)' : 'translateY(-50%) scale(1)'
      el.style.boxShadow = isHover 
        ? `0 0 20px ${theme.button.primary.background}44, 0 8px 16px rgba(0, 0, 0, 0.5)` 
        : '0 4px 12px rgba(0, 0, 0, 0.4)'
      el.style.color = isHover ? '#fff' : theme.text.primary
    },
    []
  )

  const applyHeaderToggleHover = useCallback(
    (el: HTMLButtonElement, isHover: boolean) => {
      el.style.backgroundColor = isHover ? 'rgba(255, 255, 255, 0.08)' : 'transparent'
      el.style.borderColor = isHover ? 'rgba(255, 255, 255, 0.2)' : 'rgba(255, 255, 255, 0.1)'
      el.style.transform = isHover ? 'scale(1.05)' : 'scale(1)'
      el.style.color = isHover ? '#fff' : theme.text.secondary
    },
    []
  )


  return (
    <ResizablePanels
      ref={panelsRef}
      storageKey="dashboard_panels"
      defaultSizes={[20, 50, 30]}
      minSizes={[200, 400, 250]}
      direction="horizontal"
      style={{
        height: '100%',
        backgroundColor: theme.background.primary,
      }}
      onSizesChange={(sizes) => {
        if (suppressSizesSyncRef.current) return
        // On mémorise uniquement quand les deux panneaux sont dépliés
        if (!isLeftPanelCollapsed && !isRightPanelCollapsed) {
          expandedSizesRef.current = sizes
        }
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
        {!isLeftPanelCollapsed && (
          <>
            <div
              style={{
                padding: '0.5rem 0.75rem',
                borderBottom: `1px solid ${theme.border.primary}`,
                backgroundColor: theme.background.panelHeader,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '0.5rem',
                flexShrink: 0,
              }}
            >
              <div style={{ fontSize: '0.9rem', fontWeight: 700, color: theme.text.primary }}>
                Contexte
              </div>
              <button
                onClick={toggleLeftPanel}
                onMouseDown={(e) => {
                  e.currentTarget.style.transform = 'scale(0.92)'
                }}
                onMouseUp={(e) => {
                  e.currentTarget.style.transform = 'scale(1.05)'
                }}
                title="Replier le panneau gauche"
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: 6,
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  backgroundColor: 'transparent',
                  color: theme.text.secondary,
                  cursor: 'pointer',
                  display: 'grid',
                  placeItems: 'center',
                  transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                }}
                onMouseEnter={(e) => applyHeaderToggleHover(e.currentTarget, true)}
                onMouseLeave={(e) => applyHeaderToggleHover(e.currentTarget, false)}
                aria-label="Replier le panneau gauche"
              >
                <ChevronIcon direction="left" />
              </button>
            </div>
            <ContextSelector 
              onItemSelected={(item) => {
                setSelectedContextItem(item)
                if (item) {
                  setRightPanelTab('details')
                }
              }}
            />
          </>
        )}
      </div>

      {/* Panneau central: Génération / Édition avec onglets */}
      <div
        style={{
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: theme.background.panel,
          height: '100%',
          position: 'relative',
        }}
      >
        {/* Rails (boutons) visibles quand un panneau latéral est replié */}
        {isLeftPanelCollapsed && (
          <button
            onClick={toggleLeftPanel}
            onMouseDown={(e) => {
              e.currentTarget.style.transform = 'translateY(-50%) scale(0.95)'
            }}
            onMouseUp={(e) => {
              e.currentTarget.style.transform = 'translateY(-50%) scale(1.1)'
            }}
            title="Déplier le panneau gauche"
            style={{
              position: 'absolute',
              left: 8,
              top: '50%',
              transform: 'translateY(-50%)',
              zIndex: 50,
              width: 24,
              height: 48,
              borderRadius: 12,
              border: '1px solid rgba(255, 255, 255, 0.1)',
              backgroundColor: 'rgba(45, 45, 45, 0.85)',
              backdropFilter: 'blur(8px)',
              WebkitBackdropFilter: 'blur(8px)',
              color: theme.text.primary,
              cursor: 'pointer',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.4)',
              transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
              display: 'grid',
              placeItems: 'center',
            }}
            onMouseEnter={(e) => applyToggleHover(e.currentTarget, true)}
            onMouseLeave={(e) => applyToggleHover(e.currentTarget, false)}
            aria-label="Déplier le panneau gauche"
          >
            <ChevronIcon direction="right" />
          </button>
        )}
        {isRightPanelCollapsed && (
          <button
            onClick={toggleRightPanel}
            onMouseDown={(e) => {
              e.currentTarget.style.transform = 'translateY(-50%) scale(0.95)'
            }}
            onMouseUp={(e) => {
              e.currentTarget.style.transform = 'translateY(-50%) scale(1.1)'
            }}
            title="Déplier le panneau droit"
            style={{
              position: 'absolute',
              right: 8,
              top: '50%',
              transform: 'translateY(-50%)',
              zIndex: 50,
              width: 24,
              height: 48,
              borderRadius: 12,
              border: '1px solid rgba(255, 255, 255, 0.1)',
              backgroundColor: 'rgba(45, 45, 45, 0.85)',
              backdropFilter: 'blur(8px)',
              WebkitBackdropFilter: 'blur(8px)',
              color: theme.text.primary,
              cursor: 'pointer',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.4)',
              transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
              display: 'grid',
              placeItems: 'center',
            }}
            onMouseEnter={(e) => applyToggleHover(e.currentTarget, true)}
            onMouseLeave={(e) => applyToggleHover(e.currentTarget, false)}
            aria-label="Déplier le panneau droit"
          >
            <ChevronIcon direction="left" />
          </button>
        )}
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
                          // onClose() gère déjà la fermeture (setSelectedDialogue(null))
                          // On ne fait que rafraîchir la liste pour retirer le dialogue supprimé
                          if (dialogueListRef.current) {
                            console.log('[Dashboard] Rafraîchissement de la liste des dialogues')
                            dialogueListRef.current.refresh()
                          } else {
                            console.error('[Dashboard] dialogueListRef.current est null, impossible de rafraîchir')
                          }
                        }}
                        onGenerateContinuation={() => {
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
            {
              id: 'graph',
              label: '📊 Éditeur de Graphe',
              content: (
                <GraphEditor />
              ),
            },
          ]}
          activeTabId={centerPanelTab}
          onTabChange={(tabId) => setCenterPanelTab(tabId as 'generation' | 'edition' | 'graph')}
          style={{ flex: 1, minHeight: 0, overflow: 'hidden' }}
          contentStyle={centerPanelTab === 'graph' ? { overflow: 'hidden', height: '100%', display: 'flex', flexDirection: 'column' } : undefined}
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
          position: 'relative',
        }}
      >
        {isRightPanelCollapsed ? (
          <div style={{ flex: 1, minHeight: 0 }} />
        ) : (
          <>
        <div
          style={{
            padding: '0.5rem 0.75rem',
            borderBottom: `1px solid ${theme.border.primary}`,
            backgroundColor: theme.background.panelHeader,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '0.5rem',
            flexShrink: 0,
          }}
        >
          <div style={{ fontSize: '0.9rem', fontWeight: 700, color: theme.text.primary }}>
            Détails
          </div>
          <button
            onClick={toggleRightPanel}
            onMouseDown={(e) => {
              e.currentTarget.style.transform = 'scale(0.92)'
            }}
            onMouseUp={(e) => {
              e.currentTarget.style.transform = 'scale(1.05)'
            }}
            title="Replier le panneau droit"
            style={{
              width: 28,
              height: 28,
              borderRadius: 6,
              border: '1px solid rgba(255, 255, 255, 0.1)',
              backgroundColor: 'transparent',
              color: theme.text.secondary,
              cursor: 'pointer',
              display: 'grid',
              placeItems: 'center',
              transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
            }}
            onMouseEnter={(e) => applyHeaderToggleHover(e.currentTarget, true)}
            onMouseLeave={(e) => applyHeaderToggleHover(e.currentTarget, false)}
            aria-label="Replier le panneau droit"
          >
            <ChevronIcon direction="right" />
          </button>
        </div>
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
            <div
              style={{
                position: 'relative',
                display: 'inline-block',
              }}
            >
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  if (actions.handleReset) {
                    actions.handleReset()
                  }
                }}
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
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.25rem',
                }}
                title="Réinitialiser (menu déroulant)"
              >
                Reset
                <span style={{ fontSize: '0.7rem' }}>▼</span>
              </button>
            </div>
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
            onTabChange={(tabId) => setRightPanelTab(tabId as 'prompt' | 'dialogue' | 'node' | 'details')}
            style={{ flex: 1, minHeight: 0, overflow: 'hidden' }}
            // Important: overflow: 'hidden' pour éviter le double scroll, mais scrollbar-gutter réserve l'espace
            // Le contenu enfant gère son propre scroll avec scrollbar-gutter: stable
            contentStyle={{ overflow: 'hidden', scrollbarGutter: 'stable' }}
          />
        </div>
        {/* Gros bouton Générer en bas (visible sur Prompt et Dialogue généré) */}
        {actions.handleGenerate && (rightPanelTab === 'prompt' || rightPanelTab === 'dialogue') && (
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
            {(actions.isLoading || generationState.isEstimating) && (
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
                <div
                  style={{
                    fontSize: '0.85rem',
                    color: theme.text.secondary,
                    textAlign: 'center',
                    marginBottom: '0.5rem',
                  }}
                >
                  {generationState.isEstimating && !actions.isLoading
                    ? 'Estimation des tokens...'
                    : actions.isLoading && !generationState.unityDialogueResponse
                    ? 'Génération du dialogue...'
                    : actions.isLoading
                    ? 'Validation et finalisation...'
                    : 'Traitement en cours...'}
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
          </>
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

