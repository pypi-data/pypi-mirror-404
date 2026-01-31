---
name: sim-debugger
description: Diagnoses and fixes simulator failures. Can inspect the running sandbox with browser tools. Routes issues to config-writer or flow-writer skills. Use when sandbox operations fail.
allowed-tools: Bash, Read, Write, Edit, mcp__playwright__browser_navigate, mcp__playwright__browser_snapshot, mcp__playwright__browser_take_screenshot, mcp__playwright__browser_click, mcp__playwright__browser_type
context: fork
---

# Plato Simulator Debugger

**Pipeline Position:** Central Fix Loop

**PRINCIPLE: Never return to human. Keep fixing until it works.**

You are the brain of the system. You have all context needed to fix any failure - config format, flow format, review expectations. You fix issues directly, then loop back to the appropriate pipeline step.

## API Key

**Always use this API key for all Plato CLI commands:**
```bash
export PLATO_API_KEY="pk_user_IgNNSJp5v_J0EMJtnxHGw6y68lfdYXiWdXNq1v_JaQQ"
```

---

## Input

```yaml
error_type: "healthcheck"  # or "flow", "review", "worker"
error_details: "..."
sandbox_id: "sandbox-42"
public_url: "https://job-789.sims.plato.so?_plato_router_target=appname.web.plato.so"
ssh_config: "~/.plato/ssh_42.conf"
sim_name: "appname"
sim_path: "/path/to/sim"
```

---

## Debug Workflow

### CRITICAL: Two Docker Sockets


### CRITICAL: Code Path

The code lives at:
```
/home/plato/worktree/{sim_name}/base/
```

### INNER LOOP: Fast Iteration on VM

**DO NOT** run `plato sandbox start-services` for every fix. That's slow.

Instead, iterate directly on the VM:

```bash
# 1. SSH into VM
ssh -F {ssh_config} sandbox-{id}

# 2. Go to code directory
cd /home/plato/worktree/{sim_name}/base

# 4. Edit files directly
vim docker-compose.yml

# 5. Restart containers (fast!)
docker compose down && docker compose up -d

# 6. Watch logs
docker compose logs -f

# 7. Test
curl http://localhost:80/
```

Repeat until it works on the VM.

### SYNC BACK: Copy Working Files to Local

Once it works on the VM:

```bash
scp -F {ssh_config} sandbox-{id}:/home/plato/code/base/docker-compose.yml {sim_path}/base/
scp -F {ssh_config} sandbox-{id}:/home/plato/code/base/flows.yml {sim_path}/base/
```

### OUTER LOOP: Verify Official Flow

```bash
cd {sim_path}
plato sandbox start-services
```

This syncs local files to VM and runs the official flow.

---

## Error Types and Fixes

### Container Won't Start

**Diagnose:**
```bash
ssh -F {ssh_config} sandbox-{id}
docker ps -a
docker logs {container} --tail 100
```

**Common fixes:**
- Missing env var → Add to docker-compose.yml
- Wrong database URL → Use `127.0.0.1`, not service name
- Port conflict → Check `network_mode: host`

**Loop back to:** start-services

### Healthcheck Timeout

**Common fixes:**
- Increase `start_period` in healthcheck
- Database not ready → Check db healthcheck
- Migrations slow → Increase timeout

**docker-compose.yml healthcheck format:**
```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:80/ || exit 1"]
  interval: 15s
  timeout: 5s
  retries: 5
  start_period: 45s
```

**Loop back to:** start-services

### 502 Bad Gateway / Port Routing Issue

**Symptoms:** Browser shows "502 Bad Gateway" from openresty

**Diagnose:** Check what port the router is using:
```bash
curl -sI "{public_url}" 2>&1 | grep location
# Extract the token from the location header and decode it:
python3 -c "
import base64, json
token = 'PASTE_TOKEN_HERE'
# Add padding
token += '=' * (4 - len(token) % 4)
data = json.loads(base64.b64decode(token))
print(f'vm_port: {data.get(\"vm_port\")}')
"
```

