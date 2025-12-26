import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ContextDetail } from './ContextDetail'
import type { CharacterResponse, LocationResponse, ItemResponse } from '../../types/api'

describe('ContextDetail', () => {
  it('affiche un message quand aucun élément n\'est sélectionné', () => {
    render(<ContextDetail item={null} />)
    
    expect(screen.getByText(/sélectionnez un élément/i)).toBeInTheDocument()
  })

  it('affiche les détails d\'un personnage', () => {
    const character: CharacterResponse = {
      name: 'Test Character',
      data: {
        description: 'A test character',
        portrait: 'A portrait description',
        tags: ['tag1', 'tag2'],
        traits: ['trait1', 'trait2'],
        rôle_narratif: 'Protagonist',
      },
    }

    render(<ContextDetail item={character} />)

    expect(screen.getByText('Test Character')).toBeInTheDocument()
    expect(screen.getAllByText(/portrait/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/tags/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/traits/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/rôle narratif/i).length).toBeGreaterThan(0)
  })

  it('affiche les détails d\'un lieu', () => {
    const location: LocationResponse = {
      name: 'Test Location',
      data: {
        description: 'A test location',
        region: 'Test Region',
        type: 'City',
      },
    }

    render(<ContextDetail item={location} />)

    expect(screen.getByText('Test Location')).toBeInTheDocument()
    expect(screen.getByText(/détails complets/i)).toBeInTheDocument()
  })

  it('affiche les détails d\'un objet', () => {
    const item: ItemResponse = {
      name: 'Test Item',
      data: {
        description: 'A test item',
        type: 'Weapon',
        rarity: 'Common',
      },
    }

    render(<ContextDetail item={item} />)

    expect(screen.getByText('Test Item')).toBeInTheDocument()
    expect(screen.getByText(/détails complets/i)).toBeInTheDocument()
  })

  it('affiche les données imbriquées correctement', () => {
    const character: CharacterResponse = {
      name: 'Test Character',
      data: {
        description: 'A test character',
        nested: {
          level1: {
            level2: 'Deep value',
          },
        },
      },
    }

    render(<ContextDetail item={character} />)

    expect(screen.getByText('Test Character')).toBeInTheDocument()
    expect(screen.getByText(/nested/i)).toBeInTheDocument()
  })

  it('affiche les tableaux correctement', () => {
    const character: CharacterResponse = {
      name: 'Test Character',
      data: {
        description: 'A test character',
        skills: ['Skill 1', 'Skill 2', 'Skill 3'],
      },
    }

    render(<ContextDetail item={character} />)

    expect(screen.getByText('Test Character')).toBeInTheDocument()
    expect(screen.getByText(/skills/i)).toBeInTheDocument()
  })
})

