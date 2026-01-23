/**
 * Tests unitaires pour presetUtils
 */
import { describe, it, expect } from 'vitest';
import { filterObsoleteReferences } from './presetUtils';
import type { Preset } from '../types/preset';

describe('filterObsoleteReferences', () => {
  const createSamplePreset = (): Preset => ({
    id: 'test-preset-id',
    name: 'Test Preset',
    icon: '🎭',
    metadata: {
      created: '2026-01-15T10:00:00Z',
      modified: '2026-01-15T10:00:00Z',
    },
    configuration: {
      characters: ['Akthar', 'Neth', 'ObsoleteChar'],
      locations: ['Port de Valdris', 'ObsoleteLocation'],
      region: 'Test Region',
      subLocation: 'Test SubLocation',
      sceneType: 'Première rencontre',
      instructions: 'Test instructions',
      fieldConfigs: { category1: ['field1'] },
    },
  });

  it('should filter obsolete characters from preset', () => {
    // GIVEN
    const preset = createSamplePreset();
    const obsoleteRefs = ['ObsoleteChar'];

    // WHEN
    const filtered = filterObsoleteReferences(preset, obsoleteRefs);

    // THEN
    expect(filtered.configuration.characters).toEqual(['Akthar', 'Neth']);
    expect(filtered.configuration.characters).not.toContain('ObsoleteChar');
    // Vérifier que les autres champs sont préservés
    expect(filtered.configuration.locations).toEqual(['Port de Valdris', 'ObsoleteLocation']);
    expect(filtered.configuration.region).toBe('Test Region');
    expect(filtered.configuration.instructions).toBe('Test instructions');
  });

  it('should filter obsolete locations from preset', () => {
    // GIVEN
    const preset = createSamplePreset();
    const obsoleteRefs = ['ObsoleteLocation'];

    // WHEN
    const filtered = filterObsoleteReferences(preset, obsoleteRefs);

    // THEN
    expect(filtered.configuration.locations).toEqual(['Port de Valdris']);
    expect(filtered.configuration.locations).not.toContain('ObsoleteLocation');
    // Vérifier que les autres champs sont préservés
    expect(filtered.configuration.characters).toEqual(['Akthar', 'Neth', 'ObsoleteChar']);
    expect(filtered.configuration.region).toBe('Test Region');
  });

  it('should filter both obsolete characters and locations', () => {
    // GIVEN
    const preset = createSamplePreset();
    const obsoleteRefs = ['ObsoleteChar', 'ObsoleteLocation'];

    // WHEN
    const filtered = filterObsoleteReferences(preset, obsoleteRefs);

    // THEN
    expect(filtered.configuration.characters).toEqual(['Akthar', 'Neth']);
    expect(filtered.configuration.locations).toEqual(['Port de Valdris']);
    // Vérifier que les autres champs sont préservés
    expect(filtered.configuration.region).toBe('Test Region');
    expect(filtered.configuration.subLocation).toBe('Test SubLocation');
    expect(filtered.configuration.instructions).toBe('Test instructions');
    expect(filtered.configuration.fieldConfigs).toEqual({ category1: ['field1'] });
  });

  it('should preserve all other configuration fields', () => {
    // GIVEN
    const preset = createSamplePreset();
    const obsoleteRefs = ['ObsoleteChar', 'ObsoleteLocation'];

    // WHEN
    const filtered = filterObsoleteReferences(preset, obsoleteRefs);

    // THEN - Vérifier que tous les autres champs sont inchangés
    expect(filtered.id).toBe(preset.id);
    expect(filtered.name).toBe(preset.name);
    expect(filtered.icon).toBe(preset.icon);
    expect(filtered.metadata).toEqual(preset.metadata);
    expect(filtered.configuration.region).toBe(preset.configuration.region);
    expect(filtered.configuration.subLocation).toBe(preset.configuration.subLocation);
    expect(filtered.configuration.sceneType).toBe(preset.configuration.sceneType);
    expect(filtered.configuration.instructions).toBe(preset.configuration.instructions);
    expect(filtered.configuration.fieldConfigs).toEqual(preset.configuration.fieldConfigs);
  });

  it('should return new preset object (immutability)', () => {
    // GIVEN
    const preset = createSamplePreset();
    const obsoleteRefs = ['ObsoleteChar'];

    // WHEN
    const filtered = filterObsoleteReferences(preset, obsoleteRefs);

    // THEN - Vérifier que c'est un nouvel objet
    expect(filtered).not.toBe(preset);
    expect(filtered.configuration).not.toBe(preset.configuration);
  });

  it('should handle empty obsolete refs list', () => {
    // GIVEN
    const preset = createSamplePreset();
    const obsoleteRefs: string[] = [];

    // WHEN
    const filtered = filterObsoleteReferences(preset, obsoleteRefs);

    // THEN - Rien ne doit être filtré
    expect(filtered.configuration.characters).toEqual(preset.configuration.characters);
    expect(filtered.configuration.locations).toEqual(preset.configuration.locations);
  });

  it('should handle preset with no characters or locations', () => {
    // GIVEN
    const preset: Preset = {
      id: 'test-preset-id',
      name: 'Test Preset',
      icon: '🎭',
      metadata: {
        created: '2026-01-15T10:00:00Z',
        modified: '2026-01-15T10:00:00Z',
      },
      configuration: {
        characters: [],
        locations: [],
        region: 'Test Region',
        sceneType: 'Première rencontre',
        instructions: 'Test instructions',
      },
    };
    const obsoleteRefs = ['ObsoleteChar'];

    // WHEN
    const filtered = filterObsoleteReferences(preset, obsoleteRefs);

    // THEN - Ne doit pas crash et préserver la structure
    expect(filtered.configuration.characters).toEqual([]);
    expect(filtered.configuration.locations).toEqual([]);
    expect(filtered.configuration.region).toBe('Test Region');
  });
});
