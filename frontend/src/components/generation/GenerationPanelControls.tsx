/**
 * Composant pour les contrôles de génération (sliders tokens, max choix, tags narratifs).
 */
import { useRef } from 'react'
import { CONTEXT_TOKENS_LIMITS } from '../../constants'
import { theme } from '../../theme'

export interface GenerationPanelControlsProps {
  /** Max tokens pour contexte */
  maxContextTokens: number
  /** Max tokens pour completion (null = auto) */
  maxCompletionTokens: number | null
  /** Nombre max de choix (null = libre) */
  maxChoices: number | null
  /** Tags narratifs sélectionnés */
  narrativeTags: string[]
  /** Tags narratifs disponibles */
  availableNarrativeTags: string[]
  /** Erreurs de validation */
  validationErrors: Record<string, string>
  /** Token count estimé */
  tokenCount: number | null
  /** Callback pour maxContextTokens */
  onMaxContextTokensChange: (value: number) => void
  /** Callback pour maxCompletionTokens */
  onMaxCompletionTokensChange: (value: number | null) => void
  /** Callback pour maxChoices */
  onMaxChoicesChange: (value: number | null) => void
  /** Callback pour narrativeTags */
  onNarrativeTagsChange: (tags: string[]) => void
  /** Callback pour marquer comme dirty */
  onDirty: () => void
}

/**
 * Contrôles de génération (sliders tokens, max choix, tags narratifs).
 */
