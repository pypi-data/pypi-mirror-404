---
name: sim-sandbox-worker
description: Start the Plato worker on sandbox. Use after manual login is verified.
allowed-tools: Bash, Read
context: fork
---

# Simulator Sandbox Worker

**Pipeline Position:** Phase 2, Step 4
**Previous Step:** sim-sandbox-login
**Next Step:** sim-flow-clear

## API Key

**CRITICAL: Export this BEFORE running any plato commands:**
```bash
export PLATO_API_KEY="pk_user_IgNNSJp5v_J0EMJtnxHGw6y68lfdYXiWdXNq1v_JaQQ"
```

---

## Input Required

From previous step (sim-sandbox-login):
- Manual login verified working
- Credentials confirmed correct
- No setup wizards pending

---

## CRITICAL: Why This Order Matters

**NEVER start the worker before verifying login works.**

If services are broken, the worker will:
1. Try to connect
2. Fail with 30-second timeout
3. Retry infinitely
4. Waste time and resources

By verifying login first, we know the app is working.

---

## Action

### Step 1: Start Worker

```bash
export PLATO_API_KEY="pk_user_IgNNSJp5v_J0EMJtnxHGw6y68lfdYXiWdXNq1v_JaQQ"
plato sandbox start-worker --wait
```

**The `--wait` flag is REQUIRED.** It waits for the worker to be fully ready (~4 minutes).

Without `--wait`, subsequent commands will fail with 502 errors.

### Step 2: Verify Worker

```bash
plato sandbox verify worker
```

**Must show:**
- ✅ Worker connected: true
- ✅ Audit triggers installed (audit_log_count field exists)
- ✅ Tables tracked: (number)

---

## On Success

Output:
```yaml
sandbox_result:
  action: worker
  success: true
  worker_ready: true
  connected: true
  audit_triggers_installed: true
  tables_tracked: 45
```

Proceed to: **sim-flow-clear**

---

## On Failure

### If "connected: true" but no audit_log_count

**This is a critical failure.** The worker connected but didn't install audit triggers.

"No mutations" results will be meaningless because nothing is being tracked.

**Fix:**
```bash
plato sandbox stop-worker
plato sandbox start-worker --wait
plato sandbox verify worker
```

### If still broken after restart

SSH into sandbox and check worker logs:

```bash
ssh -F {ssh_config} {ssh_host}
docker logs plato-worker 2>&1 | tail -50
```

Common issues:
- Wrong database credentials in plato-config.yml
- Database not accessible on 127.0.0.1
- Database type mismatch

### If 502 errors

Worker isn't ready yet. Either:
1. Wait longer (can take 4+ minutes)
2. Forgot `--wait` flag - restart with `--wait`

### If connection refused

Database isn't running or wrong credentials:
1. Check database container is healthy
2. Verify db_host, db_port, db_user, db_password in plato-config.yml

---

## How Audit Triggers Work

The Plato worker:
1. Connects to the database
2. Creates audit triggers on all tables
3. These triggers log all INSERT/UPDATE/DELETE operations
4. The state API reads from this audit log

**If triggers aren't installed:**
- Changes won't be tracked
- "0 mutations" is meaningless
- The simulator will be broken

---

## DO NOT

- Start worker before verifying login works
- Skip the `--wait` flag
- Proceed if audit_log_count is missing
- Assume "connected: true" means everything works
