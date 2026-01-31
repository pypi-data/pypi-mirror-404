# Plato Simulator Creation Architecture

## Overview

This document describes the complete architecture for creating Plato simulators from GitHub repositories. The system is designed around a **single debug loop that never returns to human** - it keeps iterating until success.

---

## Complete Pipeline Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         PLATO SIM CREATION PIPELINE                              │
└─────────────────────────────────────────────────────────────────────────────────┘

USER: "Create a sim for github.com/org/app"
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           PHASE 1: PREPARATION                                   │
│                                                                                 │
│   ┌────────────┐      ┌────────────┐      ┌────────────┐                       │
│   │  RESEARCH  │─────▶│  VALIDATE  │─────▶│   CONFIG   │                       │
│   │            │      │            │      │   WRITER   │                       │
│   │ • GitHub   │      │ • DB type  │      │            │                       │
│   │   README   │      │   supported│      │ • plato-   │                       │
│   │ • Docker   │      │   (PG/MySQL│      │   config   │                       │
│   │   image    │      │ • Image    │      │   .yml     │                       │
│   │ • Creds    │      │   exists   │      │ • docker-  │                       │
│   │ • DB type  │      │ • Creds    │      │   compose  │                       │
│   │ • Env vars │      │   available│      │   .yml     │                       │
│   └────────────┘      └─────┬──────┘      └─────┬──────┘                       │
│                             │                   │                               │
│                        BLOCKER?                 │                               │
│                        (MongoDB,                │                               │
│                         no image)               │                               │
│                             │                   │                               │
│                             ▼                   │                               │
│                     STOP & REPORT               │                               │
│                     (can't build)               │                               │
│                                                 │                               │
└─────────────────────────────────────────────────┼───────────────────────────────┘
                                                  │
                                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           PHASE 2: EXECUTION                                     │
│                                                                                 │
│   ┌────────────┐      ┌────────────┐      ┌────────────┐      ┌────────────┐   │
│   │   START    │─────▶│   START    │─────▶│    TEST    │─────▶│   START    │   │
│   │  SANDBOX   │      │  SERVICES  │      │   LOGIN    │      │   WORKER   │   │
│   │            │      │            │      │            │      │            │   │
│   │ plato      │      │ plato      │      │ Browser:   │      │ plato      │   │
│   │ sandbox    │      │ sandbox    │      │ • Navigate │      │ sandbox    │   │
│   │ start      │      │ start-     │      │ • Fill     │      │ start-     │   │
│   │            │      │ services   │      │   creds    │      │ worker     │   │
│   │            │      │            │      │ • Submit   │      │            │   │
│   │            │      │            │      │ • Verify   │      │            │   │
│   │            │      │            │      │   dashboard│      │            │   │
│   └────────────┘      └────────────┘      └─────┬──────┘      └─────┬──────┘   │
│         │                   │                   │                   │          │
│         │                   │                   │                   │          │
│         │                   │            ┌──────┴──────┐            │          │
│         │                   │            │             │            │          │
│         │                   │        LOGIN OK?    LOGIN FAIL        │          │
│         │                   │            │             │            │          │
│         │                   │            │             │            │          │
│         │                   │            ▼             │            │          │
│         │                   │      PROCEED TO         │            │          │
│         │                   │      WORKER             │            │          │
│         │                   │            │            │            │          │
│         │                   │            │            │            │          │
│         │                   │            │            ▼            │          │
│         │                   │            │     ┌─────────────┐     │          │
│         │                   │            │     │  ██████████ │     │          │
│         │                   │            │     │  █DEBUGGER█ │◀────┘          │
│         │                   └───────────────▶  │  ██████████ │                │
│         └─────────────────────────────────────▶│             │                │
│                                                │ (see below) │                │
│                                                └──────┬──────┘                │
│                                                       │                       │
│                                                       │ (loops back to        │
│                                                       │  appropriate step)    │
│                                                       │                       │
└───────────────────────────────────────────────────────┼───────────────────────┘
                                                        │
                              ┌─────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           PHASE 3: FINALIZATION                                  │
│                                                                                 │
│   ┌────────────┐      ┌────────────┐      ┌────────────┐                       │
│   │  SNAPSHOT  │─────▶│  REVIEW    │─────▶│   SUBMIT   │                       │
│   │            │      │  CHECK     │      │   REVIEW   │                       │
│   │ plato      │      │            │      │            │                       │
│   │ sandbox    │      │ Verify:    │      │ Queues for │                       │
│   │ snapshot   │      │ • No       │      │ human      │                       │
│   │            │      │   mutations│      │ approval   │                       │
│   │            │      │   after    │      │            │                       │
│   │            │      │   login    │      │            │                       │
│   │            │      │ • Real     │      │            │                       │
│   │            │      │   changes  │      │            │                       │
│   │            │      │   detected │      │            │                       │
│   └────────────┘      └─────┬──────┘      └─────┬──────┘                       │
│         │                   │                   │                               │
│         │              BAD OUTPUT?              │                               │
│         │              (mutations,              │                               │
│         │               no detection)           │                               │
│         │                   │                   │                               │
│         │                   ▼                   │                               │
│         │            ┌─────────────┐            │                               │
│         └───────────▶│  DEBUGGER   │            │                               │
│                      │             │            │                               │
│                      │ Fix audit   │            │                               │
│                      │ tables,     │            │                               │
│                      │ re-snapshot │            │                               │
│                      └─────────────┘            │                               │
│                                                 │                               │
└─────────────────────────────────────────────────┼───────────────────────────────┘
                                                  │
                                                  ▼
                                            ┌──────────┐
                                            │   DONE   │
                                            │          │
                                            │ Awaiting │
                                            │ human    │
                                            │ approval │
                                            └──────────┘
```

---

## The Debugger: Central Fix Loop

The debugger is the heart of the system. It **never returns to human** - it keeps iterating until the problem is solved.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                 DEBUGGER                                         │
│                                                                                 │
│  "Never give up. Never return to human. Keep fixing until it works."            │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│                          INNER LOOP (Fast, on VM)                               │
│                                                                                 │
│      This is where you iterate quickly. Don't keep running                      │
│      `plato sandbox start-services` - that's slow.                              │
│                                                                                 │
│   ┌─────────┐    ┌─────────┐    ┌─────────────┐    ┌─────────┐                 │
│   │   SSH   │───▶│  Edit   │───▶│   docker    │───▶│  Test   │                 │
│   │  into   │    │  files  │    │   compose   │    │         │                 │
│   │   VM    │    │  on VM  │    │   down &&   │    │ • curl  │                 │
│   │         │    │         │    │   up -d     │    │ • logs  │                 │
│   │         │    │         │    │             │    │ • browser│                │
│   └─────────┘    └─────────┘    └─────────────┘    └────┬────┘                 │
│        │              ▲                                 │                       │
│        │              │              NO                 │                       │
│        │              └─────────────────────────────────┤                       │
│        │                                                │                       │
│        │         ssh -F ~/.plato/ssh_42.conf sandbox-42 │                       │
│        │         cd /home/plato/code/base               │                       │
│        │         vim docker-compose.yml                 │ YES                   │
│        │         docker compose down && up -d           │                       │
│        │         docker compose logs -f                 ▼                       │
│        │                                         ┌─────────────┐               │
│        │                                         │  IT WORKS   │               │
│        │                                         │  ON THE VM! │               │
│        │                                         └──────┬──────┘               │
│        │                                                │                       │
├────────┼────────────────────────────────────────────────┼───────────────────────┤
│        │                                                │                       │
│        │                     SYNC BACK                  │                       │
│        │                                                │                       │
│        │         Once it works on VM, copy files back   │                       │
│        │         to local machine.                      │                       │
│        │                                                │                       │
│        │                                                ▼                       │
│        │                                     ┌───────────────────┐             │
│        │                                     │   scp FROM VM     │             │
│        │                                     │   TO local        │             │
│        │                                     │                   │             │
│        │                                     │ scp -F {ssh}      │             │
│        │                                     │   sandbox-42:     │             │
│        │                                     │   /home/plato/    │             │
│        │                                     │   code/base/      │             │
│        │                                     │   docker-compose  │             │
│        │                                     │   .yml            │             │
│        │                                     │   ./base/         │             │
│        │                                     └─────────┬─────────┘             │
│        │                                               │                       │
├────────┼───────────────────────────────────────────────┼───────────────────────┤
│        │                                               │                       │
│        │                  OUTER LOOP (Official)        │                       │
│        │                                               │                       │
│        │         Run the official flow to verify       │                       │
│        │         everything works through Plato.       │                       │
│        │                                               │                       │
│        │                                               ▼                       │
│        │                                    ┌────────────────────┐             │
│        │                                    │  plato sandbox     │             │
│        │                                    │  start-services    │             │
│        │                                    │                    │             │
│        │                                    │  (syncs local →    │             │
│        │                                    │   VM, runs         │             │
│        │                                    │   officially)      │             │
│        │                                    └──────────┬─────────┘             │
│        │                                               │                       │
│        │                                               ▼                       │
│        │                                    ┌────────────────────┐             │
│        │                                    │  Continue pipeline │             │
│        │                                    │  from where we     │             │
│        │                                    │  left off          │             │
│        │                                    └────────────────────┘             │
│        │                                                                       │
└────────┴───────────────────────────────────────────────────────────────────────┘
```

---

## What the Debugger Knows

The debugger has embedded knowledge from all other skills:

### From Config-Writer
- Correct `plato-config.yml` format (service, datasets, compute, metadata, services, listeners)
- Correct `docker-compose.yml` format (network_mode: host, Plato DB images, signal healthchecks)
- Database images: `public.ecr.aws/i3q4i1d7/app-sim/{postgres-15|mysql-8.0|mariadb-10.6}:prod-latest`
- Connections use `127.0.0.1`, not service names

### From Flow-Writer
- Correct `flows.yml` format (`flows:` array wrapper, `type:` not `action:`)
- Must have both `login` and `incorrect_login` flows
- Hardcoded credentials, not `{{templates}}`
- Screenshots at key points, waits after navigation

### From Review Expectations
- No mutations should appear after login (fix with `audit_ignore_tables`)
- Real changes must be detected (fix audit config)
- Login must succeed (fix flow selectors or app config)

---

## Error Types and Loop-Back Points

| Error Type | Where It Fails | Debugger Fixes | Loops Back To |
|------------|----------------|----------------|---------------|
| Container won't start | start-services | Edit docker-compose on VM | start-services |
| Healthcheck timeout | start-services | Increase timeout, fix deps | start-services |
| Missing env vars | start-services | Add env vars to compose | start-services |
| Login page not found | test-login | Fix flow URL, check app | test-login |
| Wrong selectors | test-login | Inspect with browser, fix flow | test-login |
| Login fails | test-login | Fix creds, check DB seeding | start-services |
| Worker loop (30s errors) | start-worker | Stop, fix services, re-verify | start-services |
| Mutations after login | review-check | Add audit_ignore_tables | snapshot |
| No mutations detected | review-check | Fix audit config | snapshot |

---

## Critical Gates

### Gate 1: Validation
**Must pass before creating config files.**

- Database must be PostgreSQL, MySQL, or MariaDB
- Docker image must exist with specific version tag
- Credentials must be available (default or setup wizard)

### Gate 2: Login Test
**Must pass before starting worker.**

```
WRONG:  services → worker → test login
        (If login broken, worker enters infinite error loop)

RIGHT:  services → TEST LOGIN → worker
        (Verify login works, THEN start worker)
```

### Gate 3: Review Check
**Must pass before submitting review.**

- Run review, check output
- If mutations after login → fix audit tables, re-snapshot
- If no mutations detected → fix audit config, re-snapshot
- Only submit when output is clean

---

## Skills Summary

| Skill | Purpose | When Called |
|-------|---------|-------------|
| **sim-creator** | Orchestrator - coordinates all skills | Entry point |
| **sim-research** | Gather info from GitHub | Step 1 |
| **sim-validator** | Verify app can be a sim | Step 2 |
| **sim-config-writer** | Create plato-config + docker-compose | Step 3 |
| **sim-sandbox-operator** | Run plato CLI commands | Steps 4-8 |
| **sim-flow-writer** | Create flows.yml with browser | Step 5 |
| **sim-debugger** | Fix any failure, never give up | On any failure |
| **sim-reviewer** | Check review output, submit | Step 9 |

---

## Principles

1. **Never return to human** - The debugger keeps trying until it works.

2. **Debug on VM first** - SSH in, iterate fast with `docker compose up -d`, then sync back.

3. **Test login before worker** - The worker will loop infinitely if services are broken.

4. **Review before submit** - Check the output is clean before submitting for human approval.

5. **Debugger is the brain** - It has all context (config format, flow format, review expectations) and can fix anything.

---

## Command Reference

```bash
# Start sandbox VM from plato-config.yml
plato sandbox start -c

# Deploy containers (syncs local files to VM)
plato sandbox start-services

# Start the Plato worker (ONLY after login verified)
plato sandbox start-worker

# Create snapshot (saves artifact_id to .sandbox.yaml)
plato sandbox snapshot

# Run review (pass simulator name and artifact ID)
plato pm review base -s {sim_name} -a {artifact_id}
# Or use colon notation:
plato pm review base -s {sim_name}:{artifact_id}

# SSH into VM for debugging
ssh -F ~/.plato/ssh_42.conf sandbox-42
```

### CRITICAL: Two Docker Sockets on VM

```bash
docker ps  # Shows all containers including db, app, proxy
```

### Code Path on VM

```
/home/plato/worktree/{sim_name}/base/
```

```bash
# On VM: iterate fast
cd /home/plato/worktree/{sim_name}/base
docker compose down && docker compose up -d
docker compose logs -f
```

```bash
# Sync working files back to local
scp -F ~/.plato/ssh_42.conf sandbox-42:/home/plato/worktree/{sim_name}/base/docker-compose.yml ./base/
```
