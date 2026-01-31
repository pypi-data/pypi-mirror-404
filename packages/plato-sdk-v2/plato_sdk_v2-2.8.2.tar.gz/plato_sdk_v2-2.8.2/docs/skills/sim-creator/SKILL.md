---
name: sim-creator
description: Creates Plato simulators from GitHub URLs. Use when user wants to create a simulator, build a sim, or provides a GitHub URL for simulation. This is the main entry point for Plato simulator creation.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Skill, mcp__playwright__browser_navigate, mcp__playwright__browser_snapshot, mcp__playwright__browser_type, mcp__playwright__browser_click, mcp__playwright__browser_take_screenshot
context: fork
---

# Plato Simulator Creator (Orchestrator)

You are the orchestrator for creating Plato simulators. You coordinate the pipeline by invoking skills in sequence and running verification commands.

## API Key

**CRITICAL: Export this BEFORE running any plato commands:**
```bash
export PLATO_API_KEY="pk_user_IgNNSJp5v_J0EMJtnxHGw6y68lfdYXiWdXNq1v_JaQQ"
```

---

## Pipeline Overview

```
Phase 1: Configuration
  sim-research → sim-validate → sim-config

Phase 2: Sandbox Setup
  sim-sandbox-start → sim-sandbox-services → sim-sandbox-login → sim-sandbox-worker

Phase 3: Flow Testing
  sim-flow-clear → sim-flow-run → sim-flow-mutations → sim-flow-audit
                                        ↑__________________|
                                        (loop if mutations found)

Phase 4: Snapshot & Submit
  sim-snapshot → sim-review → sim-submit
```

---

## Skills and Verification Commands

| Step | Skill | Verify Command | What It Checks |
|------|-------|----------------|----------------|
| 1 | sim-research | `plato sandbox verify research` | Required fields in research report |
| 2 | sim-validate | `plato sandbox verify validation` | DB type supported, image exists |
| 3 | sim-config | `plato sandbox verify config` | YAML valid, Plato images, network_mode |
| 4 | sim-sandbox-start | `plato sandbox verify` | .sandbox.yaml has all fields |
| 5 | sim-sandbox-services | `plato sandbox verify services` | Containers healthy, URL returns 200 |
| 6 | sim-sandbox-login | `plato sandbox verify login` | Manual check - logged in, no wizards |
| 7 | sim-sandbox-worker | `plato sandbox verify worker` | connected: true, audit_log_count exists |
| 8 | sim-flow-clear | `plato sandbox verify audit-clear` | 0 mutations |
| 9 | sim-flow-run | `plato sandbox verify flow` | Flow file exists with login section |
| 10 | sim-flow-mutations | `plato sandbox verify mutations` | 0 mutations after login |
| 11 | sim-flow-audit | `plato sandbox verify audit-active` | Manual check - changes ARE tracked |
| 12 | sim-snapshot | `plato sandbox verify snapshot` | artifact_id present |
| 13 | sim-review | `plato pm verify review` | API key, artifact_id, service present |
| 14 | sim-submit | `plato pm verify submit` | All prerequisites met |

---

## Orchestration Process

### For Each Step:

1. **Invoke the skill** (using the Skill tool)
2. **Run the verification command**
3. **If verification fails:**
   - Read the error output carefully
   - Fix inline (simple issues) or invoke sim-debugger (complex issues)
   - Re-run verification
4. **If verification passes:** Continue to next step

### Determine Starting Point:

**If user provides GitHub URL:**
- Start from sim-research

**If config files exist:**
```bash
plato sandbox verify config
```
- If passes, start from sim-sandbox-start

**If sandbox already running:**
```bash
plato sandbox verify
```
- Continue from appropriate step based on state

---

## Step-by-Step Execution

### Phase 1: Configuration

```
Step 1: Invoke skill sim-research
        → Run: plato sandbox verify research

Step 2: Invoke skill sim-validate
        → Run: plato sandbox verify validation

Step 3: Invoke skill sim-config
        → Run: plato sandbox verify config
```

### Phase 2: Sandbox Setup

```
Step 4: Invoke skill sim-sandbox-start
        → Run: plato sandbox verify

Step 5: Invoke skill sim-sandbox-services
        → Run: plato sandbox verify services

Step 6: Invoke skill sim-sandbox-login
        → Run: plato sandbox verify login

Step 7: Invoke skill sim-sandbox-worker
        → Run: plato sandbox verify worker
```

### Phase 3: Flow Testing

```
Step 8: Invoke skill sim-flow-clear
        → Run: plato sandbox verify audit-clear

Step 9: Invoke skill sim-flow-run
        → Run: plato sandbox verify flow

Step 10: Invoke skill sim-flow-mutations
         → Run: plato sandbox verify mutations
         → If FAIL: Fix audit_ignore_tables, loop to Step 8

Step 11: Invoke skill sim-flow-audit
         → Run: plato sandbox verify audit-active
```

### Phase 4: Snapshot & Submit

```
Step 12: Invoke skill sim-snapshot
         → Run: plato sandbox verify snapshot

Step 13: Invoke skill sim-review
         → Run: plato pm verify review

Step 14: Invoke skill sim-submit
         → Run: plato pm verify submit
```

---

## Error Recovery: Mutation Loop

**Most common failure:** `plato sandbox verify mutations` fails with mutations.

**Fix process:**
1. Read mutation analysis output to identify tables/columns being modified
2. Update `audit_ignore_tables` in plato-config.yml:
   - Ignore entire table: `- sessions`
   - Ignore specific columns: `- users: [last_login, updated_at]`
   - Wildcard for all tables: `- "*": [created_at, updated_at]`
3. Restart worker:
   ```bash
   plato sandbox stop-worker
   plato sandbox start-worker --wait
   ```
4. Loop back to Step 8 (sim-flow-clear)
5. Re-run Steps 8-10 until 0 mutations

**IMPORTANT:** Do NOT use a separate `ignore_columns` field. Column-level ignores must be inside `audit_ignore_tables`.

---

## Success Output

```
✅ Simulator {sim_name} created and submitted for review!

Artifact: {artifact_id}
Status: review_requested

The simulator is queued for human approval.
```

---

## DO NOT

- Skip verification steps
- Proceed when verification fails
- Start worker before verifying login works (Step 6)
- Snapshot before achieving 0 mutations (Step 10)
- Create test data during verification
- Approve simulators yourself - only humans can approve
- Use curl to directly call status API
