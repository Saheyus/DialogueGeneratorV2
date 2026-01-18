/**
 * Composant ModelSelector - Sélecteur provider/model LLM
 */
import React, { useEffect } from 'react';
import { useLLMStore } from '../../store/llmStore';

export const ModelSelector: React.FC = () => {
  const {
    provider,
    model,
    availableModels,
    setProvider,
    setModel,
    loadModels,
  } = useLLMStore();

  useEffect(() => {
    loadModels();
  }, []);

  // Grouper les modèles par provider
  const modelsByProvider = availableModels.reduce((acc, m) => {
    if (!acc[m.client_type]) {
      acc[m.client_type] = [];
    }
    acc[m.client_type].push(m);
    return acc;
  }, {} as Record<string, typeof availableModels>);

  const handleModelChange = (selectedModel: typeof availableModels[0]) => {
    setProvider(selectedModel.client_type);
    setModel(selectedModel.api_identifier);
  };

  const currentModel = availableModels.find((m) => m.api_identifier === model);
  const currentModelDisplay = currentModel?.display_name || model;

  return (
    <div className="model-selector">
      <label htmlFor="model-select" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
        Modèle
      </label>
      <select
        id="model-select"
        value={model}
        onChange={(e) => {
          const selectedModel = availableModels.find((m) => m.api_identifier === e.target.value);
          if (selectedModel) {
            handleModelChange(selectedModel);
          }
        }}
        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm dark:bg-gray-800 dark:border-gray-600 dark:text-white"
      >
        {Object.entries(modelsByProvider).map(([providerType, models]) => (
          <optgroup key={providerType} label={providerType === 'openai' ? 'OpenAI' : 'Mistral'}>
            {models.map((m) => (
              <option key={m.api_identifier} value={m.api_identifier}>
                {m.display_name}
              </option>
            ))}
          </optgroup>
        ))}
      </select>
      <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
        Provider actuel: {provider === 'openai' ? 'OpenAI' : 'Mistral'}
      </div>
    </div>
  );
};
