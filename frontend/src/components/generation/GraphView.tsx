/**
 * Vue graphe intégrée pour afficher un dialogue Unity sous forme de graphe ReactFlow.
 * Utilisé dans UnityDialogueEditor pour basculer entre vue liste et vue graphe.
 */
import { memo, useMemo, useCallback, useEffect, useState } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  type Connection,
  type Node,
  type Edge,
  type NodeTypes,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { DialogueNode, TestNode, EndNode } from '../graph/nodes'
import { theme } from '../../theme'
import type { UnityDialogueNode } from '../../types/api'

interface GraphViewProps {
  json_content: string
}

/**
 * Convertit un dialogue Unity JSON en format ReactFlow (nodes + edges).
 */
function unityJsonToGraph(jsonContent: string): { nodes: Node[]; edges: Edge[] } {
  try {
    const unityNodes: UnityDialogueNode[] = JSON.parse(jsonContent)
    
    if (!Array.isArray(unityNodes)) {
      throw new Error('Le JSON Unity doit être un tableau de nœuds')
    }
    
    const reactflowNodes: Node[] = []
    const reactflowEdges: Edge[] = []
    
    const xOffset = 0
    let yOffset = 0
    
    for (const unityNode of unityNodes) {
      const nodeId = unityNode.id
      if (!nodeId) continue
      
      // Déterminer le type de nœud
      let nodeType = 'dialogueNode'
      if (unityNode.test) {
        nodeType = 'testNode'
      } else if (nodeId === 'END' || (!unityNode.choices && !unityNode.nextNode)) {
        nodeType = 'endNode'
      }
      
      // Créer le nœud ReactFlow
      reactflowNodes.push({
        id: nodeId,
        type: nodeType,
        position: { x: xOffset, y: yOffset },
        data: unityNode,
      })
      
      yOffset += 150
      
      // Créer les edges
      if (unityNode.nextNode) {
        reactflowEdges.push({
          id: `${nodeId}-next-${unityNode.nextNode}`,
          source: nodeId,
          target: unityNode.nextNode,
          type: 'smoothstep',
        })
      }
      
      if (unityNode.successNode) {
        reactflowEdges.push({
          id: `${nodeId}-success-${unityNode.successNode}`,
          source: nodeId,
          target: unityNode.successNode,
          type: 'smoothstep',
          label: 'Succès',
          style: { stroke: '#27AE60' },
        })
      }
      
      if (unityNode.failureNode) {
        reactflowEdges.push({
          id: `${nodeId}-failure-${unityNode.failureNode}`,
          source: nodeId,
          target: unityNode.failureNode,
          type: 'smoothstep',
          label: 'Échec',
          style: { stroke: '#E74C3C' },
        })
      }
      
      if (unityNode.choices) {
        unityNode.choices.forEach((choice, index) => {
          if (choice.targetNode) {
            reactflowEdges.push({
              id: `${nodeId}-choice-${index}-${choice.targetNode}`,
              source: nodeId,
              target: choice.targetNode,
              sourceHandle: `choice-${index}`,
              type: 'smoothstep',
              label: choice.text || `Choix ${index + 1}`,
            })
          }
        })
      }
    }
    
    return { nodes: reactflowNodes, edges: reactflowEdges }
  } catch (error) {
    console.error('Erreur lors de la conversion Unity → ReactFlow:', error)
    return { nodes: [], edges: [] }
  }
}


export const GraphView = memo(function GraphView({
  json_content,
}: GraphViewProps) {
  const { nodes: initialNodes, edges: initialEdges } = useMemo(
    () => unityJsonToGraph(json_content),
    [json_content]
  )
  
  const [nodes, setNodes, onNodesChangeLocal] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)
  
  // Synchroniser quand json_content change
  useEffect(() => {
    const { nodes: newNodes, edges: newEdges } = unityJsonToGraph(json_content)
    setNodes(newNodes)
    setEdges(newEdges)
  }, [json_content, setNodes, setEdges])
  
  const nodeTypes: NodeTypes = useMemo(
    () => ({
      dialogueNode: DialogueNode,
      testNode: TestNode,
      endNode: EndNode,
    }),
    []
  )
  
  const onConnect = useCallback(
    (params: Connection) => {
      setEdges((eds) => addEdge(params, eds))
    },
    [setEdges]
  )
  
  const onNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      // TODO: Ouvrir le panneau d'édition
    },
    []
  )
  
  return (
    <div style={{ width: '100%', height: '100%', backgroundColor: theme.background.panel }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChangeLocal}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-left"
      >
        <Background />
        <Controls />
        <MiniMap
          nodeColor={(node) => {
            if (node.type === 'testNode') return '#F5A623'
            if (node.type === 'endNode') return '#B8B8B8'
            return '#4A90E2'
          }}
          style={{ backgroundColor: theme.background.secondary }}
        />
      </ReactFlow>
    </div>
  )
})
