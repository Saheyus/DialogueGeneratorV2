/**
 * Types pour la synchronisation TestNode ↔ Choix Parent.
 * 
 * Architecture SOLID : Source of Truth = choix parent (JSON Unity)
 * TestNode = vue dérivée (artefact de visualisation ReactFlow)
 */
import type { Node, Edge } from 'reactflow'
import type { Choice } from '../schemas/nodeEditorSchema'

/**
 * Informations sur le choix parent d'un TestNode.
 */
export interface TestNodeParentInfo {
  dialogueNodeId: string
  choiceIndex: number
  dialogueNode: Node
  choice: Choice
}

/**
 * Résultat d'une synchronisation TestNode.
 */
export interface TestNodeSyncResult {
  testNode: Node | null
  edges: Edge[]
}

/**
 * Direction de synchronisation pour éviter les boucles infinies.
 */
export type SyncDirection = 'choice-to-test' | 'test-to-choice'
