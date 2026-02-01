---
description: "R1: Creative Archaeology - Extract creative intent and beloved qualities from the structural observation, focusing on what enables users to create."
handoffs:
  - label: Proceed to Specify
    agent: rispec.specify
    prompt: Transform the creative archaeology findings into formal specifications with Creative Advancement Scenarios
    send: true
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

Execute Phase R1 of the RISE Framework: Creative Archaeology

Transform the neutral structural diagnosis from R0 into creative understanding by:
- Extracting **creative intent** latent in the existing system
- Identifying **beloved qualities** users/creators cherish
- Cataloging features by their creative role
- Mapping advancing patterns worth preserving

## Prerequisites

R1 assumes a completed R0 (Structural Thinking) phase. Check for:
- `r0-structural-observation.md`
- `r0-question-log.md`  
- `r0-diagnosis-summary.md`

If R0 artifacts don't exist, recommend running `/rispec.reality` first.

## R1 Question Framework

For each component identified in R0, ask:

### 1. Creative Intent
- **What does this enable the user/organization/agent to CREATE or ACHIEVE?**
- Focus on desired outcomes, not problems solved
- What manifestation does this support?

### 2. Structural Role
- **How does this shape the structural tension between current reality and desired outcome?**
- Does it clarify vision? Resolve tension? Enable manifestation?

### 3. Advancing Pattern Contribution
- **How does this component participate in an advancing structure?**
- If oscillating, what structure produces the oscillation?
- Can the oscillating structure be redesigned to advance?

## Feature Inventory (Creation-Focused)

Classify all features into three categories:

### Vision-Supporting Features
Features that help users **clarify desired outcomes**:
- Help users see what they want to create
- Enable articulation of the "top pole" of structural tension
- Support vision formation and refinement

### Tension-Resolving Features  
Features that **facilitate natural progression** toward goals:
- Transform current reality states toward desired states
- Enable movement through structural dynamics
- Support the resolution path (not forced effort)

### Manifestation Features
Features that **directly support creation** of desired results:
- Enable the actual creation of the artifact/experience/outcome
- Bring the vision into concrete existence
- Complete the creative process

## Beloved Qualities Analysis

### What Are Beloved Qualities?

Qualities users or creators cherish, even if technically messy:
- "It feels alive"
- "It lets me improvise"
- "It never blocks me"
- "It just works the way I think"
- "I can trust it"

### Why They Matter

Beloved qualities are **structural constraints** on future redesign:
- They are NOT incidental niceties to discard
- They represent core value that must be preserved
- Losing them destroys the system's creative essence

### How to Identify Them

1. Look for features users defend emotionally
2. Find patterns users have adapted their workflow around
3. Identify capabilities users mention unprompted
4. Note what would make users refuse a "better" replacement

## Process

1. **Load R0 Artifacts**
   - Read the structural observation, question log, and diagnosis summary
   - Use these as ground truth for R1 analysis

2. **Component-Level Analysis**
   For each significant component:
   
   a. Ask the three R1 questions:
      - Creative Intent
      - Structural Role
      - Advancing Pattern Contribution
   
   b. Classify by feature type:
      - Vision-Supporting
      - Tension-Resolving
      - Manifestation

3. **Beloved Qualities Extraction**
   - Review user feedback, comments, documentation
   - Look for emotional language about features
   - Identify "must preserve" elements

4. **Pattern Mapping**
   - Map which components create advancing patterns
   - Identify oscillating structures and their causes
   - Note structural relationships between components

## Output Artifacts

Create the following in the spec directory:

### r1-creative-archaeology.md

```markdown
# R1: Creative Archaeology

**Target**: [System/codebase/workflow being analyzed]
**Date**: [Current date]
**Based on**: R0 Structural Diagnosis from [date]

## Creative Intent Summary

### Primary Creative Outcome
What does this system primarily enable users to CREATE?
[Description of the main creative purpose]

### Secondary Creative Outcomes
What else can users create through this system?
[List of additional creative outcomes supported]

## Component Analysis

### [Component 1 Name]

**Creative Intent**: What this enables users to create
[Description]

**Structural Role**: How it shapes structural tension
[Vision-Supporting / Tension-Resolving / Manifestation]

**Advancing Pattern Contribution**: 
[How it supports advancement toward desired outcomes]

### [Component 2 Name]
[Repeat structure]

## Structural Tension Mapping

### Current Reality → Desired Outcome Flows

For each major user journey:

**Journey: [Name]**
- Current Reality: [Starting state]
- Desired Outcome: [What user wants to create]
- Structural Dynamics: [How the system enables natural progression]
- Key Components Involved: [List]
```

### r1-feature-inventory.json

```json
{
  "target": "[System name]",
  "analysis_date": "[Date]",
  "features": {
    "vision_supporting": [
      {
        "name": "[Feature name]",
        "description": "[What it does]",
        "creative_contribution": "[How it helps clarify desired outcomes]"
      }
    ],
    "tension_resolving": [
      {
        "name": "[Feature name]",
        "description": "[What it does]",
        "creative_contribution": "[How it enables progression toward outcomes]"
      }
    ],
    "manifestation": [
      {
        "name": "[Feature name]",
        "description": "[What it does]",
        "creative_contribution": "[How it supports actual creation]"
      }
    ]
  }
}
```

### r1-beloved-qualities.md

```markdown
# R1: Beloved Qualities

## Identified Beloved Qualities

### 1. [Quality Name]
**Description**: What makes this quality beloved
**Evidence**: How we know users cherish this
**Structural Source**: What produces this quality
**Preservation Priority**: [Critical / High / Medium]

### 2. [Quality Name]
[Repeat structure]

## Preservation Constraints

Based on beloved qualities analysis, any redesign MUST:

1. [Constraint derived from beloved quality 1]
2. [Constraint derived from beloved quality 2]

## Warning Signs

If redesign causes any of these, beloved qualities are at risk:
- [Warning sign 1]
- [Warning sign 2]
```

### r1-advancing-vs-oscillating-map.md

```markdown
# R1: Advancing vs Oscillating Patterns

## Advancing Patterns (PRESERVE)

### [Pattern Name]
**Components Involved**: [List]
**How It Advances**: [Description of natural progression]
**Desired Outcome Supported**: [What it moves toward]

## Oscillating Patterns (REDESIGN)

### [Pattern Name]
**Components Involved**: [List]
**Oscillation Cycle**: [Description of back-and-forth]
**Root Cause**: [Structural source of oscillation]
**Redesign Opportunity**: [How to convert to advancing]

## Structural Recommendations

Based on pattern analysis:

1. **Preserve**: [List components/patterns to keep]
2. **Enhance**: [List advancing patterns to strengthen]
3. **Redesign**: [List oscillating patterns to convert]
```

## Language Patterns

### USE These Patterns (Creative Orientation)
- "This enables users to create..."
- "The structure naturally advances users toward..."
- "Through this feature, users manifest..."
- "This supports the creative process of..."
- "Structural tension resolves through..."

### AVOID These Patterns (Reactive Orientation)
- "This eliminates the problem of..."
- "This fixes..."
- "Users must navigate..."
- "This bridges the gap between..."
- "This prevents users from..."

## Completion

When R1 is complete:
1. All four R1 artifacts are created
2. Creative intent is clearly articulated
3. Beloved qualities are identified and prioritized
4. Features are classified by creative role
5. Advancing patterns are mapped for preservation

Report: "R1 Creative Archaeology complete. Ready for R2 (Specify/Intent Refinement)."

Offer handoff to `/rispec.specify` to continue the RISE process.
