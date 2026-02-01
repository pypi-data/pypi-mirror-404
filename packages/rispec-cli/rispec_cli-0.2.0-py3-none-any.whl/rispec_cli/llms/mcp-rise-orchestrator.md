# RISE Orchestrator MCP Specification

## Overview

The `rise-orchestrator` MCP tool enables local AI agents to execute RISE v2 workflows on codebases, workflows, products, protocols, or conceptual systems.

This specification defines the methods, parameters, and outputs for the MCP integration.

## Tool Metadata

```yaml
name: rise-orchestrator
version: 0.1.0
description: >
  Orchestrates RISE v2 analysis of codebases, workflows, or conceptual systems.
  Runs structural diagnosis, creative archaeology, spec creation, export, and
  optional git-log-based evolution.
author: RISE Spec Kit
license: MIT
```

## Methods

### start_session

Initialize a new RISE analysis session.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "session_id": {
      "type": "string",
      "description": "Optional external session identifier. If omitted, tool generates one."
    },
    "target_type": {
      "type": "string",
      "enum": ["codebase", "workflow", "product", "protocol", "storyworld", "other"],
      "description": "Type of system being analyzed"
    },
    "target_reference": {
      "type": "string",
      "description": "For codebase: repo URL or local path. For workflow/product/etc.: free-form description or doc path."
    },
    "goals": {
      "type": "array",
      "items": { "type": "string" },
      "description": "High-level outcomes the requester wants from this RISE run."
    }
  },
  "required": ["target_type", "target_reference"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "session_id": {
      "type": "string",
      "description": "The session ID for this RISE analysis"
    },
    "artifact_index": {
      "type": "string",
      "description": "Path or identifier for the artifact registry for this session"
    },
    "status": {
      "type": "string",
      "enum": ["created", "error"]
    }
  }
}
```

### run_phase

Execute a specific RISE phase for a session.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "session_id": {
      "type": "string",
      "description": "Session ID from start_session"
    },
    "phase": {
      "type": "string",
      "enum": ["R0", "R1", "R2", "R3", "R4"],
      "description": "RISE phase to execute"
    },
    "scope": {
      "type": "object",
      "description": "Optional narrowing: files, components, modules, user journeys, or other subcontexts to limit analysis."
    },
    "options": {
      "type": "object",
      "description": "Phase-specific options",
      "properties": {
        "R0": {
          "max_question_rounds": { "type": "integer", "default": 3 }
        },
        "R1": {
          "include_beloved_qualities": { "type": "boolean", "default": true }
        },
        "R2": {
          "spec_formats": { "type": "array", "items": { "type": "string" } }
        },
        "R3": {
          "audiences": { 
            "type": "array", 
            "items": { 
              "type": "string",
              "enum": ["technical", "stakeholder", "ux", "agent"]
            }
          }
        },
        "R4": {
          "since_timestamp": { "type": "string", "format": "date-time" },
          "max_commits": { "type": "integer", "default": 100 }
        }
      }
    }
  },
  "required": ["session_id", "phase"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "enum": ["started", "completed", "failed"]
    },
    "artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "phase": { "type": "string" },
          "kind": { "type": "string" },
          "path": { "type": "string" },
          "summary": { "type": "string" }
        }
      }
    },
    "next_recommended_phase": {
      "type": "string",
      "description": "Suggested next phase based on current state"
    }
  }
}
```

### get_artifacts

List artifacts for a session, optionally filtered by phase or kind.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "session_id": { "type": "string" },
    "phase": { "type": "string", "nullable": true },
    "kind": { "type": "string", "nullable": true }
  },
  "required": ["session_id"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "phase": { "type": "string" },
          "kind": { "type": "string" },
          "path": { "type": "string" },
          "summary": { "type": "string" },
          "created_at": { "type": "string", "format": "date-time" },
          "status": { 
            "type": "string",
            "enum": ["draft", "reviewed", "accepted"]
          }
        }
      }
    }
  }
}
```

### get_artifact_content

Retrieve the full content of a specific artifact.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "session_id": { "type": "string" },
    "artifact_id": { "type": "string" }
  },
  "required": ["session_id", "artifact_id"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "artifact_id": { "type": "string" },
    "content": { "type": "string" },
    "metadata": {
      "type": "object",
      "properties": {
        "phase": { "type": "string" },
        "kind": { "type": "string" },
        "created_at": { "type": "string" },
        "producer_agent": { "type": "string" }
      }
    }
  }
}
```

### suggest_next_action

