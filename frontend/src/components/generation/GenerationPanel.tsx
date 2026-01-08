/**
 * Panneau de génération de dialogues.
 */
import { useState, useEffect, useCallback, useRef } from 'react'
import * as dialoguesAPI from '../../api/dialogues'
import * as configAPI from '../../api/config'
import { useContextStore } from '../../store/contextStore'
import { useGenerationStore } from '../../store/generationStore'
import { useGenerationActionsStore } from '../../store/generationActionsStore'
import { useContextConfigStore } from '../../store/contextConfigStore'
import { useVocabularyStore } from '../../store/vocabularyStore'
import { useAuthorProfile } from '../../hooks/useAuthorProfile'
import { getErrorMessage } from '../../types/errors'
import { theme } from '../../theme'
import type {
  LLMModelResponse,
  ContextSelection,
  GenerateUnityDialogueRequest,
  GenerateUnityDialogueResponse,
} from '../../types/api'
import { DialogueStructureWidget } from './DialogueStructureWidget'
import { SystemPromptEditor } from './SystemPromptEditor'
import { SceneSelectionWidget } from './SceneSelectionWidget'
import { useToast, toastManager, SaveStatusIndicator, ConfirmDialog } from '../shared'
import { CONTEXT_TOKENS_LIMITS, DEFAULT_MODEL } from '../../constants'
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts'
import type { SaveStatus } from '../shared/SaveStatusIndicator'


