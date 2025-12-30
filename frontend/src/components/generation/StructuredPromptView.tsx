/**
 * Composant pour afficher le prompt structuré avec sections dépliables.
 */
import { useState, useMemo } from 'react'
import { parsePromptSections, type PromptSection } from '../../hooks/usePromptPreview'
import { renderMarkdown } from '../../utils/markdownRenderer'
import { prettifyJsonInText, hasJsonContent } from '../../utils/jsonPrettifier'
import { theme } from '../../theme'

export interface StructuredPromptViewProps {
  /** Le prompt complet à afficher */
  prompt: string
}

/**
 * Composant accordéon pour une section du prompt.
 */
function AccordionSection({ section, defaultExpanded = false }: { section: PromptSection; defaultExpanded?: boolean }) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)
  
  // Prettifier le JSON si présent
  const processedContent = useMemo(() => {
    if (section.hasJson) {
      return prettifyJsonInText(section.content)
    }
    return section.content
  }, [section.content, section.hasJson])
  
  // Détecter si le contenu est principalement du JSON
  const isMainlyJson = useMemo(() => {
    try {
      JSON.parse(section.content.trim())
      return true
    } catch {
      return false
    }
  }, [section.content])
  
  return (
    <div
      style={{
        border: `1px solid ${theme.border.primary}`,
        borderRadius: '4px',
        marginBottom: '0.5rem',
        overflow: 'hidden',
      }}
    >
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        style={{
          width: '100%',
          padding: '0.75rem 1rem',
          backgroundColor: isExpanded ? theme.background.secondary : theme.background.panel,
          border: 'none',
          borderBottom: isExpanded ? `1px solid ${theme.border.primary}` : 'none',
          color: theme.text.primary,
          textAlign: 'left',
          cursor: 'pointer',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '0.9rem',
          fontWeight: '500',
          transition: 'background-color 0.2s',
        }}
        onMouseEnter={(e) => {
          if (!isExpanded) {
            e.currentTarget.style.backgroundColor = theme.background.secondary
          }
        }}
        onMouseLeave={(e) => {
          if (!isExpanded) {
            e.currentTarget.style.backgroundColor = theme.background.panel
          }
        }}
      >
        <span>{section.title}</span>
        <span
          style={{
            fontSize: '0.75rem',
            color: theme.text.secondary,
            transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: 'transform 0.2s',
            display: 'inline-block',
          }}
        >
          ▼
        </span>
      </button>
      
      {isExpanded && (
        <div
          style={{
            padding: '1rem',
            backgroundColor: theme.background.secondary,
            color: theme.text.primary,
            fontSize: '0.85rem',
            lineHeight: '1.6',
          }}
        >
          {isMainlyJson ? (
            <pre
              style={{
                margin: 0,
                padding: '0.75rem',
                backgroundColor: '#1e1e1e',
                borderRadius: '4px',
                overflow: 'auto',
                fontFamily: 'monospace',
                fontSize: '0.85rem',
                color: theme.text.primary,
              }}
            >
              {processedContent}
            </pre>
          ) : (
            <div style={{ whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}>
              {renderMarkdown(processedContent)}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export function StructuredPromptView({ prompt }: StructuredPromptViewProps) {
  const sections = useMemo(() => {
    return parsePromptSections(prompt)
  }, [prompt])
  
  if (sections.length === 0) {
    return (
      <div
        style={{
          padding: '2rem',
          textAlign: 'center',
          color: theme.text.secondary,
        }}
      >
        Aucune section trouvée dans le prompt.
      </div>
    )
  }
  
  // Déplier par défaut les sections importantes
  const importantSections = [
    'System Prompt',
    'CADRE DE LA SCÈNE',
    'CONTEXTE GÉNÉRAL DE LA SCÈNE',
    'OBJECTIF DE LA SCÈNE (Instruction Utilisateur)',
    'BRIEF DE SCÈNE (LOCAL)',
  ]
  
  return (
    <div style={{ padding: '0.5rem 0' }}>
      {sections.map((section, index) => (
        <AccordionSection
          key={`${section.title}-${index}`}
          section={section}
          defaultExpanded={importantSections.includes(section.title)}
        />
      ))}
    </div>
  )
}


