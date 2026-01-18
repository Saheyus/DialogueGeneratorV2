# Test Design: Tous les Epics - DialogueGenerator

**Date:** 2026-01-15
**Author:** Marc
**Status:** Draft (Updated after TEA Review)
**Review Date:** 2026-01-15
**Reviewer:** Murat (Master Test Architect)

**Changelog:**
- 2026-01-15: Initial test design created
- 2026-01-15: Updated after TEA review - Added NFR coverage, rebalanced test pyramid, added traceability matrix, expanded smoke tests, documented test data factories, added integration section

---

## Executive Summary

**Scope:** Test design complet pour DialogueGenerator couvrant les 16 epics (Epic 0 à Epic 15) avec évaluation des risques et stratégie de couverture.

**Risk Summary:**

- Total risks identified: 24
- High-priority risks (≥6): 8
- Critical categories: SEC, PERF, DATA, TECH

**Coverage Summary:**

- P0 scenarios: 30 tests (60 hours) - 6 E2E, 8 API, 12 Unit, 4 Component
- P1 scenarios: 52 tests (52 hours) - 10 E2E, 15 API, 20 Unit, 7 Component
- P2/P3 scenarios: 48 tests (24 hours)
- **NFR tests**: 18 tests (Security, Performance, Reliability, Maintainability)
- **Total effort**: 136 hours (~17 days) + NFR testing

---

## Risk Assessment

### High-Priority Risks (Score ≥6)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner | Timeline |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ---------- | ------- | -------- |
| R-001   | DATA     | Data loss lors de corruption graphe (stableID manquant) | 3 | 3 | 9 | Fix stableID (Epic 0 Story 0.1), validation auto-génération UUID | DEV | Epic 0 |
| R-002   | SEC      | Exposition API keys LLM au frontend | 2 | 3 | 6 | Backend-only API keys, validation config (NFR-S1) | DEV | Epic 0 |
| R-003   | PERF     | Génération LLM timeout >30s (single) ou >2min (batch) | 3 | 2 | 6 | Retry logic, fallback provider, timeout configuration | DEV | Epic 1 |
| R-004   | DATA     | Export Unity JSON invalide (schema non conforme) | 2 | 3 | 6 | Validation schema 100% avant export, tests unitaires | DEV | Epic 5 |
| R-005   | TECH     | Graph editor crash avec 500+ nœuds (rendering performance) | 2 | 3 | 6 | Virtualization, lazy loading, performance tests | DEV | Epic 2 |
| R-006   | DATA     | Auto-save écrase modifications concurrentes (LWW conflict) | 2 | 3 | 6 | Last-Write-Wins avec timestamp, warning utilisateur | DEV | Epic 10 |
| R-007   | PERF     | LLM API failure rate >10% (instabilité provider) | 3 | 2 | 6 | Fallback provider (Mistral), retry avec backoff, circuit breaker | DEV | Epic 1 |
| R-008   | SEC      | JWT token compromis ou session non sécurisée | 2 | 3 | 6 | HTTPS only, secure cookies, token rotation, RBAC validation | DEV | Epic 7 |

### Medium-Priority Risks (Score 3-4)

| Risk ID | Category | Description | Probability | Impact | Score | Mitigation | Owner |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ---------- | ------- |
| R-009   | TECH     | Cycles dans graphe non détectés (validation manquante) | 2 | 2 | 4 | Validation cycles avec warning non-bloquant (Epic 0 Story 0.4) | DEV |
| R-010   | DATA     | Contexte GDD obsolète dans presets (références invalides) | 2 | 2 | 4 | Preset validation avec warning + "Charger quand même" (Epic 0 Story 0.5) | DEV |
| R-011   | BUS      | Cost governance dépassement budget (90% soft, 100% hard) | 2 | 2 | 4 | Limites soft/hard avec alertes, blocage génération si dépassement | DEV | Epic 1 |
| R-012   | BUS      | Qualité dialogue généré <80% acceptation (re-génération fréquente) | 2 | 2 | 4 | LLM judge scoring, amélioration prompts, templates qualité | DEV | Epic 4 |
| R-013   | TECH     | Streaming cleanup timeout >10s après fin génération | 1 | 3 | 3 | Timeout 10s strict, cleanup automatique, tests E2E | DEV | Epic 0 |
| R-014   | OPS      | Auto-save suspend pendant génération (data loss potentiel) | 1 | 3 | 3 | Auto-save suspend uniquement pendant génération active | DEV | Epic 10 |

### Low-Priority Risks (Score 1-2)

| Risk ID | Category | Description | Probability | Impact | Score | Action |
| ------- | -------- | ----------- | ----------- | ------ | ----- | ------- |
| R-015   | OPS      | Monitoring metrics non disponibles (dashboard analytics) | 1 | 2 | 2 | Monitor |
| R-016   | BUS      | Onboarding wizard incomplet (première utilisation) | 1 | 2 | 2 | Monitor |
| R-017   | TECH     | Keyboard navigation partielle (accessibilité) | 1 | 2 | 2 | Monitor |
| R-018   | PERF     | Search performance dégradée avec 1000+ dialogues | 1 | 2 | 2 | Monitor |
| R-019   | DATA     | Variables non validées (références undefined) | 1 | 1 | 1 | Monitor |
| R-020   | BUS      | Template marketplace non disponible (V1.5+) | 1 | 1 | 1 | Monitor |
| R-021   | TECH     | Screen reader support incomplet (V2.0+) | 1 | 1 | 1 | Monitor |
| R-022   | OPS      | Notion sync échec (V2.0+) | 1 | 1 | 1 | Monitor |
| R-023   | BUS      | A/B testing templates non implémenté (V2.5+) | 1 | 1 | 1 | Monitor |
| R-024   | TECH     | Integration game stats non disponible (V3.0+) | 1 | 1 | 1 | Monitor |

### Risk Category Legend

- **TECH**: Technical/Architecture (flaws, integration, scalability)
- **SEC**: Security (access controls, auth, data exposure)
- **PERF**: Performance (SLA violations, degradation, resource limits)
- **DATA**: Data Integrity (loss, corruption, inconsistency)
- **BUS**: Business Impact (UX harm, logic errors, revenue)
- **OPS**: Operations (deployment, config, monitoring)