export function GenerationPanel() {
  const { 
    selections, 
    selectedRegion, 
    selectedSubLocations,
    setSelections,
    setRegion,
    restoreState: restoreContextState,
    clearSelections,
  } = useContextStore()
  const {
    sceneSelection,
    dialogueStructure,
    systemPromptOverride,
    rawPrompt,
    promptHash,
    tokenCount,
    setDialogueStructure,

    setSystemPromptOverride,
    setRawPrompt,
    setSceneSelection,

    setUnityDialogueResponse: setStoreUnityDialogueResponse,
    setTokensUsed,
  } = useGenerationStore()
  
  const {
    vocabularyConfig,
    includeNarrativeGuides,
  } = useVocabularyStore()
  
  const {
    authorProfile,
    updateProfile: updateAuthorProfile,
  } = useAuthorProfile()
  
  const [userInstructions, setUserInstructions] = useState('')
  const [maxContextTokens, setMaxContextTokens] = useState<number>(CONTEXT_TOKENS_LIMITS.DEFAULT)
  const [maxCompletionTokens, setMaxCompletionTokens] = useState<number | null>(null) // null = valeur par défaut selon le modèle
  const [llmModel, setLlmModel] = useState<string>(DEFAULT_MODEL)
  const [maxChoices, setMaxChoices] = useState<number | null>(null)
  const [choicesMode, setChoicesMode] = useState<'free' | 'capped'>('free')
  const [availableModels, setAvailableModels] = useState<LLMModelResponse[]>([])
  const [unityDialogueResponse, setUnityDialogueResponse] = useState<GenerateUnityDialogueResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isEstimating, setIsEstimating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})
  const [isDirty, setIsDirty] = useState(false)
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('saved')
  const [narrativeTags, setNarrativeTags] = useState<string[]>([])
  const [previousDialoguePreview, setPreviousDialoguePreview] = useState<string | null>(null)
  const [showResetConfirm, setShowResetConfirm] = useState(false)
  const [resetMenuOpen, setResetMenuOpen] = useState(false)
  const resetMenuRef = useRef<HTMLDivElement>(null)
  const toast = useToast()
  const sliderRef = useRef<HTMLInputElement>(null)

  const availableNarrativeTags = ['tension', 'humour', 'dramatique', 'intime', 'révélation']

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
  }, [userInstructions, authorProfile, systemPromptOverride, dialogueStructure, sceneSelection, maxContextTokens, maxCompletionTokens, llmModel, maxChoices, narrativeTags, selections, selectedRegion, selectedSubLocations])

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
        if (draft.maxCompletionTokens !== undefined) setMaxCompletionTokens(draft.maxCompletionTokens)
        if (draft.llmModel !== undefined && draft.llmModel !== "unknown") {
          // Ne charger le modèle du draft que s'il est valide (sera validé plus tard lors du chargement des modèles)
          setLlmModel(draft.llmModel)
        }
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

    setIsEstimating(true)
      setRawPrompt(null, null, null, true, null)
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
      
      const response = await dialoguesAPI.estimateTokens({
        user_instructions: userInstructions,
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
      })
      
      setRawPrompt(response.raw_prompt, response.token_count, response.prompt_hash, false, response.structured_prompt || null)
    } catch (err: any) {
      // Ne logger que les erreurs non liées à la connexion (backend non accessible)
      if (err?.code !== 'ERR_NETWORK' && err?.code !== 'ECONNREFUSED' && err?.response?.status !== 401) {
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
      if (maxCompletionTokens < 500) {
        errors.maxCompletionTokens = 'Minimum 500 tokens'
      }
      if (maxCompletionTokens > 50000) {
        errors.maxCompletionTokens = 'Maximum 50 000 tokens'
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

    setIsLoading(true)
    setError(null)
    // Toast sans durée (0) pour qu'il reste affiché pendant la génération, avec action d'annulation
    const cancelGeneration = () => {
      setIsLoading(false)
      setError('Génération annulée')
    }
    const toastId = toast('Génération en cours...', 'info', 0, [
      {
        label: 'Annuler',
        action: cancelGeneration,
        style: 'secondary',
      },
    ])

    try {
      const contextSelections = buildContextSelections()
      
      // Validation : au moins un personnage requis pour Unity
      const hasCharacters = (contextSelections.characters_full?.length || 0) + (contextSelections.characters_excerpt?.length || 0) > 0
      if (!hasCharacters) {
        toast('Au moins un personnage doit être sélectionné pour générer un dialogue Unity', 'error')
        if (toastId) {
          toastManager.remove(toastId)
        }
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
        const estimateResponse = await dialoguesAPI.estimateTokens({
          user_instructions: userInstructions,
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
      
      const request: GenerateUnityDialogueRequest = {
        user_instructions: userInstructions,
        context_selections: contextSelections,
        npc_speaker_id: sceneSelection.characterB || undefined,
        max_context_tokens: maxContextTokens,
        max_completion_tokens: maxCompletionTokens ?? undefined,
        system_prompt_override: systemPromptOverride || undefined,
        author_profile: authorProfile || undefined,
        llm_model_identifier: modelToUse,
        max_choices: maxChoices ?? undefined,
        choices_mode: choicesMode,
        narrative_tags: narrativeTags.length > 0 ? narrativeTags : undefined,
        vocabulary_config: vocabularyConfig ? (vocabularyConfig as unknown as Record<string, string>) : undefined,
        include_narrative_guides: includeNarrativeGuides,
        previous_dialogue_preview: previousDialoguePreview || undefined,
      }


      const response = await dialoguesAPI.generateUnityDialogue(request)
      
      // Afficher un avertissement si DummyLLMClient a été utilisé
      if (response.warning) {
        toast(response.warning, 'error', 10000)
      }
      
      // Stocker directement la réponse Unity dans le store et l'état local
      setUnityDialogueResponse(response)
      setStoreUnityDialogueResponse(response)
      setIsDirty(false)
      
      // Valider le hash si on a déjà fait une estimation
      if (promptHash && response.prompt_hash !== promptHash) {
        console.warn(`[HASH MISMATCH] Le prompt généré (${response.prompt_hash.slice(0, 8)}) diffère du prompt estimé (${promptHash.slice(0, 8)}).`)
      }
      
      // Mettre à jour le prompt réel dans le store
      setRawPrompt(response.raw_prompt, response.estimated_tokens, response.prompt_hash, false, response.structured_prompt || null)

      
      // Fermer le toast de génération en cours et afficher le succès
      if (toastId) {
        toastManager.remove(toastId)
      }
      if (!response.warning) {
        toast('Génération Unity JSON réussie!', 'success')
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
    maxContextTokens,
    systemPromptOverride,
    llmModel,
    authorProfile,
    maxChoices,
    narrativeTags,
    vocabularyConfig,
    includeNarrativeGuides,
    previousDialoguePreview,
    buildContextSelections,
    toast,
    setStoreUnityDialogueResponse,
    setTokensUsed,
  ])

  const handlePreview = () => {
    // TODO: Implémenter prévisualisation
    toast('Prévisualisation à implémenter', 'info')
  }


  const handleExportUnity = () => {
    // TODO: Implémenter export Unity
    toast('Export Unity à implémenter', 'info')
  }

  const handleReset = useCallback(() => {
    if (isDirty) {
      setShowResetConfirm(true)
      return
    }
    performReset()
  }, [isDirty])

  const performReset = useCallback(() => {
    setUserInstructions('')
    setUnityDialogueResponse(null)
    setError(null)
    setIsDirty(false)
    setShowResetConfirm(false)
    setResetMenuOpen(false)
    // Réinitialiser aussi le store
    setStoreUnityDialogueResponse(null)
    toast('Formulaire réinitialisé', 'info')
  }, [toast, setStoreUnityDialogueResponse])

  const handleResetAll = useCallback(() => {
    if (isDirty) {
      setShowResetConfirm(true)
      return
    }
    performResetAll()
  }, [isDirty])

  const performResetAll = useCallback(() => {
    setUserInstructions('')
    setUnityDialogueResponse(null)
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
  }, [toast, setStoreUnityDialogueResponse, setSystemPromptOverride, setDialogueStructure, setSceneSelection, clearSelections])

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

      <div style={{ marginBottom: '1rem' }}>
        <label style={{ color: theme.text.primary }}>
          Modèle LLM:
          <select
            value={llmModel}
            onChange={(e) => {
              const newValue = e.target.value
              // Ne pas accepter "unknown" comme valeur valide
              if (newValue && newValue !== "unknown") {
                setLlmModel(newValue)
                setIsDirty(true)
                setSaveStatus('unsaved')
              }
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
              min={500}
              max={50000}
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
                background: `linear-gradient(to right, ${theme.border.focus} 0%, ${theme.border.focus} ${((maxCompletionTokens ?? 10000) - 500) / (50000 - 500) * 100}%, ${theme.input.background} ${((maxCompletionTokens ?? 10000) - 500) / (50000 - 500) * 100}%, ${theme.input.background} 100%)`,
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
          <div style={{ fontSize: '0.85rem', color: theme.text.secondary, marginTop: '0.25rem' }}>
            {maxCompletionTokens ? `Limite fixée à ${maxCompletionTokens >= 1000 ? `${Math.round(maxCompletionTokens / 1000)}K` : maxCompletionTokens} tokens` : 'Valeur automatique selon le modèle (10K pour thinking, 1.5K pour autres)'}
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

      {tokenCount !== null && (
        <div style={{ 
          marginBottom: '1rem', 
          padding: '0.5rem', 
          backgroundColor: validationErrors.tokenCount ? theme.state.error.background : theme.state.info.background, 
          color: validationErrors.tokenCount ? theme.state.error.color : theme.state.info.color,
          borderRadius: '4px' 
        }}>
          {isEstimating ? (
            <span>Estimation en cours...</span>
          ) : (
            <span>
              <strong>Tokens estimés:</strong> {tokenCount.toLocaleString()}
              {validationErrors.tokenCount && (
                <div style={{ marginTop: '0.5rem', fontSize: '0.9rem' }}>
                  {validationErrors.tokenCount}
                </div>
              )}
            </span>
          )}
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
    </div>
  )
}

