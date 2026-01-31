# Simulator Creation Pipeline

This document describes the automated simulator creation pipeline with verification gates at each step.

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           PHASE 1: CONFIGURATION                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                      │
│  │  Research    │───▶│  Validate    │───▶│ Write Config │                      │
│  │              │    │              │    │              │                      │
│  │ sim-research │    │sim-validator │    │sim-config-   │                      │
│  │              │    │              │    │   writer     │                      │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                      │
│         │                   │                   │                              │
│         ▼                   ▼                   ▼                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                      │
│  │    VERIFY    │    │    VERIFY    │    │    VERIFY    │                      │
│  │   research   │    │  validation  │    │    config    │                      │
│  └──────────────┘    └──────────────┘    └──────────────┘                      │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           PHASE 2: SANDBOX SETUP                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │    Start     │───▶│    Start     │───▶│   Manual     │───▶│    Start     │  │
│  │   Sandbox    │    │   Services   │    │    Login     │    │    Worker    │  │
│  │              │    │              │    │  (Browser)   │    │              │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                   │                   │          │
│         ▼                   ▼                   ▼                   ▼          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │    VERIFY    │    │    VERIFY    │    │    VERIFY    │    │    VERIFY    │  │
│  │   sandbox    │    │   services   │    │    login     │    │    worker    │  │
│  └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           PHASE 3: FLOW TESTING                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │    Clear     │───▶│  Run Login   │───▶│    Check     │───▶│   Verify     │  │
│  │    Audit     │    │    Flow      │    │  Mutations   │    │ Audit Works  │  │
│  │              │    │              │    │              │    │  (Browser)   │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                   │                   │          │
│         ▼                   ▼                   ▼                   ▼          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │    VERIFY    │    │    VERIFY    │    │    VERIFY    │    │    VERIFY    │  │
│  │ audit-clear  │    │     flow     │    │  mutations   │    │ audit-active │  │
│  └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                                                 │
│                      ┌─────────────────────────────────┐                       │
│                      │  If mutations > 0:              │                       │
│                      │  - Analyze INSERT vs UPDATE     │                       │
│                      │  - Update audit_ignore_tables   │                       │
│                      │  - Loop back to Clear Audit     │                       │
│                      └─────────────────────────────────┘                       │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           PHASE 4: SNAPSHOT & SUBMIT                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                      │
│  │   Create     │───▶│    Review    │───▶│    Submit    │                      │
│  │  Snapshot    │    │              │    │              │                      │
│  │              │    │              │    │              │                      │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                      │
│         │                   │                   │                              │
│         ▼                   ▼                   ▼                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                      │
│  │    VERIFY    │    │    VERIFY    │    │    VERIFY    │                      │
│  │   snapshot   │    │    review    │    │    submit    │                      │
│  └──────────────┘    └──────────────┘    └──────────────┘                      │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Verification Commands Reference

All verification commands follow the pattern:
```bash
plato <domain> verify <check>
```

---

## Phase 1: Configuration

### Step 1.1: Research

**Action:** Run `sim-research` skill

**Work:**
- Fetch GitHub repository
- Identify Docker image and tag
- Determine database type (PostgreSQL/MySQL/MariaDB)
- Find default credentials
- Gather required environment variables
- Get license, description, favicon URL

**Verify:** `plato sandbox verify research`

| Check | Pass Criteria | Failure Action |
|-------|---------------|----------------|
| db_type | One of: postgresql, mysql, mariadb | Research again or mark as unsupported |
| docker_image | Image name present | Search Docker Hub / GitHub packages |
| docker_tag | Tag present (not "latest") | Find stable version tag |
| credentials | Username and password found | Check docs for defaults |
| env_vars | Required vars identified | Check Docker docs |

**Output on failure:**
```
❌ Research incomplete

Missing required fields:
  - docker_image: not found
  - credentials.password: not found

Suggestions:
  - Check GitHub packages: ghcr.io/{owner}/{repo}
  - Check Docker Hub: hub.docker.com/r/{owner}/{repo}
  - Look for INSTALL.md or docker-compose.yml in repo
```

---

### Step 1.2: Validate

**Action:** Run `sim-validator` skill

**Work:**
- Verify Docker image is pullable
- Confirm database type is supported
- Check for blockers (SQLite, commercial license, etc.)

**Verify:** `plato sandbox verify validation`

| Check | Pass Criteria | Failure Action |
|-------|---------------|----------------|
| image_exists | `docker pull` succeeds | Fix image name/tag |
| db_supported | PostgreSQL, MySQL, or MariaDB | Mark as unsupported |
| no_blockers | No SQLite, no commercial-only | Mark as unsupported |

