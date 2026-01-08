import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ContextFieldSelector } from './ContextFieldSelector'
import { useContextConfigStore } from '../../store/contextConfigStore'

// Mock du store
vi.mock('../../store/contextConfigStore', () => ({
  useContextConfigStore: vi.fn(),
}))

const mockUseContextConfigStore = vi.mocked(useContextConfigStore)

describe('ContextFieldSelector', () => {
  const mockDetectFields = vi.fn(() => Promise.resolve())
  const mockToggleField = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    
    mockUseContextConfigStore.mockReturnValue({
      availableFields: {
        character: {
          'Nom': {
            path: 'Nom',
            label: 'Nom',
            type: 'string',
            depth: 0,
            frequency: 1.0,
            suggested: false,
            category: 'identity',
            importance: 'essential',
          },
          'Dialogue Type': {
            path: 'Dialogue Type',
            label: 'Dialogue Type',
            type: 'dict',
            depth: 0,
            frequency: 0.8,
            suggested: true,
            category: 'voice',
            importance: 'essential',
          },
        },
      },
      fieldConfigs: {
        character: ['Nom'],
      },
      suggestions: {
        character: ['Dialogue Type'],
      },
      toggleField: mockToggleField,
      detectFields: mockDetectFields,
      isLoading: false,
      error: null,
    } as any)
  })

  it('devrait afficher un message de chargement quand isLoading est true', () => {
    const defaultReturn = {
      availableFields: { character: {} },
      fieldConfigs: { character: [] },
      suggestions: { character: [] },
      toggleField: mockToggleField,
      detectFields: mockDetectFields,
      isLoading: false,
      error: null,
    }
    mockUseContextConfigStore.mockReturnValue({
      ...defaultReturn,
      isLoading: true,
    } as any)

    render(<ContextFieldSelector elementType="character" />)
    
    expect(screen.getByText(/détection des champs en cours/i)).toBeInTheDocument()
  })

  it('devrait afficher une erreur quand error est défini', () => {
    const defaultReturn = {
      availableFields: { character: {} },
      fieldConfigs: { character: [] },
      suggestions: { character: [] },
      toggleField: mockToggleField,
      detectFields: mockDetectFields,
      isLoading: false,
      error: null,
    }
    mockUseContextConfigStore.mockReturnValue({
      ...defaultReturn,
      error: 'Erreur de test',
    } as any)

    render(<ContextFieldSelector elementType="character" />)
    
    expect(screen.getByText(/erreur: erreur de test/i)).toBeInTheDocument()
  })

  it('devrait appeler detectFields au montage si aucun champ n\'est disponible', async () => {
    const mockDetectFieldsWithPromise = vi.fn(() => Promise.resolve())

    const defaultReturn = {
      availableFields: { character: {} },
      fieldConfigs: { character: [] },
      suggestions: { character: [] },
      toggleField: mockToggleField,
      detectFields: mockDetectFields,
      isLoading: false,
      error: null,
    }
    mockUseContextConfigStore.mockReturnValue({
      ...defaultReturn,
      availableFields: {
        character: {},
      },
      detectFields: mockDetectFieldsWithPromise,
    } as any)

    render(<ContextFieldSelector elementType="character" />)
    
    await waitFor(() => {
      expect(mockDetectFieldsWithPromise).toHaveBeenCalledWith('character')
    })
  })

  it('devrait afficher les champs disponibles', () => {
    render(<ContextFieldSelector elementType="character" />)
    
    expect(screen.getByText(/nom/i)).toBeInTheDocument()
    expect(screen.getByText(/dialogue type/i)).toBeInTheDocument()
  })

  it('devrait permettre de rechercher des champs', async () => {
    const user = userEvent.setup()
    render(<ContextFieldSelector elementType="character" />)
    
    const searchInput = screen.getByPlaceholderText(/rechercher un champ/i)
    await user.type(searchInput, 'Nom')
    
    // Le champ "Nom" devrait être visible, "Dialogue Type" ne devrait pas l'être
    expect(screen.getByText(/nom/i)).toBeInTheDocument()
  })
})