---

## Test Coverage Plan

### P0 (Critical) - Run on every commit

**Criteria**: Blocks core journey + High risk (≥6) + No workaround

**Test Pyramid Distribution:** 6 E2E, 8 API, 12 Unit, 4 Component (30 total)

#### E2E Tests (6 tests, 12 hours)

| Requirement | Risk Link | Test Count | Owner | Notes |
| ----------- | --------- | ---------- | ----- | ----- |
| Graph stableID corruption fix (Epic 0 Story 0.1) | R-001 | 1 | QA | Renommer dialogue ne casse pas connexions |
| Graph editor 500+ nodes performance (Epic 2) | R-005 | 1 | QA | Rendering <1s, zoom/pan fluide |
| Dialogue generation single node workflow (Epic 1 Story 1.1) | - | 1 | QA | Sélection contexte → génération → acceptation |
| Dialogue generation batch workflow (Epic 1 Story 1.2) | - | 1 | QA | Batch 3-8 nœuds, auto-link |
| Unity export single dialogue workflow (Epic 5) | R-004 | 1 | QA | Export → validation → download |
| Graph editor navigation (Epic 2) | - | 1 | QA | Zoom, pan, search, jump |

#### API Tests (8 tests, 16 hours)

| Requirement | Risk Link | Test Count | Owner | Notes |
| ----------- | --------- | ---------- | ----- | ----- |
| API keys security validation (NFR-S1) | R-002 | 1 | QA | Backend-only, pas d'exposition frontend |
| LLM generation timeout validation (Epic 1) | R-003 | 2 | QA | Single <30s, batch <2min, retry logic |
| Unity JSON export schema validation (Epic 5) | R-004 | 1 | QA | Schema 100% conformité |
| Auto-save LWW conflict handling (Epic 10) | R-006 | 1 | QA | Timestamp validation, warning utilisateur |
| LLM fallback provider (Epic 1) | R-007 | 2 | QA | Mistral fallback, circuit breaker |
| JWT authentication security (Epic 7) | R-008 | 1 | QA | HTTPS, secure cookies, token rotation |

#### Unit Tests (12 tests, 24 hours)

| Requirement | Risk Link | Test Count | Owner | Notes |
| ----------- | --------- | ---------- | ----- | ----- |
| Graph stableID auto-génération (Epic 0 Story 0.1) | R-001 | 2 | DEV | `generateStableID()` unicité, validation |
| Unity JSON schema validator (Epic 5) | R-004 | 3 | DEV | Schema validation logic, edge cases |
| LLM timeout calculation (Epic 1) | R-003 | 2 | DEV | Timeout logic, retry backoff |
| Auto-save LWW timestamp logic (Epic 10) | R-006 | 2 | DEV | Timestamp comparison, conflict detection |
| LLM fallback provider selection (Epic 1) | R-007 | 2 | DEV | Provider selection logic, circuit breaker state |
| Cost governance calculation (Epic 1) | R-011 | 1 | DEV | Budget calculation, soft/hard limits |

#### Component Tests (4 tests, 8 hours)

| Requirement | Risk Link | Test Count | Owner | Notes |
| ----------- | --------- | ---------- | ----- | ----- |
| GraphEditor stableID rendering (Epic 0) | R-001 | 1 | DEV | Component uses stableID, not displayName |
| GenerationProgressModal SSE streaming (Epic 0) | - | 1 | DEV | Modal displays streaming, interrupt button |
| GraphEditor virtualization (Epic 2) | R-005 | 1 | DEV | Component lazy loads nodes, performance |
| UnityExportButton validation (Epic 5) | R-004 | 1 | DEV | Button disabled if schema invalid |

**Total P0**: 30 tests, 60 hours

### P1 (High) - Run on PR to main

**Criteria**: Important features + Medium risk (3-4) + Common workflows

**Test Pyramid Distribution:** 10 E2E, 15 API, 20 Unit, 7 Component (52 total)

#### E2E Tests (10 tests, 10 hours)

| Requirement | Risk Link | Test Count | Owner | Notes |
| ----------- | --------- | ---------- | ----- | ----- |
| Progress Modal SSE streaming (Epic 0 Story 0.2) | - | 1 | QA | Modal, streaming, interrupt, reduce |
| Presets système (Epic 0 Story 0.3) | R-010 | 1 | QA | Save, load, validation références |
| Template creation workflow (Epic 6) | - | 1 | QA | Create, save, apply templates |
| User authentication workflow (Epic 7) | - | 1 | QA | Login, logout, session management |
| Dialogue search (Epic 8) | - | 1 | QA | Search by name, character, location |
| Variables & flags workflow (Epic 9) | R-019 | 1 | QA | Define, conditions, effects |
| Auto-save 2min workflow (Epic 10) | R-014 | 1 | QA | Auto-save, session recovery |
| Onboarding wizard (Epic 11/15) | R-016 | 1 | QA | First run, guided mode |
| Keyboard navigation (Epic 14) | R-017 | 1 | QA | Tab, Arrow keys, shortcuts |
| Export batch Unity (Epic 5) | - | 1 | QA | Batch export, preview |

#### API Tests (15 tests, 15 hours)

| Requirement | Risk Link | Test Count | Owner | Notes |
| ----------- | --------- | ---------- | ----- | ----- |
| Multi-provider LLM selection (Epic 0 Story 0.4) | - | 2 | QA | OpenAI, Mistral, sélection utilisateur |
| Validation cycles warning (Epic 0 Story 0.5) | R-009 | 1 | QA | Détection cycles, warning non-bloquant |
| Cost governance endpoints (Epic 1 Story 1.5) | R-011 | 2 | QA | Limites 90%/100%, alertes, blocage |
| Dialogue quality LLM judge endpoint (Epic 4) | R-012 | 2 | QA | Scoring 0-10, variance ±1 |
| RBAC roles validation (Epic 7) | - | 3 | QA | Admin, Writer, Viewer permissions |
| Context budget tokens optimization (Epic 3) | - | 2 | QA | Optimization contexte, budget management |
| Batch validation dialogues (Epic 4) | - | 2 | QA | Validation multiple dialogues |
| Dialogue metadata endpoints (Epic 8) | - | 1 | QA | Node count, cost, last edited |

