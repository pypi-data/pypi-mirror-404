---
name: trajectory-analysis
description: Analyzes Plato session trajectories from Chronos API. Shows visual flow diagram, backtracks, issues, and diagnostic summary. Usage: /trajectory-analysis <session_id>
allowed-tools: Bash, Read
user-invocable: true
---

# Trajectory Analysis

Analyze a Plato session to visualize the execution flow and identify issues.

## API Key

```bash
CHRONOS_API_KEY="pk_user_xhAO5_6DuDXAAz4nIK4AI-gVOaxl6ADDngZYCcURqFw"
```

## Usage

The user provides a session ID as the argument. Extract it from the input (it's a UUID like `6ae416d1-83c2-4b0d-8d09-4a5e3faf8007`).

## Execution

Run this analysis in order:

### 1. Fetch and Parse Logs

```bash
SESSION_ID="{session_id}"
CHRONOS_API_KEY="pk_user_xhAO5_6DuDXAAz4nIK4AI-gVOaxl6ADDngZYCcURqFw"

curl -s -H "X-API-Key: $CHRONOS_API_KEY" \
  "https://chronos.plato.so/api/sessions/$SESSION_ID/logs" > /tmp/trajectory_logs.json
```

### 2. Get Session Overview

```bash
echo "=== Session: $SESSION_ID ==="
jq -r '.logs[] | select(.name == "world_reset") | .attributes | "Sim: \(.sim_name)\nGitHub: \(.github_url)\nTotal Steps: \(.total_steps)"' /tmp/trajectory_logs.json | head -3
```

### 3. Get Raw Step Data

```bash
jq -r '.logs[] | select(.name | test("^step_[0-9]+$")) | "\(.attributes["plato.step.number"])|\(.attributes["plato.step.observation"])"' /tmp/trajectory_logs.json
```

### 4. Get Backtrack Details (FULL - no truncation)

```bash
jq -r '.logs[] | select(.name | test("execute_step")) | select(.attributes.backtrack_to) | "BACKTRACK: \(.attributes.step_name) -> \(.attributes.backtrack_to)\nREASON: \(.attributes.backtrack_reason)"' /tmp/trajectory_logs.json
```

### 5. Get Errors

```bash
jq -r '[.logs[] | select(.attributes["log.level"] == "ERROR")] | .[] | .attributes["log.message"]' /tmp/trajectory_logs.json
```

### 6. Get Verification Results

```bash
jq -r '.logs[] | select(.name | test("^verify_")) | "\(.attributes.step_name)|\(.attributes.all_passed)|\(.attributes.verifier_count)"' /tmp/trajectory_logs.json
```

## Output Format - Visual Diagrams

After gathering the data, present it visually. **NEVER truncate or crop any text - show full reasons.**

### Header Box

```
╔══════════════════════════════════════════════════════════════════╗
║                    SESSION TRAJECTORY ANALYSIS                    ║
╠══════════════════════════════════════════════════════════════════╣
║  Session: {session_id}                                           ║
║  Sim:     {sim_name}                                             ║
║  GitHub:  {github_url}                                           ║
╚══════════════════════════════════════════════════════════════════╝
```

### Flow Diagram

Draw the actual flow with boxes and arrows. Show backtracks as return arrows.

**For a successful linear flow:**
```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ research │───▶│  config  │───▶│ sandbox  │───▶│  worker  │───▶ ...
└──────────┘    └──────────┘    └──────────┘    └──────────┘
     ✓               ✓               ✓               ✓
```

**For a flow with backtracks:**
```
┌──────────┐    ┌──────────┐    ┌──────────┐
│ research │───▶│  config  │───▶│ sandbox  │
└──────────┘    └──────────┘    └──────────┘
     ✓               ✓               ✗
                     ▲               │
                     │   BACKTRACK   │
                     └───────────────┘

                ┌──────────┐    ┌──────────┐    ┌──────────┐
           ───▶│  config  │───▶│ sandbox  │───▶│  worker  │───▶ ...
                └──────────┘    └──────────┘    └──────────┘
                     ✓               ✓               ✓
```

### Step-by-Step Timeline

```
STEP 1 ══════════════════════════════════════════════════════════════
┌─────────────────────────────────────────────────────────────────────┐
│  research                                                     [✓]   │
│  ───────────────────────────────────────────────────────────────    │
│  Status: PASSED                                                     │
│  Next:   config                                                     │
│  Verify: 2 verifiers passed                                         │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
STEP 2 ══════════════════════════════════════════════════════════════
┌─────────────────────────────────────────────────────────────────────┐
│  config                                                       [✓]   │
│  ───────────────────────────────────────────────────────────────    │
│  Status: PASSED                                                     │
│  Next:   sandbox                                                    │
│  Verify: 1 verifier passed                                          │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
STEP 3 ══════════════════════════════════════════════════════════════
┌─────────────────────────────────────────────────────────────────────┐
│  sandbox                                                      [✗]   │
│  ───────────────────────────────────────────────────────────────    │
│  Status: BACKTRACK → config                                         │
│                                                                     │
│  ┌─ ISSUE ────────────────────────────────────────────────────────┐ │
│  │ {FULL backtrack reason here - never truncate}                  │ │
│  │ {continue on multiple lines if needed}                         │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                          ┌─────────┘
                          │ RETRY
                          ▼
STEP 4 ══════════════════════════════════════════════════════════════
...
```

### Issues Summary Box

```
╔══════════════════════════════════════════════════════════════════╗
║                         ISSUES FOUND                              ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  ⚠️  BACKTRACK at Step 3: sandbox → config                        ║
║  ─────────────────────────────────────────────────────────────    ║
║  {FULL reason - show everything, wrap lines as needed}            ║
║  {line 2 of reason}                                               ║
║  {line 3 of reason}                                               ║
║                                                                   ║
╚══════════════════════════════════════════════════════════════════╝
```

### Verification Summary

```
┌─ VERIFICATIONS ─────────────────────────────────────────────────────┐
│                                                                     │
│  research     ✓ PASSED   (2 verifiers)                              │
│  config       ✓ PASSED   (1 verifier)                               │
│  config       ✓ PASSED   (1 verifier)   ← retry                     │
│  sandbox      ✓ PASSED   (5 verifiers)                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Summary Stats

```
┌─ SUMMARY ───────────────────────────────────────────────────────────┐
│                                                                     │
│  Total Steps Executed:  5                                           │
│  Backtracks:            1                                           │
│  Current Position:      worker_setup                                │
│  Overall Status:        IN PROGRESS                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Recommendations Box (if issues found)

```
╔══════════════════════════════════════════════════════════════════╗
║                       RECOMMENDATIONS                             ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  Based on: "port 8888 vs port 80" in backtrack reason             ║
║                                                                   ║
║  → The router expects traffic on port 80 but nginx/app is         ║
║    listening on port 8888                                         ║
║                                                                   ║
║  → Fix: Update nginx.conf to listen on port 80, or update         ║
║    docker-compose.yml healthcheck to match the actual port        ║
║                                                                   ║
╚══════════════════════════════════════════════════════════════════╝
```

## Common Issue Patterns

Use these to generate recommendations:

| Pattern in Reason | Likely Cause | Recommendation |
|-------------------|--------------|----------------|
| "port" mismatch | nginx/app not listening on expected port | Check vm_port from router token, update nginx.conf to listen on correct port |
| "heartbeat" | VM crashed or became unresponsive | Check container health, resource limits, increase healthcheck timeouts |
| "worker" errors | Database audit setup failed | Verify DB credentials, check worker logs, ensure DB is ready |
| "mutations" | Login generates DB changes | Add tables/columns to audit_ignore_tables in plato-config.yml |
| "verify" fail | Step requirements not met | Check verifier output for specific missing requirements |
| "manifest unknown" | GHCR image auth failed | Switch to Docker Hub image instead of ghcr.io |
| "timeout" | Operation took too long | Increase timeout values, check for slow startup |
| "connection refused" | Service not running | Check docker logs, verify service started |
