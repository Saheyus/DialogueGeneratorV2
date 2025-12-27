/**
 * Store Zustand pour gérer la configuration des champs de contexte.
 */
import { create } from 'zustand'
import * as configAPI from '../api/config'

export interface FieldInfo {
  path: string
  label: string
  type: string
  depth: number
  frequency: number
  suggested: boolean
  category?: string | null
  importance?: string | null
  is_metadata?: boolean  // Si le champ est une métadonnée (avant "Introduction" dans le JSON)
  is_essential?: boolean  // Si le champ est essentiel (contexte OU métadonnées) selon ESSENTIAL_*_FIELDS
  is_unique?: boolean  // Si le champ est unique (n'apparaît que dans une seule fiche)
}

export interface ContextFieldsResponse {
  element_type: string
  fields: Record<string, FieldInfo>
  total: number
  unique_fields_by_item?: Record<string, Record<string, string>>  // item_name -> {path: label}
}

export interface ContextFieldSuggestionsResponse {
  element_type: string
  context?: string | null
  suggested_fields: string[]
}

export interface ContextPreviewResponse {
  preview: string
  tokens: number
}

interface ContextConfigState {
  // Configuration des champs par type d'élément
  fieldConfigs: Record<string, string[]>  // element_type -> selected fields
  
  // Champs essentiels (toujours sélectionnés, non désélectionnables)
  essentialFields: Record<string, string[]>  // element_type -> essential field paths
  
  // Mode d'organisation
  organization: 'default' | 'narrative' | 'minimal'
  
  // Champs disponibles détectés
  availableFields: Record<string, Record<string, FieldInfo>>
  
  // Champs uniques regroupés par fiche
  uniqueFieldsByItem: Record<string, Record<string, Record<string, string>>>  // element_type -> item_name -> {path: label}
  
  // Suggestions par type d'élément
  suggestions: Record<string, string[]>
  
  // État de chargement
  isLoading: boolean
  error: string | null
  
  // Actions
  setFieldConfig: (elementType: string, fields: string[]) => void
  toggleField: (elementType: string, fieldPath: string) => void
  selectAllFields: (elementType: string) => void
  selectEssentialFields: (elementType: string) => void
  selectEssentialMetadataFields: (elementType: string) => void
  setOrganization: (mode: 'default' | 'narrative' | 'minimal') => void
  detectFields: (elementType: string) => Promise<void>
  loadSuggestions: (elementType: string, context?: string) => Promise<void>
  loadDefaultConfig: () => Promise<void>
  resetToDefault: () => void
  getPreview: (
    selectedElements: Record<string, string[]>,
    sceneInstruction: string,
    maxTokens?: number
  ) => Promise<ContextPreviewResponse>
  clearError: () => void
}

const defaultFieldConfigs: Record<string, string[]> = {
  character: [],
  location: [],
  item: [],
  species: [],
  community: [],
}