#### Unit Tests (20 tests, 20 hours)

| Requirement | Risk Link | Test Count | Owner | Notes |
| ----------- | --------- | ---------- | ----- | ----- |
| Preset validation logic (Epic 0) | R-010 | 2 | DEV | Validation références obsolètes |
| LLM provider factory (Epic 0) | - | 2 | DEV | Provider selection, fallback logic |
| Cycle detection algorithm (Epic 0) | R-009 | 2 | DEV | Graph cycle detection, warning logic |
| Cost calculation service (Epic 1) | R-011 | 3 | DEV | Budget calculation, soft/hard limits |
| LLM judge scoring algorithm (Epic 4) | R-012 | 3 | DEV | Scoring 0-10, variance calculation |
| RBAC permission checker (Epic 7) | - | 3 | DEV | Role-based access control logic |
| Context budget optimizer (Epic 3) | - | 2 | DEV | Token budget optimization |
| Dialogue validator (Epic 4) | - | 3 | DEV | Structure validation, orphans, cycles |

#### Component Tests (7 tests, 7 hours)

| Requirement | Risk Link | Test Count | Owner | Notes |
| ----------- | --------- | ---------- | ----- | ----- |
| PresetSelector component (Epic 0) | R-010 | 1 | DEV | Save, load, validation UI |
| LLMProviderSelector component (Epic 0) | - | 1 | DEV | Provider selection UI |
| CostGovernanceAlert component (Epic 1) | R-011 | 1 | DEV | Soft/hard limit alerts |
| DialogueQualityScore component (Epic 4) | R-012 | 1 | DEV | LLM judge score display |
| RBACPermissionGuard component (Epic 7) | - | 1 | DEV | Role-based UI rendering |
| AutoSaveIndicator component (Epic 10) | R-014 | 1 | DEV | Auto-save status display |
| KeyboardNavigationFocus component (Epic 14) | R-017 | 1 | DEV | Focus management, shortcuts |

**Total P1**: 52 tests, 52 hours

### P2 (Medium) - Run nightly/weekly

**Criteria**: Secondary features + Low risk (1-2) + Edge cases

| Requirement | Test Level | Risk Link | Test Count | Owner | Notes |
| ----------- | --------- | --------- | ---------- | ----- | ----- |
| Preset validation warning (Epic 0) | E2E | R-010 | 2 | QA | Warning modal, "Charger quand même" |
| Streaming cleanup timeout (Epic 0) | API | R-013 | 2 | QA | Timeout 10s, cleanup automatique |
| Dialogue editing manual (Epic 1) | E2E | - | 3 | QA | Edit text, speaker, metadata |
| Dialogue duplication (Epic 1) | E2E | - | 2 | QA | Duplicate nodes, create variations |
| Context relevance measurement (Epic 3) | API | - | 2 | QA | % GDD used in dialogue |
| Lore contradictions detection (Epic 4) | API | - | 3 | QA | Explicit contradictions, potential issues |
| AI slop detection (Epic 4) | API | - | 2 | QA | GPT-isms, repetition, generic phrases |
| Context dropping detection (Epic 4) | API | - | 2 | QA | Lore explicite vs subtil |
| Template marketplace (Epic 6) | E2E | R-020 | 2 | QA | Browse, share templates (V1.5+) |
| Dialogue sharing (Epic 7) | E2E | - | 2 | QA | Share with team members |
| Dialogue collections (Epic 8) | E2E | - | 2 | QA | Create folders, organize |
| Variable preview scenarios (Epic 9) | E2E | - | 2 | QA | Preview with different variable states |
| Dialogue history (Epic 10) | E2E | - | 2 | QA | Basic history MVP, detailed V2.0+ |
| Contextual help (Epic 11) | E2E | - | 2 | QA | In-app documentation, tutorials |
| Power mode toggle (Epic 12) | E2E | - | 2 | QA | Advanced features, full control |
| Preview before generation (Epic 12) | E2E | - | 2 | QA | Dry-run mode, estimated structure |
| Node comparison (Epic 12) | E2E | - | 2 | QA | Side-by-side comparison |
| Performance metrics (Epic 13) | E2E | R-015 | 2 | QA | Generation time, API latency |
| Color contrast customization (Epic 14) | E2E | - | 2 | QA | WCAG AA minimum |
| Screen reader support (Epic 14) | E2E | R-021 | 2 | QA | ARIA labels (V2.0+) |

**Total P2**: 40 tests, 20 hours

### P3 (Low) - Run on-demand

**Criteria**: Nice-to-have + Exploratory + Performance benchmarks

| Requirement | Test Level | Test Count | Owner | Notes |
| ----------- | ---------- | ---------- | ----- | ----- |
| Notion sync GDD (Epic 3) | API | 2 | QA | Webhook/polling (V2.0+) |
| A/B testing templates (Epic 6) | E2E | 2 | QA | Template quality scoring (V2.5+) |
| Game stats integration (Epic 9) | API | 2 | QA | Character attributes, reputation (V3.0+) |
| Search performance 1000+ (Epic 8) | E2E | R-018 | 2 | QA | Indexation rapide, large base |

**Total P3**: 8 tests, 4 hours

---

## Execution Order

### Smoke Tests (<7 min)

**Purpose**: Fast feedback, catch build-breaking issues

- [ ] Graph stableID validation (E2E) - 1min
- [ ] LLM generation single node (E2E) - 2min
- [ ] Unity JSON export validation (API) - 30s
- [ ] JWT authentication (API) - 1min
- [ ] Graph editor loads (E2E) - 30s
- [ ] Context GDD selection (E2E) - 1min
- [ ] Health check endpoint (API) - 10s
- [ ] Auto-save triggers (API) - 30s

**Total**: 8 scenarios (~7 min)

### P0 Tests (<40 min)

**Purpose**: Critical path validation

**E2E (6 tests, ~18 min):**
- [ ] Graph stableID corruption fix
- [ ] Graph editor 500+ nodes performance
- [ ] Dialogue generation single workflow
- [ ] Dialogue generation batch workflow
- [ ] Unity export single dialogue workflow
- [ ] Graph editor navigation

