# Plato CLI Reference

The Plato CLI (`plato`) provides commands for managing simulator development, sandbox environments, and agent workflows.

## Installation

```bash
pip install plato-sdk-v2
# or
uv add plato-sdk-v2
```

## Configuration

Set your API key:
```bash
export PLATO_API_KEY=pk_user_xxx
```

## Command Groups

| Command | Description |
|---------|-------------|
| [`plato sandbox`](cli/sandbox.md) | Manage sandbox environments for simulator development |
| [`plato pm`](cli/pm.md) | Project management for simulator review workflow |
| [`plato agent`](cli/agent.md) | Run and deploy agents using Harbor |
| [`plato world`](cli/world.md) | Manage and publish world packages |
| [`plato sims`](cli/sims.md) | Explore and publish simulation APIs |
| `plato hub` | Launch the interactive TUI for browsing simulators |
| `plato clone` | Clone a simulator repository from Plato Hub |
| `plato credentials` | Display your Plato Hub (Gitea) credentials |

## Top-Level Commands

### `plato hub`

Launch the Plato Hub CLI - an interactive terminal UI for managing simulators.

```bash
# Start interactive TUI
plato hub

# Clone a service
plato hub clone espocrm

# Show credentials
plato hub credentials
```

### `plato clone`

Clone a simulator repository from Plato Hub (Gitea).

```bash
plato clone espocrm
plato clone gitea
```

### `plato credentials`

Display your Plato Hub (Gitea) credentials for accessing repositories.

```bash
plato credentials
```

## Quick Start Workflows

### Developing a New Simulator

```bash
# 1. Clone or create simulator repo
plato clone mysim
cd mysim

# 2. Start sandbox from config
plato sandbox start --from-config

# 3. Sync local code to sandbox
plato sandbox sync

# 4. Start services (docker compose)
plato sandbox start-worker

# 5. Test login flow
plato sandbox flow --flow-name login

# 6. Create snapshot when ready
plato sandbox snapshot

# 7. Stop sandbox
plato sandbox stop
```

### Testing an Existing Simulator

```bash
# Start from published artifact
plato sandbox start --simulator espocrm:prod-latest

# Run login flow
plato sandbox flow

# Check status
plato sandbox status

# Stop when done
plato sandbox stop
```

### Running Agents on Benchmarks

```bash
# Run Claude Code on SWE-bench
plato agent run -a claude-code -m anthropic/claude-sonnet-4 -d swe-bench-lite

# List available agents
plato agent list
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `PLATO_API_KEY` | Your Plato API key (required for most commands) |
| `PLATO_BASE_URL` | API base URL (default: `https://plato.so`) |

## See Also

- [Simulator Lifecycle Guide](SIMULATOR_LIFECYCLE.md) - Complete workflow for building and iterating on simulators
- [Sim Creator Guide](SIM_CREATOR.md) - How to create new simulators from GitHub repositories
- [Creating Flows](cli/flows.md) - How to write login and test flows
- [Generating Simulator SDKs](GENERATING_SIM_SDKS.md) - How to generate Python SDKs from OpenAPI specs