**Output on failure:**
```
❌ Validation failed

Blockers found:
  - Database: SQLite (not supported)

This application cannot become a Plato simulator.
Reason: Plato requires PostgreSQL, MySQL, or MariaDB for state tracking.
```

---

### Step 1.3: Write Config

**Action:** Run `sim-config-writer` skill

**Work:**
- Create `plato-config.yml` with metadata and listeners
- Create `base/docker-compose.yml` with containers
- Create `base/nginx.conf` if needed for port mapping
- Create `base/flows.yml` placeholder

**Verify:** `plato sandbox verify config`

| Check | Pass Criteria | Failure Action |
|-------|---------------|----------------|
| plato_config_exists | File exists at `./plato-config.yml` | Create file |
| plato_config_valid | Parses as valid YAML | Fix syntax errors |
| docker_compose_exists | File exists at `./base/docker-compose.yml` | Create file |
| docker_compose_valid | Parses as valid YAML | Fix syntax errors |
| plato_db_image | Uses `public.ecr.aws/i3q4i1d7/app-sim/*` | Replace with Plato image |
| network_mode_host | All services have `network_mode: host` | Add to each service |
| db_signals_volume | DB has `/home/plato/db_signals` volume | Add volume mount |
| db_healthcheck | Uses signal-based healthcheck | Replace healthcheck |
| required_fields | service, datasets.base.metadata.name, etc. | Add missing fields |

**Output on failure:**
```
❌ Config verification failed

Issues found:
  - docker-compose.yml line 5: Using postgres:15 instead of Plato image
    Fix: image: public.ecr.aws/i3q4i1d7/app-sim/postgres-15:prod-latest

  - docker-compose.yml line 12: Missing network_mode: host
    Fix: Add "network_mode: host" to service "app"

  - docker-compose.yml line 8: Missing db_signals volume
    Fix: Add volume "/home/plato/db_signals:/tmp/postgres-signals"
```

---

## Phase 2: Sandbox Setup

### Step 2.1: Start Sandbox

**Action:** `plato sandbox start -c`

**Work:**
- Provision VM on Plato infrastructure
- Upload config files to VM
- Create `.sandbox.yaml` with connection info

**Verify:** `plato sandbox verify`

| Check | Pass Criteria | Failure Action |
|-------|---------------|----------------|
| sandbox_yaml_exists | `.sandbox.yaml` exists | Re-run sandbox start |
| job_id | Field present and non-empty | Re-run sandbox start |
| session_id | Field present and non-empty | Re-run sandbox start |
| public_url | Field present and valid URL | Re-run sandbox start |
| ssh_config_path | Field present, file exists | Re-run sandbox start |
| plato_config_path | Field present, file exists | Add manually |
| service | Field present and non-empty | Add manually |

**Output on failure:**
```
❌ Sandbox verification failed

.sandbox.yaml is missing required fields:

  plato_config_path: MISSING
    Fix: Add "plato_config_path: /absolute/path/to/plato-config.yml"

  service: MISSING
    Fix: Add "service: your-sim-name"

Current .sandbox.yaml contents:
  job_id: ab9068fa-c6ab-41c5-ada1-15d36124a54b
  session_id: 778f8012-7aba-4c1d-84a2-01a86b7d56b7
  public_url: https://ab9068fa.sims.plato.so
  ssh_config_path: ~/.plato/ssh_249.conf
```

---

### Step 2.2: Start Services

**Action:** `plato sandbox start-services`

**Work:**
- Run `docker compose up -d` on VM
- Wait for containers to be healthy
- Expose app on public URL

**Verify:** `plato sandbox verify services`

| Check | Pass Criteria | Failure Action |
|-------|---------------|----------------|
| containers_running | All containers in "running" state | Check docker logs |
| containers_healthy | All required containers healthy | Check healthcheck config |
| public_url_accessible | HTTP 200 (not 502/503/timeout) | Check app_port config |
| no_error_logs | No crash loops in logs | Check env vars, DB connection |

**Output on failure:**
```
❌ Services verification failed

Container status:
  ✅ db: running (healthy)
  ❌ app: running (unhealthy)
  ⚪ nginx: waiting on app

Public URL: https://ab9068fa.sims.plato.so
  Status: 502 Bad Gateway

Diagnosis:
  The app container is unhealthy. Nothing is listening on port 8888.

  Current listeners on VM:
    - 5432: postgres
    - 3000: node (app)

  Expected by router: 8888

Fix options:
  1. Change app to listen on 8888
  2. Add nginx to proxy 8888 -> 3000
  3. Change app_port in plato-config.yml to 3000

Recent app logs:
  Error: ECONNREFUSED 127.0.0.1:5432
  (Database connection failed - check DB_HOST uses 127.0.0.1)
```

