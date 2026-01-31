# Sim Creator Guide

This guide documents how to create new Plato simulators from GitHub repositories. It is designed for both human developers and AI agents.

**Related Documentation:**
- [CLI Reference](CLI.md) - All Plato CLI commands
- [Simulator Lifecycle](SIMULATOR_LIFECYCLE.md) - Complete build/iterate workflow
- [Creating Flows](cli/flows.md) - Login flow syntax and examples
- [Sandbox Commands](cli/sandbox.md) - Sandbox command reference

---

## Simulator Naming Rules

**Sim names MUST follow these rules:**
- **Lowercase letters only** (a-z)
- **Underscores allowed** for word separation
- **NO dashes, numbers, or special characters**

| Input | Correct Name |
|-------|--------------|
| Invoice Ninja | `invoiceninja` |
| Twenty CRM | `twenty` |
| DocuSeal | `docuseal` |
| EspoCRM | `espocrm` |
| Cal.com | `calcom` |
| Tasty Igniter | `tastyigniter` |
| Work Lenz | `worklenz` |

**BAD names:** `invoice-ninja`, `twenty-crm`, `docu_seal_1`, `EspoCRM`

---

## Existing Sims

If you're asked to create a sim that already exists, you can:
1. **Iterate on what exists** - Read the existing config files and improve them
2. **Or wipe and restart** - Delete the existing folder and start fresh if the existing setup is broken

---

## Prerequisites

### Supported Databases

**Plato ONLY supports:**
- PostgreSQL (14-17)
- MySQL
- MariaDB

**NOT SUPPORTED - STOP if the app uses:**
- MongoDB
- SQLite
- Redis (as primary data store)
- Cassandra, DynamoDB, CouchDB, or any NoSQL

If the application uses an unsupported database, the sim cannot be created.

### Required Tools

```bash
# Plato CLI
pip install plato-sdk-v2

# Set API key
export PLATO_API_KEY=pk_user_xxx
```

---

## Workflow Overview

```
1. Research App        → Gather info from GitHub
2. Validate Database   → STOP if unsupported
3. Create Files        → docker-compose.yml, plato-config.yml, flows
4. Start Sandbox       → plato sandbox start --from-config
5. Start Services      → plato sandbox start-services
6. Start Worker        → plato sandbox start-worker
7. Wait & Verify       → Wait 3 min, check state
8. Test Login          → plato sandbox flow
9. Snapshot            → plato sandbox snapshot
10. Self-Review        → Start from artifact, verify login
11. Submit             → plato pm submit base
```

---

## Phase 1: Research the Application

### Information to Gather

| Question | How to Find |
|----------|-------------|
| Database type | Check docker-compose, README, or docs |
| Docker image | Docker Hub, GitHub Container Registry |
| Image version tag | Docker Hub tags page, GitHub releases |
| Web UI port | docker-compose, docs |
| Login URL path | Usually /login, /admin, /signin |
| Default credentials | docs, docker-compose env vars |
| Required env vars | docker-compose examples |

### Research Steps

1. **Read GitHub README** - Understand what the app does
2. **Find Docker setup** - Check for docker-compose.yml in repo
3. **Find Docker image** - Check Docker Hub for official images
4. **Get version tag** - Look at Docker Hub tags, use specific version (NOT `latest` or `stable`)
5. **Find credentials** - Check docs or docker-compose for defaults
6. **Find login page** - Usually documented or can infer from app type

---

## Phase 2: Validate Database

**CRITICAL CHECK**: If the app uses MongoDB, SQLite, Redis, or any NoSQL database, STOP.

```
FAILED: Cannot create simulator.
Reason: Application uses {database_type}, which is not supported.
Plato only supports: PostgreSQL, MySQL, MariaDB
```

---

## Phase 3: Create Files

### Directory Structure

```
{simName}/
├── plato-config.yml
├── base/
│   ├── docker-compose.yml
│   └── login-flow.yml
└── flows/
    └── flows.yaml       # Alternative location
```

