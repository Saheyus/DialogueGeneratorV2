/**
 * Panel pour éditer les propriétés d'un nœud sélectionné.
 * Version avec React Hook Form + Zod pour validation.
 */
import { memo, useEffect, useState, useCallback } from 'react'
import { useForm, FormProvider, useFormContext, useFieldArray } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useGraphStore } from '../../store/graphStore'
import { useContextStore } from '../../store/contextStore'
import { useToast, WarningBanner } from '../shared'
import { theme } from '../../theme'
import { getErrorMessage } from '../../types/errors'
import { DEFAULT_MODEL } from '../../constants'
import * as configAPI from '../../api/config'
import type { LLMModelResponse } from '../../types/api'
import {
  dialogueNodeDataSchema,
  testNodeDataSchema,
  endNodeDataSchema,
  type DialogueNodeData,
  type TestNodeData,
  type EndNodeData,
  type Choice,
} from '../../schemas/nodeEditorSchema'
import { ChoiceEditor } from './ChoiceEditor'

export const NodeEditorPanel = memo(function NodeEditorPanel() {
  const { selectedNodeId, nodes, updateNode, generateFromNode, isGenerating, setSelectedNode, autoRestoredDraft, clearAutoRestoredDraft, setShowDeleteNodeConfirm } = useGraphStore()
  const { selections } = useContextStore()
  const toast = useToast()
  
  const [showGenerationOptions, setShowGenerationOptions] = useState(false)
  const [userInstructions, setUserInstructions] = useState('')
  const [llmModel, setLlmModel] = useState<string>(DEFAULT_MODEL)
  const [availableModels, setAvailableModels] = useState<LLMModelResponse[]>([])
  const [batchProgress, setBatchProgress] = useState<{ current: number; total: number } | null>(null)
  
  // Charger les modèles disponibles
  useEffect(() => {
    configAPI.listLLMModels()
      .then((response) => {
        setAvailableModels(response.models)
      })
      .catch((err) => {
        console.error('Erreur lors du chargement des modèles:', err)
      })
  }, [])
  
  const selectedNode = nodes.find((n) => n.id === selectedNodeId)
  
  const nodeType = selectedNode?.type || 'dialogueNode'
  
  // Déterminer le schéma selon le type de nœud
  const schema = nodeType === 'dialogueNode'
    ? dialogueNodeDataSchema
    : nodeType === 'testNode'
    ? testNodeDataSchema
    : endNodeDataSchema
  
  const form = useForm<DialogueNodeData | TestNodeData | EndNodeData>({
    resolver: zodResolver(schema),
    defaultValues: nodeType === 'dialogueNode'
      ? {
          id: selectedNode?.id || '',
          speaker: selectedNode?.data?.speaker || '',
          line: selectedNode?.data?.line || '',
          choices: (selectedNode?.data?.choices || []) as Choice[],
          nextNode: selectedNode?.data?.nextNode || '',
        }
      : nodeType === 'testNode'
      ? {
          id: selectedNode?.id || '',
          test: selectedNode?.data?.test || '',
          line: selectedNode?.data?.line || '',
          criticalFailureNode: selectedNode?.data?.criticalFailureNode || '',
          failureNode: selectedNode?.data?.failureNode || '',
          successNode: selectedNode?.data?.successNode || '',
          criticalSuccessNode: selectedNode?.data?.criticalSuccessNode || '',
        }
      : {
          id: selectedNode?.id || '',
        },
    mode: 'onChange',
  })
  
  const { register, handleSubmit, formState: { errors }, reset, watch } = form
  
  // Synchroniser avec le nœud sélectionné
  useEffect(() => {
    if (selectedNode?.data) {
      if (nodeType === 'dialogueNode') {
        const choices = (selectedNode.data.choices || []) as Choice[]
        
        reset({
          id: selectedNode.id,
          speaker: selectedNode.data.speaker || '',
          line: selectedNode.data.line || '',
          choices,
          nextNode: selectedNode.data.nextNode || '',
        })
      } else if (nodeType === 'testNode') {
        reset({
          id: selectedNode.id,
          test: selectedNode.data.test || '',
          line: selectedNode.data.line || '',
          criticalFailureNode: selectedNode.data.criticalFailureNode || '',
          failureNode: selectedNode.data.failureNode || '',
          successNode: selectedNode.data.successNode || '',
          criticalSuccessNode: selectedNode.data.criticalSuccessNode || '',
        })
      } else {
        reset({
          id: selectedNode.id,
        })
      }
    }
  }, [selectedNode, nodeType, reset])
  
  const onSubmit = (data: DialogueNodeData | TestNodeData | EndNodeData) => {
    if (!selectedNodeId) return
    
    updateNode(selectedNodeId, {
      data: {
        ...selectedNode?.data,
        ...data,
      },
    })
  }
  
  const handleDelete = () => {
    if (!selectedNodeId) return
    setShowDeleteNodeConfirm(true)
  }
  
  // Handler pour générer la suite (nextNode)
  const handleGenerateNext = useCallback(async () => {
    if (!selectedNodeId) {
      toast('Aucun nœud sélectionné', 'warning')
      return
    }
    
    // Vérifier si le nœud a des choix : en mode nextNode, il faut sélectionner au moins un choix
    const nodeChoices = selectedNode?.data?.choices || []
    if (nodeChoices.length > 0) {
      // Si le nœud a des choix, il faut utiliser le panneau AIGenerationPanel pour sélectionner un choix
      toast('Ce nœud a des choix. Utilisez le bouton "Générer la suite avec l\'IA" pour sélectionner un choix spécifique.', 'warning')
      return
    }
    
    try {
      const allCharacters = [
        ...(selections.characters_full || []),
        ...(selections.characters_excerpt || []),
      ]
      const npcSpeakerId = allCharacters.length > 0 ? allCharacters[0] : undefined
      
      // Si les instructions sont vides, on utilisera un texte par défaut côté backend
      const finalInstructions = userInstructions.trim() || "Ecris la réponse du PNJ à ce que dit le PJ"
      
      const generationResult = await generateFromNode(
        selectedNodeId,
        finalInstructions,
        {
          context_selections: selections,
          npc_speaker_id: npcSpeakerId,
          llm_model_identifier: llmModel,
        }
      )
      
      toast('Nœud généré avec succès', 'success', 2000)
      
      // Focus automatique vers le nouveau nœud
      if (generationResult.nodeId) {
        setSelectedNode(generationResult.nodeId)
        const event = new CustomEvent('focus-generated-node', {
          detail: { nodeId: generationResult.nodeId }
        })
        window.dispatchEvent(event)
      }
      
      setShowGenerationOptions(false)
      setUserInstructions('')
    } catch (err) {
      toast(`Erreur lors de la génération: ${getErrorMessage(err)}`, 'error')
    }
  }, [selectedNodeId, userInstructions, selections, llmModel, generateFromNode, setSelectedNode, toast])
  
  // Handler pour générer pour un choix spécifique
  const handleGenerateForChoice = useCallback(async (choiceIndex: number) => {
    if (!selectedNodeId) return
    
    // Si pas d'instructions, utiliser un prompt par défaut
    const instructions = userInstructions.trim() || 'Continue la conversation de manière naturelle'
    
    try {
      const allCharacters = [
        ...(selections.characters_full || []),
        ...(selections.characters_excerpt || []),
      ]
      const npcSpeakerId = allCharacters.length > 0 ? allCharacters[0] : undefined
      
      const generationResult = await generateFromNode(
        selectedNodeId,
        instructions,
        {
          context_selections: selections,
          npc_speaker_id: npcSpeakerId,
          llm_model_identifier: llmModel,
          target_choice_index: choiceIndex,
        }
      )
      
      toast('Nœud généré avec succès', 'success', 2000)
      
      // Focus automatique vers le nouveau nœud
      if (generationResult.nodeId) {
        setSelectedNode(generationResult.nodeId)
        const event = new CustomEvent('focus-generated-node', {
          detail: { nodeId: generationResult.nodeId }
        })
        window.dispatchEvent(event)
      }
      
      setShowGenerationOptions(false)
      setUserInstructions('')
    } catch (err) {
      toast(`Erreur lors de la génération: ${getErrorMessage(err)}`, 'error')
    }
  }, [selectedNodeId, userInstructions, selections, llmModel, generateFromNode, setSelectedNode, toast])
  
  // Handler pour générer pour tous les choix
  const handleGenerateAllChoices = useCallback(async () => {
    if (!selectedNodeId) {
      toast('Aucun nœud sélectionné', 'warning')
      return
    }
    
    try {
      const allCharacters = [
        ...(selections.characters_full || []),
        ...(selections.characters_excerpt || []),
      ]
      const npcSpeakerId = allCharacters.length > 0 ? allCharacters[0] : undefined
      
      // Si les instructions sont vides, on utilisera un texte par défaut côté backend
      const finalInstructions = userInstructions.trim() || "Ecris la réponse du PNJ à ce que dit le PJ"
      
      const generationResult = await generateFromNode(
        selectedNodeId,
        finalInstructions,
        {
          context_selections: selections,
          npc_speaker_id: npcSpeakerId,
          llm_model_identifier: llmModel,
          generate_all_choices: true,
          onBatchProgress: (current: number, total: number) => {
            setBatchProgress({ current, total })
          },
        }
      )
      
      toast('Nœuds générés avec succès', 'success', 2000)
      
      // Focus automatique vers le premier nouveau nœud
      if (generationResult.nodeId) {
        setSelectedNode(generationResult.nodeId)
        const event = new CustomEvent('focus-generated-node', {
          detail: { nodeId: generationResult.nodeId }
        })
        window.dispatchEvent(event)
      }
      
      setShowGenerationOptions(false)
      setUserInstructions('')
    } catch (err) {
      toast(`Erreur lors de la génération: ${getErrorMessage(err)}`, 'error')
    } finally {
      setBatchProgress(null)
    }
  }, [selectedNodeId, userInstructions, selections, llmModel, generateFromNode, setSelectedNode, toast])
  
  // Handler pour charger le fichier plus ancien (doit être avant le return conditionnel)
  const handleLoadOlderFile = useCallback(() => {
    // Émettre un événement pour que GraphEditor charge le fichier plus ancien
    const event = new CustomEvent('load-older-file')
    window.dispatchEvent(event)
    clearAutoRestoredDraft()
  }, [clearAutoRestoredDraft])
  
  if (!selectedNode) {
    return (
      <div
        style={{
          padding: '2rem 1rem',
          textAlign: 'center',
          color: theme.text.secondary,
        }}
      >
        Sélectionnez un nœud dans le graphe pour l'éditer
      </div>
    )
  }
  
  const choices = watch('choices') as Choice[] | undefined

  return (
    <FormProvider {...form}>
      <form
        onSubmit={handleSubmit(onSubmit)}
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem',
          height: '100%',
          overflow: 'auto',
        }}
      >
        {/* Bandeau d'avertissement pour brouillon restauré automatiquement */}
        {autoRestoredDraft && (
          <WarningBanner
            message={`Brouillon local plus récent (${new Date(autoRestoredDraft.timestamp).toLocaleString()}) restauré automatiquement. Fichier sur disque plus ancien (${new Date(autoRestoredDraft.fileTimestamp).toLocaleString()}).`}
            actionLabel="Charger le fichier plus ancien"
            onAction={handleLoadOlderFile}
            onDismiss={() => clearAutoRestoredDraft()}
          />
        )}
        
        {/* ID du nœud (readonly) */}
        <div>
          <label
            style={{
              display: 'block',
              marginBottom: '0.5rem',
              fontSize: '0.85rem',
              fontWeight: 'bold',
              color: theme.text.secondary,
            }}
          >
            ID du nœud
          </label>
          <input
            type="text"
            {...register('id')}
            readOnly
            style={{
              width: '100%',
              padding: '0.5rem',
              border: `1px solid ${theme.border.primary}`,
              borderRadius: 4,
              backgroundColor: theme.background.panel,
              color: theme.text.secondary,
              fontSize: '0.9rem',
              fontFamily: 'monospace',
            }}
          />
        </div>
        
        {/* Type de nœud */}
        <div>
          <label
            style={{
              display: 'block',
              marginBottom: '0.5rem',
              fontSize: '0.85rem',
              fontWeight: 'bold',
              color: theme.text.secondary,
            }}
          >
            Type
          </label>
          <input
            type="text"
            value={nodeType}
            readOnly
            style={{
              width: '100%',
              padding: '0.5rem',
              border: `1px solid ${theme.border.primary}`,
              borderRadius: 4,
              backgroundColor: theme.background.panel,
              color: theme.text.secondary,
              fontSize: '0.9rem',
            }}
          />
        </div>
        
        {/* Speaker (pour dialogue nodes) */}
        {nodeType === 'dialogueNode' && (
          <div>
            <label
              style={{
                display: 'block',
                marginBottom: '0.5rem',
                fontSize: '0.85rem',
                fontWeight: 'bold',
                color: theme.text.primary,
              }}
            >
              Speaker
            </label>
            <input
              type="text"
              {...register('speaker')}
              placeholder="Nom du personnage"
              style={{
                width: '100%',
                padding: '0.5rem',
                border: `1px solid ${errors.speaker ? theme.state.error.border : theme.border.primary}`,
                borderRadius: 4,
                backgroundColor: theme.background.tertiary,
                color: theme.text.primary,
                fontSize: '0.9rem',
              }}
            />
          </div>
        )}
        
        {/* Line (dialogue) */}
        {(nodeType === 'dialogueNode' || nodeType === 'testNode') && (
          <div>
            <label
              style={{
                display: 'block',
                marginBottom: '0.5rem',
                fontSize: '0.85rem',
                fontWeight: 'bold',
                color: theme.text.primary,
              }}
            >
              Dialogue
            </label>
            <textarea
              {...register('line')}
              placeholder="Texte du dialogue..."
              rows={9}
              style={{
                width: '100%',
                padding: '0.5rem',
                border: `1px solid ${errors.line ? theme.state.error.border : theme.border.primary}`,
                borderRadius: 4,
                backgroundColor: theme.background.tertiary,
                color: theme.text.primary,
                fontSize: '0.9rem',
                fontFamily: 'inherit',
                resize: 'vertical',
              }}
            />
          </div>
        )}
        
        {/* Test (pour test nodes) */}
        {nodeType === 'testNode' && (
          <div>
            <label
              style={{
                display: 'block',
                marginBottom: '0.5rem',
                fontSize: '0.85rem',
                fontWeight: 'bold',
                color: theme.text.primary,
              }}
            >
              Test d'attribut *
            </label>
            <input
              type="text"
              {...register('test', { required: true })}
              placeholder="Format: Attribut+Compétence:DD"
              style={{
                width: '100%',
                padding: '0.5rem',
                border: `1px solid ${errors.test ? theme.state.error.border : theme.border.primary}`,
                borderRadius: 4,
                backgroundColor: theme.background.tertiary,
                color: theme.text.primary,
                fontSize: '0.9rem',
                fontFamily: 'monospace',
              }}
            />
            {errors.test && (
              <div style={{ marginTop: '0.25rem', fontSize: '0.75rem', color: theme.state.error.color }}>
                {errors.test.message}
              </div>
            )}
            <div
              style={{
                marginTop: '0.25rem',
                fontSize: '0.75rem',
                color: theme.text.secondary,
                fontStyle: 'italic',
              }}
            >
              Ex: Raison+Rhétorique:8
            </div>
          </div>
        )}
        
        {/* Résultats de test (pour test nodes) */}
        {nodeType === 'testNode' && (
          <div style={{ marginBottom: '0.75rem', padding: '0.75rem', backgroundColor: theme.background.secondary, borderRadius: 6, border: `1px solid ${theme.border.primary}` }}>
            <h5 style={{ margin: '0 0 0.75rem 0', fontSize: '0.85rem', fontWeight: 'bold', color: theme.text.primary }}>
              Connexions de test
            </h5>
            
            {/* Échec critique */}
            <div style={{ marginBottom: '0.75rem' }}>
              <label
                htmlFor="test-critical-failure-node"
                style={{
                  display: 'block',
                  marginBottom: '0.5rem',
                  fontSize: '0.85rem',
                  fontWeight: 'bold',
                  color: theme.text.secondary,
                }}
              >
                Échec critique
              </label>
              <input
                id="test-critical-failure-node"
                type="text"
                {...register('criticalFailureNode' as const)}
                placeholder="ID du nœud (ex: NODE_CRITICAL_FAILURE)"
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: `1px solid ${theme.border.primary}`,
                  borderRadius: 4,
                  backgroundColor: theme.background.tertiary,
                  color: theme.text.primary,
                  fontSize: '0.85rem',
                  fontFamily: 'monospace',
                }}
              />
            </div>
            
            {/* Échec */}
            <div style={{ marginBottom: '0.75rem' }}>
              <label
                htmlFor="test-failure-node"
                style={{
                  display: 'block',
                  marginBottom: '0.5rem',
                  fontSize: '0.85rem',
                  fontWeight: 'bold',
                  color: theme.text.secondary,
                }}
              >
                Échec
              </label>
              <input
                id="test-failure-node"
                type="text"
                {...register('failureNode' as const)}
                placeholder="ID du nœud (ex: NODE_FAILURE)"
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: `1px solid ${theme.border.primary}`,
                  borderRadius: 4,
                  backgroundColor: theme.background.tertiary,
                  color: theme.text.primary,
                  fontSize: '0.85rem',
                  fontFamily: 'monospace',
                }}
              />
            </div>
            
            {/* Réussite */}
            <div style={{ marginBottom: '0.75rem' }}>
              <label
                htmlFor="test-success-node"
                style={{
                  display: 'block',
                  marginBottom: '0.5rem',
                  fontSize: '0.85rem',
                  fontWeight: 'bold',
                  color: theme.text.secondary,
                }}
              >
                Réussite
              </label>
              <input
                id="test-success-node"
                type="text"
                {...register('successNode' as const)}
                placeholder="ID du nœud (ex: NODE_SUCCESS)"
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: `1px solid ${theme.border.primary}`,
                  borderRadius: 4,
                  backgroundColor: theme.background.tertiary,
                  color: theme.text.primary,
                  fontSize: '0.85rem',
                  fontFamily: 'monospace',
                }}
              />
            </div>
            
            {/* Réussite critique */}
            <div style={{ marginBottom: '0.75rem' }}>
              <label
                htmlFor="test-critical-success-node"
                style={{
                  display: 'block',
                  marginBottom: '0.5rem',
                  fontSize: '0.85rem',
                  fontWeight: 'bold',
                  color: theme.text.secondary,
                }}
              >
                Réussite critique
              </label>
              <input
                id="test-critical-success-node"
                type="text"
                {...register('criticalSuccessNode' as const)}
                placeholder="ID du nœud (ex: NODE_CRITICAL_SUCCESS)"
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: `1px solid ${theme.border.primary}`,
                  borderRadius: 4,
                  backgroundColor: theme.background.tertiary,
                  color: theme.text.primary,
                  fontSize: '0.85rem',
                  fontFamily: 'monospace',
                }}
              />
            </div>
          </div>
        )}
        
        {/* Choix (pour dialogue nodes) */}
        {nodeType === 'dialogueNode' && (
          <ChoicesEditor onGenerateForChoice={handleGenerateForChoice} />
        )}
        
        {/* Section Génération IA */}
        {nodeType === 'dialogueNode' && (
          <div
            style={{
              padding: '1rem',
              backgroundColor: theme.background.secondary,
              borderRadius: 6,
              border: `1px solid ${theme.border.primary}`,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <h3 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 'bold', color: theme.text.primary }}>
                ✨ Génération IA
              </h3>
              <button
                type="button"
                onClick={() => setShowGenerationOptions(!showGenerationOptions)}
                style={{
                  padding: '0.5rem 0.75rem',
                  border: `1px solid ${theme.border.primary}`,
                  borderRadius: 4,
                  backgroundColor: showGenerationOptions ? theme.button.primary.background : theme.button.default.background,
                  color: showGenerationOptions ? theme.button.primary.color : theme.button.default.color,
                  cursor: 'pointer',
                  fontSize: '0.85rem',
                }}
              >
                {showGenerationOptions ? 'Masquer' : 'Afficher'}
              </button>
            </div>
            
            {showGenerationOptions && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {/* Instructions */}
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem', fontWeight: 'bold', color: theme.text.primary }}>
                    Instructions pour la génération
                  </label>
                  <textarea
                    value={userInstructions}
                    onChange={(e) => setUserInstructions(e.target.value)}
                    placeholder="Décrivez ce que vous voulez générer..."
                    rows={3}
                    style={{
                      width: '100%',
                      padding: '0.5rem',
                      border: `1px solid ${theme.border.primary}`,
                      borderRadius: 4,
                      backgroundColor: theme.background.tertiary,
                      color: theme.text.primary,
                      fontSize: '0.9rem',
                      fontFamily: 'inherit',
                      resize: 'vertical',
                    }}
                  />
                </div>
                
                {/* Modèle LLM */}
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.85rem', fontWeight: 'bold', color: theme.text.primary }}>
                    Modèle LLM
                  </label>
                  <select
                    value={llmModel}
                    onChange={(e) => setLlmModel(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.5rem',
                      border: `1px solid ${theme.border.primary}`,
                      borderRadius: 4,
                      backgroundColor: theme.background.tertiary,
                      color: theme.text.primary,
                      fontSize: '0.9rem',
                    }}
                  >
                    {availableModels.map((model, index) => (
                      <option key={`${model.model_identifier}-${index}-${model.display_name || ''}`} value={model.model_identifier}>
                        {model.display_name || model.model_identifier}
                      </option>
                    ))}
                  </select>
                </div>
                
                {/* Boutons de génération */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {/* Bouton "Générer la suite" (nextNode) */}
                  <button
                    type="button"
                    onClick={handleGenerateNext}
                    disabled={isGenerating}
                    style={{
                      width: '100%',
                      padding: '0.75rem',
                      border: 'none',
                      borderRadius: 4,
                      backgroundColor: theme.button.primary.background,
                      color: theme.button.primary.color,
                      cursor: isGenerating ? 'not-allowed' : 'pointer',
                      opacity: isGenerating ? 0.6 : 1,
                      fontSize: '0.9rem',
                      fontWeight: 'bold',
                    }}
                  >
                    {isGenerating ? 'Génération...' : '✨ Générer la suite (nextNode)'}
                  </button>
                  
                  {/* Bouton "Générer pour tous les choix" si plusieurs choix sans targetNode */}
                  {(() => {
                    const unconnectedChoices = (choices || []).filter(
                      (choice: Choice) => !choice.targetNode || choice.targetNode === 'END'
                    )
                    return unconnectedChoices.length > 1 ? (
                      <button
                        type="button"
                        onClick={handleGenerateAllChoices}
                        disabled={isGenerating}
                        style={{
                          width: '100%',
                          padding: '0.75rem',
                          border: `1px solid ${theme.border.primary}`,
                          borderRadius: 4,
                          backgroundColor: theme.button.default.background,
                          color: theme.button.default.color,
                          cursor: isGenerating ? 'not-allowed' : 'pointer',
                          opacity: isGenerating ? 0.6 : 1,
                          fontSize: '0.9rem',
                        }}
                      >
                        {isGenerating
                          ? batchProgress?.total
                            ? `Génération ${batchProgress.current}/${batchProgress.total}...`
                            : 'Génération batch...'
                          : `✨ Générer pour tous les choix (${unconnectedChoices.length})`}
                      </button>
                    ) : null
                  })()}
                </div>
              </div>
            )}
          </div>
        )}
        
        {/* Actions */}
        <div
          style={{
            display: 'flex',
            gap: '0.5rem',
            marginTop: 'auto',
            paddingTop: '1rem',
          }}
        >
          <button
            type="submit"
            style={{
              flex: 1,
              padding: '0.75rem',
              border: 'none',
              borderRadius: 4,
              backgroundColor: theme.button.primary.background,
              color: theme.button.primary.color,
              cursor: 'pointer',
              fontSize: '0.9rem',
              fontWeight: 'bold',
            }}
          >
            💾
          </button>
          
          <button
            type="button"
            onClick={handleDelete}
            style={{
              padding: '0.75rem',
              border: `1px solid ${theme.border.primary}`,
              borderRadius: 4,
              backgroundColor: '#E74C3C',
              color: 'white',
              cursor: 'pointer',
              fontSize: '0.9rem',
              fontWeight: 'bold',
            }}
          >
            🗑️
          </button>
        </div>
      </form>
    </FormProvider>
  )
})

