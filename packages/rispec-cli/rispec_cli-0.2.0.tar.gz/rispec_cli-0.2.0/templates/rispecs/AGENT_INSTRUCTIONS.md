# Agent Instructions

**Status**: ⏳ PROPOSED

**Structural Tension**
- Desired Outcome: AI agents that advance creation aligned with RISE framework
- Current Reality: Agents available but need project-specific guidance
- Natural Progression: Agents internalize structural dynamics and create advancing outputs

> Governed by: `rispecs/Creative_Orientation_Operating_Guide.md`

---

## Purpose

This document provides instructions for AI agents (Claude, Copilot, Gemini, Cursor, etc.) working on `{PROJECT_NAME}`. These instructions ensure agents operate within Creative Orientation principles and produce outputs that advance rather than oscillate.

---

## Core Principles for Agents

### 1. Start with Structural Tension

Before making changes or suggestions, establish:

```markdown
**Structural Tension**
- Desired Outcome: [What we're trying to create]
- Current Reality: [Current state]
- Natural Progression: [How structure advances toward outcome]
```

### 2. Use Create-Language

| Instead of | Use |
|------------|-----|
| "Fix the bug" | "Stabilize the behavior" |
| "Solve the problem" | "Create the solution" |
| "Eliminate the error" | "Establish correct flow" |
| "Prevent issues" | "Enable resilience" |

### 3. Observe Neutrally

When analyzing code or situations:
- State facts without judgment
- Separate observations from assessments
- Avoid problem-elimination framing

### 4. Assess Structure

After observations, assess whether current structure:
- **Advances** - naturally progresses toward desired outcome
- **Oscillates** - cycles back and forth without net progress

---

## Agent Workflow

When given a task, follow this workflow:

1. **Establish Tension**: What are we trying to create? What exists now?
2. **Observe**: What are the neutral facts about current state?
3. **Assess Structure**: Advancing or oscillating?
4. **Propose Advancing Move**: What naturally progresses toward the outcome?
5. **Create**: Implement the advancing move

---

## Specification Awareness

### Always Reference

Before making changes, check these specifications:

| Specification | Contains |
|---------------|----------|
| `rispecs/RISE_Spec.md` | Core creative intent and scenarios |
| `rispecs/Creative_Orientation_Operating_Guide.md` | Language patterns and rules |
| `rispecs/Configuration.md` | Configuration options |
| `rispecs/DataSchemas.md` | Data structures |
| `rispecs/ApplicationLogic.md` | Workflow patterns |

### Status Tag Awareness

Respect status tags when modifying specifications:

- `✅ IMPLEMENTED` - Changes require code updates too
- `⏳ PROPOSED` - Can be refined without code impact
- `🔄 Under Revision` - Coordinate with ongoing work

---

## Output Requirements

### Code Changes

1. Include Structural Tension in PR descriptions
2. Reference relevant rispecs
3. Use create-language in comments and documentation
4. Verify changes advance rather than oscillate

### Specification Updates

1. Include Structural Tension block at top
2. Use correct status tag
3. Follow language patterns from Operating Guide
4. Link to related specifications

### Analysis and Reports

1. Separate Observations from Assessments
2. Use advancing/oscillating terminology
3. Propose Advancing Moves when appropriate
4. Avoid problem-elimination framing

---

## LLMS Guidance Files

For deeper context on the methodology, reference:

- `src/llms/llms-rise-framework.txt` - Complete RISE methodology
- `src/llms/llms-creative-orientation.txt` - Creative Orientation principles
- `src/llms/llms-structural-thinking.gemini.txt` - Structural Thinking discipline
- `src/llms/llms-structural-tension-charts.txt` - Tension dynamics

---

## Anti-Patterns to Avoid

### Don't Do This

```markdown
## Problem
The authentication is broken and needs fixing.

## Solution
Fix the authentication bug.
```

### Do This Instead

```markdown
**Structural Tension**
- Desired Outcome: Users create authenticated sessions seamlessly
- Current Reality: Authentication flow does not complete successfully
- Natural Progression: Establish session token generation that enables user creation

## Observations
- Token generation returns null on line 47
- Session store is not initialized before token creation

## Structural Assessment
The current structure oscillates because session creation is attempted before store initialization.

## Advancing Move
Establish initialization order that enables session creation before authentication flow.
```

---

## Command Reference

Use these rispec commands when working on this project:

| Command | Purpose |
|---------|---------|
| `/rispec.reality` | Establish structural tension (R0) |
| `/rispec.inspect` | Analyze existing system (R1) |
| `/rispec.specify` | Refine specifications (R2) |
| `/rispec.export` | Generate audience-specific views (R3) |
| `/rispec.evolve` | Update specs from code changes (R4) |

---

## Validation Before Completion

Before completing any task, verify:

- [ ] Structural Tension block present where required
- [ ] Create-language used throughout
- [ ] No problem-elimination phrasing
- [ ] Related specifications referenced
- [ ] Status tags accurate
- [ ] Output advances rather than oscillates
