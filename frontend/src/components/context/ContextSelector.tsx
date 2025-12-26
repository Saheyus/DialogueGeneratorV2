/**
 * Composant principal de sélection de contexte avec onglets pour personnages, lieux et objets.
 */
import { useState, useEffect } from 'react'
import * as contextAPI from '../../api/context'
import type { 
  CharacterResponse, 
  LocationResponse, 
  ItemResponse,
  SpeciesResponse,
  CommunityResponse,
} from '../../types/api'
import { ContextList } from './ContextList'
import { SelectedContextSummary } from './SelectedContextSummary'
import { useContextStore } from '../../store/contextStore'
import { getErrorMessage } from '../../types/errors'
import { theme } from '../../theme'

type TabType = 'characters' | 'locations' | 'items' | 'species' | 'communities'

type ContextItem = CharacterResponse | LocationResponse | ItemResponse | SpeciesResponse | CommunityResponse

interface ContextSelectorProps {
  onItemSelected?: (item: ContextItem | null) => void
}

export function ContextSelector({ onItemSelected }: ContextSelectorProps = {}) {
  const [activeTab, setActiveTab] = useState<TabType>('characters')
  const [characters, setCharacters] = useState<CharacterResponse[]>([])
  const [locations, setLocations] = useState<LocationResponse[]>([])
  const [items, setItems] = useState<ItemResponse[]>([])
  const [species, setSpecies] = useState<SpeciesResponse[]>([])
  const [communities, setCommunities] = useState<CommunityResponse[]>([])
  const [selectedDetail, setSelectedDetail] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const { 
    selections, 
    toggleCharacter, 
    toggleLocation, 
    toggleItem, 
    toggleSpecies,
    toggleCommunity,
    clearSelections 
  } = useContextStore()

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const [charsRes, locsRes, itemsRes, speciesRes, communitiesRes] = await Promise.all([
        contextAPI.listCharacters(),
        contextAPI.listLocations(),
        contextAPI.listItems(),
        contextAPI.listSpecies(),
        contextAPI.listCommunities(),
      ])
      setCharacters(charsRes.characters)
      setLocations(locsRes.locations)
      setItems(itemsRes.items)
      setSpecies(speciesRes.species)
      setCommunities(communitiesRes.communities)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }

  const handleItemClick = async (name: string) => {
    try {
      let item: CharacterResponse | LocationResponse | ItemResponse | SpeciesResponse | CommunityResponse | null = null
      if (activeTab === 'characters') {
        item = await contextAPI.getCharacter(name)
      } else if (activeTab === 'locations') {
        item = await contextAPI.getLocation(name)
      } else if (activeTab === 'items') {
        item = await contextAPI.getItem(name)
      } else if (activeTab === 'species') {
        item = await contextAPI.getSpecies(name)
      } else if (activeTab === 'communities') {
        item = await contextAPI.getCommunity(name)
      }

      if (item && selectedDetail === name) {
        setSelectedDetail(null)
        onItemSelected?.(null)
      } else if (item) {
        setSelectedDetail(name)
        onItemSelected?.(item)
      }
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const handleItemToggle = (name: string) => {
    if (activeTab === 'characters') {
      toggleCharacter(name)
    } else if (activeTab === 'locations') {
      toggleLocation(name)
    } else if (activeTab === 'items') {
      toggleItem(name)
    } else if (activeTab === 'species') {
      toggleSpecies(name)
    } else if (activeTab === 'communities') {
      toggleCommunity(name)
    }
    if (selectedDetail === name) {
      setSelectedDetail(null)
      onItemSelected?.(null)
    }
  }

  const getCurrentItems = (): (CharacterResponse | LocationResponse | ItemResponse | SpeciesResponse | CommunityResponse)[] => {
    if (activeTab === 'characters') return characters
    if (activeTab === 'locations') return locations
    if (activeTab === 'items') return items
    if (activeTab === 'species') return species
    if (activeTab === 'communities') return communities
    return []
  }

  const getSelectedItems = (): string[] => {
    if (activeTab === 'characters') return selections.characters
    if (activeTab === 'locations') return selections.locations
    if (activeTab === 'items') return selections.items
    if (activeTab === 'species') return selections.species
    if (activeTab === 'communities') return selections.communities
    return []
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ display: 'flex', borderBottom: `1px solid ${theme.border.primary}` }}>
        <button
          onClick={() => {
            setActiveTab('characters')
            setSelectedDetail(null)
            onItemSelected?.(null)
          }}
          style={{
            flex: 1,
            padding: '0.75rem',
            border: 'none',
            borderBottom: activeTab === 'characters' ? `2px solid ${theme.button.primary.background}` : 'none',
            backgroundColor: activeTab === 'characters' ? theme.background.tertiary : 'transparent',
            color: theme.text.primary,
            cursor: 'pointer',
            fontWeight: activeTab === 'characters' ? 'bold' : 'normal',
          }}
        >
          Personnages ({characters.length})
        </button>
        <button
          onClick={() => {
            setActiveTab('locations')
            setSelectedDetail(null)
            onItemSelected?.(null)
          }}
          style={{
            flex: 1,
            padding: '0.75rem',
            border: 'none',
            borderBottom: activeTab === 'locations' ? `2px solid ${theme.button.primary.background}` : 'none',
            backgroundColor: activeTab === 'locations' ? theme.background.tertiary : 'transparent',
            color: theme.text.primary,
            cursor: 'pointer',
            fontWeight: activeTab === 'locations' ? 'bold' : 'normal',
          }}
        >
          Lieux ({locations.length})
        </button>
        <button
          onClick={() => {
            setActiveTab('items')
            setSelectedDetail(null)
            onItemSelected?.(null)
          }}
          style={{
            flex: 1,
            padding: '0.75rem',
            border: 'none',
            borderBottom: activeTab === 'items' ? `2px solid ${theme.button.primary.background}` : 'none',
            backgroundColor: activeTab === 'items' ? theme.background.tertiary : 'transparent',
            color: theme.text.primary,
            cursor: 'pointer',
            fontWeight: activeTab === 'items' ? 'bold' : 'normal',
          }}
        >
          Objets ({items.length})
        </button>
        <button
          onClick={() => {
            setActiveTab('species')
            setSelectedDetail(null)
            onItemSelected?.(null)
          }}
          style={{
            flex: 1,
            padding: '0.75rem',
            border: 'none',
            borderBottom: activeTab === 'species' ? `2px solid ${theme.button.primary.background}` : 'none',
            backgroundColor: activeTab === 'species' ? theme.background.tertiary : 'transparent',
            color: theme.text.primary,
            cursor: 'pointer',
            fontWeight: activeTab === 'species' ? 'bold' : 'normal',
          }}
        >
          Espèces ({species.length})
        </button>
        <button
          onClick={() => {
            setActiveTab('communities')
            setSelectedDetail(null)
            onItemSelected?.(null)
          }}
          style={{
            flex: 1,
            padding: '0.75rem',
            border: 'none',
            borderBottom: activeTab === 'communities' ? `2px solid ${theme.button.primary.background}` : 'none',
            backgroundColor: activeTab === 'communities' ? theme.background.tertiary : 'transparent',
            color: theme.text.primary,
            cursor: 'pointer',
            fontWeight: activeTab === 'communities' ? 'bold' : 'normal',
          }}
        >
          Communautés ({communities.length})
        </button>
      </div>

      {error && (
        <div style={{ 
          padding: '0.5rem', 
          backgroundColor: theme.state.error.background, 
          color: theme.state.error.color, 
          fontSize: '0.9rem' 
        }}>
          {error}
        </div>
      )}

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div style={{ flex: 1, overflow: 'hidden' }}>
          <ContextList
            items={getCurrentItems()}
            selectedItems={getSelectedItems()}
            onItemClick={handleItemClick}
            onItemToggle={handleItemToggle}
            selectedDetail={selectedDetail}
            onSelectDetail={setSelectedDetail}
            isLoading={isLoading}
          />
        </div>
        <SelectedContextSummary selections={selections} onClear={clearSelections} />
      </div>
    </div>
  )
}

