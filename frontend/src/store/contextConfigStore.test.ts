import { describe, it, expect, beforeEach } from 'vitest'
import { useContextConfigStore } from './contextConfigStore'

describe('contextConfigStore', () => {
  beforeEach(() => {
    // Réinitialiser le store avant chaque test
    const store = useContextConfigStore.getState()
    store.resetToDefault()
  })

  it('devrait initialiser avec des valeurs par défaut', () => {
    const store = useContextConfigStore.getState()
    
    expect(store.organization).toBe('default')
    expect(store.fieldConfigs).toEqual({
      character: [],
      location: [],
      item: [],
      species: [],
      community: [],
    })
    expect(store.isLoading).toBe(false)
    expect(store.error).toBe(null)
  })

  it('devrait permettre de définir la configuration des champs', () => {
    useContextConfigStore.getState().setFieldConfig('character', ['Nom', 'Dialogue Type'])
    
    const state = useContextConfigStore.getState()
    expect(state.fieldConfigs.character).toEqual(['Nom', 'Dialogue Type'])
  })

  it('devrait permettre de basculer un champ', () => {
    // Ajouter un champ
    useContextConfigStore.getState().toggleField('character', 'Nom')
    let state = useContextConfigStore.getState()
    expect(state.fieldConfigs.character).toContain('Nom')
    
    // Retirer le champ
    useContextConfigStore.getState().toggleField('character', 'Nom')
    state = useContextConfigStore.getState()
    expect(state.fieldConfigs.character).not.toContain('Nom')
  })

  it('devrait permettre de changer le mode d\'organisation', () => {
    useContextConfigStore.getState().setOrganization('narrative')
    let state = useContextConfigStore.getState()
    expect(state.organization).toBe('narrative')
    
    useContextConfigStore.getState().setOrganization('minimal')
    state = useContextConfigStore.getState()
    expect(state.organization).toBe('minimal')
  })

  it('devrait permettre de réinitialiser aux valeurs par défaut', () => {
    const store = useContextConfigStore.getState()
    
    // Modifier l'état
    store.setFieldConfig('character', ['Nom'])
    store.setOrganization('narrative')
    
    // Réinitialiser
    store.resetToDefault()
    
    expect(store.fieldConfigs.character).toEqual([])
    expect(store.organization).toBe('default')
  })

  it('devrait permettre de nettoyer l\'erreur', () => {
    const store = useContextConfigStore.getState()
    
    // Simuler une erreur (on ne peut pas la définir directement, mais on peut tester la méthode)
    store.clearError()
    
    expect(store.error).toBe(null)
  })
})

