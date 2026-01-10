/**
 * Types TypeScript pour la structure JSON du prompt.
 * Correspond aux modèles Pydantic du backend (models/prompt_structure.py).
 */

export interface ItemSection {
  title: string
  content: string
  raw_content?: Record<string, unknown> | unknown[] // Structure Python (dict/list) pour éviter conversion texte → re-parse. Si présent, utilisé en priorité.
  tokenCount?: number
}

export interface ContextItem {
  id: string
  name: string
  sections: ItemSection[]
  tokenCount?: number
  metadata?: {
    element_name?: string
    real_name?: string
    [key: string]: unknown
  }
}

export interface ContextCategory {
  type: string
  title: string
  items: ContextItem[]
  tokenCount?: number
}

export type PromptSectionType = 'system_prompt' | 'context' | 'instruction' | 'other'

export interface PromptSection {
  type: PromptSectionType
  title: string
  content: string
  tokenCount?: number
  categories?: ContextCategory[]
}

export interface PromptMetadata {
  totalTokens: number
  generatedAt: string
  organizationMode?: string
}

export interface PromptStructure {
  sections: PromptSection[]
  metadata: PromptMetadata
}
