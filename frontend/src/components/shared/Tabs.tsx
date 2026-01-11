/**
 * Composant Tabs réutilisable avec animations.
 */
import { ReactNode } from 'react'
import { theme } from '../../theme'

export interface Tab {
  id: string
  label: string
  content: ReactNode
  disabled?: boolean
}

export interface TabsProps {
  tabs: Tab[]
  activeTabId: string
  onTabChange: (tabId: string) => void
  style?: React.CSSProperties
  /**
   * Styles appliqués au conteneur de contenu (zone sous les onglets).
   * Utile pour désactiver le scroll interne quand le contenu gère déjà son propre overflow.
   */
  contentStyle?: React.CSSProperties
}

export function Tabs({ tabs, activeTabId, onTabChange, style, contentStyle }: TabsProps) {
  const activeTab = tabs.find((tab) => tab.id === activeTabId)

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        flex: 1,
        minHeight: 0,
        overflow: 'hidden',
        ...style,
      }}
    >
      <div
        style={{
          display: 'flex',
          borderBottom: `2px solid ${theme.border.primary}`,
          backgroundColor: theme.background.panel,
          flexShrink: 0,
        }}
      >
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => !tab.disabled && onTabChange(tab.id)}
            disabled={tab.disabled}
            style={{
              padding: '0.75rem 1.5rem',
              border: 'none',
              borderBottom:
                tab.id === activeTabId
                  ? `3px solid ${theme.button.primary.background}`
                  : '3px solid transparent',
              backgroundColor: 'transparent',
              color:
                tab.id === activeTabId
                  ? theme.text.primary
                  : theme.text.secondary,
              cursor: tab.disabled ? 'not-allowed' : 'pointer',
              fontWeight: tab.id === activeTabId ? 'bold' : 'normal',
              opacity: tab.disabled ? 0.5 : 1,
              transition: 'all 0.2s ease',
              position: 'relative',
              bottom: '-2px',
            }}
            onMouseEnter={(e) => {
              if (!tab.disabled && tab.id !== activeTabId) {
                e.currentTarget.style.color = theme.text.primary
              }
            }}
            onMouseLeave={(e) => {
              if (tab.id !== activeTabId) {
                e.currentTarget.style.color = theme.text.secondary
              }
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div
        style={{
          flex: 1,
          minHeight: 0,
          height: contentStyle?.height !== undefined ? contentStyle.height : '100%',
          overflow: contentStyle?.overflow !== undefined ? contentStyle.overflow : 'auto',
          backgroundColor: theme.background.panel,
          display: contentStyle?.display !== undefined ? contentStyle.display : 'block',
          ...contentStyle,
        }}
      >
        {activeTab?.content}
      </div>
    </div>
  )
}

