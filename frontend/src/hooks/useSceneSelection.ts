/**
 * Hook personnalisé pour gérer la sélection de scène.
 */
import { useState, useEffect, useCallback } from 'react'
import * as contextAPI from '../api/context'
import type { SceneSelection } from '../types/generation'

export interface SceneSelectionData {
  characters: string[]
  regions: string[]
  subLocations: string[]
}

export interface UseSceneSelectionReturn {
  data: SceneSelectionData
  selection: SceneSelection
  isLoading: boolean
  updateSelection: (updates: Partial<SceneSelection>) => void
  swapCharacters: () => void
}

export function useSceneSelection() {
  const [data, setData] = useState<SceneSelectionData>({
    characters: [],
    regions: [],
    subLocations: [],
  })
  const [selection, setSelection] = useState<SceneSelection>({
    characterA: null,
    characterB: null,
    sceneRegion: null,
    subLocation: null,
  })
  const [isLoading, setIsLoading] = useState(false)

  const loadCharacters = useCallback(async () => {
    try {
      const response = await contextAPI.listCharacters()
      setData((prev) => ({
        ...prev,
        characters: response.characters.map((c) => c.name).sort(),
      }))
    } catch (err) {
      console.error('Erreur lors du chargement des personnages:', err)
    }
  }, [])

  const loadRegions = useCallback(async () => {
    try {
      const response = await contextAPI.listRegions()
      setData((prev) => ({
        ...prev,
        regions: response.regions.sort(),
      }))
    } catch (err) {
      console.error('Erreur lors du chargement des régions:', err)
    }
  }, [])

  const loadSubLocations = useCallback(async (regionName: string) => {
    if (!regionName) {
      setData((prev) => ({ ...prev, subLocations: [] }))
      return
    }

    try {
      const response = await contextAPI.getSubLocations(regionName)
      setData((prev) => ({
        ...prev,
        subLocations: response.sub_locations.sort(),
      }))
    } catch (err) {
      console.error('Erreur lors du chargement des sous-lieux:', err)
      setData((prev) => ({ ...prev, subLocations: [] }))
    }
  }, [])

  useEffect(() => {
    setIsLoading(true)
    Promise.all([loadCharacters(), loadRegions()]).finally(() => {
      setIsLoading(false)
    })
  }, [loadCharacters, loadRegions])

  useEffect(() => {
    if (selection.sceneRegion) {
      loadSubLocations(selection.sceneRegion)
    } else {
      setData((prev) => ({ ...prev, subLocations: [] }))
      setSelection((prev) => ({ ...prev, subLocation: null }))
    }
  }, [selection.sceneRegion, loadSubLocations])

  const updateSelection = useCallback((updates: Partial<SceneSelection>) => {
    setSelection((prev) => ({ ...prev, ...updates }))
  }, [])

  const swapCharacters = useCallback(() => {
    setSelection((prev) => ({
      ...prev,
      characterA: prev.characterB,
      characterB: prev.characterA,
    }))
  }, [])

  return {
    data,
    selection,
    isLoading,
    updateSelection,
    swapCharacters,
  }
}

