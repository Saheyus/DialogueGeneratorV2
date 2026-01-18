/**
 * Modal de progression de génération LLM avec streaming SSE.
 * 
 * Affiche le texte généré en temps réel, la progression par étapes,
 * et permet l'interruption ou la réduction de la modal.
 */
import { useEffect } from 'react'
import { theme } from '../../theme'

export interface GenerationProgressModalProps {
  /** Contrôle l'affichage de la modal */
  isOpen: boolean
  /** Contenu streamé du LLM (caractère par caractère) */
  content: string
  /** Étape actuelle : Prompting | Generating | Validating | Complete */
  currentStep: 'Prompting' | 'Generating' | 'Validating' | 'Complete'
  /** La modal est-elle réduite (badge compact) */
  isMinimized?: boolean
  /** Message d'erreur si génération échouée */
  error?: string | null
  /** Callback pour interrompre la génération */
  onInterrupt: () => void
  /** Callback pour réduire/agrandir la modal */
  onMinimize: () => void
  /** Callback pour fermer la modal (après complétion) */
  onClose: () => void
}

/**
 * Composant Modal de progression de génération.
 * 
 * Pattern : Suivre structure GenerationOptionsModal (overlay + header + content scrollable).
 * 
 * États :
 * - Modal pleine : affichage central avec streaming visible
 * - Badge réduit : coin écran (bottom-right) avec progression compacte
 * - État terminé : bouton "Fermer" + auto-fermeture après 3s
 */
export function GenerationProgressModal({
  isOpen,
  content,
  currentStep,
  isMinimized = false,
  error = null,
  onInterrupt,
  onMinimize,
  onClose,
}: GenerationProgressModalProps) {
  // Auto-fermeture 3 secondes après complétion (si pas réduit)
  useEffect(() => {
    if (currentStep === 'Complete' && !isMinimized && !error) {
      const timer = setTimeout(() => {
        onClose()
      }, 3000)
      return () => clearTimeout(timer)
    }
  }, [currentStep, isMinimized, error, onClose])

  if (!isOpen) return null

  // Mapping des étapes pour la barre de progression
  const steps = ['Prompting', 'Generating', 'Validating', 'Complete']
  const currentStepIndex = steps.indexOf(currentStep)
  const progressPercentage = ((currentStepIndex + 1) / steps.length) * 100

  // Badge réduit (coin écran)
  if (isMinimized) {
    return (
      <div
        style={{
          position: 'fixed',
          bottom: '1rem',
          right: '1rem',
          backgroundColor: theme.background.panel,
          borderRadius: '8px',
          padding: '1rem',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
          zIndex: 1000,
          minWidth: '200px',
          border: `1px solid ${theme.border.primary}`,
        }}
        onClick={onMinimize} // Clic sur le badge agrandit la modal
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div
            style={{
              width: '12px',
              height: '12px',
              borderRadius: '50%',
              backgroundColor: error ? theme.state.error.color : theme.border.focus,
              animation: error ? 'none' : 'pulse 1.5s ease-in-out infinite',
            }}
          />
          <span style={{ color: theme.text.primary, fontSize: '0.9rem' }}>
            {error ? 'Erreur' : currentStep}
          </span>
        </div>
        <style>{`
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
          }
        `}</style>
      </div>
    )
  }

  // Modal pleine
  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.7)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
      }}
      onClick={(e) => {
        // Empêcher la fermeture par clic overlay pendant génération
        if (currentStep !== 'Complete') {
          e.stopPropagation()
        }
      }}
    >
      <div
        style={{
          backgroundColor: theme.background.panel,
          borderRadius: '8px',
          width: '90%',
          maxWidth: '800px',
          maxHeight: '80vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
          overflow: 'hidden',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: '1.5rem',
            borderBottom: `1px solid ${theme.border.primary}`,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexShrink: 0,
          }}
        >
          <h2 style={{ margin: 0, color: theme.text.primary }}>
            {currentStep === 'Complete' ? 'Génération terminée' : 'Génération en cours...'}
          </h2>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            {currentStep !== 'Complete' && (
              <button
                onClick={onMinimize}
                aria-label="Réduire"
                style={{
                  background: 'none',
                  border: 'none',
                  color: theme.text.secondary,
                  fontSize: '1.5rem',
                  cursor: 'pointer',
                  padding: '0.25rem 0.5rem',
                }}
                title="Réduire"
              >
                –
              </button>
            )}
          </div>
        </div>

        {/* Progress Bar */}
        {currentStep !== 'Complete' && !error && (
          <div
            style={{
              padding: '1rem 1.5rem',
              borderBottom: `1px solid ${theme.border.primary}`,
              flexShrink: 0,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              {steps.map((step, index) => (
                <span
                  key={step}
                  style={{
                    fontSize: '0.85rem',
                    color: index <= currentStepIndex ? theme.text.primary : theme.text.secondary,
                    fontWeight: index === currentStepIndex ? 'bold' : 'normal',
                  }}
                >
                  {step}
                </span>
              ))}
            </div>
            <div
              style={{
                width: '100%',
                height: '8px',
                backgroundColor: theme.input.background,
                borderRadius: '4px',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  width: `${progressPercentage}%`,
                  height: '100%',
                  backgroundColor: theme.border.focus,
                  transition: 'width 0.3s ease',
                }}
              />
            </div>
          </div>
        )}

        {/* Content - Streaming Text */}
        <div
          style={{
            flex: 1,
            overflow: 'auto',
            padding: '1.5rem',
            minHeight: 0,
          }}
        >
          {error ? (
            <div
              style={{
                padding: '1rem',
                backgroundColor: theme.state.error.background,
                color: theme.state.error.color,
                borderRadius: '4px',
              }}
            >
              {error}
            </div>
          ) : (
            <pre
              style={{
                margin: 0,
                fontFamily: 'monospace',
                fontSize: '0.9rem',
                color: theme.text.primary,
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}
            >
              {content || 'Préparation...'}
            </pre>
          )}
        </div>

        {/* Footer - Actions */}
        <div
          style={{
            padding: '1rem 1.5rem',
            borderTop: `1px solid ${theme.border.primary}`,
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '0.5rem',
            flexShrink: 0,
          }}
        >
          {currentStep === 'Complete' ? (
            <button
              onClick={onClose}
              style={{
                padding: '0.5rem 1rem',
                border: 'none',
                borderRadius: '4px',
                backgroundColor: theme.button.primary.background,
                color: theme.button.primary.color,
                cursor: 'pointer',
              }}
            >
              Fermer
            </button>
          ) : (
            <button
              onClick={onInterrupt}
              style={{
                padding: '0.5rem 1rem',
                border: `1px solid ${theme.border.primary}`,
                borderRadius: '4px',
                backgroundColor: theme.button.default.background,
                color: theme.button.default.color,
                cursor: 'pointer',
              }}
            >
              Interrompre
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
