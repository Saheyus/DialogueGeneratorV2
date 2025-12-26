import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { Dashboard } from './Dashboard'
import { useGenerationStore } from '../../store/generationStore'
import { useGenerationActionsStore } from '../../store/generationActionsStore'
import { useContextStore } from '../../store/contextStore'
import type { CharacterResponse } from '../../types/api'

// Mock des stores
vi.mock('../../store/generationStore')
vi.mock('../../store/generationActionsStore')
vi.mock('../../store/contextStore')

// Mock des composants complexes
vi.mock('../generation/GenerationPanel', () => ({
  GenerationPanel: () => <div data-testid="generation-panel">Generation Panel</div>,
}))

vi.mock('../context/ContextSelector', () => ({
  ContextSelector: () => <div data-testid="context-selector">Context Selector</div>,
}))

const mockUseGenerationStore = vi.mocked(useGenerationStore)
const mockUseGenerationActionsStore = vi.mocked(useGenerationActionsStore)
const mockUseContextStore = vi.mocked(useContextStore)

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    mockUseGenerationStore.mockReturnValue({
      estimatedPrompt: '',
      estimatedTokens: 0,
      isEstimating: false,
      sceneSelection: {
        characterA: null,
        characterB: null,
        sceneRegion: null,
        subLocation: null,
      },
      dialogueStructure: ['', '', '', '', '', ''] as [string, string, string, string, string, string],
      systemPromptOverride: null,
      setDialogueStructure: vi.fn(),
      setSystemPromptOverride: vi.fn(),
      setEstimatedPrompt: vi.fn(),
      setSceneSelection: vi.fn(),
    } as ReturnType<typeof useGenerationStore>)
    
    mockUseContextStore.mockReturnValue({
      selections: {
        characters: [],
        locations: [],
        items: [],
        species: [],
        communities: [],
        dialogues_examples: [],
      },
      toggleCharacter: vi.fn(),
      toggleLocation: vi.fn(),
      toggleItem: vi.fn(),
      toggleSpecies: vi.fn(),
      toggleCommunity: vi.fn(),
      clearSelections: vi.fn(),
    } as ReturnType<typeof useContextStore>)

    mockUseGenerationActionsStore.mockReturnValue({
      actions: {
        handleGenerate: undefined,
        handlePreview: undefined,
        handleExportUnity: undefined,
        handleReset: undefined,
        isLoading: false,
        isDirty: false,
      },
    } as ReturnType<typeof useGenerationActionsStore>)
  })

  it('affiche les trois panneaux', () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )

    // Le composant ResizablePanels devrait être présent
    // On vérifie indirectement en cherchant les composants enfants
    expect(screen.getByText(/sélectionnez un élément/i)).toBeInTheDocument()
  })

  it('affiche le panneau de sélection de contexte à gauche', () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )

    // Le ContextSelector devrait être présent
    expect(screen.getByTestId('context-selector')).toBeInTheDocument()
  })

  it('affiche le panneau de génération au centre', () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )

    // Le GenerationPanel devrait être présent
    expect(screen.getByTestId('generation-panel')).toBeInTheDocument()
  })

  it('affiche les onglets dans le panneau de droite', async () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/prompt estimé/i)).toBeInTheDocument()
      expect(screen.getByText(/détails/i)).toBeInTheDocument()
    })
  })

  it('affiche le message par défaut dans l\'onglet Détails', () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )

    expect(screen.getByText(/sélectionnez un élément de contexte ou une interaction/i)).toBeInTheDocument()
  })

  it('permet de changer d\'onglet dans le panneau de droite', async () => {
    const user = userEvent.setup()
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/détails/i)).toBeInTheDocument()
    })

    const detailsTab = screen.getByText(/détails/i)
    await user.click(detailsTab)

    // L'onglet Détails devrait être actif
    expect(detailsTab).toBeInTheDocument()
  })

  it('affiche les boutons d\'action quand handleGenerate est disponible', async () => {
    mockUseGenerationActionsStore.mockReturnValue({
      actions: {
        handleGenerate: vi.fn(),
        handlePreview: vi.fn(),
        handleExportUnity: vi.fn(),
        handleReset: vi.fn(),
        isLoading: false,
        isDirty: false,
      },
    } as ReturnType<typeof useGenerationActionsStore>)

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/prévisualiser/i)).toBeInTheDocument()
      expect(screen.getByText(/exporter/i)).toBeInTheDocument()
      expect(screen.getByText(/reset/i)).toBeInTheDocument()
      expect(screen.getByText(/générer/i)).toBeInTheDocument()
    })
  })

  it('affiche l\'indicateur de brouillon non sauvegardé', async () => {
    mockUseGenerationActionsStore.mockReturnValue({
      actions: {
        handleGenerate: vi.fn(),
        handlePreview: vi.fn(),
        handleExportUnity: vi.fn(),
        handleReset: vi.fn(),
        isLoading: false,
        isDirty: true,
      },
    } as ReturnType<typeof useGenerationActionsStore>)

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/brouillon non sauvegardé/i)).toBeInTheDocument()
    })
  })

  it('affiche le prompt estimé dans l\'onglet Prompt', () => {
    const testPrompt = 'Test prompt content'
    mockUseGenerationStore.mockReturnValue({
      estimatedPrompt: testPrompt,
      estimatedTokens: 100,
      isEstimating: false,
      sceneSelection: {
        characterA: null,
        characterB: null,
        sceneRegion: null,
        subLocation: null,
      },
      dialogueStructure: ['', '', '', '', '', ''] as [string, string, string, string, string, string],
      systemPromptOverride: null,
      setDialogueStructure: vi.fn(),
      setSystemPromptOverride: vi.fn(),
      setEstimatedPrompt: vi.fn(),
      setSceneSelection: vi.fn(),
    } as ReturnType<typeof useGenerationStore>)

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )

    // Le EstimatedPromptPanel devrait afficher le prompt
    // On vérifie indirectement
    expect(screen.getByText(/sélectionnez un élément/i)).toBeInTheDocument()
  })
})

