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
  _scene_protagonists?: Record<string, any>
  _scene_location?: Record<string, any>
  generation_settings?: Record<string, any>
}

export interface GenerateDialogueVariantsRequest {
  k_variants: number
  user_instructions: string
  context_selections: ContextSelection
  max_context_tokens: number
  structured_output: boolean
  system_prompt_override?: string
  llm_model_identifier: string
}

export interface DialogueVariantResponse {
  id: string
  title: string
  content: string
  is_new: boolean
}

export interface GenerateDialogueVariantsResponse {
  variants: DialogueVariantResponse[]
  prompt_used?: string
  estimated_tokens: number
}

export interface GenerateInteractionVariantsRequest {
  k_variants: number
  user_instructions: string
  context_selections: ContextSelection
  max_context_tokens: number
  system_prompt_override?: string
  llm_model_identifier: string
}

// Interaction
export interface InteractionResponse {
  interaction_id: string
  title: string
  elements: any[]
  header_commands: string[]
  header_tags: string[]
  next_interaction_id_if_no_choices?: string
}

export interface InteractionListResponse {
  interactions: InteractionResponse[]
  total: number
}

// Context
export interface CharacterResponse {
  name: string
  data: Record<string, any>
}

export interface CharacterListResponse {
  characters: CharacterResponse[]
  total: number
}

export interface LocationResponse {
  name: string
  data: Record<string, any>
}

export interface LocationListResponse {
  locations: LocationResponse[]
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

