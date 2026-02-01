---
description: "R0: Structural Thinking & Diagnosis - Observe current reality without hypothesis to understand the underlying structure that determines behavior."
handoffs:
  - label: Proceed to Inspect
    agent: rispec.inspect
    prompt: Now analyze the structural observations to extract creative intent and beloved qualities
    send: true
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

Execute Phase R0 of the RISE Framework: Create a structurally accurate, preconception-free picture of current reality before making any creative moves.

This phase implements Robert Fritz's Structural Thinking discipline:
- **Structure Determines Behavior**: The underlying structure of any system produces its observable patterns
- This is DIAGNOSTIC work, not creative work
- The goal is to see what IS, not to improve it yet

## The Three Steps of Structural Thinking

### Step 1: Start with Nothing

**CRITICAL**: Begin WITHOUT a knowledge base, preconception, or hypothesis.

- DO NOT compare the subject to anything else
- DO NOT say "This is similar to..." or reference past patterns
- Suspend all associations with other systems, theories, or models
- Observe reality *exactly* as it is presented

**Anti-patterns to avoid**:
- "This looks like a typical..." 
- "My experience suggests..."
- "Usually systems like this..."
- "Best practice would be..."

### Step 2: Picture What Is Said

Translate verbal/written information into a dimensional, visual picture:

1. **Create a mental "movie"** of what is being described
2. **Hold multiple ideas simultaneously** and see their relationships
3. **Build placeholder images** for general terms
4. **Mark blanks explicitly** - incomplete picture is critical data

**For each element observed, note**:
- Entities, flows, interactions, states
- Temporal sequences
- Dependencies and constraints
- Regions that are vague or unknown (mark as "[BLANK: description]")

**DO NOT**:
- Fill in blanks with assumptions
- Make guesses about unclear areas
- Infer intent beyond what is stated

### Step 3: Ask Questions (Four Types ONLY)

Questions MUST be internally motivated by the picture itself. Do NOT import external questions.

**Allowed Question Types**:

1. **Information Question** - Expands the picture
   - When: A part of the picture is vague or general
   - Example: "What kind of quality problem?" when told "We have a quality problem"

2. **Clarification Question** - Asks for a definition
   - When: A word or phrase isn't understood in context
   - Example: "What do you mean by 'synergy' in your context?"

3. **Implication Question** - Makes the implicit explicit
   - When: A statement implies something not directly stated
   - Example: "If you had gotten to market sooner, would performance have been better?"

4. **Discrepancy Question** - Addresses a contradiction
   - When: Two statements appear to contradict each other
   - Example: "How can this have been a great year if sales were down?"

**NO other question types are permitted in R0.**

## Process

1. **Identify the target** from user input:
   - Codebase, workflow, product, protocol, storyworld, or other
   - Get specific references (paths, URLs, descriptions)

2. **Apply the Three Steps**:
   
   a. Start with Nothing - clear preconceptions
   
   b. Picture What Is Said:
      - If codebase: Walk the structure, read key files, trace flows
      - If workflow: Map the steps, actors, decisions, artifacts
      - If product: Map features, user journeys, capabilities
      - Note all blanks and unknown regions
   
   c. Ask Questions:
      - Only use the four valid question types
      - Present questions to user and wait for responses
      - Update the picture with responses
      - Continue until no more internally-motivated questions arise

3. **Identify Behavioral Patterns**:
   
   **Oscillating Patterns** (structures that move back-and-forth):
   - Cycles that advance then reverse
   - Patterns that repeat without net progress
   - Examples: Centralize/decentralize cycles, build/cut capacity
   
   **Advancing Patterns** (structures that move toward outcomes):
   - Clear movement from current state toward desired state
   - Natural progression through structural dynamics
   - Build upon each other systematically

## Output Artifacts

Create the following in the appropriate spec directory:

### r0-structural-observation.md

```markdown
# R0: Structural Observation

**Target**: [Description of what was observed]
**Date**: [Current date]
**Observer**: [AI Agent / Human]

## The Picture

### Entities
[List key entities/components observed]

### Flows
[Describe data/process flows observed]

### Relationships
[Map dependencies and interactions]

### Temporal Sequences
[Note time-based patterns]

### Blanks (Unknown Regions)
[Explicitly mark what is NOT known]
- [BLANK: description of unknown area]
- [BLANK: description of unknown area]

## Behavioral Patterns Observed

### Oscillating Patterns
[List any back-and-forth patterns identified]
- Pattern: [Description]
  - Evidence: [What was observed]
  - Cycle: [How it repeats]

### Advancing Patterns
[List patterns that show clear progression]
- Pattern: [Description]
  - Evidence: [What was observed]
  - Direction: [Where it's moving toward]

## Structural Dynamics
[What underlying structure is producing the observed behaviors?]
```

### r0-question-log.md

```markdown
# R0: Question Log

## Questions Asked

| # | Type | Question | Region of Picture | Response | Picture Update |
|---|------|----------|-------------------|----------|----------------|
| 1 | [Info/Clarify/Implication/Discrepancy] | [Question text] | [What part of picture motivated this] | [Response received] | [How picture changed] |
```

### r0-diagnosis-summary.md

```markdown
# R0: Structural Diagnosis Summary

**One-Page Summary**: What structure is producing the observable behavior?

## Core Structural Finding
[In structural language, describe what underlying structure creates the patterns observed]

## Key Structural Elements
1. [Element and its structural role]
2. [Element and its structural role]

## Dominant Pattern
[Is this system primarily Oscillating or Advancing?]
- Type: [Oscillating / Advancing / Mixed]
- Evidence: [Key observations supporting this diagnosis]

## Structural Implications
[What does this structure naturally produce? No prescriptions - just structural analysis]

---
**Note**: This diagnosis does NOT prescribe solutions. It describes what IS, providing the foundation for Phase R1 (Creative Archaeology).
```

## Completion

When R0 is complete:
1. All three artifacts are created
2. The picture is as complete as current information allows
3. No more internally-motivated questions arise
4. Oscillating vs Advancing patterns are identified

Report: "R0 Structural Thinking complete. Ready for R1 (Inspect/Creative Archaeology)."

Offer handoff to `/rispec.inspect` to continue the RISE process.