### 3.1 docker-compose.yml (PostgreSQL)

```yaml
services:
  db:
    container_name: {simName}-db
    platform: linux/amd64
    image: public.ecr.aws/i3q4i1d7/app-sim/postgres-15-alpine:prod-latest
    network_mode: host
    command: ["postgres", "-c", "listen_addresses=127.0.0.1"]
    environment:
      POSTGRES_DB: {simName}
      POSTGRES_USER: {simName}
      POSTGRES_PASSWORD: {simName}
    volumes:
      - /home/plato/db_signals:/tmp/postgres-signals
    healthcheck:
      test: ["CMD-SHELL", "test -f /tmp/postgres-signals/pg.healthy"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  app:
    container_name: {simName}-app
    platform: linux/amd64
    image: {dockerImage}:{versionTag}  # MUST use version tag, NOT 'latest'
    network_mode: host
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://{simName}:{simName}@127.0.0.1:5432/{simName}
      # Add app-specific env vars
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://127.0.0.1:{appPort}/ || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 10
      start_period: 120s
```

### 3.2 docker-compose.yml (MySQL/MariaDB)

```yaml
services:
  db:
    container_name: {simName}-db
    platform: linux/amd64
    image: public.ecr.aws/i3q4i1d7/app-sim/mariadb-10.6:prod-latest
    network_mode: host
    environment:
      MYSQL_DATABASE: {simName}
      MYSQL_USER: {simName}
      MYSQL_PASSWORD: {simName}
      MYSQL_ROOT_PASSWORD: {simName}
    volumes:
      - /home/plato/db_signals:/tmp/mysql-signals
    healthcheck:
      test: ["CMD-SHELL", "test -f /tmp/mysql-signals/mysql.healthy"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  app:
    container_name: {simName}-app
    platform: linux/amd64
    image: {dockerImage}:{versionTag}
    network_mode: host
    depends_on:
      db:
        condition: service_healthy
    environment:
      DB_HOST: 127.0.0.1
      DB_PORT: 3306
      DB_DATABASE: {simName}
      DB_USERNAME: {simName}
      DB_PASSWORD: {simName}
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://127.0.0.1:{appPort}/ || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 10
      start_period: 120s
```

### Plato Database Images (REQUIRED)

| Database | Image |
|----------|-------|
| PostgreSQL 15 | `public.ecr.aws/i3q4i1d7/app-sim/postgres-15-alpine:prod-latest` |
| PostgreSQL 17 | `public.ecr.aws/i3q4i1d7/app-sim/postgres-17-alpine:prod-latest` |
| MariaDB 10.6 | `public.ecr.aws/i3q4i1d7/app-sim/mariadb-10.6:prod-latest` |

**You MUST use these images** - standard postgres/mysql images won't work with Plato's signal-based health checks.

### 3.3 Apps on Non-80 Ports (Nginx Proxy)

If the app doesn't serve on port 80, add nginx:

```yaml
  proxy:
    container_name: {simName}-proxy
    image: nginx:alpine
    network_mode: host
    depends_on:
      app:
        condition: service_healthy
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://127.0.0.1:80/ || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5
```

Create `base/nginx.conf`:
```nginx
server {
    listen 80;
    location / {
        proxy_pass http://127.0.0.1:{appPort};
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Important**: When using nginx proxy, set `required_healthy_containers` to the proxy container name.

### 3.4 plato-config.yml

```yaml
service: "{simName}"
datasets:
  base:
    compute:
      cpus: 2
      memory: 2048
      disk: 10240
      app_port: 80
      plato_messaging_port: 7000
    metadata:
      name: "{Human Readable Name}"
      description: "{Description from GitHub}"
      source_code_url: "{githubUrl}"
      start_url: /
      license: "MIT"
      variables:
        - name: username
          value: {defaultUsername}
        - name: password
          value: {defaultPassword}
        - name: wrong_password
          value: wrongpassword
      flows_path: base/login-flow.yml
    services:
      main_app:
        type: docker-compose
        file: base/docker-compose.yml
        healthy_wait_timeout: 600
        required_healthy_containers:
          - {simName}-app  # MUST match container_name exactly
    listeners:
      db:
        type: db
        db_type: postgresql  # or mysql
        db_host: 127.0.0.1
        db_port: 5432  # or 3306
        db_user: {simName}
        db_password: {simName}
        db_database: {simName}
        volumes:
          - /home/plato/db_signals:/tmp/postgres-signals
        audit_ignore_tables:
          - migrations
          - _prisma_migrations
          - failed_jobs
          - sessions
          - jobs
        ignore_columns:
          '*': [created_at, updated_at, deleted_at, last_login]
