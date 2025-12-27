/**
 * Hook personnalisé pour gérer la sélection de scène.
 */
import { useState, useEffect, useCallback } from 'react'
import * as contextAPI from '../api/context'
import type { SceneSelection } from '../types/generation'
import { useContextStore } from '../store/contextStore'

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
  const contextSelections = useContextStore((state) => state.selections)
  const contextRegion = useContextStore((state) => state.selectedRegion)
  const contextSubLocations = useContextStore((state) => state.selectedSubLocations)
  const toggleCharacter = useContextStore((state) => state.toggleCharacter)
  const setRegion = useContextStore((state) => state.setRegion)
  const toggleSubLocation = useContextStore((state) => state.toggleSubLocation)
  
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

  // Synchronisation avec contextStore : mapper les sélections de contexte vers la sélection de scène
  useEffect(() => {
    setSelection((prevSelection) => {
      // Ne synchroniser que si la sélection de scène est vide (pour éviter d'écraser les sélections manuelles)
      const hasSceneSelection = prevSelection.characterA || prevSelection.characterB || prevSelection.sceneRegion
      
      if (hasSceneSelection) {
        return prevSelection
      }
      
      // Mapper les personnages : les 2 premiers deviennent characterA et characterB
      const characterA = contextSelections.characters[0] || null
      const characterB = contextSelections.characters[1] || null
      
      // Mapper les lieux : le premier lieu devient sceneRegion ou subLocation
      let sceneRegion: string | null = null
      let subLocation: string | null = null
      
      // Si une région est sélectionnée dans contextStore, l'utiliser
      if (contextRegion) {
        sceneRegion = contextRegion
        // Si des sous-lieux sont sélectionnés, utiliser le premier
        if (contextSubLocations.length > 0) {
          subLocation = contextSubLocations[0]
        }
      } else if (contextSelections.locations.length > 0) {
        // Sinon, utiliser le premier lieu de la liste
        // On suppose que c'est une région (pas un sous-lieu)
        sceneRegion = contextSelections.locations[0]
      }
      
      // Mettre à jour seulement si quelque chose a changé
      if (
        characterA !== prevSelection.characterA ||
        characterB !== prevSelection.characterB ||
        sceneRegion !== prevSelection.sceneRegion ||
        subLocation !== prevSelection.subLocation
      ) {
        return {
          characterA,
          characterB,
          sceneRegion,
          subLocation,
        }
      }
      
      return prevSelection
    })
  }, [contextSelections, contextRegion, contextSubLocations])

  // Synchronisation inverse : mettre à jour contextStore quand sceneSelection change
  useEffect(() => {
    // Ajouter characterA et characterB aux sélections de personnages s'ils ne sont pas déjà présents
    if (selection.characterA && !contextSelections.characters.includes(selection.characterA)) {
      toggleCharacter(selection.characterA)
    }
    if (selection.characterB && !contextSelections.characters.includes(selection.characterB)) {
      toggleCharacter(selection.characterB)
    }
    
    // Mettre à jour la région si elle change
    if (selection.sceneRegion !== contextRegion) {
      setRegion(selection.sceneRegion)
    }
    
    // Mettre à jour le sous-lieu si il change et que la région est définie
    if (selection.subLocation && selection.sceneRegion && !contextSubLocations.includes(selection.subLocation)) {
      toggleSubLocation(selection.subLocation)
    }
  }, [selection.characterA, selection.characterB, selection.sceneRegion, selection.subLocation, contextSelections.characters, contextRegion, contextSubLocations, toggleCharacter, setRegion, toggleSubLocation])

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

