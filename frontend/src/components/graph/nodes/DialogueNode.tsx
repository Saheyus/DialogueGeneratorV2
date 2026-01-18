/**
 * Nœud personnalisé pour afficher un nœud de dialogue dans le graphe.
 */
import { memo, useState } from 'react'
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
  [key: string]: unknown
}

export const DialogueNode = memo(function DialogueNode({
  data,
  selected,
}: NodeProps<DialogueNodeData>) {
  const NODE_WIDTH = 280

  const speaker = data.speaker || 'PNJ'
  const line = data.line || ''
  const choices = data.choices || []
  const hasChoices = choices.length > 0
  const errors = data.validationErrors || []
  const warnings = data.validationWarnings || []
  const hasErrors = errors.length > 0
  const hasWarnings = warnings.length > 0
  const isHighlighted = data.isHighlighted || false
  const [isHovered, setIsHovered] = useState(false)
  const [hoveredChoiceIndex, setHoveredChoiceIndex] = useState<number | null>(null)
  
  // Tronquer le texte pour l'aperçu
  const truncatedLine = line.length > 100 ? `${line.substring(0, 100)}...` : line
  
  const handleGenerateClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    // Déclencher un événement custom pour ouvrir le panel de génération
    const event = new CustomEvent('open-ai-generation-panel', { 
      detail: { nodeId: data.id } 
    })
    window.dispatchEvent(event)
  }
  
  // Couleur du speaker (hash du nom pour consistance)
  const speakerColor = getSpeakerColor(speaker)
  
  // Déterminer la couleur de la bordure selon les erreurs
  let borderColor = selected ? '#27AE60' : '#4A90E2'
  if (hasErrors) {
    borderColor = theme.state.error.border
  } else if (hasWarnings) {
    borderColor = theme.state.warning.color
  }

  const getChoiceHandleLeftPercent = (index: number): number => {
    // Répartition uniforme sur la largeur du node, sans coller aux bords
    return ((index + 1) / (choices.length + 1)) * 100
  }
  
  return (
    <div
      style={{
        width: NODE_WIDTH,
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
        overflow: 'visible',
        position: 'relative',
        transition: 'all 0.2s ease',
        display: 'flex',
        flexDirection: 'column',
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
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
          title={errors.map((e, idx) => {
            const icon = e.type === 'orphan_node' ? '🔗' : e.type === 'broken_reference' ? '🔴' : e.type === 'empty_node' ? '⚪' : '⚠️'
            return `${icon} ${e.message}${idx < errors.length - 1 ? '\n' : ''}`
          }).join('')}
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
          title={warnings.map((w, idx) => {
            const icon = w.type === 'unreachable_node' ? '📍' : w.type === 'cycle_detected' ? '🔄' : '⚠️'
            return `${icon} ${w.message}${idx < warnings.length - 1 ? '\n' : ''}`
          }).join('')}
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
            paddingBottom: hasChoices ? '28px' : '12px', // Espace pour les ronds oranges si des choix existent
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
      
      {/* Tooltip au survol d'un rond orange (réponse associée) */}
      {hasChoices && hoveredChoiceIndex !== null && choices[hoveredChoiceIndex] && (
        <div
          style={{
            position: 'absolute',
            left: `${getChoiceHandleLeftPercent(hoveredChoiceIndex)}%`,
            bottom: 34,
            transform: 'translateX(-50%)',
            backgroundColor: theme.background.secondary,
            border: '1px solid #F5A623',
            color: theme.text.primary,
            padding: '6px 8px',
            borderRadius: 8,
            boxShadow: '0 6px 16px rgba(0, 0, 0, 0.35)',
            fontSize: '0.75rem',
            maxWidth: 260,
            lineHeight: 1.25,
            zIndex: 50,
            pointerEvents: 'none',
            whiteSpace: 'normal',
          }}
        >
          {choices[hoveredChoiceIndex].text || `Choix ${hoveredChoiceIndex + 1}`}
        </div>
      )}

      {/* Ronds oranges (handles) uniquement, dans la carte du nœud */}
      {hasChoices &&
        choices.map((choice, index) => {
          const leftPercent = getChoiceHandleLeftPercent(index)
          const label = choice.text || `Choix ${index + 1}`
          return (
            <Handle
              key={index}
              type="source"
              position={Position.Bottom}
              id={`choice-${index}`}
              title={label}
              onMouseEnter={() => setHoveredChoiceIndex(index)}
              onMouseLeave={() => setHoveredChoiceIndex((prev) => (prev === index ? null : prev))}
              style={{
                background: '#F5A623',
                width: 10,
                height: 10,
                border: '2px solid white',
                borderRadius: '50%',
                left: `${leftPercent}%`,
                bottom: 10,
                transform: 'translateX(-50%)',
              }}
            />
          )
        })}
      
      {/* Output Handle pour nextNode (si pas de choix) */}
      {!hasChoices && (
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
      
      {/* Bouton "Générer" visible au hover */}
      {(isHovered || selected) && (
        <button
          onClick={handleGenerateClick}
          style={{
            position: 'absolute',
            top: 34,
            right: 8,
            padding: '0.4rem 0.6rem',
            border: 'none',
            borderRadius: '6px',
            backgroundColor: theme.button.primary.background,
            color: theme.button.primary.color,
            cursor: 'pointer',
            fontSize: '0.75rem',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '0.3rem',
            boxShadow: '0 2px 6px rgba(0, 0, 0, 0.3)',
            zIndex: 15,
            transition: 'all 0.2s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'scale(1.05)'
            e.currentTarget.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.4)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'scale(1)'
            e.currentTarget.style.boxShadow = '0 2px 6px rgba(0, 0, 0, 0.3)'
          }}
          title="Générer la suite avec l'IA"
        >
          <span>✨</span>
          <span>Générer</span>
        </button>
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
