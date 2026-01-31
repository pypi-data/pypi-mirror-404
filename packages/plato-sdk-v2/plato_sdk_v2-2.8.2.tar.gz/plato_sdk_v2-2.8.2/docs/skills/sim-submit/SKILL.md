---
name: sim-submit
description: Submit simulator for human review. Use after review passes.
allowed-tools: Bash, Read
context: fork
---

# Simulator Submit

**Pipeline Position:** Phase 4, Step 3 (Final)
**Previous Step:** sim-review
**Next Step:** (Human review)

## API Key

**CRITICAL: Export this BEFORE running any plato commands:**
```bash
export PLATO_API_KEY="pk_user_IgNNSJp5v_J0EMJtnxHGw6y68lfdYXiWdXNq1v_JaQQ"
```

---

## Input Required

From previous step (sim-review):
- Review passed all checks
- artifact_id confirmed valid

---

## Action

### Step 1: Verify Ready to Submit

```bash
export PLATO_API_KEY="pk_user_IgNNSJp5v_J0EMJtnxHGw6y68lfdYXiWdXNq1v_JaQQ"
plato pm verify submit
```

**Must show all green:**
- ✅ PLATO_API_KEY: set
- ✅ .sandbox.yaml: exists
- ✅ artifact_id: present
- ✅ service: present
- ✅ plato_config_path: present

### Step 2: Submit

```bash
plato pm submit base
```

This:
1. Syncs metadata to server (description, license, favicon, credentials)
2. Associates artifact with simulator
3. Changes status to `review_requested`

---

## On Success

Output:
```
Simulator:      appname
Artifact ID:    e9c25ca5-1234-5678-9abc-def012345678
Status:         env_in_progress → env_review_requested

✅ Submitted for review!
```

**The simulator is now waiting for human approval.**

Output:
```yaml
sandbox_result:
  action: submit
  success: true
  status: review_requested
  artifact_id: "e9c25ca5-1234-5678-9abc-def012345678"
```

---

## On Failure

### If "PLATO_API_KEY not set"

```bash
export PLATO_API_KEY="pk_user_IgNNSJp5v_J0EMJtnxHGw6y68lfdYXiWdXNq1v_JaQQ"
plato pm submit base
```

### If "No plato_config_path"

Add to .sandbox.yaml:
```yaml
plato_config_path: /absolute/path/to/plato-config.yml
```

### If "No artifact_id"

Run snapshot first:
```bash
plato sandbox snapshot
plato pm submit base
```

### If "No service"

Add to .sandbox.yaml:
```yaml
service: your-sim-name
```

### If "Unauthorized" or permission error

The API key must have permission for this simulator. Make sure you're using the correct key:
```bash
export PLATO_API_KEY="pk_user_IgNNSJp5v_J0EMJtnxHGw6y68lfdYXiWdXNq1v_JaQQ"
```

---

## What Happens After Submit

1. Simulator status changes to `review_requested`
2. Human reviewer is notified
3. Reviewer checks:
   - Metadata is correct
   - Login flow works
   - No mutations after login
   - App is functional
4. Reviewer approves or requests changes

**You cannot approve your own simulator.** Only humans can approve.

---

## DO NOT

- Submit without running review first
- Submit without the API key
- Try to approve the simulator yourself
- Use curl to directly call status API
- Submit multiple times (check status first)