**API (8 tests, ~12 min):**
- [ ] API keys security validation
- [ ] LLM generation timeout validation (single)
- [ ] LLM generation timeout validation (batch)
- [ ] Unity JSON export schema validation
- [ ] Auto-save LWW conflict handling
- [ ] LLM fallback provider (OpenAI fail)
- [ ] LLM fallback provider (Mistral success)
- [ ] JWT authentication security

**Unit (12 tests, ~8 min):**
- [ ] Graph stableID auto-génération (unicité)
- [ ] Graph stableID auto-génération (validation)
- [ ] Unity JSON schema validator (structure)
- [ ] Unity JSON schema validator (edge cases)
- [ ] Unity JSON schema validator (error handling)
- [ ] LLM timeout calculation (single)
- [ ] LLM timeout calculation (batch)
- [ ] Auto-save LWW timestamp logic (comparison)
- [ ] Auto-save LWW timestamp logic (conflict)
- [ ] LLM fallback provider selection (logic)
- [ ] LLM fallback circuit breaker (state)
- [ ] Cost governance calculation

**Component (4 tests, ~2 min):**
- [ ] GraphEditor stableID rendering
- [ ] GenerationProgressModal SSE streaming
- [ ] GraphEditor virtualization
- [ ] UnityExportButton validation

**Total**: 30 scenarios (~40 min)

### P1 Tests (<30 min)

**Purpose**: Important feature coverage

- [ ] Progress Modal SSE (E2E)
- [ ] Presets système (E2E)
- [ ] Multi-provider LLM (API)
- [ ] Validation cycles (API)
- [ ] Cost governance (API)
- [ ] Dialogue quality LLM judge (API)
- [ ] Template creation (E2E)
- [ ] User authentication (E2E)
- [ ] RBAC roles (API)
- [ ] Dialogue search (E2E)
- [ ] Variables & flags (E2E)
- [ ] Auto-save 2min (E2E)
- [ ] Onboarding wizard (E2E)
- [ ] Keyboard navigation (E2E)
- [ ] Context budget tokens (API)
- [ ] Batch validation (API)
- [ ] Export batch Unity (E2E)
- [ ] Dialogue metadata (E2E)

**Total**: 18 scenarios

### P2/P3 Tests (<60 min)

**Purpose**: Full regression coverage

- [ ] All P2 scenarios (40 tests)
- [ ] All P3 scenarios (8 tests)

**Total**: 48 scenarios

---

## Resource Estimates

### Test Development Effort

| Priority | Count | Hours/Test | Total Hours | Notes |
| --------- | ----- | ---------- | ----------- | ----- |
| P0        | 30    | 2.0        | 60          | Complex setup, security, E2E + Unit |
| P1        | 52    | 1.0        | 52          | Standard coverage, API + E2E + Unit |
| P2        | 40    | 0.5        | 20          | Simple scenarios, edge cases |
| P3        | 8     | 0.5        | 4           | Exploratory, performance |
| **NFR**   | **18** | **1.5**    | **27**      | Security, Performance, Reliability, Maintainability |
| **Total** | **148** | **-** | **163** | **~20 days** |

### Prerequisites

**Test Data Factories:**

#### GDD Data Factories (`tests/support/factories/gdd-factory.ts`):
```typescript
// Character factory (faker-based, auto-cleanup)
export function createCharacter(overrides?: Partial<Character>): Character {
  return {
    Nom: faker.person.fullName(),
    sections: {
      Introduction: { _general: faker.lorem.paragraph() },
      Description: { _general: faker.lorem.paragraphs(2) },
      // ... other sections
    },
    ...overrides,
  };
}

// Location factory
export function createLocation(overrides?: Partial<Location>): Location {
  return {
    Nom: faker.location.city(),
    sections: {
      Introduction: { _general: faker.lorem.paragraph() },
      // ... other sections
    },
    ...overrides,
  };
}

// Region factory
export function createRegion(overrides?: Partial<Region>): Region {
  return {
    Nom: faker.location.country(),
    sections: {
      Introduction: { _general: faker.lorem.paragraph() },
      // ... other sections
    },
    ...overrides,
  };
}
```

#### Dialogue Fixtures (`tests/support/fixtures/dialogue-fixtures.ts`):
```typescript
// Empty dialogue fixture
export const emptyDialogue = {
  nodes: [],
  connections: [],
  stableID: faker.string.uuid(),
  displayName: 'Empty Dialogue',
};

// Single node dialogue fixture
export const singleNodeDialogue = {
  nodes: [createNode({ text: 'Hello', speaker: 'NPC' })],
  connections: [],
  stableID: faker.string.uuid(),
  displayName: 'Single Node Dialogue',
};

// Large dialogue fixture (500+ nodes)
export const largeDialogue = {
  nodes: Array(500).fill(null).map((_, i) => createNode({
    stableID: faker.string.uuid(),
    text: `Node ${i}`,
    speaker: i % 2 === 0 ? 'NPC' : 'Player',
  })),
  connections: generateConnections(500),
  stableID: faker.string.uuid(),
  displayName: 'Large Dialogue (500+ nodes)',
};
```

#### User Fixtures (`tests/support/fixtures/user-fixtures.ts`):
```typescript
// Admin user fixture
export const adminUser = {
  id: faker.string.uuid(),
  email: 'admin@example.com',
  role: 'Admin',
  permissions: ['read', 'write', 'delete', 'admin'],
};

// Writer user fixture
export const writerUser = {
  id: faker.string.uuid(),
  email: 'writer@example.com',
  role: 'Writer',
  permissions: ['read', 'write'],
};

// Viewer user fixture
export const viewerUser = {
  id: faker.string.uuid(),
  email: 'viewer@example.com',
  role: 'Viewer',
  permissions: ['read'],
};
```

#### LLM Response Mocks (`tests/support/mocks/llm-mocks.ts`):
```typescript
// OpenAI response mock
export const mockOpenAIResponse = {
  choices: [{
    message: {
      content: JSON.stringify({
        text: 'Generated dialogue text',
        speaker: 'NPC',
        choices: ['Choice 1', 'Choice 2'],
      }),
    },
  }],
  usage: { total_tokens: 150, prompt_tokens: 100, completion_tokens: 50 },
};

// Mistral response mock
export const mockMistralResponse = {
  choices: [{
    message: {
      content: JSON.stringify({
        text: 'Generated dialogue text',
        speaker: 'NPC',
        choices: ['Choice 1', 'Choice 2'],
      }),
    },
  }],
  usage: { total_tokens: 150, prompt_tokens: 100, completion_tokens: 50 },
};

// LLM error mock (for fallback testing)
export const mockLLMError = {
  error: {
    type: 'server_error',
    message: 'Service temporarily unavailable',
  },
};
```

