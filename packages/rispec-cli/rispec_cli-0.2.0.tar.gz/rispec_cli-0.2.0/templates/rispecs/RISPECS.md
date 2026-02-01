# Rispecs Index

**Status**: ⏳ PROPOSED

**Structural Tension**
- Desired Outcome: Comprehensive specification suite that enables creation of {PROJECT_NAME}
- Current Reality: Initial specification structure established
- Natural Progression: Specifications evolve alongside implementation, maintaining sync

> Governed by: `Creative_Orientation_Operating_Guide.md`

---

## Specification Index

This directory contains RISE-based specifications for `{PROJECT_NAME}`.

### Core Specifications

| Document | Purpose | Status |
|----------|---------|--------|
| [RISE_Spec.md](RISE_Spec.md) | Core creative intent and scenarios | ⏳ PROPOSED |
| [Creative_Orientation_Operating_Guide.md](Creative_Orientation_Operating_Guide.md) | Operating rules and language patterns | ⏳ PROPOSED |

### Technical Specifications

| Document | Purpose | Status |
|----------|---------|--------|
| [Configuration.md](Configuration.md) | System configuration options | ⏳ PROPOSED |
| [DataSchemas.md](DataSchemas.md) | Data structures and schemas | ⏳ PROPOSED |
| [ApplicationLogic.md](ApplicationLogic.md) | Workflow and procedural logic | ⏳ PROPOSED |
| [ImplementationNotes.md](ImplementationNotes.md) | Technical implementation guidance | ⏳ PROPOSED |

### Agent Guidance

| Document | Purpose | Status |
|----------|---------|--------|
| [AGENT_INSTRUCTIONS.md](AGENT_INSTRUCTIONS.md) | AI agent operating instructions | ⏳ PROPOSED |

---

## Status Legend

| Status | Meaning |
|--------|---------|
| ⏳ PROPOSED | Initial specification, not yet reviewed |
| 🔄 Under Revision | Being actively updated |
| ✅ IMPLEMENTED | Specification matches current implementation |
| ✅ COMPLETE | Feature fully implemented and tested |
| ⚠️ DEPRECATED | No longer in use, kept for reference |

---

## Adding New Specifications

When adding new specifications to this directory:

1. Use the Structural Tension block at the top
2. Reference the Operating Guide for governance
3. Use correct status tag
4. Add entry to this index
5. Follow create-language patterns

---

## Cross-Reference Validation

Specifications should maintain accurate cross-references:

- Configuration.md ↔ DataSchemas.md
- ApplicationLogic.md ↔ DataSchemas.md
- ImplementationNotes.md ↔ All specifications
- AGENT_INSTRUCTIONS.md references all specifications

---

## RISE Framework Integration

These specifications follow the RISE Framework phases:

- **R0 (Reality)**: Structural Tension blocks establish reality
- **R1 (Inspect)**: RISE_Spec.md captures beloved qualities
- **R2 (Specify)**: Creative Advancement Scenarios in RISE_Spec.md
- **R3 (Export)**: Specifications serve as audience-specific views
- **R4 (Evolve)**: ImplementationNotes.md tracks evolution

---

## Related Files

- `src/llms/llms-rise-framework.txt` - Core RISE methodology
- `src/llms/llms-creative-orientation.txt` - Creative Orientation principles
- `AGENTS.md` - Repository-level agent instructions
