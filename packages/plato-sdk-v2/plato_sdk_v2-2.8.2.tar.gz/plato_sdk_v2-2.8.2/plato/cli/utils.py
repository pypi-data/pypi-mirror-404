"""Shared utilities for Plato CLI commands."""

import asyncio
import inspect
import os
import shutil
from functools import wraps
from pathlib import Path

import httpx
import typer
import yaml
from rich.console import Console

# Initialize Rich console - shared across all CLI modules
console = Console()

# Workspace-based paths
PLATO_DIR = ".plato"
STATE_FILE = ".plato/state.yaml"


def get_sandbox_state(working_dir: Path | str | None = None) -> dict | None:
    """Read sandbox state from .plato/state.yaml.

    Args:
        working_dir: Directory containing .plato/. If None, uses cwd.
    """
    base_dir = Path(working_dir) if working_dir else Path.cwd()
    state_file = base_dir / STATE_FILE
    if not state_file.exists():
        return None
    with open(state_file) as f:
        return yaml.safe_load(f)


def save_sandbox_state(state: dict, working_dir: Path | str | None = None) -> None:
    """Save sandbox state to .plato/state.yaml.

    Args:
        state: State dict to save.
        working_dir: Directory to save .plato/ in. If None, uses cwd.
    """
    base_dir = Path(working_dir) if working_dir else Path.cwd()
    plato_dir = base_dir / PLATO_DIR
    plato_dir.mkdir(mode=0o700, exist_ok=True)
    state_file = base_dir / STATE_FILE
    with open(state_file, "w") as f:
        yaml.dump(state, f, default_flow_style=False)


def remove_sandbox_state(working_dir: Path | str | None = None, remove_all: bool = True) -> None:
    """Remove sandbox state and optionally the entire .plato/ directory.

    Args:
        working_dir: Directory containing .plato/. If None, uses cwd.
        remove_all: If True, removes entire .plato/ directory. If False, only removes state.yaml.
    """
    base_dir = Path(working_dir) if working_dir else Path.cwd()
    if remove_all:
        plato_dir = base_dir / PLATO_DIR
        if plato_dir.exists():
            shutil.rmtree(plato_dir)
    else:
        state_file = base_dir / STATE_FILE
        if state_file.exists():
            state_file.unlink()


def require_sandbox_state(working_dir: Path | str | None = None) -> dict:
    """Get sandbox state or exit with error.

    Args:
        working_dir: Directory containing .plato/. If None, uses cwd.
    """
    state = get_sandbox_state(working_dir)
    if not state:
        console.print("[red]No sandbox found (.plato/state.yaml missing)[/red]")
        console.print("\n[yellow]Start a sandbox with:[/yellow]")
        console.print("  plato sandbox start --from-config")
        console.print("  plato sandbox start --simulator <name>")
        console.print("  plato sandbox start --artifact-id <id>")
        raise typer.Exit(1)
    return state


def require_sandbox_field(state: dict, field: str, hint: str | None = None) -> str:
    """Get a required field from sandbox state or exit with error."""
    value = state.get(field)
    if not value:
        console.print(f"[red]❌ No {field} found in .plato/state.yaml[/red]")
        if hint:
            console.print(f"\n[yellow]{hint}[/yellow]")
        raise typer.Exit(1)
    return value


def with_sandbox_state(*required_fields: str):
    """Decorator that fills args from .plato/state.yaml and validates required fields.

    Args:
        required_fields: Field names that must exist (from arg or state).

    Fails with helpful message if:
        - State file missing and required fields not provided as args
        - Required field is None after checking both arg and state

    Usage:
        @with_sandbox_state("job_id", "session_id")
        def stop(job_id: str | None = None, session_id: str | None = None, working_dir: Path | None = None):
            # job_id and session_id guaranteed filled or already exited
            ...
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            working_dir = kwargs.get("working_dir")
            state = get_sandbox_state(working_dir)

            sig = inspect.signature(fn)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            missing = []
            for field in required_fields:
                if bound.arguments.get(field) is None:
                    if state and field in state:
                        bound.arguments[field] = state[field]
                    else:
                        missing.append(field)

            if missing:
                if state is None:
                    console.print("[red]No .plato/state.yaml found[/red]")
                    console.print("[dim]Run from workspace or use -w /path/to/workspace[/dim]")
                else:
                    console.print(f"[red]Missing: {', '.join(missing)}[/red]")
                    console.print(f"[dim]Provide via --{missing[0].replace('_', '-')} or add to state[/dim]")
                raise typer.Exit(1)

            return fn(*bound.args, **bound.kwargs)

        return wrapper

    return decorator


def read_plato_config(config_path: str | Path) -> dict:
    """Read plato-config.yml file or exit with error."""
    try:
        with open(config_path) as f:
            return yaml.safe_load(f)
    except Exception as e:
        console.print(f"[red]❌ Error reading plato-config.yml: {e}[/red]")
        raise typer.Exit(1) from e


def require_plato_config_field(config: dict, field: str) -> str:
    """Get a required field from plato config or exit with error."""
    value = config.get(field)
    if not value:
        console.print(f"[red]❌ No {field} in plato-config.yml[/red]")
        raise typer.Exit(1)
    return value


def require_api_key() -> str:
    """Get API key or exit with error."""
    api_key = os.getenv("PLATO_API_KEY")
    if not api_key:
        console.print("[red]PLATO_API_KEY environment variable not set[/red]")
        console.print("\n[yellow]Set your API key:[/yellow]")
        console.print("  export PLATO_API_KEY='your-api-key-here'")
        raise typer.Exit(1)
    return api_key


def get_http_client() -> httpx.Client:
    """Get configured httpx client."""
    base_url = os.getenv("PLATO_BASE_URL", "https://plato.so")
    # Strip trailing /api if present (to match v2 SDK behavior)
    if base_url.endswith("/api"):
        base_url = base_url[:-4]
    base_url = base_url.rstrip("/")
    return httpx.Client(base_url=base_url, timeout=httpx.Timeout(600.0))


def handle_async(coro):
    """Helper to run async functions with proper error handling."""
    try:
        return asyncio.run(coro)
    except KeyboardInterrupt:
        console.print("\n[red]🛑 Operation cancelled by user.[/red]")
        raise typer.Exit(1) from None
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        if "401" in str(e) or "Unauthorized" in str(e):
            console.print("💡 [yellow]Hint: Make sure PLATO_API_KEY is set in your environment[/yellow]")
        raise typer.Exit(1) from e