export function GenerationPanelControls({
  maxContextTokens,
  maxCompletionTokens,
  maxChoices,
  narrativeTags,
  availableNarrativeTags,
  validationErrors,
  tokenCount,
  onMaxContextTokensChange,
  onMaxCompletionTokensChange,
  onMaxChoicesChange,
  onNarrativeTagsChange,
  onDirty,
}: GenerationPanelControlsProps) {
  const maxContextSliderRef = useRef<HTMLInputElement>(null)
  const maxCompletionSliderRef = useRef<HTMLInputElement>(null)

  return (
    <>
      {/* Sliders de tokens sur une seule ligne */}
      <div style={{ marginBottom: '1rem' }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
          {/* Slider Max tokens contexte */}
          <div style={{ flex: 1 }}>
            <label style={{ color: theme.text.primary, display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', fontWeight: 500 }}>
              Max tokens contexte
            </label>
            {validationErrors.maxContextTokens && (
              <div style={{ fontSize: '0.85rem', color: theme.state.error.color, marginBottom: '0.25rem' }}>
                {validationErrors.maxContextTokens}
              </div>
            )}
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <input
                ref={maxContextSliderRef}
                type="range"
                className="token-slider"
                min={CONTEXT_TOKENS_LIMITS.MIN}
                max={CONTEXT_TOKENS_LIMITS.MAX}
                step={CONTEXT_TOKENS_LIMITS.STEP}
                value={maxContextTokens}
                onChange={(e) => {
                  onMaxContextTokensChange(parseInt(e.target.value))
                  onDirty()
                }}
                style={{ 
                  flex: 1,
                  height: '6px',
                  borderRadius: '3px',
                  outline: 'none',
                  WebkitAppearance: 'none',
                  appearance: 'none',
                  padding: 0,
                  margin: 0,
                }}
              />
              <span style={{ 
                minWidth: '60px', 
                textAlign: 'right',
                color: theme.text.primary,
                fontWeight: 'bold',
              }}>
                {maxContextTokens >= 1000 ? `${Math.round(maxContextTokens / 1000)}K` : maxContextTokens}
              </span>
            </div>
          </div>

          {/* Slider Max tokens génération */}
          <div style={{ flex: 1 }}>
            <label style={{ color: theme.text.primary, display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', fontWeight: 500 }}>
              Max tokens génération
            </label>
            {validationErrors.maxCompletionTokens && (
              <div style={{ fontSize: '0.85rem', color: theme.state.error.color, marginBottom: '0.25rem' }}>
                {validationErrors.maxCompletionTokens}
              </div>
            )}
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <input
                ref={maxCompletionSliderRef}
                type="range"
                className="token-slider"
                min={100}
                max={16000}
                step={500}
                value={maxCompletionTokens ?? 10000}
                onChange={(e) => {
                  const value = parseInt(e.target.value)
                  onMaxCompletionTokensChange(value === 10000 ? null : value) // null = valeur par défaut
                  onDirty()
                }}
                style={{ 
                  flex: 1,
                  height: '6px',
                  borderRadius: '3px',
                  outline: 'none',
                  WebkitAppearance: 'none',
                  appearance: 'none',
                  padding: 0,
                  margin: 0,
                }}
              />
              <span style={{ 
                minWidth: '70px', 
                textAlign: 'right',
                color: theme.text.primary,
                fontWeight: 'bold',
              }}>
                {maxCompletionTokens ? (maxCompletionTokens >= 1000 ? `${Math.round(maxCompletionTokens / 1000)}K` : maxCompletionTokens) : 'Auto (10K)'}
              </span>
            </div>
          </div>
        </div>
        <style>{`
          .token-slider {
            --range-track-bg: ${theme.border.secondary};
          }

          .token-slider::-webkit-slider-runnable-track {
            height: 6px;
            border-radius: 3px;
            background: var(--range-track-bg);
          }
          .token-slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: ${theme.border.focus};
            cursor: pointer;
            border: 2px solid ${theme.background.panel};
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
            margin-top: -6px;
          }
          .token-slider::-webkit-slider-thumb:hover {
            background: ${theme.button.primary.background};
            transform: scale(1.1);
          }
          .token-slider::-moz-range-track {
            height: 6px;
            border-radius: 3px;
            background: var(--range-track-bg);
          }
          .token-slider::-moz-range-thumb {
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: ${theme.border.focus};
            cursor: pointer;
            border: 2px solid ${theme.background.panel};
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
          }
          .token-slider::-moz-range-thumb:hover {
            background: ${theme.button.primary.background};
            transform: scale(1.1);
          }
          .token-slider::-ms-track {
            height: 6px;
            border-radius: 3px;
            background: var(--range-track-bg);
            border: none;
            color: transparent;
          }
          .token-slider::-ms-thumb {
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: ${theme.border.focus};
            cursor: pointer;
            border: 2px solid ${theme.background.panel};
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
          }
          .token-slider::-ms-thumb:hover {
            background: ${theme.button.primary.background};
            transform: scale(1.1);
          }
        `}</style>
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
          <label style={{ color: theme.text.primary, margin: 0 }}>
            Nombre max de choix
          </label>

          <div style={{ position: 'relative', display: 'inline-block' }}>
            <button
              type="button"
              style={{
                width: '24px',
                height: '24px',
                borderRadius: '12px',
                border: `1px solid ${theme.border.primary}`,
                backgroundColor: theme.background.secondary,
                color: theme.text.secondary,
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 'bold',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: 0,
              }}
              title="Vide = Mode Libre (l'IA décide entre 2 et 8 choix). Valeur 0-8 = Mode Limité (l'IA génère entre 1 et cette valeur). 0 = aucun choix (dialogue linéaire)."
            >
              ?
            </button>
          </div>
        </div>
        <input
          type="number"
          value={maxChoices ?? ''}
          onChange={(e) => {
            const value = e.target.value
            if (value === '') {
              onMaxChoicesChange(null) // Mode Libre
            } else {
              const num = parseInt(value)
              if (!isNaN(num) && num >= 0 && num <= 8) {
                onMaxChoicesChange(num) // Mode Limité
              }
            }
            onDirty()
          }}
          min={0}
          max={8}
          placeholder="Vide = Libre (2-8 choix)"
          style={{ 
            width: '100%', 
            padding: '0.5rem', 
            boxSizing: 'border-box',
            backgroundColor: theme.input.background,
            border: `1px solid ${theme.input.border}`,
            color: theme.input.color,
          }}
        />
      </div>

      {/* Tags narratifs */}
      <div style={{ marginBottom: '1rem' }}>
        <label style={{ 
          display: 'block', 
          marginBottom: '0.5rem', 
          color: theme.text.primary,
          fontWeight: 'bold'
        }}>
          Tags narratifs
        </label>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          {availableNarrativeTags.map((tag) => (
            <label
              key={tag}
              style={{
                display: 'flex',
                alignItems: 'center',
                padding: '0.5rem 1rem',
                border: `1px solid ${narrativeTags.includes(tag) ? theme.border.focus : theme.border.primary}`,
                borderRadius: '4px',
                backgroundColor: narrativeTags.includes(tag) 
                  ? theme.button.primary.background 
                  : theme.button.default.background,
                color: narrativeTags.includes(tag) 
                  ? theme.button.primary.color 
                  : theme.button.default.color,
                cursor: 'pointer',
                fontSize: '0.9rem',
              }}
            >
              <input
                type="checkbox"
                checked={narrativeTags.includes(tag)}
                onChange={(e) => {
                  if (e.target.checked) {
                    onNarrativeTagsChange([...narrativeTags, tag])
                  } else {
                    onNarrativeTagsChange(narrativeTags.filter(t => t !== tag))
                  }
                  onDirty()
                }}
                style={{ marginRight: '0.5rem', cursor: 'pointer' }}
              />
              #{tag}
            </label>
          ))}
        </div>
      </div>

      {tokenCount !== null && validationErrors.tokenCount && (
        <div style={{ marginBottom: '1rem' }}>
          <div style={{ 
            padding: '0.5rem',
            backgroundColor: theme.state.error.background,
            border: `1px solid ${theme.state.error.border}`,
            borderRadius: '4px',
            color: theme.state.error.color,
            fontSize: '0.9rem',
          }}>
            {validationErrors.tokenCount}
          </div>
        </div>
      )}
    </>
  )
}
