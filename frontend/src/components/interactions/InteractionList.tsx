/**
 * Composant pour afficher la liste des interactions avec recherche et filtres.
 */
import { useState, useEffect } from 'react'
import * as interactionsAPI from '../../api/interactions'
import { getErrorMessage } from '../../types/errors'
import { theme } from '../../theme'
import type { InteractionResponse } from '../../types/api'
import { InteractionItem } from './InteractionItem'

interface InteractionListProps {
  onSelectInteraction: (interaction: InteractionResponse | null) => void
  selectedInteractionId: string | null
}

export function InteractionList({ onSelectInteraction, selectedInteractionId }: InteractionListProps) {
  const [interactions, setInteractions] = useState<InteractionResponse[]>([])
  const [filteredInteractions, setFilteredInteractions] = useState<InteractionResponse[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadInteractions()
  }, [])

  useEffect(() => {
    // Filtrer les interactions selon la recherche
    if (!searchQuery.trim()) {
      setFilteredInteractions(interactions)
    } else {
      const query = searchQuery.toLowerCase()
      const filtered = interactions.filter(
        (interaction) =>
          interaction.title.toLowerCase().includes(query) ||
          interaction.interaction_id.toLowerCase().includes(query) ||
          JSON.stringify(interaction.elements).toLowerCase().includes(query) ||
          interaction.header_tags?.some((tag) => tag.toLowerCase().includes(query))
      )
      setFilteredInteractions(filtered)
    }
  }, [searchQuery, interactions])

  const loadInteractions = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await interactionsAPI.listInteractions()
      setInteractions(response.interactions)
      setFilteredInteractions(response.interactions)
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
          }}
        />
        <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: theme.text.secondary }}>
          {filteredInteractions.length} interaction{filteredInteractions.length !== 1 ? 's' : ''}
          {searchQuery && ` (sur ${interactions.length} total)`}
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

