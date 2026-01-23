/**
 * Types spécifiques pour la génération de dialogues.
 */

export interface SceneSelection {
  characterA: string | null
  characterB: string | null
  sceneRegion: string | null
  subLocation: string | null
}

export type DialogueStructureElement = 'PNJ' | 'PJ' | 'Stop' | ''

export type DialogueStructure = [
  DialogueStructureElement,
  DialogueStructureElement,
  DialogueStructureElement,
  DialogueStructureElement,
  DialogueStructureElement,
  DialogueStructureElement
]



