/**
 * Store Zustand pour la gestion des presets de génération
 */
import { create } from 'zustand';
import type { Preset, PresetCreate, PresetUpdate, PresetValidationResult } from '../types/preset';

interface PresetStore {
  // État
  presets: Preset[];
  selectedPreset: Preset | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  loadPresets: () => Promise<void>;
  createPreset: (presetData: PresetCreate) => Promise<void>;
  updatePreset: (id: string, updateData: PresetUpdate) => Promise<void>;
  deletePreset: (id: string) => Promise<void>;
  loadPreset: (id: string) => Promise<void>;
  validatePreset: (id: string) => Promise<PresetValidationResult>;
  setSelectedPreset: (preset: Preset | null) => void;
  reset: () => void;
}

export const usePresetStore = create<PresetStore>((set) => ({
  // État initial
  presets: [],
  selectedPreset: null,
  isLoading: false,
  error: null,

  // Actions
  loadPresets: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch('/api/v1/presets');
      if (!response.ok) {
        throw new Error(`Failed to load presets: ${response.status}`);
      }
      const presets = await response.json();
      set({ presets, isLoading: false });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      set({ error: errorMessage, isLoading: false });
    }
  },

  createPreset: async (presetData: PresetCreate) => {
    set({ isLoading: true, error: null });
    try {
      const body = JSON.stringify(presetData);
      const response = await fetch('/api/v1/presets', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body,
      });

      if (!response.ok) {
        throw new Error(`Failed to create preset: ${response.status}`);
      }

      const newPreset = await response.json();
      set((state) => ({
        presets: [...state.presets, newPreset],
        isLoading: false,
      }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      set({ error: errorMessage, isLoading: false });
    }
  },

  updatePreset: async (id: string, updateData: PresetUpdate) => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch(`/api/v1/presets/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData),
      });

      if (!response.ok) {
        throw new Error(`Failed to update preset: ${response.status}`);
      }

      const updatedPreset = await response.json();
      set((state) => ({
        presets: state.presets.map((p) => (p.id === id ? updatedPreset : p)),
        selectedPreset: state.selectedPreset?.id === id ? updatedPreset : state.selectedPreset,
        isLoading: false,
      }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      set({ error: errorMessage, isLoading: false });
    }
  },

  deletePreset: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch(`/api/v1/presets/${id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`Failed to delete preset: ${response.status}`);
      }

      set((state) => ({
        presets: state.presets.filter((p) => p.id !== id),
        selectedPreset: state.selectedPreset?.id === id ? null : state.selectedPreset,
        isLoading: false,
      }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      set({ error: errorMessage, isLoading: false });
    }
  },

  loadPreset: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch(`/api/v1/presets/${id}`);
      if (!response.ok) {
        throw new Error(`Failed to load preset: ${response.status}`);
      }
      const preset = await response.json();
      set({ selectedPreset: preset, isLoading: false });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      set({ error: errorMessage, isLoading: false, selectedPreset: null });
    }
  },

  validatePreset: async (id: string): Promise<PresetValidationResult> => {
    try {
      const response = await fetch(`/api/v1/presets/${id}/validate`);
      if (!response.ok) {
        throw new Error(`Failed to validate preset: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      throw new Error(errorMessage);
    }
  },

  setSelectedPreset: (preset: Preset | null) => {
    set({ selectedPreset: preset });
  },

  reset: () => {
    set({
      presets: [],
      selectedPreset: null,
      isLoading: false,
      error: null,
    });
  },
}));
