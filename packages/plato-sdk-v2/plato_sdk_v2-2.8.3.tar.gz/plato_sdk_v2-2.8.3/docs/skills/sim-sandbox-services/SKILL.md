---
name: sim-sandbox-services
description: Start containers on sandbox VM. Use after sandbox is started.
allowed-tools: Bash, Read
context: fork
---

# Simulator Sandbox Services

**Pipeline Position:** Phase 2, Step 2
**Previous Step:** sim-sandbox-start
**Next Step:** sim-sandbox-login

## API Key

**CRITICAL: Export this BEFORE running any plato commands:**
```bash
export PLATO_API_KEY="pk_user_IgNNSJp5v_J0EMJtnxHGw6y68lfdYXiWdXNq1v_JaQQ"
```

---

## Input Required

From previous step (sim-sandbox-start):
- `.sandbox.yaml` exists with all required fields
- Sandbox VM is running

---

## Action

### Step 1: Verify Sandbox Ready

```bash
plato sandbox verify
```

Must pass before continuing.

### Step 2: Start Services

```bash
export PLATO_API_KEY="pk_user_IgNNSJp5v_J0EMJtnxHGw6y68lfdYXiWdXNq1v_JaQQ"
plato sandbox start-services
```

This:
- Uploads code to VM
- Runs `docker compose up -d`
- Waits for containers to be healthy

**Wait for output showing:**
- All containers started
- Health checks passed

### Step 3: Verify

```bash
plato sandbox verify services
```

**Must show:**
- ✅ All containers running
- ✅ All containers healthy
- ✅ Public URL returns 200 (not 502)

---

## On Success

Output:
```yaml
sandbox_result:
  action: services
  success: true
  containers:
    - name: db
      status: healthy
    - name: app
      status: healthy
  public_url_status: 200
```

Proceed to: **sim-sandbox-login**

---

## On Failure

### If containers unhealthy

```bash
# SSH into sandbox and check logs
ssh -F {ssh_config} {ssh_host}
docker compose logs -f
```

Common issues:
- Database connection failed (check DB_HOST is 127.0.0.1)
- Missing environment variables
- Port conflicts

### If 502 Bad Gateway

The router can't reach the app. Check what's listening:

```bash
ssh -F {ssh_config} {ssh_host} "netstat -tlnp | grep LISTEN"
```

**Fix options:**
1. Change app to listen on expected port (check `app_port` in plato-config.yml)
2. Add nginx to proxy from `app_port` to app's actual port

### If timeout waiting for healthy

Increase timeout in plato-config.yml:
```yaml
services:
  main_app:
    healthy_wait_timeout: 600  # 10 minutes
```

---

## DO NOT

- Start worker in this step (that's sim-sandbox-worker)
- Login in this step (that's sim-sandbox-login)
- Proceed if verify fails
- Ignore 502 errors - they must be fixed
