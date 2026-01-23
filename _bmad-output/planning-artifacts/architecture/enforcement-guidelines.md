# Enforcement Guidelines

### All AI Agents MUST

1. **Read Cursor rules FIRST** : `.cursor/rules/*.mdc` avant toute implémentation
2. **Follow naming conventions** : Backend snake_case, Frontend camelCase, Components PascalCase
3. **Use established patterns** : ServiceContainer, Zustand immutable, Pydantic validation
4. **Write tests** : Unit + Integration, >80% coverage code critique
5. **Log properly** : Structured JSON logs, appropriate levels
6. **Handle errors** : Hierarchical exceptions + HTTPException
7. **Validate V1.0 patterns** : SSE format, Preset UUIDs, Cost middleware, Auto-save suspension

### Pattern Enforcement

**Pre-commit Checks:**
- ESLint (frontend) : Enforces TypeScript conventions
- Ruff (backend) : Enforces Python PEP8
- Pytest : >80% coverage gate
- Type checking : `mypy` (Python), `tsc --noEmit` (TypeScript)

**Code Review Checklist:**
- [ ] Naming conventions respected?
- [ ] Tests written and passing?
- [ ] Error handling proper (no silent failures)?
- [ ] V1.0 patterns followed (SSE, Presets, Cost, Auto-save)?
- [ ] Cursor rules consulted?

**Pattern Violation Process:**
1. Detect violation (linter, review, test failure)
2. Document in issue (reference this architecture doc)
3. Fix immediately (blocking for critical patterns)
4. Update pattern doc if ambiguous

---
