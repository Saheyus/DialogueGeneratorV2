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
        paddingRight: onDismiss ? '2.25rem' : '1rem',
        backgroundColor: theme.state.warning.background || '#fff3cd',
        border: `1px solid ${theme.state.warning.border || '#ffc107'}`,
        borderRadius: '6px',
        color: theme.state.warning.color || '#856404',
        fontSize: '0.875rem',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'stretch',
        gap: '0.75rem',
        marginBottom: '1rem',
        position: 'relative',
        ...style,
      }}
    >
      {onDismiss && (
        <button
          onClick={onDismiss}
          style={{
            position: 'absolute',
            top: '0.5rem',
            right: '0.5rem',
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
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem', width: '100%' }}>
        <span style={{ fontSize: '1rem', flexShrink: 0 }}>⚠️</span>
        <span style={{ flex: 1 }}>{message}</span>
      </div>
      {onAction && actionLabel && (
        <button
          onClick={onAction}
          style={{
            alignSelf: 'flex-start',
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
    </div>
  )
}
