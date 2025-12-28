/**
 * Types TypeScript pour l'API.
 */

// Auth
export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface UserResponse {
  id: string
  username: string
  email?: string
}

// Dialogue
export interface ContextSelection {
  characters: string[]
  locations: string[]
  items: string[]
  species: string[]
  communities: string[]
  dialogues_examples: string[]
  scene_protagonists?: Record<string, unknown>
  scene_location?: Record<string, unknown>
  generation_settings?: Record<string, unknown>
}

export interface GenerateDialogueVariantsRequest {
  k_variants: number
  user_instructions: string
  context_selections: ContextSelection
  max_context_tokens: number
  structured_output: boolean
  system_prompt_override?: string
  llm_model_identifier: string
  npc_speaker_id?: string
}

/**
 * @deprecated Utiliser GenerateUnityDialogueResponse à la place. Conservé pour compatibilité.
 */
export interface DialogueVariantResponse {
  id: string
  title: string
  content: string
  is_new: boolean
}

/**
 * @deprecated Utiliser GenerateUnityDialogueResponse à la place. Conservé pour compatibilité.
 */
export interface GenerateDialogueVariantsResponse {
  variants: DialogueVariantResponse[]
  prompt_used?: string
  estimated_tokens: number
  warning?: string
}

export interface EstimateTokensResponse {
  context_tokens: number
  total_estimated_tokens: number
  estimated_prompt?: string | null
}

/**
 * @deprecated Ne plus utiliser. Les interactions structurées ne sont plus générées. Conservé pour compatibilité.
 */
export interface GenerateInteractionVariantsRequest {
  k_variants: number
  user_instructions: string
  context_selections: ContextSelection
  max_context_tokens: number
  system_prompt_override?: string
  llm_model_identifier: string
  previous_interaction_id?: string
  field_configs?: Record<string, string[]>
  organization_mode?: string
  narrative_tags?: string[]
  vocabulary_min_importance?: string
  include_narrative_guides?: boolean
}

// Interaction
export interface DialogueElement {
  type: 'dialogue'
  content: string
  speaker?: string
}

export interface ChoiceElement {
  type: 'choice'
  options: Array<{
    text: string
    next_interaction_id: string
  }>
}

export type InteractionElement = DialogueElement | ChoiceElement | Record<string, unknown>

export interface InteractionResponse {
  interaction_id: string
  title: string
  elements: InteractionElement[]
  header_commands: string[]
  header_tags: string[]
  next_interaction_id_if_no_choices?: string
  narrative_warnings?: string[]
}

export interface InteractionListResponse {
  interactions: InteractionResponse[]
  total: number
}

// Context
export interface CharacterResponse {
  name: string
  data: Record<string, unknown>
}

export interface CharacterListResponse {
  characters: CharacterResponse[]
  total: number
}

export interface LocationResponse {
  name: string
  data: Record<string, unknown>
}

export interface LocationListResponse {
  locations: LocationResponse[]
  total: number
}

export interface ItemResponse {
  name: string
  data: Record<string, unknown>
}

export interface ItemListResponse {
  items: ItemResponse[]
  total: number
}

export interface SpeciesResponse {
  name: string
  data: Record<string, unknown>
}

export interface SpeciesListResponse {
  species: SpeciesResponse[]
  total: number
}

export interface CommunityResponse {
  name: string
  data: Record<string, unknown>
}

export interface CommunityListResponse {
  communities: CommunityResponse[]
  total: number
}

export interface RegionListResponse {
  regions: string[]
  total: number
}

export interface SubLocationListResponse {
  sub_locations: string[]
  total: number
  region_name: string
}

export interface LinkedElementsRequest {
  character_a?: string
  character_b?: string
  scene_region?: string
  sub_location?: string
}

export interface LinkedElementsResponse {
  linked_elements: string[]
  total: number
}

// Config
export interface LLMModelResponse {
  model_identifier: string
  display_name: string
  client_type: string
  max_tokens: number
}

export interface LLMModelsListResponse {
  models: LLMModelResponse[]
  total: number
}

export interface UnityDialoguesPathResponse {
  path: string
}

export interface InteractionContextPathResponse {
  path: InteractionResponse[]
  total: number
}

// Unity Dialogue
export interface GenerateUnityDialogueRequest {
  author_profile?: string
  user_instructions: string
  context_selections: ContextSelection
  npc_speaker_id?: string
  max_context_tokens: number
  system_prompt_override?: string
  llm_model_identifier: string
  max_choices?: number | null
  narrative_tags?: string[]
  vocabulary_min_importance?: string
  include_narrative_guides?: boolean
}

export interface GenerateUnityDialogueResponse {
  json_content: string
  title?: string
  prompt_used?: string
  estimated_tokens: number
  warning?: string
}

export interface ExportUnityDialogueRequest {
  json_content: string
  title: string
  filename?: string
}

export interface ExportUnityDialogueResponse {
  file_path: string
  filename: string
  success: boolean
}

// Unity Dialogues Library
export interface UnityDialogueMetadata {
  filename: string
  file_path: string
  size_bytes: number
  modified_time: string
  title?: string
}

export interface UnityDialogueListResponse {
  dialogues: UnityDialogueMetadata[]
  total: number
}

export interface UnityDialogueReadResponse {
  filename: string
  json_content: string
  title?: string
  size_bytes: number
  modified_time: string
}

export interface UnityDialoguePreviewRequest {
  json_content: string
}

export interface UnityDialoguePreviewResponse {
  preview_text: string
  node_count: number
}

// Unity Dialogue Node Types (for editor)
export interface UnityDialogueChoice {
  text: string
  targetNode: string
  traitRequirements?: Array<{
    trait: string
    minValue: number
  }>
  allowInfluenceForcing?: boolean
  influenceThreshold?: number
  influenceDelta?: number
  respectDelta?: number
  test?: string
  testSuccessNode?: string
  testFailureNode?: string
  condition?: string
  [key: string]: unknown
}

export interface UnityDialogueNode {
  id: string
  speaker?: string
  line?: string
  nextNode?: string
  choices?: UnityDialogueChoice[]
  test?: string
  successNode?: string
  failureNode?: string
  isLongRest?: boolean
  startState?: number
  cutsceneMode?: boolean
  cutsceneImageId?: string
  cutsceneId?: string
  exitCutsceneMode?: boolean
  consequences?: {
    flag: string
    description?: string
  }
  [key: string]: unknown
}

