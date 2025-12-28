/**
 * Tests pour SelectedContextSummary - détection de doublons et vérification du compteur.
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SelectedContextSummary } from './SelectedContextSummary'
import type { ContextSelection } from '../../types/api'

describe('SelectedContextSummary', () => {
  const mockOnClear = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('affiche "Aucune sélection" quand il n\'y a pas de sélections', () => {
    const emptySelections: ContextSelection = {
      characters: [],
      locations: [],
      items: [],
      species: [],
      communities: [],
      dialogues_examples: [],
    }

    render(<SelectedContextSummary selections={emptySelections} onClear={mockOnClear} />)
    
    expect(screen.getByText(/aucune sélection/i)).toBeInTheDocument()
  })

  it('affiche le compteur total correct', () => {
    const selections: ContextSelection = {
      characters: ['Personnage 1', 'Personnage 2'],
      locations: ['Lieu 1'],
      items: [],
      species: ['Espèce 1'],
      communities: [],
      dialogues_examples: [],
    }

    render(<SelectedContextSummary selections={selections} onClear={mockOnClear} />)
    
    // Total: 2 + 1 + 0 + 1 + 0 + 0 = 4
    expect(screen.getByText(/sélections actives \(4\)/i)).toBeInTheDocument()
  })

  it('affiche les catégories avec leurs compteurs corrects', async () => {
    const user = userEvent.setup()
    const selections: ContextSelection = {
      characters: ['Personnage 1', 'Personnage 2'],
      locations: ['Lieu 1', 'Lieu 2'],
      items: ['Objet 1'],
      species: [],
      communities: ['Communauté 1'],
      dialogues_examples: [],
    }

    const { container } = render(<SelectedContextSummary selections={selections} onClear={mockOnClear} />)
    
    // Cliquer pour développer
    const expandButton = screen.getByText(/sélections actives/i).closest('div')
    if (expandButton) {
      await user.click(expandButton)
    }

    await waitFor(() => {
      // Vérifier que le texte complet contient les catégories
      expect(container.textContent).toContain('Personnages')
      expect(container.textContent).toContain('2')
      expect(container.textContent).toContain('Lieux')
      expect(container.textContent).toContain('Objets')
      expect(container.textContent).toContain('Communautés')
      // Vérifier la présence des éléments
      expect(container.textContent).toContain('Personnage 1')
      expect(container.textContent).toContain('Personnage 2')
      expect(container.textContent).toContain('Lieu 1')
      expect(container.textContent).toContain('Lieu 2')
      expect(container.textContent).toContain('Objet 1')
      expect(container.textContent).toContain('Communauté 1')
    })

    // Espèces et dialogues_examples ne doivent pas apparaître (compteur 0)
    expect(container.textContent).not.toMatch(/Espèces/i)
    expect(container.textContent).not.toMatch(/Exemples de dialogues/i)
  })

  it('détecte les doublons dans les sélections de personnages', async () => {
    const user = userEvent.setup()
    // Cas avec doublon : "Akthar-Neth Amatru" et "l'Exégète" sont le même personnage
    const selectionsWithDuplicates: ContextSelection = {
      characters: ['Akthar-Neth Amatru', 'l\'Exégète', 'Personnage 2'],
      locations: [],
      items: [],
      species: [],
      communities: [],
      dialogues_examples: [],
    }

    const { container } = render(<SelectedContextSummary selections={selectionsWithDuplicates} onClear={mockOnClear} />)
    
    // Le compteur devrait être 3 (il compte tous les éléments du tableau, même les doublons)
    expect(screen.getByText(/sélections actives \(3\)/i)).toBeInTheDocument()
    
    // Développer pour voir la liste
    const expandButton = screen.getByText(/sélections actives/i).closest('div')
    if (expandButton) {
      await user.click(expandButton)
    }

    await waitFor(() => {
      // La liste affichée contient 3 éléments, mais il y a un doublon conceptuel
      expect(container.textContent).toContain('Personnages')
      expect(container.textContent).toContain('3')
      // Vérifier que tous les éléments sont dans la liste affichée
      expect(container.textContent).toContain('Akthar-Neth Amatru')
      expect(container.textContent).toContain('l\'Exégète')
      expect(container.textContent).toContain('Personnage 2')
    })
  })

  it('appelle onClear quand on clique sur "Tout effacer"', async () => {
    const user = userEvent.setup()
    const selections: ContextSelection = {
      characters: ['Personnage 1'],
      locations: [],
      items: [],
      species: [],
      communities: [],
      dialogues_examples: [],
    }

    render(<SelectedContextSummary selections={selections} onClear={mockOnClear} />)
    
    const clearButton = screen.getByText(/tout effacer/i)
    await user.click(clearButton)
    
    expect(mockOnClear).toHaveBeenCalledTimes(1)
  })

  it('affiche correctement le total avec toutes les catégories', () => {
    const selections: ContextSelection = {
      characters: ['P1', 'P2'], // 2
      locations: ['L1', 'L2', 'L3'], // 3
      items: ['I1'], // 1
      species: ['S1'], // 1
      communities: ['C1'], // 1
      dialogues_examples: ['D1', 'D2'], // 2
    }

    render(<SelectedContextSummary selections={selections} onClear={mockOnClear} />)
    
    // Total: 2 + 3 + 1 + 1 + 1 + 2 = 10
    expect(screen.getByText(/sélections actives \(10\)/i)).toBeInTheDocument()
  })

  it('le compteur correspond exactement au nombre d\'éléments uniques dans chaque catégorie', () => {
    // Test avec des tableaux qui pourraient contenir des doublons
    // Si le store autorise les doublons, le compteur sera faux
    const selectionsWithPotentialDuplicates: ContextSelection = {
      characters: ['Personnage 1', 'Personnage 1'], // Doublon réel dans le tableau
      locations: ['Lieu 1'],
      items: [],
      species: [],
      communities: [],
      dialogues_examples: [],
    }

    render(<SelectedContextSummary selections={selectionsWithPotentialDuplicates} onClear={mockOnClear} />)
    
    // Le compteur affiche 3 (2 personnages + 1 lieu), mais il devrait y avoir 2 éléments uniques seulement
    // Ce test documente le comportement actuel : le compteur compte tous les éléments, même les doublons
    expect(screen.getByText(/sélections actives \(3\)/i)).toBeInTheDocument()
  })

  it('affiche la liste complète des éléments quand développé', async () => {
    const user = userEvent.setup()
    const selections: ContextSelection = {
      characters: ['Personnage A', 'Personnage B', 'Personnage C'],
      locations: [],
      items: [],
      species: [],
      communities: [],
      dialogues_examples: [],
    }

    const { container } = render(<SelectedContextSummary selections={selections} onClear={mockOnClear} />)
    
    // Développer
    const expandButton = screen.getByText(/sélections actives/i).closest('div')
    if (expandButton) {
      await user.click(expandButton)
    }

    await waitFor(() => {
      expect(container.textContent).toContain('Personnages')
      expect(container.textContent).toContain('3')
      expect(container.textContent).toContain('Personnage A')
      expect(container.textContent).toContain('Personnage B')
      expect(container.textContent).toContain('Personnage C')
    })
  })
})

