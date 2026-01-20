/**
 * Indicateur visuel du statut de sauvegarde automatique.
 */
import { useState, useEffect } from 'react'
import { theme } from '../../theme'

export type SaveStatus = 'saved' | 'saving' | 'unsaved' | 'error'

export interface SaveStatusIndicatorProps {
  status: SaveStatus
  lastSavedAt?: number | null // Timestamp ms (Task 3 - Story 0.5)
  variant?: 'draft' | 'disk' // Optionnel, pour wording si besoin (Task 3 - Story 0.5)
  errorMessage?: string | null // Message d'erreur optionnel (Task 3 - Story 0.5)
  style?: React.CSSProperties
}

const STATUS_CONFIG: Record<SaveStatus, { label: string; color: string }> = {
  saved: { label: 'Sauvegardé', color: theme.state.success.color },
  saving: { label: 'En cours...', color: theme.state.info.color },
  unsaved: { label: 'Non sauvegardé', color: theme.state.warning.color },
  error: { label: 'Erreur', color: theme.state.error.color },
}

// Helper pour formater le temps relatif (Task 3 - Story 0.5)
function formatRelativeTime(timestamp: number): string {
  const now = Date.now()
  const diff = now - timestamp
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  
  if (seconds < 5) return 'à l\'instant'
  if (seconds < 60) return `il y a ${seconds}s`
  if (minutes < 60) return `il y a ${minutes}min`
  if (hours < 24) return `il y a ${hours}h`
  return `il y a ${Math.floor(hours / 24)}j`
}

export function SaveStatusIndicator({ status, lastSavedAt, errorMessage, style }: SaveStatusIndicatorProps) {
  const config = STATUS_CONFIG[status]
  const [relativeTime, setRelativeTime] = useState<string | null>(null)
  
  // Mettre à jour le temps relatif toutes les 10 secondes (Task 3 - Story 0.5)
  useEffect(() => {
    if (status === 'saved' && lastSavedAt) {
      setRelativeTime(formatRelativeTime(lastSavedAt))
      const interval = setInterval(() => {
        setRelativeTime(formatRelativeTime(lastSavedAt))
      }, 10000) // Mise à jour toutes les 10s
      
      return () => clearInterval(interval)
    } else {
      setRelativeTime(null)
    }
  }, [status, lastSavedAt])
  
  const label = status === 'saved' && relativeTime 
    ? `${config.label} ${relativeTime}`
    : config.label

  // Construire le texte de l'infobulle
  const tooltipText = status === 'error' && errorMessage 
    ? errorMessage 
    : label

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
          cursor: 'default',
        }}
        title={tooltipText}
      />
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
