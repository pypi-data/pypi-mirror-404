# Skill Restructure Plan

## Current Skills (Monolithic)

```
sim-creator (orchestrator)
sim-research
sim-validator
sim-config-writer
sim-sandbox-operator  ← Does too much (start, services, worker, flow, snapshot)
sim-flow-writer
sim-reviewer
sim-debugger
```

## Proposed Skills (One Per Pipeline Step)

Each skill does ONE thing and runs ONE verification command at the end.

### Phase 1: Configuration

| Skill | Action | Verify Command |
|-------|--------|----------------|
| `sim-research` | Research GitHub repo | `plato sandbox verify research` |
| `sim-validate` | Check app can be simulated | `plato sandbox verify validation` |
| `sim-config` | Write plato-config.yml, docker-compose.yml | `plato sandbox verify config` |

### Phase 2: Sandbox Setup

| Skill | Action | Verify Command |
|-------|--------|----------------|
| `sim-sandbox-start` | Start sandbox VM | `plato sandbox verify` |
| `sim-sandbox-services` | Start containers | `plato sandbox verify services` |
| `sim-sandbox-login` | Manual browser login | `plato sandbox verify login` |
| `sim-sandbox-worker` | Start worker | `plato sandbox verify worker` |

### Phase 3: Flow Testing

| Skill | Action | Verify Command |
|-------|--------|----------------|
| `sim-flow-clear` | Clear audit log | `plato sandbox verify audit-clear` |
| `sim-flow-run` | Run login flow | `plato sandbox verify flow` |
| `sim-flow-mutations` | Check mutations | `plato sandbox verify mutations` |
| `sim-flow-audit` | Verify audit tracks changes | `plato sandbox verify audit-active` |

### Phase 4: Snapshot & Submit

| Skill | Action | Verify Command |
|-------|--------|----------------|
| `sim-snapshot` | Create snapshot | `plato sandbox verify snapshot` |
| `sim-review` | Run review workflow | `plato pm verify review` |
| `sim-submit` | Submit for approval | `plato pm verify submit` |

### Support Skills

| Skill | Purpose |
|-------|---------|
| `sim-creator` | Orchestrator - calls skills in order, handles errors |
| `sim-debugger` | Error recovery - diagnoses failures, suggests fixes |

---

## Skill Template

Each skill follows this structure:

```markdown
---
name: sim-{name}
description: {One sentence description}
allowed-tools: Bash, Read, Edit, ... (minimal set needed)
context: fork
---

# {Skill Name}

**Pipeline Position:** Phase X, Step Y
**Previous Step:** sim-{previous}
**Next Step:** sim-{next}

## API Key

export PLATO_API_KEY="pk_user_..."

## Input Required

{What this skill needs from previous step}

## Action

{Exactly what to do - specific commands}

## Verification

Run: `plato {domain} verify {check}`

### On Success
{What to output, what to pass to next step}

### On Failure
{What to do, which skill handles the error}

## DO NOT
{Common mistakes to avoid}
```

---

## Implementation Order

### Step 1: Create Verification Commands

Add to CLI:
```
plato sandbox verify research
plato sandbox verify validation
plato sandbox verify config
plato sandbox verify
plato sandbox verify services
plato sandbox verify login
plato sandbox verify worker
plato sandbox verify audit-clear
plato sandbox verify flow
plato sandbox verify mutations
plato sandbox verify audit-active
plato sandbox verify snapshot
plato pm verify review
plato pm verify submit
```

### Step 2: Create New Skills

Create in order (each depends on previous):

1. `sim-research` (update existing)
2. `sim-validate` (rename from sim-validator)
3. `sim-config` (rename from sim-config-writer)
4. `sim-sandbox-start` (extract from sim-sandbox-operator)
5. `sim-sandbox-services` (extract from sim-sandbox-operator)
6. `sim-sandbox-login` (new)
7. `sim-sandbox-worker` (extract from sim-sandbox-operator)
8. `sim-flow-clear` (new)
9. `sim-flow-run` (extract from sim-sandbox-operator)
10. `sim-flow-mutations` (new)
11. `sim-flow-audit` (new)
12. `sim-snapshot` (extract from sim-sandbox-operator)
13. `sim-review` (update existing)
14. `sim-submit` (new)
15. `sim-creator` (update to use new skills)
16. `sim-debugger` (update for new structure)

### Step 3: Delete Old Skills

Remove:
- `sim-sandbox-operator` (split into multiple skills)
- `sim-config-writer` (renamed to sim-config)
- `sim-validator` (renamed to sim-validate)
- `sim-flow-writer` (merged into sim-flow-run or sim-sandbox-login)
- `sim-reviewer` (renamed to sim-review)

---

## File Structure

```
~/.claude/skills/
├── sim-creator/
│   └── SKILL.md
├── sim-research/
│   └── SKILL.md
├── sim-validate/
│   └── SKILL.md
├── sim-config/
│   └── SKILL.md
├── sim-sandbox-start/
│   └── SKILL.md
├── sim-sandbox-services/
│   └── SKILL.md
├── sim-sandbox-login/
│   └── SKILL.md
├── sim-sandbox-worker/
│   └── SKILL.md
├── sim-flow-clear/
│   └── SKILL.md
├── sim-flow-run/
│   └── SKILL.md
├── sim-flow-mutations/
│   └── SKILL.md
├── sim-flow-audit/
│   └── SKILL.md
├── sim-snapshot/
│   └── SKILL.md
├── sim-review/
│   └── SKILL.md
├── sim-submit/
│   └── SKILL.md
└── sim-debugger/
    └── SKILL.md
```

---

## Verification Command Locations in CLI

```
plato/v1/cli/
├── verify.py       ← All sandbox verify commands including research, validation, config
├── sandbox.py      ← Imports sandbox_verify_app from verify.py
└── pm.py           ← pm verify {review,submit}
```

---

## Questions to Resolve

1. **Should sim-flow-writer be separate or merged into sim-sandbox-login?**
   - Option A: sim-sandbox-login creates flows.yml based on what it finds
   - Option B: Separate sim-flow-write skill after login

2. **How granular should flow testing be?**
   - Option A: 4 separate skills (clear, run, mutations, audit)
   - Option B: 1 skill (sim-flow-test) that does all 4 with verification after each

3. **Should verification commands auto-fix or just report?**
   - Option A: Just report issues, agent decides how to fix
   - Option B: Offer `--fix` flag to auto-fix simple issues