export const useContextConfigStore = create<ContextConfigState>((set, get) => ({
  fieldConfigs: { ...defaultFieldConfigs },
  essentialFields: {},
  organization: 'default',
  availableFields: {},
  uniqueFieldsByItem: {},
  suggestions: {},
  isLoading: false,
  error: null,

  setFieldConfig: (elementType, fields) => {
    set((state) => {
      const newFieldConfigs = {
        ...state.fieldConfigs,
        [elementType]: fields,
      }
      return { fieldConfigs: newFieldConfigs }
    })
  },

  toggleField: (elementType, fieldPath) => {
    set((state) => {
      // Ne pas permettre la désélection des champs essentiels du contexte narratif
      // (mais laisser désélectionner les métadonnées essentielles)
      const availableFieldsForType = state.availableFields[elementType] || {}
      const fieldInfo = availableFieldsForType[fieldPath]
      const isEssential = fieldInfo?.is_essential === true
      const isMetadata = fieldInfo?.is_metadata === true
      if (isEssential && !isMetadata) {
        // Champ essentiel du contexte narratif, ne pas permettre la désélection
        return state
      }
      
      const currentFields = state.fieldConfigs[elementType] || []
      const isSelected = currentFields.includes(fieldPath)
      const newFieldConfigs = {
        ...state.fieldConfigs,
        [elementType]: isSelected
          ? currentFields.filter((f) => f !== fieldPath)
          : [...currentFields, fieldPath],
      }
      return { fieldConfigs: newFieldConfigs }
    })
  },

  selectAllFields: (elementType) => {
    set((state) => {
      const availableFieldsForType = state.availableFields[elementType] || {}
      const allFieldPaths = Object.keys(availableFieldsForType)
      const essentialFieldsForType = state.essentialFields[elementType] || []
      
      // Sélectionner tous les champs (les essentiels sont toujours inclus)
      const newFieldConfigs = {
        ...state.fieldConfigs,
        [elementType]: [...new Set([...essentialFieldsForType, ...allFieldPaths])],
      }
      return { fieldConfigs: newFieldConfigs }
    })
  },

  selectEssentialFields: (elementType) => {
    set((state) => {
      // Récupérer les champs essentiels du CONTEXTE NARRATIF depuis availableFields
      // (is_essential=true && is_metadata=false)
      const availableFieldsForType = state.availableFields[elementType] || {}
      const essentialFieldsFromDetection = Object.entries(availableFieldsForType)
        .filter(([_path, fieldInfo]: [string, any]) => {
          const isEssential = fieldInfo.is_essential === true || fieldInfo.is_essential === 'true'
          const isMetadata = fieldInfo.is_metadata === true || fieldInfo.is_metadata === 'true'
          return isEssential && !isMetadata
        })
        .map(([path]) => path)
      
      // Si aucun champ essentiel détecté, utiliser ceux du store comme fallback
      const essentialFieldsForType = essentialFieldsFromDetection.length > 0
        ? essentialFieldsFromDetection
        : (state.essentialFields[elementType] || [])
      
      // Sélectionner uniquement les champs essentiels du contexte narratif
      const newFieldConfigs = {
        ...state.fieldConfigs,
        [elementType]: [...essentialFieldsForType],
      }
      return { fieldConfigs: newFieldConfigs }
    })
  },

  selectEssentialMetadataFields: (elementType) => {
    set((state) => {
      // Récupérer les champs essentiels des MÉTADONNÉES depuis availableFields
      // (is_essential=true && is_metadata=true)
      const availableFieldsForType = state.availableFields[elementType] || {}
      const essentialMetadataFields = Object.entries(availableFieldsForType)
        .filter(([_path, fieldInfo]: [string, any]) => {
          const isEssential = fieldInfo.is_essential === true || fieldInfo.is_essential === 'true'
          const isMetadata = fieldInfo.is_metadata === true || fieldInfo.is_metadata === 'true'
          return isEssential && isMetadata
        })
        .map(([path]) => path)

      const newFieldConfigs = {
        ...state.fieldConfigs,
        [elementType]: [...essentialMetadataFields],
      }
      return { fieldConfigs: newFieldConfigs }
    })
  },

  setOrganization: (mode) => {
    set({ organization: mode })
  },

  detectFields: async (elementType) => {
    set({ isLoading: true, error: null })
    
    try {
      // Invalider le cache pour ce type d'élément pour forcer une nouvelle détection
      try {
        await configAPI.invalidateContextFieldsCache(elementType)
      } catch (err) {
        console.warn(`Impossible d'invalider le cache pour ${elementType}:`, err)
      }
      
      const response = await configAPI.getContextFields(elementType)
      
      set((state) => {
        const newAvailableFields = {
          ...state.availableFields,
          [elementType]: response.fields,
        }
        
        const newUniqueFieldsByItem = {
          ...state.uniqueFieldsByItem,
          [elementType]: response.unique_fields_by_item || {},
        }
        
        return {
          availableFields: newAvailableFields,
          uniqueFieldsByItem: newUniqueFieldsByItem,
          isLoading: false,
        }
      })
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur lors de la détection des champs'
      set({ error: errorMessage, isLoading: false })
      throw err
    }
  },

  loadSuggestions: async (elementType, context) => {
    try {
      const response = await configAPI.getFieldSuggestions(elementType, context)
      
      set((state) => ({
        suggestions: {
          ...state.suggestions,
          [elementType]: response.suggested_fields,
        },
      }))
    } catch (err) {
      console.error('Erreur lors du chargement des suggestions:', err)
      // Ne pas bloquer si les suggestions échouent
    }
  },

  loadDefaultConfig: async () => {
    try {
      const response = await configAPI.getDefaultFieldConfig()
      const state = get()
      // Ne réinitialiser les fieldConfigs que s'ils sont vides (première ouverture)
      const hasExistingConfigs = Object.values(state.fieldConfigs).some(fields => fields.length > 0)
      
      if (!hasExistingConfigs) {
        // Initialiser les fieldConfigs avec les champs par défaut seulement si vide
        const defaultFieldConfigs: Record<string, string[]> = {}
        for (const [elementType, fields] of Object.entries(response.default_fields)) {
          defaultFieldConfigs[elementType] = [...fields]
        }
        
        set({
          fieldConfigs: defaultFieldConfigs,
          essentialFields: response.essential_fields,
        })
      } else {
        // Mettre à jour seulement essentialFields, garder les fieldConfigs existants
        set({
          essentialFields: response.essential_fields,
        })
      }
    } catch (err) {
      console.error('Erreur lors du chargement de la config par défaut:', err)
      // Ne pas bloquer si le chargement échoue
    }
  },

  resetToDefault: () => {
    const state = get()
    // Réinitialiser avec les champs par défaut (incluant les essentiels)
    const defaultFieldConfigs: Record<string, string[]> = {}
    for (const [elementType, fields] of Object.entries(state.essentialFields)) {
      // Commencer avec les champs essentiels
      defaultFieldConfigs[elementType] = [...fields]
    }
    
    set({
      fieldConfigs: defaultFieldConfigs,
      organization: 'default',
    })
  },

  getPreview: async (selectedElements, sceneInstruction, maxTokens = 70000) => {
    const state = get()
    
    try {
      // Inclure les champs essentiels dans la config
      const fieldConfigsWithEssential: Record<string, string[]> = {}
      for (const [elementType, fields] of Object.entries(state.fieldConfigs)) {
        const essential = state.essentialFields[elementType] || []
        fieldConfigsWithEssential[elementType] = [...new Set([...essential, ...fields])]
      }
      
      const response = await configAPI.previewContext({
        selected_elements: selectedElements,
        field_configs: fieldConfigsWithEssential,
        organization_mode: state.organization,
        scene_instruction: sceneInstruction,
        max_tokens: maxTokens,
      })
      
      return response
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur lors de la prévisualisation'
      set({ error: errorMessage })
      throw err
    }
  },

  clearError: () => {
    set({ error: null })
  },
}))

