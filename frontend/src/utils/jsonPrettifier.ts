/**
 * Utilitaires pour détecter et prettifier le JSON dans une chaîne.
 */

/**
 * Détecte et prettifie le JSON dans une chaîne de texte.
 * 
 * @param text - Le texte à analyser
 * @returns Le texte avec le JSON prettifié, ou le texte original si aucun JSON valide n'est trouvé
 */
export function prettifyJsonInText(text: string): string {
  // Patterns pour détecter des blocs JSON potentiels
  // Chercher des objets JSON { ... } ou des tableaux JSON [ ... ]
  const jsonObjectPattern = /\{[\s\S]*?\}/g
  const jsonArrayPattern = /\[[\s\S]*?\]/g
  
  let result = text
  let hasChanges = false
  
  // Fonction pour prettifier un match JSON
  const prettifyMatch = (match: string): string => {
    try {
      const parsed = JSON.parse(match)
      const prettified = JSON.stringify(parsed, null, 2)
      // Ne remplacer que si le JSON prettifié est différent (évite les faux positifs)
      if (prettified !== match.trim()) {
        hasChanges = true
        return prettified
      }
    } catch {
      // Ce n'est pas du JSON valide, on garde l'original
    }
    return match
  }
  
  // Essayer d'abord les objets JSON (plus communs)
  result = result.replace(jsonObjectPattern, (match) => {
    // Ignorer les matches trop courts (probablement pas du JSON)
    if (match.trim().length < 10) return match
    const prettified = prettifyMatch(match)
    if (prettified !== match) {
      hasChanges = true
    }
    return prettified
  })
  
  // Ensuite les tableaux JSON
  result = result.replace(jsonArrayPattern, (match) => {
    if (match.trim().length < 10) return match
    const prettified = prettifyMatch(match)
    if (prettified !== match) {
      hasChanges = true
    }
    return prettified
  })
  
  return result
}

/**
 * Vérifie si une chaîne contient du JSON valide.
 * 
 * @param text - Le texte à vérifier
 * @returns true si le texte contient du JSON valide
 */
export function hasJsonContent(text: string): boolean {
  try {
    // Essayer de parser le texte entier
    JSON.parse(text)
    return true
  } catch {
    // Essayer de trouver des blocs JSON dans le texte
    const jsonObjectPattern = /\{[\s\S]{10,}?\}/g
    const jsonArrayPattern = /\[[\s\S]{10,}?\]/g
    
    const objectMatches = text.match(jsonObjectPattern)
    const arrayMatches = text.match(jsonArrayPattern)
    
    if (objectMatches) {
      for (const match of objectMatches) {
        try {
          JSON.parse(match)
          return true
        } catch {
          // Continuer
        }
      }
    }
    
    if (arrayMatches) {
      for (const match of arrayMatches) {
        try {
          JSON.parse(match)
          return true
        } catch {
          // Continuer
        }
      }
    }
    
    return false
  }
}

