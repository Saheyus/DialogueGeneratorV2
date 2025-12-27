/**
 * Éditeur pour les instructions de scène, le profil d'auteur et le system prompt.
 */
import React, { memo, useCallback, useState, useEffect } from 'react'
import { Tabs, type Tab } from '../shared/Tabs'
import { FormField } from '../shared/FormField'
import { useSystemPrompt } from '../../hooks/useSystemPrompt'
import { useAuthorProfile } from '../../hooks/useAuthorProfile'
import { theme } from '../../theme'
import * as configAPI from '../../api/config'

export interface SystemPromptEditorProps {
  userInstructions: string
  authorProfile: string
  systemPromptOverride: string | null
  onUserInstructionsChange: (instructions: string) => void
  onAuthorProfileChange: (profile: string) => void
  onSystemPromptChange: (prompt: string | null) => void
}

export const SystemPromptEditor = memo(function SystemPromptEditor({
  userInstructions,
  authorProfile,
  systemPromptOverride,
  onUserInstructionsChange,
  onAuthorProfileChange,
  onSystemPromptChange,
}: SystemPromptEditorProps) {
  const {
    systemPrompt,
    isLoading: isLoadingSystemPrompt,
    savePrompt,
    restore: restoreSystemPrompt,
    updatePrompt,
  } = useSystemPrompt()

  const {
    authorProfile: authorProfileState,
    saveProfile,
    restore: restoreAuthorProfile,
    updateProfile,
  } = useAuthorProfile()

  // Synchroniser le state du hook avec le prop (si le prop change depuis l'extérieur)
  useEffect(() => {
    if (authorProfile !== authorProfileState) {
      updateProfile(authorProfile)
    }
  }, [authorProfile]) // Seulement quand le prop change

  const [sceneTemplates, setSceneTemplates] = useState<configAPI.SceneInstructionTemplate[]>([])
  const [authorTemplates, setAuthorTemplates] = useState<configAPI.AuthorProfileTemplate[]>([])
  const [isLoadingTemplates, setIsLoadingTemplates] = useState(false)
  const [selectedSceneTemplateId, setSelectedSceneTemplateId] = useState<string | null>(null)
  const [selectedAuthorTemplateId, setSelectedAuthorTemplateId] = useState<string | null>(null)
  const [showTemplatePreview, setShowTemplatePreview] = useState<string | null>(null)

  useEffect(() => {
    loadTemplates()
  }, [])

  const loadTemplates = async () => {
    setIsLoadingTemplates(true)
    try {
      const [sceneResponse, authorResponse] = await Promise.all([
        configAPI.getSceneInstructionTemplates(),
        configAPI.getAuthorProfileTemplates(),
      ])
      setSceneTemplates(sceneResponse.templates)
      setAuthorTemplates(authorResponse.templates)
    } catch (err) {
      console.error('Erreur lors du chargement des templates:', err)
    } finally {
      setIsLoadingTemplates(false)
    }
  }

  const handleSceneTemplateClick = useCallback((template: configAPI.SceneInstructionTemplate) => {
    if (selectedSceneTemplateId === template.id) {
      setShowTemplatePreview(template.id)
    } else {
      setSelectedSceneTemplateId(template.id)
      // Appliquer les instructions du template au brief de scène
      const currentInstructions = userInstructions.trim()
      const newInstructions = currentInstructions
        ? `${currentInstructions}\n\n${template.instructions}`
        : template.instructions
      onUserInstructionsChange(newInstructions)
    }
  }, [selectedSceneTemplateId, userInstructions, onUserInstructionsChange])

  const handleAuthorTemplateClick = useCallback((template: configAPI.AuthorProfileTemplate) => {
    if (selectedAuthorTemplateId === template.id) {
      setShowTemplatePreview(template.id)
    } else {
      setSelectedAuthorTemplateId(template.id)
      updateProfile(template.profile)
      onAuthorProfileChange(template.profile)
    }
  }, [selectedAuthorTemplateId, updateProfile, onAuthorProfileChange])

  const handleSystemPromptChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const value = e.target.value
      updatePrompt(value)
      onSystemPromptChange(value || null)
    },
    [updatePrompt, onSystemPromptChange]
  )

  const handleAuthorProfileChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const value = e.target.value
      updateProfile(value)
      onAuthorProfileChange(value)
      if (selectedAuthorTemplateId) {
        setSelectedAuthorTemplateId(null)
      }
    },
    [updateProfile, onAuthorProfileChange, selectedAuthorTemplateId]
  )

  const handleSaveSystemPrompt = useCallback(() => {
    const currentPrompt = systemPromptOverride || systemPrompt || ''
    try {
      savePrompt(currentPrompt)
      onSystemPromptChange(currentPrompt || null)
      alert('Prompt système sauvegardé avec succès')
    } catch (err) {
      console.error('Erreur lors de la sauvegarde:', err)
      alert('Erreur lors de la sauvegarde du prompt système')
    }
  }, [systemPromptOverride, systemPrompt, savePrompt, onSystemPromptChange])

  const handleRestoreSystemPrompt = useCallback(() => {
    restoreSystemPrompt()
    onSystemPromptChange(null)
  }, [restoreSystemPrompt, onSystemPromptChange])

  const handleSaveAuthorProfile = useCallback(() => {
    const currentProfile = authorProfile || ''
    try {
      saveProfile(currentProfile)
      onAuthorProfileChange(currentProfile)
      alert('Profil d\'auteur sauvegardé avec succès')
    } catch (err) {
      console.error('Erreur lors de la sauvegarde:', err)
      alert('Erreur lors de la sauvegarde du profil d\'auteur')
    }
  }, [authorProfile, saveProfile, onAuthorProfileChange])

  const handleRestoreAuthorProfile = useCallback(() => {
    restoreAuthorProfile()
    // Le hook met à jour son state, on doit le lire après restauration
    setTimeout(() => {
      const saved = localStorage.getItem('dialogue_generator_saved_author_profile')
      onAuthorProfileChange(saved || '')
    }, 0)
  }, [restoreAuthorProfile, onAuthorProfileChange])

  const handleSaveSceneInstructions = useCallback(() => {
    try {
      localStorage.setItem('dialogue_generator_saved_scene_instructions', userInstructions)
      alert('Brief de scène sauvegardé avec succès')
    } catch (err) {
      console.error('Erreur lors de la sauvegarde:', err)
      alert('Erreur lors de la sauvegarde du brief de scène')
    }
  }, [userInstructions])

  const handleRestoreSceneInstructions = useCallback(() => {
    try {
      const saved = localStorage.getItem('dialogue_generator_saved_scene_instructions')
      if (saved) {
        onUserInstructionsChange(saved)
      }
    } catch (err) {
      console.warn('Impossible de restaurer le brief de scène:', err)
    }
  }, [onUserInstructionsChange])

  const tabs: Tab[] = [
    {
      id: 'user-instructions',
      label: 'Instructions de Scène',
      content: (
        <div style={{ padding: '1rem' }}>
          {/* Templates de scène */}
          <div style={{ marginBottom: '1rem' }}>
            <label
              style={{
                display: 'block',
                marginBottom: '0.5rem',
                color: theme.text.primary,
                fontSize: '0.9rem',
                fontWeight: 500,
              }}
            >
              Templates de scène:
            </label>
            {isLoadingTemplates ? (
              <div style={{ color: theme.text.secondary, fontSize: '0.85rem' }}>
                Chargement des templates...
              </div>
            ) : (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.5rem' }}>
                {sceneTemplates.map((template) => (
                  <button
                    key={template.id}
                    onClick={() => handleSceneTemplateClick(template)}
                    onDoubleClick={() => setShowTemplatePreview(template.id)}
                    style={{
                      padding: '0.5rem 1rem',
                      border: `1px solid ${selectedSceneTemplateId === template.id ? theme.border.focus : theme.border.primary}`,
                      borderRadius: '4px',
                      backgroundColor: selectedSceneTemplateId === template.id 
                        ? theme.button.primary.background 
                        : theme.button.default.background,
                      color: selectedSceneTemplateId === template.id 
                        ? theme.button.primary.color 
                        : theme.button.default.color,
                      cursor: 'pointer',
                      fontSize: '0.85rem',
                    }}
                    title={`${template.description}\n\nDouble-clic pour voir le contenu complet`}
                  >
                    {template.name}
                    {selectedSceneTemplateId === template.id && ' ✓'}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Prévisualisation du template */}
          {showTemplatePreview && sceneTemplates.find(t => t.id === showTemplatePreview) && (
            <div
              style={{
                marginBottom: '1rem',
                padding: '1rem',
                backgroundColor: theme.background.secondary,
                border: `1px solid ${theme.border.primary}`,
                borderRadius: '4px',
                maxHeight: '300px',
                overflowY: 'auto',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <strong style={{ color: theme.text.primary }}>
                  {sceneTemplates.find(t => t.id === showTemplatePreview)?.name}
                </strong>
                <button
                  onClick={() => setShowTemplatePreview(null)}
                  style={{
                    padding: '0.25rem 0.5rem',
                    border: `1px solid ${theme.border.primary}`,
                    borderRadius: '4px',
                    backgroundColor: theme.button.default.background,
                    color: theme.button.default.color,
                    cursor: 'pointer',
                    fontSize: '0.75rem',
                  }}
                >
                  Fermer
                </button>
              </div>
              <pre
                style={{
                  margin: 0,
                  color: theme.text.secondary,
                  fontSize: '0.8rem',
                  whiteSpace: 'pre-wrap',
                  fontFamily: 'monospace',
                }}
              >
                {sceneTemplates.find(t => t.id === showTemplatePreview)?.instructions}
              </pre>
            </div>
          )}

          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '0.5rem',
            }}
          >
            <label
              htmlFor="user-instructions-textarea"
              style={{
                color: theme.text.primary,
                fontSize: '0.9rem',
                fontWeight: 500,
              }}
            >
              Brief de scène:
            </label>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                onClick={handleSaveSceneInstructions}
                style={{
                  padding: '0.5rem 1rem',
                  border: `1px solid ${theme.border.primary}`,
                  borderRadius: '4px',
                  backgroundColor: theme.button.primary.background,
                  color: theme.button.primary.color,
                  cursor: 'pointer',
                  fontSize: '0.85rem',
                }}
                title="Sauvegarde le brief de scène actuel"
              >
                Sauvegarder
              </button>
              <button
                onClick={handleRestoreSceneInstructions}
                style={{
                  padding: '0.5rem 1rem',
                  border: `1px solid ${theme.border.primary}`,
                  borderRadius: '4px',
                  backgroundColor: theme.button.default.background,
                  color: theme.button.default.color,
                  cursor: 'pointer',
                  fontSize: '0.85rem',
                }}
                title="Restaure la dernière version sauvegardée"
              >
                Restaurer
              </button>
            </div>
          </div>
          <FormField label="" htmlFor="user-instructions-textarea">
            <div style={{ position: 'relative' }}>
              <textarea
                id="user-instructions-textarea"
                value={userInstructions}
                onChange={(e) => onUserInstructionsChange(e.target.value)}
                rows={8}
                placeholder="Ex: Bob doit annoncer à Alice qu'il part à l'aventure. Ton désiré: Héroïque. Inclure une condition sur la compétence 'Charisme' de Bob."
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  paddingBottom: '2rem',
                  boxSizing: 'border-box',
                  backgroundColor: theme.input.background,
                  border: `1px solid ${theme.input.border}`,
                  color: theme.input.color,
                  borderRadius: '4px',
                  fontFamily: 'inherit',
                  fontSize: '0.9rem',
                  resize: 'vertical',
                }}
              />
              <div
                style={{
                  position: 'absolute',
                  bottom: '0.5rem',
                  right: '0.5rem',
                  fontSize: '0.75rem',
                  color: theme.text.secondary,
                  backgroundColor: theme.background.panel,
                  padding: '0.25rem 0.5rem',
                  borderRadius: '4px',
                }}
              >
                {userInstructions.length} caractères
                {userInstructions.length > 0 && (
                  <span style={{ marginLeft: '0.5rem' }}>
                    (~{Math.ceil(userInstructions.length / 4)} tokens)
                  </span>
                )}
              </div>
            </div>
          </FormField>
        </div>
      ),
    },
    {
      id: 'author-profile',
      label: 'Auteur (global)',
      content: (
        <div style={{ padding: '1rem' }}>
          {/* Templates de profil d'auteur */}
          <div style={{ marginBottom: '1rem' }}>
            <label
              style={{
                display: 'block',
                marginBottom: '0.5rem',
                color: theme.text.primary,
                fontSize: '0.9rem',
                fontWeight: 500,
              }}
            >
              Templates de profil d'auteur:
            </label>
            {isLoadingTemplates ? (
              <div style={{ color: theme.text.secondary, fontSize: '0.85rem' }}>
                Chargement des templates...
              </div>
            ) : (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.5rem' }}>
                {authorTemplates.map((template) => (
                  <button
                    key={template.id}
                    onClick={() => handleAuthorTemplateClick(template)}
                    onDoubleClick={() => setShowTemplatePreview(template.id)}
                    style={{
                      padding: '0.5rem 1rem',
                      border: `1px solid ${selectedAuthorTemplateId === template.id ? theme.border.focus : theme.border.primary}`,
                      borderRadius: '4px',
                      backgroundColor: selectedAuthorTemplateId === template.id 
                        ? theme.button.primary.background 
                        : theme.button.default.background,
                      color: selectedAuthorTemplateId === template.id 
                        ? theme.button.primary.color 
                        : theme.button.default.color,
                      cursor: 'pointer',
                      fontSize: '0.85rem',
                    }}
                    title={`${template.description}\n\nDouble-clic pour voir le contenu complet`}
                  >
                    {template.name}
                    {selectedAuthorTemplateId === template.id && ' ✓'}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Prévisualisation du template */}
          {showTemplatePreview && authorTemplates.find(t => t.id === showTemplatePreview) && (
            <div
              style={{
                marginBottom: '1rem',
                padding: '1rem',
                backgroundColor: theme.background.secondary,
                border: `1px solid ${theme.border.primary}`,
                borderRadius: '4px',
                maxHeight: '300px',
                overflowY: 'auto',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <strong style={{ color: theme.text.primary }}>
                  {authorTemplates.find(t => t.id === showTemplatePreview)?.name}
                </strong>
                <button
                  onClick={() => setShowTemplatePreview(null)}
                  style={{
                    padding: '0.25rem 0.5rem',
                    border: `1px solid ${theme.border.primary}`,
                    borderRadius: '4px',
                    backgroundColor: theme.button.default.background,
                    color: theme.button.default.color,
                    cursor: 'pointer',
                    fontSize: '0.75rem',
                  }}
                >
                  Fermer
                </button>
              </div>
              <pre
                style={{
                  margin: 0,
                  color: theme.text.secondary,
                  fontSize: '0.8rem',
                  whiteSpace: 'pre-wrap',
                  fontFamily: 'monospace',
                }}
              >
                {authorTemplates.find(t => t.id === showTemplatePreview)?.profile || '(Vide)'}
              </pre>
            </div>
          )}

          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '0.5rem',
            }}
          >
            <label
              htmlFor="author-profile-textarea"
              style={{
                color: theme.text.primary,
                fontSize: '0.9rem',
                fontWeight: 500,
              }}
            >
              Profil d'auteur (réutilisable):
            </label>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                onClick={handleSaveAuthorProfile}
                style={{
                  padding: '0.5rem 1rem',
                  border: `1px solid ${theme.border.primary}`,
                  borderRadius: '4px',
                  backgroundColor: theme.button.primary.background,
                  color: theme.button.primary.color,
                  cursor: 'pointer',
                  fontSize: '0.85rem',
                }}
                title="Sauvegarde le profil d'auteur actuel"
              >
                Sauvegarder
              </button>
              <button
                onClick={handleRestoreAuthorProfile}
                style={{
                  padding: '0.5rem 1rem',
                  border: `1px solid ${theme.border.primary}`,
                  borderRadius: '4px',
                  backgroundColor: theme.button.default.background,
                  color: theme.button.default.color,
                  cursor: 'pointer',
                  fontSize: '0.85rem',
                }}
                title="Restaure la dernière version sauvegardée"
              >
                Restaurer
              </button>
            </div>
          </div>
          <FormField label="" htmlFor="author-profile-textarea">
            <textarea
              id="author-profile-textarea"
              value={authorProfile}
              onChange={handleAuthorProfileChange}
              rows={8}
              placeholder="Style d'auteur global (réutilisable entre toutes les scènes). Ex: Style littéraire, vocabulaire riche, etc."
              style={{
                width: '100%',
                padding: '0.5rem',
                boxSizing: 'border-box',
                backgroundColor: theme.input.background,
                border: `1px solid ${theme.input.border}`,
                color: theme.input.color,
                borderRadius: '4px',
                fontFamily: 'inherit',
                fontSize: '0.9rem',
                resize: 'vertical',
                lineHeight: '1.5',
              }}
            />
          </FormField>
        </div>
      ),
    },
    {
      id: 'system-prompt',
      label: 'Système LLM (avancé)',
      content: (
        <div style={{ padding: '1rem' }}>
          <div
            style={{
              marginBottom: '1rem',
              padding: '0.75rem',
              backgroundColor: theme.background.secondary,
              border: `1px solid ${theme.border.primary}`,
              borderRadius: '4px',
              fontSize: '0.85rem',
              color: theme.text.secondary,
            }}
          >
            <strong style={{ color: theme.text.primary }}>⚠️ Zone avancée</strong>
            <br />
            Modifiez uniquement si vous savez ce que vous faites. Ce prompt définit l'identité technique du LLM et les règles de format de sortie.
          </div>

          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '0.5rem',
            }}
          >
            <label
              htmlFor="system-prompt-textarea"
              style={{
                color: theme.text.primary,
                fontSize: '0.9rem',
                fontWeight: 500,
              }}
            >
              Prompt Système Principal:
            </label>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                onClick={handleSaveSystemPrompt}
                disabled={isLoadingSystemPrompt}
                style={{
                  padding: '0.5rem 1rem',
                  border: `1px solid ${theme.border.primary}`,
                  borderRadius: '4px',
                  backgroundColor: theme.button.primary.background,
                  color: theme.button.primary.color,
                  cursor: isLoadingSystemPrompt ? 'not-allowed' : 'pointer',
                  opacity: isLoadingSystemPrompt ? 0.6 : 1,
                  fontSize: '0.85rem',
                }}
                title="Sauvegarde le prompt système actuel"
              >
                Sauvegarder
              </button>
              <button
                onClick={handleRestoreSystemPrompt}
                disabled={isLoadingSystemPrompt}
                style={{
                  padding: '0.5rem 1rem',
                  border: `1px solid ${theme.border.primary}`,
                  borderRadius: '4px',
                  backgroundColor: theme.button.default.background,
                  color: theme.button.default.color,
                  cursor: isLoadingSystemPrompt ? 'not-allowed' : 'pointer',
                  opacity: isLoadingSystemPrompt ? 0.6 : 1,
                  fontSize: '0.85rem',
                }}
                title="Restaure la dernière version sauvegardée (ou le défaut si rien n'est sauvegardé)"
              >
                Restaurer
              </button>
            </div>
          </div>
          <FormField label="" htmlFor="system-prompt-textarea">
            <textarea
              id="system-prompt-textarea"
              value={systemPromptOverride || systemPrompt || ''}
              onChange={handleSystemPromptChange}
              rows={12}
              placeholder="Modifiez le prompt système principal envoyé au LLM. Ce prompt guide le comportement général de l'IA et le format de sortie."
              style={{
                width: '100%',
                padding: '0.5rem',
                boxSizing: 'border-box',
                backgroundColor: theme.input.background,
                border: `1px solid ${theme.input.border}`,
                color: theme.input.color,
                borderRadius: '4px',
                fontFamily: 'monospace',
                fontSize: '0.85rem',
                resize: 'vertical',
                lineHeight: '1.5',
              }}
            />
          </FormField>
        </div>
      ),
    },
  ]

  const [activeTabId, setActiveTabId] = useState(tabs[0].id)

  return (
    <div
      style={{
        marginBottom: '1rem',
        border: `1px solid ${theme.border.primary}`,
        borderRadius: '4px',
        backgroundColor: theme.background.panel,
      }}
    >
      <Tabs
        tabs={tabs}
        activeTabId={activeTabId}
        onTabChange={setActiveTabId}
        style={{ flex: 'none' }}
      />
    </div>
  )
})
