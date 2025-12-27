/**
 * Modal pour configurer les options de génération (champs de contexte, Unity, organisation, guidance).
 */
import { useState, useCallback, useEffect } from 'react'
import { useContextConfigStore } from '../../store/contextConfigStore'
import { ContextFieldSelector } from './ContextFieldSelector'
import { theme } from '../../theme'
import * as configAPI from '../../api/config'
import { getErrorMessage } from '../../types/errors'

export interface GenerationOptionsModalProps {
  isOpen: boolean
  onClose: () => void
  onApply?: () => void
}

type TabId = 'context' | 'metadata' | 'unity' | 'organization' | 'guidance'

interface Tab {
  id: TabId
  label: string
}

export function GenerationOptionsModal({
  isOpen,
  onClose,
  onApply,
}: GenerationOptionsModalProps) {
  const [activeTab, setActiveTab] = useState<TabId>('context')
  const [unityPath, setUnityPath] = useState('')
  const [isLoadingUnity, setIsLoadingUnity] = useState(false)
  const [isSavingUnity, setIsSavingUnity] = useState(false)
  const [unityError, setUnityError] = useState<string | null>(null)
  const [previewText, setPreviewText] = useState<string>('')
  const [previewTokens, setPreviewTokens] = useState<number>(0)
  const [isLoadingPreview, setIsLoadingPreview] = useState(false)

  const {
    organization,
    setOrganization,
    resetToDefault,
    getPreview,
    detectFields,
    loadSuggestions,
    loadDefaultConfig,
  } = useContextConfigStore()

  // Charger la config par défaut et le chemin Unity au montage
  useEffect(() => {
    if (isOpen) {
      loadDefaultConfig().catch(console.error)
      loadUnityPath()
    }
  }, [isOpen, loadDefaultConfig])

  const loadUnityPath = async () => {
    setIsLoadingUnity(true)
    setUnityError(null)
    try {
      const response = await configAPI.getUnityDialoguesPath()
      setUnityPath(response.path)
    } catch (err) {
      setUnityError(getErrorMessage(err))
    } finally {
      setIsLoadingUnity(false)
    }
  }

  const handleSaveUnity = async () => {
    setIsSavingUnity(true)
    setUnityError(null)
    try {
      await configAPI.setUnityDialoguesPath(unityPath)
      // Pas de fermeture automatique, juste un feedback
    } catch (err) {
      setUnityError(getErrorMessage(err))
    } finally {
      setIsSavingUnity(false)
    }
  }

  const handlePreview = useCallback(async () => {
    setIsLoadingPreview(true)
    try {
      // Utiliser les sélections du store de contexte
      const { selections } = await import('../../store/contextStore').then(m => m.useContextStore.getState())
      
      const selectedElements: Record<string, string[]> = {
        characters: selections.characters,
        locations: selections.locations,
        items: selections.items,
        species: selections.species,
        communities: selections.communities,
      }

      const response = await getPreview(
        selectedElements,
        '', // scene_instruction vide pour la prévisualisation
        70000
      )
      
      setPreviewText(response.preview)
      setPreviewTokens(response.tokens)
    } catch (err) {
      console.error('Erreur lors de la prévisualisation:', err)
    } finally {
      setIsLoadingPreview(false)
    }
  }, [getPreview])

  const handleDetectAll = useCallback(async () => {
    const elementTypes = ['character', 'location', 'item', 'species', 'community']
    // Invalider le cache pour forcer une nouvelle détection
    try {
      await configAPI.invalidateContextFieldsCache()
    } catch (err) {
      console.warn('Impossible d\'invalider le cache:', err)
    }
    
    for (const elementType of elementTypes) {
      try {
        await detectFields(elementType)
        await loadSuggestions(elementType, 'dialogue')
      } catch (err) {
        console.error(`Erreur lors de la détection pour ${elementType}:`, err)
      }
    }
  }, [detectFields, loadSuggestions])

  const tabs: Tab[] = [
    { id: 'context', label: 'Contexte' },
    { id: 'metadata', label: 'Métadonnées' },
    { id: 'unity', label: 'Unity' },
    { id: 'organization', label: 'Organisation' },
    { id: 'guidance', label: 'Guidance' },
  ]

  if (!isOpen) return null

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.7)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: theme.background.panel,
          borderRadius: '8px',
          width: '90%',
          maxWidth: '1200px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: '1.5rem',
            borderBottom: `1px solid ${theme.border.primary}`,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <h2 style={{ margin: 0, color: theme.text.primary }}>Options de Génération</h2>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: theme.text.secondary,
              fontSize: '1.5rem',
              cursor: 'pointer',
              padding: '0.25rem 0.5rem',
            }}
          >
            ×
          </button>
        </div>

        {/* Tabs */}
        <div
          style={{
            display: 'flex',
            borderBottom: `1px solid ${theme.border.primary}`,
            backgroundColor: theme.background.secondary,
          }}
        >
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: '1rem 1.5rem',
                border: 'none',
                borderBottom: activeTab === tab.id ? `3px solid ${theme.border.focus}` : '3px solid transparent',
                backgroundColor: 'transparent',
                color: activeTab === tab.id ? theme.text.primary : theme.text.secondary,
                cursor: 'pointer',
                fontWeight: activeTab === tab.id ? 'bold' : 'normal',
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div
          style={{
            flex: 1,
            overflow: 'auto',
            padding: '1.5rem',
          }}
        >
          {activeTab === 'context' && (
            <ContextTab
              onDetectAll={handleDetectAll}
              showOnlyEssential={false}
            />
          )}

          {activeTab === 'metadata' && (
            <ContextTab
              onDetectAll={handleDetectAll}
              showOnlyEssential={true}
            />
          )}

          {activeTab === 'unity' && (
            <UnityTab
              unityPath={unityPath}
              setUnityPath={setUnityPath}
              isLoading={isLoadingUnity}
              isSaving={isSavingUnity}
              error={unityError}
              onSave={handleSaveUnity}
            />
          )}

          {activeTab === 'organization' && (
            <OrganizationTab
              organization={organization}
              setOrganization={setOrganization}
              previewText={previewText}
              previewTokens={previewTokens}
              isLoadingPreview={isLoadingPreview}
              onPreview={handlePreview}
            />
          )}

          {activeTab === 'guidance' && (
            <GuidanceTab />
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            padding: '1rem 1.5rem',
            borderTop: `1px solid ${theme.border.primary}`,
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '0.5rem',
          }}
        >
          <button
            onClick={() => {
              resetToDefault()
              onClose()
            }}
            style={{
              padding: '0.5rem 1rem',
              border: `1px solid ${theme.border.primary}`,
              borderRadius: '4px',
              backgroundColor: theme.button.default.background,
              color: theme.button.default.color,
              cursor: 'pointer',
            }}
          >
            Réinitialiser
          </button>
          <button
            onClick={() => {
              onApply?.()
              onClose()
            }}
            style={{
              padding: '0.5rem 1rem',
              border: 'none',
              borderRadius: '4px',
              backgroundColor: theme.button.primary.background,
              color: theme.button.primary.color,
              cursor: 'pointer',
            }}
          >
            Appliquer
          </button>
        </div>
      </div>
    </div>
  )
}

