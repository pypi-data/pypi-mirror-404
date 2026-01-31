# plato agent

Manage, deploy, and run agents using Harbor infrastructure.

## Commands

| Command | Description |
|---------|-------------|
| `run` | Run an agent using Harbor's runner infrastructure |
| `list` | List all available agents |
| `schema` | Get the configuration schema for an agent |
| `publish` | Build and publish an agent package |
| `deploy` | Deploy a Chronos agent package to AWS CodeArtifact |

## plato agent run

Run an agent using Harbor's runner infrastructure.

```bash
# Basic usage
plato agent run -a claude-code -m anthropic/claude-sonnet-4 -d swe-bench-lite

# With OpenHands
plato agent run -a openhands -m openai/gpt-4o -d terminal-bench

# Pass additional Harbor options after --
plato agent run -- -a claude-code -m anthropic/claude-sonnet-4 -d swe-bench-lite --limit 10
```

### Options

| Option | Description |
|--------|-------------|
| `--agent, -a` | Agent name (e.g., 'claude-code', 'openhands') |
| `--model, -m` | Model name (e.g., 'anthropic/claude-sonnet-4') |
| `--dataset, -d` | Dataset to run on |

### Available Agents

**Harbor Agents:**
- `claude-code` - Anthropic's CLI coding agent
- `openhands` - All Hands AI coding agent
- `codex` - OpenAI CLI coding agent
- `aider` - AI pair programming tool
- `gemini-cli` - Google's CLI coding agent
- `goose` - Block's coding agent
- `swe-agent` - Princeton's software engineering agent
- `mini-swe-agent` - Lightweight SWE-agent
- `cline-cli` - VS Code extension CLI
- `cursor-cli` - Cursor editor CLI
- `opencode` - Open source coding agent
- `qwen-coder` - Alibaba's coding agent

**Plato Agents:**
- `computer-use` - Browser automation agent (requires `pip install plato-agent-computer-use`)

## plato agent list

List all available agents with descriptions.

```bash
plato agent list
```

## plato agent schema

Get the JSON configuration schema for an agent.

```bash
plato agent schema claude-code
plato agent schema openhands
```

## plato agent publish

Build and publish an agent package to the Plato agents repository.

```bash
# Publish from current directory
plato agent publish

# Publish from specific path
plato agent publish ./my-agent-package

# Dry run (build without uploading)
plato agent publish --dry-run
```

### Requirements

- `pyproject.toml` with package name and version
- `PLATO_API_KEY` environment variable

### Options

| Option | Description |
|--------|-------------|
| `--dry-run` | Build without uploading |

### Output

```
Package: my-agent
Version: 0.1.0
Repository: agents
Building package...
Build successful
Uploading to https://plato.so/api/v2/pypi/agents/...
Upload successful!

Install with:
  uv add my-agent --index-url https://plato.so/api/v2/pypi/agents/simple/
```

## plato agent deploy

Deploy a Chronos agent package to AWS CodeArtifact.

```bash
# Deploy from current directory
plato agent deploy

# Deploy from specific path
plato agent deploy ./my-agent-package
```

### Requirements

- `pyproject.toml` with:
  - `name` - Package name
  - `version` - Semantic version (X.Y.Z format)
  - `description` (optional)
- `PLATO_API_KEY` environment variable

### Workflow

1. Reads `pyproject.toml` for package info
2. Validates semantic version format
3. Builds package with `uv build`
4. Discovers `@ai` agents from package
5. Uploads wheel and sdist to Plato API

### Output

```
Package: my-chronos-agent
Version: 1.0.0
Building package...
Build successful
Wheel: my_chronos_agent-1.0.0-py3-none-any.whl
Sdist: my_chronos_agent-1.0.0.tar.gz
Uploading to Plato API...
Deployment successful!
Package: my-chronos-agent v1.0.0
Artifact ID: art_xyz789

Install with:
  uv add my-chronos-agent
```

## Prerequisites

### Harbor CLI

For running agents, Harbor must be installed:

```bash
pip install harbor
# or
uv tool install harbor
```

### Package Dependencies

For publishing/deploying:

```bash
pip install tomli  # For reading pyproject.toml
pip install uv     # For building packages
```

## See Also

- [Harbor Documentation](https://github.com/harbor-ai/harbor) - Harbor runner documentation
- [Main CLI Reference](../CLI.md) - Overview of all CLI commands
