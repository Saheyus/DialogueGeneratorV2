/**
 * Tests pour useGraphStore - Auto-save draft functionality
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useGraphStore } from '../store/graphStore'
import type { Node } from 'reactflow'

// Mock graphAPI
vi.mock('../api/graph', () => ({
  loadGraph: vi.fn(),
  saveGraph: vi.fn(),
  generateNode: vi.fn(),
  validateGraph: vi.fn(),
  calculateLayout: vi.fn(),
}))

describe('useGraphStore - Auto-save draft state', () => {
  beforeEach(() => {
    // Reset store avant chaque test
    useGraphStore.getState().resetGraph()
  })

  describe('Initial state', () => {
    it('should initialize hasUnsavedChanges to false', () => {
      const state = useGraphStore.getState()
      expect(state.hasUnsavedChanges).toBe(false)
    })

    it('should initialize lastDraftSavedAt to null', () => {
      const state = useGraphStore.getState()
      expect(state.lastDraftSavedAt).toBeNull()
    })

    it('should initialize lastDraftError to null', () => {
      const state = useGraphStore.getState()
      expect(state.lastDraftError).toBeNull()
    })
  })

  describe('markDirty', () => {
    it('should set hasUnsavedChanges to true', () => {
      const { markDirty } = useGraphStore.getState()
      markDirty()
      
      const state = useGraphStore.getState()
      expect(state.hasUnsavedChanges).toBe(true)
    })
  })

  describe('markDraftSaved', () => {
    it('should set hasUnsavedChanges to false and update lastDraftSavedAt', () => {
      const { markDirty, markDraftSaved } = useGraphStore.getState()
      
      // Marquer dirty d'abord
      markDirty()
      expect(useGraphStore.getState().hasUnsavedChanges).toBe(true)
      
      // Marquer sauvegardé
      const beforeSave = Date.now()
      markDraftSaved()
      const afterSave = Date.now()
      
      const state = useGraphStore.getState()
      expect(state.hasUnsavedChanges).toBe(false)
      expect(state.lastDraftSavedAt).toBeGreaterThanOrEqual(beforeSave)
      expect(state.lastDraftSavedAt).toBeLessThanOrEqual(afterSave)
    })
  })

  describe('markDraftError', () => {
    it('should set lastDraftError and set hasUnsavedChanges to false', () => {
      const { markDirty, markDraftError } = useGraphStore.getState()
      
      // Marquer dirty d'abord
      markDirty()
      expect(useGraphStore.getState().hasUnsavedChanges).toBe(true)
      
      // Marquer erreur
      const errorMessage = 'Quota exceeded'
      markDraftError(errorMessage)
      
      const state = useGraphStore.getState()
      expect(state.lastDraftError).toBe(errorMessage)
      expect(state.hasUnsavedChanges).toBe(false)
    })
  })

  describe('clearDraftError', () => {
    it('should reset lastDraftError to null', () => {
      const { markDraftError, clearDraftError } = useGraphStore.getState()
      
      // Marquer erreur d'abord
      markDraftError('Some error')
      expect(useGraphStore.getState().lastDraftError).toBe('Some error')
      
      // Clear erreur
      clearDraftError()
      
      const state = useGraphStore.getState()
      expect(state.lastDraftError).toBeNull()
    })
  })

  describe('Graph mutations should mark dirty', () => {
    it('should mark dirty when addNode is called', () => {
      const { addNode } = useGraphStore.getState()
      const newNode: Node = {
        id: 'test-node-1',
        type: 'dialogueNode',
        position: { x: 0, y: 0 },
        data: { text: 'Test' },
      }
      
      addNode(newNode)
      
      const state = useGraphStore.getState()
      expect(state.hasUnsavedChanges).toBe(true)
    })

    it('should mark dirty when updateNode is called', () => {
      const { addNode, updateNode, markDraftSaved } = useGraphStore.getState()
      
      // Ajouter un nœud et marquer sauvegardé
      const newNode: Node = {
        id: 'test-node-1',
        type: 'dialogueNode',
        position: { x: 0, y: 0 },
        data: { text: 'Test' },
      }
      addNode(newNode)
      markDraftSaved()
      
      // Modifier le nœud
      updateNode('test-node-1', { data: { text: 'Updated' } })
      
      const state = useGraphStore.getState()
      expect(state.hasUnsavedChanges).toBe(true)
    })

    it('should mark dirty when deleteNode is called', () => {
      const { addNode, deleteNode, markDraftSaved } = useGraphStore.getState()
      
      // Ajouter un nœud et marquer sauvegardé
      const newNode: Node = {
        id: 'test-node-1',
        type: 'dialogueNode',
        position: { x: 0, y: 0 },
        data: { text: 'Test' },
      }
      addNode(newNode)
      markDraftSaved()
      
      // Supprimer le nœud
      deleteNode('test-node-1')
      
      const state = useGraphStore.getState()
      expect(state.hasUnsavedChanges).toBe(true)
    })

    it('should mark dirty when connectNodes is called', () => {
      const { addNode, connectNodes, markDraftSaved } = useGraphStore.getState()
      
      // Ajouter deux nœuds et marquer sauvegardé
      const node1: Node = { id: 'node-1', type: 'dialogueNode', position: { x: 0, y: 0 }, data: {} }
      const node2: Node = { id: 'node-2', type: 'dialogueNode', position: { x: 100, y: 0 }, data: {} }
      addNode(node1)
      addNode(node2)
      markDraftSaved()
      
      // Connecter les nœuds
      connectNodes('node-1', 'node-2')
      
      const state = useGraphStore.getState()
      expect(state.hasUnsavedChanges).toBe(true)
    })

    it('should mark dirty when disconnectNodes is called', () => {
      const { addNode, connectNodes, disconnectNodes, markDraftSaved } = useGraphStore.getState()
      
      // Ajouter deux nœuds, les connecter et marquer sauvegardé
      const node1: Node = { id: 'node-1', type: 'dialogueNode', position: { x: 0, y: 0 }, data: {} }
      const node2: Node = { id: 'node-2', type: 'dialogueNode', position: { x: 100, y: 0 }, data: {} }
      addNode(node1)
      addNode(node2)
      connectNodes('node-1', 'node-2')
      markDraftSaved()
      
      // Déconnecter les nœuds
      const edges = useGraphStore.getState().edges
      const edgeId = edges.find(e => e.source === 'node-1' && e.target === 'node-2')?.id
      if (edgeId) {
        disconnectNodes(edgeId)
      }
      
      const state = useGraphStore.getState()
      expect(state.hasUnsavedChanges).toBe(true)
    })

    it('should mark dirty when updateNodePosition is called', () => {
      const { addNode, updateNodePosition, markDraftSaved } = useGraphStore.getState()
      
      // Ajouter un nœud et marquer sauvegardé
      const newNode: Node = {
        id: 'test-node-1',
        type: 'dialogueNode',
        position: { x: 0, y: 0 },
        data: { text: 'Test' },
      }
      addNode(newNode)
      markDraftSaved()
      
      // Modifier la position
      updateNodePosition('test-node-1', { x: 100, y: 100 })
      
      const state = useGraphStore.getState()
      expect(state.hasUnsavedChanges).toBe(true)
    })

    it('should mark dirty when updateMetadata is called', () => {
      const { updateMetadata, markDraftSaved } = useGraphStore.getState()
      
      markDraftSaved()
      
      // Modifier les métadonnées
      updateMetadata({ title: 'New Title' })
      
      const state = useGraphStore.getState()
      expect(state.hasUnsavedChanges).toBe(true)
    })

    it('should NOT mark dirty when loadDialogue is called', async () => {
      const { markDirty, loadDialogue } = useGraphStore.getState()
      
      // Marquer dirty d'abord
      markDirty()
      expect(useGraphStore.getState().hasUnsavedChanges).toBe(true)
      
      // Mock graphAPI.loadGraph (accessible via vi.mocked après import)
      const graphAPI = await import('../api/graph')
      const mockLoadGraph = vi.mocked(graphAPI.loadGraph)
      mockLoadGraph.mockResolvedValueOnce({
        nodes: [],
        edges: [],
        metadata: {
          title: 'Test Dialogue',
          node_count: 0,
          edge_count: 0,
          filename: 'test.json',
        },
      })
      
      // Appeler loadDialogue
      await loadDialogue('{"id": "START"}')
      
      // Vérifier que hasUnsavedChanges est réinitialisé à false
      const state = useGraphStore.getState()
      expect(state.hasUnsavedChanges).toBe(false)
      expect(state.lastDraftSavedAt).toBeNull()
      expect(state.lastDraftError).toBeNull()
      
      // Vérifier que loadGraph a été appelé
      expect(mockLoadGraph).toHaveBeenCalledWith({ json_content: '{"id": "START"}' })
    })
  })
})