**Tooling:**

- **Playwright** for E2E tests (React frontend)
- **pytest** for API/service tests (FastAPI backend)
- **Vitest + React Testing Library** for component tests
- **TestClient FastAPI** for API integration tests
- **k6** for performance load testing (NFR-P1, P2, P3, P5)
- **faker** for test data generation (characters, locations, dialogues)

**Environment:**

- Local development (Windows-first)
- Test GDD data (link symbolique `data/GDD_categories/`)
- Mock LLM providers (OpenAI, Mistral) for cost control
- Test database (in-memory or SQLite) for user/auth tests
- k6 load testing environment (staging or production-like)

---

## Quality Gate Criteria

### Pass/Fail Thresholds

- **P0 pass rate**: 100% (no exceptions)
- **P1 pass rate**: ≥95% (waivers required for failures)
- **P2/P3 pass rate**: ≥90% (informational)
- **High-risk mitigations**: 100% complete or approved waivers

### Coverage Targets

- **Critical paths**: ≥80% (Epic 0, 1, 2, 5)
- **Security scenarios**: 100% (Epic 0, 7)
- **Business logic**: ≥70% (Epic 1, 3, 4, 6)
- **Edge cases**: ≥50% (Epic 2, 8, 9, 10)

### NFR Gate Criteria

#### Security NFR (100% pass rate required):
- [ ] Unauthenticated access redirected (not exposed)
- [ ] JWT token expiry (15min) validated
- [ ] Passwords never logged or exposed
- [ ] RBAC enforced (403 for insufficient permissions)
- [ ] SQL injection blocked
- [ ] XSS attempts sanitized
- [ ] API keys never exposed to frontend

#### Performance NFR (SLO/SLA targets):
- [ ] LLM generation <30s single, <2min batch (NFR-P2) - k6 load test
- [ ] Graph editor rendering <1s for 500+ nodes (NFR-P1) - Playwright performance
- [ ] API response time <200ms non-LLM endpoints (NFR-P3) - k6 load test
- [ ] UI interaction <100ms (NFR-P4) - Playwright performance
- [ ] Initial page load FCP <1.5s, TTI <3s, LCP <2.5s (NFR-P5) - Lighthouse

#### Reliability NFR (>95% recovery rate):
- [ ] LLM API failure recovery >95% (NFR-R4) - API tests
- [ ] Error handling graceful (500 → user-friendly message) - E2E tests
- [ ] Retry logic (3 attempts with backoff) - API tests
- [ ] Circuit breaker (opens after failure threshold) - API tests
- [ ] Health check endpoint (`/api/health`) - API tests
- [ ] Auto-save data loss prevention (NFR-R3) - E2E tests

#### Maintainability NFR (CI Tools):
- [ ] Test coverage ≥80% (from CI coverage report)
- [ ] Code duplication <5% (from jscpd CI job)
- [ ] No critical/high vulnerabilities (from npm audit CI job)
- [ ] Structured logging validated (telemetry headers) - E2E tests
- [ ] Error tracking configured (Sentry/monitoring) - E2E tests

### Non-Negotiable Requirements

- [ ] All P0 tests pass
- [ ] No high-risk (≥6) items unmitigated
- [ ] Security tests (SEC category) pass 100%
- [ ] Performance targets met (PERF category) - k6 evidence
- [ ] Reliability targets met (NFR-R4 >95% recovery)
- [ ] Zero blocking bugs (NFR-R1)

---

## Mitigation Plans

### R-001: Data loss lors de corruption graphe (Score: 9)

**Mitigation Strategy:** 
- Fix stableID dans Epic 0 Story 0.1 (Graph Editor Fixes)
- Auto-génération UUID si stableID manquant (données legacy)
- Validation stableID unicité avant sauvegarde
- Script migration données existantes (backup + génération UUID)
- Tests Unit : `generateStableID()` unicité, validation
- Tests API : Serialization/deserialization avec stableID
- Tests E2E : Renommer dialogue ne casse pas connexions
- Tests Component : GraphEditor utilise stableID, pas displayName

**Owner:** DEV
**Timeline:** Epic 0 (Sprint 1)
**Status:** Planned
**Verification:** Unit/API/E2E/Component tests P0 passent, graphe stable après renommage, data migration script tested

### R-002: Exposition API keys LLM au frontend (Score: 6)

**Mitigation Strategy:**
- Backend-only API keys (jamais exposées au frontend)
- Validation config (NFR-S1) : vérifier que `OPENAI_API_KEY` n'est jamais dans le code frontend
- Environment variables sécurisées (`.env` backend uniquement)
- Tests API : Vérifier que endpoints LLM ne retournent jamais les clés

**Owner:** DEV
**Timeline:** Epic 0 (Sprint 1)
**Status:** Planned
**Verification:** Security audit, tests API P0 passent

### R-003: Génération LLM timeout >30s (single) ou >2min (batch) (Score: 6)

**Mitigation Strategy:**
- Retry logic avec backoff exponentiel (3 tentatives max)
- Fallback provider (Mistral si OpenAI fail)
- Timeout configuration (30s single, 2min batch)
- Circuit breaker pour éviter cascading failures
- Tests API : Vérifier timeouts respectés, fallback fonctionne

**Owner:** DEV
**Timeline:** Epic 1 (Sprint 2-3)
**Status:** Planned
**Verification:** Tests API P0 passent, métriques performance <30s/<2min

### R-004: Export Unity JSON invalide (schema non conforme) (Score: 6)

**Mitigation Strategy:**
- Validation schema 100% avant export (Unity custom schema)
- Tests unitaires : Validation JSON structure (DisplayName, stableID, text, etc.)
- Tests API : Export → validation → erreur si non conforme
- Tests E2E : Export → import Unity → vérifier validité

