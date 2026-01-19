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
  
  // État auto-save draft (Task 1 - Story 0.5)
  hasUnsavedChanges: boolean
  lastDraftSavedAt: number | null
  lastDraftError: string | null
  
  // Actions CRUD
  loadDialogue: (jsonContent: string) => Promise<void>
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
  ) => Promise<string> // Retourne le nodeId du nouveau nœud généré
  
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
  hasUnsavedChanges: false,
  lastDraftSavedAt: null,
  lastDraftError: null,
}

export const useGraphStore = create<GraphState>()(
  temporal(
    (set, get) => ({
      ...initialState,
      
      // Charger un dialogue Unity JSON
      loadDialogue: async (jsonContent: string) => {
        set({ isLoading: true })
        try {
          const response = await graphAPI.loadGraph({ json_content: jsonContent })
          
          // Convertir les nœuds en format ReactFlow
          const nodes: Node[] = response.nodes.map((node: any) => ({
            id: node.id,
            type: node.type,
            position: node.position,
            data: node.data,
          }))
          
          // Convertir les edges
          const edges: Edge[] = response.edges.map((edge: any) => ({
            id: edge.id,
            source: edge.source,
            target: edge.target,
            type: edge.type || 'default',
            label: edge.label,
            data: edge.data,
          }))
          
          set({
            nodes,
            edges,
            dialogueMetadata: {
              title: response.metadata.title,
              node_count: response.metadata.node_count,
              edge_count: response.metadata.edge_count,
              filename: response.metadata.filename,
            },
            isLoading: false,
            validationErrors: [],
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
        set((state) => ({
          nodes: state.nodes.map((node) =>
            node.id === nodeId ? { ...node, ...updates } : node
          ),
        }))
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
          type: 'default',
          data: {
            edgeType: connectionType,
            choiceIndex,
          },
        }
        
        const newEdges = [...state.edges, newEdge]
        
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
        set((state) => ({
          nodes: state.nodes.map((node) =>
            node.id === nodeId ? { ...node, position } : node
          ),
        }))
        // Marquer dirty pour auto-save draft (Task 1 - Story 0.5)
        get().markDirty()
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
          })
          
          // Ajouter le nouveau nœud
          const generatedNode = response.node
          const newNode: Node = {
            id: generatedNode.id,
            type: 'dialogueNode',
            position: {
              x: parentNode.position.x + 300,
              y: parentNode.position.y,
            },
            data: generatedNode,
          }
          
          get().addNode(newNode)

          // Créer les connexions suggérées
          for (const conn of response.suggested_connections) {
            get().connectNodes(
              conn.from,
              conn.to,
              conn.via_choice_index,
              conn.connection_type
            )
          }

          set({ isGenerating: false })
          
          // Retourner le nodeId du nouveau nœud pour feedback visuel
          return generatedNode.id
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
          
          set({
            validationErrors: [...response.errors, ...response.warnings],
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
      exportToUnity: () => {
        const state = get()
        
        // Reconvertir les nœuds ReactFlow en Unity JSON
        const unityNodes = state.nodes.map((node) => {
          const unityNode = { ...node.data }
          
          // Nettoyer les champs de navigation (seront recréés depuis les edges)
          delete unityNode.nextNode
          delete unityNode.successNode
          delete unityNode.failureNode
          
          if (unityNode.choices) {
            unityNode.choices = unityNode.choices.map((choice: any) => {
              const cleanChoice = { ...choice }
              delete cleanChoice.targetNode
              return cleanChoice
            })
          }
          
          return unityNode
        })
        
        // Reconstruire les connexions depuis les edges
        for (const edge of state.edges) {
          const sourceNode = unityNodes.find((n) => n.id === edge.source)
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
