---
name: sim-validator
description: Validates that an application can become a Plato simulator. Checks database type, Docker image availability, and identifies blockers. Use after sim-research completes.
allowed-tools: Read, Bash, WebFetch
context: fork
---

# Plato Simulator Validator

**Pipeline Position:** Phase 1, Step 2 (Gate 1)

You validate that an application can become a Plato simulator. This is the first critical gate - if validation fails with blockers, the pipeline stops.

---

## Input

A research report from sim-research skill.

---

## Validation Checks

### Check 1: Database Type (CRITICAL)

**Supported:**
- PostgreSQL (14-17)
- MySQL (any version)
- MariaDB (any version)

**NOT Supported - BLOCKER:**
- MongoDB
- SQLite
- Redis (as primary)
- Any NoSQL

### Check 2: Docker Image Exists

```bash
curl -s "https://hub.docker.com/v2/repositories/{owner}/{repo}/tags/{tag}"
```

### Check 3: Version Tag is Specific

**INVALID:** `latest`, `stable`, `main`, `master`
**VALID:** `1.2.3`, `v2.0.0`, `php8.4`

### Check 4: Credentials Available

Either:
- Default credentials documented, OR
- App allows first-run setup wizard

---

## Decision Logic

```
IF database_type NOT IN [postgresql, mysql, mariadb]:
    → BLOCKER

IF docker_image not found:
    → BLOCKER

IF image_tag IN [latest, stable, main, master]:
    → BLOCKER

IF no credentials AND no initial_setup:
    → BLOCKER

ELSE:
    → VALID - proceed to config-writer
```

---

## Output Format

### If Valid

```yaml
validation_result:
  valid: true
  blockers: []
  warnings:
    - "App requires initial setup before login"
  recommendations:
    - "Use PostgreSQL 15 image"
  research_report: {pass through}
```

### If Invalid

```yaml
validation_result:
  valid: false
  blockers:
    - "Uses MongoDB - not supported"
    - "No Docker image available"
```

And report to user:
```
FAILED: Cannot create simulator for {app_name}

Blockers:
- {blocker 1}
- {blocker 2}

The application cannot be built as a Plato simulator.
```

---

## DO NOT

- Proceed if blockers exist
- Guess at missing information
- Skip validation checks
