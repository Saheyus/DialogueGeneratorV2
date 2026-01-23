/**
 * Modal d'aide affichant tous les raccourcis clavier disponibles.
 */
import { useState, useEffect } from 'react'
import { theme } from '../../theme'
import { getAllShortcuts, formatShortcut } from '../../hooks/useKeyboardShortcuts'

export interface KeyboardShortcutsHelpProps {
  isOpen: boolean
  onClose: () => void
}

const DEFAULT_SHORTCUTS = [
  { key: 'ctrl+enter', description: 'Générer un dialogue' },
  { key: 'alt+s', description: 'Échanger les personnages (swap)' },
  { key: 'ctrl+k', description: 'Ouvrir la palette de commandes' },
  { key: '/', description: 'Filtrer dans le panneau de gauche' },
  { key: 'ctrl+e', description: 'Exporter le dialogue Unity' },
  { key: 'ctrl+s', description: 'Sauvegarder le dialogue' },
  { key: 'ctrl+n', description: 'Nouveau dialogue (réinitialiser)' },
  { key: 'ctrl+,', description: 'Ouvrir les options' },
  { key: 'escape', description: 'Fermer les modals/panels' },
  { key: 'ctrl+/', description: 'Afficher cette aide' },
  { key: 'ctrl+1', description: 'Naviguer vers Dashboard' },
  { key: 'ctrl+2', description: 'Naviguer vers Dialogues Unity' },
  { key: 'ctrl+3', description: 'Naviguer vers Usage/Statistiques' },
]

export function KeyboardShortcutsHelp({ isOpen, onClose }: KeyboardShortcutsHelpProps) {
  const [shortcuts, setShortcuts] = useState(DEFAULT_SHORTCUTS)

  useEffect(() => {
    if (isOpen) {
      // Récupérer les raccourcis dynamiques enregistrés
      const dynamicShortcuts = getAllShortcuts()
      const combined = [...DEFAULT_SHORTCUTS, ...dynamicShortcuts]
      
      // Dédupliquer par key (garder la première occurrence)
      const unique = new Map<string, { key: string; description: string }>()
      combined.forEach(s => {
        if (!unique.has(s.key)) {
          unique.set(s.key, s)
        }
      })
      
      setShortcuts(Array.from(unique.values()))
    }
  }, [isOpen])

  // Fermer avec Escape
  useEffect(() => {
    if (!isOpen) return
    
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 10000,
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: theme.background.panel,
          borderRadius: '8px',
          padding: '2rem',
          maxWidth: '600px',
          width: '90%',
          maxHeight: '80vh',
          overflowY: 'auto',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2 style={{ margin: 0, color: theme.text.primary }}>Raccourcis clavier</h2>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '1.5rem',
              cursor: 'pointer',
              color: theme.text.secondary,
              padding: '0.25rem 0.5rem',
            }}
            aria-label="Fermer"
          >
            ×
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {shortcuts.map((shortcut, index) => (
            <div
              key={index}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '0.75rem',
                backgroundColor: theme.background.secondary,
                borderRadius: '4px',
              }}
            >
              <span style={{ color: theme.text.secondary }}>{shortcut.description}</span>
              <kbd
                style={{
                  padding: '0.25rem 0.5rem',
                  backgroundColor: theme.input.background,
                  border: `1px solid ${theme.border.primary}`,
                  borderRadius: '4px',
                  fontSize: '0.85rem',
                  fontFamily: 'monospace',
                  color: theme.text.primary,
                  boxShadow: '0 1px 2px rgba(0, 0, 0, 0.1)',
                }}
              >
                {formatShortcut(shortcut.key)}
              </kbd>
            </div>
          ))}
        </div>

        <div
          style={{
            marginTop: '1.5rem',
            paddingTop: '1rem',
            borderTop: `1px solid ${theme.border.primary}`,
            fontSize: '0.85rem',
            color: theme.text.secondary,
            textAlign: 'center',
          }}
        >
          Appuyez sur <kbd style={{ padding: '0.125rem 0.25rem', backgroundColor: theme.input.background, borderRadius: '2px' }}>Esc</kbd> pour fermer
        </div>
      </div>
    </div>
  )
}

