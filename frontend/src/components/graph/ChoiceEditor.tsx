/**
 * Composant pour éditer un choix de dialogue avec conditions et mécaniques RPG.
 */
import { memo } from 'react'
import { useFormContext } from 'react-hook-form'
import { theme } from '../../theme'
import type { Choice, DialogueNodeData } from '../../schemas/nodeEditorSchema'

export interface ChoiceEditorProps {
  choiceIndex: number
  onRemove?: () => void
}

export const ChoiceEditor = memo(function ChoiceEditor({
  choiceIndex,
  onRemove,
}: ChoiceEditorProps) {
  const { register, formState: { errors } } = useFormContext<DialogueNodeData>()
  const choicesErrors = errors.choices?.[choiceIndex]
  
  return (
    <div
      style={{
        padding: '1rem',
        backgroundColor: theme.background.panel,
        borderRadius: 6,
        border: `1px solid ${theme.border.primary}`,
        marginBottom: '0.75rem',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
        <h4 style={{ margin: 0, fontSize: '0.9rem', color: theme.text.primary }}>
          Choix #{choiceIndex + 1}
        </h4>
        {onRemove && (
          <button
            type="button"
            onClick={onRemove}
            style={{
              padding: '0.25rem 0.5rem',
              border: `1px solid ${theme.border.primary}`,
              borderRadius: 4,
              backgroundColor: '#E74C3C',
              color: 'white',
              cursor: 'pointer',
              fontSize: '0.75rem',
            }}
          >
            🗑️ Supprimer
          </button>
        )}
      </div>
      
      {/* Texte du choix */}
      <div style={{ marginBottom: '0.75rem' }}>
        <label
          style={{
            display: 'block',
            marginBottom: '0.5rem',
            fontSize: '0.85rem',
            fontWeight: 'bold',
            color: theme.text.primary,
          }}
        >
          Texte du choix *
        </label>
        <textarea
          {...register(`choices.${choiceIndex}.text` as const, { required: true })}
          placeholder="Texte du choix..."
          rows={2}
          style={{
            width: '100%',
            padding: '0.5rem',
            border: `1px solid ${choicesErrors?.text ? theme.state.error.border : theme.border.primary}`,
            borderRadius: 4,
            backgroundColor: theme.background.tertiary,
            color: theme.text.primary,
            fontSize: '0.9rem',
            fontFamily: 'inherit',
            resize: 'vertical',
          }}
        />
        {choicesErrors?.text && (
          <div style={{ marginTop: '0.25rem', fontSize: '0.75rem', color: theme.state.error.color }}>
            {choicesErrors.text.message}
          </div>
        )}
      </div>
      
      {/* Target Node */}
      <div style={{ marginBottom: '0.75rem' }}>
        <label
          style={{
            display: 'block',
            marginBottom: '0.5rem',
            fontSize: '0.85rem',
            fontWeight: 'bold',
            color: theme.text.secondary,
          }}
        >
          Nœud cible
        </label>
        <input
          type="text"
          {...register(`choices.${choiceIndex}.targetNode` as const)}
          placeholder="ID du nœud cible (ex: END, START, NODE_123)"
          style={{
            width: '100%',
            padding: '0.5rem',
            border: `1px solid ${theme.border.primary}`,
            borderRadius: 4,
            backgroundColor: theme.background.tertiary,
            color: theme.text.primary,
            fontSize: '0.9rem',
            fontFamily: 'monospace',
          }}
        />
      </div>
      
      {/* Condition */}
      <div style={{ marginBottom: '0.75rem' }}>
        <label
          style={{
            display: 'block',
            marginBottom: '0.5rem',
            fontSize: '0.85rem',
            fontWeight: 'bold',
            color: theme.text.secondary,
          }}
        >
          Condition d'affichage
        </label>
        <input
          type="text"
          {...register(`choices.${choiceIndex}.condition` as const)}
          placeholder="Ex: FLAG_NAME, NOT FLAG_NAME, startState == 1"
          style={{
            width: '100%',
            padding: '0.5rem',
            border: `1px solid ${theme.border.primary}`,
            borderRadius: 4,
            backgroundColor: theme.background.tertiary,
            color: theme.text.primary,
            fontSize: '0.85rem',
            fontFamily: 'monospace',
          }}
        />
        <div style={{ marginTop: '0.25rem', fontSize: '0.75rem', color: theme.text.secondary, fontStyle: 'italic' }}>
          Format: FLAG_NAME, NOT FLAG_NAME, ou expression (ex: startState == 1)
        </div>
      </div>
      
      {/* Test d'attribut */}
      <div style={{ marginBottom: '0.75rem' }}>
        <label
          style={{
            display: 'block',
            marginBottom: '0.5rem',
            fontSize: '0.85rem',
            fontWeight: 'bold',
            color: theme.text.secondary,
          }}
        >
          Test d'attribut
        </label>
        <input
          type="text"
          {...register(`choices.${choiceIndex}.test` as const)}
          placeholder="Format: Attribut+Compétence:DD (ex: Raison+Rhétorique:8)"
          style={{
            width: '100%',
            padding: '0.5rem',
            border: `1px solid ${theme.border.primary}`,
            borderRadius: 4,
            backgroundColor: theme.background.tertiary,
            color: theme.text.primary,
            fontSize: '0.85rem',
            fontFamily: 'monospace',
          }}
        />
        <div style={{ marginTop: '0.25rem', fontSize: '0.75rem', color: theme.text.secondary, fontStyle: 'italic' }}>
          Format: Attribut+Compétence:DD (ex: Raison+Rhétorique:8)
        </div>
      </div>
    </div>
  )
})
