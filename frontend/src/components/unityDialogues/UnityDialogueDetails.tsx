/**
 * Composant pour afficher et éditer un dialogue Unity.
 */
import { useState, useEffect, useCallback } from 'react'
import * as unityDialoguesAPI from '../../api/unityDialogues'
import { getErrorMessage } from '../../types/errors'
import { theme } from '../../theme'
import { UnityDialogueEditor } from '../generation/UnityDialogueEditor'

interface UnityDialogueDetailsProps {
  filename: string
  onClose: () => void
  onDeleted?: () => void
  onGenerateContinuation?: (dialogueJson: string, dialogueTitle: string) => void
}

export function UnityDialogueDetails({
  filename,
  onClose,
  onDeleted,
  onGenerateContinuation,
}: UnityDialogueDetailsProps) {
  const [jsonContent, setJsonContent] = useState<string>('')
  const [title, setTitle] = useState<string>('')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  useEffect(() => {
    loadDialogue()
  }, [filename])

  const loadDialogue = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await unityDialoguesAPI.getUnityDialogue(filename)
      setJsonContent(response.json_content)
      setTitle(response.title || filename.replace('.json', ''))
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }

  const handleSave = useCallback(
    async (savedFilename: string) => {
      // Recharger le dialogue après sauvegarde
      await loadDialogue()
    },
    [filename]
  )

  const handleDelete = async () => {
    if (!confirm(`Êtes-vous sûr de vouloir supprimer "${filename}" ?`)) {
      return
    }

    setIsDeleting(true)
    try {
      await unityDialoguesAPI.deleteUnityDialogue(filename)
      onDeleted?.()
      onClose()
    } catch (err) {
      setError(getErrorMessage(err))
      setIsDeleting(false)
    }
  }

  if (isLoading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: theme.text.secondary }}>
        Chargement du dialogue...
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
          onClick={loadDialogue}
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

  if (!jsonContent) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: theme.text.secondary }}>
        Aucun contenu à afficher
      </div>
    )
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* En-tête avec actions */}
      <div
        style={{
          padding: '1rem',
          borderBottom: `1px solid ${theme.border.primary}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: theme.background.panelHeader,
        }}
      >
        <div>
          <h3 style={{ margin: 0, color: theme.text.primary }}>{title}</h3>
          <div style={{ fontSize: '0.85rem', color: theme.text.secondary, marginTop: '0.25rem' }}>
            {filename}
          </div>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {onGenerateContinuation && (
            <button
              onClick={() => onGenerateContinuation(jsonContent, title)}
              style={{
                padding: '0.5rem 1rem',
                border: `1px solid ${theme.border.primary}`,
                borderRadius: '4px',
                backgroundColor: theme.button.primary.background,
                color: theme.button.primary.color,
                cursor: 'pointer',
                fontWeight: 'bold',
              }}
              title="Générer un dialogue qui suit celui-ci"
            >
              Générer la suite
            </button>
          )}
          <button
            onClick={handleDelete}
            disabled={isDeleting}
            style={{
              padding: '0.5rem 1rem',
              border: `1px solid ${theme.border.primary}`,
              borderRadius: '4px',
              backgroundColor: '#dc3545',
              color: '#ffffff',
              cursor: isDeleting ? 'not-allowed' : 'pointer',
              opacity: isDeleting ? 0.6 : 1,
            }}
          >
            {isDeleting ? 'Suppression...' : 'Supprimer'}
          </button>
          <button
            onClick={onClose}
            style={{
              padding: '0.5rem 1rem',
              border: `1px solid ${theme.border.primary}`,
              borderRadius: '4px',
              backgroundColor: theme.button.default.background,
              color: theme.button.default.color,
              cursor: 'pointer',
            }}
          >
            Fermer
          </button>
        </div>
      </div>

      {/* Éditeur */}
      <div style={{ flex: 1, overflow: 'hidden' }}>
        <UnityDialogueEditor
          json_content={jsonContent}
          title={title}
          filename={filename.replace('.json', '')}
          onSave={handleSave}
          onCancel={onClose}
        />
      </div>
    </div>
  )
}

