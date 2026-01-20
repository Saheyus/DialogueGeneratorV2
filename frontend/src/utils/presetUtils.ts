/**
 * Utilitaires pour la gestion des presets
 */
import type { Preset } from '../types/preset'

/**
 * Filtre les références obsolètes d'un preset.
 * 
 * Supprime les personnages et lieux obsolètes de la configuration du preset
 * tout en préservant les autres champs (region, subLocation, instructions, etc.).
 * 
 * @param preset - Preset à filtrer
 * @param obsoleteRefs - Liste des références obsolètes (noms de personnages/lieux)
 * @returns Preset filtré avec références obsolètes supprimées
 */
export function filterObsoleteReferences(preset: Preset, obsoleteRefs: string[]): Preset {
  const filteredPreset: Preset = { ...preset }
  filteredPreset.configuration = {
    ...preset.configuration,
    characters: preset.configuration.characters.filter(c => !obsoleteRefs.includes(c)),
    locations: preset.configuration.locations.filter(l => !obsoleteRefs.includes(l))
  }
  return filteredPreset
}
