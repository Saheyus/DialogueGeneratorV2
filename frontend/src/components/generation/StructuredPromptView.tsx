/**
 * Composant pour afficher le prompt structuré avec sections dépliables.
 */
import { useState, useMemo } from 'react'
import { parsePromptSections, type PromptSection } from '../../hooks/usePromptPreview'
import { renderMarkdown } from '../../utils/markdownRenderer'
import { prettifyJsonInText } from '../../utils/jsonPrettifier'
import { theme } from '../../theme'

export interface StructuredPromptViewProps {
  /** Le prompt complet à afficher */
  prompt: string
}

/**
 * Composant accordéon pour une section du prompt (récursif pour supporter l'imbrication).
 */
function AccordionSection({ 
  section, 
  defaultExpanded = false,
  isControlled = false,
  controlledExpanded = false,
  onToggle,
  level = 0,
  sectionKey = '',
  expandedKeys = new Set<string>(),
  onToggleKey,
}: { 
  section: PromptSection
  defaultExpanded?: boolean
  isControlled?: boolean
  controlledExpanded?: boolean
  onToggle?: () => void
  level?: number
  sectionKey?: string
  expandedKeys?: Set<string>
  onToggleKey?: (key: string) => void
}) {
  const [internalExpanded, setInternalExpanded] = useState(defaultExpanded)
  const isExpanded = isControlled ? (sectionKey ? expandedKeys.has(sectionKey) : controlledExpanded) : internalExpanded
  
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
  
  const handleToggle = () => {
    if (isControlled) {
      if (sectionKey && onToggleKey) {
        onToggleKey(sectionKey)
      } else if (onToggle) {
        onToggle()
      }
    } else {
      setInternalExpanded(!internalExpanded)
    }
  }
  
  const hasChildren = section.children && section.children.length > 0
  const hasContent = section.content.trim().length > 0
  
  return (
    <div
      style={{
        border: `1px solid ${theme.border.primary}`,
        borderRadius: '4px',
        marginBottom: '0.5rem',
        marginLeft: level > 0 ? `${level}rem` : '0',
        overflow: 'hidden',
      }}
    >
      <button
        type="button"
        onClick={handleToggle}
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
        <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span>{section.title}</span>
          {section.tokenCount !== undefined && (
            <span
              style={{
                fontSize: '0.75rem',
                color: theme.text.secondary,
                fontWeight: 'normal',
              }}
            >
              ({section.tokenCount.toLocaleString()} tokens)
            </span>
          )}
        </span>
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
          {/* Afficher les enfants comme accordéons imbriqués s'il y en a */}
          {hasChildren && (
            <div style={{ marginBottom: hasContent ? '1rem' : '0' }}>
              {section.children!.map((child, index) => (
                <AccordionSection
                  key={`${child.title}-${index}`}
                  section={child}
                  defaultExpanded={false}
                  isControlled={true}
                  level={level + 1}
                  sectionKey={`${sectionKey}-${index}`}
                  expandedKeys={expandedKeys}
                  onToggleKey={onToggleKey}
                />
              ))}
            </div>
          )}
          
          {/* Afficher le contenu s'il y en a */}
          {hasContent && (
            <>
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
            </>
          )}
        </div>
      )}
    </div>
  )
}

/**
 * Collecte récursivement toutes les clés hiérarchiques d'une section et de ses enfants.
 */
function collectAllKeys(sections: PromptSection[], prefix: string = ''): string[] {
  const keys: string[] = []
  sections.forEach((section, index) => {
    const key = prefix ? `${prefix}-${index}` : `${index}`
    keys.push(key)
    if (section.children && section.children.length > 0) {
      keys.push(...collectAllKeys(section.children, key))
    }
  })
  return keys
}

export function StructuredPromptView({ prompt }: StructuredPromptViewProps) {
  const sections = useMemo(() => {
    return parsePromptSections(prompt)
  }, [prompt])
  
  const [allExpanded, setAllExpanded] = useState(false)
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(new Set())
  
  // Collecter toutes les clés disponibles
  const allKeys = useMemo(() => {
    return collectAllKeys(sections)
  }, [sections])
  
  const toggleAll = () => {
    const newExpanded = !allExpanded
    setAllExpanded(newExpanded)
    if (newExpanded) {
      setExpandedKeys(new Set(allKeys))
    } else {
      setExpandedKeys(new Set())
    }
  }
  
  const toggleKey = (key: string) => {
    setExpandedKeys((prev) => {
      const next = new Set(prev)
      if (next.has(key)) {
        next.delete(key)
        // Si on ferme une section, fermer aussi toutes ses sous-sections
        const keysToRemove = allKeys.filter(k => k.startsWith(key + '-'))
        keysToRemove.forEach(k => next.delete(k))
        if (next.size === 0) {
          setAllExpanded(false)
        }
      } else {
        next.add(key)
        // Vérifier si toutes les sections sont maintenant ouvertes
        if (next.size === allKeys.length) {
          setAllExpanded(true)
        }
      }
      return next
    })
  }
  
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
  
  return (
    <div style={{ padding: '0.5rem 0' }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'flex-end',
          marginBottom: '0.5rem',
        }}
      >
        <button
          type="button"
          onClick={toggleAll}
          style={{
            padding: '0.5rem 1rem',
            border: `1px solid ${theme.border.primary}`,
            borderRadius: '4px',
            backgroundColor: theme.background.secondary,
            color: theme.text.primary,
            cursor: 'pointer',
            fontSize: '0.85rem',
            transition: 'background-color 0.2s',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = theme.background.panel
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = theme.background.secondary
          }}
        >
          {allExpanded ? 'Tout replier' : 'Tout déplier'}
        </button>
      </div>
      {sections.map((section, index) => (
        <AccordionSection
          key={`${section.title}-${index}`}
          section={section}
          defaultExpanded={false}
          isControlled={true}
          level={0}
          sectionKey={`${index}`}
          expandedKeys={expandedKeys}
          onToggleKey={toggleKey}
        />
      ))}
    </div>
  )
}


