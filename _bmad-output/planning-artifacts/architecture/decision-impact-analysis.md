# Decision Impact Analysis

### Implementation Sequence

Les 5 décisions d'implémentation suivent cet ordre de priorité :

1. **ID-001 (Auto-save)** : Fondamental, impacte toutes features
2. **ID-003 (Cost governance)** : Critique avant production (protection financière)
3. **ID-004 (Streaming cleanup)** : Requis pour ADR-001 (Progress Modal)
4. **ID-005 (Preset validation)** : Requis pour ADR-002 (Presets)
5. **ID-002 (Validation cycles)** : Nice-to-have, peut être post-MVP

### Cross-Component Dependencies

**Auto-save (ID-001) ↔ Streaming cleanup (ID-004):**
- Auto-save suspendu pendant génération streaming
- Reprise auto-save après cleanup (interrupted ou completed)

**Cost governance (ID-003) ↔ Streaming (ID-004):**
- Cost check **avant** démarrage stream
- Si interruption, cost partiel enregistré (tokens consommés)

**Preset validation (ID-005) ↔ Auto-save (ID-001):**
- Preset chargé → configuration modifiée → auto-save déclenché
- Validation strictness cohérente (warning vs blocking)

### Architectural Consistency

Toutes les décisions respectent les principes baseline :

- ✅ **Windows-first** : Pas d'hypothèses POSIX
- ✅ **Type safety** : TypeScript strict + Pydantic
- ✅ **Error handling** : Pas de silent failures, logs structurés
- ✅ **Testing** : Unit + Integration + E2E coverage
- ✅ **UX-first** : Informer sans bloquer workflow créatif

---
