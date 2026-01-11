/**
 * Nœud personnalisé pour afficher un nœud de dialogue dans le graphe.
 */
import { memo } from 'react'
import { Handle, Position, type NodeProps } from 'reactflow'
import { theme } from '../../../theme'

interface ValidationError {
  type: string
  node_id?: string
  message: string
  severity: string
  target?: string
}

interface DialogueNodeData {
  id: string
  speaker?: string
  line?: string
  choices?: Array<{
    text: string
    targetNode?: string
  }>
  nextNode?: string
  validationErrors?: ValidationError[]
  validationWarnings?: ValidationError[]
  isHighlighted?: boolean
  [key: string]: any
}

export const DialogueNode = memo(function DialogueNode({
  data,
  selected,
}: NodeProps<DialogueNodeData>) {
  const speaker = data.speaker || 'PNJ'
  const line = data.line || ''
  const choices = data.choices || []
  const hasChoices = choices.length > 0
  const errors = data.validationErrors || []
  const warnings = data.validationWarnings || []
  const hasErrors = errors.length > 0
  const hasWarnings = warnings.length > 0
  const isHighlighted = data.isHighlighted || false
  
  // Tronquer le texte pour l'aperçu
  const truncatedLine = line.length > 100 ? `${line.substring(0, 100)}...` : line
  
  // Couleur du speaker (hash du nom pour consistance)
  const speakerColor = getSpeakerColor(speaker)
  
  // Déterminer la couleur de la bordure selon les erreurs
  let borderColor = selected ? '#27AE60' : '#4A90E2'
  if (hasErrors) {
    borderColor = theme.state.error.border
  } else if (hasWarnings) {
    borderColor = theme.state.warning.color
  }
  
  return (
    <div
      style={{
        width: 280,
        minHeight: 100,
        maxHeight: 500,
        border: `2px solid ${borderColor}`,
        borderRadius: 8,
        backgroundColor: isHighlighted ? theme.state.selected.background : theme.background.tertiary,
        boxShadow: selected
          ? '0 4px 12px rgba(0, 0, 0, 0.3)'
          : isHighlighted
          ? '0 0 0 3px rgba(116, 192, 252, 0.5)'
          : '0 2px 6px rgba(0, 0, 0, 0.2)',
        overflow: 'hidden',
        position: 'relative',
        transition: 'all 0.2s ease',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Badge d'erreur */}
      {hasErrors && (
        <div
          style={{
            position: 'absolute',
            top: 4,
            right: 4,
            backgroundColor: theme.state.error.border,
            color: 'white',
            borderRadius: '50%',
            width: 20,
            height: 20,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '0.75rem',
            fontWeight: 'bold',
            zIndex: 10,
            boxShadow: '0 2px 4px rgba(0, 0, 0, 0.3)',
          }}
          title={`${errors.length} erreur(s): ${errors.map((e) => e.message).join(', ')}`}
        >
          {errors.length}
        </div>
      )}
      
      {/* Badge d'avertissement */}
      {!hasErrors && hasWarnings && (
        <div
          style={{
            position: 'absolute',
            top: 4,
            right: 4,
            backgroundColor: theme.state.warning.color,
            color: 'black',
            borderRadius: '50%',
            width: 20,
            height: 20,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '0.75rem',
            fontWeight: 'bold',
            zIndex: 10,
            boxShadow: '0 2px 4px rgba(0, 0, 0, 0.3)',
          }}
          title={`${warnings.length} avertissement(s): ${warnings.map((w) => w.message).join(', ')}`}
        >
          {warnings.length}
        </div>
      )}
      {/* Input Handle (haut) */}
      <Handle
        type="target"
        position={Position.Top}
        style={{
          background: '#4A90E2',
          width: 12,
          height: 12,
          border: '2px solid white',
        }}
      />
      
      {/* Header avec speaker */}
      <div
        style={{
          padding: '8px 12px',
          backgroundColor: speakerColor,
          borderBottom: `1px solid ${theme.border.primary}`,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}
      >
        <div
          style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            backgroundColor: 'white',
          }}
        />
        <span
          style={{
            fontSize: '0.85rem',
            fontWeight: 'bold',
            color: 'white',
            textShadow: '0 1px 2px rgba(0, 0, 0, 0.3)',
          }}
        >
          {speaker}
        </span>
      </div>
      
      {/* Contenu (dialogue) */}
      {line && (
        <div
          style={{
            padding: '12px',
            fontSize: '0.9rem',
            lineHeight: 1.4,
            color: theme.text.primary,
            whiteSpace: 'pre-wrap',
            wordWrap: 'break-word',
          }}
        >
          {truncatedLine}
        </div>
      )}
      
      {/* Aperçu des choix */}
      {hasChoices && (
        <div
          style={{
            padding: '8px 12px',
            borderTop: `1px solid ${theme.border.primary}`,
            backgroundColor: theme.background.secondary,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              marginBottom: choices.length > 0 ? '6px' : 0,
              fontSize: '0.75rem',
              fontWeight: 'bold',
              color: theme.text.secondary,
            }}
          >
            <span>⚡</span>
            <span>{choices.length} choix</span>
          </div>
          {/* Liste des choix (max 4, puis "... et X autres") */}
          {choices.slice(0, 4).map((choice, index) => {
            const truncatedText = (choice.text || '').length > 40 
              ? `${(choice.text || '').substring(0, 40)}...` 
              : (choice.text || '')
            
            return (
              <div
                key={index}
                style={{
                  padding: '4px 8px',
                  marginBottom: index < Math.min(choices.length, 4) - 1 ? '4px' : 0,
                  backgroundColor: theme.background.panel,
                  borderRadius: 4,
                  border: `1px solid ${theme.border.primary}`,
                  fontSize: '0.75rem',
                  color: theme.text.primary,
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 6,
                }}
              >
                <span
                  style={{
                    color: '#F5A623',
                    fontWeight: 'bold',
                    fontSize: '0.7rem',
                    flexShrink: 0,
                  }}
                >
                  {index + 1}.
                </span>
                <span style={{ flex: 1, lineHeight: 1.3 }}>
                  {truncatedText || '(choix vide)'}
                </span>
              </div>
            )
          })}
          {choices.length > 4 && (
            <div
              style={{
                marginTop: '4px',
                padding: '4px 8px',
                fontSize: '0.75rem',
                color: theme.text.secondary,
                fontStyle: 'italic',
              }}
            >
              ... et {choices.length - 4} autre{choices.length - 4 > 1 ? 's' : ''}
            </div>
          )}
        </div>
      )}
      
      {/* Output Handles (bas) */}
      {hasChoices ? (
        // Plusieurs handles pour les choix
        choices.map((_, index) => (
          <Handle
            key={index}
            type="source"
            position={Position.Bottom}
            id={`choice-${index}`}
            style={{
              background: '#F5A623',
              width: 12,
              height: 12,
              border: '2px solid white',
              left: `${((index + 1) / (choices.length + 1)) * 100}%`,
            }}
          />
        ))
      ) : (
        // Un seul handle pour nextNode
        <Handle
          type="source"
          position={Position.Bottom}
          style={{
            background: '#4A90E2',
            width: 12,
            height: 12,
            border: '2px solid white',
          }}
        />
      )}
    </div>
  )
})

/**
 * Génère une couleur consistante pour un speaker.
 */
function getSpeakerColor(speaker: string): string {
  const colors = [
    '#4A90E2', // Bleu
    '#9013FE', // Violet
    '#F5A623', // Orange
    '#E74C3C', // Rouge
    '#27AE60', // Vert
    '#16A085', // Turquoise
    '#8E44AD', // Violet foncé
    '#D35400', // Orange foncé
  ]
  
  // Hash simple du nom pour sélectionner une couleur
  let hash = 0
  for (let i = 0; i < speaker.length; i++) {
    hash = speaker.charCodeAt(i) + ((hash << 5) - hash)
  }
  
  return colors[Math.abs(hash) % colors.length]
}
