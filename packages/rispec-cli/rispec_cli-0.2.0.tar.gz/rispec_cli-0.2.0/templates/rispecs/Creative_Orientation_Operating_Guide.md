# Creative Orientation Operating Guide

**Status**: ⏳ PROPOSED

**Purpose**: Operationalize Creative Orientation within {PROJECT_NAME} by defining short, enforceable rules and templates that align with the RISE framework without reframing observations as problems.

---

## Operating Rules

- Structural Tension block appears at the top of major docs and agent outputs.
- Observations are recorded neutrally (including Risks & Issues) without categorization.
- Structural Assessment states whether a structure tends to advance or oscillate.
- Advancing Moves (optional) propose the next natural step that advances tension toward the desired outcome.
- Use create-language (create, manifest, build, enable, stabilize); avoid problem-elimination phrasing (fix, mitigate, eliminate, solve).
- When helpful, tag phase: germination, assimilation, completion.

### Structural Tension Block

Every governed document must include this block at the top:

```markdown
**Structural Tension**
- Desired Outcome: <one sentence describing what we want to create>
- Current Reality: <one sentence describing current state>
- Natural Progression: <one sentence describing how structure advances toward outcome>
```

### Section Structure

For observations and assessments, use this structure:

1) **Observations** (neutral facts)
2) **Structural Assessment** (advance or oscillate)
3) **Advancing Moves** (optional - next natural steps)

### Acceptance Checklist (Definition of Done)

Before considering a spec complete, verify:

- [ ] Structural Tension block present
- [ ] Observations stated neutrally
- [ ] Structural Assessment uses "advancing/oscillating" language
- [ ] Language patterns adhere to create-language rules
- [ ] If Advancing Moves are provided, they describe natural progression, not elimination

### Doc-Lint Policy

When reviewing documents:

- Allow neutral Observations; flag problem-elimination verbs outside of technical contexts
- Require "advancing/oscillating" only in Structural Assessment sections
- Require Structural Tension block in all governed docs

---

## Language Patterns

### USE These Patterns (Create-Language)

| Verb | Example |
|------|---------|
| create | "Create a stable foundation for..." |
| manifest | "Manifest the user's creative vision..." |
| build | "Build upon the existing structure..." |
| enable | "Enable natural progression toward..." |
| stabilize | "Stabilize the configuration for..." |
| establish | "Establish the structural dynamics..." |
| advance | "Advance toward the desired outcome..." |

### AVOID These Patterns (Problem-Elimination)

| Avoid | Replace With |
|-------|--------------|
| fix | stabilize, establish |
| mitigate | enable resilience for |
| eliminate | create absence of |
| solve | resolve tension through |
| prevent | create conditions that ensure |
| reduce | create efficiency in |
| remove | create space for |

### Examples

**Reactive (AVOID):**
- "Fix chapter over-generation in tests."
- "Eliminate outline inconsistency."
- "Solve the authentication problem."

**Creative (USE):**
- "Create a 3-chapter test preset that stabilizes chapter count during test runs."
- "Enable outline-stage RAG injection to stabilize foundational consistency."
- "Establish secure authentication flow that enables user creation."

---

## Agent Application Matrix

When working with multiple AI agents, each should apply Creative Orientation:

| Agent Role | Application |
|------------|-------------|
| vision-agent | Produces the Structural Tension block first |
| architect-agent | Outlines reflect advancing patterns; Observations kept separate |
| writer-agent | Prompts and staging described in create-language |
| critic-agent | Findings recorded as Observations; assessment states advance/oscillate; suggestions become Advancing Moves |
| revisor-agent | Enforces Acceptance Checklist before completion |
| rag-agent | Retrieval intent framed as context that advances the Desired Outcome |
| editor/meta agents | Preserve advancing pattern language in polish and metadata |

---

## Status Tags

Use these standardized status tags in all rispecs:

| Tag | Meaning |
|-----|---------|
| `⏳ PROPOSED` | Initial specification, not yet reviewed |
| `🔄 Under Revision` | Being actively updated |
| `✅ IMPLEMENTED` | Specification matches current implementation |
| `✅ COMPLETE` | Feature fully implemented and tested |
| `⚠️ DEPRECATED` | No longer in use, kept for reference |

---

## Governed Documents

This guide governs specifications in `rispecs/` and agent outputs. It complements:

- `src/llms/llms-rise-framework.txt` - Core RISE methodology
- `src/llms/llms-creative-orientation.txt` - Creative Orientation principles
- `src/llms/llms-structural-thinking.gemini.txt` - Structural Thinking discipline
- `rispecs/RISE_Spec.md` - Core application specification

---

## Validation Checklist

Use this checklist when reviewing any rispec document:

### Structural Completeness
- [ ] Has Structural Tension block at top
- [ ] Status tag is present and accurate
- [ ] Related specifications are linked

### Creative Orientation Compliance
- [ ] No problem-elimination verbs (fix, mitigate, eliminate, solve)
- [ ] Uses create-language throughout
- [ ] Observations are neutral, not problem-framed
- [ ] Structural Assessment uses advancing/oscillating terminology

### Cross-Reference Integrity
- [ ] All referenced files exist
- [ ] Code paths are accurate (e.g., `src/module.py`)
- [ ] Configuration parameters are synchronized

### Implementation Alignment
- [ ] Spec accurately reflects current code
- [ ] Status tag matches implementation state
- [ ] No stale information
