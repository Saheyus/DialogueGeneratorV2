/**
 * Panneau d'affichage du prompt brut (RawPrompt).
 * Source de vérité unique pour ce qui est envoyé au LLM.
 */
import { memo, useState, useCallback } from 'react'
import { usePromptPreview } from '../../hooks/usePromptPreview'
import { StructuredPromptView } from './StructuredPromptView'
import { theme } from '../../theme'
import { useToast } from '../shared'
import { useGenerationStore } from '../../store/generationStore'
import type { RawPrompt } from '../../types/api'
import type { PromptStructure } from '../../types/prompt'

export interface EstimatedPromptPanelProps {
  /** Le prompt brut à afficher (RawPrompt) */
  raw_prompt: RawPrompt | null | undefined
  /** Indique si l'estimation est en cours */
  isEstimating?: boolean
  /** Nombre de tokens */
  tokenCount?: number | null
  /** Hash du prompt pour validation */
  promptHash?: string | null
  /** Structure JSON du prompt (optionnel) */
  structuredPrompt?: PromptStructure | null
}

export const EstimatedPromptPanel = memo(function EstimatedPromptPanel({
  raw_prompt,
  isEstimating = false,
  tokenCount,
  promptHash,
  structuredPrompt: structuredPromptProp,
}: EstimatedPromptPanelProps) {
  const [viewMode, setViewMode] = useState<'raw' | 'structured'>('structured')
  const toast = useToast()
  
  // Récupérer structuredPrompt depuis le store si non fourni en prop
  const structuredPromptFromStore = useGenerationStore((state) => state.structuredPrompt)
  const structuredPrompt = structuredPromptProp ?? structuredPromptFromStore
  
  const { sections } = usePromptPreview(raw_prompt, structuredPrompt)
  
  const handleCopyPrompt = useCallback(() => {
    if (!raw_prompt) return
    
    navigator.clipboard.writeText(raw_prompt)
      .then(() => {
        toast('Prompt copié dans le presse-papier', 'success', 2000)
      })
      .catch(() => {
        toast('Erreur lors de la copie', 'error', 2000)
      })
  }, [raw_prompt, toast])
  
  // Calculer le total comme la somme des tokens de chaque section
  const calculatedTotal = sections.reduce((sum, section) => {
    return sum + (section.tokenCount || 0)
  }, 0)
  
  // Utiliser le total calculé à partir des sections si on a des sections, sinon utiliser tokenCount du backend
  const displayTotal = sections.length > 0 ? calculatedTotal : (tokenCount ?? null)

  return (
    <>
      <div
        style={{
          flex: 1,
          minHeight: 0,
          maxHeight: '100%',
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
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          {isEstimating ? (
            <div style={{ color: theme.text.secondary }}>Estimation en cours...</div>
          ) : displayTotal !== null && displayTotal !== undefined ? (
            <>
              <div style={{ color: theme.text.primary }}>
                <strong>Tokens:</strong> {displayTotal.toLocaleString()}
              </div>
              {promptHash && (
                <div style={{ color: theme.text.tertiary, fontSize: '0.7rem', fontFamily: 'monospace' }}>
                  HASH: {promptHash.slice(0, 16)}...
                </div>
              )}
            </>
          ) : null}
        </div>
        {raw_prompt && !isEstimating && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              color: theme.text.secondary,
              fontSize: '0.85rem',
            }}
          >
            {viewMode === 'raw' && (
              <button
                type="button"
                onClick={handleCopyPrompt}
                style={{
                  padding: '0.5rem 1rem',
                  border: `1px solid ${theme.border.primary}`,
                  borderRadius: '4px',
                  backgroundColor: theme.background.secondary,
                  color: theme.text.primary,
                  cursor: 'pointer',
                  fontSize: '0.85rem',
                  transition: 'background-color 0.2s',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = theme.background.panel
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = theme.background.secondary
                }}
              >
                📋 Copier
              </button>
            )}
            <span style={{ color: viewMode === 'raw' ? theme.text.primary : theme.text.secondary }}>
              Brut (Réel)
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
          flex: '1 1 0%',
          minHeight: 0,
          height: 0,
          overflowY: 'auto',
          overflowX: 'hidden',
          padding: '1rem',
          boxSizing: 'border-box',
          scrollbarGutter: 'stable',
        }}
      >
        {raw_prompt ? (
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
              {raw_prompt}
            </pre>
          ) : (
            <StructuredPromptView prompt={raw_prompt} structuredPrompt={structuredPrompt} />
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
              ? 'Construction du prompt...'
              : 'Aucun prompt disponible. Configurez votre génération.'}
          </div>
        )}
      </div>
    </div>
    </>
  )
})


