/**
 * Éditeur de graphe narratif avec sélecteur de dialogue.
 * Structure : Liste de dialogues à gauche, graphe à droite.
 */
import { useState, useRef, useCallback, useEffect } from 'react'
import { ReactFlowProvider } from 'reactflow'
import { UnityDialogueList, type UnityDialogueListRef } from '../unityDialogues/UnityDialogueList'
import { GraphCanvas } from './GraphCanvas'
import { AIGenerationPanel } from './AIGenerationPanel'
import { GraphSearchBar } from './GraphSearchBar'
import { useGraphStore } from '../../store/graphStore'
import { exportGraphToPNG, exportGraphToSVG, exportFullGraphToPNG } from '../../utils/graphExport'
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts'
import { useToast } from '../shared'
import { theme } from '../../theme'
import * as unityDialoguesAPI from '../../api/unityDialogues'
import * as dialoguesAPI from '../../api/dialogues'
import { getErrorMessage } from '../../types/errors'
import type { UnityDialogueMetadata } from '../../types/api'

export function GraphEditor() {
  const [selectedDialogue, setSelectedDialogue] = useState<UnityDialogueMetadata | null>(null)
  const [isLoadingDialogue, setIsLoadingDialogue] = useState(false)
  const [layoutDirection, setLayoutDirection] = useState<'TB' | 'LR' | 'BT' | 'RL'>('TB')
  const [showAIGenerationPanel, setShowAIGenerationPanel] = useState(false)
  const [reactFlowInstance, setReactFlowInstance] = useState<any>(null)
  const dialogueListRef = useRef<UnityDialogueListRef>(null)
  const toast = useToast()
  
  // Écouter l'événement pour obtenir l'instance ReactFlow
  useEffect(() => {
    const handleInstanceReady = (event: CustomEvent) => {
      setReactFlowInstance(event.detail)
    }
    
    window.addEventListener('reactflow-instance-ready', handleInstanceReady as EventListener)
    return () => {
      window.removeEventListener('reactflow-instance-ready', handleInstanceReady as EventListener)
    }
  }, [])
  
  const {
    loadDialogue,
    exportToUnity,
    validateGraph,
    applyAutoLayout,
    saveDialogue,
    setSelectedNode,
    selectedNodeId,
    isLoading: isGraphLoading,
    validationErrors: graphValidationErrors,
    isSaving: isGraphSaving,
  } = useGraphStore()
  
  // Charger le dialogue sélectionné dans le graphe
  useEffect(() => {
    if (selectedDialogue) {
      setIsLoadingDialogue(true)
      unityDialoguesAPI.getUnityDialogue(selectedDialogue.filename)
        .then((response) => {
          return loadDialogue(response.json_content)
        })
        .then(() => {
          setIsLoadingDialogue(false)
        })
        .catch((err) => {
          console.error('Erreur lors du chargement du dialogue:', err)
          toast(`Erreur: ${getErrorMessage(err)}`, 'error')
          setIsLoadingDialogue(false)
        })
    } else {
      // Réinitialiser le graphe si aucun dialogue sélectionné
      useGraphStore.getState().resetGraph()
    }
  }, [selectedDialogue, loadDialogue, toast])
  
  // Handler pour valider le graphe
  const handleValidate = useCallback(async () => {
    try {
      await validateGraph()
      if (graphValidationErrors.length === 0) {
        toast('Graphe valide', 'success', 2000)
      } else {
        toast(`${graphValidationErrors.length} erreur(s) trouvée(s)`, 'warning', 3000)
      }
    } catch (err) {
      toast(`Erreur lors de la validation: ${getErrorMessage(err)}`, 'error')
    }
  }, [validateGraph, graphValidationErrors, toast])
  
  // Handler pour auto-layout
  const handleAutoLayout = useCallback(async () => {
    try {
      await applyAutoLayout('dagre', layoutDirection)
      toast('Layout appliqué', 'success', 2000)
    } catch (err) {
      toast(`Erreur lors de l'auto-layout: ${getErrorMessage(err)}`, 'error')
    }
  }, [applyAutoLayout, layoutDirection, toast])
  
  // Handler pour exporter en PNG
  const handleExportPNG = useCallback(async () => {
    if (!reactFlowInstance || !selectedDialogue) {
      toast('Aucun dialogue sélectionné', 'warning')
      return
    }
    try {
      const filename = selectedDialogue.filename.replace('.json', '')
      await exportGraphToPNG(reactFlowInstance, filename, 1.0)
      toast('Export PNG réussi', 'success', 2000)
    } catch (err) {
      toast(`Erreur lors de l'export PNG: ${getErrorMessage(err)}`, 'error')
    }
  }, [reactFlowInstance, selectedDialogue, toast])
  
  // Handler pour exporter en SVG
  const handleExportSVG = useCallback(async () => {
    if (!reactFlowInstance || !selectedDialogue) {
      toast('Aucun dialogue sélectionné', 'warning')
      return
    }
    try {
      const filename = selectedDialogue.filename.replace('.json', '')
      await exportGraphToSVG(reactFlowInstance, filename)
      toast('Export SVG réussi', 'success', 2000)
    } catch (err) {
      toast(`Erreur lors de l'export SVG: ${getErrorMessage(err)}`, 'error')
    }
  }, [reactFlowInstance, selectedDialogue, toast])
  
  // Handler pour exporter tout le graphe en PNG
  const handleExportFullPNG = useCallback(async () => {
    if (!reactFlowInstance || !selectedDialogue) {
      toast('Aucun dialogue sélectionné', 'warning')
      return
    }
    try {
      const filename = `${selectedDialogue.filename.replace('.json', '')}-full`
      await exportFullGraphToPNG(reactFlowInstance, filename, 1.0)
      toast('Export PNG (graphe complet) réussi', 'success', 2000)
    } catch (err) {
      toast(`Erreur lors de l'export PNG complet: ${getErrorMessage(err)}`, 'error')
    }
  }, [reactFlowInstance, selectedDialogue, toast])
  
  // Handler pour sauvegarder
  const handleSave = useCallback(async () => {
    if (!selectedDialogue) {
      toast('Aucun dialogue sélectionné', 'warning')
      return
    }
    
    try {
      setIsLoadingDialogue(true)
      const unityJson = exportToUnity()
      const response = await dialoguesAPI.exportUnityDialogue({
        json_content: unityJson,
        title: selectedDialogue.title || selectedDialogue.filename,
        filename: selectedDialogue.filename.replace('.json', ''), // Enlever l'extension
      })
      toast(`Dialogue sauvegardé: ${response.filename}`, 'success', 3000)
      // Rafraîchir la liste
      dialogueListRef.current?.refresh()
    } catch (err) {
      toast(`Erreur lors de la sauvegarde: ${getErrorMessage(err)}`, 'error')
    } finally {
      setIsLoadingDialogue(false)
    }
  }, [selectedDialogue, exportToUnity, toast])
  
  // Raccourcis clavier
  useKeyboardShortcuts(
    [
      {
        key: 'ctrl+z',
        handler: (e) => {
          e.preventDefault()
          const { undo } = useGraphStore.temporal.getState()
          undo()
        },
        description: 'Annuler',
      },
      {
        key: 'ctrl+shift+z',
        handler: (e) => {
          e.preventDefault()
          const { redo } = useGraphStore.temporal.getState()
          redo()
        },
        description: 'Refaire',
      },
      {
        key: 'ctrl+s',
        handler: (e) => {
          e.preventDefault()
          if (selectedDialogue && !isGraphSaving) {
            handleSave()
          }
        },
        description: 'Sauvegarder',
        enabled: !!selectedDialogue && !isGraphSaving,
      },
    ],
    [selectedDialogue, isGraphSaving, handleSave]
  )
  
  return (
    <div style={{ 
      display: 'flex', 
      height: '100%', 
      minHeight: 0,
      overflow: 'hidden',
      flex: 1,
    }}>
      {/* Panneau gauche : Liste des dialogues */}
      <div
        style={{
          width: 'clamp(260px, 22vw, 340px)',
          minWidth: '240px',
          borderRight: `1px solid ${theme.border.primary}`,
          overflow: 'hidden',
          backgroundColor: theme.background.panel,
          height: '100%',
          minHeight: 0,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <UnityDialogueList
          ref={dialogueListRef}
          onSelectDialogue={setSelectedDialogue}
          selectedFilename={selectedDialogue?.filename || null}
        />
      </div>
      
      {/* Panneau droit : Graphe */}
      <div style={{ 
        flex: 1, 
        minHeight: 0,
        overflow: 'hidden', 
        backgroundColor: theme.background.panel,
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
      }}>
        {/* En-tête avec actions */}
        <div
          style={{
            flexShrink: 0,
            padding: '0.75rem 1rem',
            borderBottom: `1px solid ${theme.border.primary}`,
            backgroundColor: theme.background.panelHeader,
            display: 'flex',
            gap: '0.5rem',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
          }}
        >
          <div style={{ minWidth: 0 }}>
            <div
              style={{
                margin: 0,
                color: theme.text.primary,
                fontSize: '1rem',
                fontWeight: 700,
                lineHeight: 1.2,
                wordBreak: 'break-word',
              }}
            >
              {selectedDialogue 
                ? `Éditeur de Graphe - ${selectedDialogue.title || selectedDialogue.filename}`
                : 'Éditeur de Graphe Narratif'}
            </div>
            {selectedDialogue && (
              <div style={{ fontSize: '0.85rem', color: theme.text.secondary, marginTop: '0.25rem' }}>
                {selectedDialogue.filename}
              </div>
            )}
          </div>
          
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <button
              onClick={handleValidate}
              disabled={isGraphLoading || isLoadingDialogue || !selectedDialogue}
              style={{
                padding: '0.5rem 1rem',
                border: `1px solid ${theme.border.primary}`,
                borderRadius: '6px',
                backgroundColor: theme.button.default.background,
                color: theme.button.default.color,
                cursor: (isGraphLoading || isLoadingDialogue || !selectedDialogue) ? 'not-allowed' : 'pointer',
                opacity: (isGraphLoading || isLoadingDialogue || !selectedDialogue) ? 0.6 : 1,
                fontSize: '0.9rem',
              }}
              title="Valider le graphe"
            >
              ✓ Valider
            </button>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <select
                value={layoutDirection}
                onChange={(e) => setLayoutDirection(e.target.value as 'TB' | 'LR' | 'BT' | 'RL')}
                disabled={isGraphLoading || isLoadingDialogue || !selectedDialogue}
                style={{
                  padding: '0.5rem 0.75rem',
                  border: `1px solid ${theme.input.border}`,
                  borderRadius: '6px',
                  backgroundColor: theme.input.background,
                  color: theme.input.color,
                  fontSize: '0.85rem',
                  cursor: (isGraphLoading || isLoadingDialogue || !selectedDialogue) ? 'not-allowed' : 'pointer',
                  opacity: (isGraphLoading || isLoadingDialogue || !selectedDialogue) ? 0.6 : 1,
                }}
                title="Direction du layout"
              >
                <option value="TB">TB (Haut-Bas)</option>
                <option value="LR">LR (Gauche-Droite)</option>
                <option value="BT">BT (Bas-Haut)</option>
                <option value="RL">RL (Droite-Gauche)</option>
              </select>
              <button
                onClick={handleAutoLayout}
                disabled={isGraphLoading || isLoadingDialogue || !selectedDialogue}
                style={{
                  padding: '0.5rem 1rem',
                  border: `1px solid ${theme.border.primary}`,
                  borderRadius: '6px',
                  backgroundColor: theme.button.default.background,
                  color: theme.button.default.color,
                  cursor: (isGraphLoading || isLoadingDialogue || !selectedDialogue) ? 'not-allowed' : 'pointer',
                  opacity: (isGraphLoading || isLoadingDialogue || !selectedDialogue) ? 0.6 : 1,
                  fontSize: '0.9rem',
                }}
                title="Auto-layout (Dagre)"
              >
                📐 Auto-layout
              </button>
            </div>
            <button
              onClick={() => setShowAIGenerationPanel(true)}
              disabled={!selectedNodeId || isGraphLoading || isLoadingDialogue || !selectedDialogue}
              style={{
                padding: '0.5rem 1rem',
                border: 'none',
                borderRadius: '6px',
                backgroundColor: theme.button.primary.background,
                color: theme.button.primary.color,
                cursor: (!selectedNodeId || isGraphLoading || isLoadingDialogue || !selectedDialogue) ? 'not-allowed' : 'pointer',
                opacity: (!selectedNodeId || isGraphLoading || isLoadingDialogue || !selectedDialogue) ? 0.6 : 1,
                fontWeight: 700,
                fontSize: '0.9rem',
              }}
              title="Générer un nœud avec l'IA depuis le nœud sélectionné"
            >
              ✨ Générer nœud IA
            </button>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <button
                onClick={handleExportPNG}
                disabled={!reactFlowInstance || isLoadingDialogue || !selectedDialogue}
                style={{
                  padding: '0.5rem 0.75rem',
                  border: `1px solid ${theme.border.primary}`,
                  borderRadius: '6px',
                  backgroundColor: theme.button.default.background,
                  color: theme.button.default.color,
                  cursor: (!reactFlowInstance || isLoadingDialogue || !selectedDialogue) ? 'not-allowed' : 'pointer',
                  opacity: (!reactFlowInstance || isLoadingDialogue || !selectedDialogue) ? 0.6 : 1,
                  fontSize: '0.85rem',
                }}
                title="Exporter le graphe visible en PNG"
              >
                📷 PNG
              </button>
              <button
                onClick={handleExportSVG}
                disabled={!reactFlowInstance || isLoadingDialogue || !selectedDialogue}
                style={{
                  padding: '0.5rem 0.75rem',
                  border: `1px solid ${theme.border.primary}`,
                  borderRadius: '6px',
                  backgroundColor: theme.button.default.background,
                  color: theme.button.default.color,
                  cursor: (!reactFlowInstance || isLoadingDialogue || !selectedDialogue) ? 'not-allowed' : 'pointer',
                  opacity: (!reactFlowInstance || isLoadingDialogue || !selectedDialogue) ? 0.6 : 1,
                  fontSize: '0.85rem',
                }}
                title="Exporter le graphe visible en SVG"
              >
                🎨 SVG
              </button>
            </div>
            <button
              onClick={handleSave}
              disabled={isGraphSaving || isLoadingDialogue || !selectedDialogue}
              style={{
                padding: '0.5rem 1rem',
                border: 'none',
                borderRadius: '6px',
                backgroundColor: theme.button.primary.background,
                color: theme.button.primary.color,
                cursor: (isGraphSaving || isLoadingDialogue || !selectedDialogue) ? 'not-allowed' : 'pointer',
                opacity: (isGraphSaving || isLoadingDialogue || !selectedDialogue) ? 1 : 0.6,
                fontWeight: 700,
                fontSize: '0.9rem',
              }}
            >
              {isGraphSaving ? 'Sauvegarde...' : '💾 Sauvegarder'}
            </button>
          </div>
        </div>
        
        {/* Contenu : Graphe + Panneau d'édition */}
        {!selectedDialogue ? (
          <div style={{ 
            flex: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: theme.text.secondary,
            padding: '2rem',
            textAlign: 'center',
          }}>
            <div>
              <div style={{ fontSize: '3rem', marginBottom: '1rem', opacity: 0.7 }}>📊</div>
              <div style={{ fontSize: '1.2rem', marginBottom: '0.5rem', color: theme.text.primary }}>
                Sélectionnez un dialogue Unity
              </div>
              <div style={{ fontSize: '0.9rem' }}>
                Choisissez un dialogue dans la liste à gauche pour le visualiser et l'éditer sous forme de graphe
              </div>
            </div>
          </div>
        ) : (
          <div style={{ 
            flex: 1, 
            minHeight: 0,
            height: 0, // Force flex child to respect parent height
            position: 'relative',
            backgroundColor: theme.background.panel,
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          }}>
            {isLoadingDialogue || isGraphLoading ? (
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center', 
                height: '100%',
                color: theme.text.secondary,
              }}>
                Chargement du graphe...
              </div>
            ) : (
              <>
                <GraphSearchBar 
                  onNodeSelect={(nodeId) => {
                    // Le GraphCanvas gérera le scroll via fitView
                  }}
                />
                <div style={{ flex: 1, minHeight: 0, overflow: 'hidden' }}>
                  <ReactFlowProvider>
                    <GraphCanvas />
                  </ReactFlowProvider>
                </div>
              </>
            )}
            {/* Panel d'erreurs de validation (overlay) */}
            {graphValidationErrors.length > 0 && (
              <div
                style={{
                  position: 'absolute',
                  bottom: 16,
                  left: 16,
                  right: 16,
                  maxHeight: '300px',
                  overflowY: 'auto',
                  backgroundColor: theme.state.error.background,
                  border: `1px solid ${theme.state.error.border}`,
                  borderRadius: '6px',
                  padding: '0.75rem',
                  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.4)',
                  zIndex: 1000,
                }}
              >
                <div style={{ 
                  fontSize: '0.85rem', 
                  fontWeight: 'bold', 
                  color: theme.state.error.color,
                  marginBottom: '0.5rem',
                }}>
                  ⚠️ {graphValidationErrors.length} erreur(s) de validation
                </div>
                <div style={{ fontSize: '0.8rem', color: theme.state.error.color }}>
                  {graphValidationErrors.map((err, idx) => (
                    <div
                      key={idx}
                      onClick={() => {
                        if (err.node_id) {
                          setSelectedNode(err.node_id)
                        }
                      }}
                      style={{
                        marginBottom: '0.25rem',
                        padding: '0.25rem 0.5rem',
                        borderRadius: '4px',
                        cursor: err.node_id ? 'pointer' : 'default',
                        backgroundColor: err.node_id ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
                        transition: 'background-color 0.2s',
                      }}
                      onMouseEnter={(e) => {
                        if (err.node_id) {
                          e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.2)'
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (err.node_id) {
                          e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)'
                        }
                      }}
                    >
                      {err.node_id ? `[${err.node_id}] ` : ''}{err.message}
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Panel de génération IA (modal overlay) */}
            {showAIGenerationPanel && (
              <div
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  backgroundColor: 'rgba(0, 0, 0, 0.7)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  zIndex: 2000,
                }}
                onClick={(e) => {
                  if (e.target === e.currentTarget) {
                    setShowAIGenerationPanel(false)
                  }
                }}
              >
                <div
                  style={{
                    width: '90%',
                    maxWidth: '600px',
                    maxHeight: '90%',
                    backgroundColor: theme.background.panel,
                    borderRadius: '8px',
                    boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)',
                    display: 'flex',
                    flexDirection: 'column',
                    overflow: 'hidden',
                  }}
                  onClick={(e) => e.stopPropagation()}
                >
                  <AIGenerationPanel
                    parentNodeId={selectedNodeId}
                    onClose={() => setShowAIGenerationPanel(false)}
                    onGenerated={() => {
                      // Rafraîchir la liste des dialogues si nécessaire
                      dialogueListRef.current?.refresh()
                    }}
                  />
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
