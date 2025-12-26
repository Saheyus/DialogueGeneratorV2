/**
 * Panneau de génération de dialogues.
 */
import { useState, useEffect, useCallback, useRef } from 'react'
import * as dialoguesAPI from '../../api/dialogues'
import * as configAPI from '../../api/config'
import * as interactionsAPI from '../../api/interactions'
import { useContextStore } from '../../store/contextStore'
import { useGenerationStore } from '../../store/generationStore'
import { useGenerationActionsStore } from '../../store/generationActionsStore'
import { getErrorMessage } from '../../types/errors'
import { theme } from '../../theme'
import type {
  GenerateDialogueVariantsRequest,
  GenerateInteractionVariantsRequest,
  DialogueVariantResponse,
  InteractionResponse,
  LLMModelResponse,
  InteractionListResponse,
  ContextSelection,
  GenerateDialogueVariantsResponse,
  GenerateUnityDialogueRequest,
  GenerateUnityDialogueResponse,
} from '../../types/api'
import { DialogueStructureWidget } from './DialogueStructureWidget'
import { SystemPromptEditor } from './SystemPromptEditor'
import { SceneSelectionWidget } from './SceneSelectionWidget'
import { VariantsTabsView } from './VariantsTabsView'
import { InteractionsTab } from './InteractionsTab'
import { Tabs, type Tab } from '../shared/Tabs'
import { ContextActions } from '../context/ContextActions'
import { ContextSummaryChips, useToast, toastManager } from '../shared'

type GenerationMode = 'variants' | 'interactions' | 'unity'
type PanelTab = 'generation' | 'interactions'

