# Plato Python SDK

Python SDK for the Plato platform. Uses [Harbor](https://harborframework.com) for agent execution.

## Installation

```bash
pip install plato-sdk-v2

# For agent functionality (requires Python 3.12+)
pip install 'plato-sdk-v2[agents]'
```

Or with uv:

```bash
uv add plato-sdk-v2
uv add 'plato-sdk-v2[agents]'  # for agent support
```

## Configuration

Create a `.env` file in your project root:

```bash
PLATO_API_KEY=your-api-key
PLATO_BASE_URL=https://plato.so  # optional, defaults to https://plato.so
```

Or set environment variables directly:

```bash
export PLATO_API_KEY=your-api-key
```

## Agents

The SDK uses Harbor's agent framework. All agents are `BaseInstalledAgent` subclasses that run in containers.

### Available Agents

**Harbor built-in agents** (code agents):
| Agent | Description |
|-------|-------------|
| `claude-code` | Claude Code CLI |
| `openhands` | OpenHands/All Hands AI |
| `codex` | OpenAI Codex CLI |
| `aider` | Aider pair programming |
| `gemini-cli` | Google Gemini CLI |
| `goose` | Block Goose |
| `swe-agent` | SWE-agent |
| `mini-swe-agent` | Mini SWE-agent |
| `cline-cli` | Cline CLI |
| `cursor-cli` | Cursor CLI |
| `opencode` | OpenCode |
| `qwen-coder` | Qwen Coder |

**Plato custom agents** (browser/automation):
| Agent | Description |
|-------|-------------|
| `computer-use` | Browser automation (install: `pip install plato-agent-computer-use`) |

### Python Usage

```python
from plato.agents import ClaudeCode, OpenHands, AgentFactory, AgentName
from pathlib import Path

# Option 1: Use AgentFactory
agent = AgentFactory.create_agent_from_name(
    AgentName.CLAUDE_CODE,
    logs_dir=Path("./logs"),
    model_name="anthropic/claude-sonnet-4",
)

# Option 2: Import agent class directly
agent = ClaudeCode(
    logs_dir=Path("./logs"),
    model_name="anthropic/claude-sonnet-4",
)

# Option 3: Create custom BaseInstalledAgent
from plato.agents import BaseInstalledAgent
```

### CLI Usage

```bash
# Run an agent
plato agent run -a claude-code -m anthropic/claude-sonnet-4 -d swe-bench-lite

# List available agents
plato agent list

# Get agent config schema
plato agent schema claude-code

# Publish custom agent to Plato PyPI
plato agent publish ./my-agent
```

### Agent Schemas

Get configuration schemas for any agent:

```python
from plato.agents import get_agent_schema, AGENT_SCHEMAS

# Get schema for specific agent
schema = get_agent_schema("claude-code")
print(schema)

# List all available schemas
print(list(AGENT_SCHEMAS.keys()))
```

### Custom Agents

Create a custom agent by extending `BaseInstalledAgent`:

```python
from harbor.agents.installed.base import BaseInstalledAgent, ExecInput
from pathlib import Path

class MyAgent(BaseInstalledAgent):
    @staticmethod
    def name() -> str:
        return "my-agent"

    @property
    def _install_agent_template_path(self) -> Path:
        return Path(__file__).parent / "install.sh.j2"

    def create_run_agent_commands(self, instruction: str) -> list[ExecInput]:
        return [ExecInput(command=f"my-agent --task '{instruction}'")]
```

Publish to Plato PyPI:
```bash
plato agent publish ./my-agent-package
```

---

## Sessions & Environments

### Flow 1: Create Session from Environments

Use this when you want to spin up environments for development, testing, or custom automation.

```python
import asyncio
from plato.v2 import AsyncPlato, Env

async def main():
    plato = AsyncPlato()

    # Create session with one or more environments
    # (heartbeat starts automatically to keep session alive)
    session = await plato.sessions.create(
        envs=[
            Env.simulator("gitea", dataset="blank", alias="gitea"),
            Env.simulator("kanboard", alias="kanboard"),
        ],
        timeout=600,
    )

    # Reset environments to initial state
    await session.reset()

    # Get public URLs for browser access
    public_urls = await session.get_public_url()
    for alias, url in public_urls.items():
        print(f"{alias}: {url}")

    # Get state mutations from all environments
    state = await session.get_state()
    print(state)

    # Cleanup
    await session.close()
    await plato.close()

asyncio.run(main())
```

### Flow 2: Create Session from Task

Use this when running evaluations against predefined tasks. This flow includes task evaluation at the end.

```python
import asyncio
from plato.v2 import AsyncPlato

async def main():
    plato = AsyncPlato()

    # Create session from task ID
    session = await plato.sessions.create(task=123, timeout=600)

    # Reset environments to initial state
    await session.reset()

    # Get public URLs for browser access
    public_urls = await session.get_public_url()
    for alias, url in public_urls.items():
        print(f"{alias}: {url}")

    # Evaluate task completion
    evaluation = await session.evaluate()
    print(f"Task completed: {evaluation}")

    # Cleanup
    await session.close()
    await plato.close()

asyncio.run(main())
```

## Environment Configuration

Two ways to specify environments:

```python
from plato.v2 import Env

# 1. From simulator (most common)
Env.simulator("gitea")                          # default tag
Env.simulator("gitea", tag="staging")           # specific tag
Env.simulator("gitea", dataset="blank")         # specific dataset
Env.simulator("gitea", alias="my-git")          # custom alias

# 2. From artifact ID
Env.artifact("artifact-abc123")
Env.artifact("artifact-abc123", alias="my-env")
```

## Per-Environment Operations

Access individual environments within a session:

```python
# Get all environments
for env in session.envs:
    print(f"{env.alias}: {env.job_id}")

# Get specific environment by alias
gitea = session.get_env("gitea")

if gitea:
    # Execute shell command
    result = await gitea.execute("whoami", timeout=30)
    print(result)

    # Get state for this environment only
    state = await gitea.get_state()

    # Reset this environment only
    await gitea.reset()
```

## Sync Client

A synchronous client is also available:

```python
from plato.v2 import Plato, Env

plato = Plato()

session = plato.sessions.create(
    envs=[Env.simulator("gitea", alias="gitea")],
    timeout=600,
)

session.reset()

public_urls = session.get_public_url()
state = session.get_state()

session.close()
plato.close()
```

## Architecture

```
plato/
├── agents/          # Harbor agent re-exports + schemas
├── sims/            # Simulator clients (Spree, Firefly, etc.)
├── world/           # World/environment abstractions
├── v1/              # Legacy SDK + CLI
└── v2/              # New API client
```

## Documentation

- [Generating Simulator SDKs](docs/GENERATING_SIM_SDKS.md) - How to create API clients for simulators
- [Building Simulators](BUILDING_SIMS.md) - Internal docs for snapshotting simulators

## License

MIT
