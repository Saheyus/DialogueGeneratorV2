/**
 * Tests unitaires pour les schémas de validation des nœuds de dialogue.
 */
import { describe, it, expect } from 'vitest'
import { choiceSchema, testNodeDataSchema } from '../schemas/nodeEditorSchema'

describe('nodeEditorSchema - 4 résultats de test', () => {
  describe('choiceSchema - Rétrocompatibilité avec 2 résultats', () => {
    it('devrait accepter un choix avec testSuccessNode et testFailureNode (rétrocompatibilité)', () => {
      const choice = {
        text: 'Test choice',
        test: 'Raison+Diplomatie:8',
        testSuccessNode: 'node-success',
        testFailureNode: 'node-failure',
      }
      
      const result = choiceSchema.safeParse(choice)
      expect(result.success).toBe(true)
      if (result.success) {
        expect(result.data.testSuccessNode).toBe('node-success')
        expect(result.data.testFailureNode).toBe('node-failure')
      }
    })
  })

  describe('choiceSchema - Support des 4 résultats de test', () => {
    it('devrait accepter un choix avec les 4 résultats de test', () => {
      const choice = {
        text: 'Test choice',
        test: 'Raison+Diplomatie:8',
        testCriticalFailureNode: 'node-critical-failure',
        testFailureNode: 'node-failure',
        testSuccessNode: 'node-success',
        testCriticalSuccessNode: 'node-critical-success',
      }
      
      const result = choiceSchema.safeParse(choice)
      expect(result.success).toBe(true)
      if (result.success) {
        expect(result.data.testCriticalFailureNode).toBe('node-critical-failure')
        expect(result.data.testFailureNode).toBe('node-failure')
        expect(result.data.testSuccessNode).toBe('node-success')
        expect(result.data.testCriticalSuccessNode).toBe('node-critical-success')
      }
    })

    it('devrait accepter un choix avec seulement les résultats critiques', () => {
      const choice = {
        text: 'Test choice',
        test: 'Raison+Diplomatie:8',
        testCriticalFailureNode: 'node-critical-failure',
        testCriticalSuccessNode: 'node-critical-success',
      }
      
      const result = choiceSchema.safeParse(choice)
      expect(result.success).toBe(true)
      if (result.success) {
        expect(result.data.testCriticalFailureNode).toBe('node-critical-failure')
        expect(result.data.testCriticalSuccessNode).toBe('node-critical-success')
      }
    })
  })

  describe('testNodeDataSchema - Support des 4 résultats de test', () => {
    it('devrait accepter un TestNode avec les 4 résultats de test', () => {
      const testNode = {
        id: 'test-node-1',
        test: 'Raison+Diplomatie:8',
        criticalFailureNode: 'node-critical-failure',
        failureNode: 'node-failure',
        successNode: 'node-success',
        criticalSuccessNode: 'node-critical-success',
      }
      
      const result = testNodeDataSchema.safeParse(testNode)
      expect(result.success).toBe(true)
      if (result.success) {
        expect(result.data.criticalFailureNode).toBe('node-critical-failure')
        expect(result.data.failureNode).toBe('node-failure')
        expect(result.data.successNode).toBe('node-success')
        expect(result.data.criticalSuccessNode).toBe('node-critical-success')
      }
    })

    it('devrait accepter un TestNode avec seulement 2 résultats (rétrocompatibilité)', () => {
      const testNode = {
        id: 'test-node-1',
        test: 'Raison+Diplomatie:8',
        successNode: 'node-success',
        failureNode: 'node-failure',
      }
      
      const result = testNodeDataSchema.safeParse(testNode)
      expect(result.success).toBe(true)
      if (result.success) {
        expect(result.data.successNode).toBe('node-success')
        expect(result.data.failureNode).toBe('node-failure')
      }
    })
  })
})
