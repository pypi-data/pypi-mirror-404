# Generating Simulator SDKs

This guide explains how to generate Python SDK clients from OpenAPI specs for Plato simulators.

## Overview

The SDK generator creates type-safe Python clients from OpenAPI specifications. Generated SDKs include:

- Async and sync HTTP clients with automatic authentication
- Pydantic models for request/response types
- API endpoint functions organized by tag
- Full type hints for IDE support

## Directory Structure

A simulator repository should have this structure:

```
my-sim/
├── plato-config.yml      # Main configuration
├── specs/
│   ├── openapi.yaml      # OpenAPI specification
│   └── auth.yaml         # Authentication configuration
└── tests/
    └── test_api.py       # Integration tests
```

## Configuration Files

### plato-config.yml

The main configuration file for your simulator:

```yaml
service: my-sim
target: my-sim.web.plato.so

sdk:
  package_name: my-sim        # PyPI package name
  version: 0.1.0              # Semantic version
  description: My Sim API SDK
  specs_dir: specs            # Directory containing OpenAPI spec
```

### specs/auth.yaml

Authentication configuration for the generated client. Supports multiple auth types:

#### OAuth Client Credentials

```yaml
type: oauth
env_prefix: MYSIM

oauth:
  token_endpoint: /oauth/token
  grant_type: client_credentials
  scope: admin
  default_client_id: your-client-id
  default_client_secret: your-client-secret
```

#### OAuth Password Grant

```yaml
type: oauth
env_prefix: MYSIM

oauth:
  token_endpoint: /oauth/token
  grant_type: password
  scope: admin
  default_username: admin@example.com
  default_password: password123
```

#### Bearer Token

```yaml
type: bearer_token
env_prefix: MYSIM

bearer_token:
  default_token: your-api-token
  header: Authorization      # optional, default: Authorization
  prefix: Bearer            # optional, default: Bearer
```

#### Basic Auth

```yaml
type: basic
env_prefix: MYSIM

basic:
  default_username: admin
  default_password: password
```

#### Session Auth

```yaml
type: session
env_prefix: MYSIM

session:
  login_endpoint: /api/login
  default_username: admin
  default_password: password
```

### specs/openapi.yaml

Standard OpenAPI 3.0/3.1 specification. The `servers` section should use empty string for relative paths:

```yaml
openapi: 3.0.0
info:
  title: My Sim API
  version: 1.0.0
servers:
  - url: ""  # Empty for relative paths
paths:
  /api/v1/users:
    get:
      operationId: listUsers
      tags:
        - Users
      responses:
        '200':
          description: Success
```

## Generating & Publishing

### Prerequisites

```bash
# Install plato-sdk-v2 with sims extras
uv add plato-sdk-v2

# Set your API key
export PLATO_API_KEY=pk_user_xxx
```

### Commands

```bash
# Generate and publish SDK
plato sims publish

# Dry run (generate without uploading)
plato sims publish --dry-run

# Specify custom config path
plato sims publish --config path/to/plato-config.yml
```

### Output

On success:
```
Publishing SDK for: my-sim
Package name: my-sim
Version: 0.1.0
Using OpenAPI spec: specs/openapi.yaml
Generating SDK code...
  Generator version: 2.0.28
  Parsed 50 endpoints
Building package...
  Build successful
  Built: my-sim-0.1.0-py3-none-any.whl
Uploading...
  Upload successful!

Install with:
  uv add my-sim --index-url https://plato.so/api/v2/pypi/sims/simple/
```

## Using Generated SDKs

### Installation

```bash
# Add the Plato sims index to pyproject.toml
[[tool.uv.index]]
name = "plato-sims"
url = "https://plato.so/api/v2/pypi/sims/simple/"

# Install the SDK
uv add my-sim
```

### Usage

```python
from plato.sims import my_sim

# Async client (auto-authenticates)
async def main():
    client = await my_sim.AsyncClient.create(base_url="https://...")

    # Use httpx client for requests
    response = await client.httpx.get("/api/v1/users")
    data = response.json()

    await client.close()

# Sync client
def sync_main():
    client = my_sim.Client.create(base_url="https://...")
    response = client.httpx.get("/api/v1/users")
    client.close()
```

### With Plato Sessions

```python
from plato.v2 import AsyncPlato, Env
from plato.sims import my_sim

async def main():
    plato = AsyncPlato()

    session = await plato.sessions.create(
        envs=[Env.artifact("artifact-id", alias="my-sim")],
        timeout=300,
    )
    await session.wait_until_ready()

    urls = await session.get_connect_url()

    # Create authenticated client
    client = await my_sim.AsyncClient.create(base_url=urls["my-sim"])

    # Make API calls
    response = await client.httpx.get("/api/v1/users")

    await client.close()
    await session.close()
```

## Writing Tests

Example test file (`tests/test_api.py`):

```python
import pytest
import pytest_asyncio
from plato.sims import my_sim
from plato.v2 import Env

ARTIFACT_ID = "your-artifact-id"

class TestMySimAPI:
    @pytest_asyncio.fixture
    async def session(self, plato_client):
        session = await plato_client.sessions.create(
            envs=[Env.artifact(ARTIFACT_ID, alias="my-sim")],
            timeout=300,
        )
        await session.wait_until_ready()
        await session.start_heartbeat()

        urls = await session.get_connect_url()
        yield urls["my-sim"], session

        await session.close()

    @pytest.mark.asyncio
    async def test_list_users(self, session):
        url, _ = session
        client = await my_sim.AsyncClient.create(base_url=url)

        response = await client.httpx.get("/api/v1/users")
        assert response.status_code == 200

        data = response.json()
        assert "data" in data

        await client.close()
```

Run tests:

```bash
PLATO_API_KEY=pk_user_xxx uv run pytest tests/test_api.py -v
```

## Environment Variables

The generated client respects these environment variables (prefix from `env_prefix` in auth.yaml):

| Variable | Description |
|----------|-------------|
| `{PREFIX}_BASE_URL` | Base URL for API requests |
| `{PREFIX}_API_TOKEN` | Bearer token (for bearer_token auth) |
| `{PREFIX}_CLIENT_ID` | OAuth client ID (for oauth auth) |
| `{PREFIX}_CLIENT_SECRET` | OAuth client secret (for oauth auth) |
| `{PREFIX}_USERNAME` | Username (for password/basic/session auth) |
| `{PREFIX}_PASSWORD` | Password (for password/basic/session auth) |

## Troubleshooting

### "OpenAPI spec not found"

Ensure `sdk.specs_dir` in `plato-config.yml` points to the directory containing `openapi.yaml`.

### "invalid_client" OAuth error

The OAuth application credentials may not be seeded in the artifact. Check:
1. The artifact has the OAuth app registered
2. The `client_id` and `client_secret` in `auth.yaml` match

### Version conflict on publish

Bump the version in `plato-config.yml`:
```yaml
sdk:
  version: 0.1.1  # Increment this
```

### Platform API returns 401 but Storefront works

Some APIs (like Spree) have different auth requirements for different API sections. Platform APIs may require a registered OAuth application while storefront APIs work with password grant.
