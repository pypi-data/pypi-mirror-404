# Agent Implementation Spec

How to implement an agent that works with the Plato runtime.

## Overview

An agent is a program that:
1. Receives a task prompt via CLI
2. Has access to Plato simulator APIs via environment variables
3. Runs inside a Docker container

## Contract

### Input

1. **CLI arguments** - Task prompt (e.g., `-t "do something"`)
2. **Environment variables** - Simulator URLs, API keys

### Environment Variables

```bash
# Simulator URLs (from World)
SPREE_BASE_URL=http://sim-abc123.plato.so/spree
FIREFLY_BASE_URL=http://sim-abc123.plato.so/firefly

# API keys (user-provided)
ANTHROPIC_API_KEY=sk-...

# Workspace
WORKSPACE=/workspace
```

### Workspace

- Mounted at `/workspace`
- Read/write access
- Use for intermediate files, git ops, etc.

### Output

- Exit 0 on success, non-zero on failure
- Logs to stdout/stderr (captured by runtime)

---

## Docker Image

### Minimal Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

# Install plato SDK for simulator access
RUN pip install plato-sdk-v2[sims]

ENTRYPOINT ["python", "-m", "my_agent"]
```

---

## Agent Implementation

### 1. The Agent Code

```python
# my_agent/__main__.py
import argparse
import os
from plato.sims import spree

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--task", required=True)
    args = parser.parse_args()

    # Get simulator client from env
    client = spree.Client.from_env()  # Uses SPREE_BASE_URL

    print(f"Executing: {args.task}")
    # ... your agent logic ...

    return 0

if __name__ == "__main__":
    exit(main())
```

### 2. The Agent Class

```python
from plato.agent import Agent, AgentConfig

class MyAgent(Agent):
    # Production image (from ECR)
    PROD_IMAGE = "123456.dkr.ecr.../my-agent:latest"
    # Dev image (base image for mounting code)
    DEV_IMAGE = "python:3.11-slim"

    def __init__(self, config: MyAgentConfig):
        super().__init__(config)

    @property
    def image(self) -> str:
        if self.config.local_code_path:
            return self.DEV_IMAGE
        return self.PROD_IMAGE

    @property
    def local_code_path(self) -> str | None:
        # Set this to enable dev mode
        return self.config.local_code_path

    @property
    def code_mount_path(self) -> str:
        return "/app/my_agent"

    def build_command(self, prompt: str) -> list[str]:
        return ["python", "-m", "my_agent", "-t", prompt]
```

---

## Dev Mode (Fast Iteration)

Dev mode mounts your local code into a base Docker image, so you don't need to rebuild.

### How It Works

```
┌─────────────────────────────────────┐
│  Docker Container (python:3.11)    │
│  ┌─────────────────────────────┐   │
│  │ /app/my_agent (mounted)     │◄──┼── Your local code
│  │ /workspace (mounted)        │◄──┼── Workspace dir
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

### Enable Dev Mode

```python
# In your agent config
class MyAgentConfig(AgentConfig):
    local_code_path: str | None = None  # Set for dev mode

# Usage
config = MyAgentConfig(
    model="anthropic/claude-sonnet-4",
    local_code_path="/home/user/my_agent",  # Mount local code
)
agent = MyAgent(config)
```

### Dev Workflow

```bash
# Edit your agent code locally
vim my_agent/logic.py

# Run - no Docker rebuild needed!
python run_simulation.py

# Code changes are reflected immediately
```

---

## Production Deployment

### 1. Build and Push

```bash
docker build -t my-agent:latest .
docker tag my-agent:latest 123456.dkr.ecr.../my-agent:latest
docker push 123456.dkr.ecr.../my-agent:latest
```

### 2. Use in Agent

```python
config = MyAgentConfig(
    model="anthropic/claude-sonnet-4",
    # No local_code_path = production mode
)
agent = MyAgent(config)  # Uses PROD_IMAGE
```

---

## Example: Custom Agent

```python
from plato.agent import Agent, AgentConfig
from pydantic import Field

class MyAgentConfig(AgentConfig):
    local_code_path: str | None = Field(default=None)
    custom_flag: bool = Field(default=False)

class MyAgent(Agent):
    PROD_IMAGE = "my-agent:latest"
    DEV_IMAGE = "python:3.11-slim"

    def __init__(self, config: MyAgentConfig | None = None):
        super().__init__(config or MyAgentConfig(model="gpt-4"))

    @property
    def my_config(self) -> MyAgentConfig:
        return self.config  # type: ignore

    @property
    def image(self) -> str:
        return self.DEV_IMAGE if self.my_config.local_code_path else self.PROD_IMAGE

    @property
    def local_code_path(self) -> str | None:
        return self.my_config.local_code_path

    @property
    def code_mount_path(self) -> str:
        return "/app"

    def build_command(self, prompt: str) -> list[str]:
        cmd = ["python", "-m", "my_agent", "-t", prompt]
        if self.my_config.custom_flag:
            cmd.append("--custom")
        return cmd
```

---

## Checklist

- [ ] Agent accepts task via CLI (`-t` or positional)
- [ ] Agent reads simulator URLs from env vars
- [ ] Agent exits 0 on success
- [ ] Dockerfile builds and runs
- [ ] Dev mode works (mounted code)
- [ ] Production image pushed to ECR
