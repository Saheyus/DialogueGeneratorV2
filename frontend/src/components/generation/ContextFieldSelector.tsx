/**
 * Composant pour sélectionner les champs de contexte à inclure.
 */
import { useState, useMemo, useCallback, useEffect } from 'react'
import { useContextConfigStore, type FieldInfo } from '../../store/contextConfigStore'
import { theme } from '../../theme'

export interface ContextFieldSelectorProps {
  elementType: string
  onFieldsChange?: (fields: string[]) => void
  showOnlyEssential?: boolean  // Si true, n'affiche que les champs essentiels
}

interface FieldNode {
  path: string
  label: string
  fieldInfo: FieldInfo
  children: FieldNode[]
  parent?: FieldNode
}

export function ContextFieldSelector({
  elementType,
  onFieldsChange,
  showOnlyEssential = false,
}: ContextFieldSelectorProps) {
  const {
    availableFields,
    fieldConfigs,
    essentialFields,
    suggestions,
    toggleField,
    detectFields,
    isLoading,
    error,
  } = useContextConfigStore()

  const [searchQuery, setSearchQuery] = useState('')
  const [expandedPaths, setExpandedPaths] = useState<Set<string>>(new Set())

  // Charger les champs au montage
  useEffect(() => {
    if (!availableFields[elementType] || Object.keys(availableFields[elementType]).length === 0) {
      detectFields(elementType).catch(console.error)
    }
  }, [elementType, availableFields, detectFields])

  // Construire l'arbre hiérarchique
  const fieldTree = useMemo(() => {
    const fields = availableFields[elementType] || {}
    const root: FieldNode[] = []
    const nodeMap = new Map<string, FieldNode>()

    // Filtrer les champs selon showOnlyEssential
    // showOnlyEssential=true affiche les métadonnées (is_metadata=true)
    // showOnlyEssential=false affiche le contexte narratif (is_metadata=false)
    const filteredFields = showOnlyEssential
      ? Object.fromEntries(
          Object.entries(fields).filter(([path, fieldInfo]: [string, any]) => fieldInfo.is_metadata === true)
        )
      : Object.fromEntries(
          Object.entries(fields).filter(([path, fieldInfo]: [string, any]) => fieldInfo.is_metadata !== true)
        )
    
    // Créer tous les nœuds
    for (const [path, fieldInfo] of Object.entries(filteredFields)) {
      const parts = path.split('.')
      let currentPath = ''
      
      for (let i = 0; i < parts.length; i++) {
        const part = parts[i]
        currentPath = currentPath ? `${currentPath}.${part}` : part
        
        if (!nodeMap.has(currentPath)) {
          const isLeaf = i === parts.length - 1
          const node: FieldNode = {
            path: currentPath,
            label: isLeaf ? fieldInfo.label : part.replace(/_/g, ' ').replace(/-/g, ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' '),
            fieldInfo: isLeaf ? fieldInfo : {
              path: currentPath,
              label: part,
              type: 'dict',
              depth: i,
              frequency: 1.0,
              suggested: false,
            },
            children: [],
            parent: i > 0 ? nodeMap.get(parts.slice(0, i).join('.')) : undefined,
          }
          nodeMap.set(currentPath, node)
          
          if (i === 0) {
            root.push(node)
          } else {
            const parentPath = parts.slice(0, i).join('.')
            const parent = nodeMap.get(parentPath)
            if (parent) {
              parent.children.push(node)
            }
          }
        }
      }
    }

    return root
  }, [availableFields, elementType, showOnlyEssential])

  // Filtrer l'arbre selon la recherche
  const filteredTree = useMemo(() => {
    if (!searchQuery.trim()) {
      return fieldTree
    }

    const query = searchQuery.toLowerCase()
    const filterNode = (node: FieldNode): FieldNode | null => {
      const matches = node.label.toLowerCase().includes(query) || 
                     node.path.toLowerCase().includes(query)
      
      const filteredChildren = node.children
        .map(filterNode)
        .filter((n): n is FieldNode => n !== null)
      
      if (matches || filteredChildren.length > 0) {
        return {
          ...node,
          children: filteredChildren,
        }
      }
      
      return null
    }

    return fieldTree.map(filterNode).filter((n): n is FieldNode => n !== null)
  }, [fieldTree, searchQuery])

  const selectedFields = fieldConfigs[elementType] || []
  const essentialFieldsForType = essentialFields[elementType] || []
  const suggestedFields = suggestions[elementType] || []

  const handleToggleField = useCallback((fieldPath: string) => {
    // Ne pas permettre la désélection des champs essentiels
    if (essentialFieldsForType.includes(fieldPath)) {
      return
    }
    
    toggleField(elementType, fieldPath)
    const newSelection = selectedFields.includes(fieldPath)
      ? selectedFields.filter(f => f !== fieldPath)
      : [...selectedFields, fieldPath]
    onFieldsChange?.(newSelection)
  }, [elementType, selectedFields, availableFields, toggleField, onFieldsChange])

  const toggleExpanded = useCallback((path: string) => {
    setExpandedPaths(prev => {
      const next = new Set(prev)
      if (next.has(path)) {
        next.delete(path)
      } else {
        next.add(path)
      }
      return next
    })
  }, [])

  const getFieldIndicator = (fieldInfo: FieldInfo) => {
    const isSuggested = fieldInfo.suggested || suggestedFields.includes(fieldInfo.path)
    const importance = fieldInfo.importance || 
      (fieldInfo.frequency >= 0.8 ? 'essential' : 
       fieldInfo.frequency >= 0.2 ? 'common' : 'rare')
    
    if (isSuggested) {
      return { icon: '✓', color: theme.state.success.color, title: 'Champ suggéré' }
    }
    
    switch (importance) {
      case 'essential':
        return { icon: '⭐', color: theme.state.info.color, title: 'Champ essentiel' }
      case 'common':
        return { icon: 'ⓘ', color: theme.text.secondary, title: 'Champ commun' }
      case 'rare':
        return { icon: '○', color: theme.text.tertiary, title: 'Champ rare' }
      default:
        return null
    }
  }

  const renderFieldNode = (node: FieldNode, depth: number = 0): JSX.Element => {
    const isExpanded = expandedPaths.has(node.path)
    const hasChildren = node.children.length > 0
    // is_essential concerne uniquement les champs essentiels du contexte narratif (pour génération minimale)
    const isEssential = node.fieldInfo.is_essential === true
    const isSelected = isEssential || selectedFields.includes(node.path)
    const isLeaf = node.fieldInfo.type !== 'dict'
    const indicator = getFieldIndicator(node.fieldInfo)

    return (
      <div key={node.path}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            padding: '0.5rem',
            paddingLeft: `${depth * 1.5 + 0.5}rem`,
            cursor: isLeaf ? 'pointer' : 'default',
            backgroundColor: isSelected ? theme.state.selected.background : 'transparent',
            borderRadius: '4px',
            marginBottom: '0.25rem',
          }}
          onClick={() => {
            if (hasChildren) {
              toggleExpanded(node.path)
            } else if (isLeaf) {
              handleToggleField(node.path)
            }
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
          title={node.fieldInfo.category ? `Catégorie: ${node.fieldInfo.category}` : undefined}
        >
          {hasChildren && (
            <span
              style={{
                marginRight: '0.5rem',
                color: theme.text.secondary,
                userSelect: 'none',
              }}
            >
              {isExpanded ? '▼' : '▶'}
            </span>
          )}
          
          {isLeaf && (
            <input
              type="checkbox"
              checked={isSelected}
              disabled={isEssential}
              onChange={(e) => {
                e.stopPropagation()
                if (!isEssential) {
                  handleToggleField(node.path)
                }
              }}
              onClick={(e) => e.stopPropagation()}
              style={{
                marginRight: '0.5rem',
                cursor: isEssential ? 'not-allowed' : 'pointer',
                opacity: isEssential ? 0.6 : 1,
              }}
              title={isEssential ? 'Champ essentiel (toujours sélectionné)' : undefined}
            />
          )}
          
          {indicator && (
            <span
              style={{
                marginRight: '0.5rem',
                color: indicator.color,
                fontSize: '0.9rem',
              }}
              title={indicator.title}
            >
              {indicator.icon}
            </span>
          )}
          
          <span
            style={{
              flex: 1,
              color: theme.text.primary,
              fontWeight: isSelected ? 'bold' : 'normal',
            }}
          >
            {node.label}
          </span>
          
          {isLeaf && (
            <span
              style={{
                fontSize: '0.75rem',
                color: theme.text.tertiary,
                marginLeft: '0.5rem',
              }}
            >
              ({node.fieldInfo.type})
            </span>
          )}
        </div>
        
        {hasChildren && isExpanded && (
          <div>
            {node.children.map(child => renderFieldNode(child, depth + 1))}
          </div>
        )}
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
        Erreur: {error}
        <button
          onClick={() => detectFields(elementType)}
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

  if (isLoading) {
    return (
      <div style={{ padding: '1rem', textAlign: 'center', color: theme.text.secondary }}>
        Détection des champs en cours...
      </div>
    )
  }

  // Compter les champs visibles (filtrés) et sélectionnés
  // showOnlyEssential=true : afficher les métadonnées (is_metadata=true)
  // showOnlyEssential=false : afficher le contexte narratif (is_metadata=false)
  const fields = availableFields[elementType] || {}
  const visibleFields = showOnlyEssential
    ? Object.keys(fields).filter(path => fields[path]?.is_metadata === true)
    : Object.keys(fields).filter(path => fields[path]?.is_metadata !== true)
  
  const totalFields = visibleFields.length
  
  // Compter uniquement les champs sélectionnés parmi ceux visibles dans l'onglet actuel
  // Note: is_essential concerne les champs essentiels du contexte narratif (pour génération minimale)
  const visibleSelectedFields = visibleFields.filter(path => {
    const isEssential = fields[path]?.is_essential === true
    if (isEssential) {
      return true  // Les champs essentiels du contexte narratif sont toujours sélectionnés
    }
    return selectedFields.includes(path)
  })
  const visibleSelectedCount = visibleSelectedFields.length
  
  // Afficher le comptage pour l'onglet actuel uniquement
  const selectedCount = visibleSelectedCount
  const totalFieldsToDisplay = totalFields

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ marginBottom: '1rem' }}>
        <input
          type="text"
          placeholder="Rechercher un champ..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            width: '100%',
            padding: '0.5rem',
            border: `1px solid ${theme.border.primary}`,
            borderRadius: '4px',
            backgroundColor: theme.input.background,
            color: theme.input.color,
          }}
        />
        <div
          style={{
            marginTop: '0.5rem',
            fontSize: '0.85rem',
            color: theme.text.secondary,
          }}
        >
          {selectedCount} / {totalFieldsToDisplay} champs sélectionnés
        </div>
      </div>

      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '0.5rem',
          border: `1px solid ${theme.border.primary}`,
          borderRadius: '4px',
          backgroundColor: theme.background.panel,
        }}
      >
        {filteredTree.length === 0 ? (
          <div style={{ padding: '1rem', textAlign: 'center', color: theme.text.secondary }}>
            {totalFields === 0
              ? 'Aucun champ détecté. Cliquez sur "Détecter automatiquement".'
              : 'Aucun champ ne correspond à la recherche.'}
          </div>
        ) : (
          filteredTree.map(node => renderFieldNode(node))
        )}
      </div>
    </div>
  )
}

