/**
 * Panneau d'affichage du prompt estimé.
 */
import { memo, useState } from 'react'
import { usePromptPreview } from '../../hooks/usePromptPreview'
import { StructuredPromptView } from './StructuredPromptView'
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
  const [viewMode, setViewMode] = useState<'raw' | 'structured'>('structured')

  return (
    <>
      {/* Pas de styles personnalisés : utilise les scrollbars par défaut du navigateur, comme les autres composants (ContextList, ContextSelector) */}
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
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <div>
          {isEstimating ? (
            <div style={{ color: theme.text.secondary }}>Estimation en cours...</div>
          ) : estimatedTokens !== null && estimatedTokens !== undefined ? (
            <div style={{ color: theme.text.primary }}>
              <strong>Tokens estimés:</strong> {estimatedTokens.toLocaleString()}
            </div>
          ) : null}
        </div>
        {estimatedPrompt && !isEstimating && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              color: theme.text.secondary,
              fontSize: '0.85rem',
            }}
          >
            <span style={{ color: viewMode === 'raw' ? theme.text.primary : theme.text.secondary }}>
              Brut
            </span>
            <label
              style={{
                position: 'relative',
                display: 'inline-block',
                width: '44px',
                height: '24px',
                cursor: 'pointer',
              }}
            >
              <input
                type="checkbox"
                checked={viewMode === 'structured'}
                onChange={(e) => setViewMode(e.target.checked ? 'structured' : 'raw')}
                style={{
                  opacity: 0,
                  width: 0,
                  height: 0,
                }}
              />
              <span
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  backgroundColor: viewMode === 'structured' ? theme.border.focus : theme.input.border,
                  borderRadius: '12px',
                  transition: 'background-color 0.2s',
                }}
              />
              <span
                style={{
                  position: 'absolute',
                  top: '2px',
                  left: viewMode === 'structured' ? '22px' : '2px',
                  width: '20px',
                  height: '20px',
                  borderRadius: '50%',
                  backgroundColor: 'white',
                  transition: 'left 0.2s',
                  boxShadow: '0 2px 4px rgba(0, 0, 0, 0.2)',
                }}
              />
            </label>
            <span style={{ color: viewMode === 'structured' ? theme.text.primary : theme.text.secondary }}>
              Structuré
            </span>
          </div>
        )}
      </div>
      <div 
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
          viewMode === 'raw' ? (
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
            <StructuredPromptView prompt={estimatedPrompt!} />
          )
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

