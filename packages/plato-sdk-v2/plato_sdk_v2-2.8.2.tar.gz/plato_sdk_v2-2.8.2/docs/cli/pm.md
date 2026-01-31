# plato pm

Project management commands for the simulator review workflow. Used by both simulator developers (workers) and reviewers to manage the submission and approval process.

## Command Groups

| Command Group | Description |
|---------------|-------------|
| `plato pm list` | List simulators pending review |
| `plato pm review` | Review simulator artifacts |
| `plato pm submit` | Submit simulator artifacts for review |

## Simulator Status Flow

```
not_started
    ↓
env_in_progress → env_review_requested → env_approved
                        ↓ (reject)
                  env_in_progress

env_approved
    ↓
data_in_progress → data_review_requested → data_approved
                        ↓ (reject)
                  data_in_progress
```

## List Commands

### plato pm list base

List simulators pending base/environment review.

```bash
plato pm list base
```

Shows all simulators with status: `env_review_requested`

### plato pm list data

List simulators pending data review.

```bash
plato pm list data
```

Shows all simulators with status: `data_review_requested`

## Review Commands

### plato pm review base

Review a base/environment artifact. Opens the simulator in a browser for manual testing.

```bash
# Interactive - prompts for simulator and artifact
plato pm review base

# Direct - specify simulator (uses base_artifact_id from config)
plato pm review base --simulator espocrm

# Direct - specify both
plato pm review base -s espocrm -a art_abc123
```

**Workflow:**
1. Creates a session with the artifact
2. Resets the environment
3. Launches browser and logs in
4. Interactive loop for testing:
   - `state` or `s`: Show environment state and mutations
   - `finish` or `f`: Exit and submit review
5. Prompts for outcome: pass, reject, or skip

**On Pass:**
- Status: `env_review_requested` → `env_approved`
- Artifact tagged as `prod-latest`

**On Reject:**
- Status: `env_review_requested` → `env_in_progress`
- Comments required

### plato pm review data

Launch browser with EnvGen Recorder extension for data review.

```bash
# Generic - opens sims.plato.so
plato pm review data

# For specific simulator
plato pm review data -s fathom
```

**Workflow:**
1. Copies EnvGen Recorder extension to temp directory
2. Launches Chrome with extension loaded
3. Navigates to simulator URL
4. Auto-configures API key in extension
5. User manually tests and submits review via extension
6. Press Ctrl+C when done

## Submit Commands

### plato pm submit base

Submit base/environment artifact for review after creating a snapshot.

```bash
# From sandbox directory (reads .sandbox.yaml)
plato pm submit base
```

**Requirements:**
- Active sandbox with `artifact_id` in `.sandbox.yaml`
- `plato_config_path` pointing to valid plato-config.yml
- Current status: `env_in_progress`

**Effect:**
- Status: `env_in_progress` → `env_review_requested`
- Tags artifact as `base-pending-review`

### plato pm submit data

Submit data artifact for review after data generation.

```bash
# Interactive - prompts for inputs
plato pm submit data

# Direct
plato pm submit data --simulator espocrm --artifact art_abc123
plato pm submit data -s espocrm -a art_abc123
```

**Requirements:**
- Current status: `data_in_progress`

**Effect:**
- Status: `data_in_progress` → `data_review_requested`
- Tags artifact as `data-pending-review`

## Typical Workflows

### Worker: Building Base Environment

```bash
# 1. Develop simulator locally
plato sandbox start --from-config
plato sandbox sync
plato sandbox start-worker
plato sandbox flow

# 2. Create snapshot when ready
plato sandbox snapshot

# 3. Submit for review
plato pm submit base

# 4. Wait for review feedback
plato sandbox stop
```

### Reviewer: Reviewing Base Environment

```bash
# 1. See what's pending
plato pm list base

# 2. Review a specific simulator
plato pm review base -s espocrm

# 3. Test in browser, then choose:
#    - pass (→ env_approved, tagged prod-latest)
#    - reject (→ env_in_progress, with comments)
#    - skip (no change)
```

### Worker: Building Data Layer

```bash
# 1. Start from approved base
plato sandbox start --simulator espocrm:prod-latest

# 2. Generate/seed data
# ... (manual or automated data generation)

# 3. Create snapshot
plato sandbox snapshot

# 4. Submit for data review
plato pm submit data -s espocrm -a <artifact_id>
```

### Reviewer: Reviewing Data

```bash
# 1. See what's pending
plato pm list data

# 2. Launch extension browser
plato pm review data -s espocrm

# 3. Use EnvGen Recorder to test and submit review
```

## Options Reference

### plato pm review base

| Option | Description |
|--------|-------------|
| `--simulator, -s` | Simulator name |
| `--artifact, -a` | Artifact ID (uses base_artifact_id if not provided) |

### plato pm review data

| Option | Description |
|--------|-------------|
| `--simulator, -s` | Simulator name (navigates to {simulator}.web.plato.so) |

### plato pm submit data

| Option | Description |
|--------|-------------|
| `--simulator, -s` | Simulator name |
| `--artifact, -a` | Artifact ID (required) |

## See Also

- [Simulator Lifecycle Guide](../SIMULATOR_LIFECYCLE.md) - Complete workflow for building simulators
- [sandbox.md](sandbox.md) - Sandbox commands for development
- [Main CLI Reference](../CLI.md) - Overview of all CLI commands
