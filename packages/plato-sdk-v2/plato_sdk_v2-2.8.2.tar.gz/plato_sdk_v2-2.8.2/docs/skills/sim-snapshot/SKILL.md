---
name: sim-snapshot
description: Create a snapshot of the simulator state. Use after audit verification passes.
allowed-tools: Bash, Read
context: fork
---

# Simulator Snapshot

**Pipeline Position:** Phase 4, Step 1
**Previous Step:** sim-flow-audit
**Next Step:** sim-review

## API Key

**CRITICAL: Export this BEFORE running any plato commands:**
```bash
export PLATO_API_KEY="pk_user_IgNNSJp5v_J0EMJtnxHGw6y68lfdYXiWdXNq1v_JaQQ"
```

---

## Input Required

From previous steps:
- 0 mutations after login flow
- Audit system verified working
- Audit log cleared after verification test

---

## When to Snapshot

**Only snapshot when EVERYTHING is working:**
- ✅ Services healthy
- ✅ Login works
- ✅ Worker connected with audit triggers
- ✅ Login flow runs with 0 mutations
- ✅ Audit system verified (changes ARE tracked)
- ✅ No test data created

**Do NOT snapshot multiple times during testing.** Test everything on ONE sandbox, snapshot ONCE when ready.

---

## Action

### Step 1: Final Pre-Snapshot Checks

```bash
export PLATO_API_KEY="pk_user_IgNNSJp5v_J0EMJtnxHGw6y68lfdYXiWdXNq1v_JaQQ"

# Verify audit is clear
plato sandbox verify audit-clear

# If not clear, clear it
plato sandbox clear-audit
```

### Step 2: Create Snapshot

```bash
plato sandbox snapshot
```

This:
1. Captures current database state
2. Creates artifact on Plato servers
3. Returns artifact_id
4. Saves artifact_id to .sandbox.yaml

### Step 3: Verify Snapshot

```bash
plato sandbox verify snapshot
```

**Must show:**
- ✅ artifact_id present and valid

---

## On Success

Output:
```yaml
sandbox_result:
  action: snapshot
  success: true
  artifact_id: "e9c25ca5-1234-5678-9abc-def012345678"
```

Proceed to: **sim-review**

---

## On Failure

### If "Worker not connected"

Worker died or disconnected:
```bash
plato sandbox verify worker
plato sandbox start-worker --wait  # If needed
plato sandbox snapshot
```

### If artifact_id not saved

Manually add to .sandbox.yaml:
```yaml
artifact_id: "e9c25ca5-1234-5678-9abc-def012345678"
```

### If snapshot times out

Large databases may take longer:
```bash
# Wait and retry
plato sandbox snapshot
```

---

## What Gets Snapshotted

The snapshot captures:
- All database tables and data
- Current state of the app

**NOT included:**
- File system changes
- Container images (uses original images)
- Logs

---

## Test Data Warning

**If you accidentally created test data, it's now in the snapshot.**

Options:
1. Delete test data via app, clear audit, re-snapshot
2. Start fresh with new sandbox

Test data in a snapshot = polluted simulator that will confuse users.

---

## DO NOT

- Snapshot before verifying 0 mutations
- Snapshot multiple times during testing
- Snapshot with test data in the database
- Skip the pre-snapshot audit clear
