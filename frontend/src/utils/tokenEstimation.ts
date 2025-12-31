/**
 * Utilitaires pour estimer le nombre de tokens dans un texte.
 * 
 * Cette estimation est approximative et basée sur des règles simples :
 * - Pour GPT, en moyenne 1 token ≈ 4 caractères ou 0.75 mots
 * - Utilise une estimation conservative pour être proche de tiktoken
 */

/**
 * Estime le nombre de tokens dans un texte.
 * 
 * Cette estimation est approximative et basée sur des observations :
 * - Pour les modèles GPT, en moyenne 1 token ≈ 4 caractères
 * - Cette formule donne une estimation proche de tiktoken pour la plupart des textes
 * 
 * @param text Le texte pour lequel estimer les tokens
 * @returns Une estimation du nombre de tokens
 */
export function estimateTokens(text: string): number {
  if (!text || text.length === 0) {
    return 0
  }
  
  // Estimation simple : environ 4 caractères par token en moyenne
  // C'est une approximation qui fonctionne bien pour le français et l'anglais
  const estimated = Math.ceil(text.length / 4)
  
  // Ajustement pour les espaces et ponctuation (réduisent légèrement le ratio)
  // On ajoute un petit facteur pour être plus proche de tiktoken
  return Math.ceil(estimated * 0.9)
}
