# Simulator Lifecycle Guide

This guide explains the complete workflow for building, testing, and iterating on Plato simulators.

## Overview

A simulator goes through several phases:

```
1. Setup        → Create repository and configuration
2. Development  → Build base environment in sandbox
3. Base Review  → Submit and get approval for environment
4. Data Layer   → Add realistic data to the environment
5. Data Review  → Submit and get approval for data
6. Production   → Publish and maintain the simulator
```

## Phase 1: Setup

### Clone or Create Repository

```bash
# Clone existing simulator
plato clone mysim
cd mysim

# Or create new directory
mkdir mysim && cd mysim
```

### Create plato-config.yml

```yaml
service: mysim
target: mysim.web.plato.so

datasets:
  base:
    compute:
      cpus: 2
      memory: 2048
      disk: 10240
      app_port: 80
      plato_messaging_port: 7000
    metadata:
      name: My Simulator
      description: A simulator for MyApp
      start_url: /
      flows_path: flows/flows.yaml
    services:
      web:
        type: docker-compose
        file: docker-compose.yml
    listeners:
      - name: web
        port: 80
```

### Create Docker Compose

```yaml
# docker-compose.yml
version: '3.8'
services:
  web:
    image: myapp:1.2.3  # Use version tags, not 'latest'
    network_mode: host
    container_name: mysim-web
    environment:
      - DATABASE_URL=postgresql://user:pass@localhost:5432/db
```

### Create Login Flow

Create a flow file that defines how to log into your application. See the [Flows Guide](cli/flows.md) for complete documentation on available step types.

```yaml
# flows/flows.yaml
flows:
  - name: login
    description: Standard login flow for MyApp
    steps:
      - type: screenshot
        filename: 01_before_login.png
        description: Initial page state

      - type: wait
        duration: 2000
        description: Wait for page to load

      - type: navigate
        url: /login

      - type: fill
        selector: "#email"
        value: "admin@example.com"

      - type: fill
        selector: "#password"
        value: "password123"

      - type: click
        selector: "button[type='submit']"

      - type: wait
        duration: 3000
        description: Wait for login to process

      - type: verify_no_errors
        description: Verify no error messages

      - type: screenshot
        filename: 02_logged_in.png
        description: After successful login
```

Reference the flow file in `plato-config.yml`:

```yaml
datasets:
  base:
    metadata:
      flows_path: flows/flows.yaml
```

## Phase 2: Development (Base Environment)

### Step 1: Start Sandbox

```bash
# Start sandbox from your config
plato sandbox start --from-config

# Check status (note the SSH command for later)
plato sandbox status
```

### Step 2: Start Services

This command syncs your local code to the VM AND starts docker compose:

```bash
plato sandbox start-services
```

This does:
1. Pushes code to Plato Hub (Gitea)
2. Clones code on the VM
3. Runs `docker compose up -d` for services defined in plato-config.yml

### Step 3: Start Worker

```bash
plato sandbox start-worker
```

### Step 4: Wait and Verify

The worker takes time to initialize. Wait approximately 3 minutes, then verify:

```bash
# Check environment state
plato sandbox state

# Verify containers are running (via SSH)
ssh -F ~/.plato/ssh_xxx.conf sandbox-xxx "docker ps"
```

### Step 5: Test Login Flow

```bash
plato sandbox flow --flow-name login
```

### Iterate

If you need to make changes:

```bash
# 1. Make local code changes

# 2. Re-run start-services (syncs code + restarts docker compose)
plato sandbox start-services

# 3. Re-run start-worker
plato sandbox start-worker

# 4. Wait ~3 minutes, then test again
plato sandbox flow
```

**Note:** Use `start-services` for iteration, not `sync` alone. `start-services` both syncs your code AND restarts the docker compose services.

### Step 6: Create Snapshot

When the environment works correctly:

```bash
# Create snapshot immediately after verifying login works
# (sandboxes can timeout, so don't wait)
plato sandbox snapshot
```

Save the artifact ID from the output (e.g., `art_abc123`).

### Step 7: Self-Review (Verify Artifact)

Before submitting for review, verify the artifact works:

```bash
# Stop current sandbox
plato sandbox stop

# Start fresh from your artifact
plato sandbox start --artifact-id art_abc123

# Test login on the artifact
plato sandbox flow --flow-name login
```

If login fails, go back to development:
```bash
plato sandbox stop
plato sandbox start --from-config
# Fix issues, re-snapshot, re-test
```

## Phase 3: Base Review

### Submit for Review

Once self-review passes:

