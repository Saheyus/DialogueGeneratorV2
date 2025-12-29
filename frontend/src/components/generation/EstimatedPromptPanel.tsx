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
          /* Firefox - scrollbar visible */
          scrollbar-width: auto;
          scrollbar-color: #9d4edd #1a1a1a;
          scrollbar-gutter: stable;
        }
        .estimated-prompt-scroll-container::-webkit-scrollbar {
          width: 50px !important;
          display: block !important;
          -webkit-appearance: none !important;
        }
        .estimated-prompt-scroll-container::-webkit-scrollbar-track {
          background: #1a1a1a !important;
          border-left: 3px solid #9d4edd !important;
          -webkit-box-shadow: inset 0 0 6px rgba(157, 78, 221, 0.3) !important;
        }
        .estimated-prompt-scroll-container::-webkit-scrollbar-thumb {
          background-color: #9d4edd !important;
          border-radius: 10px !important;
          border: 5px solid #1a1a1a !important;
          min-height: 100px !important;
          -webkit-box-shadow: inset 0 0 6px rgba(157, 78, 221, 0.5) !important;
        }
        .estimated-prompt-scroll-container::-webkit-scrollbar-thumb:hover {
          background-color: #c77dff !important;
        }
        .estimated-prompt-scroll-container::-webkit-scrollbar-thumb:active {
          background-color: #7b2cbf !important;
        }
        /* Force la scrollbar à être toujours visible, même au repos */
        .estimated-prompt-scroll-container:hover::-webkit-scrollbar-thumb {
          background-color: #9d4edd !important;
        }
      `}</style>
      <div
        style={{
          flex: 1,
          minHeight: 0,
          maxHeight: '100%', // Force le conteneur à respecter la hauteur du parent
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
          flex: '1 1 0%', // Utilise flex-basis: 0% pour forcer le respect de la hauteur parent
          minHeight: 0,
          height: 0, // Force le conteneur à respecter la hauteur du parent flex
          // NE PAS utiliser overflow: 'auto' car React le combine mal avec overflowX/overflowY
          // Utiliser overflowY et overflowX séparément (comme ContextSelector ligne 330)
          overflowY: 'auto', // Comme les autres scrollbars visibles de l'app
          overflowX: 'hidden', // Pas de scroll horizontal
          padding: '1rem',
          boxSizing: 'border-box',
          // Force la scrollbar à être visible
          scrollbarGutter: 'stable',
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

