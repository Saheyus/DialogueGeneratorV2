/**
 * Store Zustand pour la gestion de l'état du graphe de dialogues.
 * Gère la conversion Unity JSON ↔ ReactFlow, actions CRUD, undo/redo.
 */
import { create } from 'zustand'
import { temporal } from 'zundo'
import type { Node, Edge } from 'reactflow'
import * as graphAPI from '../api/graph'
import type {
  SaveGraphResponse,
  ValidationErrorDetail,
} from '../types/graph'
import { saveNodePositions, loadNodePositions, type NodePositions } from '../utils/nodePositions'
import {
  getParentChoiceForTestNode,
  syncTestNodeFromChoice,
  syncChoiceFromTestNode,
  TEST_HANDLE_TO_CHOICE_FIELD,
} from '../utils/testNodeSync'
import type { Choice } from '../schemas/nodeEditorSchema'

export interface GraphMetadata {
  title: string
  filename?: string
  node_count: number
  edge_count: number
}

export interface GraphState {
  // Données
  nodes: Node[]
  edges: Edge[]
  selectedNodeId: string | null
  dialogueMetadata: GraphMetadata
  
  // État UI
  isGenerating: boolean
  isLoading: boolean
  isSaving: boolean
  validationErrors: ValidationErrorDetail[]
  highlightedNodeIds: string[] // Pour la recherche
  highlightedCycleNodes: string[] // Pour les nœuds dans des cycles
  intentionalCycles: string[] // IDs des cycles marqués comme intentionnels (persisté localStorage)
  
  // État auto-save draft (Task 1 - Story 0.5)
  hasUnsavedChanges: boolean
  lastDraftSavedAt: number | null
  lastDraftError: string | null
  autoRestoredDraft: { timestamp: number; fileTimestamp: number } | null // Brouillon restauré automatiquement
  
  // Actions CRUD
  loadDialogue: (
    jsonContent: string,
    savedPositions?: Record<string, { x: number; y: number }>,
    filename?: string
  ) => Promise<void>
  addNode: (node: Node) => void
  updateNode: (nodeId: string, updates: Partial<Node>) => void
  deleteNode: (nodeId: string) => void
  connectNodes: (
    sourceId: string,
    targetId: string,
    choiceIndex?: number,
    connectionType?: string
  ) => void
  disconnectNodes: (edgeId: string) => void
  setSelectedNode: (nodeId: string | null) => void
  updateNodePosition: (nodeId: string, position: { x: number; y: number }) => void
  
  // Actions IA
  generateFromNode: (
    parentNodeId: string,
    instructions: string,
    options: Record<string, unknown>
  ) => Promise<{ nodeId: string | null; batchInfo?: {
    generatedChoices: number
    connectedChoices: number
    failedChoices: number
    totalChoices: number
  } }> // Retourne le nodeId du nouveau nœud généré + infos batch
  
  // Validation
  validateGraph: () => Promise<void>
  
  // Persistence
  saveDialogue: () => Promise<SaveGraphResponse>
  exportToUnity: () => string
  
  // Layout
  applyAutoLayout: (algorithm: string, direction: string) => Promise<void>
  
  // Metadata
  updateMetadata: (updates: Partial<GraphMetadata>) => void
  
  // Reset
  resetGraph: () => void
  
  // Recherche
  setHighlightedNodes: (nodeIds: string[]) => void
  
  // Cycles intentionnels
  markCycleAsIntentional: (cycleId: string) => void
  unmarkCycleAsIntentional: (cycleId: string) => void
  
  // Actions auto-save draft (Task 1 - Story 0.5)
  markDirty: () => void
  markDraftSaved: () => void
  markDraftError: (message: string) => void
  clearDraftError: () => void
  setAutoRestoredDraft: (draft: { timestamp: number; fileTimestamp: number } | null) => void
  clearAutoRestoredDraft: () => void

  // Modale confirmation suppression nœud (Supr.)
  showDeleteNodeConfirm: boolean
  setShowDeleteNodeConfirm: (show: boolean) => void
}

const initialState = {
  nodes: [],
  edges: [],
  selectedNodeId: null,
  dialogueMetadata: {
    title: 'Nouveau Dialogue',
    node_count: 0,
    edge_count: 0,
  },
  isGenerating: false,
  isLoading: false,
  isSaving: false,
  validationErrors: [],
  highlightedNodeIds: [],
  highlightedCycleNodes: [],
  intentionalCycles: (() => {
    // Charger depuis localStorage au démarrage
    try {
      const stored = localStorage.getItem('graph_intentional_cycles')
      return stored ? JSON.parse(stored) : []
    } catch {
      return []
    }
  })(),
  hasUnsavedChanges: false,
  lastDraftSavedAt: null,
  lastDraftError: null,
  autoRestoredDraft: null,
  showDeleteNodeConfirm: false,
}

