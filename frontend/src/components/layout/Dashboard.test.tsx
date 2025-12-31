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
      rawPrompt: '',
      tokenCount: 0,
      promptHash: null,
      isEstimating: false,
      unityDialogueResponse: null,
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
      setRawPrompt: vi.fn(),
      setSceneSelection: vi.fn(),
      setUnityDialogueResponse: vi.fn(),
      tokensUsed: null,
      setTokensUsed: vi.fn(),
      clearGenerationResults: vi.fn(),
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
    expect(screen.getByTestId('context-selector')).toBeInTheDocument()
    expect(screen.getByTestId('generation-panel')).toBeInTheDocument()
    // Les onglets devraient être présents
    expect(screen.getAllByText(/prompt estimé/i).length).toBeGreaterThan(0)
    expect(screen.getByText(/détails/i)).toBeInTheDocument()
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

  it('affiche les onglets dans le panneau de droite', () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )

    // Il y a plusieurs éléments avec "prompt estimé" (bouton et contenu)
    expect(screen.getAllByText(/prompt estimé/i).length).toBeGreaterThan(0)
    expect(screen.getByText(/dialogue unity/i)).toBeInTheDocument()
    expect(screen.getByText(/détails/i)).toBeInTheDocument()
  })

  it('affiche le message par défaut dans l\'onglet Détails', async () => {
    const user = userEvent.setup()
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )

    // Cliquer sur l'onglet Détails pour l'activer
    const detailsTab = screen.getByText(/détails/i)
    await user.click(detailsTab)

    // Maintenant le message devrait être visible
    await waitFor(() => {
      expect(screen.getByText(/sélectionnez un élément de contexte ou une interaction pour voir ses détails/i)).toBeInTheDocument()
    })
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

  it('affiche le prompt estimé dans l\'onglet Prompt', async () => {
    const testPrompt = 'Test prompt content'
    mockUseGenerationStore.mockReturnValue({
      rawPrompt: testPrompt,
      tokenCount: 100,
      promptHash: 'hash123',
      isEstimating: false,
      unityDialogueResponse: null,
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
      setRawPrompt: vi.fn(),
      setSceneSelection: vi.fn(),
      setUnityDialogueResponse: vi.fn(),
      tokensUsed: null,
      setTokensUsed: vi.fn(),
      clearGenerationResults: vi.fn(),
    } as ReturnType<typeof useGenerationStore>)


    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )

    // Le EstimatedPromptPanel devrait afficher le prompt
    await waitFor(() => {
      expect(screen.getByText(testPrompt)).toBeInTheDocument()
    })
  })

  it('affiche UnityDialogueViewer quand unityDialogueResponse est présent', () => {
    const mockUnityResponse = {
      json_content: JSON.stringify([{ id: 'START', speaker: 'NPC', line: 'Hello' }]),
      title: 'Test Dialogue',
      estimated_tokens: 100,
    }

    mockUseGenerationStore.mockReturnValue({
      rawPrompt: '',
      tokenCount: 0,
      promptHash: null,
      isEstimating: false,
      unityDialogueResponse: mockUnityResponse,
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
      setRawPrompt: vi.fn(),
      setSceneSelection: vi.fn(),
      setUnityDialogueResponse: vi.fn(),
      tokensUsed: null,
      setTokensUsed: vi.fn(),
      clearGenerationResults: vi.fn(),
    } as ReturnType<typeof useGenerationStore>)


    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )

    expect(screen.getByText('Test Dialogue')).toBeInTheDocument()
  })

  it('affiche un message quand aucun dialogue Unity n\'est généré', async () => {
    const user = userEvent.setup()
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    )

    // Cliquer sur l'onglet Dialogue Unity
    const dialogueTab = screen.getByText(/dialogue unity/i)
    await user.click(dialogueTab)

    await waitFor(() => {
      expect(screen.getByText(/aucun dialogue unity généré/i)).toBeInTheDocument()
    })
  })
})