Given current artifacts and goals, propose the next structurally sensible RISE step.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "session_id": { "type": "string" },
    "current_focus": {
      "type": "string",
      "description": "Optional natural-language description of what the local agent is working on."
    }
  },
  "required": ["session_id"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "recommendation": {
      "type": "string",
      "description": "Natural language recommendation for next step"
    },
    "rationale": {
      "type": "string",
      "description": "Structural reasoning for the recommendation"
    },
    "suggested_call": {
      "type": "object",
      "description": "Example arguments for a follow-up run_phase call"
    },
    "alternatives": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "action": { "type": "string" },
          "reason": { "type": "string" }
        }
      }
    }
  }
}
```

## Phase Descriptions

### R0: Reality (Structural Thinking)

**Purpose**: Create preconception-free picture of current reality

**Steps**:
1. Start with Nothing - suspend hypotheses
2. Picture What Is Said - build mental model
3. Ask Questions - four valid types only

**Artifacts Produced**:
- `r0-structural-observation.md`
- `r0-question-log.md`
- `r0-diagnosis-summary.md`

### R1: Inspect (Creative Archaeology)

**Purpose**: Extract creative intent and beloved qualities

**Steps**:
1. Component-level creative intent analysis
2. Feature inventory by creative role
3. Beloved qualities identification
4. Advancing/oscillating pattern mapping

**Artifacts Produced**:
- `r1-creative-archeology.md`
- `r1-feature-inventory.json`
- `r1-beloved-qualities.md`
- `r1-advancing-vs-oscillating-map.md`

### R2: Specify (Intent Refinement)

**Purpose**: Transform insights into structured specifications

**Steps**:
1. Desired outcome definition
2. Structural tension analysis
3. Creative Advancement Scenarios
4. Spec document creation

**Artifacts Produced**:
- `spec.md` (main specification)
- `creative-advancement-scenarios.md`
- Related spec documents (architecture, data, UI, etc.)

### R3: Export (Multi-Audience Views)

**Purpose**: Generate audience-specific documentation

**Export Types**:
1. Technical Documentation
2. Stakeholder Communication
3. User Experience
4. Agent-Oriented

**Artifacts Produced**:
- `exports/technical/*.md`
- `exports/stakeholder/*.md`
- `exports/ux/*.md`
- `exports/agents/*.md`

### R4: Evolution (Living Specs)

**Purpose**: Maintain alignment between specs and implementation

**Steps**:
1. Temporal gap analysis
2. Commit message mining
3. Differential mapping
4. Targeted spec upgrades
5. Validation

**Artifacts Produced**:
- `r4-staleness-report.md`
- `r4-commit-clusters.json`
- `r4-spec-upgrade-drafts/*.md`
- `r4-validation-report.md`

## Multi-Agent Protocol

### Canonical Roles

| Role | Phase | Responsibility |
|------|-------|----------------|
| R0.StructuralThinker | R0 | Runs structural thinking discipline |
| R1.Archaeologist | R1 | Creative archaeology and beloved qualities |
| R2.Specifier | R2 | Authors specs and CAS |
| R3.Exporter | R3 | Produces audience views |
| R4.Maintainer | R4 | Monitors and updates specs |

### Coordination Pattern

All agents share:
- **RISE Session ID**: Unique identifier for the analysis
- **Target Descriptor**: What is being analyzed
- **Artifact Index**: Registry of all produced artifacts

### Handoff Protocol

```json
{
  "handoff": {
    "from_agent": "R0.StructuralThinker",
    "to_agent": "R1.Archaeologist",
    "artifacts_produced": ["r0-structural-observation.md"],
    "context": "Structural diagnosis complete, ready for creative archaeology",
    "timestamp": "2026-02-01T00:00:00Z"
  }
}
```

## Safety Rails

### Structural Thinking Enforcement

During R0, the tool enforces:
- No comparative language ("This is like...")
- No hypothesizing
- Only four valid question types
- No premature solutions

### Creative Orientation Enforcement

Across all phases:
- No reactive "fixing" language
- Focus on desired outcomes, not problems
- Advancing patterns, not oscillating
- Structural dynamics, not forced connections

## Example Usage

### Python Client

```python
import mcp

# Initialize client
client = mcp.Client("rise-orchestrator")

# Start session
session = client.call("start_session", {
    "target_type": "codebase",
    "target_reference": "/path/to/project",
    "goals": ["Understand user authentication flow", "Generate specs for modernization"]
})

# Run phases
r0_result = client.call("run_phase", {
    "session_id": session["session_id"],
    "phase": "R0"
})

r1_result = client.call("run_phase", {
    "session_id": session["session_id"],
    "phase": "R1",
    "options": {"R1": {"include_beloved_qualities": True}}
})

# Get suggestion for next step
suggestion = client.call("suggest_next_action", {
    "session_id": session["session_id"],
    "current_focus": "Ready to create specifications"
})
```

## Version History

- **0.1.0** (2026-02-01): Initial MCP specification for RISE v2
