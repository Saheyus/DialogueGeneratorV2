/**
 * Tests projection document → nodes/edges avec IDs stables (ADR-008).
 * Story 16.4 Task 2.1.
 */
import { describe, it, expect } from 'vitest'
import {
  documentToGraph,
  graphToDocument,
  buildLayoutFromNodes,
  type UnityDocument,
  type LayoutPositions,
} from '../utils/documentToGraph'

describe('documentToGraph', () => {
  describe('stable IDs (choiceId present)', () => {
    it('uses node.id as React Flow node id (SCREAMING_SNAKE_CASE)', () => {
      const doc: UnityDocument = {
        schemaVersion: '1.1.0',
        nodes: [
          { id: 'START', line: 'Hi', nextNode: 'END' },
          { id: 'END', line: '' },
        ],
      }
      const layout: LayoutPositions = { nodes: { START: { x: 0, y: 0 }, END: { x: 0, y: 150 } } }
      const { nodes } = documentToGraph(doc, layout)
      const ids = nodes.map((n) => n.id).filter((id) => id !== 'test:__idx_0' && !id.startsWith('test:'));
      expect(ids).toContain('START')
      expect(ids).toContain('END')
    })

    it('uses choice:choiceId for choice sourceHandle and edge id e:nodeId:choice:choiceId:targetId', () => {
      const doc: UnityDocument = {
        schemaVersion: '1.1.0',
        nodes: [
          {
            id: 'START',
            line: 'Choose',
            choices: [
              { choiceId: 'accept', text: 'Accept', targetNode: 'END' },
              { choiceId: 'refuse', text: 'Refuse', targetNode: 'END' },
            ],
          },
          { id: 'END', line: '' },
        ],
      }
      const layout: LayoutPositions = { nodes: { START: { x: 0, y: 0 }, END: { x: 0, y: 150 } } }
      const { nodes, edges } = documentToGraph(doc, layout)
      const acceptEdge = edges.find(
        (e) => e.source === 'START' && e.target === 'END' && e.data?.choiceId === 'accept'
      )
      expect(acceptEdge).toBeDefined()
      expect(acceptEdge?.sourceHandle).toBe('choice:accept')
      expect(acceptEdge?.id).toBe('e:START:choice:accept:END')
      const refuseEdge = edges.find(
        (e) => e.source === 'START' && e.target === 'END' && e.data?.choiceId === 'refuse'
      )
      expect(refuseEdge?.sourceHandle).toBe('choice:refuse')
      expect(refuseEdge?.id).toBe('e:START:choice:refuse:END')
      expect(nodes.some((n) => n.type === 'testNode')).toBe(false)
    })

    it('uses test:choiceId for TestNode id and e:nodeId:choice:choiceId:test for choice→test edge', () => {
      const doc: UnityDocument = {
        schemaVersion: '1.1.0',
        nodes: [
          {
            id: 'NODE_A',
            line: 'Test choice',
            choices: [
              {
                choiceId: 'skill_check',
                text: 'Try',
                test: { formula: '1d20' },
                testSuccessNode: 'END',
                testFailureNode: 'END',
              },
            ],
          },
          { id: 'END', line: '' },
        ],
      }
      const layout: LayoutPositions = { nodes: { NODE_A: { x: 0, y: 0 }, END: { x: 0, y: 150 } } }
      const { nodes, edges } = documentToGraph(doc, layout)
      const testNode = nodes.find((n) => n.type === 'testNode')
      expect(testNode?.id).toBe('test:skill_check')
      const choiceToTest = edges.find(
        (e) => e.source === 'NODE_A' && e.target === 'test:skill_check'
      )
      expect(choiceToTest?.id).toBe('e:NODE_A:choice:skill_check:test')
      expect(choiceToTest?.sourceHandle).toBe('choice:skill_check')
    })
  })

  describe('fallback when choiceId missing', () => {
    it('uses __idx_N for handle and edge id when choice has no choiceId', () => {
      const doc: UnityDocument = {
        schemaVersion: '1.1.0',
        nodes: [
          {
            id: 'START',
            line: 'Choose',
            choices: [
              { text: 'First', targetNode: 'END' },
              { text: 'Second', targetNode: 'END' },
            ],
          },
          { id: 'END', line: '' },
        ],
      }
      const layout: LayoutPositions = { nodes: { START: { x: 0, y: 0 }, END: { x: 0, y: 150 } } }
      const { edges } = documentToGraph(doc, layout)
      const firstEdge = edges.find(
        (e) => e.source === 'START' && e.target === 'END' && e.data?.choiceIndex === 0
      )
      expect(firstEdge?.sourceHandle).toBe('choice:__idx_0')
      expect(firstEdge?.id).toBe('e:START:choice:__idx_0:END')
      const secondEdge = edges.find(
        (e) => e.source === 'START' && e.target === 'END' && e.data?.choiceIndex === 1
      )
      expect(secondEdge?.sourceHandle).toBe('choice:__idx_1')
      expect(secondEdge?.id).toBe('e:START:choice:__idx_1:END')
    })
  })

  describe('positions from layout', () => {
    it('applies layout node positions when provided', () => {
      const doc: UnityDocument = {
        schemaVersion: '1.1.0',
        nodes: [
          { id: 'START', line: 'Hi', nextNode: 'END' },
          { id: 'END', line: '' },
        ],
      }
      const layout: LayoutPositions = {
        nodes: { START: { x: 100, y: 200 }, END: { x: 100, y: 350 } },
      }
      const { nodes } = documentToGraph(doc, layout)
      const start = nodes.find((n) => n.id === 'START')
      const end = nodes.find((n) => n.id === 'END')
      expect(start?.position).toEqual({ x: 100, y: 200 })
      expect(end?.position).toEqual({ x: 100, y: 350 })
    })
  })
})

describe('graphToDocument', () => {
  it('reconstructs document with choiceId from stable sourceHandle', () => {
    const doc: UnityDocument = {
      schemaVersion: '1.1.0',
      nodes: [
        {
          id: 'START',
          line: 'Choose',
          choices: [
            { choiceId: 'yes', text: 'Yes', targetNode: 'END' },
            { choiceId: 'no', text: 'No', targetNode: 'END' },
          ],
        },
        { id: 'END', line: '' },
      ],
    }
    const layout: LayoutPositions = { nodes: { START: { x: 0, y: 0 }, END: { x: 0, y: 150 } } }
    const { nodes, edges } = documentToGraph(doc, layout)
    const roundTrip = graphToDocument(nodes, edges)
    expect(roundTrip.nodes).toHaveLength(2)
    const start = roundTrip.nodes.find((n) => n.id === 'START')
    expect(start?.choices).toHaveLength(2)
    expect(start?.choices?.[0].choiceId).toBe('yes')
    expect(start?.choices?.[0].targetNode).toBe('END')
    expect(start?.choices?.[1].choiceId).toBe('no')
    expect(start?.choices?.[1].targetNode).toBe('END')
  })
})

describe('buildLayoutFromNodes', () => {
  it('extracts positions by node id', () => {
    const nodes = [
      { id: 'START', type: 'dialogueNode', position: { x: 10, y: 20 }, data: {} },
      { id: 'END', type: 'endNode', position: { x: 10, y: 170 }, data: {} },
    ]
    const layout = buildLayoutFromNodes(nodes as never)
    expect(layout.nodes).toEqual({ START: { x: 10, y: 20 }, END: { x: 10, y: 170 } })
  })
})
