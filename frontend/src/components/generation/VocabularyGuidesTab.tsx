/**
 * Onglet pour configurer le vocabulaire Alteir et les guides narratifs.
 */
import { useState, useEffect } from 'react'
import { useVocabularyStore, type ImportanceLevel } from '../../store/vocabularyStore'
import { theme } from '../../theme'

const IMPORTANCE_LEVELS: ImportanceLevel[] = [
  'Majeur',
  'Important',
  'Modéré',
  'Secondaire',
  'Mineur',
  'Anecdotique',
]

export function VocabularyGuidesTab() {
  const {
    vocabularyMinImportance,
    includeNarrativeGuides,
    vocabularyTerms,
    totalTerms,
    vocabularyStats,
    lastSyncTime,
    isSyncing,
    error,
    setMinImportance,
    toggleGuides,
    loadVocabulary,
    loadNarrativeGuides,
    syncFromNotion,
    loadStats,
    clearError,
  } = useVocabularyStore()

  const [isLoading, setIsLoading] = useState(false)

  // Charger les données au montage
  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true)
      try {
        await Promise.all([
          loadVocabulary(),
          loadNarrativeGuides(),
          loadStats(),
        ])
      } catch (err) {
        console.error('Erreur lors du chargement initial:', err)
      } finally {
        setIsLoading(false)
      }
    }
    loadData()
  }, [loadVocabulary, loadNarrativeGuides, loadStats])

  // Calculer le nombre de termes selon le niveau sélectionné
  const getFilteredCount = (level: ImportanceLevel | null): number => {
    if (!level || !vocabularyStats) return totalTerms

    const order: Record<ImportanceLevel, number> = {
      Majeur: 1,
      Important: 2,
      Modéré: 3,
      Secondaire: 4,
      Mineur: 5,
      Anecdotique: 6,
    }

    const levelOrder = order[level]
    let count = 0
    for (const [importance, num] of Object.entries(order)) {
      if (num <= levelOrder) {
        count += vocabularyStats.by_importance[importance] || 0
      }
    }
    return count
  }

  const handleSync = async () => {
    await syncFromNotion()
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Vocabulaire Alteir */}
      <div
        style={{
          padding: '1rem',
          border: `1px solid ${theme.border.primary}`,
          borderRadius: '8px',
          backgroundColor: theme.background.secondary,
        }}
      >
        <h3 style={{ margin: '0 0 1rem 0', color: theme.text.primary }}>
          Vocabulaire Alteir
        </h3>

        {/* Sélecteur de niveau d'importance */}
        <div style={{ marginBottom: '1rem' }}>
          <label
            style={{
              display: 'block',
              marginBottom: '0.5rem',
              color: theme.text.primary,
              fontWeight: 'bold',
            }}
          >
            Niveau d'importance minimum
          </label>
          <select
            value={vocabularyMinImportance || ''}
            onChange={(e) =>
              setMinImportance(
                (e.target.value as ImportanceLevel) || null
              )
            }
            style={{
              padding: '0.5rem',
              border: `1px solid ${theme.border.primary}`,
              borderRadius: '4px',
              backgroundColor: theme.input.background,
              color: theme.input.color,
              width: '100%',
              maxWidth: '300px',
            }}
          >
            <option value="">Tous les termes</option>
            {IMPORTANCE_LEVELS.map((level) => (
              <option key={level} value={level}>
                {level}
              </option>
            ))}
          </select>
          {vocabularyMinImportance && (
            <p
              style={{
                margin: '0.5rem 0 0 0',
                color: theme.text.secondary,
                fontSize: '0.9rem',
              }}
            >
              {getFilteredCount(vocabularyMinImportance)} terme(s) seront inclus
              (niveau {vocabularyMinImportance} + tous les niveaux plus
              importants)
            </p>
          )}
        </div>

        {/* Statistiques */}
        {vocabularyStats && (
          <div
            style={{
              marginTop: '1rem',
              padding: '0.75rem',
              backgroundColor: theme.background.panel,
              borderRadius: '4px',
              fontSize: '0.9rem',
            }}
          >
            <strong style={{ color: theme.text.primary }}>
              Statistiques :
            </strong>
            <ul style={{ margin: '0.5rem 0', paddingLeft: '1.5rem' }}>
              <li>Total : {totalTerms} termes</li>
              {Object.entries(vocabularyStats.by_importance).map(
                ([importance, count]) => (
                  <li key={importance}>
                    {importance} : {count} terme(s)
                  </li>
                )
              )}
            </ul>
          </div>
        )}

        {/* Bouton de synchronisation */}
        <div style={{ marginTop: '1rem' }}>
          <button
            onClick={handleSync}
            disabled={isSyncing || isLoading}
            style={{
              padding: '0.5rem 1rem',
              border: 'none',
              borderRadius: '4px',
              backgroundColor: isSyncing
                ? theme.button.default.background
                : theme.button.primary.background,
              color: theme.button.primary.color,
              cursor: isSyncing ? 'not-allowed' : 'pointer',
              opacity: isSyncing ? 0.6 : 1,
            }}
          >
            {isSyncing ? 'Synchronisation...' : 'Synchroniser depuis Notion'}
          </button>
          {lastSyncTime && (
            <p
              style={{
                margin: '0.5rem 0 0 0',
                color: theme.text.secondary,
                fontSize: '0.85rem',
              }}
            >
              Dernière synchronisation :{' '}
              {new Date(lastSyncTime).toLocaleString('fr-FR')}
            </p>
          )}
        </div>
      </div>

      {/* Guides narratifs */}
      <div
        style={{
          padding: '1rem',
          border: `1px solid ${theme.border.primary}`,
          borderRadius: '8px',
          backgroundColor: theme.background.secondary,
        }}
      >
        <h3 style={{ margin: '0 0 1rem 0', color: theme.text.primary }}>
          Guides narratifs
        </h3>

        <div style={{ marginBottom: '1rem' }}>
          <label
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              cursor: 'pointer',
            }}
          >
            <input
              type="checkbox"
              checked={includeNarrativeGuides}
              onChange={toggleGuides}
              style={{
                width: '1.2rem',
                height: '1.2rem',
                cursor: 'pointer',
              }}
            />
            <span style={{ color: theme.text.primary }}>
              Inclure les guides narratifs dans le prompt système
            </span>
          </label>
          <p
            style={{
              margin: '0.5rem 0 0 1.7rem',
              color: theme.text.secondary,
              fontSize: '0.9rem',
            }}
          >
            Les guides des dialogues et de narration seront injectés dans le
            prompt pour guider la génération.
          </p>
        </div>

        {/* Informations sur les guides */}
        {includeNarrativeGuides && (
          <div
            style={{
              marginTop: '1rem',
              padding: '0.75rem',
              backgroundColor: theme.background.panel,
              borderRadius: '4px',
              fontSize: '0.9rem',
            }}
          >
            <strong style={{ color: theme.text.primary }}>
              Guides disponibles :
            </strong>
            <ul style={{ margin: '0.5rem 0', paddingLeft: '1.5rem' }}>
              <li>Guide des dialogues</li>
              <li>Guide de narration</li>
            </ul>
          </div>
        )}
      </div>

      {/* Message d'erreur */}
      {error && (
        <div
          style={{
            padding: '0.75rem',
            backgroundColor: theme.error.background || '#fee',
            color: theme.error.color || '#c00',
            borderRadius: '4px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <span>{error}</span>
          <button
            onClick={clearError}
            style={{
              background: 'none',
              border: 'none',
              color: theme.error.color || '#c00',
              cursor: 'pointer',
              fontSize: '1.2rem',
              padding: '0 0.5rem',
            }}
          >
            ×
          </button>
        </div>
      )}

      {/* Indicateur de chargement */}
      {isLoading && (
        <div
          style={{
            padding: '1rem',
            textAlign: 'center',
            color: theme.text.secondary,
          }}
        >
          Chargement...
        </div>
      )}
    </div>
  )
}