export const useGraphStore = create<GraphState>()(
  temporal(
    (set, get) => ({
      ...initialState,
      
      // Charger un dialogue Unity JSON
      loadDialogue: async (jsonContent: string, savedPositions?: Record<string, { x: number; y: number }>, explicitFilename?: string) => {
        set({ isLoading: true })
        try {
          const response = await graphAPI.loadGraph({ json_content: jsonContent })
          
          // Charger les positions depuis localStorage (clé dédiée)
          // Utiliser le filename passé en paramètre en priorité, sinon celui des métadonnées
          const filename = explicitFilename || response.metadata.filename
          const persistedPositions = filename ? loadNodePositions(filename) : null
          
          // Convertir les nœuds en format ReactFlow
          // Priorité : positions localStorage > positions draft (savedPositions) > positions backend
          const nodes: Node[] = response.nodes.map((node: { id: string; type: string; position: { x: number; y: number }; data: unknown }) => {
            const position = persistedPositions?.[node.id] || savedPositions?.[node.id] || node.position
            return {
              id: node.id,
              type: node.type,
              position,
              data: node.data,
            }
          })
          
          // Convertir les edges
          const edges: Edge[] = response.edges.map((edge: { id: string; source: string; target: string; sourceHandle?: string; targetHandle?: string; label?: string }) => ({
            id: edge.id,
            source: edge.source,
            target: edge.target,
            type: edge.type || 'default',
            label: edge.label,
            data: edge.data,
            ...(edge.sourceHandle && { sourceHandle: edge.sourceHandle }), // Préserver sourceHandle si présent
          }))
          
          set({
            nodes,
            edges,
            dialogueMetadata: {
              title: response.metadata.title,
              node_count: response.metadata.node_count,
              edge_count: response.metadata.edge_count,
              filename: filename, // Utiliser le filename résolu (explicitFilename ou metadata)
            },
            isLoading: false,
            validationErrors: [],
            highlightedCycleNodes: [], // Réinitialiser highlight cycles lors du chargement
            // Réinitialiser l'état auto-save draft (Task 1 - Story 0.5)
            hasUnsavedChanges: false,
            lastDraftSavedAt: null,
            lastDraftError: null,
          })
        } catch (error) {
          console.error('Erreur lors du chargement du graphe:', error)
          set({ isLoading: false })
          throw error
        }
      },
      
      // Ajouter un nœud
      addNode: (node: Node) => {
        const state = get()
        const newNodes = [...state.nodes, node]
        set({
          nodes: newNodes,
          dialogueMetadata: {
            ...state.dialogueMetadata,
            node_count: newNodes.length,
          },
        })
        // Marquer dirty pour auto-save draft (Task 1 - Story 0.5)
        get().markDirty()
      },
      
      // Mettre à jour un nœud
      updateNode: (nodeId: string, updates: Partial<Node>) => {
        set((state) => {
          const node = state.nodes.find((n) => n.id === nodeId)
          if (!node) {
            return state
          }

          // Si c'est un TestNode, rediriger vers le choix parent
          if (node.type === 'testNode') {
            const parent = getParentChoiceForTestNode(nodeId, state.nodes)
            if (parent) {
              // Appliquer les updates au TestNode
              const updatedTestNode = { ...node, ...updates } as Node

              // Synchroniser le choix parent depuis le TestNode (testNode → choice)
              const updatedChoice = syncChoiceFromTestNode(
                updatedTestNode,
                parent.dialogueNodeId,
                parent.choiceIndex,
                parent.choice
              )

              // Mettre à jour le DialogueNode avec le choix modifié
              const updatedDialogueNode = {
                ...parent.dialogueNode,
                data: {
                  ...parent.dialogueNode.data,
                  choices: (parent.dialogueNode.data.choices as Choice[]).map((choice, idx) =>
                    idx === parent.choiceIndex ? updatedChoice : choice
                  ),
                },
              }

              // Remplacer le DialogueNode dans la liste
              const newNodes = state.nodes.map((n) =>
                n.id === parent.dialogueNodeId ? updatedDialogueNode : n
              )

              // Synchroniser le TestNode depuis le choix mis à jour (choice → testNode)
              // pour garantir la cohérence
              const syncResult = syncTestNodeFromChoice(
                updatedChoice,
                parent.choiceIndex,
                parent.dialogueNodeId,
                updatedDialogueNode.position,
                updatedTestNode,
                state.edges,
                newNodes
              )

              // Mettre à jour ou supprimer le TestNode selon le résultat
              let finalNodes = newNodes
              if (syncResult.testNode) {
                // Mettre à jour le TestNode
                finalNodes = finalNodes.map((n) =>
                  n.id === nodeId ? syncResult.testNode! : n
                )
              } else {
                // Supprimer le TestNode (si le test a été supprimé du choix)
                finalNodes = finalNodes.filter((n) => n.id !== nodeId)
              }

              return {
                nodes: finalNodes,
                edges: syncResult.edges,
                dialogueMetadata: {
                  ...state.dialogueMetadata,
                  node_count: finalNodes.length,
                  edge_count: syncResult.edges.length,
                },
              }
            }
            // Si parent non trouvé, retourner state inchangé
            return state
          }

          // Logique existante pour DialogueNode
          const updatedNodes = state.nodes.map((node) =>
            node.id === nodeId ? { ...node, ...updates } : node
          )

          // Trouver le nœud mis à jour
          const updatedNode = updatedNodes.find((n) => n.id === nodeId)
          if (!updatedNode || updatedNode.type !== 'dialogueNode') {
            return { nodes: updatedNodes }
          }

          // Vérifier si un choix a obtenu ou perdu un attribut test
          const updatedData = updatedNode.data as {
            choices?: Choice[]
            [key: string]: unknown
          }
          const choices = updatedData?.choices || []

          const newNodes = [...updatedNodes]
          // Commencer avec les edges existants, mais exclure ceux liés aux TestNodes de ce DialogueNode
          // (ils seront recréés par syncTestNodeFromChoice)
          const testNodeIdsForThisDialogue = choices.map(
            (_, idx) => `test-node-${nodeId}-choice-${idx}`
          )
          let newEdges = state.edges.filter(
            (e) =>
              !testNodeIdsForThisDialogue.includes(e.source) &&
              !testNodeIdsForThisDialogue.includes(e.target)
          )

          // Parcourir tous les choix pour détecter les changements
          choices.forEach((choice: Choice, choiceIndex: number) => {
            const testNodeId = `test-node-${nodeId}-choice-${choiceIndex}`
            const existingTestNode = newNodes.find((n) => n.id === testNodeId)

            // Utiliser syncTestNodeFromChoice pour synchroniser
            // Passer newEdges et newNodes pour vérifier l'existence des nœuds cibles
            // Note: newEdges est accumulé à chaque itération pour préserver les edges des choix précédents
            const syncResult = syncTestNodeFromChoice(
              choice,
              choiceIndex,
              nodeId,
              updatedNode.position,
              existingTestNode || null,
              newEdges,
              newNodes
            )

            // Mettre à jour ou supprimer le TestNode
            if (syncResult.testNode) {
              const testNodeIndex = newNodes.findIndex((n) => n.id === testNodeId)
              if (testNodeIndex !== -1) {
                newNodes[testNodeIndex] = syncResult.testNode
              } else {
                newNodes.push(syncResult.testNode)
              }
            } else {
              // Supprimer le TestNode s'il existe
              const testNodeIndex = newNodes.findIndex((n) => n.id === testNodeId)
              if (testNodeIndex !== -1) {
                newNodes.splice(testNodeIndex, 1)
              }
            }

            // Accumuler les edges : syncResult.edges contient les edges existants passés en paramètre
            // + les nouveaux edges TestNode créés/mis à jour
            // Donc on peut simplement utiliser syncResult.edges qui inclut déjà tout
            newEdges = syncResult.edges

            // Supprimer l'edge directe vers targetNode si elle existe (choix avec test n'a pas de targetNode direct)
            if (choice.targetNode) {
              const directEdgeIndex = newEdges.findIndex(
                (e) =>
                  e.source === nodeId &&
                  e.target === choice.targetNode &&
                  e.sourceHandle === `choice-${choiceIndex}`
              )
              if (directEdgeIndex !== -1) {
                newEdges.splice(directEdgeIndex, 1)
              }
            }
          })

          return {
            nodes: newNodes,
            edges: newEdges,
            dialogueMetadata: {
              ...state.dialogueMetadata,
              node_count: newNodes.length,
              edge_count: newEdges.length,
            },
          }
        })
        // Marquer dirty pour auto-save draft (Task 1 - Story 0.5)
        get().markDirty()
      },
      
      // Supprimer un nœud
      deleteNode: (nodeId: string) => {
        set((state) => {
          // Si c'est un TestNode, supprimer le test du choix parent
          if (nodeId.startsWith('test-node-')) {
            const parent = getParentChoiceForTestNode(nodeId, state.nodes)
            
            if (parent) {
              // Supprimer le champ test et tous les champs test*Node du choix
              const updatedChoices = (parent.dialogueNode.data.choices as Choice[]).map(
                (choice, idx) => {
                  if (idx === parent.choiceIndex) {
                    const { test, testCriticalFailureNode, testFailureNode, testSuccessNode, testCriticalSuccessNode, ...rest } = choice
                    return rest
                  }
                  return choice
                }
              )

              // Mettre à jour le DialogueNode avec le choix modifié
              const updatedDialogueNode = {
                ...parent.dialogueNode,
                data: {
                  ...parent.dialogueNode.data,
                  choices: updatedChoices,
                },
              }

              // Remplacer le DialogueNode dans la liste
              const newNodes = state.nodes.map((n) =>
                n.id === parent.dialogueNodeId ? updatedDialogueNode : n
              )

              // Supprimer le TestNode et toutes ses edges
              const finalNodes = newNodes.filter((n) => n.id !== nodeId)
              const newEdges = state.edges.filter(
                (e) => e.source !== nodeId && e.target !== nodeId
              )

              // Mettre à jour selectedNodeId si le TestNode était sélectionné
              const selectedNodeToRemove = state.selectedNodeId === nodeId
              
              // Si le TestNode était sélectionné, sélectionner automatiquement le DialogueNode parent
              // pour que l'utilisateur voie que le test a été supprimé du choix
              const newSelectedNodeId = selectedNodeToRemove 
                ? parent.dialogueNodeId  // Sélectionner le DialogueNode parent
                : state.selectedNodeId

              return {
                nodes: finalNodes,
                edges: newEdges,
                selectedNodeId: newSelectedNodeId,
                dialogueMetadata: {
                  ...state.dialogueMetadata,
                  node_count: finalNodes.length,
                  edge_count: newEdges.length,
                },
              }
            }
            // Si parent non trouvé, supprimer simplement le TestNode
            const newNodes = state.nodes.filter((n) => n.id !== nodeId)
            const newEdges = state.edges.filter(
              (e) => e.source !== nodeId && e.target !== nodeId
            )
            const selectedNodeToRemove = state.selectedNodeId === nodeId

            return {
              nodes: newNodes,
              edges: newEdges,
              selectedNodeId: selectedNodeToRemove ? null : state.selectedNodeId,
              dialogueMetadata: {
                ...state.dialogueMetadata,
                node_count: newNodes.length,
                edge_count: newEdges.length,
              },
            }
          }

          // Logique existante pour DialogueNode : supprimer le nœud et tous ses TestNodes associés
          // Identifier les TestNodes associés (format: test-node-{nodeId}-choice-{index})
          const testNodePrefix = `test-node-${nodeId}-`
          const associatedTestNodeIds = state.nodes
            .filter((n) => n.id.startsWith(testNodePrefix))
            .map((n) => n.id)

          // Supprimer le nœud principal et tous les TestNodes associés
          const nodesToDelete = [nodeId, ...associatedTestNodeIds]
          const newNodes = state.nodes.filter((n) => !nodesToDelete.includes(n.id))

          // Supprimer aussi les edges liés (source ou target = nodeId ou TestNode associé)
          const newEdges = state.edges.filter(
            (e) => !nodesToDelete.includes(e.source) && !nodesToDelete.includes(e.target)
          )

          // Mettre à jour le selectedNodeId si le nœud supprimé ou un TestNode associé était sélectionné
          const selectedNodeToRemove = nodesToDelete.includes(state.selectedNodeId || '')

          return {
            nodes: newNodes,
            edges: newEdges,
            selectedNodeId: selectedNodeToRemove ? null : state.selectedNodeId,
            dialogueMetadata: {
              ...state.dialogueMetadata,
              node_count: newNodes.length,
              edge_count: newEdges.length,
            },
          }
        })
        // Marquer dirty pour auto-save draft (Task 1 - Story 0.5)
        get().markDirty()
      },
      
      // Connecter deux nœuds
      connectNodes: (
        sourceId: string,
        targetId: string,
        choiceIndex?: number,
        connectionType: string = 'default',
        sourceHandle?: string
      ) => {
        const state = get()
        
        // Extraire le sourceHandle depuis connectionType si c'est un type de test
        let actualSourceHandle = sourceHandle
        if (!actualSourceHandle && connectionType.startsWith('test-')) {
          actualSourceHandle = connectionType.replace('test-', '')
        }
        
        // Générer un ID unique pour l'edge
        const edgeId = actualSourceHandle
          ? `${sourceId}-${actualSourceHandle}-${targetId}`
          : choiceIndex !== undefined
          ? `${sourceId}-choice${choiceIndex}->${targetId}`
          : `${sourceId}->${targetId}`
        
        // Vérifier si l'edge existe déjà
        if (state.edges.some((e) => e.id === edgeId)) {
          return
        }
        
        // Créer le nouvel edge
        const newEdge: Edge = {
          id: edgeId,
          source: sourceId,
          target: targetId,
          ...(actualSourceHandle && { sourceHandle: actualSourceHandle }), // Utiliser sourceHandle si fourni (pour TestNodes)
          ...(!actualSourceHandle && choiceIndex !== undefined && { sourceHandle: `choice-${choiceIndex}` }), // Correspond à l'ID du handle dans DialogueNode
          type: 'default',
          data: {
            edgeType: connectionType,
            choiceIndex,
          },
        }
        
        let newEdges = [...state.edges, newEdge]
        
        // Mettre à jour les nœuds selon le type de connexion
        let updatedNodes = [...state.nodes]
        const sourceNodeIndex = updatedNodes.findIndex((n) => n.id === sourceId)
        
        if (sourceNodeIndex !== -1) {
          const sourceNode = updatedNodes[sourceNodeIndex]
          
          // Gérer les connexions depuis un TestNode (avec sourceHandle pour les 4 résultats)
          if (actualSourceHandle && (actualSourceHandle === 'critical-failure' || actualSourceHandle === 'failure' || actualSourceHandle === 'success' || actualSourceHandle === 'critical-success')) {
            // Trouver le choix parent du TestNode
            const parent = getParentChoiceForTestNode(sourceId, state.nodes)
            if (parent && TEST_HANDLE_TO_CHOICE_FIELD[actualSourceHandle]) {
              // Mettre à jour le champ test*Node dans le choix parent (Source of Truth)
              const fieldName = TEST_HANDLE_TO_CHOICE_FIELD[actualSourceHandle]
              const updatedChoices = (parent.dialogueNode.data.choices as Choice[]).map(
                (choice, idx) =>
                  idx === parent.choiceIndex
                    ? { ...choice, [fieldName]: targetId }
                    : choice
              )

              // Mettre à jour le DialogueNode avec le choix modifié
              const updatedDialogueNode = {
                ...parent.dialogueNode,
                data: {
                  ...parent.dialogueNode.data,
                  choices: updatedChoices,
                },
              }

              // Remplacer le DialogueNode dans la liste
              updatedNodes = updatedNodes.map((n) =>
                n.id === parent.dialogueNodeId ? updatedDialogueNode : n
              )

              // Synchroniser le TestNode depuis le choix mis à jour (choice → testNode)
              const updatedChoice = updatedChoices[parent.choiceIndex]
              const syncResult = syncTestNodeFromChoice(
                updatedChoice,
                parent.choiceIndex,
                parent.dialogueNodeId,
                updatedDialogueNode.position,
                sourceNode,
                newEdges,
                updatedNodes
              )

              // Mettre à jour le TestNode
              if (syncResult.testNode) {
                updatedNodes = updatedNodes.map((n) =>
                  n.id === sourceId ? syncResult.testNode! : n
                )
              }

              // Mettre à jour les edges avec ceux retournés par syncTestNodeFromChoice
              newEdges = syncResult.edges
            } else {
              // Fallback : mettre à jour le champ correspondant dans le TestNode (pour compatibilité)
              const fieldMapping: Record<string, string> = {
                'critical-failure': 'criticalFailureNode',
                'failure': 'failureNode',
                'success': 'successNode',
                'critical-success': 'criticalSuccessNode',
              }
              const fieldName = fieldMapping[actualSourceHandle]
              if (fieldName) {
                updatedNodes[sourceNodeIndex] = {
                  ...sourceNode,
                  data: {
                    ...sourceNode.data,
                    [fieldName]: targetId,
                  },
                }
              }
            }
          } else if (choiceIndex !== undefined) {
            // Connexion via choix (DialogueNode)
            if (sourceNode.data?.choices && sourceNode.data.choices[choiceIndex]) {
              // Mettre à jour targetNode dans le choix
              updatedNodes[sourceNodeIndex] = {
                ...sourceNode,
                data: {
                  ...sourceNode.data,
                  choices: (sourceNode.data.choices as Array<{ targetNode?: string; [key: string]: unknown }>).map((choice, idx: number) =>
                    idx === choiceIndex
                      ? { ...choice, targetNode: targetId }
                      : choice
                  ),
                },
              }
            }
          } else if (connectionType === 'nextNode') {
            // Mettre à jour nextNode dans le parent pour navigation linéaire
            updatedNodes[sourceNodeIndex] = {
              ...sourceNode,
              data: {
                ...sourceNode.data,
                nextNode: targetId,
              },
            }
          }
        }
        
        set({
          nodes: updatedNodes,
          edges: newEdges,
          dialogueMetadata: {
            ...state.dialogueMetadata,
            node_count: updatedNodes.length,
            edge_count: newEdges.length,
          },
        })
        // Marquer dirty pour auto-save draft (Task 1 - Story 0.5)
        get().markDirty()
      },
      
      // Déconnecter deux nœuds
      disconnectNodes: (edgeId: string) => {
        set((state) => {
          const edge = state.edges.find((e) => e.id === edgeId)
          if (!edge) {
            return state
          }

          // Si déconnexion depuis un TestNode, mettre à jour le choix parent
          if (edge.sourceHandle && edge.source.startsWith('test-node-')) {
            const parent = getParentChoiceForTestNode(edge.source, state.nodes)
            if (parent && TEST_HANDLE_TO_CHOICE_FIELD[edge.sourceHandle]) {
              // Supprimer le champ test*Node dans le choix parent (Source of Truth)
              const fieldName = TEST_HANDLE_TO_CHOICE_FIELD[edge.sourceHandle]
              const updatedChoices = (parent.dialogueNode.data.choices as Choice[]).map(
                (choice, idx) => {
                  if (idx === parent.choiceIndex) {
                    const { [fieldName]: _, ...rest } = choice
                    return rest
                  }
                  return choice
                }
              )

              // Mettre à jour le DialogueNode avec le choix modifié
              const updatedDialogueNode = {
                ...parent.dialogueNode,
                data: {
                  ...parent.dialogueNode.data,
                  choices: updatedChoices,
                },
              }

              // Remplacer le DialogueNode dans la liste
              let updatedNodes = state.nodes.map((n) =>
                n.id === parent.dialogueNodeId ? updatedDialogueNode : n
              )

              // Supprimer l'edge
              const newEdges = state.edges.filter((e) => e.id !== edgeId)

              // Synchroniser le TestNode depuis le choix mis à jour (choice → testNode)
              const updatedChoice = updatedChoices[parent.choiceIndex]
              const testNode = updatedNodes.find((n) => n.id === edge.source)
              const syncResult = syncTestNodeFromChoice(
                updatedChoice,
                parent.choiceIndex,
                parent.dialogueNodeId,
                updatedDialogueNode.position,
                testNode || null,
                newEdges,
                updatedNodes
              )

              // Mettre à jour le TestNode
              if (syncResult.testNode) {
                updatedNodes = updatedNodes.map((n) =>
                  n.id === edge.source ? syncResult.testNode! : n
                )
              }

              return {
                nodes: updatedNodes,
                edges: syncResult.edges,
                dialogueMetadata: {
                  ...state.dialogueMetadata,
                  node_count: updatedNodes.length,
                  edge_count: syncResult.edges.length,
                },
              }
            }
          }

          // Logique existante : supprimer simplement l'edge
          const newEdges = state.edges.filter((e) => e.id !== edgeId)

          return {
            edges: newEdges,
            dialogueMetadata: {
              ...state.dialogueMetadata,
              edge_count: newEdges.length,
            },
          }
        })
        // Marquer dirty pour auto-save draft (Task 1 - Story 0.5)
        get().markDirty()
      },
      
      // Sélectionner un nœud
      setSelectedNode: (nodeId: string | null) => {
        set({ selectedNodeId: nodeId })
      },
      
      // Mettre à jour la position d'un nœud
      updateNodePosition: (nodeId: string, position: { x: number; y: number }) => {
        const state = get()
        const node = state.nodes.find((n) => n.id === nodeId)
        
        // Ne marquer dirty que si la position a vraiment changé (évite faux positifs)
        const positionChanged = !node || 
          Math.abs(node.position.x - position.x) > 0.1 || 
          Math.abs(node.position.y - position.y) > 0.1
        
        set({
          nodes: state.nodes.map((n) =>
            n.id === nodeId ? { ...n, position } : n
          ),
        })
        
        // Marquer dirty pour auto-save draft SEULEMENT si position a changé (Task 1 - Story 0.5)
        if (positionChanged) {
          get().markDirty()
          
          // Sauvegarder immédiatement les positions dans localStorage (clé dédiée)
          const filename = state.dialogueMetadata.filename
          if (filename) {
            const positions: NodePositions = {}
            state.nodes.forEach((n) => {
              positions[n.id] = n.id === nodeId ? position : n.position
            })
            saveNodePositions(filename, positions)
          }
        }
      },
      
      // Générer un nœud depuis un parent avec l'IA
      generateFromNode: async (
        parentNodeId: string,
        instructions: string,
        options: Record<string, unknown>
      ) => {
        set({ isGenerating: true })
        try {
          const state = get()
          const parentNode = state.nodes.find((n) => n.id === parentNodeId)
          
          if (!parentNode) {
            throw new Error(`Nœud parent ${parentNodeId} introuvable`)
          }
          
          // Si on génère depuis un TestNode, trouver le DialogueNode parent
          let parentNodeContent = parentNode.data
          if (parentNode.type === 'testNode' || parentNodeId.startsWith('test-node-')) {
            // Format: test-node-{parent_id}-choice-{index}
            const parts = parentNodeId.replace('test-node-', '').split('-choice-')
            if (parts.length === 2) {
              const parentDialogueId = parts[0]
              const parentDialogueNode = state.nodes.find((n) => n.id === parentDialogueId)
              if (parentDialogueNode) {
                // Enrichir les données du TestNode avec les données du DialogueNode parent
                parentNodeContent = {
                  ...parentNode.data,
                  type: 'testNode',
                  parent_speaker: parentDialogueNode.data?.speaker || 'PNJ',
                  parent_line: parentDialogueNode.data?.line || '',
                }
              }
            }
          }
          
          // Appeler l'API pour générer le nœud
          const response = await graphAPI.generateNode({
            parent_node_id: parentNodeId,
            parent_node_content: parentNodeContent,
            user_instructions: instructions,
            context_selections: options.context_selections || {},
            max_choices: options.max_choices,
            npc_speaker_id: options.npc_speaker_id,
            system_prompt_override: options.system_prompt_override,
            narrative_tags: options.narrative_tags,
            llm_model_identifier: options.llm_model_identifier,
            target_choice_index: options.target_choice_index ?? null,
            generate_all_choices: options.generate_all_choices ?? false,
          })
          
          // Gérer génération batch (si generate_all_choices, l'API retourne une liste)
          // OU si TestNode (génère toujours 4 nœuds pour les résultats de test)
          // Utiliser response.nodes si disponible (batch ou TestNode), sinon response.node (backward compatibility)
          const isTestNode = parentNodeId.startsWith('test-node-')
          const isBatch = options.generate_all_choices ?? false
          const hasMultipleNodes = response.nodes && response.nodes.length > 0
          
          const generatedNodes = hasMultipleNodes
            ? response.nodes 
            : (response.node ? [response.node] : [])
          
          // Ajouter les nouveaux nœuds avec positionnement en cascade pour batch
          const generatedNodeIds: string[] = []
          
          // Pour TestNodes, les connexions utilisent connection_type au lieu de via_choice_index
          // Pour batch normal, utiliser via_choice_index
          const connectionMap = new Map<number | string, { node: Record<string, unknown>, conn: { to: string; via_choice_index?: number; connection_type?: string; [key: string]: unknown } }>()
          for (const conn of response.suggested_connections) {
            const node = generatedNodes.find((n) => n.id === conn.to)
            if (node) {
              // Pour TestNodes, utiliser connection_type comme clé
              // Pour batch normal, utiliser via_choice_index
              const mapKey = isTestNode && conn.connection_type 
                ? conn.connection_type 
                : (conn.via_choice_index !== undefined ? conn.via_choice_index : `conn-${conn.to}`)
              connectionMap.set(mapKey, { node, conn })
            }
          }
          
          // Trier les connexions pour positionnement cascade
          // Pour TestNodes, ordre fixe: critical-failure, failure, success, critical-success
          // Pour batch normal, trier par via_choice_index
          let nodesToAdd: Array<{ node: Record<string, unknown>, choiceIndex: number }>
          if (isTestNode) {
            // Ordre fixe pour TestNodes
            const testOrder = ['test-critical-failure', 'test-failure', 'test-success', 'test-critical-success']
            nodesToAdd = testOrder
              .map((connType, index) => {
                const entry = connectionMap.get(connType)
                return entry ? { node: entry.node, choiceIndex: index } : null
              })
              .filter((item): item is { node: Record<string, unknown>, choiceIndex: number } => item !== null)
            // Ajouter les nœuds non mappés
            const mappedNodeIds = new Set(nodesToAdd.map(({ node }) => node.id))
            for (const node of generatedNodes) {
              if (!mappedNodeIds.has(node.id)) {
                nodesToAdd.push({ node, choiceIndex: nodesToAdd.length })
              }
            }
          } else {
            // Pour batch normal, trier par via_choice_index
            const sortedConnections = Array.from(connectionMap.entries())
              .filter(([key]) => typeof key === 'number')
              .sort((a, b) => (a[0] as number) - (b[0] as number))
            nodesToAdd = sortedConnections.length > 0
              ? sortedConnections.map(([choiceIndex, { node }]) => ({ node, choiceIndex: choiceIndex as number }))
              : generatedNodes.map((node, index) => ({ node, choiceIndex: index }))
          }
          
          const totalToAdd = nodesToAdd.length
          
          // Initialiser la progression si batch ou TestNode avec plusieurs nœuds
          if ((isBatch || (isTestNode && totalToAdd > 1)) && typeof options.onBatchProgress === 'function' && totalToAdd > 0) {
            options.onBatchProgress(0, totalToAdd)
          }
          
          // Ajouter les nœuds et mettre à jour la progression
          // Utiliser un batch update pour éviter les re-renders multiples
          const nodesToAddBatch: Node[] = []
          nodesToAdd.forEach(({ node: generatedNode, choiceIndex }, index) => {
            const isBatchOrTestNode = isBatch || (isTestNode && totalToAdd > 1)
            const isChoiceSpecific = !isBatchOrTestNode && options.target_choice_index !== undefined && options.target_choice_index !== null
            const verticalOffset = isBatchOrTestNode
              ? 150 * choiceIndex
              : (isChoiceSpecific ? (60 * choiceIndex) + 60 : 0)
            const newNode: Node = {
              id: generatedNode.id,
              type: 'dialogueNode',
              position: {
                x: parentNode.position.x + 300,
                // Positionnement en cascade verticale pour batch (offset Y = 150 * index_choice)
                y: parentNode.position.y + verticalOffset,
              },
              data: generatedNode,
            }
            
            nodesToAddBatch.push(newNode)
            generatedNodeIds.push(generatedNode.id)
            
            // Mettre à jour la progression (appelé pour chaque nœud pour feedback progressif)
            if (isBatchOrTestNode && typeof options.onBatchProgress === 'function' && totalToAdd > 0) {
              options.onBatchProgress(index + 1, totalToAdd)
            }
          })
          
          // Ajouter tous les nœuds en une seule opération pour un re-render unique
          const currentState = get()
          const newNodes = [...currentState.nodes, ...nodesToAddBatch]
          set({
            nodes: newNodes,
            dialogueMetadata: {
              ...currentState.dialogueMetadata,
              node_count: newNodes.length,
            },
          })

          // Créer les connexions suggérées (appliquer automatiquement)
          for (const conn of response.suggested_connections) {
            // Appliquer automatiquement les connexions (mise à jour targetNode dans parent)
            get().connectNodes(
              conn.from,
              conn.to,
              conn.via_choice_index,
              conn.connection_type
            )
          }

          // Marquer la génération comme terminée APRÈS avoir ajouté tous les nœuds
          // Cela permet à la modale de se fermer et aux nœuds d'être visibles immédiatement
          set({ isGenerating: false })
          
          // Retourner le nodeId du premier nouveau nœud pour feedback visuel
          // Note: Pour batch, on retourne l'ID du premier nœud, mais tous les nœuds sont ajoutés
          const firstNodeId = generatedNodeIds[0] || generatedNodes[0]?.id
          const batchInfo = options.generate_all_choices ? {
            generatedChoices: response.generated_choices_count ?? generatedNodes.length,
            connectedChoices: response.connected_choices_count ?? 0,
            failedChoices: response.failed_choices_count ?? 0,
            totalChoices: response.total_choices_count ?? (parentNode.data?.choices?.length ?? 0),
          } : undefined
          
          // Logger le résultat batch si applicable
          if (options.generate_all_choices && response.batch_count) {
            console.log(`Génération batch: ${response.batch_count} nœud(s) généré(s)`)
          }
          
          return { nodeId: firstNodeId ?? null, batchInfo }
        } catch (error: any) {
          console.error('Erreur lors de la génération de nœud:', error)
          set({ isGenerating: false })
          throw error
        }
      },
      
      // Valider le graphe
      validateGraph: async () => {
        try {
          const state = get()
          const response = await graphAPI.validateGraph({
            nodes: state.nodes.map((n) => ({
              id: n.id,
              type: n.type,
              position: n.position,
              data: n.data,
            })),
            edges: state.edges.map((e) => ({
              id: e.id,
              source: e.source,
              target: e.target,
              type: e.type,
              label: e.label,
              data: e.data,
            })),
          })
          
          // Extraire les nœuds des cycles depuis les warnings
          const cycleWarnings = response.warnings.filter(
            (w) => w.type === 'cycle_detected' && w.cycle_nodes && Array.isArray(w.cycle_nodes)
          )
          const cycleNodeIds = new Set<string>()
          cycleWarnings.forEach((warn) => {
            if (warn.cycle_nodes && Array.isArray(warn.cycle_nodes)) {
              warn.cycle_nodes.forEach((nodeId) => cycleNodeIds.add(nodeId))
            }
          })
          
          set({
            validationErrors: [...response.errors, ...response.warnings],
            // Réinitialiser highlightedCycleNodes même s'il n'y a pas de cycles (AC #4)
            highlightedCycleNodes: Array.from(cycleNodeIds),
          })
        } catch (error) {
          console.error('Erreur lors de la validation:', error)
          throw error
        }
      },
      
      // Sauvegarder le dialogue
      saveDialogue: async () => {
        set({ isSaving: true })
        try {
          const state = get()
          const response = await graphAPI.saveGraph({
            nodes: state.nodes.map((n) => ({
              id: n.id,
              type: n.type,
              position: n.position,
              data: n.data,
            })),
            edges: state.edges.map((e) => ({
              id: e.id,
              source: e.source,
              target: e.target,
              type: e.type,
              label: e.label,
              data: e.data,
            })),
            metadata: state.dialogueMetadata,
          })
          
          set({
            isSaving: false,
            dialogueMetadata: {
              ...state.dialogueMetadata,
              filename: response.filename,
            },
          })
          
          return response
        } catch (error) {
          console.error('Erreur lors de la sauvegarde:', error)
          set({ isSaving: false })
          throw error
        }
      },
      
      // Exporter en Unity JSON
      // ⚠️ ATTENTION: Cette méthode utilise une logique locale simplifiée pour le draft local uniquement.
      // Elle NE gère PAS les TestNodes avec 4 résultats (testCriticalFailureNode, testCriticalSuccessNode).
      // Pour un export canonique avec validation complète, utilisez saveDialogue() qui appelle l'API /save.
      exportToUnity: () => {
        const state = get()
        
        // Reconvertir les nœuds ReactFlow en Unity JSON
        const unityNodes = state.nodes.map((node) => {
          const unityNode = { ...node.data }
          
          // Ignorer les TestNodes (ils ne sont pas dans le JSON Unity, seulement les champs test*Node dans les choix)
          if (node.type === 'testNode') {
            return null
          }
          
          // Nettoyer les champs de navigation (seront recréés depuis les edges)
          delete unityNode.nextNode
          delete unityNode.successNode
          delete unityNode.failureNode
          
          if (unityNode.choices) {
            unityNode.choices = (unityNode.choices as Array<{ targetNode?: string; [key: string]: unknown }>).map((choice) => {
              const cleanChoice = { ...choice }
              delete cleanChoice.targetNode
              // Note: Cette logique locale ne reconstruit PAS les 4 résultats de test correctement
              // (testCriticalFailureNode, testCriticalSuccessNode ne sont pas gérés)
              return cleanChoice
            })
          }
          
          return unityNode
        }).filter((node) => node !== null) // Filtrer les TestNodes
        
        // Reconstruire les connexions depuis les edges
        // ⚠️ Cette logique simplifiée ne gère pas les TestNodes avec 4 résultats
        for (const edge of state.edges) {
          const sourceNode = unityNodes.find((n) => n && n.id === edge.source)
          if (!sourceNode) continue
          
          const edgeType = edge.data?.edgeType
          const choiceIndex = edge.data?.choiceIndex
          
          if (edgeType === 'success') {
            sourceNode.successNode = edge.target
          } else if (edgeType === 'failure') {
            sourceNode.failureNode = edge.target
          } else if (edgeType === 'choice' && choiceIndex !== undefined) {
            if (sourceNode.choices && sourceNode.choices[choiceIndex]) {
              sourceNode.choices[choiceIndex].targetNode = edge.target
            }
          } else {
            // Edge par défaut (nextNode)
            if (!sourceNode.choices && !sourceNode.test) {
              sourceNode.nextNode = edge.target
            }
          }
        }
        
        return JSON.stringify(unityNodes, null, 2)
      },
      
      // Appliquer un auto-layout
      applyAutoLayout: async (algorithm: string, direction: string) => {
        try {
          const state = get()
          
          // Si Dagre, calculer côté frontend
          if (algorithm === 'dagre') {
            const { calculateDagreLayout } = await import('../utils/dagreLayout')
            const layoutedNodes = calculateDagreLayout(
              state.nodes,
              state.edges,
              { direction: direction as 'TB' | 'LR' | 'BT' | 'RL' }
            )
            
            // Mettre à jour les positions
            set({ nodes: layoutedNodes })
            return
          }
          
          // Sinon, utiliser l'API backend (fallback pour autres algorithmes)
          const response = await graphAPI.calculateLayout({
            nodes: state.nodes.map((n) => ({
              id: n.id,
              type: n.type,
              position: n.position,
              data: n.data,
            })),
            edges: state.edges.map((e) => ({
              id: e.id,
              source: e.source,
              target: e.target,
              type: e.type,
              label: e.label,
              data: e.data,
            })),
            algorithm,
            direction,
          })
          
          // Mettre à jour les positions
          set((state) => ({
            nodes: state.nodes.map((node) => {
              const layoutedNode = response.nodes.find((n: { id: string; position: { x: number; y: number }; [key: string]: unknown }) => n.id === node.id)
              return layoutedNode
                ? { ...node, position: layoutedNode.position }
                : node
            }),
          }))
        } catch (error) {
          console.error('Erreur lors du calcul de layout:', error)
          throw error
        }
      },
      
      // Mettre à jour les métadonnées
      updateMetadata: (updates: Partial<GraphMetadata>) => {
        set((state) => ({
          dialogueMetadata: {
            ...state.dialogueMetadata,
            ...updates,
          },
        }))
        // Marquer dirty pour auto-save draft (Task 1 - Story 0.5)
        get().markDirty()
      },
      
      // Réinitialiser le graphe
      resetGraph: () => {
        set(initialState)
      },
      
      // Définir les nœuds en surbrillance (pour la recherche)
      setHighlightedNodes: (nodeIds: string[]) => {
        set({ highlightedNodeIds: nodeIds })
      },
      
      // Marquer un cycle comme intentionnel
      markCycleAsIntentional: (cycleId: string) => {
        set((state) => {
          const newIntentionalCycles = state.intentionalCycles.includes(cycleId)
            ? state.intentionalCycles
            : [...state.intentionalCycles, cycleId]
          
          // Persister dans localStorage
          try {
            localStorage.setItem('graph_intentional_cycles', JSON.stringify(newIntentionalCycles))
          } catch (error) {
            console.error('Erreur lors de la sauvegarde des cycles intentionnels:', error)
            // Afficher une notification à l'utilisateur si localStorage est plein
            if (error instanceof DOMException && error.name === 'QuotaExceededError') {
              alert('Impossible de sauvegarder le marquage intentionnel: l\'espace de stockage est plein. Veuillez libérer de l\'espace.')
            }
          }
          
          return { intentionalCycles: newIntentionalCycles }
        })
      },
      
      // Décocher un cycle intentionnel
      unmarkCycleAsIntentional: (cycleId: string) => {
        set((state) => {
          const newIntentionalCycles = state.intentionalCycles.filter((id) => id !== cycleId)
          
          // Persister dans localStorage
          try {
            localStorage.setItem('graph_intentional_cycles', JSON.stringify(newIntentionalCycles))
          } catch (error) {
            console.error('Erreur lors de la sauvegarde des cycles intentionnels:', error)
            // Afficher une notification à l'utilisateur si localStorage est plein
            if (error instanceof DOMException && error.name === 'QuotaExceededError') {
              alert('Impossible de sauvegarder le marquage intentionnel: l\'espace de stockage est plein. Veuillez libérer de l\'espace.')
            }
          }
          
          return { intentionalCycles: newIntentionalCycles }
        })
      },
      
      // Actions auto-save draft (Task 1 - Story 0.5)
      markDirty: () => {
        set({ hasUnsavedChanges: true })
      },
      
      markDraftSaved: () => {
        set({
          hasUnsavedChanges: false,
          lastDraftSavedAt: Date.now(),
        })
      },
      
      markDraftError: (message: string) => {
        set({
          lastDraftError: message,
          hasUnsavedChanges: false,
        })
      },
      
      clearDraftError: () => {
        set({ lastDraftError: null })
      },
      
      setAutoRestoredDraft: (draft: { timestamp: number; fileTimestamp: number } | null) => {
        set({ autoRestoredDraft: draft })
      },
      
      clearAutoRestoredDraft: () => {
        set({ autoRestoredDraft: null })
      },

      setShowDeleteNodeConfirm: (show: boolean) => {
        set({ showDeleteNodeConfirm: show })
      },
    }),
    {
      // Configuration du middleware temporal (undo/redo)
      limit: 50, // Historique de 50 actions
      equality: (a, b) => a === b,
      // Partialiser pour ne pas historiser certains champs UI transitoires
      partialize: (state): Partial<GraphState> => {
        const {
          isGenerating: _isGenerating,
          isLoading: _isLoading,
          isSaving: _isSaving,
          validationErrors: _validationErrors,
          highlightedNodeIds: _highlightedNodeIds,
          showDeleteNodeConfirm: _showDeleteNodeConfirm,
          ...rest
        } = state
        return rest
      },
    }
  )
)

// Export des actions undo/redo depuis zundo
export const { undo, redo, clear: clearHistory } = useGraphStore.temporal.getState()
