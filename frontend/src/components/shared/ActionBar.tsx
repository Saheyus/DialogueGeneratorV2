/**
 * Barre d'actions sticky avec les CTA principaux.
 */
import { theme } from '../../theme'

export interface ActionButton {
  id: string
  label: string
  onClick: () => void
  variant?: 'primary' | 'secondary' | 'danger'
  disabled?: boolean
  icon?: string
  shortcut?: string
}

interface ActionBarProps {
  actions: ActionButton[]
  isDirty?: boolean
  style?: React.CSSProperties
}

export function ActionBar({ actions, isDirty = false, style }: ActionBarProps) {
  const getButtonStyles = (variant: ActionButton['variant'] = 'secondary') => {
    const baseStyles: React.CSSProperties = {
      padding: '0.5rem 1rem',
      border: 'none',
      borderRadius: '4px',
      cursor: 'pointer',
      fontSize: '0.9rem',
      fontWeight: 500,
      display: 'inline-flex',
      alignItems: 'center',
      gap: '0.5rem',
      transition: 'all 0.2s',
    }

    switch (variant) {
      case 'primary':
        return {
          ...baseStyles,
          backgroundColor: theme.button.primary.background,
          color: theme.button.primary.color,
        }
      case 'danger':
        return {
          ...baseStyles,
          backgroundColor: '#dc3545',
          color: '#ffffff',
        }
      case 'secondary':
      default:
        return {
          ...baseStyles,
          backgroundColor: theme.button.default.background,
          color: theme.button.default.color,
          border: `1px solid ${theme.border.primary}`,
        }
    }
  }

  return (
    <div
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 100,
        backgroundColor: theme.background.panelHeader,
        borderBottom: `2px solid ${theme.border.primary}`,
        padding: '0.75rem 1rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '0.75rem',
        ...style,
      }}
    >
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', flex: 1 }}>
        {actions.map((action) => (
          <button
            key={action.id}
            onClick={action.onClick}
            disabled={action.disabled}
            style={{
              ...getButtonStyles(action.variant),
              opacity: action.disabled ? 0.6 : 1,
              cursor: action.disabled ? 'not-allowed' : 'pointer',
            }}
            title={action.shortcut ? `${action.label} (${action.shortcut})` : action.label}
          >
            {action.icon && <span>{action.icon}</span>}
            <span>{action.label}</span>
            {action.shortcut && (
              <span
                style={{
                  fontSize: '0.75rem',
                  opacity: 0.7,
                  marginLeft: '0.25rem',
                }}
              >
                {action.shortcut}
              </span>
            )}
          </button>
        ))}
      </div>
      {isDirty && (
        <div
          style={{
            fontSize: '0.85rem',
            color: theme.state.info.color,
            fontStyle: 'italic',
          }}
        >
          ● Brouillon non sauvegardé
        </div>
      )}
    </div>
  )
}