/**
 * Composant interne pour gérer les choix avec useFieldArray.
 */
interface ChoicesEditorProps {
  onGenerateForChoice?: (choiceIndex: number) => void
}

function ChoicesEditor({ onGenerateForChoice }: ChoicesEditorProps) {
  const { control, watch } = useFormContext<DialogueNodeData>()
  const { fields, append, remove } = useFieldArray({
    control,
    name: 'choices',
  })
  
  // choices non utilisé directement - gardé pour usage futur si nécessaire
  // const choices = watch('choices') || []
  
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
        <label
          style={{
            display: 'block',
            fontSize: '0.85rem',
            fontWeight: 'bold',
            color: theme.text.primary,
          }}
        >
          Choix ({fields.length})
        </label>
        <button
          type="button"
          onClick={() => append({ text: '', targetNode: 'END' })}
          style={{
            padding: '0.5rem 0.75rem',
            border: `1px solid ${theme.border.primary}`,
            borderRadius: 4,
            backgroundColor: theme.button.default.background,
            color: theme.button.default.color,
            cursor: 'pointer',
            fontSize: '0.85rem',
          }}
        >
          + Ajouter un choix
        </button>
      </div>
      
      {fields.length === 0 ? (
        <div
          style={{
            padding: '1rem',
            backgroundColor: theme.background.panel,
            borderRadius: 4,
            border: `1px dashed ${theme.border.primary}`,
            textAlign: 'center',
            color: theme.text.secondary,
            fontSize: '0.85rem',
          }}
        >
          Aucun choix. Cliquez sur "Ajouter un choix" pour en créer un.
        </div>
      ) : (
        fields.map((field, index) => (
          <ChoiceEditor
            key={field.id}
            choiceIndex={index}
            onRemove={fields.length > 1 ? () => remove(index) : undefined}
            onGenerateForChoice={onGenerateForChoice}
          />
        ))
      )}
    </div>
  )
}
