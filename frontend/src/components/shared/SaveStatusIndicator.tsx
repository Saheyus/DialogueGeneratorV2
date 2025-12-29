/**
 * Indicateur visuel du statut de sauvegarde automatique.
 */
import { theme } from '../../theme'

export type SaveStatus = 'saved' | 'saving' | 'unsaved' | 'error'

export interface SaveStatusIndicatorProps {
  status: SaveStatus
  style?: React.CSSProperties
}

const STATUS_CONFIG: Record<SaveStatus, { label: string; color: string }> = {
  saved: { label: 'Sauvegardé', color: theme.state.success.color },
  saving: { label: 'En cours...', color: theme.state.info.color },
  unsaved: { label: 'Non sauvegardé', color: theme.state.warning.color },
  error: { label: 'Erreur', color: theme.state.error.color },
}

export function SaveStatusIndicator({ status, style }: SaveStatusIndicatorProps) {
  const config = STATUS_CONFIG[status]

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
        fontSize: '0.85rem',
        color: config.color,
        ...style,
      }}
    >
      <div
        style={{
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          backgroundColor: config.color,
          opacity: status === 'saving' ? 0.6 : 1,
          animation: status === 'saving' ? 'pulse 1.5s ease-in-out infinite' : 'none',
        }}
      />
      <span>{config.label}</span>
      <style>
        {`
          @keyframes pulse {
            0%, 100% { opacity: 0.6; }
            50% { opacity: 1; }
          }
        `}
      </style>
    </div>
  )
}

