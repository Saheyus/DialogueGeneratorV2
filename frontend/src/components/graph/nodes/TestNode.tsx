/**
 * Nœud personnalisé pour afficher un nœud de test d'attribut dans le graphe.
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

interface TestNodeData {
  id: string
  test?: string
  line?: string
  successNode?: string
  failureNode?: string
  validationErrors?: ValidationError[]
  validationWarnings?: ValidationError[]
  isHighlighted?: boolean
  [key: string]: unknown
}

export const TestNode = memo(function TestNode({
  data,
  selected,
}: NodeProps<TestNodeData>) {
  const test = data.test || 'Test non défini'
  const line = data.line || ''
  const errors = data.validationErrors || []
  const warnings = data.validationWarnings || []
  const hasErrors = errors.length > 0
  const hasWarnings = warnings.length > 0
  const isHighlighted = data.isHighlighted || false
  const [isHovered, setIsHovered] = useState(false)
  
  // Tronquer le dialogue si présent
  const truncatedLine = line.length > 80 ? `${line.substring(0, 80)}...` : line
  
  const handleGenerateClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    // Déclencher un événement custom pour ouvrir le panel de génération
    const event = new CustomEvent('open-ai-generation-panel', { 
      detail: { nodeId: data.id } 
    })
    window.dispatchEvent(event)
  }
  
  // Déterminer la couleur de la bordure selon les erreurs
  let borderColor = selected ? '#27AE60' : '#F5A623'
  if (hasErrors) {
    borderColor = theme.state.error.border
  } else if (hasWarnings) {
    borderColor = theme.state.warning.color
  }
  
  return (
    <div
      style={{
        width: 250,
        minHeight: 100,
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
            const icon = e.type === 'orphan_node' ? '🔗' : e.type === 'broken_reference' ? '🔴' : e.type === 'empty_node' ? '⚪' : e.type === 'missing_test' ? '❓' : '⚠️'
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
          background: '#F5A623',
          width: 12,
          height: 12,
          border: '2px solid white',
        }}
      />
      
      {/* Header avec icône de dé */}
      <div
        style={{
          padding: '8px 12px',
          backgroundColor: '#F5A623',
          borderBottom: `1px solid ${theme.border.primary}`,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}
      >
        <span style={{ fontSize: '1.2rem' }}>🎲</span>
        <span
          style={{
            fontSize: '0.85rem',
            fontWeight: 'bold',
            color: 'white',
            textShadow: '0 1px 2px rgba(0, 0, 0, 0.3)',
          }}
        >
          Test d'attribut
        </span>
      </div>
      
      {/* Test (format: Attribut+Compétence:DD) */}
      <div
        style={{
          padding: '12px',
          backgroundColor: theme.background.secondary,
          borderBottom: `1px solid ${theme.border.primary}`,
        }}
      >
        <div
          style={{
            fontFamily: 'monospace',
            fontSize: '0.85rem',
            color: theme.text.primary,
            fontWeight: 'bold',
            textAlign: 'center',
          }}
        >
          {test}
        </div>
      </div>
      
      {/* Dialogue contextuel (optionnel) */}
      {line && (
        <div
          style={{
            padding: '12px',
            fontSize: '0.85rem',
            lineHeight: 1.4,
            color: theme.text.secondary,
            fontStyle: 'italic',
            whiteSpace: 'pre-wrap',
            wordWrap: 'break-word',
          }}
        >
          {truncatedLine}
        </div>
      )}
      
      {/* Labels pour success/failure */}
      <div
        style={{
          padding: '8px 12px',
          borderTop: `1px solid ${theme.border.primary}`,
          backgroundColor: theme.background.panel,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '0.75rem',
          color: theme.text.secondary,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <span style={{ color: '#27AE60' }}>✓</span>
          <span>Succès</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <span style={{ color: '#E74C3C' }}>✗</span>
          <span>Échec</span>
        </div>
      </div>
      
      {/* Output Handles (bas) - success à gauche, failure à droite */}
      <Handle
        type="source"
        position={Position.Bottom}
        id="success"
        style={{
          background: '#27AE60',
          width: 12,
          height: 12,
          border: '2px solid white',
          left: '25%',
        }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="failure"
        style={{
          background: '#E74C3C',
          width: 12,
          height: 12,
          border: '2px solid white',
          left: '75%',
        }}
      />
      
      {/* Bouton "Générer" visible au hover */}
      {(isHovered || selected) && (
        <button
          onClick={handleGenerateClick}
          style={{
            position: 'absolute',
            bottom: 8,
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