```

### 3.5 Login Flow (base/login-flow.yml)

See [Creating Flows](cli/flows.md) for complete step type reference.

```yaml
flows:
  - name: login
    description: Standard login flow for {simName}
    steps:
      - type: screenshot
        filename: 01_before_login.png
        description: Initial page state

      - type: wait
        duration: 3000
        description: Wait for page to load

      - type: wait_for_selector
        selector: 'input[name="email"], input[type="email"], input[name="username"], #email, #username'
        timeout: 30000
        description: Wait for username field

      - type: fill
        selector: 'input[name="email"], input[type="email"], input[name="username"], #email, #username'
        value: {defaultUsername}
        description: Fill username

      - type: fill
        selector: 'input[name="password"], input[type="password"], #password'
        value: {defaultPassword}
        description: Fill password

      - type: screenshot
        filename: 02_credentials_entered.png
        description: After entering credentials

      - type: click
        selector: 'button[type="submit"], input[type="submit"]'
        description: Click submit

      - type: wait
        duration: 5000
        description: Wait for login to process

      - type: screenshot
        filename: 03_after_login.png
        description: After login attempt

      # Verify success by looking for dashboard elements
      - type: verify
        verify_type: element_exists
        selector: 'nav, .navbar, .sidebar, .dashboard, .user-menu, text=Dashboard'
        description: Verify logged in
```

**Important**: Avoid using `verify_no_errors` with generic selectors like `[role="alert"]` which can match non-error UI elements. Instead, verify success by checking for dashboard elements.

### Flow Step Types Reference

| Type | Required Fields | Description |
|------|-----------------|-------------|
| `navigate` | `url` | Navigate to URL |
| `fill` | `selector`, `value` | Fill input field |
| `click` | `selector` | Click element |
| `wait` | `duration` | Wait milliseconds |
| `wait_for_selector` | `selector`, `timeout` | Wait for element |
| `screenshot` | `filename` | Take screenshot |
| `verify` | `verify_type`, `selector` | Verify element exists |
| `verify_text` | `text`, `should_exist` | Verify text appears/doesn't appear |
| `verify_url` | `url`, `contains` | Verify current URL |
| `check_element` | `selector`, `should_exist` | Check if element exists (non-blocking) |

---

## Phase 4: Start Sandbox and Services

### Step 1: Start Sandbox

```bash
cd /path/to/{simName}
plato sandbox start --from-config
```

Note the output:
- SSH config path: `~/.plato/ssh_XX.conf`
- Job ID from URL

### Step 2: Start Services

```bash
plato sandbox start-services
```

This command:
1. Pushes code to Plato Hub (Gitea)
2. Clones code on the VM
3. Runs `docker compose up -d`

### Step 3: Start Worker

```bash
plato sandbox start-worker
```

### Step 4: Wait and Verify

**Wait approximately 3 minutes** for the worker to initialize.

```bash
# Check state
plato sandbox state

# Check containers via SSH
ssh -F ~/.plato/ssh_XX.conf sandbox-XX "docker ps"

