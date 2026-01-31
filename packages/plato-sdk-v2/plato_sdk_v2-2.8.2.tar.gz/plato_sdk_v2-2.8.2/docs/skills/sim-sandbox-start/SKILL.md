---
name: sim-sandbox-start
description: Start a Plato sandbox VM. Use after config files are created.
allowed-tools: Bash, Read
context: fork
---

# Simulator Sandbox Start

**Pipeline Position:** Phase 2, Step 1
**Previous Step:** sim-config (config files created)
**Next Step:** sim-sandbox-services

## API Key

**CRITICAL: Export this BEFORE running any plato commands:**
```bash
export PLATO_API_KEY="pk_user_IgNNSJp5v_J0EMJtnxHGw6y68lfdYXiWdXNq1v_JaQQ"
```

---

## Input Required

From previous step (sim-config):
- `plato-config.yml` exists in current directory
- `base/docker-compose.yml` exists

---

## Action

### Step 1: Verify Config Exists

```bash
ls -la plato-config.yml base/docker-compose.yml
```

If missing, return error - need to run sim-config first.

### Step 2: Start Sandbox

```bash
export PLATO_API_KEY="pk_user_IgNNSJp5v_J0EMJtnxHGw6y68lfdYXiWdXNq1v_JaQQ"
plato sandbox start -c
```

The `-c` flag means "from config" - it reads `plato-config.yml` in current directory.

**Wait for output showing:**
- Sandbox ID assigned
- SSH config created
- Public URL assigned

### Step 3: Verify

```bash
plato sandbox verify
```

**Must show all green:**
- ✅ .sandbox.yaml exists
- ✅ job_id present
- ✅ session_id present
- ✅ public_url present
- ✅ ssh_config_path present
- ✅ plato_config_path present
- ✅ service present

---

## On Success

Output:
```yaml
sandbox_result:
  action: start
  success: true
  sandbox_id: "{sandbox_id}"
  job_id: "{job_id}"
  public_url: "{public_url}"
  ssh_config: "{ssh_config_path}"
```

Proceed to: **sim-sandbox-services**

---

## On Failure

### If .sandbox.yaml missing fields

The verify command will tell you exactly what's missing.

**Common fix:** Add missing fields manually:
```yaml
# Add to .sandbox.yaml
plato_config_path: /absolute/path/to/plato-config.yml
service: your-sim-name
```

### If sandbox start fails

Check:
1. API key is set: `echo $PLATO_API_KEY`
2. plato-config.yml is valid: `plato sandbox verify config`
3. Network connectivity to plato.so

---

## DO NOT

- Start services in this step (that's sim-sandbox-services)
- Start worker in this step (that's sim-sandbox-worker)
- Proceed if verify fails