**Owner:** DEV
**Timeline:** Epic 5 (Sprint 4-5)
**Status:** Planned
**Verification:** Tests API/E2E P0 passent, 100% conformité schema

### R-005: Graph editor crash avec 500+ nœuds (Score: 6)

**Mitigation Strategy:**
- Virtualization (React Window ou similar) pour rendering efficace
- Lazy loading nœuds (charger uniquement nœuds visibles)
- Performance tests : Mesurer rendering time <1s pour 500+ nœuds
- Tests E2E : Graphe 500+ nœuds, zoom/pan fluide

**Owner:** DEV
**Timeline:** Epic 2 (Sprint 3-4)
**Status:** Planned
**Verification:** Performance tests passent, E2E tests P0 passent

### R-006: Auto-save écrase modifications concurrentes (Score: 6)

**Mitigation Strategy:**
- Last-Write-Wins (LWW) avec timestamp
- Warning utilisateur si conflit détecté (modification depuis dernier save)
- Auto-save suspend pendant génération active (éviter conflits)
- Tests API : Simuler modifications concurrentes, vérifier LWW

**Owner:** DEV
**Timeline:** Epic 10 (Sprint 5-6)
**Status:** Planned
**Verification:** Tests API P0 passent, warning affiché si conflit

### R-007: LLM API failure rate >10% (Score: 6)

**Mitigation Strategy:**
- Fallback provider (Mistral si OpenAI fail)
- Retry avec backoff exponentiel (3 tentatives)
- Circuit breaker pour éviter cascading failures
- Monitoring métriques (failure rate, retry count)
- Tests API : Simuler failures, vérifier fallback/retry

**Owner:** DEV
**Timeline:** Epic 1 (Sprint 2-3)
**Status:** Planned
**Verification:** Tests API P0 passent, failure rate <10%

### R-008: JWT token compromis ou session non sécurisée (Score: 6)

**Mitigation Strategy:**
- HTTPS only (pas de HTTP en production)
- Secure cookies (httpOnly, secure, sameSite)
- Token rotation (refresh token 7 jours, access token 15min)
- RBAC validation backend (jamais frontend-only)
- Tests API : Vérifier sécurité cookies, token validation

**Owner:** DEV
**Timeline:** Epic 7 (Sprint 6-7)
**Status:** Planned
**Verification:** Security audit, tests API P0 passent

---

## Assumptions and Dependencies

### Assumptions

1. GDD data externe (non modifiable) disponible via lien symbolique `data/GDD_categories/`
2. LLM providers (OpenAI, Mistral) disponibles avec API keys valides
3. Unity Dialogue System compatible avec format JSON exporté
4. Windows-first environnement (pathlib.Path, encodage utf-8)
5. Git repository disponible pour versioning dialogues
6. 3-5 utilisateurs concurrents (MVP), scaling à 10+ (V2.0+)

### Dependencies

1. Epic 0 (Infrastructure) - Required by Sprint 1 (base technique)
2. Epic 1 (Génération) - Required by Sprint 2-3 (core feature)
3. Epic 3 (Contexte GDD) - Required by Epic 1 (génération nécessite contexte)
4. Epic 2 (Graph Editor) - Required by Sprint 3-4 (visualisation/édition)
5. Epic 5 (Export Unity) - Required by Sprint 4-5 (intégration production)
6. Epic 7 (Auth/RBAC) - Required by Sprint 6-7 (collaboration)

### Risks to Plan

- **Risk**: LLM provider downtime (OpenAI/Mistral unavailable)
  - **Impact**: Génération bloquée, production narrative arrêtée
  - **Contingency**: Fallback provider automatique, cache prompts si possible

- **Risk**: GDD data corruption ou sync Notion échec (V2.0+)
  - **Impact**: Contexte narratif obsolète, dialogues incohérents
  - **Contingency**: Backup GDD local, validation données avant génération

- **Risk**: Performance dégradée avec 1000+ dialogues
  - **Impact**: Search/navigation lente, UX dégradée
  - **Contingency**: Indexation optimisée, pagination, lazy loading

---

## NFR Test Coverage

### Security NFR Tests (Playwright E2E - P0)

| Test Scenario | Tool | Priority | Risk Link | Notes |
| ------------- | ---- | -------- | --------- | ----- |
| Unauthenticated access redirected | Playwright | P0 | R-002 | Redirect to login, no data exposed |
| JWT token expiry (15min) | Playwright | P0 | R-008 | Token expires, API call fails |
| Passwords never logged or exposed | Playwright | P0 | R-002 | No password in console, DOM, network |
| RBAC enforced (403 for insufficient permissions) | Playwright | P0 | R-008 | User A cannot access User B resources |
| SQL injection blocked | Playwright | P0 | R-002 | Input sanitization, no SQL execution |
| XSS attempts sanitized | Playwright | P0 | R-002 | Script tags escaped, not executed |
| API keys never exposed to frontend | Playwright | P0 | R-002 | No API keys in frontend code/network |

**Total**: 7 Security tests (P0)

### Performance NFR Tests (k6 Load Testing - P0)

| Test Scenario | Tool | Priority | NFR Link | Threshold | Notes |
| ------------- | ---- | -------- | -------- | --------- | ----- |
| LLM generation single <30s | k6 | P0 | NFR-P2 | p95 <30s | Load test generation endpoint |
| LLM generation batch <2min | k6 | P0 | NFR-P2 | p95 <2min | Load test batch endpoint |
| Graph editor rendering <1s (500+ nodes) | Playwright | P0 | NFR-P1 | <1s | Performance test rendering |
| API response time <200ms (non-LLM) | k6 | P0 | NFR-P3 | p95 <200ms | Load test API endpoints |
| UI interaction <100ms | Playwright | P0 | NFR-P4 | <100ms | Performance test interactions |
| Initial page load (FCP <1.5s, TTI <3s, LCP <2.5s) | Lighthouse | P0 | NFR-P5 | FCP<1.5s, TTI<3s, LCP<2.5s | Core Web Vitals |

**Total**: 6 Performance tests (P0)

### Reliability NFR Tests (Playwright E2E + API - P0)