export function GenerationPanel() {
  const { 
    selections, 
    selectedRegion, 
    selectedSubLocations,
    setSelections,
    setRegion,
    restoreState: restoreContextState,
  } = useContextStore()
  const {
    sceneSelection,
    dialogueStructure,
    systemPromptOverride,
    setDialogueStructure,
    setSystemPromptOverride,
    setEstimatedPrompt,
    setSceneSelection,
    setVariantsResponse: setStoreVariantsResponse,
    setInteractionsResponse: setStoreInteractionsResponse,
    setTokensUsed,
  } = useGenerationStore()
  
  const [generationMode, setGenerationMode] = useState<GenerationMode>('unity')
  const [userInstructions, setUserInstructions] = useState('')
  const [kVariants, setKVariants] = useState(2)
  const [maxContextTokens, setMaxContextTokens] = useState(1500)
  const [llmModel, setLlmModel] = useState('gpt-4o-mini')
  const [maxChoices, setMaxChoices] = useState<number | null>(null)
  const [availableModels, setAvailableModels] = useState<LLMModelResponse[]>([])
  const [variantsResponse, setVariantsResponse] = useState<GenerateDialogueVariantsResponse | null>(null)
  const [interactions, setInteractions] = useState<InteractionResponse[]>([])
  const [estimatedTokens, setEstimatedTokens] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isEstimating, setIsEstimating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [previousInteractionId, setPreviousInteractionId] = useState<string>('')
  const [availableInteractions, setAvailableInteractions] = useState<InteractionResponse[]>([])
  const [activePanelTab, setActivePanelTab] = useState<PanelTab>('generation')
  const [isDirty, setIsDirty] = useState(false)
  const [npcSpeakerId, setNpcSpeakerId] = useState<string>('')
  const toast = useToast()

  // Sauvegarde automatique très fréquente (toutes les 2 secondes)
  const DRAFT_STORAGE_KEY = 'generation_draft'
  
  const saveDraft = useCallback(() => {
    const draft = {
      userInstructions,
      systemPromptOverride,
      dialogueStructure,
      sceneSelection,
      kVariants,
      maxContextTokens,
      llmModel,
      generationMode,
      previousInteractionId,
      npcSpeakerId,
      maxChoices,
      contextSelections: selections,
      selectedRegion,
      selectedSubLocations,
      timestamp: Date.now(),
    }
    try {
      localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(draft))
      setIsDirty(false)
    } catch (err) {
      console.error('Erreur lors de la sauvegarde automatique:', err)
    }
  }, [userInstructions, systemPromptOverride, dialogueStructure, sceneSelection, kVariants, maxContextTokens, llmModel, maxChoices, generationMode, previousInteractionId, npcSpeakerId, selections, selectedRegion, selectedSubLocations])

  // Charger le brouillon au démarrage (AVANT loadModels pour préserver le modèle sauvegardé)
  useEffect(() => {
    try {
      const saved = localStorage.getItem(DRAFT_STORAGE_KEY)
      if (saved) {
        const draft = JSON.parse(saved)
        if (draft.userInstructions !== undefined) setUserInstructions(draft.userInstructions)
        if (draft.systemPromptOverride !== undefined) setSystemPromptOverride(draft.systemPromptOverride)
        if (draft.dialogueStructure !== undefined) setDialogueStructure(draft.dialogueStructure)
        if (draft.sceneSelection !== undefined) {
          setSceneSelection(draft.sceneSelection)
        }
        if (draft.kVariants !== undefined) setKVariants(draft.kVariants)
        if (draft.maxContextTokens !== undefined) setMaxContextTokens(draft.maxContextTokens)
        if (draft.llmModel !== undefined) setLlmModel(draft.llmModel)
        if (draft.maxChoices !== undefined) setMaxChoices(draft.maxChoices)
        if (draft.generationMode !== undefined) {
          setGenerationMode(draft.generationMode)
        } else {
          // Mode par défaut : Unity
          setGenerationMode('unity')
        }
        if (draft.previousInteractionId !== undefined) setPreviousInteractionId(draft.previousInteractionId)
        if (draft.npcSpeakerId !== undefined) setNpcSpeakerId(draft.npcSpeakerId)
        // Charger les sélections de contexte
        if (draft.contextSelections !== undefined) {
          const savedRegion = draft.selectedRegion !== undefined ? draft.selectedRegion : null
          const savedSubLocations = draft.selectedSubLocations !== undefined && Array.isArray(draft.selectedSubLocations) 
            ? draft.selectedSubLocations 
            : []
          restoreContextState(draft.contextSelections, savedRegion, savedSubLocations)
        }
        setIsDirty(false)
      }
    } catch (err) {
      console.error('Erreur lors du chargement du brouillon:', err)
    }
  }, [setDialogueStructure, setSystemPromptOverride, setSceneSelection, restoreContextState]) // Charger une seule fois au montage

  // Détecter les changements de sceneSelection pour déclencher la sauvegarde
  // (sauf au chargement initial)
  const [isInitialLoad, setIsInitialLoad] = useState(true)
  useEffect(() => {
    if (!isInitialLoad) {
      setIsDirty(true)
    }
  }, [sceneSelection, isInitialLoad])

  // Détecter les changements dans les sélections de contexte pour déclencher la sauvegarde
  useEffect(() => {
    if (!isInitialLoad) {
      setIsDirty(true)
    }
  }, [selections, selectedRegion, selectedSubLocations, isInitialLoad])
  
  useEffect(() => {
    // Marquer la fin du chargement initial après un court délai
    const timer = setTimeout(() => setIsInitialLoad(false), 1000)
    return () => clearTimeout(timer)
  }, [])

  // Sauvegarde automatique avec debounce (toutes les 2 secondes)
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (isDirty) {
        saveDraft()
      }
    }, 2000) // Sauvegarder 2 secondes après le dernier changement

    return () => clearTimeout(timeoutId)
  }, [isDirty, saveDraft])

  const loadModels = useCallback(async () => {
    try {
      const response = await configAPI.listLLMModels()
      setAvailableModels(response.models)
      // Ne pas écraser le modèle si un draft existe avec un modèle sauvegardé
      const saved = localStorage.getItem(DRAFT_STORAGE_KEY)
      if (saved) {
        try {
          const draft = JSON.parse(saved)
          if (draft.llmModel && response.models.some(m => m.model_identifier === draft.llmModel)) {
            // Le modèle sauvegardé existe toujours, on le garde (déjà chargé par le useEffect du draft)
            return
          }
        } catch {
          // Ignorer les erreurs de parsing, continuer avec le modèle par défaut
        }
      }
      // Sinon, utiliser le premier modèle disponible seulement si aucun modèle n'est déjà défini
      if (response.models.length > 0 && !llmModel) {
        setLlmModel(response.models[0].model_identifier)
      }
    } catch (err) {
      console.error('Erreur lors du chargement des modèles:', err)
    }
  }, [llmModel])

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

  // Construire context_selections avec scene_protagonists, scene_location, et generation_settings
  const buildContextSelections = useCallback((): ContextSelection => {
    const contextSelections: ContextSelection = {
      ...selections,
    }

    // Ajouter scene_protagonists
    const sceneProtagonists: Record<string, string> = {}
    if (sceneSelection.characterA) {
      sceneProtagonists.personnage_a = sceneSelection.characterA
    }
    if (sceneSelection.characterB) {
      sceneProtagonists.personnage_b = sceneSelection.characterB
    }
    if (Object.keys(sceneProtagonists).length > 0) {
      contextSelections.scene_protagonists = sceneProtagonists
    }

    // Ajouter scene_location
    const sceneLocation: Record<string, string> = {}
    if (sceneSelection.sceneRegion) {
      sceneLocation.lieu = sceneSelection.sceneRegion
    }
    if (sceneSelection.subLocation) {
      sceneLocation.sous_lieu = sceneSelection.subLocation
    }
    if (Object.keys(sceneLocation).length > 0) {
      contextSelections.scene_location = sceneLocation
    }

    // Ajouter generation_settings avec dialogue_structure
    if (dialogueStructure && dialogueStructure.length > 0) {
      contextSelections.generation_settings = {
        dialogue_structure: dialogueStructure,
      }
    }

    return contextSelections
  }, [selections, sceneSelection, dialogueStructure])

  const estimateTokens = useCallback(async () => {
    // Permettre l'estimation si on a au moins : instructions, sélections, ou un system prompt
    const hasSystemPrompt = systemPromptOverride && systemPromptOverride.trim().length > 0
    if (!userInstructions.trim() && !hasSelections() && !hasSystemPrompt) {
      setEstimatedTokens(null)
      setEstimatedPrompt(null, null, false)
      return
    }

    setIsEstimating(true)
    setEstimatedPrompt(null, null, true)
    try {
      const contextSelections = buildContextSelections()
      const response = await dialoguesAPI.estimateTokens(
        contextSelections,
        userInstructions,
        maxContextTokens,
        systemPromptOverride
      )
      setEstimatedTokens(response.total_estimated_tokens)
      setEstimatedPrompt(response.estimated_prompt || null, response.total_estimated_tokens, false)
    } catch (err: any) {
      // Ne logger que les erreurs non liées à la connexion (backend non accessible)
      // Les erreurs de connexion sont normales si le backend n'est pas encore démarré
      if (err?.code !== 'ERR_NETWORK' && err?.code !== 'ECONNREFUSED' && err?.response?.status !== 401) {
        console.error('Erreur lors de l\'estimation:', err)
      }
      setEstimatedTokens(null)
      setEstimatedPrompt(null, null, false)
    } finally {
      setIsEstimating(false)
    }
  }, [userInstructions, hasSelections, maxContextTokens, buildContextSelections, setEstimatedPrompt, systemPromptOverride])

  useEffect(() => {
    // Estimer les tokens quand les sélections, les instructions ou le system prompt changent
    const hasAnySelections = 
      selections.characters.length > 0 ||
      selections.locations.length > 0 ||
      selections.items.length > 0 ||
      selections.species.length > 0 ||
      selections.communities.length > 0 ||
      selections.dialogues_examples.length > 0
    
    const hasSystemPrompt = systemPromptOverride && systemPromptOverride.trim().length > 0
    
    const timeoutId = setTimeout(() => {
      if (userInstructions.trim() || hasAnySelections || hasSystemPrompt) {
        estimateTokens()
      } else {
        setEstimatedTokens(null)
        setEstimatedPrompt(null, null, false)
      }
    }, 500)

    return () => clearTimeout(timeoutId)
  }, [userInstructions, selections.characters, selections.locations, selections.items, selections.species, selections.communities, selections.dialogues_examples, maxContextTokens, estimateTokens, sceneSelection, dialogueStructure, systemPromptOverride, setEstimatedPrompt])

  const handleGenerate = useCallback(async () => {
    // Validation minimale
    if (!sceneSelection.characterA && !sceneSelection.characterB && !userInstructions.trim()) {
      toast('Veuillez sélectionner au moins un personnage ou ajouter des instructions', 'error')
      return
    }

    setIsLoading(true)
    setError(null)
    // Toast sans durée (0) pour qu'il reste affiché pendant la génération
    const toastId = toast('Génération en cours...', 'info', 0)

    try {
      const contextSelections = buildContextSelections()
      // Log pour déboguer les personnages sélectionnés
      console.log('Context selections envoyés:', contextSelections)
      console.log('Personnages dans contextSelections:', contextSelections.characters)
      
      // Calculer les tokens envoyés avant la génération
      let tokensSent = 0
      try {
        const estimateResponse = await dialoguesAPI.estimateTokens(
          contextSelections,
          userInstructions,
          maxContextTokens,
          systemPromptOverride
        )
        tokensSent = estimateResponse.total_estimated_tokens
        setTokensUsed(tokensSent)
      } catch (err) {
        console.warn('Impossible d\'estimer les tokens:', err)
      }
      
      if (generationMode === 'variants') {
        const request: GenerateDialogueVariantsRequest = {
          k_variants: kVariants,
          user_instructions: userInstructions,
          context_selections: contextSelections,
          max_context_tokens: maxContextTokens,
          structured_output: false,
          system_prompt_override: systemPromptOverride || undefined,
          llm_model_identifier: llmModel,
          npc_speaker_id: npcSpeakerId || undefined,
        }

        const response = await dialoguesAPI.generateDialogueVariants(request)
        
        // Afficher un avertissement si DummyLLMClient a été utilisé
        if (response.warning) {
          toast(response.warning, 'error', 10000) // Afficher pendant 10 secondes
        }
        
        // Stocker dans le store pour affichage dans le panneau de droite
        setStoreVariantsResponse(response)
        setStoreInteractionsResponse(null)
        setVariantsResponse(response)
        setInteractions([])
        setIsDirty(false)
        // Mettre à jour le prompt estimé avec le prompt utilisé
        if (response.prompt_used) {
          setEstimatedPrompt(response.prompt_used, response.estimated_tokens, false)
        }
        // Mettre à jour les tokens utilisés
        if (response.estimated_tokens) {
          setTokensUsed(response.estimated_tokens)
        }
        // Fermer le toast de génération en cours et afficher le succès
        if (toastId) {
          toastManager.remove(toastId)
        }
        if (!response.warning) {
          toast('Génération réussie!', 'success')
        }
      } else if (generationMode === 'interactions') {
        const request: GenerateInteractionVariantsRequest = {
          k_variants: kVariants,
          user_instructions: userInstructions,
          context_selections: contextSelections,
          max_context_tokens: maxContextTokens,
          system_prompt_override: systemPromptOverride || undefined,
          llm_model_identifier: llmModel,
          previous_interaction_id: previousInteractionId || undefined,
        }

        const response = await dialoguesAPI.generateInteractionVariants(request)
        // Stocker dans le store pour affichage dans le panneau de droite
        setStoreInteractionsResponse(response)
        setStoreVariantsResponse(null)
        setInteractions(response)
        setVariantsResponse(null)
        setIsDirty(false)
        // Fermer le toast de génération en cours et afficher le succès
        if (toastId) {
          toastManager.remove(toastId)
        }
        toast('Génération réussie!', 'success')
      } else if (generationMode === 'unity') {
        // Validation : au moins un personnage requis pour Unity
        if (!contextSelections.characters || contextSelections.characters.length === 0) {
          toast('Au moins un personnage doit être sélectionné pour générer un dialogue Unity', 'error')
          if (toastId) {
            toastManager.remove(toastId)
          }
          setIsLoading(false)
          return
        }
        
        const request: GenerateUnityDialogueRequest = {
          user_instructions: userInstructions,
          context_selections: contextSelections,
          npc_speaker_id: npcSpeakerId || undefined,
          max_context_tokens: maxContextTokens,
          system_prompt_override: systemPromptOverride || undefined,
          llm_model_identifier: llmModel,
          max_choices: maxChoices ?? undefined,
        }

        const response = await dialoguesAPI.generateUnityDialogue(request)
        
        // Afficher un avertissement si DummyLLMClient a été utilisé
        if (response.warning) {
          toast(response.warning, 'error', 10000)
        }
        
        // Pour Unity, on affiche le JSON dans une variante
        const unityVariant: DialogueVariantResponse = {
          id: 'unity-1',
          title: response.title || 'Dialogue Unity JSON',
          content: response.json_content,
          is_new: true
        }
        
        const unityResponse: GenerateDialogueVariantsResponse = {
          variants: [unityVariant],
          prompt_used: response.prompt_used || undefined,
          estimated_tokens: response.estimated_tokens,
          warning: response.warning || undefined
        }
        
        // Stocker dans le store pour affichage
        setStoreVariantsResponse(unityResponse)
        setStoreInteractionsResponse(null)
        setVariantsResponse(unityResponse)
        setInteractions([])
        setIsDirty(false)
        
        if (response.prompt_used) {
          setEstimatedPrompt(response.prompt_used, response.estimated_tokens, false)
        }
        if (response.estimated_tokens) {
          setTokensUsed(response.estimated_tokens)
        }
        
        // Fermer le toast de génération en cours et afficher le succès
        if (toastId) {
          toastManager.remove(toastId)
        }
        if (!response.warning) {
          toast('Génération Unity JSON réussie!', 'success')
        }
      }
    } catch (err) {
      const errorMsg = getErrorMessage(err)
      setError(errorMsg)
      // Fermer le toast de génération en cours en cas d'erreur
      if (toastId) {
        toastManager.remove(toastId)
      }
      toast(errorMsg, 'error')
    } finally {
      setIsLoading(false)
    }
  }, [
    sceneSelection,
    userInstructions,
    generationMode,
    kVariants,
    maxContextTokens,
    systemPromptOverride,
    llmModel,
    previousInteractionId,
    buildContextSelections,
    toast,
    setStoreVariantsResponse,
    setStoreInteractionsResponse,
    setTokensUsed,
    setEstimatedPrompt,
  ])

  const handlePreview = () => {
    // TODO: Implémenter prévisualisation
    toast('Prévisualisation à implémenter', 'info')
  }


  const handleExportUnity = () => {
    // TODO: Implémenter export Unity
    toast('Export Unity à implémenter', 'info')
  }

  const handleReset = () => {
    setUserInstructions('')
    setVariantsResponse(null)
    setInteractions([])
    setError(null)
    setIsDirty(false)
    toast('Formulaire réinitialisé', 'info')
  }

  // Raccourci clavier pour générer (Ctrl+Enter)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === 'Enter') {
        e.preventDefault()
        if (!isLoading) {
          handleGenerate()
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isLoading, handleGenerate])

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
      loadInteractions()
    } catch (err) {
      alert(getErrorMessage(err))
    }
  }

  const panelTabs: Tab[] = [
    {
      id: 'generation',
      label: 'Génération',
      content: (
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column', backgroundColor: theme.background.panel }}>
          <div style={{ padding: '1.5rem', flex: 1, overflowY: 'auto' }}>
            <h2 style={{ marginTop: 0, color: theme.text.primary }}>Génération de Dialogues</h2>

            <ContextSummaryChips
              sceneSelection={sceneSelection}
              style={{ marginBottom: '1rem' }}
            />

            <div style={{ marginBottom: '1rem', display: 'flex', gap: '0.5rem' }}>
        <button
          onClick={() => {
            setGenerationMode('unity')
            setVariantsResponse(null)
            setInteractions([])
            setIsDirty(true)
          }}
          style={{
            padding: '0.5rem 1rem',
            border: `1px solid ${theme.border.primary}`,
            borderRadius: '4px',
            backgroundColor: generationMode === 'unity' ? theme.button.primary.background : theme.button.default.background,
            color: generationMode === 'unity' ? theme.button.primary.color : theme.button.default.color,
            cursor: 'pointer',
          }}
        >
          Dialogue Unity
        </button>
        <button
          onClick={() => {
            setGenerationMode('variants')
            setVariantsResponse(null)
            setInteractions([])
            setIsDirty(true)
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
          Texte libre
        </button>
        <button
          onClick={() => {
            setGenerationMode('interactions')
            setVariantsResponse(null)
            setInteractions([])
            setIsDirty(true)
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

      <SceneSelectionWidget />

      <ContextActions
        onError={setError}
        onSuccess={(msg: string) => {
          // Optionnel: afficher un message de succès
          console.log(msg)
        }}
      />

      <SystemPromptEditor
        userInstructions={userInstructions}
        systemPromptOverride={systemPromptOverride}
        onUserInstructionsChange={(value) => {
          setUserInstructions(value)
          setIsDirty(true)
        }}
        onSystemPromptChange={(value) => {
          setSystemPromptOverride(value)
          setIsDirty(true)
        }}
      />

      <DialogueStructureWidget
        value={dialogueStructure}
        onChange={(value) => {
          setDialogueStructure(value)
          setIsDirty(true)
        }}
      />

      {selections.characters.length > 0 && (
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ color: theme.text.primary, display: 'block', marginBottom: '0.5rem' }}>
            PNJ interlocuteur:
          </label>
          <select
            value={npcSpeakerId}
            onChange={(e) => {
              setNpcSpeakerId(e.target.value)
              setIsDirty(true)
            }}
            style={{ 
              width: '100%', 
              padding: '0.5rem', 
              boxSizing: 'border-box',
              backgroundColor: theme.input.background,
              border: `1px solid ${theme.input.border}`,
              color: theme.input.color,
            }}
          >
            <option value="">Sélectionner un PNJ...</option>
            {selections.characters.map((char) => (
              <option key={char} value={char}>
                {char}
              </option>
            ))}
          </select>
          <div style={{ 
            fontSize: '0.85rem', 
            color: theme.text.secondary, 
            marginTop: '0.25rem' 
          }}>
            Personnage joueur: Seigneuresse Uresaïr (par défaut)
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
        <div>
          <label style={{ color: theme.text.primary }}>
            Nombre de variantes:
            <input
              type="number"
              value={kVariants}
              onChange={(e) => {
                setKVariants(parseInt(e.target.value) || 1)
                setIsDirty(true)
              }}
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
              onChange={(e) => {
                setLlmModel(e.target.value)
                setIsDirty(true)
              }}
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
              onChange={(e) => {
                setMaxContextTokens(parseInt(e.target.value) || 1500)
                setIsDirty(true)
              }}
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

      {generationMode === 'unity' && (
        <div style={{ marginBottom: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <label style={{ color: theme.text.primary, margin: 0 }}>
              Nombre max de choix:
            </label>
            <div style={{ position: 'relative', display: 'inline-block' }}>
              <button
                type="button"
                style={{
                  width: '24px',
                  height: '24px',
                  borderRadius: '12px',
                  border: `1px solid ${theme.border.primary}`,
                  backgroundColor: theme.background.secondary,
                  color: theme.text.secondary,
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: 0,
                }}
                title="0 = aucun choix (dialogue linéaire), 1-8 = nombre max de choix, vide = l'IA décide"
              >
                ?
              </button>
            </div>
          </div>
          <input
            type="number"
            value={maxChoices ?? ''}
            onChange={(e) => {
              const value = e.target.value
              if (value === '') {
                setMaxChoices(null)
              } else {
                const num = parseInt(value)
                if (!isNaN(num) && num >= 0 && num <= 8) {
                  setMaxChoices(num)
                }
              }
              setIsDirty(true)
            }}
            min={0}
            max={8}
            placeholder="Libre"
            style={{ 
              width: '100%', 
              padding: '0.5rem', 
              boxSizing: 'border-box',
              backgroundColor: theme.input.background,
              border: `1px solid ${theme.input.border}`,
              color: theme.input.color,
            }}
          />
        </div>
      )}

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


      {generationMode === 'interactions' && (
        <div style={{ marginBottom: '1rem', padding: '1rem', border: `1px solid ${theme.border.primary}`, borderRadius: '4px' }}>
          <h3 style={{ marginTop: 0, marginBottom: '0.75rem', fontSize: '1rem', fontWeight: 'bold' }}>
            Continuité (Interaction précédente)
          </h3>
          <select
            value={previousInteractionId}
            onChange={(e) => {
              setPreviousInteractionId(e.target.value)
              setIsDirty(true)
            }}
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
          </div>
        </div>
      ),
    },
    {
      id: 'interactions',
      label: 'Interactions',
      content: (
        <InteractionsTab
          onSelectInteraction={(interaction) => {
            if (interaction) {
              setPreviousInteractionId(interaction.interaction_id)
            }
          }}
        />
      ),
    },
  ]

  const { setActions } = useGenerationActionsStore()
  
  // Utiliser useRef pour stocker les handlers et éviter les boucles infinies
  const handlersRef = useRef({
    handleGenerate,
    handlePreview,
    handleExportUnity,
    handleReset,
  })
  
  // Mettre à jour la ref quand les handlers changent
  useEffect(() => {
    handlersRef.current = {
      handleGenerate,
      handlePreview,
      handleExportUnity,
      handleReset,
    }
  }, [handleGenerate, handlePreview, handleExportUnity, handleReset])

  // Exposer les handlers via le store pour Dashboard
  // Mettre à jour au montage initial et quand isLoading ou isDirty changent
  useEffect(() => {
    setActions({
      handleGenerate: handlersRef.current.handleGenerate,
      handlePreview: handlersRef.current.handlePreview,
      handleExportUnity: handlersRef.current.handleExportUnity,
      handleReset: handlersRef.current.handleReset,
      isLoading,
      isDirty,
    })
  }, [isLoading, isDirty, setActions])
  
  // S'assurer que le store est initialisé au montage même si isLoading/isDirty ne changent pas
  // (nécessaire car le useEffect ci-dessus ne s'exécute que si isLoading/isDirty changent)
  useEffect(() => {
    setActions({
      handleGenerate: handlersRef.current.handleGenerate,
      handlePreview: handlersRef.current.handlePreview,
      handleExportUnity: handlersRef.current.handleExportUnity,
      handleReset: handlersRef.current.handleReset,
      isLoading,
      isDirty,
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []) // Exécuter une seule fois au montage pour initialiser le store

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', backgroundColor: theme.background.panel }}>
      <Tabs tabs={panelTabs} activeTabId={activePanelTab} onTabChange={(tabId) => setActivePanelTab(tabId as PanelTab)} />
    </div>
  )
}

