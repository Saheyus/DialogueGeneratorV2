/**
 * Composant pour afficher la liste des dialogues Unity avec recherche.
 */
import { useState, useEffect, useMemo, useImperativeHandle, forwardRef, useCallback } from 'react'
import * as unityDialoguesAPI from '../../api/unityDialogues'
import { getErrorMessage } from '../../types/errors'
import { theme } from '../../theme'
import type { UnityDialogueMetadata } from '../../types/api'
import { UnityDialogueItem } from './UnityDialogueItem'

interface UnityDialogueListProps {
  onSelectDialogue: (dialogue: UnityDialogueMetadata | null) => void
  selectedFilename: string | null
}

export interface UnityDialogueListRef {
  refresh: () => void
}

export const UnityDialogueList = forwardRef<UnityDialogueListRef, UnityDialogueListProps>(
  function UnityDialogueList({ onSelectDialogue, selectedFilename }, ref) {
  const [dialogues, setDialogues] = useState<UnityDialogueMetadata[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadDialogues = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await unityDialoguesAPI.listUnityDialogues()
      setDialogues(response.dialogues)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadDialogues()
  }, [loadDialogues])

  // Filtrer les dialogues
  const filteredDialogues = useMemo(() => {
    if (!searchQuery.trim()) return dialogues

    const query = searchQuery.toLowerCase()
    return dialogues.filter(
      (dialogue) =>
        dialogue.filename.toLowerCase().includes(query) ||
        (dialogue.title && dialogue.title.toLowerCase().includes(query))
    )
  }, [dialogues, searchQuery])

  // Exposer la fonction de rafraîchissement via ref
  useImperativeHandle(ref, () => ({
    refresh: loadDialogues,
  }), [loadDialogues])

  const handleItemClick = (dialogue: UnityDialogueMetadata) => {
    if (selectedFilename === dialogue.filename) {
      onSelectDialogue(null)
    } else {
      onSelectDialogue(dialogue)
    }
  }

  if (isLoading) {
    return (
      <div style={{ padding: '1rem', textAlign: 'center', color: theme.text.secondary }}>
        <div>Chargement des dialogues Unity...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div
        style={{
          padding: '1rem',
          color: theme.state.error.color,
          backgroundColor: theme.state.error.background,
          borderRadius: '4px',
        }}
      >
        {error}
        <button
          onClick={loadDialogues}
          style={{
            marginTop: '0.5rem',
            padding: '0.5rem 1rem',
            border: `1px solid ${theme.border.primary}`,
            borderRadius: '4px',
            backgroundColor: theme.button.default.background,
            color: theme.button.default.color,
            cursor: 'pointer',
          }}
        >
          Réessayer
        </button>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div
        style={{
          padding: '0.75rem 0.75rem 0.5rem 0.75rem',
          borderBottom: `1px solid ${theme.border.primary}`,
          backgroundColor: theme.background.panelHeader,
        }}
      >
        <input
          type="text"
          placeholder="Rechercher un dialogue..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            width: '100%',
            padding: '0.6rem 0.75rem',
            border: `1px solid ${theme.input.border}`,
            borderRadius: '6px',
            boxSizing: 'border-box',
            backgroundColor: theme.input.background,
            color: theme.input.color,
            marginBottom: '0.6rem',
          }}
        />

        <div style={{ fontSize: '0.85rem', color: theme.text.secondary }}>
          {filteredDialogues.length} dialogue{filteredDialogues.length !== 1 ? 's' : ''}
          {searchQuery && ` (sur ${dialogues.length} total)`}
        </div>
      </div>
      <div style={{ flex: 1, overflowY: 'auto', padding: '0.75rem' }}>
        {filteredDialogues.length === 0 ? (
          <div style={{ padding: '1rem', textAlign: 'center', color: theme.text.secondary }}>
            {searchQuery ? 'Aucun dialogue trouvé' : 'Aucun dialogue Unity'}
          </div>
        ) : (
          filteredDialogues.map((dialogue) => (
            <UnityDialogueItem
              key={dialogue.filename}
              dialogue={dialogue}
              onClick={() => handleItemClick(dialogue)}
              isSelected={selectedFilename === dialogue.filename}
            />
          ))
        )}
      </div>
    </div>
  )
  }
)