---

### Step 2.3: Manual Login

**Action:** Browser automation via Playwright

**Work:**
- Navigate to public URL
- Enter credentials
- Click login button
- Verify logged-in state

**Verify:** `plato sandbox verify login`

| Check | Pass Criteria | Failure Action |
|-------|---------------|----------------|
| page_loads | Not blank, not error page | Check services |
| login_form_found | Username/password fields exist | Check start_url |
| login_succeeds | Dashboard/home visible after login | Check credentials |
| no_setup_wizard | No onboarding/setup screens | Complete setup first |
| credentials_saved | Credentials recorded for flows.yml | Save to flows.yml |

**Output on failure:**
```
❌ Login verification failed

Screenshot analysis:
  - Current page: Setup Wizard (Step 1 of 3)
  - Expected: Dashboard or home page

Issue: The app requires first-time setup before login works.

Fix:
  1. Complete the setup wizard manually via browser
  2. Save any admin credentials you create
  3. Run: plato sandbox clear-audit
  4. Re-verify login
```

---

### Step 2.4: Start Worker

**Action:** `plato sandbox start-worker --wait`

**Work:**
- Start Plato worker container
- Connect to database
- Install audit triggers
- Wait for ready state (~4 min)

**Verify:** `plato sandbox verify worker`

| Check | Pass Criteria | Failure Action |
|-------|---------------|----------------|
| worker_running | Worker container in running state | Check worker logs |
| state_api_responds | `plato sandbox state` returns data | Wait longer or restart worker |
| connected_true | State shows `connected: true` | Check DB credentials in config |
| audit_triggers | `audit_log_count` field exists | Restart worker |
| no_502_errors | State API doesn't return 502 | Wait for worker to be ready |

**Output on failure:**
```
❌ Worker verification failed

State API response:
  connected: true
  tables: 45
  audit_log_count: <MISSING>

Issue: Worker is connected but audit triggers are NOT installed.
       "No mutations" results will be meaningless.

Fix:
  plato sandbox stop-worker
  plato sandbox start-worker --wait

If still failing, check worker logs:
  ssh -F ~/.plato/ssh_249.conf sandbox-249
  docker logs plato-worker 2>&1 | tail -50
```

---

## Phase 3: Flow Testing

### Step 3.1: Clear Audit

**Action:** `plato sandbox clear-audit`

**Work:**
- Clear all entries from audit log
- Reset mutation counter to 0

**Verify:** `plato sandbox verify audit-clear`

| Check | Pass Criteria | Failure Action |
|-------|---------------|----------------|
| command_succeeds | Exit code 0 | Check worker is running |
| mutations_zero | State shows 0 mutations | Re-run clear-audit |

**Output on failure:**
```
❌ Audit clear verification failed

Current mutation count: 15

The audit log was not cleared properly.

Fix:
  1. Ensure worker is running: plato sandbox verify worker
  2. Re-run: plato sandbox clear-audit
```

---

### Step 3.2: Run Login Flow

**Action:** `plato sandbox flow login`

**Work:**
- Execute login flow from flows.yml
- Automate: navigate, fill credentials, submit

**Verify:** `plato sandbox verify flow`

| Check | Pass Criteria | Failure Action |
|-------|---------------|----------------|
| flow_exists | flows.yml has login flow defined | Create flows.yml |
| flow_completes | All steps execute without error | Fix selectors |
| no_timeout | Completes within timeout | Increase timeout or fix flow |

**Output on failure:**
```
❌ Flow verification failed

Flow execution stopped at step 3:
  Action: click
  Selector: button[type="submit"]
  Error: Element not found (timeout 10s)

Page snapshot shows:
  - Login form visible
  - Submit button has class "btn-login" not type="submit"

Fix flows.yml:
  - selector: button[type="submit"]
  + selector: button.btn-login
```

---

### Step 3.3: Check Mutations

**Action:** `plato sandbox state -v`

**Work:**
- Query state API for mutations
- Analyze mutation types and counts

**Verify:** `plato sandbox verify mutations`

| Check | Pass Criteria | Failure Action |
|-------|---------------|----------------|
| mutation_count | 0 mutations | Analyze and fix audit_ignore |

