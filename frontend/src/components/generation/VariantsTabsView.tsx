/**
 * Visualisation des variantes générées avec onglets.
 */
import { memo, useCallback, useState } from 'react'
import { Tabs, type Tab } from '../shared/Tabs'
import { theme } from '../../theme'
import type { DialogueVariantResponse, GenerateDialogueVariantsResponse } from '../../types/api'

export interface VariantsTabsViewProps {
  response: GenerateDialogueVariantsResponse | null
  onValidateAsInteraction?: (variant: DialogueVariantResponse) => void
}

export const VariantsTabsView = memo(function VariantsTabsView({
  response,
  onValidateAsInteraction,
}: VariantsTabsViewProps) {
  const handleValidate = useCallback(
    (variant: DialogueVariantResponse) => {
      onValidateAsInteraction?.(variant)
    },
    [onValidateAsInteraction]
  )

  if (!response || response.variants.length === 0) {
    return (
      <div
        style={{
          padding: '2rem',
          textAlign: 'center',
          color: theme.text.secondary,
        }}
      >
        Aucune variante générée
      </div>
    )
  }

  const tabs: Tab[] = [
    ...response.variants.map((variant, index) => ({
      id: `variant-${variant.id}`,
      label: `Variante ${index + 1}`,
      content: (
        <div style={{ padding: '1rem', height: '100%', overflow: 'auto' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '1rem',
            }}
          >
            <h4 style={{ margin: 0, color: theme.text.primary }}>
              {variant.title}
            </h4>
            <button
              onClick={() => handleValidate(variant)}
              style={{
                padding: '0.5rem 1rem',
                border: `1px solid ${theme.border.primary}`,
                borderRadius: '4px',
                backgroundColor: theme.button.primary.background,
                color: theme.button.primary.color,
                cursor: 'pointer',
                fontSize: '0.9rem',
              }}
            >
              Valider comme Interaction
            </button>
          </div>
          <div
            style={{
              backgroundColor: theme.background.tertiary,
              padding: '1rem',
              borderRadius: '4px',
              border: `1px solid ${theme.border.primary}`,
            }}
          >
            <pre
              style={{
                fontFamily: 'inherit',
                fontSize: '0.9rem',
                lineHeight: '1.6',
                color: theme.text.secondary,
                whiteSpace: 'pre-wrap',
                wordWrap: 'break-word',
                margin: 0,
              }}
            >
              {variant.content}
            </pre>
          </div>
        </div>
      ),
    })),
  ]

  const [activeTabId, setActiveTabId] = useState(tabs[0].id)

  return (
    <div
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: theme.background.panel,
      }}
    >
      <Tabs
        tabs={tabs}
        activeTabId={activeTabId}
        onTabChange={setActiveTabId}
        style={{ flex: 1, display: 'flex', flexDirection: 'column' }}
      />
    </div>
  )
})