function ContextTab({ 
  onDetectAll, 
  showOnlyEssential 
}: { 
  onDetectAll: () => void
  showOnlyEssential: boolean 
}) {
  const elementTypes = [
    { id: 'character', label: 'Personnages' },
    { id: 'location', label: 'Lieux' },
    { id: 'item', label: 'Objets' },
    { id: 'species', label: 'Espèces' },
    { id: 'community', label: 'Communautés' },
  ]

  const [selectedElementType, setSelectedElementType] = useState('character')
  const { selectAllFields, selectEssentialFields, availableFields, fieldConfigs, essentialFields } = useContextConfigStore()
  
  const handleSelectAll = useCallback(() => {
    if (showOnlyEssential) {
      // Dans l'onglet Métadonnées : sélectionner tous les champs essentiels
      selectEssentialFields(selectedElementType)
    } else {
      // Dans l'onglet Contexte : sélectionner tous les champs (essentiels + non-essentiels)
      selectAllFields(selectedElementType)
    }
  }, [selectedElementType, selectAllFields, selectEssentialFields, showOnlyEssential])

  const handleSelectEssential = useCallback(() => {
    if (showOnlyEssential) {
      // Dans l'onglet Métadonnées : "Sélectionner essentiels" = sélectionner tous les essentiels (déjà fait par handleSelectAll)
      selectEssentialFields(selectedElementType)
    } else {
      // Dans l'onglet Contexte : "Sélectionner essentiels" = sélectionner uniquement les essentiels
      selectEssentialFields(selectedElementType)
    }
  }, [selectedElementType, selectEssentialFields, showOnlyEssential])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ marginBottom: '1rem', display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <select
          value={selectedElementType}
          onChange={(e) => setSelectedElementType(e.target.value)}
          style={{
            padding: '0.5rem',
            border: `1px solid ${theme.border.primary}`,
            borderRadius: '4px',
            backgroundColor: theme.input.background,
            color: theme.input.color,
          }}
        >
          {elementTypes.map((et) => (
            <option key={et.id} value={et.id}>
              {et.label}
            </option>
          ))}
        </select>
        <button
          onClick={onDetectAll}
          style={{
            padding: '0.5rem 1rem',
            border: `1px solid ${theme.border.primary}`,
            borderRadius: '4px',
            backgroundColor: theme.button.default.background,
            color: theme.button.default.color,
            cursor: 'pointer',
          }}
        >
          Détecter automatiquement tous les champs
        </button>
        {!showOnlyEssential && (
          <>
            <button
              onClick={handleSelectEssential}
              style={{
                padding: '0.5rem 1rem',
                border: `1px solid ${theme.border.primary}`,
                borderRadius: '4px',
                backgroundColor: theme.button.default.background,
                color: theme.button.default.color,
                cursor: 'pointer',
              }}
            >
              Sélectionner essentiels
            </button>
            <button
              onClick={handleSelectAll}
              style={{
                padding: '0.5rem 1rem',
                border: `1px solid ${theme.border.primary}`,
                borderRadius: '4px',
                backgroundColor: theme.button.default.background,
                color: theme.button.default.color,
                cursor: 'pointer',
              }}
            >
              Tout sélectionner
            </button>
          </>
        )}
        {showOnlyEssential && (
          <button
            onClick={handleSelectAll}
            style={{
              padding: '0.5rem 1rem',
              border: `1px solid ${theme.border.primary}`,
              borderRadius: '4px',
              backgroundColor: theme.button.default.background,
              color: theme.button.default.color,
              cursor: 'pointer',
            }}
          >
            Tout sélectionner
          </button>
        )}
      </div>

      <div style={{ flex: 1, minHeight: 0 }}>
        <ContextFieldSelector
          elementType={selectedElementType}
          showOnlyEssential={showOnlyEssential}
        />
      </div>
    </div>
  )
}

