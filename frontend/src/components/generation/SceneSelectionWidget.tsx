/**
 * Widget pour sélectionner la scène principale (personnages A/B, région, sous-lieu).
 */
import { memo, useCallback, useEffect, useState } from 'react'
import { Combobox, type ComboboxOption } from '../shared/Combobox'
import { FormField } from '../shared/FormField'
import { useSceneSelection } from '../../hooks/useSceneSelection'
import { useGenerationStore } from '../../store/generationStore'
import { theme } from '../../theme'

export const SceneSelectionWidget = memo(function SceneSelectionWidget() {
  const { data, selection, updateSelection, swapCharacters, isLoading } =
    useSceneSelection()
  const { setSceneSelection } = useGenerationStore()
  const [recentCharacters, setRecentCharacters] = useState<string[]>([])
  const [recentRegions, setRecentRegions] = useState<string[]>([])

  useEffect(() => {
    setSceneSelection(selection)
  }, [selection, setSceneSelection])

  // Raccourci clavier pour swap (Alt+S)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.altKey && e.key === 's') {
        e.preventDefault()
        if (selection.characterA || selection.characterB) {
          swapCharacters()
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [selection, swapCharacters])

  const handleCharacterAChange = useCallback(
    (value: string | null) => {
      updateSelection({ characterA: value })
    },
    [updateSelection]
  )

  const handleCharacterBChange = useCallback(
    (value: string | null) => {
      updateSelection({ characterB: value })
    },
    [updateSelection]
  )

  const handleRegionChange = useCallback(
    (value: string | null) => {
      updateSelection({ sceneRegion: value, subLocation: null })
    },
    [updateSelection]
  )

  const handleSubLocationChange = useCallback(
    (value: string | null) => {
      updateSelection({ subLocation: value })
    },
    [updateSelection]
  )

  const characterOptions: ComboboxOption[] = data.characters.map((name) => ({
    value: name,
    label: name,
  }))

  const regionOptions: ComboboxOption[] = data.regions.map((name) => ({
    value: name,
    label: name,
  }))

  const subLocationOptions: ComboboxOption[] = data.subLocations.map((name) => ({
    value: name,
    label: name,
  }))

  const hasContext = selection.characterA || selection.characterB || selection.sceneRegion

  if (!hasContext && !isLoading) {
    return (
      <div
        style={{
          padding: '2rem',
          border: `1px dashed ${theme.border.primary}`,
          borderRadius: '4px',
          backgroundColor: theme.background.tertiary,
          marginBottom: '1rem',
          textAlign: 'center',
        }}
      >
        <div style={{ color: theme.text.secondary, marginBottom: '1rem' }}>
          <strong style={{ color: theme.text.primary, display: 'block', marginBottom: '0.5rem' }}>
            Aucun contexte sélectionné
          </strong>
          Choisis PJ/PNJ + région, ou charge une interaction existante à droite
        </div>
      </div>
    )
  }

  return (
    <div
      style={{
        padding: '1rem',
        border: `1px solid ${theme.border.primary}`,
        borderRadius: '4px',
        backgroundColor: theme.background.panel,
        marginBottom: '1rem',
      }}
    >
      <h3
        style={{
          marginTop: 0,
          marginBottom: '0.75rem',
          fontSize: '1rem',
          fontWeight: 'bold',
          color: theme.text.primary,
        }}
      >
        Scène Principale
      </h3>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr auto 1fr',
          gap: '0.5rem',
          alignItems: 'center',
          marginBottom: '1rem',
        }}
      >
        <FormField label="PJ:" style={{ marginBottom: 0 }}>
          <Combobox
            options={characterOptions}
            value={selection.characterA}
            onChange={handleCharacterAChange}
            placeholder="(Aucun) - Rechercher..."
            disabled={isLoading}
            allowClear
            recentlyUsed={recentCharacters}
            onRecentUpdate={setRecentCharacters}
          />
        </FormField>

        <button
          onClick={swapCharacters}
          disabled={isLoading || (!selection.characterA && !selection.characterB)}
          title="Échanger PJ et PNJ (Alt+S)"
          style={{
            width: '32px',
            height: '32px',
            padding: 0,
            border: `1px solid ${theme.border.primary}`,
            borderRadius: '4px',
            backgroundColor: theme.button.default.background,
            color: theme.button.default.color,
            cursor:
              isLoading || (!selection.characterA && !selection.characterB)
                ? 'not-allowed'
                : 'pointer',
            opacity:
              isLoading || (!selection.characterA && !selection.characterB)
                ? 0.5
                : 1,
            fontSize: '1.2rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            alignSelf: 'center',
          }}
        >
          ⇄
        </button>

        <FormField label="PNJ:" style={{ marginBottom: 0 }}>
          <Combobox
            options={characterOptions}
            value={selection.characterB}
            onChange={handleCharacterBChange}
            placeholder="(Aucun) - Rechercher..."
            disabled={isLoading}
            allowClear
            recentlyUsed={recentCharacters}
            onRecentUpdate={setRecentCharacters}
          />
        </FormField>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '1rem',
        }}
      >
        <FormField label="Région de la Scène:" style={{ marginBottom: 0 }}>
          <Combobox
            options={regionOptions}
            value={selection.sceneRegion}
            onChange={handleRegionChange}
            placeholder="(Aucune) - Rechercher..."
            disabled={isLoading}
            allowClear
            recentlyUsed={recentRegions}
            onRecentUpdate={setRecentRegions}
          />
        </FormField>

        <FormField label="Sous-Lieu (optionnel):" style={{ marginBottom: 0 }}>
          <Combobox
            options={subLocationOptions}
            value={selection.subLocation}
            onChange={handleSubLocationChange}
            placeholder={
              selection.sceneRegion
                ? '(Aucun) - Rechercher...'
                : 'Sélectionnez d\'abord une région'
            }
            disabled={isLoading || !selection.sceneRegion}
            allowClear
          />
        </FormField>
      </div>
    </div>
  )
})

