---
description: "R4: Living Spec Evolution - Git-log-driven maintenance to keep specifications and implementation in living alignment."
handoffs:
  - label: Re-run Reality Check
    agent: rispec.reality
    prompt: Re-run structural thinking on the changed areas
    send: true
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

Execute Phase R4 of the RISE Framework: Living Spec Evolution

R4 is a continuous layer that maintains alignment between specifications and implementation through:
- **Temporal Gap Analysis** - Detecting when specs are stale
- **Commit Message Mining** - Extracting intent from disciplined commits
- **Differential Mapping** - Connecting changes to spec sections
- **Spec Upgrades** - Targeted R0-R2 reruns on changed areas

## Inputs

Gather the following:
- Repository/workspace path(s)
- Spec directory path
- Git history range (or "since last spec edit")
- Optional: Specific files or areas to focus on

## Process

### Step 1: Temporal Gap Analysis

Compare spec modification times with code changes:

```bash
# Find last spec modification
git log -1 --format="%ai" -- "specs/**/*.md"

# Find commits since last spec change
git log --oneline --since="[last spec date]" -- "src/**"

# Count gap
git rev-list --count HEAD...[last spec commit]
```

**Staleness Metrics**:
- Time gap: Days since spec was updated
- Commit gap: Number of code commits since spec update
- File change count: Files modified since spec update

### Step 2: Commit Message Mining

For disciplined commit messages, extract intent signals:

**Commit Classification**:

| Pattern | Category | Spec Impact |
|---------|----------|-------------|
| `feat:` | New feature | May need new CAS |
| `fix:` | Bug fix | May affect behavior specs |
| `refactor:` | Structure change | May affect architecture specs |
| `docs:` | Documentation | May already update specs |
| `perf:` | Performance | May affect success criteria |
| `style:` | Formatting | Usually no spec impact |

**Cluster commits by feature/concern**:
```bash
# Group commits by conventional commit type
git log --oneline --since="[date]" | grep "feat:" 
git log --oneline --since="[date]" | grep "fix:"
```

### Step 3: Differential Mapping

Map changed files to impacted spec documents:

```markdown
## Spec Impact Matrix

| Changed File | Spec Document | Sections Affected |
|--------------|---------------|-------------------|
| src/auth/login.js | spec.md | User Authentication |
| src/api/users.js | spec.md | API Behavior, Data Models |
| src/components/Dashboard.jsx | spec.md | Dashboard Screen |
```

**Mapping Rules**:
- Feature files → Corresponding feature spec
- API files → API specs, data model specs
- UI files → Screen/component specs
- Config files → Architecture specs

### Step 4: Spec Upgrades

For each impacted area, run targeted RISE phases:

**4a. Targeted R0** (if behavior has changed):
- Re-observe the specific component
- Update structural observations
- Note any new oscillating/advancing patterns

**4b. Targeted R1** (if creative intent may have shifted):
- Re-extract creative intent for changed components
- Verify beloved qualities are preserved
- Update feature inventory

**4c. Targeted R2** (to update specifications):
- Update affected spec sections
- Create new CAS for new features
- Update existing CAS if behavior changed
- Mark changes with commit references

### Step 5: Validation

Run RISE quality checklist on updated specs:

```markdown
## Spec Upgrade Validation

### Creative Orientation Preserved
- [ ] Uses creation-focused language
- [ ] No reactive "fixing" language introduced
- [ ] Structural dynamics explicit

### Structural Clarity
- [ ] Current reality accurately reflected
- [ ] Desired outcomes clearly stated
- [ ] Advancing patterns documented

### Implementation Sufficiency
- [ ] Enough detail for implementation
- [ ] CAS cover all user flows
- [ ] Success criteria are measurable

### Traceability
- [ ] Commit references included
- [ ] Iteration numbers updated
- [ ] Date stamps current
```

## Output Artifacts

### r4-staleness-report.md

