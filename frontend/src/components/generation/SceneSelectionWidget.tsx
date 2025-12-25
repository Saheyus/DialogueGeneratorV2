/**
 * Widget pour sélectionner la scène principale (personnages A/B, région, sous-lieu).
 */
import { memo, useCallback, useEffect } from 'react'
import { Select, type SelectOption } from '../shared/Select'
import { FormField } from '../shared/FormField'
import { useSceneSelection } from '../../hooks/useSceneSelection'
import { useGenerationStore } from '../../store/generationStore'
import { theme } from '../../theme'

export const SceneSelectionWidget = memo(function SceneSelectionWidget() {
  const { data, selection, updateSelection, swapCharacters, isLoading } =
    useSceneSelection()
  const { setSceneSelection } = useGenerationStore()

  useEffect(() => {
    setSceneSelection(selection)
  }, [selection, setSceneSelection])

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

  const characterOptions: SelectOption[] = [
    { value: '', label: '(Aucun)' },
    ...data.characters.map((name) => ({ value: name, label: name })),
  ]

  const regionOptions: SelectOption[] = [
    { value: '', label: '(Aucune)' },
    ...data.regions.map((name) => ({ value: name, label: name })),
  ]

  const subLocationOptions: SelectOption[] = [
    { value: '', label: '(Aucun)' },
    ...data.subLocations.map((name) => ({ value: name, label: name })),
  ]

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
          alignItems: 'end',
          marginBottom: '1rem',
        }}
      >
        <FormField label="Personnage A:" style={{ marginBottom: 0 }}>
          <Select
            options={characterOptions}
            value={selection.characterA || ''}
            onChange={(value) => handleCharacterAChange(value)}
            placeholder="Sélectionner..."
            disabled={isLoading}
            allowClear
          />
        </FormField>

        <button
          onClick={swapCharacters}
          disabled={isLoading || !selection.characterA && !selection.characterB}
          title="Échanger Personnage A et Personnage B"
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
            marginBottom: '1.5rem',
          }}
        >
          ⇄
        </button>

        <FormField label="Personnage B:" style={{ marginBottom: 0 }}>
          <Select
            options={characterOptions}
            value={selection.characterB || ''}
            onChange={(value) => handleCharacterBChange(value)}
            placeholder="Sélectionner..."
            disabled={isLoading}
            allowClear
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
          <Select
            options={regionOptions}
            value={selection.sceneRegion || ''}
            onChange={(value) => handleRegionChange(value)}
            placeholder="Sélectionner..."
            disabled={isLoading}
            allowClear
          />
        </FormField>

        <FormField label="Sous-Lieu (optionnel):" style={{ marginBottom: 0 }}>
          <Select
            options={subLocationOptions}
            value={selection.subLocation || ''}
            onChange={(value) => handleSubLocationChange(value)}
            placeholder={
              selection.sceneRegion
                ? 'Sélectionner...'
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