**Output on success:**
```
✅ Mutation verification passed

Mutations after login: 0
Login is read-only - ready for snapshot.
```

**Output on failure:**
```
❌ Mutation verification failed

Mutations after login: 170

Analysis:
┌─────────────────────────────────┬────────┬────────┬────────┐
│ Table                           │ INSERT │ UPDATE │ DELETE │
├─────────────────────────────────┼────────┼────────┼────────┤
│ common_inventreesetting         │ 85     │ 0      │ 0      │
│ common_inventreeusersetting     │ 45     │ 0      │ 0      │
│ plugin_pluginsetting            │ 40     │ 0      │ 0      │
└─────────────────────────────────┴────────┴────────┴────────┘

Diagnosis:
  All 170 mutations are INSERT operations (new rows created).
  This is lazy initialization - settings created on first access.

  ⚠️  Column-level ignores will NOT work for INSERT operations.
  You must ignore the entire table.

Suggested fix for plato-config.yml:
  audit_ignore_tables:
    # Lazy-init settings tables (INSERT on first login)
    - common_inventreesetting
    - common_inventreeusersetting
    - plugin_pluginsetting

After updating config:
  1. plato sandbox stop-worker
  2. plato sandbox start-worker --wait
  3. plato sandbox clear-audit
  4. plato sandbox flow login
  5. plato sandbox verify mutations
```

**Output for UPDATE mutations:**
```
❌ Mutation verification failed

Mutations after login: 3

Analysis:
┌─────────────────────────────────┬────────┬────────┬────────┐
│ Table                           │ INSERT │ UPDATE │ DELETE │
├─────────────────────────────────┼────────┼────────┼────────┤
│ users                           │ 0      │ 2      │ 0      │
│ auth_sessions                   │ 1      │ 0      │ 0      │
└─────────────────────────────────┴────────┴────────┴────────┘

Column details for UPDATE operations:
  users: last_login (2 updates)

Diagnosis:
  - users.last_login: Timestamp update on login (use column ignore)
  - auth_sessions: Session created (ignore entire table)

Suggested fix for plato-config.yml:
  audit_ignore_tables:
    - auth_sessions                    # Session table - ignore entirely
    - table: users
      columns: [last_login]            # Column ignore works for UPDATE
```

---

### Step 3.4: Verify Audit Works

**Action:** Browser - make a small change in the app

**Work:**
- While logged in, change a setting
- Check that mutations ARE recorded
- Proves audit system is actually working

**Verify:** `plato sandbox verify audit-active`

| Check | Pass Criteria | Failure Action |
|-------|---------------|----------------|
| mutations_appear | State shows 1+ mutations after change | Restart worker, check triggers |

**Output on success:**
```
✅ Audit system verification passed

Before change: 0 mutations
After change: 1 mutation
  - settings: UPDATE {"theme": "light" -> "dark"}

Audit system is correctly tracking changes.
```

**Output on failure:**
```
❌ Audit system verification failed

Before change: 0 mutations
After change: 0 mutations

Issue: No mutations recorded after making a change.
       The audit system is NOT working.
       Previous "0 mutations after login" result is INVALID.

Possible causes:
  1. Audit triggers not installed
  2. Worker monitoring wrong database
  3. Worker not connected

Fix:
  plato sandbox stop-worker
  plato sandbox start-worker --wait
  plato sandbox verify worker
```

---

## Phase 4: Snapshot & Submit

### Step 4.1: Create Snapshot

**Action:** `plato sandbox snapshot`

**Work:**
- Capture current database state
- Create artifact on Plato servers
- Save artifact_id to .sandbox.yaml

**Verify:** `plato sandbox verify snapshot`

| Check | Pass Criteria | Failure Action |
|-------|---------------|----------------|
| command_succeeds | Exit code 0, artifact_id returned | Check worker is running |
| artifact_id_saved | .sandbox.yaml has artifact_id field | Add manually |
| artifact_id_valid | UUID format | Re-run snapshot |

**Output on failure:**
```
❌ Snapshot verification failed

Snapshot command output:
  Error: Worker not connected

Fix:
  1. plato sandbox verify worker
  2. Fix any worker issues
  3. Re-run: plato sandbox snapshot
```

---

### Step 4.2: Review

**Action:** `plato pm review base --skip-review`

**Work:**
- Start session from artifact
- Run login flow
- Check state for mutations
- Verify logged-in state via browser

**Verify:** `plato pm verify review`

