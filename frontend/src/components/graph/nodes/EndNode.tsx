/**
 * Nœud personnalisé pour afficher un nœud de fin de dialogue dans le graphe.
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

interface EndNodeData {
  id: string
  validationErrors?: ValidationError[]
  validationWarnings?: ValidationError[]
  isHighlighted?: boolean
  [key: string]: any
}

export const EndNode = memo(function EndNode({
  data,
  selected,
}: NodeProps<EndNodeData>) {
  const errors = data?.validationErrors || []
  const warnings = data?.validationWarnings || []
  const hasErrors = errors.length > 0
  const hasWarnings = warnings.length > 0
  const isHighlighted = data?.isHighlighted || false
  
  // Déterminer la couleur de la bordure selon les erreurs
  let borderColor = selected ? '#27AE60' : '#B8B8B8'
  if (hasErrors) {
    borderColor = theme.state.error.border
  } else if (hasWarnings) {
    borderColor = theme.state.warning.color
  }
  
  return (
    <div
      style={{
        width: 200,
        height: 80,
        border: `2px dashed ${borderColor}`,
        borderRadius: 8,
        backgroundColor: isHighlighted ? theme.state.selected.background : theme.background.secondary,
        boxShadow: selected
          ? '0 4px 12px rgba(0, 0, 0, 0.3)'
          : isHighlighted
          ? '0 0 0 3px rgba(116, 192, 252, 0.5)'
          : '0 2px 6px rgba(0, 0, 0, 0.1)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 8,
        opacity: 0.8,
        position: 'relative',
        transition: 'all 0.2s ease',
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
          background: '#B8B8B8',
          width: 12,
          height: 12,
          border: '2px solid white',
        }}
      />
      
      {/* Icône de fin */}
      <div style={{ fontSize: '1.5rem' }}>🏁</div>
      
      {/* Label */}
      <div
        style={{
          fontSize: '0.9rem',
          fontWeight: 'bold',
          color: theme.text.secondary,
          textAlign: 'center',
        }}
      >
        Fin du dialogue
      </div>
      
      {/* Pas de handle de sortie (c'est une fin) */}
    </div>
  )
})
