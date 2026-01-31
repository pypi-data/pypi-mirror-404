---
name: sim-flow-audit
description: Verify audit system is actively tracking changes. Use after 0 mutations confirmed.
allowed-tools: Bash, Read, mcp__playwright__browser_navigate, mcp__playwright__browser_snapshot, mcp__playwright__browser_type, mcp__playwright__browser_click
context: fork
---

# Simulator Flow Audit

**Pipeline Position:** Phase 3, Step 4
**Previous Step:** sim-flow-mutations (with 0 mutations)
**Next Step:** sim-snapshot

## API Key

**CRITICAL: Export this BEFORE running any plato commands:**
```bash
export PLATO_API_KEY="pk_user_IgNNSJp5v_J0EMJtnxHGw6y68lfdYXiWdXNq1v_JaQQ"
```

---

## Purpose

Verify the audit system is actually working by confirming changes ARE tracked.

**Why this matters:**
- "0 mutations after login" could mean login is read-only (good)
- OR it could mean audit is broken and nothing is being tracked (bad)
- We need to prove audit works before trusting the "0 mutations" result

---

## Input Required

From previous step (sim-flow-mutations):
- 0 mutations after login flow
- Still have browser access to logged-in app

---

## CRITICAL: Do NOT Create Test Data

**When verifying audit, do NOT create new records.**

Why? Test data ends up in the snapshot and pollutes the simulator.

**DO verify by:**
- Update a setting (language, timezone, theme)
- Change profile info (then change back)
- Toggle a preference

**Do NOT verify by:**
- Creating new users
- Creating new items/categories
- Adding test records

---

## Action

### Step 1: Make a Small Change in the App

Navigate to settings and change something:

```
mcp__playwright__browser_navigate to {public_url}/settings (or similar)
mcp__playwright__browser_snapshot
```

Find a setting to change (theme, language, timezone) and change it:

```
mcp__playwright__browser_click on setting toggle/dropdown
mcp__playwright__browser_snapshot
```

### Step 2: Check State for Mutations

```bash
export PLATO_API_KEY="pk_user_IgNNSJp5v_J0EMJtnxHGw6y68lfdYXiWdXNq1v_JaQQ"
plato sandbox state -v
```

### Step 3: Verify Mutations Appear

**Expected:** 1 or more mutations from your change

```
Mutations (1):
  - table: settings, operation: UPDATE
```

**If mutations appear:** ✅ Audit system is working!

**If NO mutations appear:** ❌ Audit system is broken!

---

## On Success (Mutations Appear)

Output:
```yaml
sandbox_result:
  action: audit-verify
  success: true
  audit_working: true
  test_mutations: 1
```

**Important:** Now clear the audit log before snapshot:

```bash
plato sandbox clear-audit
```

Proceed to: **sim-snapshot**

---

## On Failure (No Mutations After Change)

The audit system is broken. "0 mutations after login" was meaningless.

**Fix:**
```bash
plato sandbox stop-worker
plato sandbox start-worker --wait
plato sandbox verify worker
```

Make sure `audit_log_count` field exists in verify output.

If still broken, SSH and check worker logs:
```bash
ssh -F {ssh_config} {ssh_host}
docker logs plato-worker 2>&1 | tail -50
```

---

## What If I Accidentally Created Test Data?

If you created test records instead of updating settings:

**Option 1:** Delete the test data, then clear audit
```bash
# Delete via app UI or database
plato sandbox clear-audit
```

**Option 2:** Start fresh with new sandbox
```bash
plato sandbox stop
plato sandbox start -c
# Restart the whole process
```

---

## DO NOT

- Create test data (items, users, categories)
- Skip this verification step
- Proceed to snapshot if audit isn't working
- Forget to clear-audit after your test change
