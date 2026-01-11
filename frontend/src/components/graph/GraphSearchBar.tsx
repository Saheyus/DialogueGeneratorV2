/**
 * Barre de recherche et filtrage pour le graphe.
 * Permet de rechercher des nœuds par ID, texte, speaker et filtrer par type.
 */
import { useState, useCallback, useMemo, useEffect, useRef } from 'react'
import { useGraphStore } from '../../store/graphStore'
import { theme } from '../../theme'
import type { Node } from 'reactflow'

interface GraphSearchBarProps {
  onNodeSelect?: (nodeId: string) => void
}

export function GraphSearchBar({ onNodeSelect }: GraphSearchBarProps) {
  const { nodes, setSelectedNode, setHighlightedNodes } = useGraphStore()
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTypeFilter, setSelectedTypeFilter] = useState<string | null>(null)
  const [currentResultIndex, setCurrentResultIndex] = useState(-1)
  const searchInputRef = useRef<HTMLInputElement>(null)
  
  // Recherche insensible à la casse dans ID, speaker, line
  const searchResults = useMemo(() => {
    if (!searchQuery.trim()) {
      return []
    }
    
    const query = searchQuery.toLowerCase().trim()
    const results: Node[] = []
    
    for (const node of nodes) {
      // Filtrer par type si un filtre est sélectionné
      if (selectedTypeFilter && node.type !== selectedTypeFilter) {
        continue
      }
      
      // Rechercher dans ID
      if (node.id.toLowerCase().includes(query)) {
        results.push(node)
        continue
      }
      
      // Rechercher dans speaker
      if (node.data?.speaker && node.data.speaker.toLowerCase().includes(query)) {
        results.push(node)
        continue
      }
      
      // Rechercher dans line
      if (node.data?.line && node.data.line.toLowerCase().includes(query)) {
        results.push(node)
        continue
      }
    }
    
    return results
  }, [nodes, searchQuery, selectedTypeFilter])
  
  // Navigation dans les résultats avec flèches haut/bas
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+F pour focus la recherche
      if (e.ctrlKey && e.key === 'f') {
        e.preventDefault()
        searchInputRef.current?.focus()
        return
      }
      
      // Si la recherche n'est pas active, ne rien faire
      if (document.activeElement !== searchInputRef.current && !searchQuery) {
        return
      }
      
      // Flèches haut/bas pour naviguer dans les résultats
      if (e.key === 'ArrowDown' && searchResults.length > 0) {
        e.preventDefault()
        const nextIndex = currentResultIndex < searchResults.length - 1 
          ? currentResultIndex + 1 
          : 0
        setCurrentResultIndex(nextIndex)
        const node = searchResults[nextIndex]
        if (node) {
          setSelectedNode(node.id)
          onNodeSelect?.(node.id)
        }
      } else if (e.key === 'ArrowUp' && searchResults.length > 0) {
        e.preventDefault()
        const prevIndex = currentResultIndex > 0 
          ? currentResultIndex - 1 
          : searchResults.length - 1
        setCurrentResultIndex(prevIndex)
        const node = searchResults[prevIndex]
        if (node) {
          setSelectedNode(node.id)
          onNodeSelect?.(node.id)
        }
      } else if (e.key === 'Escape') {
        setSearchQuery('')
        setCurrentResultIndex(-1)
        searchInputRef.current?.blur()
      }
    }
    
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [searchQuery, searchResults, currentResultIndex, setSelectedNode, onNodeSelect])
  
  // Réinitialiser l'index quand la recherche change
  useEffect(() => {
    setCurrentResultIndex(-1)
  }, [searchQuery])
  
  // Mettre à jour les nœuds en surbrillance quand les résultats changent
  useEffect(() => {
    if (searchQuery.trim() && searchResults.length > 0) {
      setHighlightedNodes(searchResults.map((n) => n.id))
    } else {
      setHighlightedNodes([])
    }
  }, [searchQuery, searchResults, setHighlightedNodes])
  
  // Types de nœuds disponibles
  const nodeTypes = useMemo(() => {
    const types = new Set<string>()
    nodes.forEach((node) => {
      if (node.type) {
        types.add(node.type)
      }
    })
    return Array.from(types)
  }, [nodes])
  
  const handleResultClick = useCallback((nodeId: string) => {
    setSelectedNode(nodeId)
    onNodeSelect?.(nodeId)
  }, [setSelectedNode, onNodeSelect])
  
  return (
    <div style={{
      padding: '0.75rem',
      borderBottom: `1px solid ${theme.border.primary}`,
      backgroundColor: theme.background.panelHeader,
    }}>
      {/* Barre de recherche */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
        <input
          ref={searchInputRef}
          type="text"
          placeholder="Rechercher (Ctrl+F)..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            flex: 1,
            padding: '0.5rem 0.75rem',
            border: `1px solid ${theme.input.border}`,
            borderRadius: '6px',
            backgroundColor: theme.input.background,
            color: theme.input.color,
            fontSize: '0.9rem',
          }}
        />
        {searchQuery && (
          <button
            onClick={() => {
              setSearchQuery('')
              setCurrentResultIndex(-1)
              searchInputRef.current?.focus()
            }}
            style={{
              padding: '0.5rem',
              border: `1px solid ${theme.border.primary}`,
              borderRadius: '6px',
              backgroundColor: theme.button.default.background,
              color: theme.button.default.color,
              cursor: 'pointer',
              fontSize: '0.9rem',
            }}
            title="Effacer"
          >
            ✕
          </button>
        )}
      </div>
      
      {/* Filtres par type */}
      {nodeTypes.length > 0 && (
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <button
            onClick={() => setSelectedTypeFilter(null)}
            style={{
              padding: '0.25rem 0.75rem',
              border: `1px solid ${selectedTypeFilter === null ? theme.button.primary.background : theme.input.border}`,
              borderRadius: '4px',
              backgroundColor: selectedTypeFilter === null ? theme.button.primary.background : theme.input.background,
              color: selectedTypeFilter === null ? theme.button.primary.color : theme.input.color,
              cursor: 'pointer',
              fontSize: '0.8rem',
            }}
          >
            Tous
          </button>
          {nodeTypes.map((type) => (
            <button
              key={type}
              onClick={() => setSelectedTypeFilter(type)}
              style={{
                padding: '0.25rem 0.75rem',
                border: `1px solid ${selectedTypeFilter === type ? theme.button.primary.background : theme.input.border}`,
                borderRadius: '4px',
                backgroundColor: selectedTypeFilter === type ? theme.button.primary.background : theme.input.background,
                color: selectedTypeFilter === type ? theme.button.primary.color : theme.input.color,
                cursor: 'pointer',
                fontSize: '0.8rem',
              }}
            >
              {type === 'dialogueNode' ? 'Dialogue' : 
               type === 'testNode' ? 'Test' : 
               type === 'endNode' ? 'Fin' : type}
            </button>
          ))}
        </div>
      )}
      
      {/* Résultats de recherche */}
      {searchQuery && searchResults.length > 0 && (
        <div style={{
          marginTop: '0.75rem',
          padding: '0.5rem',
          backgroundColor: theme.background.secondary,
          borderRadius: '6px',
          maxHeight: '200px',
          overflowY: 'auto',
          fontSize: '0.85rem',
        }}>
          <div style={{ 
            fontWeight: 'bold', 
            marginBottom: '0.5rem',
            color: theme.text.primary,
          }}>
            {searchResults.length} résultat(s) - Utilisez ↑↓ pour naviguer
          </div>
          {searchResults.map((node, index) => (
            <div
              key={node.id}
              onClick={() => handleResultClick(node.id)}
              style={{
                padding: '0.5rem',
                marginBottom: '0.25rem',
                borderRadius: '4px',
                backgroundColor: index === currentResultIndex 
                  ? theme.button.selected.background 
                  : 'transparent',
                border: `1px solid ${index === currentResultIndex 
                  ? theme.button.selected.border 
                  : 'transparent'}`,
                cursor: 'pointer',
                color: theme.text.primary,
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => {
                if (index !== currentResultIndex) {
                  e.currentTarget.style.backgroundColor = theme.state.hover.background
                }
              }}
              onMouseLeave={(e) => {
                if (index !== currentResultIndex) {
                  e.currentTarget.style.backgroundColor = 'transparent'
                }
              }}
            >
              <div style={{ fontWeight: 'bold', marginBottom: '0.25rem' }}>
                {node.id}
              </div>
              {node.data?.speaker && (
                <div style={{ fontSize: '0.8rem', color: theme.text.secondary }}>
                  Speaker: {node.data.speaker}
                </div>
              )}
              {node.data?.line && (
                <div style={{ 
                  fontSize: '0.8rem', 
                  color: theme.text.tertiary,
                  marginTop: '0.25rem',
                  maxHeight: '40px',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}>
                  {node.data.line.substring(0, 60)}
                  {node.data.line.length > 60 ? '...' : ''}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
      
      {searchQuery && searchResults.length === 0 && (
        <div style={{
          marginTop: '0.75rem',
          padding: '0.5rem',
          textAlign: 'center',
          color: theme.text.secondary,
          fontSize: '0.85rem',
        }}>
          Aucun résultat trouvé
        </div>
      )}
    </div>
  )
}
