/**
 * Panneau d'affichage du prompt estimé.
 */
import { memo } from 'react'
import { usePromptPreview } from '../../hooks/usePromptPreview'
import { theme } from '../../theme'

export interface EstimatedPromptPanelProps {
  /** Le prompt estimé à afficher */
  estimatedPrompt: string | null | undefined
  /** Indique si l'estimation est en cours */
  isEstimating?: boolean
  /** Nombre de tokens estimés */
  estimatedTokens?: number | null
}

export const EstimatedPromptPanel = memo(function EstimatedPromptPanel({
  estimatedPrompt,
  isEstimating = false,
  estimatedTokens,
}: EstimatedPromptPanelProps) {
  const { formattedPrompt } = usePromptPreview(estimatedPrompt)

  return (
    <>
      <style>{`
        .estimated-prompt-scroll-container {
          scrollbar-width: thin;
          scrollbar-color: ${theme.border.primary} ${theme.background.panel};
        }
        .estimated-prompt-scroll-container::-webkit-scrollbar {
          width: 12px;
        }
        .estimated-prompt-scroll-container::-webkit-scrollbar-track {
          background: ${theme.background.panel};
        }
        .estimated-prompt-scroll-container::-webkit-scrollbar-thumb {
          background-color: ${theme.border.primary};
          border-radius: 6px;
          border: 2px solid ${theme.background.panel};
        }
        .estimated-prompt-scroll-container::-webkit-scrollbar-thumb:hover {
          background-color: ${theme.button.primary.background};
        }
      `}</style>
      <div
        style={{
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: theme.background.panel,
          overflow: 'hidden',
        }}
      >
      <div style={{ 
        padding: '1rem', 
        borderBottom: `1px solid ${theme.border.primary}`,
        flexShrink: 0,
      }}>
        {isEstimating ? (
          <div style={{ color: theme.text.secondary }}>Estimation en cours...</div>
        ) : estimatedTokens !== null && estimatedTokens !== undefined ? (
          <div style={{ color: theme.text.primary }}>
            <strong>Tokens estimés:</strong> {estimatedTokens.toLocaleString()}
          </div>
        ) : null}
      </div>
      <div 
        className="estimated-prompt-scroll-container"
        style={{ 
          flex: 1, 
          minHeight: 0,
          overflowY: 'auto',
          overflowX: 'hidden',
          padding: '1rem',
          boxSizing: 'border-box',
        }}
      >
        {formattedPrompt ? (
          <pre
            style={{
              fontFamily: 'monospace',
              fontSize: '0.85rem',
              lineHeight: '1.6',
              color: theme.text.secondary,
              backgroundColor: theme.background.secondary,
              padding: '1rem',
              borderRadius: '4px',
              border: `1px solid ${theme.border.primary}`,
              whiteSpace: 'pre-wrap',
              wordWrap: 'break-word',
              margin: 0,
            }}
          >
            {formattedPrompt}
          </pre>
        ) : (
          <div
            style={{
              padding: '2rem',
              textAlign: 'center',
              color: theme.text.secondary,
            }}
          >
            {isEstimating
              ? 'Estimation du prompt en cours...'
              : 'Aucun prompt estimé disponible. Configurez votre génération pour voir le prompt estimé.'}
          </div>
        )}
      </div>
    </div>
    </>
  )
})

