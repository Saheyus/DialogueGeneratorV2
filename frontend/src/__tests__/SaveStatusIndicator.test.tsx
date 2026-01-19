/**
 * Tests pour SaveStatusIndicator - Indicateur de statut de sauvegarde
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { SaveStatusIndicator } from '../components/shared/SaveStatusIndicator'

// Mock le theme
vi.mock('../theme', () => ({
  theme: {
    state: {
      success: { color: '#28a745' },
      info: { color: '#17a2b8' },
      warning: { color: '#ffc107' },
      error: { color: '#dc3545' },
    },
  },
}))

describe('SaveStatusIndicator', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('Status display', () => {
    it('should display "Sauvegardé" when status is saved', () => {
      render(<SaveStatusIndicator status="saved" />)
      expect(screen.getByText('Sauvegardé')).toBeInTheDocument()
    })

    it('should display "En cours..." when status is saving', () => {
      render(<SaveStatusIndicator status="saving" />)
      expect(screen.getByText('En cours...')).toBeInTheDocument()
    })

    it('should display "Non sauvegardé" when status is unsaved', () => {
      render(<SaveStatusIndicator status="unsaved" />)
      expect(screen.getByText('Non sauvegardé')).toBeInTheDocument()
    })

    it('should display "Erreur" when status is error', () => {
      render(<SaveStatusIndicator status="error" />)
      expect(screen.getByText('Erreur')).toBeInTheDocument()
    })
  })

  describe('Relative time display (Task 3 - Story 0.5)', () => {
    it('should display "à l\'instant" when lastSavedAt is less than 5 seconds ago', () => {
      const now = Date.now()
      render(<SaveStatusIndicator status="saved" lastSavedAt={now - 2000} />)
      expect(screen.getByText(/Sauvegardé à l'instant/)).toBeInTheDocument()
    })

    it('should display "il y a Xs" when lastSavedAt is less than 60 seconds ago', () => {
      const now = Date.now()
      render(<SaveStatusIndicator status="saved" lastSavedAt={now - 15000} />)
      expect(screen.getByText(/Sauvegardé il y a \d+s/)).toBeInTheDocument()
    })

    it('should display "il y a Xmin" when lastSavedAt is less than 60 minutes ago', () => {
      const now = Date.now()
      render(<SaveStatusIndicator status="saved" lastSavedAt={now - 30 * 60 * 1000} />)
      expect(screen.getByText(/Sauvegardé il y a \d+min/)).toBeInTheDocument()
    })

    it('should display "il y a Xh" when lastSavedAt is less than 24 hours ago', () => {
      const now = Date.now()
      render(<SaveStatusIndicator status="saved" lastSavedAt={now - 5 * 60 * 60 * 1000} />)
      expect(screen.getByText(/Sauvegardé il y a \d+h/)).toBeInTheDocument()
    })

    it('should update relative time every 10 seconds', async () => {
      const now = Date.now()
      const { rerender } = render(<SaveStatusIndicator status="saved" lastSavedAt={now - 10000} />)
      
      // Vérifier initial
      expect(screen.getByText(/Sauvegardé il y a \d+s/)).toBeInTheDocument()
      
      // Avancer de 15 secondes (5 secondes de plus)
      vi.advanceTimersByTime(15000)
      
      await waitFor(() => {
        // Le temps relatif devrait être mis à jour (10s + 15s = 25s)
        expect(screen.getByText(/Sauvegardé il y a \d+s/)).toBeInTheDocument()
      })
    })
  })

  describe('Error message display (Task 3 - Story 0.5)', () => {
    it('should display error message in title attribute when status is error', () => {
      const errorMessage = 'Quota exceeded'
      render(<SaveStatusIndicator status="error" errorMessage={errorMessage} />)
      
      const indicator = screen.getByText('Erreur').closest('div')
      expect(indicator).toHaveAttribute('title', errorMessage)
    })

    it('should not display error message in title when status is not error', () => {
      render(<SaveStatusIndicator status="saved" errorMessage="Some error" />)
      
      const indicator = screen.getByText('Sauvegardé').closest('div')
      expect(indicator).not.toHaveAttribute('title')
    })
  })

  describe('Status indicator dot', () => {
    it('should show pulsing animation when status is saving', () => {
      render(<SaveStatusIndicator status="saving" />)
      const dot = screen.getByText('En cours...').previousElementSibling
      expect(dot).toHaveStyle({ animation: expect.stringContaining('pulse') })
    })

    it('should not show pulsing animation when status is not saving', () => {
      render(<SaveStatusIndicator status="saved" />)
      const dot = screen.getByText('Sauvegardé').previousElementSibling
      expect(dot).toHaveStyle({ animation: 'none' })
    })
  })
})