| Test Scenario | Tool | Priority | NFR Link | Notes |
| ------------- | ---- | -------- | -------- | ----- |
| LLM API failure recovery >95% | API | P0 | NFR-R4 | Retry logic, fallback provider |
| Error handling graceful (500 → user message) | Playwright | P0 | NFR-R1 | User-friendly error, retry button |
| Retry logic (3 attempts with backoff) | API | P0 | NFR-R4 | Transient failures → eventual success |
| Circuit breaker (opens after threshold) | API | P0 | NFR-R4 | Stops retries after 5 failures |
| Health check endpoint (`/api/health`) | API | P0 | NFR-R2 | Service status monitoring |
| Auto-save data loss prevention | Playwright | P0 | NFR-R3 | Auto-save, session recovery |

**Total**: 6 Reliability tests (P0)

### Maintainability NFR Tests (CI Tools - P1)

| Test Scenario | Tool | Priority | Notes |
| ------------- | ---- | -------- | ----- |
| Test coverage ≥80% | CI (coverage report) | P1 | Code coverage threshold |
| Code duplication <5% | CI (jscpd) | P1 | Duplication threshold |
| No critical/high vulnerabilities | CI (npm audit) | P1 | Security vulnerabilities |
| Structured logging validated | Playwright | P1 | Telemetry headers, trace IDs |
| Error tracking configured | Playwright | P1 | Sentry/monitoring integration |

**Total**: 5 Maintainability tests (P1)

**NFR Test Summary**: 24 NFR tests (18 P0, 5 P1)

---

## Traceability Matrix

### Requirements-to-Tests Mapping

| Epic | Story | Acceptance Criteria | Test Scenario | Test Level | Priority | Risk Link |
|------|-------|---------------------|---------------|------------|----------|-----------|
| Epic 0 | 0.1 | stableID auto-génération si manquant | `test_stableid_auto_generation()` | Unit | P0 | R-001 |
| Epic 0 | 0.1 | stableID unicité validation | `test_stableid_uniqueness()` | Unit | P0 | R-001 |
| Epic 0 | 0.1 | Renommer dialogue ne casse pas connexions | `test_rename_dialogue_connections_intact()` | E2E | P0 | R-001 |
| Epic 0 | 0.1 | GraphEditor utilise stableID | `test_graph_editor_uses_stableid()` | Component | P0 | R-001 |
| Epic 0 | 0.2 | Modal affiche streaming SSE | `test_progress_modal_sse_streaming()` | Component | P1 | - |
| Epic 0 | 0.2 | Interrompre génération proprement | `test_interrupt_generation()` | E2E | P1 | - |
| Epic 0 | 0.3 | Presets save/load | `test_presets_save_load()` | E2E | P1 | R-010 |
| Epic 0 | 0.3 | Preset validation références | `test_preset_validation()` | Unit | P1 | R-010 |
| Epic 0 | 0.4 | Multi-provider LLM selection | `test_llm_provider_selection()` | API | P1 | - |
| Epic 0 | 0.4 | Fallback provider (Mistral) | `test_llm_fallback_provider()` | API | P0 | R-007 |
| Epic 0 | 0.5 | Validation cycles warning | `test_cycle_detection_warning()` | API | P1 | R-009 |
| Epic 1 | 1.1 | Génération single <30s | `test_llm_generation_timeout_single()` | API | P0 | R-003 |
| Epic 1 | 1.1 | Génération single workflow | `test_dialogue_generation_single_workflow()` | E2E | P0 | - |
| Epic 1 | 1.2 | Génération batch <2min | `test_llm_generation_timeout_batch()` | API | P0 | R-003 |
| Epic 1 | 1.2 | Génération batch workflow | `test_dialogue_generation_batch_workflow()` | E2E | P0 | - |
| Epic 1 | 1.5 | Cost governance limites | `test_cost_governance_limits()` | API | P1 | R-011 |
| Epic 2 | 2.1 | Graph editor 500+ nodes <1s | `test_graph_editor_performance_500_nodes()` | E2E | P0 | R-005 |
| Epic 2 | 2.1 | GraphEditor virtualization | `test_graph_editor_virtualization()` | Component | P0 | R-005 |
| Epic 2 | 2.2 | Graph navigation (zoom, pan) | `test_graph_editor_navigation()` | E2E | P0 | - |
| Epic 3 | 3.1 | Context GDD selection | `test_context_gdd_selection()` | E2E | P0 | - |
| Epic 3 | 3.2 | Context budget tokens | `test_context_budget_optimization()` | API | P1 | - |
| Epic 4 | 4.1 | Validation structurelle (orphans, cycles) | `test_validation_structurelle()` | API | P0 | - |
| Epic 4 | 4.2 | Dialogue quality LLM judge | `test_llm_judge_scoring()` | API | P1 | R-012 |
| Epic 5 | 5.1 | Unity JSON export schema 100% | `test_unity_export_schema_validation()` | API | P0 | R-004 |
| Epic 5 | 5.1 | Unity JSON schema validator | `test_unity_schema_validator()` | Unit | P0 | R-004 |
| Epic 5 | 5.1 | Unity export workflow | `test_unity_export_workflow()` | E2E | P0 | R-004 |
| Epic 7 | 7.1 | JWT authentication security | `test_jwt_authentication_security()` | API | P0 | R-008 |
| Epic 7 | 7.2 | RBAC roles validation | `test_rbac_roles_validation()` | API | P1 | - |
| Epic 10 | 10.1 | Auto-save LWW conflict | `test_auto_save_lww_conflict()` | API | P0 | R-006 |
| Epic 10 | 10.1 | Auto-save 2min workflow | `test_auto_save_workflow()` | E2E | P1 | R-014 |

### Risk-to-Tests Mapping

