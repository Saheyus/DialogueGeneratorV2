/**
 * Utilitaires pour calculer des hashs côté client.
 * 
 * Utilisé pour le cache des prompts afin d'éviter les appels API redondants.
 */

/**
 * Interface pour les paramètres d'entrée du prompt.
 * 
 * Doit correspondre exactement aux paramètres envoyés à l'API previewPrompt.
 */
export interface PromptStateParams {
  user_instructions: string
  context_selections: any
  npc_speaker_id?: string
  max_context_tokens: number
  system_prompt_override?: string
  author_profile?: string
  max_choices?: number
  choices_mode: 'free' | 'capped'
  narrative_tags?: string[]
  vocabulary_config?: Record<string, string>
  include_narrative_guides: boolean
  previous_dialogue_preview?: string
  field_configs?: Record<string, string[]>
  organization_mode?: string
  in_game_flags?: any[]
}

/**
 * Calcule un hash SHA-256 d'un objet pour comparaison.
 * 
 * Les objets sont triés par clé pour garantir un hash cohérent
 * indépendamment de l'ordre des propriétés.
 * 
 * @param params - Paramètres à hasher
 * @returns Hash hexadécimal SHA-256
 */
export async function computeStateHash(params: PromptStateParams): Promise<string> {
  // Normaliser les paramètres pour garantir un hash cohérent
  const normalized = normalizeParams(params)
  
  // Convertir en JSON stringifié (ordre garanti par normalizeParams)
  const jsonString = JSON.stringify(normalized)
  
  // Calculer SHA-256 via Web Crypto API
  const encoder = new TextEncoder()
  const data = encoder.encode(jsonString)
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)
  
  // Convertir en hexadécimal
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
  
  return hashHex
}

/**
 * Normalise les paramètres pour garantir un hash cohérent.
 * 
 * - Trie les clés des objets
 * - Normalise les valeurs undefined/null
 * - Trie les tableaux pour garantir l'ordre
 * 
 * @param params - Paramètres à normaliser
 * @returns Objet normalisé
 */
function normalizeParams(params: PromptStateParams): Record<string, any> {
  const normalized: Record<string, any> = {}
  
  // Trier les clés pour garantir l'ordre
  const sortedKeys = Object.keys(params).sort()
  
  for (const key of sortedKeys) {
    const value = params[key as keyof PromptStateParams]
    
    // Ignorer les valeurs undefined (mais garder null)
    if (value === undefined) {
      continue
    }
    
    // Normaliser selon le type
    if (value === null) {
      normalized[key] = null
    } else if (Array.isArray(value)) {
      // Trier les tableaux pour garantir l'ordre (sauf si c'est un tableau d'objets)
      if (value.length > 0 && typeof value[0] === 'object' && value[0] !== null) {
        // Tableau d'objets: normaliser chaque objet et trier par JSON stringifié
        normalized[key] = value
          .map(item => normalizeValue(item))
          .sort((a, b) => JSON.stringify(a).localeCompare(JSON.stringify(b)))
      } else {
        // Tableau de primitives: trier
        normalized[key] = [...value].sort()
      }
    } else if (typeof value === 'object') {
      // Objet: normaliser récursivement
      normalized[key] = normalizeValue(value)
    } else {
      // Primitive: garder tel quel
      normalized[key] = value
    }
  }
  
  return normalized
}

/**
 * Normalise une valeur (objet ou primitive).
 * 
 * @param value - Valeur à normaliser
 * @returns Valeur normalisée
 */
function normalizeValue(value: any): any {
  if (value === null || value === undefined) {
    return value
  }
  
  if (Array.isArray(value)) {
    return value.map(item => normalizeValue(item))
  }
  
  if (typeof value === 'object') {
    const normalized: Record<string, any> = {}
    const sortedKeys = Object.keys(value).sort()
    for (const key of sortedKeys) {
      normalized[key] = normalizeValue(value[key])
    }
    return normalized
  }
  
  return value
}
