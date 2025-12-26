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
    <div
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: theme.background.panel,
      }}
    >
      <div style={{ padding: '1rem', borderBottom: `1px solid ${theme.border.primary}` }}>
        {isEstimating ? (
          <div style={{ color: theme.text.secondary }}>Estimation en cours...</div>
        ) : estimatedTokens !== null && estimatedTokens !== undefined ? (
          <div style={{ color: theme.text.primary }}>
            <strong>Tokens estimés:</strong> {estimatedTokens.toLocaleString()}
          </div>
        ) : null}
      </div>
      <div style={{ flex: 1, overflow: 'auto', padding: '1rem' }}>
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
  )
})

