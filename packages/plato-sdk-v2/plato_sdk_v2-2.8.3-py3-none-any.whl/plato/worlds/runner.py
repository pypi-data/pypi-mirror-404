"""World runner - discovers and runs Plato worlds."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Annotated

import typer

from plato.worlds.config import RunConfig

app = typer.Typer(
    name="plato-world-runner",
    help="Run Plato worlds",
    no_args_is_help=True,
)

logger = logging.getLogger(__name__)


def discover_worlds() -> None:
    """Discover and load installed world packages via entry points.

    World packages declare entry points in pyproject.toml:
        [project.entry-points."plato.worlds"]
        code = "code_world:CodeWorld"

    This function loads all such entry points, triggering registration.
    """
    import importlib.metadata

    try:
        eps = importlib.metadata.entry_points(group="plato.worlds")
    except TypeError:
        # Python < 3.10 compatibility
        eps = importlib.metadata.entry_points().get("plato.worlds", [])

    for ep in eps:
        try:
            ep.load()
            logger.debug(f"Loaded world: {ep.name}")
        except Exception as e:
            logger.warning(f"Failed to load world '{ep.name}': {e}")


async def run_world(world_name: str, config: RunConfig) -> None:
    """Run a world by name with the given configuration.

    Args:
        world_name: Name of the world to run
        config: Run configuration (should be the world's typed config class)

    Raises:
        ValueError: If world not found
    """
    discover_worlds()

    from plato.worlds.base import get_registered_worlds, get_world

    world_cls = get_world(world_name)
    if world_cls is None:
        available = list(get_registered_worlds().keys())
        raise ValueError(f"World '{world_name}' not found. Available: {available}")

    world = world_cls()
    await world.run(config)


@app.command()
def run(
    world: Annotated[str, typer.Option("--world", "-w", help="World name to run")],
    config: Annotated[Path, typer.Option("--config", "-c", help="Path to config JSON file")],
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose logging")] = False,
) -> None:
    """Run a world with the given configuration."""
    # Setup logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if not config.exists():
        typer.echo(f"Error: Config file not found: {config}", err=True)
        raise typer.Exit(1)

    # Discover worlds first to get config class
    discover_worlds()

    from plato.worlds.base import get_registered_worlds, get_world

    world_cls = get_world(world)
    if world_cls is None:
        available = list(get_registered_worlds().keys())
        typer.echo(f"Error: World '{world}' not found. Available: {available}", err=True)
        raise typer.Exit(1)

    # Load config using the world's typed config class
    config_class = world_cls.get_config_class()
    run_config = config_class.from_file(config)

    try:
        world_instance = world_cls()
        asyncio.run(world_instance.run(run_config))
    except Exception as e:
        logger.exception(f"World execution failed: {e}")
        raise typer.Exit(1)


@app.command("list")
def list_worlds(
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose logging")] = False,
) -> None:
    """List available worlds."""
    if verbose:
        logging.basicConfig(level=logging.DEBUG)

    discover_worlds()

    from plato.worlds.base import get_registered_worlds

    worlds = get_registered_worlds()
    if not worlds:
        typer.echo("No worlds found.")
        return

    typer.echo("Available worlds:")
    for name, cls in worlds.items():
        desc = getattr(cls, "description", "") or ""
        version = cls.get_version()
        typer.echo(f"  {name} (v{version}): {desc}")


def main() -> None:
    """CLI entry point."""
    app()


if __name__ == "__main__":
    main()