# Check sandbox status
plato sandbox status
```

---

## Phase 5: Test Login Flow

### Initial Setup vs Login Flow

**IMPORTANT**: Many apps require initial setup (creating admin account, configuring settings, etc.) before login will work. This setup should NOT be in the login flow.

**Flows should ONLY do login** - nothing else. No setup, no onboarding, no configuration.

If the app needs initial setup:
1. Start the sandbox and get it running
2. Open the public URL (from `plato sandbox status`) in your browser
3. Complete the initial setup manually:
   - Create the admin account
   - Configure any required settings
   - Complete the onboarding wizard
4. After setup is complete, THEN test the login flow
5. The login flow should use the credentials created during setup

**Example apps requiring manual setup:**
- Apps with "first run" wizards
- Apps that create admin account on first visit
- Apps requiring license key or initial configuration

### Running the Flow

```bash
plato sandbox flow --flow-name login
```

This opens a browser and executes the flow. Watch for:
- Fields being filled correctly
- Submit button click
- Successful navigation to dashboard

### Debugging Login Failures

1. **Check screenshots** in the `screenshots/` directory
2. **Update selectors** - Use browser DevTools to find correct selectors
3. **Add wait steps** - The page may need more time to load
4. **Check containers** - Verify app is running: `docker logs {container}`

---

## Phase 6: Create Snapshot

When login works:

```bash
plato sandbox snapshot
```

Save the artifact ID from the output (e.g., `art_abc123`).

**Important**: Create snapshots immediately after verifying login. Sandboxes can timeout.

---

## Phase 7: Self-Review

Before submitting, verify the artifact works:

```bash
# Stop current sandbox
plato sandbox stop

# Start fresh from artifact
plato sandbox start --artifact-id art_abc123

# Test login on the artifact
plato sandbox flow --flow-name login
```

If login fails on the artifact:
1. Stop sandbox
2. Start from config: `plato sandbox start --from-config`
3. Fix issues
4. Re-snapshot
5. Re-test

### Review Checklist (5 Verification Points)

Before submitting for review, verify ALL of the following:

#### 1. Flow Executes Successfully

```bash
plato sandbox flow --flow-name login
```

The flow should complete without errors. If it fails:
- Check screenshots in the output directory
- Update selectors if elements changed
- Add wait steps if timing issues

#### 2. Flow Has Post-Login Verification

Your login flow MUST verify that login actually succeeded by checking for elements that only appear after authentication:

```yaml
# GOOD - Verifies dashboard elements exist after login
- type: verify
  verify_type: element_exists
  selector: 'nav, .navbar, .sidebar, .dashboard, .user-menu, [data-testid="user-avatar"]'
  description: Verify logged in by checking for dashboard elements

# BAD - No verification, just screenshots
- type: screenshot
  filename: 03_after_login.png
  # Missing verification step!
```

#### 3. State Shows No Mutations After Login

After running the login flow, check that no database mutations occurred:

```bash
plato sandbox state
```

**Expected output**: Empty mutations or only ignored tables/columns.

If you see mutations after login:
- Add the table to `audit_ignore_tables` if it's a session/log table
- Add the column to `ignore_columns` if it's a timestamp like `last_login`

#### 4. Audit Ignores Are Configured Correctly

Review your `plato-config.yml` audit configuration:

```yaml
listeners:
  db:
    audit_ignore_tables:
      - migrations        # OK - schema migrations
      - _prisma_migrations # OK - ORM migrations
      - sessions          # OK - session storage
      - jobs              # OK - background jobs
      - failed_jobs       # OK - job failures
      - cache             # OK - cache storage
      - audit_log         # OK - audit logging
    ignore_columns:
      '*': [created_at, updated_at, deleted_at, last_login, last_seen]
```

**Safe to ignore:**
- Migration tables (`migrations`, `_prisma_migrations`, `schema_migrations`)
- Session tables (`sessions`, `user_sessions`)
- Job/queue tables (`jobs`, `failed_jobs`, `queue`)
- Cache tables (`cache`, `cache_locks`)
- Timestamp columns (`created_at`, `updated_at`, `last_login`, `last_seen`)

**NOT safe to ignore:**
- User data tables (`users`, `accounts`, `profiles`)
- Business data tables (orders, products, invoices, etc.)
- Configuration tables (`settings`, `options`)

#### 5. Real Modifications DO Show in State (Audit Works)

This is **critical** - you must verify the audit system is actually capturing changes:

```bash
# 1. Run login flow
plato sandbox flow --flow-name login