| Check | Pass Criteria | Failure Action |
|-------|---------------|----------------|
| session_started | Review session created | Check artifact_id valid |
| login_succeeded | "Logged into environment" shown | Fix flow or credentials |
| state_works | State API returns data | Fix worker |
| no_mutations | 0 mutations after login | Fix audit_ignore |
| browser_logged_in | Dashboard visible (not login page) | Fix flow |

**Output on failure:**
```
❌ Review verification failed

Review results:
  ✅ Session started from artifact
  ✅ Login flow completed
  ❌ State check: 5 mutations detected
  ⚪ Browser check: skipped (state failed)

This means the snapshot has the mutation issue baked in.

Fix:
  1. Return to running sandbox (or start new one)
  2. Fix audit_ignore_tables
  3. Clear audit and re-test login flow
  4. Create new snapshot
  5. Re-run review
```

---

### Step 4.3: Submit

**Action:** `plato pm submit base`

**Work:**
- Submit simulator for human approval
- Sync metadata to server
- Change status to review_requested

**Verify:** `plato pm verify submit`

| Check | Pass Criteria | Failure Action |
|-------|---------------|----------------|
| api_key_set | PLATO_API_KEY env var present | Export the key |
| sandbox_yaml_complete | All required fields present | Add missing fields |
| artifact_id_present | artifact_id in .sandbox.yaml | Run snapshot first |

**Output on failure:**
```
❌ Submit verification failed

Pre-submit checks:
  ❌ PLATO_API_KEY: not set
  ✅ .sandbox.yaml: exists
  ✅ plato_config_path: present
  ✅ service: present
  ✅ artifact_id: present

Fix:
  export PLATO_API_KEY="pk_user_IgNNSJp5v_J0EMJtnxHGw6y68lfdYXiWdXNq1v_JaQQ"
  plato pm submit base
```

**Output on success:**
```
✅ Submit verification passed

All pre-submit checks passed:
  ✅ PLATO_API_KEY: set
  ✅ .sandbox.yaml: complete
  ✅ artifact_id: 4045fafa-7bc8-4193-bdd5-eea1400f9dbb

Ready to submit. Running: plato pm submit base
```

---

## Command Summary

| Phase | Step | Action Command | Verify Command |
|-------|------|----------------|----------------|
| 1 | Research | `sim-research` skill | `plato sandbox verify research` |
| 1 | Validate | `sim-validator` skill | `plato sandbox verify validation` |
| 1 | Config | `sim-config-writer` skill | `plato sandbox verify config` |
| 2 | Start Sandbox | `plato sandbox start -c` | `plato sandbox verify` |
| 2 | Start Services | `plato sandbox start-services` | `plato sandbox verify services` |
| 2 | Manual Login | Browser (Playwright) | `plato sandbox verify login` |
| 2 | Start Worker | `plato sandbox start-worker --wait` | `plato sandbox verify worker` |
| 3 | Clear Audit | `plato sandbox clear-audit` | `plato sandbox verify audit-clear` |
| 3 | Run Flow | `plato sandbox flow login` | `plato sandbox verify flow` |
| 3 | Check Mutations | `plato sandbox state -v` | `plato sandbox verify mutations` |
| 3 | Verify Audit | Browser change | `plato sandbox verify audit-active` |
| 4 | Snapshot | `plato sandbox snapshot` | `plato sandbox verify snapshot` |
| 4 | Review | `plato pm review base --skip-review` | `plato pm verify review` |
| 4 | Submit | `plato pm submit base` | `plato pm verify submit` |

---

## Error Recovery Flows

### Mutation Loop
```
verify mutations FAILED
        │
        ▼
┌───────────────────┐
│ Analyze mutations │
│ (INSERT vs UPDATE)│
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Update config     │
│ audit_ignore_tables│
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ stop-worker       │
│ start-worker      │
│ clear-audit       │
│ flow login        │
└─────────┬─────────┘
          │
          ▼
    verify mutations
```

### Worker Issues Loop
```
verify worker FAILED
        │
        ▼
┌───────────────────┐
│ stop-worker       │
│ start-worker --wait│
└─────────┬─────────┘
          │
          ▼
    verify worker ───FAILED───▶ Check logs via SSH
        │
      PASSED
        │
        ▼
    Continue pipeline
```

### Services Issues Loop
```
verify services FAILED (502)
        │
        ▼
┌───────────────────┐
│ Check app_port    │
│ vs actual port    │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Either:           │
│ - Add nginx proxy │
│ - Change app_port │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ Restart services  │
└─────────┬─────────┘
          │
          ▼
    verify services
```
