/**
 * Panel pour générer un nœud de dialogue avec l'IA depuis un nœud parent.
 * Permet de générer une suite ou une branche alternative.
 */
import { useState, useCallback, useEffect } from 'react'
import { useGraphStore } from '../../store/graphStore'
import { useContextStore } from '../../store/contextStore'
import { useToast } from '../shared'
import { theme } from '../../theme'
import { getErrorMessage } from '../../types/errors'
import { DEFAULT_MODEL } from '../../constants'
import * as configAPI from '../../api/config'
import type { LLMModelResponse } from '../../types/api'

interface AIGenerationPanelProps {
  parentNodeId: string | null
  onClose: () => void
  onGenerated?: () => void
}

export function AIGenerationPanel({
  parentNodeId,
  onClose,
  onGenerated,
}: AIGenerationPanelProps) {
  const { generateFromNode, isGenerating, nodes } = useGraphStore()
  const { selections } = useContextStore()
  const toast = useToast()
  
  const [userInstructions, setUserInstructions] = useState('')
  const [generationMode, setGenerationMode] = useState<'continuation' | 'branch'>('continuation')
  const [llmModel, setLlmModel] = useState<string>(DEFAULT_MODEL)
  const [maxChoices, setMaxChoices] = useState<number | null>(null)
  const [availableModels, setAvailableModels] = useState<LLMModelResponse[]>([])
  const [narrativeTags, setNarrativeTags] = useState<string[]>([])
  
  const availableNarrativeTags = ['tension', 'humour', 'dramatique', 'intime', 'révélation']
  
  // Charger les modèles disponibles
  useEffect(() => {
    configAPI.getAvailableLLMModels()
      .then((models) => {
        setAvailableModels(models)
      })
      .catch((err) => {
        console.error('Erreur lors du chargement des modèles:', err)
      })
  }, [])
  
  // Trouver le nœud parent
  const parentNode = parentNodeId ? nodes.find((n) => n.id === parentNodeId) : null
  
  // Les sélections sont déjà au bon format (ContextSelection)
  // Pas besoin de conversion, utiliser directement selections
  
  // Handler pour générer le nœud
  const handleGenerate = useCallback(async () => {
    if (!parentNodeId || !userInstructions.trim()) {
      toast('Veuillez entrer des instructions', 'warning')
      return
    }
    
    try {
      // Déterminer le speaker NPC (premier personnage sélectionné en full ou excerpt)
      const allCharacters = [
        ...(selections.characters_full || []),
        ...(selections.characters_excerpt || []),
      ]
      const npcSpeakerId = allCharacters.length > 0 ? allCharacters[0] : undefined
      
      await generateFromNode(
        parentNodeId,
        userInstructions,
        {
          context_selections: selections,
          max_choices: maxChoices,
          npc_speaker_id: npcSpeakerId,
          narrative_tags: narrativeTags.length > 0 ? narrativeTags : undefined,
          llm_model_identifier: llmModel,
        }
      )
      
      toast('Nœud généré avec succès', 'success', 2000)
      onGenerated?.()
      onClose()
    } catch (err) {
      toast(`Erreur lors de la génération: ${getErrorMessage(err)}`, 'error')
    }
  }, [
    parentNodeId,
    userInstructions,
    generationMode,
    maxChoices,
    narrativeTags,
    llmModel,
    selections,
    generateFromNode,
    toast,
    onGenerated,
    onClose,
  ])
  
  if (!parentNodeId || !parentNode) {
    return (
      <div style={{ padding: '1rem', color: theme.text.secondary }}>
        Aucun nœud parent sélectionné
      </div>
    )
  }
  
  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      height: '100%',
      padding: '1rem',
      gap: '1rem',
    }}>
      {/* En-tête */}
      <div>
        <h3 style={{ 
          margin: 0, 
          marginBottom: '0.5rem',
          color: theme.text.primary,
          fontSize: '1.1rem',
        }}>
          Générer un nœud depuis {parentNodeId}
        </h3>
        <div style={{ 
          fontSize: '0.85rem', 
          color: theme.text.secondary,
          marginBottom: '0.5rem',
        }}>
          {parentNode.data?.speaker && (
            <div>Speaker: <strong>{parentNode.data.speaker}</strong></div>
          )}
          {parentNode.data?.line && (
            <div style={{ 
              marginTop: '0.25rem',
              fontStyle: 'italic',
              maxHeight: '60px',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}>
              {parentNode.data.line.substring(0, 100)}
              {parentNode.data.line.length > 100 ? '...' : ''}
            </div>
          )}
        </div>
      </div>
      
      {/* Instructions utilisateur */}
      <div>
        <label style={{ 
          display: 'block',
          marginBottom: '0.5rem',
          fontSize: '0.9rem',
          fontWeight: 'bold',
          color: theme.text.primary,
        }}>
          Instructions pour la génération
        </label>
        <textarea
          value={userInstructions}
          onChange={(e) => setUserInstructions(e.target.value)}
          placeholder="Décrivez ce que vous voulez générer..."
          style={{
            width: '100%',
            minHeight: '100px',
            padding: '0.75rem',
            border: `1px solid ${theme.input.border}`,
            borderRadius: '6px',
            backgroundColor: theme.input.background,
            color: theme.input.color,
            fontSize: '0.9rem',
            fontFamily: 'inherit',
            resize: 'vertical',
          }}
        />
      </div>
      
      {/* Mode de génération */}
      <div>
        <label style={{ 
          display: 'block',
          marginBottom: '0.5rem',
          fontSize: '0.9rem',
          fontWeight: 'bold',
          color: theme.text.primary,
        }}>
          Mode
        </label>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            onClick={() => setGenerationMode('continuation')}
            style={{
              flex: 1,
              padding: '0.5rem',
              border: `1px solid ${generationMode === 'continuation' ? theme.button.primary.background : theme.input.border}`,
              borderRadius: '6px',
              backgroundColor: generationMode === 'continuation' ? theme.button.primary.background : theme.input.background,
              color: generationMode === 'continuation' ? theme.button.primary.color : theme.input.color,
              cursor: 'pointer',
              fontSize: '0.85rem',
            }}
          >
            Suite (nextNode)
          </button>
          <button
            onClick={() => setGenerationMode('branch')}
            style={{
              flex: 1,
              padding: '0.5rem',
              border: `1px solid ${generationMode === 'branch' ? theme.button.primary.background : theme.input.border}`,
              borderRadius: '6px',
              backgroundColor: generationMode === 'branch' ? theme.button.primary.background : theme.input.background,
              color: generationMode === 'branch' ? theme.button.primary.color : theme.input.color,
              cursor: 'pointer',
              fontSize: '0.85rem',
            }}
          >
            Branche alternative (choice)
          </button>
        </div>
      </div>
      
      {/* Options LLM */}
      <div>
        <label style={{ 
          display: 'block',
          marginBottom: '0.5rem',
          fontSize: '0.9rem',
          fontWeight: 'bold',
          color: theme.text.primary,
        }}>
          Modèle LLM
        </label>
        <select
          value={llmModel}
          onChange={(e) => setLlmModel(e.target.value)}
          style={{
            width: '100%',
            padding: '0.5rem',
            border: `1px solid ${theme.input.border}`,
            borderRadius: '6px',
            backgroundColor: theme.input.background,
            color: theme.input.color,
            fontSize: '0.9rem',
          }}
        >
          {availableModels.map((model) => (
            <option key={model.id} value={model.id}>
              {model.name} {model.provider && `(${model.provider})`}
            </option>
          ))}
        </select>
      </div>
      
      {/* Max choices */}
      <div>
        <label style={{ 
          display: 'block',
          marginBottom: '0.5rem',
          fontSize: '0.9rem',
          fontWeight: 'bold',
          color: theme.text.primary,
        }}>
          Nombre maximum de choix (optionnel)
        </label>
        <input
          type="number"
          min="1"
          max="10"
          value={maxChoices || ''}
          onChange={(e) => setMaxChoices(e.target.value ? parseInt(e.target.value, 10) : null)}
          placeholder="Laisser vide pour illimité"
          style={{
            width: '100%',
            padding: '0.5rem',
            border: `1px solid ${theme.input.border}`,
            borderRadius: '6px',
            backgroundColor: theme.input.background,
            color: theme.input.color,
            fontSize: '0.9rem',
          }}
        />
      </div>
      
      {/* Tags narratifs */}
      <div>
        <label style={{ 
          display: 'block',
          marginBottom: '0.5rem',
          fontSize: '0.9rem',
          fontWeight: 'bold',
          color: theme.text.primary,
        }}>
          Tags narratifs (optionnel)
        </label>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          {availableNarrativeTags.map((tag) => (
            <button
              key={tag}
              onClick={() => {
                setNarrativeTags((prev) =>
                  prev.includes(tag)
                    ? prev.filter((t) => t !== tag)
                    : [...prev, tag]
                )
              }}
              style={{
                padding: '0.25rem 0.75rem',
                border: `1px solid ${narrativeTags.includes(tag) ? theme.button.primary.background : theme.input.border}`,
                borderRadius: '4px',
                backgroundColor: narrativeTags.includes(tag) ? theme.button.primary.background : theme.input.background,
                color: narrativeTags.includes(tag) ? theme.button.primary.color : theme.input.color,
                cursor: 'pointer',
                fontSize: '0.8rem',
              }}
            >
              {tag}
            </button>
          ))}
        </div>
      </div>
      
      {/* Info contexte */}
      <div style={{ 
        padding: '0.75rem',
        backgroundColor: theme.background.secondary,
        borderRadius: '6px',
        fontSize: '0.85rem',
        color: theme.text.secondary,
      }}>
        <div style={{ fontWeight: 'bold', marginBottom: '0.25rem', color: theme.text.primary }}>
          Contexte sélectionné
        </div>
        <div>
          {(selections.characters_full?.length || 0) + (selections.characters_excerpt?.length || 0) > 0 && (
            <div>Personnages: {(selections.characters_full?.length || 0) + (selections.characters_excerpt?.length || 0)}</div>
          )}
          {(selections.locations_full?.length || 0) + (selections.locations_excerpt?.length || 0) > 0 && (
            <div>Lieux: {(selections.locations_full?.length || 0) + (selections.locations_excerpt?.length || 0)}</div>
          )}
          {(selections.items_full?.length || 0) + (selections.items_excerpt?.length || 0) > 0 && (
            <div>Objets: {(selections.items_full?.length || 0) + (selections.items_excerpt?.length || 0)}</div>
          )}
          {(selections.characters_full?.length || 0) + (selections.characters_excerpt?.length || 0) === 0 && 
           (selections.locations_full?.length || 0) + (selections.locations_excerpt?.length || 0) === 0 && 
           (selections.items_full?.length || 0) + (selections.items_excerpt?.length || 0) === 0 && (
            <div style={{ fontStyle: 'italic' }}>
              Aucun contexte sélectionné. Utilisez le panneau de gauche pour sélectionner des éléments.
            </div>
          )}
        </div>
      </div>
      
      {/* Actions */}
      <div style={{ 
        display: 'flex', 
        gap: '0.5rem',
        marginTop: 'auto',
        paddingTop: '1rem',
        borderTop: `1px solid ${theme.border.primary}`,
      }}>
        <button
          onClick={onClose}
          disabled={isGenerating}
          style={{
            flex: 1,
            padding: '0.75rem',
            border: `1px solid ${theme.border.primary}`,
            borderRadius: '6px',
            backgroundColor: theme.button.default.background,
            color: theme.button.default.color,
            cursor: isGenerating ? 'not-allowed' : 'pointer',
            opacity: isGenerating ? 0.6 : 1,
            fontSize: '0.9rem',
          }}
        >
          Annuler
        </button>
        <button
          onClick={handleGenerate}
          disabled={isGenerating || !userInstructions.trim()}
          style={{
            flex: 1,
            padding: '0.75rem',
            border: 'none',
            borderRadius: '6px',
            backgroundColor: theme.button.primary.background,
            color: theme.button.primary.color,
            cursor: (isGenerating || !userInstructions.trim()) ? 'not-allowed' : 'pointer',
            opacity: (isGenerating || !userInstructions.trim()) ? 0.6 : 1,
            fontWeight: 700,
            fontSize: '0.9rem',
          }}
        >
          {isGenerating ? 'Génération...' : '✨ Générer'}
        </button>
      </div>
    </div>
  )
}
