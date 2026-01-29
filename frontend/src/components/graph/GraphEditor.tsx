/**
 * Éditeur de graphe narratif avec sélecteur de dialogue.
 * Structure : Liste de dialogues à gauche, graphe à droite.
 */
import { useState, useRef, useCallback, useEffect } from 'react'
import { ReactFlowProvider } from 'reactflow'
import type { ReactFlowInstance } from 'reactflow'
import { UnityDialogueList, type UnityDialogueListRef } from '../unityDialogues/UnityDialogueList'
import { GraphCanvas } from './GraphCanvas'
import { AIGenerationPanel } from './AIGenerationPanel'
import { DeleteNodeConfirmModal } from './DeleteNodeConfirmModal'
import { useGraphStore } from '../../store/graphStore'
import { exportGraphToPNG, exportGraphToSVG } from '../../utils/graphExport'
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts'
import { useToast, SaveStatusIndicator } from '../shared'
import { theme } from '../../theme'
import * as unityDialoguesAPI from '../../api/unityDialogues'
import { getErrorMessage } from '../../types/errors'
import type { UnityDialogueMetadata } from '../../types/api'

export function GraphEditor() {
  const [selectedDialogue, setSelectedDialogue] = useState<UnityDialogueMetadata | null>(null)
  const [isLoadingDialogue, setIsLoadingDialogue] = useState(false)
  const [layoutDirection, setLayoutDirection] = useState<'TB' | 'LR' | 'BT' | 'RL'>('TB')
  const [showAIGenerationPanel, setShowAIGenerationPanel] = useState(false)
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null)
  const dialogueListRef = useRef<UnityDialogueListRef>(null)
  const prevSelectedDialogueRef = useRef<UnityDialogueMetadata | null>(null)
  const loadInFlightRef = useRef(false)
  const canvasWrapperRef = useRef<HTMLDivElement | null>(null)
  const toast = useToast()
  
  // États auto-save draft (Task 2 - Story 0.5) - supprimés, maintenant géré automatiquement
  
  // État pour le dialogue de sélection de format d'export
  const [showExportFormatDialog, setShowExportFormatDialog] = useState(false)
  
  // Panneau d'avertissements/erreurs de validation (affiché via clic sur le badge)
  const [showValidationPanel, setShowValidationPanel] = useState(false)
  
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
    nodes,
    loadDialogue,
    saveDialogue,
    validateGraph,
    applyAutoLayout,
    setSelectedNode,
    selectedNodeId,
    isLoading: isGraphLoading,
    validationErrors: graphValidationErrors,
    isSaving: isGraphSaving,
    isGenerating,
    intentionalCycles,
    markCycleAsIntentional,
    unmarkCycleAsIntentional,
    createEmptyNode,
    addNode,
    hasUnsavedChanges,
    lastSaveError,
    lastSavedAt,
    setShowDeleteNodeConfirm,
    syncStatus,
    lastAckSeq,
    documentId,
  } = useGraphStore()
  
  /** Désactive les actions graphe si aucun dialogue ou chargement en cours (évite duplication de condition). */
  const canEditGraph = !!selectedDialogue && !isGraphLoading && !isLoadingDialogue
  /** Offset position pour nœuds manuels (Story 1.6 - éviter chevauchement). */
  const MANUAL_NODE_OFFSET_X = 150
  const MANUAL_NODE_OFFSET_Y = 100
  const MANUAL_NODE_STEP = 40

  // Écouter l'événement pour ouvrir le panel de génération depuis un nœud
  useEffect(() => {
    const handleOpenGenerationPanel = (event: CustomEvent<{ nodeId: string }>) => {
      const nodeId = event.detail.nodeId
      setSelectedNode(nodeId)
      setShowAIGenerationPanel(true)
    }
    
    window.addEventListener('open-ai-generation-panel', handleOpenGenerationPanel as EventListener)
    return () => {
      window.removeEventListener('open-ai-generation-panel', handleOpenGenerationPanel as EventListener)
    }
  }, [setSelectedNode])
  
  // Charger le dialogue sélectionné depuis l'API (plus de draft local).
  // Ne pas appeler resetGraph à la désélection : le graphe reste affiché jusqu'au prochain chargement
  // (évite que les nœuds disparaissent après un load quand l'effet else s'exécute).
  useEffect(() => {
    if (selectedDialogue) {
      prevSelectedDialogueRef.current = selectedDialogue
      loadInFlightRef.current = true
      setIsLoadingDialogue(true)
      unityDialoguesAPI.getUnityDialogue(selectedDialogue.filename)
        .then((response) => loadDialogue(response.json_content, undefined, selectedDialogue.filename))
        .then(async () => {
          try {
            await validateGraph()
          } catch (err) {
            console.error('Erreur lors de la validation automatique au chargement:', err)
          }
          loadInFlightRef.current = false
          setIsLoadingDialogue(false)
          const state = useGraphStore.getState()
          // Sélectionner le premier nœud pour afficher le panneau Détails (évite "rien ne s'affiche dans le dialogue")
          if (state.nodes.length > 0 && !state.selectedNodeId) {
            state.setSelectedNode(state.nodes[0].id)
          }
        })
        .catch((err) => {
          console.error('Erreur lors du chargement du dialogue:', err)
          toast(`Erreur: ${getErrorMessage(err)}`, 'error')
          loadInFlightRef.current = false
          setIsLoadingDialogue(false)
        })
    } else {
      // Désélection : ne pas vider le graphe (remplacé au prochain load)
      prevSelectedDialogueRef.current = null
    }
  }, [selectedDialogue, loadDialogue, validateGraph, toast])

  // Auto-save backend : micro-batch 100 ms (ADR-006)
  useEffect(() => {
    if (
      !selectedDialogue ||
      !hasUnsavedChanges ||
      isGraphLoading ||
      isGraphSaving ||
      isLoadingDialogue ||
      isGenerating
    ) {
      return
    }
    const timeoutId = setTimeout(() => {
      saveDialogue().catch((err) => {
        toast(`Sauvegarde automatique échouée: ${getErrorMessage(err)}`, 'error')
      })
    }, 100)
    return () => clearTimeout(timeoutId)
  }, [selectedDialogue, hasUnsavedChanges, isGraphLoading, isGraphSaving, isLoadingDialogue, isGenerating, nodes, saveDialogue, toast])
  
  // Handler pour auto-layout
  const handleAutoLayout = useCallback(async () => {
    try {
      await applyAutoLayout('dagre', layoutDirection)
      toast('Layout appliqué', 'success', 2000)
    } catch (err) {
      toast(`Erreur lors de l'auto-layout: ${getErrorMessage(err)}`, 'error')
    }
  }, [applyAutoLayout, layoutDirection, toast])
  
  // Handler pour ouvrir le dialogue de sélection de format
  const handleOpenExportDialog = useCallback(() => {
    if (!reactFlowInstance || !selectedDialogue) {
      toast('Aucun dialogue sélectionné', 'warning')
      return
    }
    setShowExportFormatDialog(true)
  }, [reactFlowInstance, selectedDialogue, toast])
  
  // Handler pour exporter en PNG
  const handleExportPNG = useCallback(async () => {
    if (!reactFlowInstance || !selectedDialogue) {
      toast('Aucun dialogue sélectionné', 'warning')
      return
    }
    try {
      setShowExportFormatDialog(false)
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
      setShowExportFormatDialog(false)
      const filename = selectedDialogue.filename.replace('.json', '')
      await exportGraphToSVG(reactFlowInstance, filename)
      toast('Export SVG réussi', 'success', 2000)
    } catch (err) {
      toast(`Erreur lors de l'export SVG: ${getErrorMessage(err)}`, 'error')
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
      // Flush du panneau Détails (formulaire) vers le store avant sauvegarde (évite perte speaker/line des nœuds manuels)
      window.dispatchEvent(new CustomEvent('flush-node-editor-form'))
      await new Promise<void>((resolve) => {
        const timeout = setTimeout(resolve, 1500)
        const onFlushed = () => {
          clearTimeout(timeout)
          resolve()
        }
        window.addEventListener('node-editor-flushed', onFlushed, { once: true })
      })
      // saveDialogue() appelle l'API save-and-write (conversion + écriture disque en un appel)
      const saveResponse = await saveDialogue()
      try {
        await validateGraph()
        const state = useGraphStore.getState()
        const errors = state.validationErrors.filter((e) => e.severity === 'error')
        const warnings = state.validationErrors.filter((e) => e.severity === 'warning')
        if (errors.length === 0 && warnings.length === 0) {
          toast(`Dialogue sauvegardé: ${saveResponse.filename} - Graphe valide`, 'success', 3000)
        } else if (errors.length > 0) {
          toast(`Dialogue sauvegardé: ${saveResponse.filename} - ${errors.length} erreur(s) et ${warnings.length} avertissement(s)`, 'warning', 4000)
        } else {
          toast(`Dialogue sauvegardé: ${saveResponse.filename} - ${warnings.length} avertissement(s)`, 'warning', 4000)
        }
      } catch (validationErr) {
        console.error('Erreur lors de la validation automatique:', validationErr)
        toast(`Dialogue sauvegardé: ${saveResponse.filename}`, 'success', 3000)
      }
      dialogueListRef.current?.refresh()
    } catch (err) {
      toast(`Erreur lors de la sauvegarde: ${getErrorMessage(err)}`, 'error')
    } finally {
      setIsLoadingDialogue(false)
    }
  }, [selectedDialogue, saveDialogue, validateGraph, toast])

  // Sauvegarder quand le panneau Détails envoie "request-save-dialogue" (bouton Sauvegarder du panneau)
  useEffect(() => {
    const onRequestSave = () => { handleSave() }
    window.addEventListener('request-save-dialogue', onRequestSave)
    return () => window.removeEventListener('request-save-dialogue', onRequestSave)
  }, [handleSave])
  
  // Raccourcis clavier
  useKeyboardShortcuts(
    [
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
      {
        key: 'ctrl+g',
        handler: (e) => {
          e.preventDefault()
          if (selectedNodeId && !isGraphLoading && !isLoadingDialogue && selectedDialogue) {
            setShowAIGenerationPanel(true)
          }
        },
        description: 'Générer un nœud avec l\'IA',
        enabled: !!selectedNodeId && !isGraphLoading && !isLoadingDialogue && !!selectedDialogue,
      },
      {
        key: 'delete',
        handler: (e) => {
          e.preventDefault()
          const currentSelectedNodeId = useGraphStore.getState().selectedNodeId
          if (currentSelectedNodeId) {
            setShowDeleteNodeConfirm(true)
          }
        },
        description: 'Supprimer le nœud sélectionné',
        enabled: () => !!useGraphStore.getState().selectedNodeId,
      },
    ],
    [selectedDialogue, isGraphSaving, handleSave, selectedNodeId, isGraphLoading, isLoadingDialogue, setShowDeleteNodeConfirm]
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
            justifyContent: 'flex-end',
            flexWrap: 'wrap',
          }}
        >
          <div style={{ 
            flex: 1, 
            minWidth: 0, 
            display: 'flex', 
            gap: '0.5rem', 
            alignItems: 'center', 
            flexWrap: 'wrap',
            justifyContent: 'flex-start',
          }}>
            {/* Badge de santé global du graphe (validation automatique à chaque sauvegarde) */}
            {(() => {
              const errors = graphValidationErrors.filter((e) => e.severity === 'error')
              const warnings = graphValidationErrors.filter((e) => e.severity === 'warning')
              const hasErrors = errors.length > 0
              const hasWarnings = warnings.length > 0 && !hasErrors
              const isValid = !hasErrors && !hasWarnings
              const canToggle = hasErrors || hasWarnings
              const badgeStyle = {
                padding: '0.4rem 0.75rem',
                borderRadius: '6px',
                fontSize: '0.85rem',
                fontWeight: 600,
                backgroundColor: isValid 
                  ? theme.state.success.background 
                  : hasErrors 
                  ? theme.state.error.background 
                  : theme.state.warning.background,
                color: isValid 
                  ? theme.state.success.color 
                  : hasErrors 
                  ? theme.state.error.color 
                  : theme.state.warning.color,
                border: `1px solid ${isValid 
                  ? theme.state.success.color 
                  : hasErrors 
                  ? theme.state.error.border 
                  : theme.state.warning.color}`,
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                ...(canToggle && { cursor: 'pointer' }),
              } as React.CSSProperties
              const title = isValid 
                ? 'Graphe valide (validation automatique à chaque sauvegarde)' 
                : canToggle 
                ? (showValidationPanel 
                  ? 'Cliquer pour masquer les détails' 
                  : 'Cliquer pour afficher les détails')
                : hasErrors 
                ? `${errors.length} erreur(s) détectée(s)` 
                : `${warnings.length} avertissement(s) détecté(s)`
              
              const content = (
                <>
                  <span>{isValid ? '✓' : hasErrors ? '✗' : '⚠'}</span>
                  <span>
                    {isValid 
                      ? 'Graphe valide' 
                      : hasErrors 
                      ? `${errors.length} erreur${errors.length > 1 ? 's' : ''}` 
                      : `${warnings.length} avertissement${warnings.length > 1 ? 's' : ''}`}
                  </span>
                </>
              )
              
              if (canToggle) {
                return (
                  <button
                    type="button"
                    style={{
                      ...badgeStyle,
                      margin: 0,
                      appearance: 'none',
                      WebkitAppearance: 'none',
                      font: 'inherit',
                    }}
                    title={title}
                    onClick={() => setShowValidationPanel((v) => !v)}
                  >
                    {content}
                  </button>
                )
              }
              return (
                <div style={badgeStyle} title={title}>
                  {content}
                </div>
              )
            })()}
            {/* Indicateur sauvegarde ADR-006: Synced (seq …) / Offline, N queued / Error */}
            {selectedDialogue && (() => {
              const status: 'saved' | 'saving' | 'unsaved' | 'error' = lastSaveError
                ? 'error'
                : isGraphSaving
                  ? 'saving'
                  : hasUnsavedChanges
                    ? 'unsaved'
                    : 'saved'
              const pendingCount = hasUnsavedChanges ? 1 : 0
              const syncStatusDisplay =
                syncStatus === 'synced' && typeof navigator !== 'undefined' && !navigator.onLine
                  ? 'offline'
                  : syncStatus
              return (
                <SaveStatusIndicator
                  status={status}
                  lastSavedAt={lastSavedAt}
                  errorMessage={lastSaveError}
                  ackSeq={lastAckSeq}
                  pendingCount={pendingCount}
                  syncStatusDisplay={syncStatusDisplay}
                />
              )
            })()}
            {/* Direction layout + Auto-layout */}
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <select
                value={layoutDirection}
                onChange={(e) => setLayoutDirection(e.target.value as 'TB' | 'LR' | 'BT' | 'RL')}
                disabled={!canEditGraph}
                style={{
                  padding: '0.5rem 0.75rem',
                  border: `1px solid ${theme.input.border}`,
                  borderRadius: '6px',
                  backgroundColor: theme.input.background,
                  color: theme.input.color,
                  fontSize: '0.85rem',
                  cursor: canEditGraph ? 'pointer' : 'not-allowed',
                  opacity: canEditGraph ? 1 : 0.6,
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
                disabled={!canEditGraph}
                style={{
                  padding: '0.5rem 1rem',
                  border: `1px solid ${theme.border.primary}`,
                  borderRadius: '6px',
                  backgroundColor: theme.button.default.background,
                  color: theme.button.default.color,
                  cursor: canEditGraph ? 'pointer' : 'not-allowed',
                  opacity: canEditGraph ? 1 : 0.6,
                  fontSize: '0.9rem',
                }}
                title="Auto-layout (Dagre)"
              >
                📐 Auto-layout
              </button>
            </div>
            <button
              data-testid="btn-new-manual-node"
              onClick={() => {
                const count = nodes.filter((n) => n.type === 'dialogueNode').length
                const position = {
                  x: MANUAL_NODE_OFFSET_X + count * MANUAL_NODE_STEP,
                  y: MANUAL_NODE_OFFSET_Y + count * MANUAL_NODE_STEP,
                }
                const node = createEmptyNode(position)
                addNode(node)
                setSelectedNode(node.id)
                if (reactFlowInstance) {
                  requestAnimationFrame(() => {
                    requestAnimationFrame(() => {
                      const n = reactFlowInstance.getNode(node.id)
                      if (n) reactFlowInstance.fitView({ nodes: [n], padding: 0.2, duration: 200 })
                    })
                  })
                }
              }}
              disabled={!canEditGraph}
              style={{
                padding: '0.5rem 1rem',
                border: `1px solid ${theme.border.primary}`,
                borderRadius: '6px',
                backgroundColor: theme.button.default.background,
                color: theme.button.default.color,
                cursor: canEditGraph ? 'pointer' : 'not-allowed',
                opacity: canEditGraph ? 1 : 0.6,
                fontWeight: 600,
                fontSize: '0.9rem',
              }}
              title="Créer un nœud vide (sans IA) et ouvrir l'éditeur"
            >
              ➕ Nouveau nœud
            </button>
            <button
              onClick={() => setShowAIGenerationPanel(true)}
              disabled={!selectedNodeId || !canEditGraph}
              style={{
                padding: '0.5rem 1rem',
                border: 'none',
                borderRadius: '6px',
                backgroundColor: theme.button.primary.background,
                color: theme.button.primary.color,
                cursor: (!selectedNodeId || !canEditGraph) ? 'not-allowed' : 'pointer',
                opacity: (!selectedNodeId || !canEditGraph) ? 0.6 : 1,
                fontWeight: 700,
                fontSize: '0.9rem',
              }}
              title="Générer un nœud avec l'IA depuis le nœud sélectionné"
            >
              ✨ Générer nœud
            </button>
            <button
              onClick={handleOpenExportDialog}
              disabled={!reactFlowInstance || !canEditGraph}
              style={{
                padding: '0.5rem 1rem',
                border: `1px solid ${theme.border.primary}`,
                borderRadius: '6px',
                backgroundColor: theme.button.default.background,
                color: theme.button.default.color,
                cursor: (!reactFlowInstance || !canEditGraph) ? 'not-allowed' : 'pointer',
                opacity: (!reactFlowInstance || !canEditGraph) ? 0.6 : 1,
                fontSize: '0.9rem',
              }}
              title="Exporter le graphe visible"
            >
              📤 Exporter
            </button>
            {/* ADR-006: pas de bouton Sauvegarder (autosave immédiat) */}
          </div>
        </div>
        
        {/* Contenu : Graphe + Panneau d'édition. Afficher le canvas si dialogue sélectionné OU si le store a des nœuds (graphe déjà chargé). */}
        {!selectedDialogue && nodes.length === 0 ? (
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
              <div
                ref={canvasWrapperRef}
                key={`graph-${documentId ?? 'empty'}`}
                style={{ flex: 1, minHeight: 400, overflow: 'hidden' }}
              >
                <ReactFlowProvider>
                  <GraphCanvas />
                </ReactFlowProvider>
              </div>
            )}
            {/* Panel d'erreurs de validation (overlay) — affiché via clic sur le badge */}
            {showValidationPanel && graphValidationErrors.length > 0 && (() => {
              const errors = graphValidationErrors.filter((e) => e.severity === 'error')
              // Filtrer les cycles intentionnels des warnings (ne pas afficher si marqués intentionnels)
              const warnings = graphValidationErrors
                .filter((e) => e.severity === 'warning')
                .filter((warn) => {
                  // Filtrer les cycles intentionnels (ne pas afficher si dans intentionalCycles)
                  if (warn.type === 'cycle_detected' && warn.cycle_id) {
                    return !intentionalCycles.includes(warn.cycle_id)
                  }
                  return true
                })
              
              // Grouper les erreurs par type
              const errorsByType = errors.reduce((acc, err) => {
                const type = err.type || 'other'
                if (!acc[type]) acc[type] = []
                acc[type].push(err)
                return acc
              }, {} as Record<string, typeof errors>)
              
              const warningsByType = warnings.reduce((acc, warn) => {
                const type = warn.type || 'other'
                if (!acc[type]) acc[type] = []
                acc[type].push(warn)
                return acc
              }, {} as Record<string, typeof warnings>)
              
              const getIconForType = (type: string) => {
                switch (type) {
                  case 'orphan_node': return '🔗'
                  case 'broken_reference': return '🔴'
                  case 'empty_node': return '⚪'
                  case 'missing_test': return '❓'
                  case 'unreachable_node': return '📍'
                  case 'cycle_detected': return '🔄'
                  default: return '⚠️'
                }
              }
              
              const getLabelForType = (type: string) => {
                switch (type) {
                  case 'orphan_node': return 'Nœuds orphelins'
                  case 'broken_reference': return 'Références cassées'
                  case 'empty_node': return 'Nœuds vides'
                  case 'missing_test': return 'Tests manquants'
                  case 'unreachable_node': return 'Nœuds inaccessibles'
                  case 'cycle_detected': return 'Cycles détectés'
                  default: return 'Autres'
                }
              }
              
              return (
                <div
                  style={{
                    position: 'absolute',
                    bottom: 16,
                    left: 16,
                    right: 16,
                    maxHeight: '350px',
                    overflowY: 'auto',
                    backgroundColor: errors.length > 0 ? theme.state.error.background : theme.state.warning.background,
                    border: `1px solid ${errors.length > 0 ? theme.state.error.border : theme.state.warning.color}`,
                    borderRadius: '6px',
                    padding: '0.75rem',
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.4)',
                    zIndex: 1000,
                  }}
                >
                  <div style={{ 
                    fontSize: '0.85rem', 
                    fontWeight: 'bold', 
                    color: errors.length > 0 ? theme.state.error.color : theme.state.warning.color,
                    marginBottom: '0.75rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                  }}>
                    <span>{errors.length > 0 ? '✗' : '⚠'}</span>
                    <span>
                      {errors.length > 0 
                        ? `${errors.length} erreur${errors.length > 1 ? 's' : ''}`
                        : `${warnings.length} avertissement${warnings.length > 1 ? 's' : ''}`}
                    </span>
                  </div>
                  
                  {/* Erreurs groupées par type */}
                  {errors.length > 0 && Object.entries(errorsByType).map(([type, typeErrors]) => (
                    <div key={`error-${type}`} style={{ marginBottom: '0.75rem' }}>
                      <div style={{
                        fontSize: '0.8rem',
                        fontWeight: 600,
                        color: theme.state.error.color,
                        marginBottom: '0.25rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.4rem',
                      }}>
                        <span>{getIconForType(type)}</span>
                        <span>{getLabelForType(type)} ({typeErrors.length})</span>
                      </div>
                      {typeErrors.map((err, idx) => (
                        <div
                          key={idx}
                          onClick={() => {
                            if (err.node_id) {
                              setSelectedNode(err.node_id)
                            }
                          }}
                          style={{
                            fontSize: '0.75rem',
                            color: theme.state.error.color,
                            marginBottom: '0.2rem',
                            padding: '0.3rem 0.5rem',
                            borderRadius: '4px',
                            cursor: err.node_id ? 'pointer' : 'default',
                            backgroundColor: err.node_id ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
                            transition: 'background-color 0.2s',
                            marginLeft: '1.5rem',
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
                  ))}
                  
                  {/* Avertissements groupés par type */}
                  {warnings.length > 0 && Object.entries(warningsByType).map(([type, typeWarnings]) => (
                    <div key={`warning-${type}`} style={{ marginBottom: '0.75rem' }}>
                      <div style={{
                        fontSize: '0.8rem',
                        fontWeight: 600,
                        color: theme.state.warning.color,
                        marginBottom: '0.25rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.4rem',
                      }}>
                        <span>{getIconForType(type)}</span>
                        <span>{getLabelForType(type)} ({typeWarnings.length})</span>
                      </div>
                      {typeWarnings.map((warn, idx) => {
                        // Gestion spéciale pour les cycles
                        const isCycle = type === 'cycle_detected' && warn.cycle_path && warn.cycle_nodes
                        
                        const handleClick = () => {
                          if (isCycle && reactFlowInstance && warn.cycle_nodes) {
                            // Zoomer vers les nœuds du cycle
                            const cycleNodeObjects = warn.cycle_nodes
                              .map(nodeId => reactFlowInstance.getNode(nodeId))
                              .filter(node => node !== undefined)
                            
                            if (cycleNodeObjects.length > 0) {
                              reactFlowInstance.fitView({
                                nodes: cycleNodeObjects,
                                padding: 0.2,
                                duration: 300
                              })
                            }
                          } else if (warn.node_id) {
                            setSelectedNode(warn.node_id)
                          }
                        }
                        
                        return (
                          <div
                            key={idx}
                            onClick={handleClick}
                            style={{
                              fontSize: '0.75rem',
                              color: theme.state.warning.color,
                              marginBottom: '0.2rem',
                              padding: '0.3rem 0.5rem',
                              borderRadius: '4px',
                              cursor: (isCycle || warn.node_id) ? 'pointer' : 'default',
                              backgroundColor: (isCycle || warn.node_id) ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
                              transition: 'background-color 0.2s',
                              marginLeft: '1.5rem',
                            }}
                            onMouseEnter={(e) => {
                              if (isCycle || warn.node_id) {
                                e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.2)'
                              }
                            }}
                            onMouseLeave={(e) => {
                              if (isCycle || warn.node_id) {
                                e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)'
                              }
                            }}
                            title={isCycle ? 'Cliquer pour zoomer sur les nœuds du cycle' : undefined}
                          >
                            {isCycle ? (
                              // Afficher le chemin complet du cycle avec checkbox "intentionnel"
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                                <span style={{ fontWeight: 500, flex: 1 }}>
                                  {warn.cycle_path}
                                </span>
                                {warn.cycle_id && (
                                  <label
                                    style={{
                                      display: 'flex',
                                      alignItems: 'center',
                                      gap: '0.25rem',
                                      fontSize: '0.7rem',
                                      cursor: 'pointer',
                                      userSelect: 'none',
                                    }}
                                    onClick={(e) => e.stopPropagation()}
                                  >
                                    <input
                                      type="checkbox"
                                      checked={intentionalCycles.includes(warn.cycle_id)}
                                      onChange={(e) => {
                                        e.stopPropagation()
                                        if (warn.cycle_id) {
                                          if (e.target.checked) {
                                            markCycleAsIntentional(warn.cycle_id)
                                          } else {
                                            unmarkCycleAsIntentional(warn.cycle_id)
                                          }
                                        }
                                      }}
                                      style={{ cursor: 'pointer' }}
                                    />
                                    <span>Marquer comme intentionnel</span>
                                  </label>
                                )}
                              </div>
                            ) : (
                              // Affichage normal pour les autres warnings
                              <>
                                {warn.node_id ? `[${warn.node_id}] ` : ''}{warn.message}
                              </>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  ))}
                </div>
              )
            })()}
            
            {/* Panel de génération IA (modal overlay) */}
            {showAIGenerationPanel && (
              <div
                style={{
                  position: 'fixed',
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
                    maxHeight: '90vh',
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
      
      
      {/* Dialog de sélection de format d'export */}
      {showExportFormatDialog && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 10001,
          }}
          onClick={() => setShowExportFormatDialog(false)}
        >
          <div
            style={{
              backgroundColor: theme.background.panel,
              borderRadius: '8px',
              padding: '1.5rem',
              maxWidth: '400px',
              width: '90%',
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
              border: `1px solid ${theme.border.primary}`,
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2 style={{ marginTop: 0, marginBottom: '1rem', color: theme.text.primary }}>
              Choisir le format d'export
            </h2>
            <p style={{ marginBottom: '1.5rem', color: theme.text.secondary, lineHeight: 1.6 }}>
              Sélectionnez le format dans lequel vous souhaitez exporter le graphe :
            </p>
            <div style={{ display: 'flex', gap: '0.75rem', flexDirection: 'column' }}>
              <button
                onClick={handleExportPNG}
                style={{
                  padding: '0.75rem 1rem',
                  border: `1px solid ${theme.border.primary}`,
                  borderRadius: '6px',
                  backgroundColor: theme.button.default.background,
                  color: theme.button.default.color,
                  cursor: 'pointer',
                  fontSize: '0.9rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  justifyContent: 'center',
                }}
              >
                <span>📷</span>
                <span>PNG (Image raster)</span>
              </button>
              <button
                onClick={handleExportSVG}
                style={{
                  padding: '0.75rem 1rem',
                  border: `1px solid ${theme.border.primary}`,
                  borderRadius: '6px',
                  backgroundColor: theme.button.default.background,
                  color: theme.button.default.color,
                  cursor: 'pointer',
                  fontSize: '0.9rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  justifyContent: 'center',
                }}
              >
                <span>🎨</span>
                <span>SVG (Vectoriel)</span>
              </button>
            </div>
            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
              <button
                onClick={() => setShowExportFormatDialog(false)}
                style={{
                  padding: '0.5rem 1rem',
                  border: `1px solid ${theme.border.primary}`,
                  borderRadius: '4px',
                  backgroundColor: theme.button.default.background,
                  color: theme.button.default.color,
                  cursor: 'pointer',
                }}
              >
                Annuler
              </button>
            </div>
          </div>
        </div>
      )}

      <DeleteNodeConfirmModal />
    </div>
  )
}