| Risk ID | Risk Description | Test Scenarios | Test Count |
|---------|------------------|----------------|------------|
| R-001 | Data loss corruption graphe | `test_stableid_*`, `test_rename_dialogue_*`, `test_graph_editor_uses_stableid` | 4 (Unit, API, E2E, Component) |
| R-002 | Exposition API keys | `test_api_keys_security`, `test_unauthenticated_redirect`, `test_passwords_never_logged` | 3 (API, E2E) |
| R-003 | LLM timeout | `test_llm_generation_timeout_single`, `test_llm_generation_timeout_batch`, `test_llm_timeout_calculation` | 4 (API, Unit) |
| R-004 | Unity JSON invalide | `test_unity_export_schema_validation`, `test_unity_schema_validator`, `test_unity_export_workflow` | 4 (API, Unit, E2E) |
| R-005 | Graph editor crash 500+ nodes | `test_graph_editor_performance_500_nodes`, `test_graph_editor_virtualization` | 2 (E2E, Component) |
| R-006 | Auto-save LWW conflict | `test_auto_save_lww_conflict`, `test_auto_save_timestamp_logic` | 3 (API, Unit) |
| R-007 | LLM API failure >10% | `test_llm_fallback_provider`, `test_llm_fallback_selection`, `test_circuit_breaker` | 4 (API, Unit) |
| R-008 | JWT compromis | `test_jwt_authentication_security`, `test_jwt_token_expiry`, `test_rbac_enforced` | 4 (API, E2E) |

### NFR-to-Tests Mapping

| NFR | NFR Description | Test Scenarios | Test Count |
|-----|-----------------|----------------|------------|
| NFR-S1 | API Key Protection | `test_api_keys_security`, `test_unauthenticated_redirect`, `test_passwords_never_logged` | 3 (E2E) |
| NFR-S2 | Auth & Session Security | `test_jwt_authentication_security`, `test_jwt_token_expiry`, `test_rbac_enforced` | 3 (E2E) |
| NFR-P1 | Graph Editor Performance | `test_graph_editor_performance_500_nodes`, `test_graph_editor_virtualization` | 2 (E2E, Component) |
| NFR-P2 | LLM Generation Performance | `test_llm_generation_timeout_single`, `test_llm_generation_timeout_batch` | 2 (k6) |
| NFR-P3 | API Response Time | `test_api_response_time_non_llm` | 1 (k6) |
| NFR-P4 | UI Interaction Responsiveness | `test_ui_interaction_responsiveness` | 1 (Playwright) |
| NFR-P5 | Initial Page Load | `test_initial_page_load_web_vitals` | 1 (Lighthouse) |
| NFR-R1 | Zero Blocking Bugs | `test_error_handling_graceful`, `test_auto_save_data_loss_prevention` | 2 (E2E) |
| NFR-R2 | System Uptime | `test_health_check_endpoint` | 1 (API) |
| NFR-R3 | Data Loss Prevention | `test_auto_save_data_loss_prevention` | 1 (E2E) |
| NFR-R4 | Error Recovery LLM | `test_llm_failure_recovery`, `test_retry_logic`, `test_circuit_breaker` | 3 (API) |

---

## Integration with Existing Test Structure

### Test File Organization

**Backend Tests (pytest):**
- `tests/api/test_*.py` - API endpoint tests (P0-P1)
- `tests/services/test_*.py` - Service layer tests (P0-P1)
- `tests/core/test_*.py` - Core logic tests (P0-P1)
- `tests/utils/test_*.py` - Utility tests (P2-P3)

**Frontend Tests (Vitest + React Testing Library):**
- `tests/frontend/test_*.test.tsx` - Component tests (P0-P1)
- `tests/frontend/test_*.test.ts` - Utility tests (P2-P3)

**E2E Tests (Playwright):**
- `e2e/*.spec.ts` - End-to-end tests (P0-P1)

**NFR Tests:**
- `tests/nfr/security.spec.ts` - Security NFR tests (Playwright E2E)
- `tests/nfr/performance.k6.js` - Performance NFR tests (k6)
- `tests/nfr/reliability.spec.ts` - Reliability NFR tests (Playwright E2E + API)
- `.github/workflows/nfr-maintainability.yml` - Maintainability NFR tests (CI)

### Test Markers (pytest)

```python
@pytest.mark.p0  # Critical tests (run on every commit)
@pytest.mark.p1  # High priority (run on PR to main)
@pytest.mark.p2  # Medium priority (run nightly)
@pytest.mark.p3  # Low priority (run on-demand)
@pytest.mark.e2e  # End-to-end tests
@pytest.mark.api  # API tests
@pytest.mark.unit  # Unit tests
@pytest.mark.component  # Component tests
@pytest.mark.nfr_security  # Security NFR tests
@pytest.mark.nfr_performance  # Performance NFR tests
@pytest.mark.nfr_reliability  # Reliability NFR tests
```

### Test Execution Commands

```bash
# P0 tests only (smoke + critical)
pytest -m "p0"  # Backend
npm run test:p0  # Frontend
npx playwright test --grep @p0  # E2E

# P0 + P1 tests (core functionality)
pytest -m "p0 or p1"  # Backend
npm run test:p1  # Frontend
npx playwright test --grep "@p0|@p1"  # E2E

# NFR tests
npx playwright test tests/nfr/security.spec.ts  # Security
k6 run tests/nfr/performance.k6.js  # Performance
pytest -m nfr_reliability  # Reliability
```

---

## Follow-on Workflows (Manual)

- Run `*atdd` to generate failing P0 tests (separate workflow; not auto-run).
- Run `*automate` for broader coverage once implementation exists.
- Run `*ci` to configure CI/CD pipeline with test execution order.
- Run `*nfr-assess` to validate NFR criteria (Security, Performance, Reliability, Maintainability).

---

## Approval

**Test Design Approved By:**

- [ ] Product Manager: {name} Date: {date}
- [ ] Tech Lead: {name} Date: {date}
- [ ] QA Lead: {name} Date: {date}

**Comments:**

---

---

## Appendix

### Knowledge Base References

- `risk-governance.md` - Risk classification framework
- `probability-impact.md` - Risk scoring methodology
- `test-levels-framework.md` - Test level selection
- `test-priorities-matrix.md` - P0-P3 prioritization

### Related Documents

- PRD: `_bmad-output/planning-artifacts/prd.md`
- Epics: `_bmad-output/planning-artifacts/epics.md`
- Architecture: `_bmad-output/planning-artifacts/architecture.md`
- Tech Spec: Architecture document (ADR-001 à ADR-004, ID-001 à ID-005)

---

**Generated by**: BMad TEA Agent - Test Architect Module
**Workflow**: `_bmad/bmm/testarch/test-design`
**Version**: 4.0 (BMad v6)
**Review Status**: ✅ Updated with TEA review recommendations
