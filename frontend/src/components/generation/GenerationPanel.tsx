/**
 * Panneau de génération de dialogues.
 */
import { useState, useEffect, useCallback } from 'react'
import * as dialoguesAPI from '../../api/dialogues'
import * as configAPI from '../../api/config'
import * as interactionsAPI from '../../api/interactions'
import * as contextAPI from '../../api/context'
import { useContextStore } from '../../store/contextStore'
import { getErrorMessage } from '../../types/errors'
import { theme } from '../../theme'
import type {
  GenerateDialogueVariantsRequest,
  GenerateInteractionVariantsRequest,
  DialogueVariantResponse,
  InteractionResponse,
  LLMModelResponse,
  InteractionListResponse,
} from '../../types/api'

type GenerationMode = 'variants' | 'interactions'

export function GenerationPanel() {
  const { selections } = useContextStore()
  const [generationMode, setGenerationMode] = useState<GenerationMode>('variants')
  const [userInstructions, setUserInstructions] = useState('')
  const [kVariants, setKVariants] = useState(2)
  const [maxContextTokens, setMaxContextTokens] = useState(1500)
  const [llmModel, setLlmModel] = useState('gpt-4o-mini')
  const [availableModels, setAvailableModels] = useState<LLMModelResponse[]>([])
  const [variants, setVariants] = useState<DialogueVariantResponse[]>([])
  const [interactions, setInteractions] = useState<InteractionResponse[]>([])
  const [estimatedTokens, setEstimatedTokens] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isEstimating, setIsEstimating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [previousInteractionId, setPreviousInteractionId] = useState<string>('')
  const [availableInteractions, setAvailableInteractions] = useState<InteractionResponse[]>([])
  const [characterA, setCharacterA] = useState<string>('')
  const [characterB, setCharacterB] = useState<string>('')
  const [sceneRegion, setSceneRegion] = useState<string>('')
  const [subLocation, setSubLocation] = useState<string>('')

  const loadModels = useCallback(async () => {
    try {
      const response = await configAPI.listLLMModels()
      setAvailableModels(response.models)
      if (response.models.length > 0) {
        setLlmModel(response.models[0].model_identifier)
      }
    } catch (err) {
      console.error('Erreur lors du chargement des modèles:', err)
    }
  }, [])

  useEffect(() => {
    loadModels()
    loadInteractions()
  }, [loadModels])

  const loadInteractions = useCallback(async () => {
    try {
      const response: InteractionListResponse = await interactionsAPI.listInteractions()
      setAvailableInteractions(response.interactions)
    } catch (err) {
      console.error('Erreur lors du chargement des interactions:', err)
    }
  }, [])

  const hasSelections = useCallback((): boolean => {
    return (
      selections.characters.length > 0 ||
      selections.locations.length > 0 ||
      selections.items.length > 0 ||
      selections.species.length > 0 ||
      selections.communities.length > 0 ||
      selections.dialogues_examples.length > 0
    )
  }, [selections])

  const estimateTokens = useCallback(async () => {
    if (!userInstructions.trim() && !hasSelections()) {
      setEstimatedTokens(null)
      return
    }

    setIsEstimating(true)
    try {
      const response = await dialoguesAPI.estimateTokens(
        selections,
        userInstructions,
        maxContextTokens
      )
      setEstimatedTokens(response.total_estimated_tokens)
    } catch (err) {
      console.error('Erreur lors de l\'estimation:', err)
      // Ne pas afficher d'erreur pour l'estimation, juste ne pas afficher le résultat
      setEstimatedTokens(null)
    } finally {
      setIsEstimating(false)
    }
  }, [selections, userInstructions, maxContextTokens, hasSelections])

  useEffect(() => {
    // Estimer les tokens quand les sélections ou les instructions changent
    const timeoutId = setTimeout(() => {
      if (userInstructions.trim() || hasSelections()) {
        estimateTokens()
      } else {
        setEstimatedTokens(null)
      }
    }, 500)

    return () => clearTimeout(timeoutId)
  }, [userInstructions, selections, maxContextTokens, estimateTokens, hasSelections])


  const handleGenerate = async () => {
    setIsLoading(true)
    setError(null)

    try {
      if (generationMode === 'variants') {
        const request: GenerateDialogueVariantsRequest = {
          k_variants: kVariants,
          user_instructions: userInstructions,
          context_selections: selections,
          max_context_tokens: maxContextTokens,
          structured_output: false,
          llm_model_identifier: llmModel,
        }

        const response = await dialoguesAPI.generateDialogueVariants(request)
        setVariants(response.variants)
        setInteractions([])
      } else {
        const request: GenerateInteractionVariantsRequest = {
          k_variants: kVariants,
          user_instructions: userInstructions,
          context_selections: selections,
          max_context_tokens: maxContextTokens,
          llm_model_identifier: llmModel,
          previous_interaction_id: previousInteractionId || undefined,
        }

        const response = await dialoguesAPI.generateInteractionVariants(request)
        setInteractions(response)
        setVariants([])
      }
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }

  const handleSaveAsInteraction = async (variant: DialogueVariantResponse) => {
    try {
      // Convertir une variante en interaction (structure basique)
      const interaction: InteractionResponse = {
        interaction_id: `generated_${Date.now()}`,
        title: variant.title,
        elements: [
          {
            type: 'dialogue',
            content: variant.content,
          },
        ],
        header_commands: [],
        header_tags: ['generated'],
      }

      await interactionsAPI.createInteraction(interaction)
      alert('Interaction sauvegardée avec succès!')
    } catch (err) {
      alert(getErrorMessage(err))
    }
  }

  return (
    <div style={{ padding: '1.5rem', height: '100%', overflowY: 'auto', backgroundColor: theme.background.panel }}>
      <h2 style={{ marginTop: 0, color: theme.text.primary }}>Génération de Dialogues</h2>

      <div style={{ marginBottom: '1rem', display: 'flex', gap: '0.5rem' }}>
        <button
          onClick={() => {
            setGenerationMode('variants')
            setVariants([])
            setInteractions([])
          }}
          style={{
            padding: '0.5rem 1rem',
            border: `1px solid ${theme.border.primary}`,
            borderRadius: '4px',
            backgroundColor: generationMode === 'variants' ? theme.button.primary.background : theme.button.default.background,
            color: generationMode === 'variants' ? theme.button.primary.color : theme.button.default.color,
            cursor: 'pointer',
          }}
        >
          Variantes texte
        </button>
        <button
          onClick={() => {
            setGenerationMode('interactions')
            setVariants([])
            setInteractions([])
          }}
          style={{
            padding: '0.5rem 1rem',
            border: `1px solid ${theme.border.primary}`,
            borderRadius: '4px',
            backgroundColor: generationMode === 'interactions' ? theme.button.primary.background : theme.button.default.background,
            color: generationMode === 'interactions' ? theme.button.primary.color : theme.button.default.color,
            cursor: 'pointer',
          }}
        >
          Interactions structurées
        </button>
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <label style={{ color: theme.text.primary }}>
          Instructions:
          <textarea
            value={userInstructions}
            onChange={(e) => setUserInstructions(e.target.value)}
            rows={5}
            style={{ 
              width: '100%', 
              padding: '0.5rem', 
              marginTop: '0.5rem', 
              boxSizing: 'border-box',
              backgroundColor: theme.input.background,
              border: `1px solid ${theme.input.border}`,
              color: theme.input.color,
            }}
          />
        </label>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
        <div>
          <label style={{ color: theme.text.primary }}>
            Nombre de variantes:
            <input
              type="number"
              value={kVariants}
              onChange={(e) => setKVariants(parseInt(e.target.value) || 1)}
              min={1}
              max={10}
              style={{ 
                width: '100%', 
                padding: '0.5rem', 
                marginTop: '0.5rem', 
                boxSizing: 'border-box',
                backgroundColor: theme.input.background,
                border: `1px solid ${theme.input.border}`,
                color: theme.input.color,
              }}
            />
          </label>
        </div>

        <div>
          <label style={{ color: theme.text.primary }}>
            Modèle LLM:
            <select
              value={llmModel}
              onChange={(e) => setLlmModel(e.target.value)}
              style={{ 
                width: '100%', 
                padding: '0.5rem', 
                marginTop: '0.5rem', 
                boxSizing: 'border-box',
                backgroundColor: theme.input.background,
                border: `1px solid ${theme.input.border}`,
                color: theme.input.color,
              }}
            >
              {availableModels.map((model, index) => (
                <option key={`${model.model_identifier}-${index}-${model.display_name}`} value={model.model_identifier}>
                  {model.display_name || model.model_identifier}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <label style={{ color: theme.text.primary }}>
          Max tokens contexte:
          <input
            type="number"
            value={maxContextTokens}
            onChange={(e) => setMaxContextTokens(parseInt(e.target.value) || 1500)}
            min={100}
            max={8000}
            style={{ 
              width: '100%', 
              padding: '0.5rem', 
              marginTop: '0.5rem', 
              boxSizing: 'border-box',
              backgroundColor: theme.input.background,
              border: `1px solid ${theme.input.border}`,
              color: theme.input.color,
            }}
          />
        </label>
      </div>

      {estimatedTokens !== null && (
        <div style={{ 
          marginBottom: '1rem', 
          padding: '0.5rem', 
          backgroundColor: theme.state.info.background, 
          color: theme.state.info.color,
          borderRadius: '4px' 
        }}>
          {isEstimating ? (
            <span>Estimation en cours...</span>
          ) : (
            <span>
              <strong>Tokens estimés:</strong> {estimatedTokens.toLocaleString()}
            </span>
          )}
        </div>
      )}

      <div style={{ marginBottom: '1rem', padding: '1rem', border: `1px solid ${theme.border.primary}`, borderRadius: '4px' }}>
        <h3 style={{ marginTop: 0, marginBottom: '0.75rem', fontSize: '1rem', fontWeight: 'bold' }}>
          Lier Éléments Connexes
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '0.5rem' }}>
          <input
            type="text"
            placeholder="Personnage A"
            value={characterA}
            onChange={(e) => setCharacterA(e.target.value)}
            style={{ 
              padding: '0.5rem', 
              backgroundColor: theme.input.background,
              border: `1px solid ${theme.input.border}`,
              color: theme.input.color,
            }}
          />
          <input
            type="text"
            placeholder="Personnage B"
            value={characterB}
            onChange={(e) => setCharacterB(e.target.value)}
            style={{ 
              padding: '0.5rem', 
              backgroundColor: theme.input.background,
              border: `1px solid ${theme.input.border}`,
              color: theme.input.color,
            }}
          />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '0.5rem' }}>
          <input
            type="text"
            placeholder="Région"
            value={sceneRegion}
            onChange={(e) => setSceneRegion(e.target.value)}
            style={{ 
              padding: '0.5rem', 
              backgroundColor: theme.input.background,
              border: `1px solid ${theme.input.border}`,
              color: theme.input.color,
            }}
          />
          <input
            type="text"
            placeholder="Sous-lieu"
            value={subLocation}
            onChange={(e) => setSubLocation(e.target.value)}
            style={{ 
              padding: '0.5rem', 
              backgroundColor: theme.input.background,
              border: `1px solid ${theme.input.border}`,
              color: theme.input.color,
            }}
          />
        </div>
        <button
          onClick={async () => {
            try {
              const { applyLinkedElements } = useContextStore.getState()
              const response = await contextAPI.getLinkedElements({
                character_a: characterA || undefined,
                character_b: characterB || undefined,
                scene_region: sceneRegion || undefined,
                sub_location: subLocation || undefined,
              })
              applyLinkedElements(response.linked_elements)
              alert(`${response.total} éléments liés ajoutés`)
            } catch (err) {
              setError(getErrorMessage(err))
            }
          }}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: theme.button.secondary?.background || theme.button.default.background,
            color: theme.button.secondary?.color || theme.button.default.color,
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          Lier Éléments Connexes
        </button>
      </div>

      {generationMode === 'interactions' && (
        <div style={{ marginBottom: '1rem', padding: '1rem', border: `1px solid ${theme.border.primary}`, borderRadius: '4px' }}>
          <h3 style={{ marginTop: 0, marginBottom: '0.75rem', fontSize: '1rem', fontWeight: 'bold' }}>
            Continuité (Interaction précédente)
          </h3>
          <select
            value={previousInteractionId}
            onChange={(e) => setPreviousInteractionId(e.target.value)}
            style={{ 
              width: '100%', 
              padding: '0.5rem', 
              backgroundColor: theme.input.background,
              border: `1px solid ${theme.input.border}`,
              color: theme.input.color,
            }}
          >
            <option value="">-- Aucune interaction précédente --</option>
            {availableInteractions.map((interaction) => (
              <option key={interaction.interaction_id} value={interaction.interaction_id}>
                {interaction.title || interaction.interaction_id}
              </option>
            ))}
          </select>
        </div>
      )}

      <button
        onClick={handleGenerate}
        disabled={isLoading || !userInstructions.trim()}
        style={{
          padding: '0.75rem 1.5rem',
          backgroundColor: theme.button.primary.background,
          color: theme.button.primary.color,
          border: 'none',
          borderRadius: '4px',
          cursor: isLoading || !userInstructions.trim() ? 'not-allowed' : 'pointer',
          opacity: isLoading || !userInstructions.trim() ? 0.6 : 1,
          marginBottom: '1rem',
        }}
      >
        {isLoading ? 'Génération...' : 'Générer'}
      </button>

      {error && (
        <div style={{ 
          color: theme.state.error.color, 
          marginTop: '1rem', 
          padding: '0.5rem', 
          backgroundColor: theme.state.error.background, 
          borderRadius: '4px' 
        }}>
          {error}
        </div>
      )}

      {variants.length > 0 && (
        <div style={{ marginTop: '2rem' }}>
          <h3 style={{ color: theme.text.primary }}>Variantes générées ({variants.length}):</h3>
          {variants.map((variant) => (
            <div
              key={variant.id}
              style={{
                marginBottom: '1rem',
                padding: '1rem',
                border: `1px solid ${theme.border.primary}`,
                borderRadius: '4px',
                backgroundColor: theme.background.tertiary,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <h4 style={{ margin: 0, color: theme.text.primary }}>{variant.title}</h4>
                <button
                  onClick={() => handleSaveAsInteraction(variant)}
                  style={{
                    padding: '0.25rem 0.5rem',
                    fontSize: '0.85rem',
                    border: `1px solid ${theme.border.primary}`,
                    borderRadius: '4px',
                    backgroundColor: theme.button.default.background,
                    color: theme.button.default.color,
                    cursor: 'pointer',
                  }}
                >
                  Sauvegarder
                </button>
              </div>
              <p style={{ whiteSpace: 'pre-wrap', margin: 0, color: theme.text.secondary }}>{variant.content}</p>
            </div>
          ))}
        </div>
      )}

      {interactions.length > 0 && (
        <div style={{ marginTop: '2rem' }}>
          <h3 style={{ color: theme.text.primary }}>Interactions générées ({interactions.length}):</h3>
          {interactions.map((interaction) => (
            <div
              key={interaction.interaction_id}
              style={{
                marginBottom: '1rem',
                padding: '1rem',
                border: `1px solid ${theme.border.primary}`,
                borderRadius: '4px',
                backgroundColor: theme.background.tertiary,
              }}
            >
              <h4 style={{ marginTop: 0, color: theme.text.primary }}>{interaction.title}</h4>
              <div style={{ fontSize: '0.9rem', color: theme.text.secondary, marginBottom: '0.5rem' }}>
                ID: {interaction.interaction_id}
                {interaction.header_tags.length > 0 && (
                  <span style={{ marginLeft: '1rem' }}>
                    Tags: {interaction.header_tags.join(', ')}
                  </span>
                )}
              </div>
              <pre style={{ 
                whiteSpace: 'pre-wrap', 
                fontSize: '0.9rem', 
                backgroundColor: theme.background.secondary, 
                color: theme.text.secondary,
                padding: '0.5rem', 
                borderRadius: '4px',
                border: `1px solid ${theme.border.primary}`,
              }}>
                {JSON.stringify(interaction.elements, null, 2)}
              </pre>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

