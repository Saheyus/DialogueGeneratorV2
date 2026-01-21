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
    options: any
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
          const nodes: Node[] = response.nodes.map((node: any) => {
            const position = persistedPositions?.[node.id] || savedPositions?.[node.id] || node.position
            return {
              id: node.id,
              type: node.type,
              position,
              data: node.data,
            }
          })
          
          // Convertir les edges
          const edges: Edge[] = response.edges.map((edge: any) => ({
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
          const updatedNodes = state.nodes.map((node) =>
            node.id === nodeId ? { ...node, ...updates } : node
          )
          
          // Trouver le nœud mis à jour
          const updatedNode = updatedNodes.find((n) => n.id === nodeId)
          if (!updatedNode || updatedNode.type !== 'dialogueNode') {
            return { nodes: updatedNodes }
          }
          
          // Vérifier si un choix a obtenu ou perdu un attribut test
          const updatedData = updatedNode.data as any
          const choices = updatedData?.choices || []
          
          const newNodes = [...updatedNodes]
          const newEdges = [...state.edges]
          
          // Parcourir tous les choix pour détecter les changements
          choices.forEach((choice: any, choiceIndex: number) => {
            const testNodeId = `test-node-${nodeId}-choice-${choiceIndex}`
            const existingTestNode = newNodes.find((n) => n.id === testNodeId)
            const existingEdge = newEdges.find(
              (e) => e.source === nodeId && e.target === testNodeId && e.sourceHandle === `choice-${choiceIndex}`
            )
            
            if (choice.test) {
              // Le choix a un test : créer le TestNode s'il n'existe pas
              if (!existingTestNode) {
                // Calculer la position du TestNode (à droite du DialogueNode)
                const dialogueNode = updatedNode
                const testNodePosition = {
                  x: (dialogueNode.position?.x || 0) + 300,
                  y: (dialogueNode.position?.y || 0) - 150 + (choiceIndex * 200),
                }
                
                // Créer le TestNode
                newNodes.push({
                  id: testNodeId,
                  type: 'testNode',
                  position: testNodePosition,
                  data: {
                    id: testNodeId,
                    test: choice.test,
                    line: choice.text || '',
                    criticalFailureNode: choice.testCriticalFailureNode,
                    failureNode: choice.testFailureNode,
                    successNode: choice.testSuccessNode,
                    criticalSuccessNode: choice.testCriticalSuccessNode,
                  },
                })
              } else {
                // Mettre à jour le TestNode existant avec les nouvelles données
                const testNodeIndex = newNodes.findIndex((n) => n.id === testNodeId)
                if (testNodeIndex !== -1) {
                  newNodes[testNodeIndex] = {
                    ...newNodes[testNodeIndex],
                    data: {
                      ...newNodes[testNodeIndex].data,
                      test: choice.test,
                      line: choice.text || '',
                      criticalFailureNode: choice.testCriticalFailureNode,
                      failureNode: choice.testFailureNode,
                      successNode: choice.testSuccessNode,
                      criticalSuccessNode: choice.testCriticalSuccessNode,
                    },
                  }
                }
              }
              
              // Créer l'edge DialogueNode → TestNode s'il n'existe pas
              if (!existingEdge) {
                const choiceText = choice.text || `Choix ${choiceIndex + 1}`
                // Tronquer le label pour l'affichage (comme pour les autres edges)
                const truncatedLabel = choiceText.length > 30 ? `${choiceText.substring(0, 30)}...` : choiceText
                newEdges.push({
                  id: `${nodeId}-choice-${choiceIndex}-to-test`,
                  source: nodeId,
                  target: testNodeId,
                  sourceHandle: `choice-${choiceIndex}`,
                  type: 'smoothstep',
                  label: truncatedLabel,
                })
              }
              
              // Créer les edges TestNode → nœuds de résultat (si les nœuds existent)
              const testResults = [
                { field: 'testCriticalFailureNode', handleId: 'critical-failure', color: '#C0392B', label: 'Échec critique' },
                { field: 'testFailureNode', handleId: 'failure', color: '#E74C3C', label: 'Échec' },
                { field: 'testSuccessNode', handleId: 'success', color: '#27AE60', label: 'Réussite' },
                { field: 'testCriticalSuccessNode', handleId: 'critical-success', color: '#229954', label: 'Réussite critique' },
              ]
              
              testResults.forEach((result) => {
                const targetNodeId = choice[result.field]
                if (targetNodeId) {
                  // Vérifier que le nœud cible existe
                  const targetNodeExists = newNodes.some((n) => n.id === targetNodeId)
                  if (targetNodeExists) {
                    // Vérifier que l'edge n'existe pas déjà
                    const existingResultEdge = newEdges.find(
                      (e) => e.source === testNodeId && e.target === targetNodeId && e.sourceHandle === result.handleId
                    )
                    if (!existingResultEdge) {
                      newEdges.push({
                        id: `${testNodeId}-${result.handleId}-${targetNodeId}`,
                        source: testNodeId,
                        target: targetNodeId,
                        sourceHandle: result.handleId,
                        type: 'smoothstep',
                        label: result.label,
                        style: { stroke: result.color },
                      })
                    }
                  }
                }
              })
              
              // Supprimer l'edge directe vers targetNode si elle existe (choix avec test n'a pas de targetNode direct)
              if (choice.targetNode) {
                const directEdgeIndex = newEdges.findIndex(
                  (e) => e.source === nodeId && e.target === choice.targetNode && e.sourceHandle === `choice-${choiceIndex}`
                )
                if (directEdgeIndex !== -1) {
                  newEdges.splice(directEdgeIndex, 1)
                }
              }
            } else {
              // Le choix n'a plus de test : supprimer le TestNode et ses edges
              if (existingTestNode) {
                // Supprimer le TestNode
                const testNodeIndex = newNodes.findIndex((n) => n.id === testNodeId)
                if (testNodeIndex !== -1) {
                  newNodes.splice(testNodeIndex, 1)
                }
                
                // Supprimer toutes les edges liées au TestNode
                const edgesToRemove = newEdges.filter(
                  (e) => e.source === testNodeId || e.target === testNodeId
                )
                edgesToRemove.forEach((edge) => {
                  const edgeIndex = newEdges.findIndex((e) => e.id === edge.id)
                  if (edgeIndex !== -1) {
                    newEdges.splice(edgeIndex, 1)
                  }
                })
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
        const state = get()
        const newNodes = state.nodes.filter((n) => n.id !== nodeId)
        // Supprimer aussi les edges liés
        const newEdges = state.edges.filter(
          (e) => e.source !== nodeId && e.target !== nodeId
        )
        
        set({
          nodes: newNodes,
          edges: newEdges,
          selectedNodeId: state.selectedNodeId === nodeId ? null : state.selectedNodeId,
          dialogueMetadata: {
            ...state.dialogueMetadata,
            node_count: newNodes.length,
            edge_count: newEdges.length,
          },
        })
        // Marquer dirty pour auto-save draft (Task 1 - Story 0.5)
        get().markDirty()
      },
      
      // Connecter deux nœuds
      connectNodes: (
        sourceId: string,
        targetId: string,
        choiceIndex?: number,
        connectionType: string = 'default'
      ) => {
        const state = get()
        
        // Générer un ID unique pour l'edge
        const edgeId =
          choiceIndex !== undefined
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
          ...(choiceIndex !== undefined && { sourceHandle: `choice-${choiceIndex}` }), // Correspond à l'ID du handle dans DialogueNode
          type: 'default',
          data: {
            edgeType: connectionType,
            choiceIndex,
          },
        }
        
        const newEdges = [...state.edges, newEdge]
        
        // Mettre à jour targetNode dans le parent si connexion via choix
        const updatedNodes = [...state.nodes]
        if (choiceIndex !== undefined) {
          const sourceNodeIndex = updatedNodes.findIndex((n) => n.id === sourceId)
          if (sourceNodeIndex !== -1) {
            const sourceNode = updatedNodes[sourceNodeIndex]
            if (sourceNode.data?.choices && sourceNode.data.choices[choiceIndex]) {
              // Mettre à jour targetNode dans le choix
              updatedNodes[sourceNodeIndex] = {
                ...sourceNode,
                data: {
                  ...sourceNode.data,
                  choices: sourceNode.data.choices.map((choice: any, idx: number) =>
                    idx === choiceIndex
                      ? { ...choice, targetNode: targetId }
                      : choice
                  ),
                },
              }
            }
          }
        } else if (connectionType === 'nextNode') {
          // Mettre à jour nextNode dans le parent pour navigation linéaire
          const sourceNodeIndex = updatedNodes.findIndex((n) => n.id === sourceId)
          if (sourceNodeIndex !== -1) {
            const sourceNode = updatedNodes[sourceNodeIndex]
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
            edge_count: newEdges.length,
          },
        })
        // Marquer dirty pour auto-save draft (Task 1 - Story 0.5)
        get().markDirty()
      },
      
      // Déconnecter deux nœuds
      disconnectNodes: (edgeId: string) => {
        const state = get()
        const newEdges = state.edges.filter((e) => e.id !== edgeId)
        
        set({
          edges: newEdges,
          dialogueMetadata: {
            ...state.dialogueMetadata,
            edge_count: newEdges.length,
          },
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
        options: any
      ) => {
        set({ isGenerating: true })
        try {
          const state = get()
          const parentNode = state.nodes.find((n) => n.id === parentNodeId)
          
          if (!parentNode) {
            throw new Error(`Nœud parent ${parentNodeId} introuvable`)
          }
          
          // Appeler l'API pour générer le nœud
          const response = await graphAPI.generateNode({
            parent_node_id: parentNodeId,
            parent_node_content: parentNode.data,
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
          // Utiliser response.nodes si disponible (batch), sinon response.node (backward compatibility)
          const generatedNodes = response.nodes && response.nodes.length > 0 
            ? response.nodes 
            : (response.node ? [response.node] : [])
          
          // Ajouter les nouveaux nœuds avec positionnement en cascade pour batch
          const generatedNodeIds: string[] = []
          
          // Créer un map pour associer chaque connexion à son nœud généré
          const connectionMap = new Map<number, { node: any, conn: any }>()
          for (const conn of response.suggested_connections) {
            const node = generatedNodes.find((n) => n.id === conn.to)
            if (node && conn.via_choice_index !== undefined) {
              connectionMap.set(conn.via_choice_index, { node, conn })
            }
          }
          
          // Trier les connexions par via_choice_index pour positionnement cascade
          const sortedConnections = Array.from(connectionMap.entries()).sort((a, b) => a[0] - b[0])
          
          // Si pas de connexions avec via_choice_index, utiliser l'ordre des nœuds
          const nodesToAdd = sortedConnections.length > 0
            ? sortedConnections.map(([choiceIndex, { node }]) => ({ node, choiceIndex }))
            : generatedNodes.map((node, index) => ({ node, choiceIndex: index }))
          const totalToAdd = nodesToAdd.length
          
          if (options.generate_all_choices && typeof options.onBatchProgress === 'function' && totalToAdd > 0) {
            options.onBatchProgress(0, totalToAdd)
          }
          
          nodesToAdd.forEach(({ node: generatedNode, choiceIndex }, index) => {
            const isBatch = options.generate_all_choices
            const isChoiceSpecific = !isBatch && options.target_choice_index !== undefined && options.target_choice_index !== null
            const verticalOffset = isBatch
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
            
            get().addNode(newNode)
            generatedNodeIds.push(generatedNode.id)
            
            if (isBatch && typeof options.onBatchProgress === 'function' && totalToAdd > 0) {
              options.onBatchProgress(index + 1, totalToAdd)
            }
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
        } catch (error) {
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
            unityNode.choices = unityNode.choices.map((choice: any) => {
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
              const layoutedNode = response.nodes.find((n: any) => n.id === node.id)
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
    }),
    {
      // Configuration du middleware temporal (undo/redo)
      limit: 50, // Historique de 50 actions
      equality: (a, b) => a === b,
      // Partialiser pour ne pas historiser certains champs UI transitoires
      partialize: (state): any => {
        const {
          isGenerating,
          isLoading,
          isSaving,
          validationErrors,
          highlightedNodeIds,
          ...rest
        } = state
        return rest
      },
    }
  )
)

// Export des actions undo/redo depuis zundo
export const { undo, redo, clear: clearHistory } = useGraphStore.temporal.getState()