# 2. Check state is clean (no mutations)
plato sandbox state

# 3. Manually make a change via the UI
#    - Go to the public URL shown in `plato sandbox status`
#    - Log in manually
#    - Create/edit/delete something (e.g., create a new contact, update a setting)

# 4. Check state again - should now show mutations!
plato sandbox state
```

If no mutations appear after making a real change:
- The audit system may not be configured correctly
- Check that `db_type` matches your database
- Verify `db_host`, `db_port`, `db_user`, `db_password` are correct
- Ensure the volumes mapping for signals is correct

**Summary: Self-Review Must Pass ALL 5 Checks**

| Check | Command | Expected Result |
|-------|---------|-----------------|
| 1. Flow succeeds | `plato sandbox flow` | Completes without errors |
| 2. Has verification | Review flow YAML | Has `verify` step for post-login elements |
| 3. No mutations after login | `plato sandbox state` | Empty or only ignored tables |
| 4. Audit ignores correct | Review config | Only timestamps/sessions/migrations ignored |
| 5. Real changes detected | Manual test + `state` | Shows mutations after UI change |

---

## Phase 8: Submit for Review

Once self-review passes:

```bash
plato pm submit base
```

This transitions the simulator status to `env_review_requested`.

---

## Common Pitfalls & Solutions

### 1. Using `latest` or `stable` Image Tags

**Problem**: Generic tags cause unpredictable behavior, missing assets, or broken builds.

**Solution**: Always use specific version tags:
```yaml
# BAD
image: myapp/myapp:latest
image: myapp/myapp:stable

# GOOD
image: myapp/myapp:1.2.3
image: myapp/myapp:v2.5.0
```

Check Docker Hub or GitHub releases for version tags.

### 2. Container Name Mismatch

**Problem**: `required_healthy_containers` doesn't match actual container names.

**Solution**: Always set explicit `container_name` and use it exactly:
```yaml
# docker-compose.yml
services:
  app:
    container_name: myapp-app  # Explicit name

# plato-config.yml
required_healthy_containers:
  - myapp-app  # Must match exactly
```

### 3. Using Standard Database Images

**Problem**: Standard postgres/mysql images don't work with Plato's health checks.

**Solution**: Use Plato database images:
```yaml
# BAD
image: postgres:15

# GOOD
image: public.ecr.aws/i3q4i1d7/app-sim/postgres-15-alpine:prod-latest
```

### 4. Network Mode Issues

**Problem**: Containers can't communicate.

**Solution**: All containers must use `network_mode: host`:
```yaml
services:
  db:
    network_mode: host
  app:
    network_mode: host
```

Use `127.0.0.1` for inter-container communication, not container names.

### 5. Generic Error Selectors in Flows

**Problem**: `[role="alert"]` or `.alert` matches non-error UI elements.

**Solution**: Verify success by looking for dashboard elements:
```yaml
# BAD
- type: verify_no_errors
  error_selectors:
    - '[role="alert"]'

# GOOD
- type: verify
  verify_type: element_exists
  selector: 'nav, .dashboard, .user-menu'
```

### 6. Apps Needing Nginx Proxy

**Problem**: App runs on port 3000 but Plato expects port 80.

**Solution**: Add nginx proxy and update `required_healthy_containers`:
```yaml
services:
  proxy:
    container_name: myapp-proxy
    image: nginx:alpine
    # ...

# plato-config.yml - use proxy container
required_healthy_containers:
  - myapp-proxy