function UnityTab({
  unityPath,
  setUnityPath,
  isLoading,
  isSaving,
  error,
  onSave,
}: {
  unityPath: string
  setUnityPath: (path: string) => void
  isLoading: boolean
  isSaving: boolean
  error: string | null
  onSave: () => void
}) {
  return (
    <div>
      <h3 style={{ marginTop: 0, color: theme.text.primary }}>Configuration Unity</h3>

      {error && (
        <div
          style={{
            padding: '0.5rem',
            backgroundColor: theme.state.error.background,
            color: theme.state.error.color,
            marginBottom: '1rem',
            borderRadius: '4px',
          }}
        >
          {error}
        </div>
      )}

      <div style={{ marginBottom: '1rem' }}>
        <label style={{ display: 'block', marginBottom: '0.5rem', color: theme.text.primary }}>
          Chemin vers le dossier Unity des dialogues:
        </label>
        <input
          type="text"
          value={unityPath}
          onChange={(e) => setUnityPath(e.target.value)}
          disabled={isLoading}
          placeholder="Ex: F:/Unity/Alteir/Alteir_Cursor/Assets/Dialogue/generated"
          style={{
            width: '100%',
            padding: '0.5rem',
            boxSizing: 'border-box',
            backgroundColor: theme.input.background,
            border: `1px solid ${theme.input.border}`,
            color: theme.input.color,
            borderRadius: '4px',
          }}
        />
      </div>

      <button
        onClick={onSave}
        disabled={isSaving || isLoading}
        style={{
          padding: '0.5rem 1rem',
          border: 'none',
          borderRadius: '4px',
          backgroundColor: theme.button.primary.background,
          color: theme.button.primary.color,
          cursor: isSaving || isLoading ? 'not-allowed' : 'pointer',
          opacity: isSaving || isLoading ? 0.6 : 1,
        }}
      >
        {isSaving ? 'Enregistrement...' : 'Enregistrer'}
      </button>
    </div>
  )
}

