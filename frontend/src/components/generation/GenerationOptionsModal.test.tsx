import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { GenerationOptionsModal } from './GenerationOptionsModal'
import { useContextConfigStore } from '../../store/contextConfigStore'
import * as configAPI from '../../api/config'

// Mock des dépendances
vi.mock('../../store/contextConfigStore')
vi.mock('../../api/config')
vi.mock('./ContextFieldSelector', () => ({
  ContextFieldSelector: ({ elementType }: { elementType: string }) => (
    <div data-testid={`field-selector-${elementType}`}>Field Selector for {elementType}</div>
  ),
}))

const mockUseContextConfigStore = vi.mocked(useContextConfigStore)
const mockConfigAPI = vi.mocked(configAPI)

describe('GenerationOptionsModal', () => {
  const mockOnClose = vi.fn()
  const mockOnApply = vi.fn()
  const mockSetOrganization = vi.fn()
  const mockResetToDefault = vi.fn()
  const mockGetPreview = vi.fn()
  const mockDetectFields = vi.fn()
  const mockLoadSuggestions = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    
    mockUseContextConfigStore.mockReturnValue({
      fieldConfigs: {
        character: [],
        location: [],
        item: [],
        species: [],
        community: [],
      },
      organization: 'default',
      setOrganization: mockSetOrganization,
      resetToDefault: mockResetToDefault,
      getPreview: mockGetPreview,
      detectFields: mockDetectFields,
      loadSuggestions: mockLoadSuggestions,
      availableFields: {},
      suggestions: {},
      isLoading: false,
      error: null,
      toggleField: vi.fn(),
      clearError: vi.fn(),
    } as any)

    mockConfigAPI.getUnityDialoguesPath.mockResolvedValue({ path: '/test/path' })
  })

  it('ne devrait pas s\'afficher quand isOpen est false', () => {
    render(
      <GenerationOptionsModal
        isOpen={false}
        onClose={mockOnClose}
        onApply={mockOnApply}
      />
    )
    
    expect(screen.queryByText(/options de génération/i)).not.toBeInTheDocument()
  })

  it('devrait s\'afficher quand isOpen est true', () => {
    render(
      <GenerationOptionsModal
        isOpen={true}
        onClose={mockOnClose}
        onApply={mockOnApply}
      />
    )
    
    expect(screen.getByText(/options de génération/i)).toBeInTheDocument()
  })

  it('devrait afficher les onglets', () => {
    render(
      <GenerationOptionsModal
        isOpen={true}
        onClose={mockOnClose}
        onApply={mockOnApply}
      />
    )
    
    expect(screen.getByText(/contexte/i)).toBeInTheDocument()
    expect(screen.getByText(/unity/i)).toBeInTheDocument()
    expect(screen.getByText(/organisation/i)).toBeInTheDocument()
    expect(screen.getByText(/guidance/i)).toBeInTheDocument()
  })

  it('devrait permettre de changer d\'onglet', async () => {
    const user = userEvent.setup()
    render(
      <GenerationOptionsModal
        isOpen={true}
        onClose={mockOnClose}
        onApply={mockOnApply}
      />
    )
    
    const unityTab = screen.getByText(/unity/i)
    await user.click(unityTab)
    
    expect(screen.getByText(/configuration unity/i)).toBeInTheDocument()
  })

  it('devrait fermer le modal quand on clique sur le bouton de fermeture', async () => {
    const user = userEvent.setup()
    render(
      <GenerationOptionsModal
        isOpen={true}
        onClose={mockOnClose}
        onApply={mockOnApply}
      />
    )
    
    const closeButton = screen.getByText('×')
    await user.click(closeButton)
    
    expect(mockOnClose).toHaveBeenCalled()
  })

  it('devrait appeler onApply quand on clique sur Appliquer', async () => {
    const user = userEvent.setup()
    render(
      <GenerationOptionsModal
        isOpen={true}
        onClose={mockOnClose}
        onApply={mockOnApply}
      />
    )
    
    const applyButton = screen.getByText(/appliquer/i)
    await user.click(applyButton)
    
    expect(mockOnApply).toHaveBeenCalled()
    expect(mockOnClose).toHaveBeenCalled()
  })

  it('devrait réinitialiser et fermer quand on clique sur Réinitialiser', async () => {
    const user = userEvent.setup()
    render(
      <GenerationOptionsModal
        isOpen={true}
        onClose={mockOnClose}
        onApply={mockOnApply}
      />
    )
    
    const resetButton = screen.getByText(/réinitialiser/i)
    await user.click(resetButton)
    
    expect(mockResetToDefault).toHaveBeenCalled()
    expect(mockOnClose).toHaveBeenCalled()
  })

  it('devrait charger le chemin Unity au montage', async () => {
    render(
      <GenerationOptionsModal
        isOpen={true}
        onClose={mockOnClose}
        onApply={mockOnApply}
      />
    )
    
    // Changer vers l'onglet Unity
    const unityTab = screen.getByText(/unity/i)
    await userEvent.click(unityTab)
    
    await waitFor(() => {
      expect(mockConfigAPI.getUnityDialoguesPath).toHaveBeenCalled()
    })
  })
})