```

### 7. Sandbox Timeout

**Problem**: SSH returns 502 or "VM shutdown due to heartbeat miss".

**Solution**: Sandboxes timeout after inactivity. Create snapshots immediately after verifying login works. If timeout occurs, start fresh: `plato sandbox stop && plato sandbox start --from-config`

### 8. Healthcheck Fails

**Problem**: Container healthcheck keeps failing.

**Solution**: Increase `start_period` and `retries`:
```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://127.0.0.1:3000/ || exit 1"]
  interval: 30s
  timeout: 10s
  retries: 15        # Increase retries
  start_period: 180s # Increase start period
```

### 9. Database Connection Refused

**Problem**: App can't connect to database.

**Solution**: Ensure db healthcheck passes before app starts:
```yaml
app:
  depends_on:
    db:
      condition: service_healthy
```

And use `127.0.0.1` not `localhost` or container name.

### 10. Missing Environment Variables

**Problem**: App fails to start due to missing config.

**Solution**: Check the app's documentation for required env vars. Common ones:
```yaml
environment:
  SECRET_KEY: supersecretkey
  APP_URL: http://127.0.0.1
  TRUSTED_PROXIES: "*"
  SESSION_DRIVER: database
```

### 11. Plato CLI Authentication Errors

**Problem**: Getting 401, 403, "unauthorized", or "invalid token" errors from Plato CLI.

**Solution**: Your API key may be missing or invalid. Set it:
```bash
export PLATO_API_KEY=pk_user_xxx
```

You can find your API key at: https://plato.so/settings/api-keys

---

## Quick Reference

### CLI Commands

| Command | Description |
|---------|-------------|
| `plato sandbox start --from-config` | Start sandbox from plato-config.yml |
| `plato sandbox start-services` | Sync code and start docker compose |
| `plato sandbox start-worker` | Start Plato worker |
| `plato sandbox state` | Get environment state |
| `plato sandbox status` | Check sandbox status |
| `plato sandbox flow` | Run login flow |
| `plato sandbox snapshot` | Create artifact |
| `plato sandbox stop` | Stop sandbox |
| `plato pm submit base` | Submit for review |

### Correct Workflow Sequence

```bash
# Initial development
plato sandbox start --from-config
plato sandbox start-services
plato sandbox start-worker
# Wait ~3 minutes
plato sandbox state
plato sandbox flow

# Iterate (after changes)
plato sandbox start-services
plato sandbox start-worker
# Wait ~3 minutes
plato sandbox flow

# When ready
plato sandbox snapshot

# Self-review
plato sandbox stop
plato sandbox start --artifact-id <id>
plato sandbox flow

# Submit
plato pm submit base
```

---

## Production Examples

These are working examples from production simulators.

### Example 1: DocuSeal (PostgreSQL + Nginx Proxy)

**plato-config.yml:**
```yaml
service: docuseal
datasets:
  base:
    compute:
      cpus: 1
      memory: 2048
      disk: 10240
      app_port: 80
      plato_messaging_port: 7000
    metadata:
      name: docuseal
      description: Open source document signing and form filling platform
      source_code_url: https://github.com/docusealco/docuseal
      start_url: blank
      license: AGPLv3
      variables:
        - name: username
          value: admin@admin.com
        - name: password
          value: password
        - name: wrong_password
          value: wrongpassword
      flows_path: base/flow.yml
    services:
      main_app:
        type: docker-compose
        file: base/docker-compose.yml
        healthy_wait_timeout: 600
        required_healthy_containers:
          - app
          - nginx
    listeners:
      db:
        type: db
        db_type: postgresql
        db_host: 127.0.0.1
        db_port: 5432
        db_user: docuseal
        db_password: docuseal
        db_database: docuseal
        volumes:
          - /home/plato/db_signals:/tmp/postgres-signals
        audit_ignore_tables:
          - ar_internal_metadata
          - schema_migrations
          - webhook_attempts
          - access_tokens
          - oauth_access_grants
          - oauth_access_tokens
          - table: "*"
            columns: [updated_at]
          - table: "users"
            columns: [current_sign_in_at, updated_at, sign_in_count, last_sign_in_at, last_sign_in_ip, current_sign_in_ip]
