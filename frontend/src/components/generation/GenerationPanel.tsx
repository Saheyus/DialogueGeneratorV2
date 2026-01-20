/**
 * Panneau de génération de dialogues.
 */
import { useState, useEffect, useCallback, useRef } from 'react'
import * as dialoguesAPI from '../../api/dialogues'
import { estimateTokens as estimateTokensUtil } from '../../utils/tokenEstimation'
import * as configAPI from '../../api/config'
import { useContextStore } from '../../store/contextStore'
import { useGenerationStore } from '../../store/generationStore'
import { useGenerationActionsStore } from '../../store/generationActionsStore'
import { useContextConfigStore } from '../../store/contextConfigStore'
import { useVocabularyStore } from '../../store/vocabularyStore'
import { useNarrativeGuidesStore } from '../../store/narrativeGuidesStore'
import { useGraphStore } from '../../store/graphStore'
import { useLLMStore } from '../../store/llmStore'
import { useAuthorProfile } from '../../hooks/useAuthorProfile'
import { getErrorMessage } from '../../types/errors'
import { theme } from '../../theme'
import type {
  LLMModelResponse,
  ContextSelection,
  GenerateUnityDialogueRequest,
} from '../../types/api'
import { DialogueStructureWidget } from './DialogueStructureWidget'
import { SystemPromptEditor } from './SystemPromptEditor'
import { SceneSelectionWidget } from './SceneSelectionWidget'
import { InGameFlagsSummary } from './InGameFlagsSummary'
import { GenerationProgressModal } from './GenerationProgressModal'
import { ModelSelector } from './ModelSelector'
import { PresetSelector } from './PresetSelector'
import { PresetValidationModal } from './PresetValidationModal'
import { useToast, SaveStatusIndicator, ConfirmDialog } from '../shared'
import type { Preset } from '../../types/preset'
import { filterObsoleteReferences as filterObsoleteRefs } from '../../utils/presetUtils'
import { CONTEXT_TOKENS_LIMITS, DEFAULT_MODEL, API_TIMEOUTS } from '../../constants'
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts'
import { useCostGovernance } from '../../hooks/useCostGovernance'
import type { SaveStatus } from '../shared/SaveStatusIndicator'
import { useFlagsStore } from '../../store/flagsStore'