**Common issue:** The `vm_port` (usually **80 or 8888**) doesn't match what your app is listening on.

**Fix:** Your app/nginx must listen on the port the router expects (`vm_port`):
- Check `vm_port` from the decoded token
- Update nginx to `listen {vm_port};`
- Proxy to your app's actual internal port

**Example nginx config** (if `vm_port` is 80 but app listens on 8000):
```nginx
server {
    listen 80;  # Must match vm_port
    location / {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

**Loop back to:** start-services

### Login Page Not Found

**Diagnose:**
```
mcp__playwright__browser_navigate to {public_url}
mcp__playwright__browser_snapshot
```

**Common fixes:**
- Wrong login URL path
- App redirects to setup wizard
- App not fully started

**Loop back to:** test-login (flow-writer)

### Wrong Selectors

**Diagnose:**
```
mcp__playwright__browser_navigate to {public_url}/login
mcp__playwright__browser_snapshot
```

Find the actual selectors from the snapshot.

**flows.yml format (CRITICAL):**
```yaml
flows:
  - name: login
    description: Login to AppName
    steps:
      - description: Screenshot
        type: screenshot
        filename: 01_landing.png
      - description: Navigate to login
        type: navigate
        url: /login
      - description: Wait for page
        type: wait
        duration: 3000
      - description: Fill username
        type: fill
        selector: "input#email"
        value: admin@example.com
      - description: Fill password
        type: fill
        selector: "input#password"
        value: password123
      - description: Click submit
        type: click
        selector: "button[type='submit']"
      - description: Wait for login
        type: wait
        duration: 3000
      - description: Screenshot result
        type: screenshot
        filename: 02_logged_in.png

  - name: incorrect_login
    description: Verify login fails with wrong password
    steps:
      # Similar steps with wrong password
```

**Rules:**
- Use `type:` NOT `action:`
- Hardcode credentials, NOT `{{templates}}`
- Must have both `login` and `incorrect_login` flows
- Must have `flows:` wrapper at top level

**Loop back to:** test-login

### Worker Infinite Loop

**Symptoms:** Errors every 30 seconds in `/var/log/docker-user.log`

**Fix:**
```bash
plato sandbox stop
plato sandbox start -c     # -c = from plato-config.yml
plato sandbox start-services
# TEST LOGIN WORKS FIRST
plato sandbox start-worker
```

**Loop back to:** start-services

### Mutations After Login (Review Fail)

**Diagnose:** Look at the mutation output to identify which tables/columns are being modified.

**Fix:** Add to `audit_ignore_tables` in plato-config.yml, then **restart the worker**.

### audit_ignore_tables Format

There are THREE formats:

**Format 1: Ignore entire table (string)**
```yaml
audit_ignore_tables:
  - sessions           # Ignores ALL changes to this table
  - migration_versions
```

**Format 2: Ignore specific columns (inline format - PREFERRED)**
```yaml
audit_ignore_tables:
  - users: [last_login, updated_at, session_token]  # Inline format
  - posts: [modified_at]
```

**Format 3: Ignore specific columns (verbose format)**
```yaml
audit_ignore_tables:
  - table: users
    columns:
      - last_login     # Only ignore changes to these columns
      - updated_at
      - session_token
```

**Format 4: Mix of all formats**
```yaml
audit_ignore_tables:
  - sessions                    # Ignore entire table (Format 1)
  - doctrine_migration_versions # Ignore entire table (Format 1)
  - users: [last_login, last_activity]  # Ignore columns (Format 2 - inline)
  - table: audit_log            # Ignore columns (Format 3 - verbose)
    columns:
      - timestamp