```

**docker-compose.yml:**
```yaml
services:
  db:
    image: public.ecr.aws/i3q4i1d7/app-sim/postgres-15-alpine:prod-latest
    network_mode: host
    environment:
      POSTGRES_DB: docuseal
      POSTGRES_USER: docuseal
      POSTGRES_PASSWORD: docuseal
    volumes:
      - /home/plato/db_signals:/tmp/postgres-signals
    healthcheck:
      test: ["CMD-SHELL", "test -f /tmp/postgres-signals/pg.healthy"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 20s

  app:
    depends_on:
      db:
        condition: service_healthy
    image: docuseal/docuseal:1.8.9
    network_mode: host
    environment:
      - FORCE_SSL=true
      - DATABASE_URL=postgresql://docuseal:docuseal@127.0.0.1:5432/docuseal

  nginx:
    image: nginx:alpine
    network_mode: host
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - app
```

### Example 2: InvoiceNinja (MariaDB + Redis + Custom Nginx)

**docker-compose.yml:**
```yaml
services:
  db:
    image: public.ecr.aws/i3q4i1d7/app-sim/mariadb-10.6:prod-latest
    network_mode: host
    environment:
      MYSQL_DATABASE: ninja
      MYSQL_USER: ninja
      MYSQL_PASSWORD: ninja
      MYSQL_ROOT_PASSWORD: ninjaAdm1nPassword
    command:
      - --character-set-server=utf8mb4
      - --collation-server=utf8mb4_unicode_ci
    volumes:
      - mysql-signals:/tmp/mysql-signals
    healthcheck:
      test: ["CMD-SHELL", "test -f /tmp/mysql-signals/mysql.healthy"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  redis:
    image: redis:7-alpine
    network_mode: host
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  invoiceninja:
    image: invoiceninja/invoiceninja:5.10.29
    network_mode: host
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      APP_URL: https://sims.plato.so
      APP_KEY: base64:OwWRRZ2Bl/dmHUrbyWIP7LQd5mTuTdbhd8RKgg0xsBM=
      TRUSTED_PROXIES: "*"
      CACHE_DRIVER: redis
      QUEUE_CONNECTION: redis
      SESSION_DRIVER: redis
      REDIS_HOST: 127.0.0.1
      DB_CONNECTION: mysql
      DB_HOST: 127.0.0.1
      DB_PORT: "3306"
      DB_DATABASE: ninja
      DB_USERNAME: ninja
      DB_PASSWORD: ninja
      IN_USER_EMAIL: admin@example.com
      IN_PASSWORD: changeme!

  invoiceninja-nginx:
    container_name: invoiceninja-nginx
    image: nginx:alpine
    network_mode: host
    depends_on:
      invoiceninja:
        condition: service_started
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://127.0.0.1:8080/health"]
      interval: 60s
      timeout: 10s
      retries: 10
      start_period: 60s

volumes:
  mysql-signals:
    name: mysql-signals
```

### Example 3: Twenty CRM (PostgreSQL + Redis + Worker)

**docker-compose.yml:**
```yaml
services:
  twenty-db:
    image: public.ecr.aws/i3q4i1d7/app-sim/postgres-16-alpine:prod-latest
    network_mode: host
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: mysecurepass123
    volumes:
      - postgres-signals:/tmp/postgres-signals
    healthcheck:
      test: ["CMD-SHELL", "test -f /tmp/postgres-signals/pg.healthy"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 5s

  twenty-redis:
    image: redis:7-alpine
    network_mode: host
    command:
      - --maxmemory-policy
      - noeviction

  twenty-server:
    image: twentycrm/twenty:0.32.0
    network_mode: host
    depends_on:
      twenty-db:
        condition: service_healthy
      twenty-redis:
        condition: service_started
    environment:
      NODE_PORT: 3000
      PG_DATABASE_URL: postgres://postgres:mysecurepass123@localhost:5432/default
      SERVER_URL: https://twenty.com
      REDIS_URL: redis://127.0.0.1:6379
      APP_SECRET: twenty
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:3000/healthz || exit 1"]
      interval: 5s
      timeout: 5s
      retries: 9
      start_period: 10s

  twenty-worker:
    image: twentycrm/twenty:0.32.0
    network_mode: host
    depends_on:
      twenty-server:
        condition: service_healthy
    command: ["yarn", "worker:prod"]
    environment:
      PG_DATABASE_URL: postgres://postgres:mysecurepass123@127.0.0.1:5432/default
      REDIS_URL: redis://127.0.0.1:6379
      APP_SECRET: twenty

volumes:
  postgres-signals:
    name: postgres-signals
```

### Example 4: Login Flow (DocuSeal)

**flow.yml:**
```yaml
flows:
- name: login
  description: Standard login flow for DocuSeal
  steps:
  - type: screenshot
    filename: 01_before_login.png
    description: Screenshot before login

  - type: wait
    duration: 5000
    description: Wait for page to fully load

  - type: click
    selector: 'a[href*="sign_in"], a:has-text("Sign In")'
    description: Click Sign In button

  - type: wait
    duration: 3000
    description: Wait for login form

  - type: wait_for_selector
    selector: 'input[type="email"], input[name="email"]'
    timeout: 15000
    description: Wait for email field

  - type: fill
    selector: 'input[type="email"], input[name="email"]'
    value: admin@admin.com
    description: Fill email field

  - type: fill
    selector: 'input[type="password"], input[name="password"]'
    value: password
    description: Fill password field

  - type: screenshot
    filename: 02_credentials_entered.png
    description: Screenshot credentials entered

  - type: click
    selector: 'button[type="submit"], input[type="submit"]'
    description: Click submit

  - type: wait
    duration: 5000
    description: Wait for login to process

  - type: screenshot
    filename: 03_after_login.png
    description: Screenshot after login

  - type: verify
    verify_type: element_exists
    selector: 'h1:has-text("Document Templates"), button:has-text("CREATE"), a:has-text("Settings")'
    description: Verify DocuSeal dashboard elements are present
```

---

## Checklist

### Pre-flight
- [ ] Sim name follows rules (lowercase letters and underscores only)
- [ ] Database is PostgreSQL, MySQL, or MariaDB (NOT MongoDB/SQLite/Redis)
- [ ] Found specific version tag for app Docker image

### Docker Setup
- [ ] Using Plato database images (not standard postgres/mysql)
- [ ] All containers use `network_mode: host`
- [ ] All containers have explicit `container_name`
- [ ] Health checks use signal files for DB
- [ ] App image uses version tag (not `latest`/`stable`)

### Configuration
- [ ] `required_healthy_containers` matches container names exactly
- [ ] `app_port` is 80 (use nginx proxy if app runs on different port)
- [ ] Login credentials in `metadata.variables`
- [ ] `flows_path` points to login flow file

### Testing
- [ ] `plato sandbox start --from-config` succeeds
- [ ] `plato sandbox start-services` succeeds
- [ ] `plato sandbox start-worker` succeeds
- [ ] Waited ~3 minutes after start-worker
- [ ] `plato sandbox state` shows ready
- [ ] `plato sandbox flow` login succeeds
- [ ] `plato sandbox snapshot` creates artifact

### Self-Review (5 Verification Points)
- [ ] Started fresh from artifact: `plato sandbox start --artifact-id <id>`
- [ ] **Check 1**: Login flow executes successfully
- [ ] **Check 2**: Flow has `verify` step for post-login elements (not just screenshots)
- [ ] **Check 3**: `plato sandbox state` shows no mutations after login
- [ ] **Check 4**: Audit ignores only timestamps/sessions/migrations (not business data)
- [ ] **Check 5**: Making a real UI change DOES show mutations in `state`
- [ ] Ready to submit: `plato pm submit base`