export function GenerationPanel() {
  const { 
    selections, 
    selectedRegion, 
    selectedSubLocations,
    restoreState: restoreContextState,
    clearSelections,
  } = useContextStore()
  const {
    sceneSelection,
    dialogueStructure,
    systemPromptOverride,
    promptHash,
    tokenCount,
    structuredPrompt,
    setDialogueStructure,

    setSystemPromptOverride,
    setRawPrompt,
    setSceneSelection,

    setUnityDialogueResponse: setStoreUnityDialogueResponse,
    setTokensUsed,
    
    // État streaming (Story 0.2)
    isGenerating,
    streamingContent,
    currentStep,
    isMinimized,
    error: streamingError,
    currentJobId,
    isInterrupting,  // Task 4 - Story 0.8
    startGeneration,
    interrupt,
    minimize,
    resetStreamingState,
    setInterrupting,  // Task 4 - Story 0.8
    setError: setStreamingError,  // Task 4 - Story 0.8 (renommé pour éviter conflit avec setError local)
  } = useGenerationStore()
  
  const {
    vocabularyConfig,
  } = useVocabularyStore()
  
  const {
    includeNarrativeGuides,
  } = useNarrativeGuidesStore()
  
  const {
    authorProfile,
    updateProfile: updateAuthorProfile,
  } = useAuthorProfile()
  
  // Hook useLLMStore pour sélection provider/model (Story 0.3)
  const { model: selectedLLMModel } = useLLMStore()
  
  // État pour PresetValidationModal (Task 6)
  const [isValidationModalOpen, setIsValidationModalOpen] = useState(false)
  const [validationResult, setValidationResult] = useState<any>(null)
  const [pendingPreset, setPendingPreset] = useState<any>(null)
  
  // Hook cost governance (Task 7)
  const { checkBudget } = useCostGovernance()
  const [showBudgetBlockModal, setShowBudgetBlockModal] = useState(false)
  const [budgetBlockMessage, setBudgetBlockMessage] = useState<string>('')
  
  const [userInstructions, setUserInstructions] = useState('')
  const [maxContextTokens, setMaxContextTokens] = useState<number>(CONTEXT_TOKENS_LIMITS.DEFAULT)
  const [maxCompletionTokens, setMaxCompletionTokens] = useState<number | null>(null) // null = valeur par défaut selon le modèle
  const [llmModel, setLlmModel] = useState<string>(DEFAULT_MODEL)
  const [reasoningEffort, setReasoningEffort] = useState<'none' | 'low' | 'medium' | 'high' | 'xhigh' | null>(null)
  const [maxChoices, setMaxChoices] = useState<number | null>(null)
  const [choicesMode, setChoicesMode] = useState<'free' | 'capped'>('free')
  const [availableModels, setAvailableModels] = useState<LLMModelResponse[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isEstimating, setIsEstimating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})
  const [isDirty, setIsDirty] = useState(false)
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('saved')
  const [narrativeTags, setNarrativeTags] = useState<string[]>([])
  const [previousDialoguePreview] = useState<string | null>(null)
  
  // Synchroniser l'état local llmModel avec useLLMStore (Story 0.3)
  useEffect(() => {
    if (selectedLLMModel && selectedLLMModel !== llmModel) {
      setLlmModel(selectedLLMModel)
      setIsDirty(true)
      setSaveStatus('unsaved')
    }
  }, [selectedLLMModel])
  const [showResetConfirm, setShowResetConfirm] = useState(false)
  const [, setResetMenuOpen] = useState(false)
  const toast = useToast()
  const sliderRef = useRef<HTMLInputElement>(null)
  const eventSourceRef = useRef<EventSource | null>(null)
  
  /**
   * Ferme l'EventSource proprement en évitant les race conditions.
   * 
   * Vérifie que l'EventSource existe et n'est pas déjà fermé avant de le fermer.
   * Utilisé pour éviter les exceptions lors de fermetures multiples (timeout, erreur, succès).
   * 
   * Story 0.8 - Fix race condition EventSource
   */
  const closeEventSource = useCallback(() => {
    if (eventSourceRef.current) {
      // Vérifier que l'EventSource n'est pas déjà fermé
      if (eventSourceRef.current.readyState !== EventSource.CLOSED) {
        eventSourceRef.current.close()
      }
      eventSourceRef.current = null
    }
  }, [])
  const sseClosedByClientRef = useRef(false)
  const sseHasReceivedAnyMessageRef = useRef(false)
  const sseErrorDebounceTimerRef = useRef<number | null>(null)

  const availableNarrativeTags = ['tension', 'humour', 'dramatique', 'intime', 'révélation']
  
  // Lancer le streaming SSE quand isGenerating devient true avec currentJobId (Story 0.2)
  useEffect(() => {
    if (isGenerating && currentJobId && !eventSourceRef.current) {
      // Créer EventSource vers l'endpoint SSE du job
      const streamUrl = `/api/v1/dialogues/generate/jobs/${currentJobId}/stream`
      const es = new EventSource(streamUrl)
      eventSourceRef.current = es
      sseClosedByClientRef.current = false
      sseHasReceivedAnyMessageRef.current = false
      
      const { appendChunk, setStep, complete, setError: setStreamError } = useGenerationStore.getState()
      
      const handleMessage = async (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data)
          sseHasReceivedAnyMessageRef.current = true
          
          // Dispatcher selon le type d'événement SSE
          switch (data.type) {
            case 'chunk':
              if (data.content) {
                appendChunk(data.content)
              }
              break
            case 'step':
              if (data.step) {
                setStep(data.step)
              }
              break
            case 'metadata':
              console.debug('SSE metadata:', data)
              if (data.tokens) {
                setTokensUsed(data.tokens)
              }
              break
            case 'complete':
              // Le résultat Unity JSON est dans data.result
              if (data.result) {
                setStoreUnityDialogueResponse(data.result)
                setIsDirty(false)
                if (data.result.raw_prompt && data.result.estimated_tokens && data.result.prompt_hash) {
                  setRawPrompt(
                    data.result.raw_prompt,
                    data.result.estimated_tokens,
                    data.result.prompt_hash,
                    false,
                    data.result.structured_prompt || null
                  )
                }
                // Ajouter les nœuds générés au graphe
                if (data.result.json_content) {
                  try {
                    await useGraphStore.getState().loadDialogue(data.result.json_content)
                  } catch (graphError) {
                    console.warn('Erreur lors du chargement du graphe généré:', graphError)
                  }
                }
                toast('Génération Unity JSON réussie!', 'success')
              }
              complete()
              setIsLoading(false)
              sseClosedByClientRef.current = true
              if (sseErrorDebounceTimerRef.current !== null) {
                window.clearTimeout(sseErrorDebounceTimerRef.current)
                sseErrorDebounceTimerRef.current = null
              }
              es.close()
              eventSourceRef.current = null
              break
            case 'error':
              if (data.message) {
                setStreamError(data.message)
                setError(data.message)
                toast(data.message, 'error')
              }
              setIsLoading(false)
              sseClosedByClientRef.current = true
              if (sseErrorDebounceTimerRef.current !== null) {
                window.clearTimeout(sseErrorDebounceTimerRef.current)
                sseErrorDebounceTimerRef.current = null
              }
              es.close()
              eventSourceRef.current = null
              break
          }
        } catch (err) {
          console.warn('Erreur parsing SSE:', err)
        }
      }
      
      es.onmessage = (event) => {
        void handleMessage(event)
      }
      
      es.onerror = () => {
        if (sseClosedByClientRef.current || es.readyState === EventSource.CLOSED) {
          return
        }
        // NOTE: EventSource déclenche souvent onerror lors d'une fermeture "normale"
        // (EOF côté serveur → tentative de reconnexion). Pour éviter un faux toast juste
        // avant un événement "complete", on débounce l'erreur et on l'annule si la
        // génération se termine.
        if (sseErrorDebounceTimerRef.current !== null) {
          return
        }

        sseErrorDebounceTimerRef.current = window.setTimeout(() => {
          sseErrorDebounceTimerRef.current = null

          if (sseClosedByClientRef.current || es.readyState === EventSource.CLOSED) {
            return
          }

          // Si on a déjà reçu des messages, c'est probablement un close/reconnect transitoire.
          // On évite d'alarmer l'utilisateur avec un toast "erreur serveur" dans ce cas.
          if (sseHasReceivedAnyMessageRef.current) {
            console.debug('EventSource error after messages; ignoring toast.')
            return
          }

          console.error('Erreur EventSource')
          const errorMsg = 'Erreur de connexion au serveur'
          setStreamError(errorMsg)
          setError(errorMsg)
          toast(errorMsg, 'error')
          setIsLoading(false)
          sseClosedByClientRef.current = true
          es.close()
          eventSourceRef.current = null
        }, 600)
      }
    }
    
    // Cleanup : fermer EventSource si isGenerating devient false
    return () => {
      if (sseErrorDebounceTimerRef.current !== null) {
        window.clearTimeout(sseErrorDebounceTimerRef.current)
        sseErrorDebounceTimerRef.current = null
      }
      if (eventSourceRef.current && !isGenerating) {
        sseClosedByClientRef.current = true
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
    }
  }, [isGenerating, currentJobId, setError, setIsLoading, setTokensUsed, setStoreUnityDialogueResponse, setIsDirty, setRawPrompt, toast])

  // Sauvegarde automatique très fréquente (toutes les 2 secondes)
  const DRAFT_STORAGE_KEY = 'generation_draft'
  
  const saveDraft = useCallback(() => {
    setSaveStatus('saving')
    const draft = {
      userInstructions,
      authorProfile,
      systemPromptOverride,
      dialogueStructure,
      sceneSelection,
      maxContextTokens,
      maxCompletionTokens,
      llmModel,
      reasoningEffort,
      maxChoices,
      choicesMode,
      narrativeTags,
      contextSelections: selections,

      selectedRegion,
      selectedSubLocations,
      timestamp: Date.now(),
    }
    try {
      localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(draft))
      setIsDirty(false)
      setSaveStatus('saved')
    } catch (err) {
      console.error('Erreur lors de la sauvegarde automatique:', err)
      setSaveStatus('error')
    }
  }, [userInstructions, authorProfile, systemPromptOverride, dialogueStructure, sceneSelection, maxContextTokens, maxCompletionTokens, llmModel, reasoningEffort, maxChoices, choicesMode, narrativeTags, selections, selectedRegion, selectedSubLocations])

  // Charger le brouillon au démarrage (AVANT loadModels pour préserver le modèle sauvegardé)
  useEffect(() => {
    try {
      const saved = localStorage.getItem(DRAFT_STORAGE_KEY)
      if (saved) {
        const draft = JSON.parse(saved)
        if (draft.userInstructions !== undefined) setUserInstructions(draft.userInstructions)
        if (draft.authorProfile !== undefined) {
          // Charger le profil d'auteur depuis le draft et le sauvegarder dans le hook
          updateAuthorProfile(draft.authorProfile)
        }
        if (draft.systemPromptOverride !== undefined) setSystemPromptOverride(draft.systemPromptOverride)
        if (draft.dialogueStructure !== undefined) setDialogueStructure(draft.dialogueStructure)
        if (draft.sceneSelection !== undefined) {
          setSceneSelection(draft.sceneSelection)
        }
        if (draft.maxContextTokens !== undefined) {
          // Convertir les anciennes valeurs < MIN à MIN minimum
          const value = Math.max(CONTEXT_TOKENS_LIMITS.MIN, draft.maxContextTokens)
          setMaxContextTokens(value)
        }
        if (draft.maxCompletionTokens !== undefined) {
          const clampedMaxCompletionTokens = Math.min(Math.max(draft.maxCompletionTokens, 100), 16000)
          setMaxCompletionTokens(clampedMaxCompletionTokens)
        }
        if (draft.llmModel !== undefined && draft.llmModel !== "unknown") {
          // Ne charger le modèle du draft que s'il est valide (sera validé plus tard lors du chargement des modèles)
          setLlmModel(draft.llmModel)
        }
        if (draft.reasoningEffort !== undefined) setReasoningEffort(draft.reasoningEffort)
        if (draft.maxChoices !== undefined) setMaxChoices(draft.maxChoices)
        if (draft.choicesMode !== undefined) setChoicesMode(draft.choicesMode)
        if (draft.narrativeTags !== undefined) setNarrativeTags(draft.narrativeTags)

        // Charger les sélections de contexte
        if (draft.contextSelections !== undefined) {
          const savedRegion = draft.selectedRegion !== undefined ? draft.selectedRegion : null
          const savedSubLocations = draft.selectedSubLocations !== undefined && Array.isArray(draft.selectedSubLocations) 
            ? draft.selectedSubLocations 
            : []
          restoreContextState(draft.contextSelections, savedRegion, savedSubLocations)
        }
        setIsDirty(false)
        setSaveStatus('saved')
      }
    } catch (err) {
      console.error('Erreur lors du chargement du brouillon:', err)
      setSaveStatus('error')
    }
  }, [setDialogueStructure, setSystemPromptOverride, setSceneSelection, restoreContextState, updateAuthorProfile]) // Charger une seule fois au montage

  // Détecter les changements de sceneSelection pour déclencher la sauvegarde
  // (sauf au chargement initial)
  const [isInitialLoad, setIsInitialLoad] = useState(true)
  useEffect(() => {
    if (!isInitialLoad) {
      setIsDirty(true)
      setSaveStatus('unsaved')
    }
  }, [sceneSelection, isInitialLoad])

  // Détecter les changements dans les sélections de contexte pour déclencher la sauvegarde
  useEffect(() => {
    if (!isInitialLoad) {
      setIsDirty(true)
      setSaveStatus('unsaved')
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
      // Valider que le modèle actuel existe dans la liste des modèles disponibles
      // Si le modèle actuel n'existe pas, utiliser le premier modèle disponible
      if (response.models.length > 0) {
        const currentModelExists = llmModel && response.models.some(m => m.model_identifier === llmModel && m.model_identifier !== "unknown")
        if (!currentModelExists) {
          // Le modèle actuel n'existe pas ou est invalide, utiliser le premier modèle disponible
          const firstModel = response.models.find(m => m.model_identifier && m.model_identifier !== "unknown") || response.models[0]
          if (firstModel && firstModel.model_identifier && firstModel.model_identifier !== "unknown") {
            setLlmModel(firstModel.model_identifier)
          }
        }
      }
    } catch (err) {
      console.error('Erreur lors du chargement des modèles:', err)
    }
  }, [llmModel])

  useEffect(() => {
    loadModels()
  }, [loadModels])

  const hasSelections = useCallback((): boolean => {
    return (
      selections.characters_full.length > 0 ||
      selections.characters_excerpt.length > 0 ||
      selections.locations_full.length > 0 ||
      selections.locations_excerpt.length > 0 ||
      selections.items_full.length > 0 ||
      selections.items_excerpt.length > 0 ||
      selections.species_full.length > 0 ||
      selections.species_excerpt.length > 0 ||
      selections.communities_full.length > 0 ||
      selections.communities_excerpt.length > 0 ||
      selections.dialogues_examples.length > 0
    )
  }, [selections])

  // Construire context_selections avec scene_protagonists, scene_location, et generation_settings
  const buildContextSelections = useCallback((): ContextSelection => {
    // Créer un nouvel objet sans scene_protagonists et scene_location pour éviter d'envoyer des valeurs vides
    const { scene_protagonists, scene_location, ...baseSelections } = selections
    // Intentionnel: on extrait ces champs uniquement pour les exclure de baseSelections
    void scene_protagonists
    void scene_location
    const contextSelections: ContextSelection = {
      ...baseSelections,
    }

    // Ajouter scene_protagonists seulement s'il y a des valeurs
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

    // Ajouter scene_location seulement s'il y a des valeurs
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
      setRawPrompt(null, null, null, false, null)
      return
    }

    // Récupérer le hash actuel pour comparaison après l'appel API
    const currentState = useGenerationStore.getState()
    const currentHash = currentState.promptHash
    
    // Ne pas effacer le prompt existant pendant l'estimation
    // On met seulement isEstimating=true pour indiquer qu'on est en train d'estimer
    setIsEstimating(true)
    // Ne pas effacer le prompt : on le garde visible pendant l'estimation
    // setRawPrompt(null, null, null, true, null) // RETIRÉ : on garde le prompt existant
    
    try {
      const contextSelections = buildContextSelections()
      
      // Récupérer les fieldConfigs et organization depuis le store
      const { fieldConfigs, essentialFields, organization } = useContextConfigStore.getState()
      
      // Inclure les champs essentiels dans la config
      const fieldConfigsWithEssential: Record<string, string[]> = {}
      for (const [elementType, fields] of Object.entries(fieldConfigs)) {
        const essential = essentialFields[elementType] || []
        fieldConfigsWithEssential[elementType] = [...new Set([...essential, ...fields])]
      }
      
      // Récupérer les flags sélectionnés
      const { getSelectedFlagsArray } = useFlagsStore.getState()
      const inGameFlags = getSelectedFlagsArray()
      
      // Utiliser previewPrompt pour la prévisualisation (plus approprié que estimate-tokens)
      // Utiliser une valeur par défaut si userInstructions est vide (backend exige min_length=1)
      const userInstructionsValue = userInstructions.trim() || ' '
      const response = await dialoguesAPI.previewPrompt({
        user_instructions: userInstructionsValue,
        context_selections: contextSelections,
        npc_speaker_id: sceneSelection.characterB || undefined,
        max_context_tokens: maxContextTokens,
        system_prompt_override: systemPromptOverride || undefined,
        author_profile: authorProfile || undefined,
        max_choices: maxChoices ?? undefined,
        choices_mode: choicesMode,
        narrative_tags: narrativeTags.length > 0 ? narrativeTags : undefined,
        vocabulary_config: vocabularyConfig ? (vocabularyConfig as unknown as Record<string, string>) : undefined,
        include_narrative_guides: includeNarrativeGuides,
        previous_dialogue_preview: previousDialoguePreview || undefined,
        field_configs: Object.keys(fieldConfigsWithEssential).length > 0 ? fieldConfigsWithEssential : undefined,
        organization_mode: organization,
        in_game_flags: inGameFlags.length > 0 ? inGameFlags : undefined
      })
      
      // Estimer approximativement les tokens côté frontend pour l'affichage
      const estimatedTokenCount = estimateTokensUtil(response.raw_prompt)
      
      // Mettre à jour le prompt seulement si le hash a changé ou si on n'avait pas de prompt
      // Cela évite de reconstruire l'affichage si le prompt est identique
      if (currentHash !== response.prompt_hash || currentHash === null) {
        setRawPrompt(response.raw_prompt, estimatedTokenCount, response.prompt_hash, false, response.structured_prompt || null)
      }
      // Si le hash est identique, on ne met pas à jour le prompt (évite re-render inutile)
      // isEstimating sera mis à false dans le finally
    } catch (err: unknown) {
      // Ne logger que les erreurs non liées à la connexion (backend non accessible)
      const e = err as { code?: string; response?: { status?: number } } | null
      if (e?.code !== 'ERR_NETWORK' && e?.code !== 'ECONNREFUSED' && e?.response?.status !== 401) {
        console.error('Erreur lors de l\'estimation:', err)
        // Afficher un toast pour informer l'utilisateur de l'erreur
        const errorMessage = getErrorMessage(err)
        toast(errorMessage, 'error', 5000)
      }
      // Ne pas effacer le prompt existant si l'estimation échoue
      // Le prompt précédent reste visible pour l'utilisateur, seule l'indication d'estimation est désactivée
      // On conserve le prompt précédent au lieu de le mettre à null
      // Lire les valeurs depuis le store pour éviter les dépendances qui causent une boucle infinie
      const currentState = useGenerationStore.getState()
      setRawPrompt(currentState.rawPrompt, currentState.tokenCount, currentState.promptHash, false, null)
    } finally {
      setIsEstimating(false)
    }
  }, [userInstructions, authorProfile, maxChoices, choicesMode, narrativeTags, previousDialoguePreview, hasSelections, maxContextTokens, buildContextSelections, setRawPrompt, systemPromptOverride, vocabularyConfig, includeNarrativeGuides, sceneSelection.characterB, toast])



  // Récupérer fieldConfigs et organization depuis le store pour les inclure dans les dépendances
  const { fieldConfigs, organization } = useContextConfigStore()
  
  // Validation en temps réel
  useEffect(() => {
    const errors: Record<string, string> = {}
    
    if (maxContextTokens < CONTEXT_TOKENS_LIMITS.MIN) {
      errors.maxContextTokens = `Minimum ${CONTEXT_TOKENS_LIMITS.MIN.toLocaleString()} tokens`
    }
    if (maxContextTokens > CONTEXT_TOKENS_LIMITS.MAX) {
      errors.maxContextTokens = `Maximum ${CONTEXT_TOKENS_LIMITS.MAX.toLocaleString()} tokens`
    }
    
    if (maxCompletionTokens !== null) {
      if (maxCompletionTokens < 100) {
        errors.maxCompletionTokens = 'Minimum 100 tokens'
      }
      if (maxCompletionTokens > 16000) {
        errors.maxCompletionTokens = 'Maximum 16 000 tokens (limite backend)'
      }
    }
    
    if (tokenCount && tokenCount > maxContextTokens) {
      errors.tokenCount = `Les tokens estimés (${tokenCount.toLocaleString()}) dépassent la limite (${maxContextTokens.toLocaleString()})`
    }
    
    setValidationErrors(errors)
  }, [maxContextTokens, maxCompletionTokens, tokenCount])

  useEffect(() => {
    // Estimer les tokens quand les sélections, les instructions, le system prompt, ou les fieldConfigs changent
    const hasAnySelections = 
      selections.characters_full.length > 0 ||
      selections.characters_excerpt.length > 0 ||
      selections.locations_full.length > 0 ||
      selections.locations_excerpt.length > 0 ||
      selections.items_full.length > 0 ||
      selections.items_excerpt.length > 0 ||
      selections.species_full.length > 0 ||
      selections.species_excerpt.length > 0 ||
      selections.communities_full.length > 0 ||
      selections.communities_excerpt.length > 0 ||
      selections.dialogues_examples.length > 0
    
    const hasSystemPrompt = systemPromptOverride && systemPromptOverride.trim().length > 0
    
    const timeoutId = setTimeout(() => {
      if (userInstructions.trim() || hasAnySelections || hasSystemPrompt) {
        estimateTokens()
      } else {
        setRawPrompt(null, null, null, false, null)
      }
    }, 500)

    return () => clearTimeout(timeoutId)
  }, [userInstructions, selections, authorProfile, maxChoices, choicesMode, narrativeTags, previousDialoguePreview, maxContextTokens, estimateTokens, sceneSelection, dialogueStructure, systemPromptOverride, setRawPrompt, fieldConfigs, organization, vocabularyConfig, includeNarrativeGuides])



  const handleGenerate = useCallback(async () => {
    // Validation minimale
    if (!sceneSelection.characterA && !sceneSelection.characterB && !userInstructions.trim()) {
      toast('Veuillez sélectionner au moins un personnage ou ajouter des instructions', 'error')
      return
    }

    // Vérifier le budget avant génération (Task 7)
    const budgetCheck = await checkBudget()
    if (!budgetCheck.allowed) {
      setBudgetBlockMessage(budgetCheck.message || 'Budget dépassé')
      setShowBudgetBlockModal(true)
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const contextSelections = buildContextSelections()
      
      // Validation : au moins un personnage requis pour Unity
      const hasCharacters = (contextSelections.characters_full?.length || 0) + (contextSelections.characters_excerpt?.length || 0) > 0
      if (!hasCharacters) {
        toast('Au moins un personnage doit être sélectionné pour générer un dialogue Unity', 'error')
        setIsLoading(false)
        return
      }
      
      // Calculer les tokens envoyés avant la génération
      let tokensSent = 0
      try {
        const { fieldConfigs: fieldConfigsForEstimate, essentialFields, organization: organizationForEstimate } = useContextConfigStore.getState()
        const fieldConfigsWithEssential: Record<string, string[]> = {}
        for (const [elementType, fields] of Object.entries(fieldConfigsForEstimate)) {
          const essential = essentialFields[elementType] || []
          fieldConfigsWithEssential[elementType] = [...new Set([...essential, ...fields])]
        }
        
        // Récupérer les flags
        const { getSelectedFlagsArray } = useFlagsStore.getState()
        const inGameFlags = getSelectedFlagsArray()
        
        // Utiliser une valeur par défaut si userInstructions est vide (backend exige min_length=1)
        const userInstructionsValue = userInstructions.trim() || ' '
        const estimateResponse = await dialoguesAPI.estimateTokens({
          user_instructions: userInstructionsValue,
          context_selections: contextSelections,
          npc_speaker_id: sceneSelection.characterB || undefined,
          max_context_tokens: maxContextTokens,
          system_prompt_override: systemPromptOverride || undefined,
          author_profile: authorProfile || undefined,
          max_choices: maxChoices ?? undefined,
          choices_mode: choicesMode,
        narrative_tags: narrativeTags.length > 0 ? narrativeTags : undefined,
        vocabulary_config: vocabularyConfig ? (vocabularyConfig as unknown as Record<string, string>) : undefined,
        include_narrative_guides: includeNarrativeGuides,
          previous_dialogue_preview: previousDialoguePreview || undefined,
          field_configs: Object.keys(fieldConfigsWithEssential).length > 0 ? fieldConfigsWithEssential : undefined,
          organization_mode: organizationForEstimate,
          in_game_flags: inGameFlags.length > 0 ? inGameFlags : undefined
        })
        tokensSent = estimateResponse.token_count
        setTokensUsed(tokensSent)
      } catch (err) {
        console.warn('Impossible d\'estimer les tokens:', err)
      }
      
      // Valider que le modèle sélectionné existe dans la liste des modèles disponibles
      // Si availableModels est vide, essayer de charger les modèles d'abord
      let modelsToCheck = availableModels
      if (modelsToCheck.length === 0) {
        try {
          const response = await configAPI.listLLMModels()
          setAvailableModels(response.models)
          modelsToCheck = response.models
        } catch (err) {
          console.error('Erreur lors du chargement des modèles:', err)
          throw new Error('Impossible de charger les modèles LLM disponibles')
        }
      }
      
      // Déterminer le modèle à utiliser (valide ou fallback)
      let modelToUse = llmModel
      const validModel = modelsToCheck.find(m => m.model_identifier === llmModel)?.model_identifier
      if (!validModel) {
        // Utiliser le premier modèle disponible comme fallback
        const fallbackModel = modelsToCheck[0]?.model_identifier
        if (fallbackModel) {
          setLlmModel(fallbackModel)
          modelToUse = fallbackModel
        } else {
          throw new Error(`Aucun modèle LLM disponible. Modèle demandé: ${llmModel}`)
        }
      }
      
      // Utiliser une valeur par défaut si userInstructions est vide (backend exige min_length=1)
      const userInstructionsValue = userInstructions.trim() || ' '
      const safeMaxCompletionTokens = maxCompletionTokens !== null
        ? Math.min(Math.max(maxCompletionTokens, 100), 16000)
        : null
      if (safeMaxCompletionTokens !== maxCompletionTokens) {
        setMaxCompletionTokens(safeMaxCompletionTokens)
      }
      const request: GenerateUnityDialogueRequest = {
        user_instructions: userInstructionsValue,
        context_selections: contextSelections,
        npc_speaker_id: sceneSelection.characterB || undefined,
        max_context_tokens: maxContextTokens,
        max_completion_tokens: safeMaxCompletionTokens ?? undefined,
        system_prompt_override: systemPromptOverride || undefined,
        author_profile: authorProfile || undefined,
        llm_model_identifier: modelToUse,
        reasoning_effort: reasoningEffort ?? undefined,
        max_choices: maxChoices ?? undefined,
        choices_mode: choicesMode,
        narrative_tags: narrativeTags.length > 0 ? narrativeTags : undefined,
        vocabulary_config: vocabularyConfig ? (vocabularyConfig as unknown as Record<string, string>) : undefined,
        include_narrative_guides: includeNarrativeGuides,
        previous_dialogue_preview: previousDialoguePreview || undefined,
        in_game_flags: useFlagsStore.getState().getSelectedFlagsArray().length > 0 
          ? useFlagsStore.getState().getSelectedFlagsArray() 
          : undefined
      }

      // Créer le job de génération avec streaming SSE (Story 0.2)
      const job = await dialoguesAPI.createGenerationJob(request)
      
      // Démarrer la génération avec le job_id
      startGeneration(job.job_id)
      
      // Le useEffect ci-dessus se chargera de connecter l'EventSource
      // et de mettre à jour le store avec les événements SSE
    } catch (err) {
      const errorMsg = getErrorMessage(err)
      setError(errorMsg)
      toast(errorMsg, 'error')
      // Si la création du job échoue, on peut reset le streaming (sinon le SSE gère)
      resetStreamingState()
    } finally {
      setIsLoading(false)
    }
  }, [startGeneration, resetStreamingState, buildContextSelections, toast, sceneSelection, userInstructions, maxContextTokens, maxCompletionTokens, systemPromptOverride, llmModel, reasoningEffort, authorProfile, maxChoices, choicesMode, narrativeTags, promptHash, availableModels, vocabularyConfig, includeNarrativeGuides, previousDialoguePreview, setStoreUnityDialogueResponse, setTokensUsed, setRawPrompt, setIsDirty, setAvailableModels])

  const handlePreview = useCallback(() => {
    // TODO: Implémenter prévisualisation
    toast('Prévisualisation à implémenter', 'info')
  }, [toast])


  const handleExportUnity = useCallback(() => {
    // TODO: Implémenter export Unity
    toast('Export Unity à implémenter', 'info')
  }, [toast])

  const performReset = useCallback(() => {
    setUserInstructions('')
    setError(null)
    setIsDirty(false)
    setShowResetConfirm(false)
    setResetMenuOpen(false)
    // Réinitialiser aussi le store
    setStoreUnityDialogueResponse(null)
    toast('Formulaire réinitialisé', 'info')
  }, [toast, setStoreUnityDialogueResponse])

  const handleReset = useCallback(() => {
    if (isDirty) {
      setShowResetConfirm(true)
      return
    }
    performReset()
  }, [isDirty, performReset])

  const performResetAll = useCallback(() => {
    setUserInstructions('')
    setError(null)
    setIsDirty(false)
    setShowResetConfirm(false)
    setResetMenuOpen(false)
    setSystemPromptOverride(null)
    setDialogueStructure(['PNJ', 'PJ', 'Stop', '', '', ''])
    setSceneSelection({ characterA: null, characterB: null, sceneRegion: null, subLocation: null })
    setMaxContextTokens(CONTEXT_TOKENS_LIMITS.DEFAULT)
    setMaxCompletionTokens(null)
    setMaxChoices(null)
    setChoicesMode('free')
    setNarrativeTags([])
    setStoreUnityDialogueResponse(null)
    clearSelections()
    toast('Tout a été réinitialisé', 'info')
  }, [
    clearSelections,
    setChoicesMode,
    setDialogueStructure,
    setMaxChoices,
    setMaxCompletionTokens,
    setMaxContextTokens,
    setNarrativeTags,
    setSceneSelection,
    setStoreUnityDialogueResponse,
    setSystemPromptOverride,
    toast,
  ])

  const handleResetAll = useCallback(() => {
    if (isDirty) {
      setShowResetConfirm(true)
      return
    }
    performResetAll()
  }, [isDirty, performResetAll])

  const handleResetInstructions = useCallback(() => {
    setUserInstructions('')
    setIsDirty(true)
    setResetMenuOpen(false)
    toast('Instructions réinitialisées', 'info')
  }, [toast])

  const handleResetSelections = useCallback(() => {
    clearSelections()
    setResetMenuOpen(false)
    toast('Sélections réinitialisées', 'info')
  }, [clearSelections, toast])

  // Handlers Preset (Task 6)
  const handlePresetLoaded = useCallback(async (preset: any) => {
    try {
      // Validation du preset
      const validation = await fetch(`/api/v1/presets/${preset.id}/validate`)
      const validationResult = await validation.json()
      
      if (!validationResult.valid) {
        // Afficher modal de validation si références obsolètes
        setValidationResult(validationResult)
        setPendingPreset(preset)
        setIsValidationModalOpen(true)
      } else {
        // Appliquer directement si valide
        applyPreset(preset)
        toast('Preset chargé avec succès', 'success')
      }
    } catch (err) {
      const message = getErrorMessage(err)
      toast(`Erreur lors de la validation du preset: ${message}`, 'error')
    }
  }, [toast])
  
  const applyPreset = useCallback((preset: any) => {
    const config = preset.configuration

    // Appliquer le preset au ContextStore pour que le ContextSelector reflète exactement le preset
    // (sinon on garde des sélections résiduelles hors preset)
    const contextState = useContextStore.getState()
    if (config.contextSelections) {
      contextState.restoreState(
        config.contextSelections,
        config.selectedRegion ?? config.region ?? null,
        Array.isArray(config.selectedSubLocations)
          ? config.selectedSubLocations
          : (config.subLocation ? [config.subLocation] : [])
      )
    } else {
      contextState.clearSelections()
      ;(config.characters || []).forEach((name: string) => {
        contextState.toggleCharacter(name, 'full')
      })
      contextState.setRegion(config.region || null)
      if (config.subLocation) {
        contextState.toggleSubLocation(config.subLocation)
      }
    }
    
    // Pré-remplir sceneSelection
    setSceneSelection({
      characterA: config.characters?.[0] || null,
      characterB: config.characters?.[1] || null,
      sceneRegion: (config.selectedRegion ?? config.region) || null,
      subLocation: (Array.isArray(config.selectedSubLocations) ? config.selectedSubLocations[0] : config.subLocation) || null,
    })
    
    // Pré-remplir instructions
    setUserInstructions(config.instructions || '')
    
    // Pré-remplir fieldConfigs si sauvegardé
    if (config.fieldConfigs) {
      const { setFieldConfig } = useContextConfigStore.getState()
      Object.entries(config.fieldConfigs).forEach(([category, fields]) => {
        setFieldConfig(category, fields as string[])
      })
    }
    
    setIsDirty(true)
    setSaveStatus('unsaved')
  }, [setSceneSelection])
  
  const handleValidationConfirm = useCallback(() => {
    if (pendingPreset && validationResult) {
      // Filtrer les références obsolètes avant d'appliquer le preset
      const filteredPreset = filterObsoleteRefs(pendingPreset, validationResult.obsoleteRefs || [])
      applyPreset(filteredPreset)
      
      // Améliorer toast avec nombre de références obsolètes ignorées
      const obsoleteCount = validationResult.obsoleteRefs?.length || 0
      if (obsoleteCount > 0) {
        toast(`Preset chargé avec ${obsoleteCount} référence(s) obsolète(s) ignorée(s)`, 'warning')
      } else {
        toast('Preset chargé avec succès', 'success')
      }
    }
    setIsValidationModalOpen(false)
    setPendingPreset(null)
    setValidationResult(null)
  }, [pendingPreset, validationResult, applyPreset, toast])
  
  const handleValidationClose = useCallback(() => {
    setIsValidationModalOpen(false)
    setPendingPreset(null)
    setValidationResult(null)
  }, [])
  
  // Configuration actuelle pour sauvegarde preset
  const getCurrentConfiguration = useCallback(() => {
    const { fieldConfigs } = useContextConfigStore.getState()
    const contextState = useContextStore.getState()
    const selections = contextState.selections
    const selectedRegion = contextState.selectedRegion
    const selectedSubLocations = contextState.selectedSubLocations

    const uniq = <T,>(arr: T[]) => Array.from(new Set(arr))
    const allCharacters = uniq([
      ...(Array.isArray(selections.characters_full) ? selections.characters_full : []),
      ...(Array.isArray(selections.characters_excerpt) ? selections.characters_excerpt : []),
    ])

    // Locations: inclure les cases cochées + région + sous-lieux (exhaustif)
    const allLocations = uniq([
      ...(Array.isArray(selections.locations_full) ? selections.locations_full : []),
      ...(Array.isArray(selections.locations_excerpt) ? selections.locations_excerpt : []),
      ...(selectedRegion ? [selectedRegion] : []),
      ...(Array.isArray(selectedSubLocations) ? selectedSubLocations : []),
    ])
    
    const config = {
      characters: allCharacters,
      locations: allLocations,
      region: selectedRegion || sceneSelection.sceneRegion || '',
      subLocation: selectedSubLocations?.[0] || sceneSelection.subLocation || undefined,
      sceneType: 'Generic', // TODO: Inférer depuis narrative tags ou instructions
      instructions: userInstructions,
      fieldConfigs,
      contextSelections: selections,
      selectedRegion,
      selectedSubLocations,
    }
    
    return config
  }, [sceneSelection, userInstructions])

  // Raccourcis clavier
  useKeyboardShortcuts(
    [
      {
        key: 'ctrl+enter',
        handler: () => {
          if (!isLoading) {
            handleGenerate()
          }
        },
        description: 'Générer un dialogue',
        enabled: !isLoading,
      },
      {
        key: 'ctrl+n',
        handler: () => {
          handleReset()
        },
        description: 'Nouveau dialogue (réinitialiser)',
      },
    ],
    [isLoading, handleGenerate, handleReset]
  )

  const { setActions } = useGenerationActionsStore()

  // Utiliser useRef pour stocker les handlers et éviter les boucles infinies
  const handlersRef = useRef({
    handleGenerate,
    handlePreview,
    handleExportUnity,
    handleReset,
    handleResetAll,
    handleResetInstructions,
    handleResetSelections,
  })
  
  // Mettre à jour la ref quand les handlers changent
  useEffect(() => {
    handlersRef.current = {
      handleGenerate,
      handlePreview,
      handleExportUnity,
      handleReset,
      handleResetAll,
      handleResetInstructions,
      handleResetSelections,
    }
  }, [handleGenerate, handlePreview, handleExportUnity, handleReset, handleResetAll, handleResetInstructions, handleResetSelections])

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

  // Mettre à jour le style du slider en fonction de la valeur
  useEffect(() => {
    if (sliderRef.current) {
      const percentage = ((maxContextTokens - CONTEXT_TOKENS_LIMITS.MIN) / (CONTEXT_TOKENS_LIMITS.MAX - CONTEXT_TOKENS_LIMITS.MIN)) * 100
      sliderRef.current.style.background = `linear-gradient(to right, ${theme.border.focus} 0%, ${theme.border.focus} ${percentage}%, ${theme.input.background} ${percentage}%, ${theme.input.background} 100%)`
    }
  }, [maxContextTokens])

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', backgroundColor: theme.background.panel }}>
      <div style={{ padding: '1.5rem', flex: 1, overflowY: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2 style={{ marginTop: 0, marginBottom: 0, color: theme.text.primary }}>Génération de Dialogues</h2>
          <SaveStatusIndicator status={saveStatus} />
        </div>

        {/* PresetSelector (Task 6) */}
        <PresetSelector
          onPresetLoaded={handlePresetLoaded}
          getCurrentConfiguration={getCurrentConfiguration}
        />

            <SceneSelectionWidget />

      <SystemPromptEditor
        userInstructions={userInstructions}
        authorProfile={authorProfile}
        systemPromptOverride={systemPromptOverride}
        onUserInstructionsChange={(value) => {
          setUserInstructions(value)
          setIsDirty(true)
          setSaveStatus('unsaved')
        }}
        onAuthorProfileChange={(value) => {
          updateAuthorProfile(value)
          setIsDirty(true)
          setSaveStatus('unsaved')
        }}
        onSystemPromptChange={(value) => {
          setSystemPromptOverride(value)
          setIsDirty(true)
          setSaveStatus('unsaved')
        }}
      />

      <DialogueStructureWidget
        value={dialogueStructure}
        onChange={(value) => {
          setDialogueStructure(value)
          setIsDirty(true)
          setSaveStatus('unsaved')
        }}
      />

      <InGameFlagsSummary />

      {/* Sélecteur de modèle LLM (Story 0.3) */}
      <div style={{ marginBottom: '1rem' }}>
        <ModelSelector />
      </div>

      {(llmModel === "gpt-5.2" || llmModel === "gpt-5.2-pro") && (
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ color: theme.text.primary }}>
            Niveau de raisonnement:
            <select
              value={reasoningEffort || 'none'}
              onChange={(e) => {
                const newValue = e.target.value as 'none' | 'low' | 'medium' | 'high' | 'xhigh'
                setReasoningEffort(newValue === 'none' ? null : newValue)
                setIsDirty(true)
                setSaveStatus('unsaved')
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
              <option value="none">Aucun (rapide, latence minimale)</option>
              <option value="low">Faible (raisonnement minimal)</option>
              <option value="medium">Moyen (équilibré, recommandé)</option>
              <option value="high">Élevé (raisonnement approfondi)</option>
              <option value="xhigh">Très élevé (raisonnement maximal)</option>
            </select>
            <div style={{ fontSize: '0.875rem', color: theme.text.secondary, marginTop: '0.25rem' }}>
              Contrôle la profondeur de raisonnement du modèle. Plus élevé = meilleure qualité mais plus lent et plus coûteux.
            </div>
          </label>
        </div>
      )}

      <div style={{ marginBottom: '1rem' }}>
        <label style={{ color: theme.text.primary, display: 'block' }}>
          Max tokens contexte:
          {validationErrors.maxContextTokens && (
            <div style={{ fontSize: '0.85rem', color: theme.state.error.color, marginTop: '0.25rem' }}>
              {validationErrors.maxContextTokens}
            </div>
          )}
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginTop: '0.5rem' }}>
            <input
              ref={sliderRef}
              type="range"
              min={CONTEXT_TOKENS_LIMITS.MIN}
              max={CONTEXT_TOKENS_LIMITS.MAX}
              step={CONTEXT_TOKENS_LIMITS.STEP}
              value={maxContextTokens}
              onChange={(e) => {
                setMaxContextTokens(parseInt(e.target.value))
                setIsDirty(true)
                setSaveStatus('unsaved')
              }}
              style={{ 
                flex: 1,
                height: '6px',
                borderRadius: '3px',
                background: theme.input.background,
                outline: 'none',
                WebkitAppearance: 'none',
                appearance: 'none',
              }}
            />
            <span style={{ 
              minWidth: '60px', 
              textAlign: 'right',
              color: theme.text.primary,
              fontWeight: 'bold',
            }}>
              {maxContextTokens >= 1000 ? `${Math.round(maxContextTokens / 1000)}K` : maxContextTokens}
            </span>
          </div>
          <style>{`
            input[type="range"]::-webkit-slider-thumb {
              -webkit-appearance: none;
              appearance: none;
              width: 18px;
              height: 18px;
              border-radius: 50%;
              background: ${theme.border.focus};
              cursor: pointer;
              border: 2px solid ${theme.background.panel};
              box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
            }
            input[type="range"]::-webkit-slider-thumb:hover {
              background: ${theme.button.primary.background};
              transform: scale(1.1);
            }
            input[type="range"]::-moz-range-thumb {
              width: 18px;
              height: 18px;
              border-radius: 50%;
              background: ${theme.border.focus};
              cursor: pointer;
              border: 2px solid ${theme.background.panel};
              box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
            }
            input[type="range"]::-moz-range-thumb:hover {
              background: ${theme.button.primary.background};
              transform: scale(1.1);
            }
            input[type="range"]::-ms-thumb {
              width: 18px;
              height: 18px;
              border-radius: 50%;
              background: ${theme.border.focus};
              cursor: pointer;
              border: 2px solid ${theme.background.panel};
              box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
            }
            input[type="range"]::-ms-thumb:hover {
              background: ${theme.button.primary.background};
              transform: scale(1.1);
            }
          `}</style>
        </label>
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <label style={{ color: theme.text.primary, display: 'block' }}>
          Max tokens génération:
          {validationErrors.maxCompletionTokens && (
            <div style={{ fontSize: '0.85rem', color: theme.state.error.color, marginTop: '0.25rem' }}>
              {validationErrors.maxCompletionTokens}
            </div>
          )}
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginTop: '0.5rem' }}>
            <input
              type="range"
              min={100}
              max={16000}
              step={500}
              value={maxCompletionTokens ?? 10000}
              onChange={(e) => {
                const value = parseInt(e.target.value)
                setMaxCompletionTokens(value === 10000 ? null : value) // null = valeur par défaut
                setIsDirty(true)
                setSaveStatus('unsaved')
              }}
              style={{ 
                flex: 1,
                height: '6px',
                borderRadius: '3px',
                background: `linear-gradient(to right, ${theme.border.focus} 0%, ${theme.border.focus} ${((maxCompletionTokens ?? 10000) - 100) / (16000 - 100) * 100}%, ${theme.input.background} ${((maxCompletionTokens ?? 10000) - 100) / (16000 - 100) * 100}%, ${theme.input.background} 100%)`,
                outline: 'none',
                WebkitAppearance: 'none',
                appearance: 'none',
                cursor: 'pointer',
              }}
            />
            <span style={{ 
              minWidth: '70px', 
              textAlign: 'right',
              color: theme.text.primary,
              fontWeight: 'bold',
            }}>
              {maxCompletionTokens ? (maxCompletionTokens >= 1000 ? `${Math.round(maxCompletionTokens / 1000)}K` : maxCompletionTokens) : 'Auto (10K)'}
            </span>
          </div>
          <style>{`
            input[type="range"][value="${maxCompletionTokens ?? 10000}"]::-webkit-slider-runnable-track {
              height: 6px;
              border-radius: 3px;
            }
            input[type="range"][value="${maxCompletionTokens ?? 10000}"]::-moz-range-track {
              height: 6px;
              border-radius: 3px;
              background: ${theme.input.background};
            }
            input[type="range"][value="${maxCompletionTokens ?? 10000}"]::-webkit-slider-thumb {
              -webkit-appearance: none;
              appearance: none;
              width: 18px;
              height: 18px;
              border-radius: 50%;
              background: ${theme.border.focus};
              cursor: pointer;
              border: 2px solid ${theme.background.panel};
              box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
              margin-top: -6px;
            }
            input[type="range"][value="${maxCompletionTokens ?? 10000}"]::-webkit-slider-thumb:hover {
              background: ${theme.button.primary.background};
              transform: scale(1.1);
            }
            input[type="range"][value="${maxCompletionTokens ?? 10000}"]::-moz-range-thumb {
              width: 18px;
              height: 18px;
              border-radius: 50%;
              background: ${theme.border.focus};
              cursor: pointer;
              border: 2px solid ${theme.background.panel};
              box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
            }
            input[type="range"][value="${maxCompletionTokens ?? 10000}"]::-moz-range-thumb:hover {
              background: ${theme.button.primary.background};
              transform: scale(1.1);
            }
            input[type="range"][value="${maxCompletionTokens ?? 10000}"]::-ms-thumb {
              width: 18px;
              height: 18px;
              border-radius: 50%;
              background: ${theme.border.focus};
              cursor: pointer;
              border: 2px solid ${theme.background.panel};
              box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
            }
            input[type="range"][value="${maxCompletionTokens ?? 10000}"]::-ms-thumb:hover {
              background: ${theme.button.primary.background};
              transform: scale(1.1);
            }
          `}</style>
        </label>
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <label style={{ color: theme.text.primary, display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>
          Mode de génération des choix:
        </label>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', color: theme.text.primary }}>
            <input
              type="radio"
              name="choicesMode"
              value="free"
              checked={choicesMode === 'free'}
              onChange={() => {
                setChoicesMode('free')
                setIsDirty(true)
                setSaveStatus('unsaved')
              }}
              style={{ marginRight: '0.5rem' }}
            />
            Libre
          </label>
          <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', color: theme.text.primary }}>
            <input
              type="radio"
              name="choicesMode"
              value="capped"
              checked={choicesMode === 'capped'}
              onChange={() => {
                setChoicesMode('capped')
                setIsDirty(true)
                setSaveStatus('unsaved')
              }}
              style={{ marginRight: '0.5rem' }}
            />
            Limité
          </label>
        </div>
      </div>

      <div style={{ marginBottom: '1rem', opacity: choicesMode === 'capped' ? 1 : 0.5, pointerEvents: choicesMode === 'capped' ? 'auto' : 'none' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
          <label style={{ color: theme.text.primary, margin: 0 }}>
            Nombre max de choix (si limité):
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
            setSaveStatus('unsaved')
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

      {/* Tags narratifs */}
      <div style={{ marginBottom: '1rem' }}>
        <label style={{ 
          display: 'block', 
          marginBottom: '0.5rem', 
          color: theme.text.primary,
          fontWeight: 'bold'
        }}>
          Tags narratifs
        </label>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          {availableNarrativeTags.map((tag) => (
            <label
              key={tag}
              style={{
                display: 'flex',
                alignItems: 'center',
                padding: '0.5rem 1rem',
                border: `1px solid ${narrativeTags.includes(tag) ? theme.border.focus : theme.border.primary}`,
                borderRadius: '4px',
                backgroundColor: narrativeTags.includes(tag) 
                  ? theme.button.primary.background 
                  : theme.button.default.background,
                color: narrativeTags.includes(tag) 
                  ? theme.button.primary.color 
                  : theme.button.default.color,
                cursor: 'pointer',
                fontSize: '0.9rem',
              }}
            >
              <input
                type="checkbox"
                checked={narrativeTags.includes(tag)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setNarrativeTags([...narrativeTags, tag])
                  } else {
                    setNarrativeTags(narrativeTags.filter(t => t !== tag))
                  }
                  setIsDirty(true)
                }}
                style={{ marginRight: '0.5rem', cursor: 'pointer' }}
              />
              #{tag}
            </label>
          ))}
        </div>
      </div>

      {tokenCount !== null && validationErrors.tokenCount && (
        <div style={{ marginBottom: '1rem' }}>
          <div style={{ 
            padding: '0.5rem',
            backgroundColor: theme.state.error.background,
            color: theme.state.error.color,
            borderRadius: '4px',
            fontSize: '0.9rem' 
          }}>
            {validationErrors.tokenCount}
          </div>
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
      
      {/* Modal de progression streaming (Story 0.2) */}
      <ConfirmDialog
        isOpen={showResetConfirm}
        title="Réinitialiser le formulaire"
        message="Vous avez des modifications non sauvegardées. Êtes-vous sûr de vouloir tout réinitialiser ? Cette action est irréversible."
        confirmLabel="Réinitialiser"
        cancelLabel="Annuler"
        variant="warning"
        onConfirm={performReset}
        onCancel={() => setShowResetConfirm(false)}
      />
      
      {/* Modal de progression streaming (Story 0.2) */}
      <GenerationProgressModal
        isOpen={isGenerating}
        content={streamingContent}
        currentStep={currentStep}
        isMinimized={isMinimized}
        isInterrupting={isInterrupting}
        onInterrupt={async () => {
          // Afficher "Interruption en cours..."
          setInterrupting(true)
          
          // Appeler l'API de cancel avec le job_id avec timeout de 10s
          if (currentJobId) {
            try {
              // Promise.race entre cancelGenerationJob et timeout 10s
              // Fix: Gérer l'erreur si cancelPromise rejette (Issue #2)
              const cancelPromise = dialoguesAPI.cancelGenerationJob(currentJobId).catch((err) => {
                console.warn('Erreur lors de l\'annulation du job:', err)
                return 'error' as const
              })
              const timeoutPromise = new Promise<'timeout'>((resolve) => 
                setTimeout(() => resolve('timeout'), API_TIMEOUTS.CANCEL_JOB)
              )
              
              const result = await Promise.race([cancelPromise, timeoutPromise])
              
              // Si timeout atteint ou erreur, force close EventSource
              if (result === 'timeout' || result === 'error') {
                closeEventSource()
                setStreamingError('Interruption terminée')
              } else {
                // Interruption réussie
                closeEventSource()
                setStreamingError('Génération interrompue')
              }
            } catch (err) {
              console.warn('Erreur lors de l\'annulation du job:', err)
              // En cas d'erreur, force close EventSource quand même
              closeEventSource()
              setStreamingError('Interruption terminée')
            }
          } else {
            // Si pas de job_id, fermer EventSource directement
            closeEventSource()
            setStreamingError('Génération interrompue')
          }
          
          // Réinitialiser l'état
          interrupt()
          
          // Réinitialiser l'état d'interruption après un court délai pour permettre l'affichage du message
          setTimeout(() => {
            setInterrupting(false)
            resetStreamingState()
            setIsLoading(false)
          }, 2000)  // 2 secondes pour permettre la lecture du message
        }}
        onMinimize={minimize}
        onClose={() => {
          resetStreamingState()
          setIsLoading(false)
        }}
        error={streamingError}
      />
      
      {/* Modal de validation preset (Task 6) */}
      {validationResult && (
        <PresetValidationModal
          isOpen={isValidationModalOpen}
          validationResult={validationResult}
          onClose={handleValidationClose}
          onConfirm={handleValidationConfirm}
        />
      )}
      
      {/* Modal de blocage budget (Task 7) */}
      <ConfirmDialog
        isOpen={showBudgetBlockModal}
        title="Budget dépassé"
        message={budgetBlockMessage || "Votre quota mensuel a été atteint. Veuillez augmenter le budget ou attendre le prochain mois."}
        confirmLabel="Fermer"
        cancelLabel="Fermer"
        variant="danger"
        onConfirm={() => setShowBudgetBlockModal(false)}
        onCancel={() => setShowBudgetBlockModal(false)}
      />
    </div>
  )
}

