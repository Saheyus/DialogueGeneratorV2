/**
 * Panel pour éditer les propriétés d'un nœud sélectionné.
 * Version avec React Hook Form + Zod pour validation.
 */
import { memo, useEffect } from 'react'
import { useForm, FormProvider, useFormContext, useFieldArray } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useGraphStore } from '../../store/graphStore'
import { theme } from '../../theme'
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
  const { selectedNodeId, nodes, updateNode, deleteNode } = useGraphStore()
  
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
          successNode: selectedNode?.data?.successNode || '',
          failureNode: selectedNode?.data?.failureNode || '',
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
        reset({
          id: selectedNode.id,
          speaker: selectedNode.data.speaker || '',
          line: selectedNode.data.line || '',
          choices: (selectedNode.data.choices || []) as Choice[],
          nextNode: selectedNode.data.nextNode || '',
        })
      } else if (nodeType === 'testNode') {
        reset({
          id: selectedNode.id,
          test: selectedNode.data.test || '',
          line: selectedNode.data.line || '',
          successNode: selectedNode.data.successNode || '',
          failureNode: selectedNode.data.failureNode || '',
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
    
    if (confirm(`Supprimer le nœud ${selectedNodeId} ?`)) {
      deleteNode(selectedNodeId)
    }
  }
  
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
        
        {/* Choix (pour dialogue nodes) */}
        {nodeType === 'dialogueNode' && <ChoicesEditor />}
        
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
            💾 Enregistrer
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
function ChoicesEditor() {
  const { control, watch } = useFormContext<DialogueNodeData>()
  const { fields, append, remove } = useFieldArray({
    control,
    name: 'choices',
  })
  
  const choices = watch('choices') || []
  
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
          />
        ))
      )}
    </div>
  )
}