function OrganizationTab({
  organization,
  setOrganization,
  previewText,
  previewTokens,
  isLoadingPreview,
  onPreview,
}: {
  organization: 'default' | 'narrative' | 'minimal'
  setOrganization: (mode: 'default' | 'narrative' | 'minimal') => void
  previewText: string
  previewTokens: number
  isLoadingPreview: boolean
  onPreview: () => void
}) {
  return (
    <div>
      <h3 style={{ marginTop: 0, color: theme.text.primary }}>Organisation du Prompt</h3>

      <div style={{ marginBottom: '1rem' }}>
        <label style={{ display: 'block', marginBottom: '0.5rem', color: theme.text.primary }}>
          Mode d'organisation:
        </label>
        <select
          value={organization}
          onChange={(e) => setOrganization(e.target.value as 'default' | 'narrative' | 'minimal')}
          style={{
            width: '100%',
            padding: '0.5rem',
            border: `1px solid ${theme.border.primary}`,
            borderRadius: '4px',
            backgroundColor: theme.input.background,
            color: theme.input.color,
          }}
        >
          <option value="default">Par défaut (ordre de la config)</option>
          <option value="narrative">Narratif (groupé par pertinence)</option>
          <option value="minimal">Minimal (seulement l'essentiel)</option>
        </select>
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <button
          onClick={onPreview}
          disabled={isLoadingPreview}
          style={{
            padding: '0.5rem 1rem',
            border: `1px solid ${theme.border.primary}`,
            borderRadius: '4px',
            backgroundColor: theme.button.default.background,
            color: theme.button.default.color,
            cursor: isLoadingPreview ? 'not-allowed' : 'pointer',
            opacity: isLoadingPreview ? 0.6 : 1,
          }}
        >
          {isLoadingPreview ? 'Chargement...' : 'Prévisualiser le contexte'}
        </button>
      </div>

      {previewText && (
        <div>
          <div style={{ marginBottom: '0.5rem', color: theme.text.secondary, fontSize: '0.9rem' }}>
            Tokens estimés: {previewTokens}
          </div>
          <pre
            style={{
              padding: '1rem',
              backgroundColor: theme.background.secondary,
              border: `1px solid ${theme.border.primary}`,
              borderRadius: '4px',
              overflow: 'auto',
              maxHeight: '400px',
              fontSize: '0.85rem',
              color: theme.text.primary,
              whiteSpace: 'pre-wrap',
            }}
          >
            {previewText}
          </pre>
        </div>
      )}
    </div>
  )
}

function GuidanceTab() {
  return (
    <div>
      <h3 style={{ marginTop: 0, color: theme.text.primary }}>Guide d'Utilisation</h3>

      <div style={{ marginBottom: '1.5rem' }}>
        <h4 style={{ color: theme.text.primary, marginBottom: '0.5rem' }}>Indicateurs Visuels</h4>
        <ul style={{ color: theme.text.secondary, paddingLeft: '1.5rem' }}>
          <li>
            <span style={{ color: theme.state.success.color }}>✓</span> Vert : Champ suggéré/recommandé
          </li>
          <li>
            <span style={{ color: theme.state.info.color }}>⭐</span> Bleu : Champ essentiel
          </li>
          <li>
            <span style={{ color: theme.text.secondary }}>ⓘ</span> Gris : Champ commun
          </li>
          <li>
            <span style={{ color: theme.text.tertiary }}>○</span> Gris clair : Champ rare
          </li>
        </ul>
      </div>

      <div style={{ marginBottom: '1.5rem' }}>
        <h4 style={{ color: theme.text.primary, marginBottom: '0.5rem' }}>Champs Recommandés par Type de Scène</h4>
        <div style={{ color: theme.text.secondary, fontSize: '0.9rem' }}>
          <p><strong>Dialogue :</strong> Dialogue Type, Caractérisation, Relations</p>
          <p><strong>Action :</strong> Pouvoirs, Compétences, Stats</p>
          <p><strong>Émotionnel :</strong> Caractérisation, Relations, Background</p>
          <p><strong>Révélation :</strong> Background, Évènements marquants, Arcs Narratifs</p>
        </div>
      </div>

      <div style={{ marginBottom: '1.5rem' }}>
        <h4 style={{ color: theme.text.primary, marginBottom: '0.5rem' }}>Modes d'Organisation</h4>
        <div style={{ color: theme.text.secondary, fontSize: '0.9rem' }}>
          <p><strong>Par défaut :</strong> Ordre linéaire selon la configuration</p>
          <p><strong>Narratif :</strong> Groupement logique (Identité → Caractérisation → Voix → Background → Mécaniques)</p>
          <p><strong>Minimal :</strong> Seulement les champs essentiels pour la génération</p>
        </div>
      </div>

      <div>
        <h4 style={{ color: theme.text.primary, marginBottom: '0.5rem' }}>Conseils</h4>
        <ul style={{ color: theme.text.secondary, paddingLeft: '1.5rem', fontSize: '0.9rem' }}>
          <li>Utilisez "Détecter automatiquement" pour découvrir tous les champs disponibles</li>
          <li>Les champs suggérés sont particulièrement pertinents pour le type de génération</li>
          <li>Le mode "Narratif" améliore la compréhension du LLM en organisant logiquement les informations</li>
          <li>Utilisez la prévisualisation pour vérifier le contexte avant de générer</li>
        </ul>
      </div>
    </div>
  )
}

