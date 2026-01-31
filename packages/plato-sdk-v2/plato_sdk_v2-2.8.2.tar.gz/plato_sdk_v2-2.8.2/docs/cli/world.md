# plato world

Manage and publish world packages.

## Commands

| Command | Description |
|---------|-------------|
| `publish` | Build and publish a world package |

## plato world publish

Build and publish a world package to the Plato worlds repository.

```bash
# Publish from current directory
plato world publish

# Publish from specific path
plato world publish ./my-world-package

# Dry run (build without uploading)
plato world publish --dry-run
```

### Requirements

- `pyproject.toml` with package name and version
- `PLATO_API_KEY` environment variable

### Options

| Option | Description |
|--------|-------------|
| `--dry-run` | Build without uploading |

### Workflow

1. Reads `pyproject.toml` for package info
2. Builds package with `uv build`
3. Uploads wheel to Plato worlds repository

### Output

```
Package: my-world
Version: 0.1.0
Repository: worlds
Building package...
Build successful
Built: my_world-0.1.0-py3-none-any.whl
Uploading to https://plato.so/api/v2/pypi/worlds/...
Upload successful!

Install with:
  uv add my-world --index-url https://plato.so/api/v2/pypi/worlds/simple/
```

## What is a World?

A world defines the environment and constraints for agent benchmarks. It includes:

- Environment configuration
- Task definitions
- Evaluation criteria
- Dataset specifications

## Creating a World Package

### Directory Structure

```
my-world/
├── pyproject.toml
├── my_world/
│   ├── __init__.py
│   ├── config.py
│   └── tasks.py
└── README.md
```

### pyproject.toml

```toml
[project]
name = "my-world"
version = "0.1.0"
description = "My custom world for agent evaluation"
requires-python = ">=3.10"
dependencies = [
    "plato-sdk-v2>=2.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## Installation

After publishing, install your world:

```bash
uv add my-world --index-url https://plato.so/api/v2/pypi/worlds/simple/
```

Or add the index to your `pyproject.toml`:

```toml
[[tool.uv.index]]
name = "plato-worlds"
url = "https://plato.so/api/v2/pypi/worlds/simple/"
```

Then:

```bash
uv add my-world
```

## Prerequisites

```bash
pip install tomli  # For reading pyproject.toml
pip install uv     # For building packages
```

## See Also

- [plato agent](agent.md) - Agent commands for running on worlds
- [Main CLI Reference](../CLI.md) - Overview of all CLI commands
