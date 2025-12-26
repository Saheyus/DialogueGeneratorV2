/**
 * Composant pour afficher la liste des interactions avec recherche et filtres.
 */
import { useState, useEffect, useMemo } from 'react'
import * as interactionsAPI from '../../api/interactions'
import { getErrorMessage } from '../../types/errors'
import { theme } from '../../theme'
import type { InteractionResponse } from '../../types/api'
import { InteractionItem } from './InteractionItem'

interface InteractionListProps {
  onSelectInteraction: (interaction: InteractionResponse | null) => void
  selectedInteractionId: string | null
}

type FilterStatus = 'all' | 'draft' | 'validated'

export function InteractionList({ onSelectInteraction, selectedInteractionId }: InteractionListProps) {
  const [interactions, setInteractions] = useState<InteractionResponse[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [filterStatus, setFilterStatus] = useState<FilterStatus>('all')
  const [filterTags, setFilterTags] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadInteractions()
  }, [])

  // Extraire tous les tags disponibles
  const availableTags = useMemo(() => {
    const tagsSet = new Set<string>()
    interactions.forEach((interaction) => {
      interaction.header_tags?.forEach((tag) => tagsSet.add(tag))
    })
    return Array.from(tagsSet).sort()
  }, [interactions])

  // Filtrer les interactions
  const filteredInteractions = useMemo(() => {
    let filtered = interactions

    // Filtre par recherche
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(
        (interaction) =>
          interaction.title.toLowerCase().includes(query) ||
          interaction.interaction_id.toLowerCase().includes(query) ||
          JSON.stringify(interaction.elements).toLowerCase().includes(query) ||
          interaction.header_tags?.some((tag) => tag.toLowerCase().includes(query))
      )
    }

    // Filtre par tags
    if (filterTags.length > 0) {
      filtered = filtered.filter((interaction) =>
        filterTags.some((tag) => interaction.header_tags?.includes(tag))
      )
    }

    // Filtre par statut (simplifié - on peut améliorer avec un champ statut réel)
    if (filterStatus !== 'all') {
      filtered = filtered.filter((interaction) => {
        const hasDraftTag = interaction.header_tags?.includes('draft')
        if (filterStatus === 'draft') return hasDraftTag
        if (filterStatus === 'validated') return !hasDraftTag
        return true
      })
    }

    return filtered
  }, [interactions, searchQuery, filterTags, filterStatus])

  const loadInteractions = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await interactionsAPI.listInteractions()
      setInteractions(response.interactions)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }

  const handleItemClick = (interaction: InteractionResponse) => {
    if (selectedInteractionId === interaction.interaction_id) {
      onSelectInteraction(null)
    } else {
      onSelectInteraction(interaction)
    }
  }

  if (isLoading) {
    return (
      <div style={{ padding: '1rem', textAlign: 'center', color: theme.text.secondary }}>
        <div>Chargement des interactions...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ 
        padding: '1rem', 
        color: theme.state.error.color, 
        backgroundColor: theme.state.error.background, 
        borderRadius: '4px' 
      }}>
        {error}
        <button
          onClick={loadInteractions}
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

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ padding: '0.5rem', borderBottom: `1px solid ${theme.border.primary}` }}>
        <input
          type="text"
          placeholder="Rechercher une interaction..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            width: '100%',
            padding: '0.5rem',
            border: `1px solid ${theme.input.border}`,
            borderRadius: '4px',
            boxSizing: 'border-box',
            backgroundColor: theme.input.background,
            color: theme.input.color,
            marginBottom: '0.5rem',
          }}
        />
        
        {/* Filtres */}
        <div style={{ marginBottom: '0.5rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as FilterStatus)}
            style={{
              padding: '0.25rem 0.5rem',
              border: `1px solid ${theme.input.border}`,
              borderRadius: '4px',
              backgroundColor: theme.input.background,
              color: theme.input.color,
              fontSize: '0.85rem',
            }}
          >
            <option value="all">Tous les statuts</option>
            <option value="draft">Brouillons</option>
            <option value="validated">Validés</option>
          </select>
        </div>

        {/* Tags filtres */}
        {availableTags.length > 0 && (
          <div style={{ marginBottom: '0.5rem', fontSize: '0.85rem' }}>
            <div style={{ color: theme.text.secondary, marginBottom: '0.25rem' }}>Tags:</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
              {availableTags.map((tag) => {
                const isSelected = filterTags.includes(tag)
                return (
                  <button
                    key={tag}
                    onClick={() => {
                      if (isSelected) {
                        setFilterTags(filterTags.filter((t) => t !== tag))
                      } else {
                        setFilterTags([...filterTags, tag])
                      }
                    }}
                    style={{
                      padding: '0.125rem 0.5rem',
                      border: `1px solid ${theme.border.primary}`,
                      borderRadius: '12px',
                      backgroundColor: isSelected
                        ? theme.button.primary.background
                        : theme.button.default.background,
                      color: isSelected
                        ? theme.button.primary.color
                        : theme.button.default.color,
                      cursor: 'pointer',
                      fontSize: '0.75rem',
                    }}
                  >
                    {tag}
                  </button>
                )
              })}
            </div>
          </div>
        )}

        <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: theme.text.secondary }}>
          {filteredInteractions.length} interaction{filteredInteractions.length !== 1 ? 's' : ''}
          {(searchQuery || filterTags.length > 0 || filterStatus !== 'all') &&
            ` (sur ${interactions.length} total)`}
        </div>
      </div>
      <div style={{ flex: 1, overflowY: 'auto', padding: '0.5rem' }}>
        {filteredInteractions.length === 0 ? (
          <div style={{ padding: '1rem', textAlign: 'center', color: theme.text.secondary }}>
            {searchQuery ? 'Aucune interaction trouvée' : 'Aucune interaction'}
          </div>
        ) : (
          filteredInteractions.map((interaction) => (
            <InteractionItem
              key={interaction.interaction_id}
              interaction={interaction}
              onClick={() => handleItemClick(interaction)}
              isSelected={selectedInteractionId === interaction.interaction_id}
            />
          ))
        )}
      </div>
    </div>
  )
}