```bash
plato pm submit base
```

### Check Review Status

```bash
plato pm list base
```

### Handle Review Feedback

**If Rejected:**
1. Read reviewer comments
2. Fix issues
3. Create new snapshot
4. Resubmit

```bash
# Start from your artifact to continue work
plato sandbox start --artifact-id art_xxx

# Make fixes, test, snapshot
plato sandbox flow
plato sandbox snapshot
plato pm submit base
```

**If Approved:**
- Artifact is tagged as `prod-latest`
- Move to data layer phase

## Phase 4: Data Layer

### Start from Approved Base

```bash
plato sandbox start --simulator mysim:prod-latest
```

### Generate/Seed Data

Options:
1. **Manual seeding** - Use the app UI to create data
2. **API seeding** - Use the generated SDK to create data programmatically
3. **Database seeding** - Run SQL scripts via SSH

Example API seeding:

```python
from plato.sims import mysim

client = await mysim.AsyncClient.create(base_url=url)

# Create sample data
await client.httpx.post("/api/users", json={
    "name": "Test User",
    "email": "test@example.com"
})
```

### Create Data Snapshot

```bash
plato sandbox snapshot
```

## Phase 5: Data Review

### Submit for Review

```bash
plato pm submit data --simulator mysim --artifact art_xxx
```

### Reviewer Process

```bash
# Reviewer lists pending
plato pm list data

# Reviewer tests with EnvGen Recorder
plato pm review data -s mysim
```

### Handle Feedback

Same process as base review - fix issues, re-snapshot, resubmit.

## Phase 6: Production

### Access Production Simulator

```bash
# Start from production artifact
plato sandbox start --simulator mysim:prod-latest

# Or use in code
from plato.v2 import AsyncPlato, Env

plato = AsyncPlato()
session = await plato.sessions.create(
    envs=[Env.simulator("mysim:prod-latest")]
)
```

### Publish SDK

If your simulator has an OpenAPI spec:

```bash
plato sims publish
```

### Maintenance

For updates:
1. Clone repo: `plato clone mysim`
2. Start sandbox: `plato sandbox start --from-config`
3. Start services: `plato sandbox start-services`
4. Start worker: `plato sandbox start-worker`
5. Wait ~3 min, then test: `plato sandbox flow`
6. Snapshot: `plato sandbox snapshot`
7. Self-review: `plato sandbox start --artifact-id <id>` then `plato sandbox flow`
8. Submit: `plato pm submit base` (or data)

## Quick Reference Commands

### Development Cycle

```bash
# Initial setup
plato sandbox start --from-config
plato sandbox start-services
plato sandbox start-worker
# Wait ~3 minutes
plato sandbox state
plato sandbox flow

# Iterate (after making local changes)
plato sandbox start-services
plato sandbox start-worker
# Wait ~3 minutes
plato sandbox flow

# When ready, snapshot
plato sandbox snapshot

# Self-review before submitting
plato sandbox stop
plato sandbox start --artifact-id <artifact_id>
plato sandbox flow  # Verify login works on artifact

# Submit for review
plato pm submit base

# Clean up
plato sandbox stop
```

### Testing Published Artifacts

```bash
plato sandbox start --simulator name:prod-latest
plato sandbox flow
plato sandbox status
plato sandbox stop
```

### Review Workflow

```bash
# Worker: After snapshot, self-review, then submit
plato pm submit base          # After self-review passes
plato pm submit data -s name -a artifact_id

# Reviewer
plato pm list base            # See pending
plato pm review base -s name  # Test and approve/reject
plato pm review data -s name  # Test data layer
```

## Troubleshooting

### VM Died Due to Heartbeat Miss

The sandbox timed out. Start fresh:
```bash
plato sandbox stop
plato sandbox start --from-config  # or --simulator
```

### Docker Compose Not Starting

```bash
docker compose up -d
```

### Login Flow Failing

1. Check URL in `.sandbox.yaml` has correct `_plato_router_target`
2. Verify containers are running: `docker ps`
3. Check flow selectors match current UI

### Sync Not Working

1. Check SSH connection: `ssh -F ~/.plato/ssh_xxx.conf sandbox-xxx`
2. Verify remote path exists
3. Check for excluded patterns in sync

## See Also

- [CLI Reference](CLI.md) - Full CLI documentation
- [Sandbox Commands](cli/sandbox.md) - Detailed sandbox command reference
- [PM Commands](cli/pm.md) - Project management commands
- [Generating SDKs](GENERATING_SIM_SDKS.md) - SDK generation guide
