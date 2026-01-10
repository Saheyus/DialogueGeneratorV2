import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ContextSelector } from './ContextSelector'
import * as contextAPI from '../../api/context'
import { useContextStore } from '../../store/contextStore'
import type { CharacterResponse, LocationResponse, ItemResponse } from '../../types/api'

// Mock des modules
vi.mock('../../api/context')
vi.mock('../../store/contextStore')

const mockUseContextStore = vi.mocked(useContextStore)

describe('ContextSelector', () => {
  const mockToggleCharacter = vi.fn()
  const mockToggleLocation = vi.fn()
  const mockToggleItem = vi.fn()
  const mockToggleSpecies = vi.fn()
  const mockToggleCommunity = vi.fn()
  const mockClearSelections = vi.fn()
  const mockSetElementLists = vi.fn()
  const mockGetElementMode = vi.fn(() => null)
  const mockSetElementMode = vi.fn()

  const mockSelections = {
    characters_full: [],
    characters_excerpt: [],
    locations_full: [],
    locations_excerpt: [],
    items_full: [],
    items_excerpt: [],
    species_full: [],
    species_excerpt: [],
    communities_full: [],
    communities_excerpt: [],
    dialogues_examples: [],
  }

  const mockCharacter: CharacterResponse = {
    name: 'Test Character',
    data: { description: 'A test character' },
  }

  const mockLocation: LocationResponse = {
    name: 'Test Location',
    data: { description: 'A test location' },
  }

  const mockItem: ItemResponse = {
    name: 'Test Item',
    data: { description: 'A test item' },
  }

  beforeEach(() => {
    vi.clearAllMocks()
    
    mockUseContextStore.mockReturnValue({
      selections: mockSelections,
      toggleCharacter: mockToggleCharacter,
      toggleLocation: mockToggleLocation,
      toggleItem: mockToggleItem,
      toggleSpecies: mockToggleSpecies,
      toggleCommunity: mockToggleCommunity,
      clearSelections: mockClearSelections,
      setElementLists: mockSetElementLists,
      getElementMode: mockGetElementMode,
      setElementMode: mockSetElementMode,
    } as ReturnType<typeof useContextStore>)

    // Mock des appels API par défaut
    vi.mocked(contextAPI.listCharacters).mockResolvedValue({
      characters: [mockCharacter],
      total: 1,
    })
    vi.mocked(contextAPI.listLocations).mockResolvedValue({
      locations: [mockLocation],
      total: 1,
    })
    vi.mocked(contextAPI.listItems).mockResolvedValue({
      items: [mockItem],
      total: 1,
    })
    vi.mocked(contextAPI.listSpecies).mockResolvedValue({
      species: [],
      total: 0,
    })
    vi.mocked(contextAPI.listCommunities).mockResolvedValue({
      communities: [],
      total: 0,
    })
  })

  it('affiche les onglets de sélection', async () => {
    render(<ContextSelector />)

    await waitFor(() => {
      expect(screen.getByText(/personnages/i)).toBeInTheDocument()
      expect(screen.getByText(/lieux/i)).toBeInTheDocument()
      expect(screen.getByText(/objets/i)).toBeInTheDocument()
      expect(screen.getByText(/espèces/i)).toBeInTheDocument()
      expect(screen.getByText(/communautés/i)).toBeInTheDocument()
    })
  })

  it('charge les données au montage', async () => {
    render(<ContextSelector />)

    await waitFor(() => {
      expect(contextAPI.listCharacters).toHaveBeenCalled()
      expect(contextAPI.listLocations).toHaveBeenCalled()
      expect(contextAPI.listItems).toHaveBeenCalled()
      expect(contextAPI.listSpecies).toHaveBeenCalled()
      expect(contextAPI.listCommunities).toHaveBeenCalled()
    })
  })

  it('affiche le champ de recherche', async () => {
    render(<ContextSelector />)

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/rechercher/i)).toBeInTheDocument()
    })
  })

  it('permet de changer d\'onglet', async () => {
    const user = userEvent.setup()
    render(<ContextSelector />)

    await waitFor(() => {
      expect(screen.getByText(/personnages/i)).toBeInTheDocument()
    })

    const locationsTab = screen.getByText(/lieux/i)
    await user.click(locationsTab)

    // L'onglet Lieux devrait être actif
    expect(locationsTab).toBeInTheDocument()
  })

  it('appelle onItemSelected quand un élément est cliqué', async () => {
    const user = userEvent.setup()
    const mockOnItemSelected = vi.fn()
    
    vi.mocked(contextAPI.getCharacter).mockResolvedValue(mockCharacter)

    render(<ContextSelector onItemSelected={mockOnItemSelected} />)

    await waitFor(() => {
      expect(screen.getByText('Test Character')).toBeInTheDocument()
    })

    const characterItem = screen.getByText('Test Character')
    await user.click(characterItem)

    await waitFor(() => {
      expect(contextAPI.getCharacter).toHaveBeenCalledWith('Test Character')
      expect(mockOnItemSelected).toHaveBeenCalledWith(mockCharacter)
    })
  })

  it('appelle toggleCharacter quand on coche un personnage', async () => {
    const user = userEvent.setup()
    render(<ContextSelector />)

    await waitFor(() => {
      expect(screen.getByText('Test Character')).toBeInTheDocument()
    })

    const characterItem = screen.getByText('Test Character').closest('div')
    if (characterItem) {
      const checkbox = characterItem.querySelector('input[type="checkbox"]')
      if (checkbox) {
        await user.click(checkbox)
        expect(mockToggleCharacter).toHaveBeenCalledWith('Test Character')
      }
    }
  })

  it('affiche une erreur si le chargement échoue', async () => {
    const errorMessage = 'Erreur de chargement'
    vi.mocked(contextAPI.listCharacters).mockRejectedValue(new Error(errorMessage))

    render(<ContextSelector />)

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })
  })

  it('affiche le résumé des sélections', async () => {
    mockUseContextStore.mockReturnValue({
      selections: {
        characters_full: ['Test Character'],
        characters_excerpt: [],
        locations_full: ['Test Location'],
        locations_excerpt: [],
        items_full: [],
        items_excerpt: [],
        species_full: [],
        species_excerpt: [],
        communities_full: [],
        communities_excerpt: [],
        dialogues_examples: [],
      },
      toggleCharacter: mockToggleCharacter,
      toggleLocation: mockToggleLocation,
      toggleItem: mockToggleItem,
      toggleSpecies: mockToggleSpecies,
      toggleCommunity: mockToggleCommunity,
      clearSelections: mockClearSelections,
      setElementLists: mockSetElementLists,
      getElementMode: mockGetElementMode,
      setElementMode: mockSetElementMode,
    } as ReturnType<typeof useContextStore>)

    render(<ContextSelector />)

    await waitFor(() => {
      // Le résumé doit afficher le personnage sélectionné
      expect(screen.getByText(/test character/i)).toBeInTheDocument()
    })
  })

  it('réinitialise la sélection quand on change d\'onglet', async () => {
    const user = userEvent.setup()
    const mockOnItemSelected = vi.fn()
    
    vi.mocked(contextAPI.getCharacter).mockResolvedValue(mockCharacter)

    render(<ContextSelector onItemSelected={mockOnItemSelected} />)

    await waitFor(() => {
      expect(screen.getByText('Test Character')).toBeInTheDocument()
    })

    // Sélectionner un personnage
    const characterItem = screen.getByText('Test Character')
    await user.click(characterItem)

    await waitFor(() => {
      expect(mockOnItemSelected).toHaveBeenCalledWith(mockCharacter)
    })

    // Changer d'onglet
    const locationsTab = screen.getByText(/lieux/i)
    await user.click(locationsTab)

    // La sélection devrait être réinitialisée
    await waitFor(() => {
      expect(mockOnItemSelected).toHaveBeenCalledWith(null)
    })
  })
})

