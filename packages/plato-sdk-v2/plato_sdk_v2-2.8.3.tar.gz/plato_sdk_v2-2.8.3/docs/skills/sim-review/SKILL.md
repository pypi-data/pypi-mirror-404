---
name: sim-review
description: Run the official review workflow to final-check the simulator. Use after snapshot.
allowed-tools: Bash, Read, mcp__playwright__browser_navigate, mcp__playwright__browser_snapshot
context: fork
---

# Simulator Review

**Pipeline Position:** Phase 4, Step 2
**Previous Step:** sim-snapshot
**Next Step:** sim-submit

## API Key

**CRITICAL: Export this BEFORE running any plato commands:**
```bash
export PLATO_API_KEY="pk_user_IgNNSJp5v_J0EMJtnxHGw6y68lfdYXiWdXNq1v_JaQQ"
```

---

## Purpose

Run the official review workflow as a final check before submission.

This is a **sanity check** - all the real verification happened in earlier steps:
- Login verified in sim-sandbox-login
- Worker verified in sim-sandbox-worker
- Mutations verified in sim-flow-mutations
- Audit verified in sim-flow-audit

---

## Input Required

From previous steps:
- artifact_id from sim-snapshot
- service name

---

## Action

### Step 1: Verify Prerequisites

```bash
export PLATO_API_KEY="pk_user_IgNNSJp5v_J0EMJtnxHGw6y68lfdYXiWdXNq1v_JaQQ"
plato pm verify review
```

Must show all green.

### Step 2: Run Review

```bash
export PLATO_API_KEY="pk_user_IgNNSJp5v_J0EMJtnxHGw6y68lfdYXiWdXNq1v_JaQQ"
plato pm review base -s {service} -a {artifact_id} --skip-review
```

**Always use `--skip-review`** - interactive mode doesn't work with Claude Code.

### Step 3: Check Output

**Success indicators:**
```
✅ Logged into environment
Checking environment state after login...
No mutations recorded
✅ Login flow verified - no mutations created
```

**Failure indicators:**
```
Mutations (N):
⚠️  WARNING: Login flow created mutations!
```

---

## On Success

Output:
```yaml
review_result:
  passed: true
  artifact_id: "{artifact_id}"
```

Proceed to: **sim-submit**

---

## On Failure

### If mutations detected

This shouldn't happen if earlier steps passed. Go back and check:
1. Did sim-flow-mutations actually pass with 0?
2. Was a fresh snapshot created after fixing mutations?

**Fix:**
```bash
plato sandbox clear-audit
plato sandbox flow login
plato sandbox verify mutations
# If 0, re-snapshot
plato sandbox snapshot
```

### If login fails

Login flow issue. Check:
1. Credentials in flows.yml
2. Selectors in flows.yml

### If state errors (502)

Worker issue. Restart:
```bash
plato sandbox stop-worker
plato sandbox start-worker --wait
```

---

## DO NOT

- Use interactive review (omit `--skip-review`) - it will hang
- Proceed if review fails
- Submit before review passes
