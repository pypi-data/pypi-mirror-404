# Plato Worlds - Local Development Guide

Run Plato worlds locally for development and testing.

## Quick Start

```bash
# List available worlds
plato-world-runner list

# Run a world with a config file
plato-world-runner run --world <name> --config config.json
```

## Config File Format

Create a JSON config file:

```json
{
  "repository_url": "https://github.com/example/repo",
  "prompt": "Fix the bug in main.py",
  "coder": {
    "image": "my-agent:latest",
    "config": {
      "model": "gpt-4"
    }
  },
  "git_token": "ghp_...",
  "session_id": "local-test-001",
  "otel_url": "",
  "upload_url": ""
}
```

Or with nested format (backwards compatible):

```json
{
  "world_config": {
    "repository_url": "https://github.com/example/repo",
    "prompt": "Fix the bug in main.py"
  },
  "agents": {
    "coder": {
      "image": "my-agent:latest"
    }
  },
  "secrets": {
    "git_token": "ghp_..."
  },
  "session_id": "local-test-001"
}
```

## Creating a World

### 1. Define the Config and World Class

```python
from typing import Annotated
from plato.worlds import (
    BaseWorld, RunConfig, Agent, Secret, AgentConfig,
    Observation, StepResult, register_world
)

class MyWorldConfig(RunConfig):
    """Typed config - all fields accessible directly."""

    # World-specific fields
    prompt: str
    max_steps: int = 10

    # Agents (typed, no .get() needed)
    worker: Annotated[AgentConfig, Agent(description="The main agent")]

    # Secrets (typed, optional)
    api_key: Annotated[str | None, Secret(description="API key")] = None

@register_world("my-world")
class MyWorld(BaseWorld[MyWorldConfig]):
    name = "my-world"
    description = "A simple example world"

    async def reset(self) -> Observation:
        """Setup the world. Access config via self.config."""
        # All access is typed - no .get() methods
        prompt = self.config.prompt          # str
        worker = self.config.worker          # AgentConfig
        api_key = self.config.api_key        # str | None

        return Observation(data={"prompt": prompt})

    async def step(self) -> StepResult:
        """Execute one step."""
        return StepResult(
            observation=Observation(data={"status": "done"}),
            done=True,
        )

    async def close(self) -> None:
        """Cleanup resources."""
        pass
```

### 2. Register via Entry Point

In your `pyproject.toml`:

```toml
[project.entry-points."plato.worlds"]
my-world = "my_world:MyWorld"
```

### 3. Run It

```bash
# Install your package
pip install -e .

# Verify it's registered
plato-world-runner list

# Run with config
plato-world-runner run --world my-world --config config.json -v
```

## Programmatic Usage

```python
import asyncio
from plato.worlds import run_world
from my_world import MyWorldConfig, AgentConfig

config = MyWorldConfig(
    prompt="Hello world",
    worker=AgentConfig(image="agent:latest"),
    api_key="secret",
)

asyncio.run(run_world("my-world", config))
```

Or load from a file:

```python
from my_world import MyWorldConfig

config = MyWorldConfig.from_file("config.json")
```

## CLI Options

```
plato-world-runner [COMMAND] [OPTIONS]

Commands:
  run     Run a world with the given configuration
  list    List available worlds

Run options:
  -w, --world TEXT    World name to run (required)
  -c, --config PATH   Path to config JSON file (required)
  -v, --verbose       Enable debug logging
```

## World Lifecycle

1. **Discovery**: Worlds are discovered via `plato.worlds` entry points
2. **Instantiation**: World class is instantiated
3. **Reset**: `reset()` is called to setup the world (config available via `self.config`)
4. **Step Loop**: `step()` is called repeatedly until `done=True`
5. **Cleanup**: `close()` is called to cleanup resources

```
┌───────────────────────────────────────────────┐
│  plato-world-runner run --world X --config Y  │
└───────────────────────────────────────────────┘
                    │
                    ▼
          ┌─────────────────┐
          │ discover_worlds │
          └─────────────────┘
                    │
                    ▼
          ┌─────────────────┐
          │  world.reset()  │
          └─────────────────┘
                    │
                    ▼
          ┌─────────────────┐
          │  world.step()   │◄──┐
          └─────────────────┘   │
                    │           │
                ┌───┴───┐       │
                │ done? │───No──┘
                └───┬───┘
                   Yes
                    │
                    ▼
          ┌─────────────────┐
          │  world.close()  │
          └─────────────────┘
```

## Debugging

Enable verbose logging:

```bash
plato-world-runner run --world my-world --config config.json --verbose
```

Or set log level in code:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```
