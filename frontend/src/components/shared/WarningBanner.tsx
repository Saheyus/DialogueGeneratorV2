/**
 * Bandeau d'avertissement pour afficher des notifications non-bloquantes.
 */
import { theme } from '../../theme'

export interface WarningBannerProps {
  message: string
  onAction?: () => void
  actionLabel?: string
  onDismiss?: () => void
  style?: React.CSSProperties
}

export function WarningBanner({
  message,
  onAction,
  actionLabel,
  onDismiss,
  style,
}: WarningBannerProps) {
  return (
    <div
      style={{
        padding: '0.75rem 1rem',
        backgroundColor: theme.state.warning.background || '#fff3cd',
        border: `1px solid ${theme.state.warning.border || '#ffc107'}`,
        borderRadius: '6px',
        color: theme.state.warning.color || '#856404',
        fontSize: '0.875rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '1rem',
        marginBottom: '1rem',
        ...style,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: 1 }}>
        <span style={{ fontSize: '1rem' }}>⚠️</span>
        <span>{message}</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        {onAction && actionLabel && (
          <button
            onClick={onAction}
            style={{
              padding: '0.375rem 0.75rem',
              border: `1px solid ${theme.state.warning.border || '#ffc107'}`,
              borderRadius: '4px',
              backgroundColor: theme.button.default.background || '#fff',
              color: theme.state.warning.color || '#856404',
              cursor: 'pointer',
              fontSize: '0.875rem',
              fontWeight: '500',
              whiteSpace: 'nowrap',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = theme.button.default.hover?.background || '#f8f9fa'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = theme.button.default.background || '#fff'
            }}
          >
            {actionLabel}
          </button>
        )}
        {onDismiss && (
          <button
            onClick={onDismiss}
            style={{
              padding: '0.25rem 0.5rem',
              border: 'none',
              borderRadius: '4px',
              backgroundColor: 'transparent',
              color: theme.state.warning.color || '#856404',
              cursor: 'pointer',
              fontSize: '1.25rem',
              lineHeight: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(0, 0, 0, 0.1)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent'
            }}
            title="Fermer"
          >
            ×
          </button>
        )}
      </div>
    </div>
  )
}
