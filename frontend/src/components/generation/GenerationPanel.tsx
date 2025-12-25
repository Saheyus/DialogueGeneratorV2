/**
 * Panneau de génération de dialogues.
 */
import { useState } from 'react'
import * as dialoguesAPI from '../../api/dialogues'
import type { GenerateDialogueVariantsRequest, DialogueVariantResponse } from '../../types/api'

export function GenerationPanel() {
  const [userInstructions, setUserInstructions] = useState('')
  const [kVariants, setKVariants] = useState(2)
  const [variants, setVariants] = useState<DialogueVariantResponse[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleGenerate = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const request: GenerateDialogueVariantsRequest = {
        k_variants: kVariants,
        user_instructions: userInstructions,
        context_selections: {
          characters: [],
          locations: [],
          items: [],
          species: [],
          communities: [],
          dialogues_examples: [],
        },
        max_context_tokens: 1500,
        structured_output: false,
        llm_model_identifier: 'gpt-4o-mini',
      }

      const response = await dialoguesAPI.generateDialogueVariants(request)
      setVariants(response.variants)
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Erreur lors de la génération')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div style={{ padding: '2rem' }}>
      <h2>Génération de Dialogues</h2>
      
      <div style={{ marginBottom: '1rem' }}>
        <label>
          Instructions:
          <textarea
            value={userInstructions}
            onChange={(e) => setUserInstructions(e.target.value)}
            rows={5}
            style={{ width: '100%', padding: '0.5rem', marginTop: '0.5rem' }}
          />
        </label>
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <label>
          Nombre de variantes:
          <input
            type="number"
            value={kVariants}
            onChange={(e) => setKVariants(parseInt(e.target.value))}
            min={1}
            max={10}
            style={{ marginLeft: '0.5rem', padding: '0.5rem' }}
          />
        </label>
      </div>

      <button onClick={handleGenerate} disabled={isLoading || !userInstructions.trim()}>
        {isLoading ? 'Génération...' : 'Générer'}
      </button>

      {error && <div style={{ color: 'red', marginTop: '1rem' }}>{error}</div>}

      {variants.length > 0 && (
        <div style={{ marginTop: '2rem' }}>
          <h3>Variantes générées:</h3>
          {variants.map((variant) => (
            <div key={variant.id} style={{ marginBottom: '1rem', padding: '1rem', border: '1px solid #ccc', borderRadius: '4px' }}>
              <h4>{variant.title}</h4>
              <p style={{ whiteSpace: 'pre-wrap' }}>{variant.content}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