```

**IMPORTANT:** Do NOT use a separate `ignore_columns` field. Column-level ignores must be inside `audit_ignore_tables`.

### When to use which format

| Scenario | Format | Example |
|----------|--------|---------|
| Session/login tracking tables | Entire table | `- sessions` |
| Migration/schema tables | Entire table | `- doctrine_migration_versions` |
| User table with `last_login` column | Column-only | `table: users, columns: [last_login]` |
| Audit logs you don't care about | Entire table | `- audit_log` |
| Timestamp columns updated on every request | Column-only | `table: posts, columns: [updated_at]` |

**Rule of thumb:**
- If the table is ONLY for session/login tracking → ignore entire table
- If the table has important data but also has "noise" columns (timestamps, counters) → ignore specific columns

### CRITICAL: Restart the worker!

**Just editing `plato-config.yml` is NOT enough.** The worker reads audit_ignore_tables at startup.

```bash
# Stop the worker
plato sandbox stop-worker

# Restart the worker and wait for it to be ready (~4 min)
plato sandbox start-worker --wait

# Run login flow
plato sandbox flow login

# Verify no mutations (exits with code 1 if mutations found)
plato sandbox state --verify-no-mutations
```

### Visual helper tool

For complex cases, use the audit UI:
```bash
plato sandbox audit-ui
```
This opens a Streamlit app that shows all tables/columns and lets you check boxes to ignore them.

**Loop back to:** snapshot (after worker restart)

### No Mutations Detected (Review Fail)

**Fix:** Check audit config in plato-config.yml. Ensure:
- `db_type` matches actual database
- `db_host: 127.0.0.1`
- `db_port` correct (5432 for postgres, 3306 for mysql)
- `volumes` includes signal path

**Loop back to:** snapshot

---

## Config Knowledge (from config-writer)

### Database Images - USE PLATO IMAGES

| Database | Image |
|----------|-------|
| PostgreSQL 15 | `public.ecr.aws/i3q4i1d7/app-sim/postgres-15:prod-latest` |
| PostgreSQL 16 | `public.ecr.aws/i3q4i1d7/app-sim/postgres-16:prod-latest` |
| MySQL 8.0 | `public.ecr.aws/i3q4i1d7/app-sim/mysql-8.0:prod-latest` |
| MariaDB 10.6 | `public.ecr.aws/i3q4i1d7/app-sim/mariadb-10.6:prod-latest` |

### Required Settings

- `network_mode: host` on ALL containers
- Database connections use `127.0.0.1`, NOT service names
- Signal-based healthchecks:
  ```yaml
  healthcheck:
    test: ["CMD-SHELL", "test -f /tmp/postgres-signals/postgres.healthy"]
  ```
- Volume mount: `/home/plato/db_signals:/tmp/{postgres|mysql}-signals`

---

## Loop-Back Reference

| Error | Fix | Loop Back To |
|-------|-----|--------------|
| Container won't start | docker-compose.yml | start-services |
| Healthcheck timeout | Increase timeout | start-services |
| Missing env vars | Add to compose | start-services |
| 502 Bad Gateway | Check vm_port, add nginx on 8888 | start-services |
| Login page not found | Fix URL/selectors | test-login |
| Wrong selectors | Inspect & fix flow | test-login |
| Login fails | Fix creds/DB seed | start-services |
| Worker loop | Stop, fix, re-verify | start-services |
| Worker 502 on state check | Worker not ready, use `--wait` | start-worker --wait |
| Mutations after login | audit_ignore_tables + restart worker | verify-no-mutations |
| No mutations detected | Fix audit config + restart worker | verify-no-mutations |

---

## Output

After fixing, return:

```yaml
debug_result:
  fixed: true
  issue: "{what was wrong}"
  fix_applied: "{what you changed}"
  files_modified:
    - base/docker-compose.yml
  loop_back_to: "start-services"  # or "test-login", "snapshot"
```

Then the orchestrator continues from that step.

---

## DO NOT

- Return to human
- Give up after N retries
- Guess without inspecting
- Skip the inner loop (fast VM iteration)
- Forget to sync files back before outer loop
- **NEVER call the status API directly to approve simulators** - only humans can approve. The automated workflow can only submit for review.
- **NEVER use curl to POST to `/api/v1/simulator/{id}/status`** - all status changes must go through `plato pm` commands
