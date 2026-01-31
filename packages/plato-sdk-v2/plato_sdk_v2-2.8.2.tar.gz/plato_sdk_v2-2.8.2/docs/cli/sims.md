# plato sims

Explore simulation APIs and publish SDK packages.

## Commands

| Command | Description |
|---------|-------------|
| `list` | List all available simulators |
| `info` | Show detailed information about a simulator |
| `endpoints` | List API endpoints for a simulator |
| `spec` | Output the full OpenAPI spec as JSON |
| `publish` | Generate and publish an SDK package |

## plato sims list

List all available simulation APIs that are installed.

```bash
plato sims list
```

Example output:
```
Available simulation APIs:

  espocrm
    EspoCRM API (v1.0.0)
    Auth: oauth

  spree
    Spree Commerce API (v4.0.0)
    Auth: bearer_token
```

## plato sims info

Show detailed information about a specific simulator.

```bash
plato sims info spree
```

Example output:
```
Spree Commerce API (v4.0.0)
============================================================

E-commerce platform API for managing products, orders, and users.

Name: spree
Generator Version: 2.0.34
Auth Type: bearer_token

Required Environment Variables:
  SPREE_API_TOKEN: API bearer token

Usage:
  from plato.sims import spree
  client = await spree.AsyncClient.create(base_url='...')
```

## plato sims endpoints

List API endpoints for a simulator. Useful for exploring available operations.

```bash
# Show all resources (high-level overview)
plato sims endpoints espocrm

# Filter by resource/tag
plato sims endpoints espocrm --tag account

# Show import examples
plato sims endpoints espocrm --tag account --code

# Filter by path
plato sims endpoints espocrm --path "/User" --code

# For multi-spec APIs
plato sims endpoints spree --spec platform --tag Products --code
```

### Options

| Option | Description |
|--------|-------------|
| `--spec` | Spec name for multi-spec APIs (e.g., platform, storefront) |
| `--tag` | Filter by resource/tag name |
| `--path` | Filter by URL path substring |
| `--code` | Show import/usage code examples |

### Example Output

```
EspoCRM API (v8.0.0)
============================================================

API Resources (15):

  ACCOUNT (12 endpoints)
    - account_create_post
    - account_get
    - account_list_get
    ...

  CONTACT (10 endpoints)
    - contact_create_post
    ...

Use --tag <resource> to filter, or --code to see import examples
Example: plato sims endpoints espocrm --tag account --code
```

With `--code`:
```
  ACCOUNT (12 endpoints)
    - account_create_post
        from plato.sims.espocrm.api.account import account_create_post
        result = await account_create_post.asyncio(client.httpx, ...)

    - account_get
        from plato.sims.espocrm.api.account import account_get
        result = await account_get.asyncio(client.httpx, ...)
```

## plato sims spec

Output the full OpenAPI specification as JSON.

```bash
plato sims spec spree
plato sims spec spree --spec platform
```

**Note:** OpenAPI specs are no longer bundled with sim packages. Check the sim's source repository for the spec.

## plato sims publish

Generate and publish an SDK package from an OpenAPI specification.

```bash
# Publish from current directory
plato sims publish

# Specify config file
plato sims publish --config plato-config.yml

# Dry run (build without uploading)
plato sims publish --dry-run

# Specify repository
plato sims publish --repo sims
```

### Options

| Option | Description |
|--------|-------------|
| `--config` | Path to plato-config.yml (default: plato-config.yml) |
| `--repo` | Repository name (default: sims) |
| `--dry-run` | Build without uploading |
| `--output-dir` | Copy built wheel to this directory |

### Requirements

- `plato-config.yml` with SDK configuration
- OpenAPI specification file
- `PLATO_API_KEY` environment variable

### plato-config.yml Example

```yaml
service: my-sim
target: my-sim.web.plato.so

sdk:
  package_name: my-sim          # PyPI package name
  version: 0.1.0                # Semantic version
  description: My Sim API SDK
  specs_dir: specs              # Directory containing OpenAPI spec
```

### Directory Structure

```
my-sim/
├── plato-config.yml
├── specs/
│   ├── openapi.yaml    # OpenAPI specification
│   └── auth.yaml       # Authentication configuration
└── ...
```

### Output

```
Publishing SDK for: my-sim
Package name: my-sim
Version: 0.1.0
Using OpenAPI spec: specs/openapi.yaml
Generating SDK code...
  Generator version: 2.0.34
  Parsed 50 endpoints
Building package...
  Build successful
  Built: my-sim-0.1.0-py3-none-any.whl
Uploading...
  Upload successful!

Install with:
  uv add my-sim --index-url https://plato.so/api/v2/pypi/sims/simple/
```

## Using Published SDKs

### Installation

Add the Plato sims index to your `pyproject.toml`:

```toml
[[tool.uv.index]]
name = "plato-sims"
url = "https://plato.so/api/v2/pypi/sims/simple/"
```

Install:

```bash
uv add my-sim
```

### Usage

```python
from plato.sims import my_sim

# Async client (auto-authenticates)
async def main():
    client = await my_sim.AsyncClient.create(base_url="https://...")
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
    client = await my_sim.AsyncClient.create(base_url=urls["my-sim"])

    response = await client.httpx.get("/api/v1/users")

    await client.close()
    await session.close()
```

## See Also

- [Generating Simulator SDKs](../GENERATING_SIM_SDKS.md) - Detailed guide on SDK generation
- [Main CLI Reference](../CLI.md) - Overview of all CLI commands
