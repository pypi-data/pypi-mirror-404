# Data Schemas

**Status**: ⏳ PROPOSED

**Structural Tension**
- Desired Outcome: {What data structures enable users to create}
- Current Reality: {Current data structure state}
- Natural Progression: {How schemas evolve to support creation}

> Governed by: `rispecs/Creative_Orientation_Operating_Guide.md`

---

## Overview

This document defines the data schemas for `{PROJECT_NAME}`. Schemas are designed to support the structural dynamics that enable natural progression toward desired outcomes.

---

## Core Schemas

### {Schema Name}

**Purpose**: {What this schema enables users to create}

```yaml
# Schema definition
{schema_name}:
  type: object
  properties:
    id:
      type: string
      description: Unique identifier
    # Add properties here
  required:
    - id
```

**Usage**:
- {Where this schema is used}
- {What it enables}

---

### {Schema Name 2}

**Purpose**: {What this schema enables}

```yaml
# Schema definition
```

---

## Schema Relationships

```
{Schema A} --creates--> {Schema B}
{Schema B} --enables--> {Schema C}
```

---

## Validation Rules

| Schema | Rule | Description |
|--------|------|-------------|
| `{schema}` | `{rule}` | {What it ensures} |

---

## Migration Patterns

When schemas evolve, follow these advancing patterns:

1. **Create new version** alongside existing schema
2. **Enable gradual migration** with compatibility layer
3. **Stabilize** on new schema when migration complete

---

## Related Specifications

- `rispecs/Configuration.md` - Configuration that uses these schemas
- `rispecs/ApplicationLogic.md` - Workflows that process this data
- `rispecs/RISE_Spec.md` - Core specification these schemas support