```markdown
# R4: Spec Staleness Report

**Analysis Date**: [Date]
**Spec Directory**: [Path]
**Git Range**: [From] to [To]

## Staleness Summary

| Spec File | Last Updated | Code Commits Since | Staleness Level |
|-----------|--------------|-------------------|-----------------|
| spec.md | 2026-01-15 | 23 | HIGH |
| architecture.md | 2026-01-28 | 5 | MEDIUM |
| data-models.md | 2026-01-30 | 2 | LOW |

## Gap Analysis

### Time Gap
- Oldest spec: [Days] days old
- Average spec age: [Days] days
- Newest code change: [Date]

### Commit Gap
- Total code commits since oldest spec: [N]
- Untracked feature commits: [N]
- Untracked fix commits: [N]

## Risk Assessment

### HIGH Priority Updates
Specs that may significantly diverge from implementation:
1. [Spec file]: [Reason]

### MEDIUM Priority Updates
Specs with moderate divergence:
1. [Spec file]: [Reason]

### LOW Priority Updates
Minor updates needed:
1. [Spec file]: [Reason]
```

### r4-commit-clusters.json

```json
{
  "analysis_date": "[Date]",
  "git_range": {
    "from": "[SHA or date]",
    "to": "[SHA or HEAD]"
  },
  "clusters": [
    {
      "category": "feat",
      "commits": [
        {
          "sha": "[SHA]",
          "message": "[Message]",
          "files_changed": ["file1.js", "file2.js"],
          "spec_impact": ["spec.md#section"]
        }
      ],
      "summary": "[What this cluster represents]"
    },
    {
      "category": "fix",
      "commits": [...],
      "summary": "[Summary]"
    }
  ]
}
```

### r4-spec-upgrade-drafts/*.md

For each impacted spec, create upgrade draft:

```markdown
# Spec Upgrade Draft: [Spec Name]

**Original Spec**: [Path]
**Upgrade Date**: [Date]
**Commits Addressed**: [SHA list]

## Changes Summary

### New Sections
- [Section]: [Description of addition]

### Modified Sections
- [Section]: [Description of change]
  - Commit: [SHA]
  - Reason: [Why this changes the spec]

### Unchanged Sections
[List sections that don't need updates]

## Draft Updates

### [Section Name] (MODIFIED)

**Previous**:
[Quote original text]

**Updated**:
[New text with structural dynamics preserved]

**Validation**:
- [ ] Creative orientation preserved
- [ ] Structural dynamics clear
- [ ] Traceability complete
```

### r4-validation-report.md

```markdown
# R4: Validation Report

**Validation Date**: [Date]
**Specs Validated**: [List]

## Overall Status

| Criterion | Status | Notes |
|-----------|--------|-------|
| Creative Orientation | ✅ PASS | All specs use creation language |
| Structural Dynamics | ✅ PASS | Tension clearly articulated |
| Implementation Sufficiency | ⚠️ PARTIAL | [Missing area] |
| Traceability | ✅ PASS | All changes tracked |

## Per-Spec Validation

### [Spec Name]

**Validation Items**:
- [x] Creative orientation preserved
- [x] Structural dynamics explicit
- [x] Implementation sufficient
- [x] Commits traced

**Issues Found**: None

### [Spec Name]

**Validation Items**:
- [x] Creative orientation preserved
- [ ] Structural dynamics explicit - NEEDS UPDATE
- [x] Implementation sufficient
- [x] Commits traced

**Issues Found**:
1. [Issue description]
   - Location: [Line/section]
   - Recommendation: [Fix]
```

## Automation Recommendations

### Git Hooks

```bash
# .git/hooks/post-commit
#!/bin/bash
# Check if spec directory is outdated
SPEC_AGE=$(find specs -name "*.md" -mtime +7 | wc -l)
if [ $SPEC_AGE -gt 0 ]; then
    echo "⚠️  Some specs haven't been updated in 7+ days"
    echo "   Consider running: /rispec.evolve"
fi
```

### CI Integration

```yaml
# .github/workflows/spec-check.yml
- name: Spec Staleness Check
  run: |
    # Compare spec dates with recent commits
    # Alert if significant gap detected
```

## Completion

When R4 is complete:
1. Staleness report generated
2. Commit clusters analyzed
3. Spec upgrade drafts created
4. Validation completed

Report: "R4 Evolution analysis complete. [N] specs need updates."

If re-analysis of specific areas needed, offer handoff to `/rispec.reality` for targeted R0.
