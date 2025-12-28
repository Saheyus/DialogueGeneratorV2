/**
 * Composant pour afficher un item de dialogue Unity dans la liste.
 */
import { memo } from 'react'
import { theme } from '../../theme'
import type { UnityDialogueMetadata } from '../../types/api'

interface UnityDialogueItemProps {
  dialogue: UnityDialogueMetadata
  onClick: () => void
  isSelected: boolean
}

export const UnityDialogueItem = memo(function UnityDialogueItem({
  dialogue,
  onClick,
  isSelected,
}: UnityDialogueItemProps) {
  const formatSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const formatDate = (isoString: string): string => {
    const date = new Date(isoString)
    return date.toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div
      onClick={onClick}
      style={{
        padding: '0.75rem',
        borderBottom: `1px solid ${theme.border.primary}`,
        backgroundColor: isSelected ? theme.state.selected.background : 'transparent',
        color: theme.text.primary,
        cursor: 'pointer',
        transition: 'background-color 0.2s',
      }}
      onMouseEnter={(e) => {
        if (!isSelected) {
          e.currentTarget.style.backgroundColor = theme.state.hover.background
        }
      }}
      onMouseLeave={(e) => {
        if (!isSelected) {
          e.currentTarget.style.backgroundColor = 'transparent'
        }
      }}
    >
      <div style={{ fontWeight: 500, marginBottom: '0.25rem' }}>
        {dialogue.title || dialogue.filename}
      </div>
      <div style={{ fontSize: '0.85rem', color: theme.text.secondary, marginBottom: '0.25rem' }}>
        <span style={{ fontFamily: 'monospace' }}>{dialogue.filename}</span>
      </div>
      <div
        style={{
          fontSize: '0.75rem',
          color: theme.text.tertiary,
          display: 'flex',
          gap: '0.5rem',
        }}
      >
        <span>{formatSize(dialogue.size_bytes)}</span>
        <span>•</span>
        <span>{formatDate(dialogue.modified_time)}</span>
      </div>
    </div>
  )
})

