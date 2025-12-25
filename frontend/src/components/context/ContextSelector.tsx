/**
 * Composant principal de sélection de contexte avec onglets pour personnages, lieux et objets.
 */
import { useState, useEffect } from 'react'
import * as contextAPI from '../../api/context'
import type { CharacterResponse, LocationResponse, ItemResponse } from '../../types/api'
import { ContextList } from './ContextList'
import { ContextDetail } from './ContextDetail'
import { SelectedContextSummary } from './SelectedContextSummary'
import { useContextStore } from '../../store/contextStore'
import { getErrorMessage } from '../../types/errors'
import { theme } from '../../theme'

type TabType = 'characters' | 'locations' | 'items'

export function ContextSelector() {
  const [activeTab, setActiveTab] = useState<TabType>('characters')
  const [characters, setCharacters] = useState<CharacterResponse[]>([])
  const [locations, setLocations] = useState<LocationResponse[]>([])
  const [items, setItems] = useState<ItemResponse[]>([])
  const [selectedDetail, setSelectedDetail] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const { selections, toggleCharacter, toggleLocation, toggleItem, clearSelections } = useContextStore()

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const [charsRes, locsRes, itemsRes] = await Promise.all([
        contextAPI.listCharacters(),
        contextAPI.listLocations(),
        contextAPI.listItems(),
      ])
      setCharacters(charsRes.characters)
      setLocations(locsRes.locations)
      setItems(itemsRes.items)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }

  const handleItemClick = async (name: string) => {
    try {
      let item: CharacterResponse | LocationResponse | ItemResponse | null = null
      if (activeTab === 'characters') {
        item = await contextAPI.getCharacter(name)
      } else if (activeTab === 'locations') {
        item = await contextAPI.getLocation(name)
      } else if (activeTab === 'items') {
        item = await contextAPI.getItem(name)
      }

      if (item && selectedDetail === name) {
        setSelectedDetail(null)
      } else if (item) {
        setSelectedDetail(name)
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
    }
    if (selectedDetail === name) {
      setSelectedDetail(null)
    }
  }

  const getCurrentItems = (): (CharacterResponse | LocationResponse | ItemResponse)[] => {
    if (activeTab === 'characters') return characters
    if (activeTab === 'locations') return locations
    return items
  }

  const getSelectedItems = (): string[] => {
    if (activeTab === 'characters') return selections.characters
    if (activeTab === 'locations') return selections.locations
    return selections.items
  }

  const getSelectedDetailItem = ():
    | CharacterResponse
    | LocationResponse
    | ItemResponse
    | null => {
    if (!selectedDetail) return null
    const allItems = [...characters, ...locations, ...items]
    return allItems.find((item) => item.name === selectedDetail) || null
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ display: 'flex', borderBottom: `1px solid ${theme.border.primary}` }}>
        <button
          onClick={() => {
            setActiveTab('characters')
            setSelectedDetail(null)
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

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        <div style={{ 
          width: '50%', 
          borderRight: `1px solid ${theme.border.primary}`, 
          display: 'flex', 
          flexDirection: 'column' 
        }}>
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
        <div style={{ width: '50%', display: 'flex', flexDirection: 'column' }}>
          <div style={{ flex: 1, overflowY: 'auto' }}>
            <ContextDetail item={getSelectedDetailItem()} />
          </div>
          <SelectedContextSummary selections={selections} onClear={clearSelections} />
        </div>
      </div>
    </div>
  )
}

