/**
 * Hook personnalisé pour gérer la structure de dialogue.
 */
import { useState, useCallback } from 'react'
import type { DialogueStructure, DialogueStructureElement } from '../types/generation'

const DEFAULT_STRUCTURE: DialogueStructure = ['PNJ', 'PJ', 'Stop', '', '', '']

export function useDialogueStructure(
  initialStructure: DialogueStructure = DEFAULT_STRUCTURE
) {
  const [structure, setStructure] = useState<DialogueStructure>(initialStructure)

  const updateElement = useCallback(
    (index: number, value: DialogueStructureElement) => {
      setStructure((prev) => {
        const newStructure = [...prev] as DialogueStructure
        newStructure[index] = value
        return newStructure
      })
    },
    []
  )

  const reset = useCallback(() => {
    setStructure(DEFAULT_STRUCTURE)
  }, [])

  const getStructureDescription = useCallback((): string => {
    // Filtrer les éléments vides et s'arrêter au premier "Stop"
    const filtered: DialogueStructureElement[] = []
    for (const element of structure) {
      if (element === 'Stop') {
        filtered.push(element)
        break
      } else if (element !== '') {
        filtered.push(element)
      }
    }

    if (filtered.length === 0) {
      return 'Structure libre (pas de contrainte spécifique)'
    }

    const descriptions: Record<string, string> = {
      PNJ: 'le personnage B parle directement',
      PJ: 'le personnage A (joueur) fait un choix parmi plusieurs options',
      Stop: 'fin de l\'interaction',
    }

    const parts = filtered
      .filter((el) => el in descriptions)
      .map((el, i) => `${i + 1}. ${descriptions[el]}`)

    return 'Structure requise:\n' + parts.join('\n')
  }, [structure])

  const validate = useCallback((): boolean => {
    // Doit avoir au moins un élément avant Stop
    let hasElementBeforeStop = false
    for (const element of structure) {
      if (element === 'Stop') {
        return hasElementBeforeStop
      }
      if (element !== '') {
        hasElementBeforeStop = true
      }
    }
    return hasElementBeforeStop || structure.every((el) => el === '')
  }, [structure])

  return {
    structure,
    updateElement,
    reset,
    getStructureDescription,
    validate,
    setStructure: setStructure as (structure: DialogueStructure) => void,
  }
}



