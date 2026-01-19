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
import { useGraphStore } from '../../store/graphStore'
import { exportGraphToPNG, exportGraphToSVG } from '../../utils/graphExport'
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts'
import { useToast, ConfirmDialog, SaveStatusIndicator } from '../shared'
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
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null)
  const dialogueListRef = useRef<UnityDialogueListRef>(null)
  const toast = useToast()
  
  // États auto-save draft (Task 2 - Story 0.5)
  const [showRestoreDialog, setShowRestoreDialog] = useState(false)
  const [draftToRestore, setDraftToRestore] = useState<{json_content: string; timestamp: number} | null>(null)
  
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
    setSelectedNode,
    selectedNodeId,
    isLoading: isGraphLoading,
    validationErrors: graphValidationErrors,
    isSaving: isGraphSaving,
    isGenerating,
    // États auto-save draft (Task 2 - Story 0.5)
    hasUnsavedChanges,
    lastDraftSavedAt,
    lastDraftError,
    markDraftSaved,
    markDraftError,
    clearDraftError,
  } = useGraphStore()
  
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
  
  // Charger le dialogue sélectionné dans le graphe + vérifier draft (Task 2 - Story 0.5)
  useEffect(() => {
    if (selectedDialogue) {
      setIsLoadingDialogue(true)
      
      // Clé stable pour le draft
      const draftKey = `unity_dialogue_draft:${selectedDialogue.filename}`
      
      // Charger le dialogue depuis l'API
      unityDialoguesAPI.getUnityDialogue(selectedDialogue.filename)
        .then((response) => {
          // Vérifier s'il existe un draft local
          const draftStr = localStorage.getItem(draftKey)
          if (draftStr) {
            try {
              const draft = JSON.parse(draftStr)
              const draftTimestamp = draft.timestamp || 0
              const fileTimestamp = selectedDialogue.modified_time 
                ? new Date(selectedDialogue.modified_time).getTime() 
                : 0
              
              // Si draft plus récent que le fichier → proposer restauration
              if (draftTimestamp > fileTimestamp) {
                setDraftToRestore(draft)
                setShowRestoreDialog(true)
                setIsLoadingDialogue(false)
                return // Attendre la décision de l'utilisateur
              } else {
                // Draft obsolète → supprimer
                localStorage.removeItem(draftKey)
              }
            } catch (err) {
              console.error('Erreur lors de la lecture du draft:', err)
              localStorage.removeItem(draftKey)
            }
          }
          
          // Charger le dialogue normalement
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
  
  // Auto-save draft avec debounce (Task 2 - Story 0.5)
  useEffect(() => {
    // Ne pas auto-save si conditions bloquantes
    if (!selectedDialogue || 
        !hasUnsavedChanges || 
        isGraphLoading || 
        isGraphSaving || 
        isLoadingDialogue ||
        isGenerating) {
      return
    }
    
    const draftKey = `unity_dialogue_draft:${selectedDialogue.filename}`
    const timeoutId = setTimeout(() => {
      try {
        clearDraftError()
        const json_content = exportToUnity()
        const draft = {
          filename: selectedDialogue.filename,
          json_content,
          timestamp: Date.now(),
        }
        localStorage.setItem(draftKey, JSON.stringify(draft))
        markDraftSaved()
      } catch (err) {
        console.error('Erreur lors de l\'auto-save draft:', err)
        const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue'
        markDraftError(errorMessage)
      }
    }, 3000) // Debounce 3s après le dernier changement
    
    return () => clearTimeout(timeoutId)
  }, [selectedDialogue, hasUnsavedChanges, isGraphLoading, isGraphSaving, isLoadingDialogue, isGenerating, exportToUnity, markDraftSaved, markDraftError, clearDraftError])
  
  // Handler pour valider le graphe
  const handleValidate = useCallback(async () => {
    try {
      await validateGraph()
      // Récupérer les erreurs après validation (mise à jour du store)
      const state = useGraphStore.getState()
      const errors = state.validationErrors.filter((e) => e.severity === 'error')
      const warnings = state.validationErrors.filter((e) => e.severity === 'warning')
      
      if (errors.length === 0 && warnings.length === 0) {
        toast('Graphe valide', 'success', 2000)
      } else if (errors.length > 0) {
        toast(`${errors.length} erreur(s) et ${warnings.length} avertissement(s) trouvés`, 'error', 3000)
      } else {
        toast(`${warnings.length} avertissement(s) trouvé(s)`, 'warning', 3000)
      }
    } catch (err) {
      toast(`Erreur lors de la validation: ${getErrorMessage(err)}`, 'error')
    }
  }, [validateGraph, toast])
  
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
      
      // Supprimer le draft après sauvegarde réussie (Task 2 - Story 0.5)
      const draftKey = `unity_dialogue_draft:${selectedDialogue.filename}`
      localStorage.removeItem(draftKey)
      markDraftSaved()
      
      // Rafraîchir la liste
      dialogueListRef.current?.refresh()
    } catch (err) {
      toast(`Erreur lors de la sauvegarde: ${getErrorMessage(err)}`, 'error')
    } finally {
      setIsLoadingDialogue(false)
    }
  }, [selectedDialogue, exportToUnity, toast, markDraftSaved])
  
  // Handlers pour restauration draft (Task 2 - Story 0.5)
  const handleRestoreDraft = useCallback(() => {
    if (draftToRestore && selectedDialogue) {
      setIsLoadingDialogue(true)
      loadDialogue(draftToRestore.json_content)
        .then(() => {
          setShowRestoreDialog(false)
          setDraftToRestore(null)
          setIsLoadingDialogue(false)
          toast('Brouillon restauré', 'success', 2000)
        })
        .catch((err) => {
          console.error('Erreur lors de la restauration du brouillon:', err)
          toast(`Erreur: ${getErrorMessage(err)}`, 'error')
          setIsLoadingDialogue(false)
        })
    }
  }, [draftToRestore, selectedDialogue, loadDialogue, toast])
  
  const handleDiscardDraft = useCallback(() => {
    if (selectedDialogue) {
      const draftKey = `unity_dialogue_draft:${selectedDialogue.filename}`
      localStorage.removeItem(draftKey)
      setShowRestoreDialog(false)
      setDraftToRestore(null)
      
      // Charger le dialogue normal depuis l'API
      setIsLoadingDialogue(true)
      unityDialoguesAPI.getUnityDialogue(selectedDialogue.filename)
        .then((response) => loadDialogue(response.json_content))
        .then(() => {
          setIsLoadingDialogue(false)
          toast('Brouillon supprimé, dialogue du fichier chargé', 'info', 2000)
        })
        .catch((err) => {
          console.error('Erreur lors du chargement du dialogue:', err)
          toast(`Erreur: ${getErrorMessage(err)}`, 'error')
          setIsLoadingDialogue(false)
        })
    }
  }, [selectedDialogue, loadDialogue, toast])
  
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
    ],
    [selectedDialogue, isGraphSaving, handleSave, selectedNodeId, isGraphLoading, isLoadingDialogue]
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
            {/* Badge de santé global du graphe */}
            {(() => {
              const errors = graphValidationErrors.filter((e) => e.severity === 'error')
              const warnings = graphValidationErrors.filter((e) => e.severity === 'warning')
              const hasErrors = errors.length > 0
              const hasWarnings = warnings.length > 0 && !hasErrors
              const isValid = !hasErrors && !hasWarnings
              
              return (
                <div
                  onClick={() => {
                    if (graphValidationErrors.length > 0) {
                      handleValidate()
                    }
                  }}
                  style={{
                    padding: '0.4rem 0.75rem',
                    borderRadius: '6px',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    cursor: graphValidationErrors.length > 0 ? 'pointer' : 'default',
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
                  }}
                  title={isValid 
                    ? 'Graphe valide' 
                    : hasErrors 
                    ? `${errors.length} erreur(s) - Cliquer pour valider` 
                    : `${warnings.length} avertissement(s) - Cliquer pour valider`}
                >
                  <span>{isValid ? '✓' : hasErrors ? '✗' : '⚠'}</span>
                  <span>
                    {isValid 
                      ? 'Graphe valide' 
                      : hasErrors 
                      ? `${errors.length} erreur${errors.length > 1 ? 's' : ''}` 
                      : `${warnings.length} avertissement${warnings.length > 1 ? 's' : ''}`}
                  </span>
                </div>
              )
            })()}
            {/* Indicateur auto-save draft (Task 3 - Story 0.5) */}
            {selectedDialogue && (() => {
              const isWriting = hasUnsavedChanges && !isGraphLoading && !isGraphSaving && !isLoadingDialogue
              const status: 'saved' | 'saving' | 'unsaved' | 'error' = lastDraftError 
                ? 'error' 
                : isWriting 
                ? 'saving' 
                : hasUnsavedChanges 
                ? 'unsaved' 
                : 'saved'
              
              return (
                <SaveStatusIndicator
                  status={status}
                  lastSavedAt={lastDraftSavedAt}
                  errorMessage={lastDraftError}
                />
              )
            })()}
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
              <div style={{ flex: 1, minHeight: 0, overflow: 'hidden' }}>
                <ReactFlowProvider>
                  <GraphCanvas />
                </ReactFlowProvider>
              </div>
            )}
            {/* Panel d'erreurs de validation (overlay) */}
            {graphValidationErrors.length > 0 && (() => {
              const errors = graphValidationErrors.filter((e) => e.severity === 'error')
              const warnings = graphValidationErrors.filter((e) => e.severity === 'warning')
              
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
                      {typeWarnings.map((warn, idx) => (
                        <div
                          key={idx}
                          onClick={() => {
                            if (warn.node_id) {
                              setSelectedNode(warn.node_id)
                            }
                          }}
                          style={{
                            fontSize: '0.75rem',
                            color: theme.state.warning.color,
                            marginBottom: '0.2rem',
                            padding: '0.3rem 0.5rem',
                            borderRadius: '4px',
                            cursor: warn.node_id ? 'pointer' : 'default',
                            backgroundColor: warn.node_id ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
                            transition: 'background-color 0.2s',
                            marginLeft: '1.5rem',
                          }}
                          onMouseEnter={(e) => {
                            if (warn.node_id) {
                              e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.2)'
                            }
                          }}
                          onMouseLeave={(e) => {
                            if (warn.node_id) {
                              e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)'
                            }
                          }}
                        >
                          {warn.node_id ? `[${warn.node_id}] ` : ''}{warn.message}
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              )
            })()}
            
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
      
      {/* Dialog de restauration draft (Task 2 - Story 0.5) */}
      {showRestoreDialog && draftToRestore && (
        <ConfirmDialog
          isOpen={showRestoreDialog}
          title="Brouillon local trouvé"
          message={`Un brouillon plus récent que le fichier a été trouvé pour ce dialogue (sauvegardé ${new Date(draftToRestore.timestamp).toLocaleString()}).\n\nVoulez-vous restaurer le brouillon ?`}
          confirmLabel="Restaurer le brouillon"
          cancelLabel="Charger le fichier"
          onConfirm={handleRestoreDraft}
          onCancel={handleDiscardDraft}
        />
      )}
    </div>
  )
}
