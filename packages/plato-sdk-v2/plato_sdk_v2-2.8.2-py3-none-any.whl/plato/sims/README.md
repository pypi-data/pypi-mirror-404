# Plato Sims - Simulation API Clients

Auto-generated API clients for simulation environments, designed for easy integration with code agents.

## Features

- **Auto-discovery**: Automatically discovers available sims from OpenAPI specs
- **Environment-based auth**: Reads credentials from environment variables
- **Default credentials**: Uses defaults from `auth.yaml` for Plato artifacts
- **CLI exploration**: Browse API documentation without opening files
- **Agent-friendly**: Clean interface for code agents to discover and use sims

## Quick Start

### Using a Client

```python
import os
from plato.sims import firefly

# Set environment variables
os.environ["FIREFLY_BASE_URL"] = "https://firefly.example.com"
os.environ["FIREFLY_TOKEN"] = "your-token-here"

# Create client - base_url read from env automatically
client = firefly.Client.create()

# Use the API
response = client.httpx.get("/v2/autocomplete/accounts")
print(response.json())

client.close()
```

### Or Use Async

```python
import asyncio
from plato.sims import firefly

async def main():
    # Reads from env vars automatically
    client = await firefly.AsyncClient.create()

    response = await client.httpx.get("/v2/autocomplete/accounts")
    print(response.json())

    await client.close()

asyncio.run(main())
```

## CLI - Exploring APIs

### List available sims
```bash
uv run python -m plato.sims.cli list
```

### Get detailed info about a sim
```bash
uv run python -m plato.sims.cli info firefly
```

Output:
```
Firefly III API v6.2.13
============================================================

Name: firefly
Auth Type: bearer_token

Required Environment Variables:
  FIREFLY_BASE_URL: Base URL for the API (has default for artifacts)
  FIREFLY_TOKEN: Bearer token / Personal Access Token (has default for artifacts)

Usage:
  from plato.sims import firefly
  client = await firefly.AsyncClient.create()
```

### List all endpoints
```bash
uv run python -m plato.sims.cli endpoints firefly
```

### Get the raw OpenAPI spec
```bash
uv run python -m plato.sims.cli spec firefly
```

## For Code Agents

### Discovery and Documentation

```python
from plato.sims.agent_helpers import (
    get_available_sims,
    get_sim_env_requirements,
    get_sim_api_docs,
    setup_sim_env,
    create_sim_client,
)

# Discover available sims
sims = get_available_sims()
print(sims.keys())  # ['espocrm', 'firefly', 'mattermost', 'spree']

# Get env requirements for a sim
reqs = get_sim_env_requirements("firefly")
print(reqs)
# {
#     "FIREFLY_BASE_URL": "Base URL for the API",
#     "FIREFLY_TOKEN": "Bearer token / Personal Access Token"
# }

# Get API documentation
docs = get_sim_api_docs("firefly")
print(docs)  # Markdown-formatted API docs
```

### Creating Clients for Agents

```python
import os
from plato.sims.agent_helpers import setup_sim_env, create_sim_client

# Option 1: Use with artifact ID (constructs base URL automatically)
setup_sim_env("firefly", artifact_id="abc-123")
client = create_sim_client("firefly", artifact_id="abc-123")

# Option 2: Manual env setup
os.environ["FIREFLY_BASE_URL"] = "https://firefly.example.com"
os.environ["FIREFLY_TOKEN"] = "token"
client = create_sim_client("firefly")

# Option 3: Use Plato Env object
from plato.v2 import Env
env = Env.from_artifact("artifact-id")
client = create_sim_client("firefly", env=env)

# Use the client
response = client.httpx.get("/v2/autocomplete/accounts")
```

### Direct Import (Recommended)

The cleanest approach is to just set env vars and use the client directly:

```python
import os
from plato.sims import firefly

# Set env vars (agent can do this programmatically)
os.environ["FIREFLY_BASE_URL"] = "https://firefly.example.com"
os.environ["FIREFLY_TOKEN"] = "token"

# Create client - no base_url needed!
client = firefly.Client.create()

# API is available
response = client.httpx.get("/v2/autocomplete/accounts")
```

## Available Sims

- **firefly** - Firefly III personal finance manager (bearer token auth)
- **spree** - Spree Commerce platform (OAuth, multiple APIs: platform/storefront)
- **espocrm** - EspoCRM customer relationship manager (basic auth)
- **mattermost** - Mattermost team collaboration (session auth)

## Multi-API Sims

Some sims like Spree have multiple APIs:

```python
from plato.sims.spree import platform, storefront

# Set env
os.environ["SPREE_BASE_URL"] = "https://spree.example.com"
os.environ["SPREE_CLIENT_ID"] = "id"
os.environ["SPREE_CLIENT_SECRET"] = "secret"

# Create platform API client
platform_client = platform.Client.create()

# Create storefront API client
storefront_client = storefront.Client.create()
```

## Authentication Types

### Bearer Token (e.g., Firefly)
```python
# Env vars:
# {PREFIX}_BASE_URL
# {PREFIX}_TOKEN

client = firefly.Client.create()
```

### OAuth Client Credentials (e.g., Spree)
```python
# Env vars:
# {PREFIX}_BASE_URL
# {PREFIX}_CLIENT_ID
# {PREFIX}_CLIENT_SECRET

client = spree.platform.Client.create()
```

### Basic Auth (e.g., EspoCRM)
```python
# Env vars:
# {PREFIX}_BASE_URL
# {PREFIX}_USERNAME
# {PREFIX}_PASSWORD

client = espocrm.Client.create()
```

### Session Login (e.g., Mattermost)
```python
# Env vars:
# {PREFIX}_BASE_URL
# {PREFIX}_USERNAME
# {PREFIX}_PASSWORD

client = mattermost.Client.create()  # Logs in automatically
```

## Regenerating Clients

After modifying OpenAPI specs:

```bash
uv run python -m plato.sims.generate_clients
```

This will:
1. Auto-discover all sims in `specs/` directory
2. Generate Python clients from OpenAPI specs
3. Configure authentication based on `auth.yaml`
4. Run type checking to ensure correctness

## Architecture

```
plato/sims/
├── specs/                    # OpenAPI specs and auth configs
│   ├── firefly/
│   │   ├── default.yaml     # OpenAPI spec
│   │   └── auth.yaml        # Auth configuration
│   ├── spree/
│   │   ├── platform.yaml    # Platform API spec
│   │   ├── storefront.yaml  # Storefront API spec
│   │   └── auth.yaml        # Shared auth config
│   └── ...
├── firefly/                  # Generated client code
│   ├── client.py
│   ├── models/
│   └── api/
├── spree/
│   ├── platform/            # Platform API client
│   └── storefront/          # Storefront API client
├── registry.py              # Sim discovery and metadata
├── agent_helpers.py         # Helper functions for agents
├── cli.py                   # CLI for exploring APIs
└── generate_clients.py      # Generator script
```

## Type Safety

All generated clients are fully type-checked with **0 errors**:
- Pydantic v2 models for request/response types
- Type hints for all functions
- Optional types for nullable fields
- Union types for polymorphic responses

```bash
# Run type checker
uv run basedpyright plato/sims/
```
