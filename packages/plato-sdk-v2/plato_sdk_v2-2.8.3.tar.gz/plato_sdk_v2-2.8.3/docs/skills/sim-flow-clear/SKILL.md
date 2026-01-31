---
name: sim-flow-clear
description: Clear the audit log before running login flow. Use after worker is started.
allowed-tools: Bash, Read
context: fork
---

# Simulator Flow Clear

**Pipeline Position:** Phase 3, Step 1
**Previous Step:** sim-sandbox-worker
**Next Step:** sim-flow-run

## API Key

**CRITICAL: Export this BEFORE running any plato commands:**
```bash
export PLATO_API_KEY="pk_user_IgNNSJp5v_J0EMJtnxHGw6y68lfdYXiWdXNq1v_JaQQ"
```

---

## Purpose

Clear the audit log to establish a clean baseline before running the login flow.

**Why this matters:**
- Manual testing during login verification creates mutations
- Lazy initialization when browsing pages creates mutations
- Previous flow runs leave mutations
- We need 0 mutations BEFORE running the login flow to get accurate results

---

## Input Required

From previous step (sim-sandbox-worker):
- Worker running and connected
- Audit triggers installed

---

## Action

### Step 1: Clear Audit Log

```bash
export PLATO_API_KEY="pk_user_IgNNSJp5v_J0EMJtnxHGw6y68lfdYXiWdXNq1v_JaQQ"
plato sandbox clear-audit
```

### Step 2: Verify

```bash
plato sandbox verify audit-clear
```

**Must show:**
- ✅ Audit log clear: 0 mutations

---

## On Success

Output:
```yaml
sandbox_result:
  action: clear-audit
  success: true
  mutations: 0
```

Proceed to: **sim-flow-run**

---

## On Failure

### If mutations still > 0

Try again:
```bash
plato sandbox clear-audit
plato sandbox verify audit-clear
```

### If command fails

Check worker is running:
```bash
plato sandbox verify worker
```

If worker not connected, restart it:
```bash
plato sandbox stop-worker
plato sandbox start-worker --wait
```

---

## DO NOT

- Skip this step - mutations from previous activity will pollute results
- Run login flow without clearing first
- Proceed if verify fails
