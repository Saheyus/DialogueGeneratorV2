/**
 * Constantes partagées pour l'application.
 * 
 * IMPORTANT: Ces constantes doivent être synchronisées avec constants.py côté backend.
 */

/**
 * Limites pour les tokens de contexte.
 * 
 * Ces valeurs doivent correspondre à celles définies dans constants.py (Defaults.MAX_CONTEXT_TOKENS, Defaults.MIN_CONTEXT_TOKENS)
 */
export const CONTEXT_TOKENS_LIMITS = {
  /** Minimum autorisé pour le slider (10K) */
  MIN: 10000,
  /** Maximum autorisé pour le slider et l'API (100K) */
  MAX: 100000,
  /** Pas du slider (5K) */
  STEP: 5000,
  /** Valeur par défaut (50K) */
  DEFAULT: 50000,
} as const



