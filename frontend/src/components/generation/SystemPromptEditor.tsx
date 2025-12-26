/**
 * Éditeur pour les instructions de scène et le system prompt.
 */
import React, { memo, useCallback, useState } from 'react'
import { Tabs, type Tab } from '../shared/Tabs'
import { FormField } from '../shared/FormField'
import { useSystemPrompt } from '../../hooks/useSystemPrompt'
import { theme } from '../../theme'

export interface SystemPromptEditorProps {
  userInstructions: string
  systemPromptOverride: string | null
  onUserInstructionsChange: (instructions: string) => void
  onSystemPromptChange: (prompt: string | null) => void
}

export const SystemPromptEditor = memo(function SystemPromptEditor({
  userInstructions,
  systemPromptOverride,
  onUserInstructionsChange,
  onSystemPromptChange,
}: SystemPromptEditorProps) {
  const {
    systemPrompt,
    isLoading,
    resetToDefault,
    updatePrompt,
  } = useSystemPrompt()

  const handleSystemPromptChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const value = e.target.value
      updatePrompt(value)
      onSystemPromptChange(value || null)
    },
    [updatePrompt, onSystemPromptChange]
  )

  const handleReset = useCallback(() => {
    resetToDefault()
    onSystemPromptChange(null)
  }, [resetToDefault, onSystemPromptChange])

  const tabs: Tab[] = [
    {
      id: 'user-instructions',
      label: 'Instructions de Scène',
      content: (
        <div style={{ padding: '1rem' }}>
          <FormField
            label="Instructions"
            htmlFor="user-instructions-textarea"
          >
            <div style={{ position: 'relative' }}>
              <textarea
                id="user-instructions-textarea"
                value={userInstructions}
                onChange={(e) => onUserInstructionsChange(e.target.value)}
                rows={8}
                placeholder="Ex: Bob doit annoncer à Alice qu'il part à l'aventure. Ton désiré: Héroïque. Inclure une condition sur la compétence 'Charisme' de Bob."
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  paddingBottom: '2rem',
                  boxSizing: 'border-box',
                  backgroundColor: theme.input.background,
                  border: `1px solid ${theme.input.border}`,
                  color: theme.input.color,
                  borderRadius: '4px',
                  fontFamily: 'inherit',
                  fontSize: '0.9rem',
                  resize: 'vertical',
                }}
              />
              <div
                style={{
                  position: 'absolute',
                  bottom: '0.5rem',
                  right: '0.5rem',
                  fontSize: '0.75rem',
                  color: theme.text.secondary,
                  backgroundColor: theme.background.panel,
                  padding: '0.25rem 0.5rem',
                  borderRadius: '4px',
                }}
              >
                {userInstructions.length} caractères
                {userInstructions.length > 0 && (
                  <span style={{ marginLeft: '0.5rem' }}>
                    (~{Math.ceil(userInstructions.length / 4)} tokens)
                  </span>
                )}
              </div>
            </div>
          </FormField>
        </div>
      ),
    },
    {
      id: 'system-prompt',
      label: 'Instructions Système LLM',
      content: (
        <div style={{ padding: '1rem' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '0.5rem',
            }}
          >
            <label
              htmlFor="system-prompt-textarea"
              style={{
                color: theme.text.primary,
                fontSize: '0.9rem',
                fontWeight: 500,
              }}
            >
              Prompt Système Principal:
            </label>
            <button
              onClick={handleReset}
              disabled={isLoading}
              style={{
                padding: '0.5rem 1rem',
                border: `1px solid ${theme.border.primary}`,
                borderRadius: '4px',
                backgroundColor: theme.button.default.background,
                color: theme.button.default.color,
                cursor: isLoading ? 'not-allowed' : 'pointer',
                opacity: isLoading ? 0.6 : 1,
                fontSize: '0.85rem',
              }}
              title="Restaure le prompt système par défaut de l'application"
            >
              Restaurer Défaut
            </button>
          </div>
          <FormField label="" htmlFor="system-prompt-textarea">
            <textarea
              id="system-prompt-textarea"
              value={systemPromptOverride || systemPrompt || ''}
              onChange={handleSystemPromptChange}
              rows={12}
              placeholder="Modifiez le prompt système principal envoyé au LLM. Ce prompt guide le comportement général de l'IA."
              style={{
                width: '100%',
                padding: '0.5rem',
                boxSizing: 'border-box',
                backgroundColor: theme.input.background,
                border: `1px solid ${theme.input.border}`,
                color: theme.input.color,
                borderRadius: '4px',
                fontFamily: 'monospace',
                fontSize: '0.85rem',
                resize: 'vertical',
                lineHeight: '1.5',
              }}
            />
          </FormField>
        </div>
      ),
    },
  ]

  const [activeTabId, setActiveTabId] = useState(tabs[0].id)

  return (
    <div
      style={{
        marginBottom: '1rem',
        border: `1px solid ${theme.border.primary}`,
        borderRadius: '4px',
        backgroundColor: theme.background.panel,
        height: '100%',
      }}
    >
      <Tabs
        tabs={tabs}
        activeTabId={activeTabId}
        onTabChange={setActiveTabId}
      />
    </div>
  )
})

