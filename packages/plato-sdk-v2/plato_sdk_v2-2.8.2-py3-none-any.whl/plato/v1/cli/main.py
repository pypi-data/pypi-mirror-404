"""Plato CLI - Main entry point."""

import os
import platform
import shutil
from pathlib import Path

import typer
from dotenv import load_dotenv

from plato.v1.cli.agent import agent_app
from plato.v1.cli.chronos import chronos_app
from plato.v1.cli.pm import pm_app
from plato.v1.cli.proxy import app as proxy_app
from plato.v1.cli.sandbox import sandbox_app
from plato.v1.cli.utils import console
from plato.v1.cli.world import world_app


def _find_bundled_cli() -> str | None:
    """
    Find the Plato Go CLI binary.

    Returns:
        Path to the CLI binary if found, None otherwise.
    """
    # Check locations in order of preference
    search_paths = []

    # 1. Bundled in package (plato-cli) - go up from cli/ to v1/
    binary_name = "plato-cli.exe" if platform.system().lower() == "windows" else "plato-cli"
    package_dir = Path(__file__).resolve().parent.parent  # v1/
    bin_dir = package_dir / "bin"
    search_paths.append(bin_dir / binary_name)

    # 2. plato-client/cli/bin/plato (development location)
    # Navigate from python-sdk/plato/v1/cli/main.py to plato-client/cli/bin/plato
    plato_client_dir = package_dir.parent.parent.parent  # Go up to plato-client
    go_binary_name = "plato.exe" if platform.system().lower() == "windows" else "plato"
    search_paths.append(plato_client_dir / "cli" / "bin" / go_binary_name)

    # 3. Check PATH for 'plato-cli' only (not 'plato' to avoid finding Python entry point)
    which_result = shutil.which(binary_name)
    if which_result:
        search_paths.append(Path(which_result))

    # Return first found executable that is NOT the Python entry point
    python_entry_point = shutil.which("plato")  # This is the Python CLI
    for path in search_paths:
        if path.exists() and os.access(path, os.X_OK):
            # Skip if this is the Python entry point (would cause infinite recursion)
            if python_entry_point and str(path.resolve()) == str(Path(python_entry_point).resolve()):
                continue
            return str(path)

    return None


# Load environment variables
load_dotenv()
load_dotenv(dotenv_path=os.path.join(os.path.expanduser("~"), ".env"))
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))


# =============================================================================
# MAIN APP
# =============================================================================

app = typer.Typer(help="[bold blue]Plato CLI[/bold blue] - Manage Plato environments and simulators.")

# Register sub-apps
app.add_typer(sandbox_app, name="sandbox")
app.add_typer(pm_app, name="pm")
app.add_typer(agent_app, name="agent")
app.add_typer(world_app, name="world")
app.add_typer(chronos_app, name="chronos")
app.add_typer(proxy_app, name="proxy")


# =============================================================================
# TOP-LEVEL COMMANDS
# =============================================================================


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def hub(
    ctx: typer.Context,
):
    """Launch the Plato Hub CLI (interactive TUI for managing simulators).

    Opens the Go-based Plato CLI which provides an interactive terminal UI for
    browsing simulators, launching environments, and managing VMs. Any additional
    arguments are passed through to the Go CLI.

    Common subcommands: 'clone <service>', 'credentials', or no args for interactive mode.
    """
    # Find the bundled CLI binary
    plato_bin = _find_bundled_cli()

    if not plato_bin:
        console.print("[red]❌ Plato CLI binary not found in package[/red]")
        console.print("\n[yellow]The bundled CLI binary was not found in this installation.[/yellow]")
        console.print("This indicates an installation issue with the plato-sdk package.")
        console.print("\n[yellow]💡 Try reinstalling the package:[/yellow]")
        console.print("   pip install --upgrade --force-reinstall plato-sdk")
        console.print("\n[dim]If the issue persists, please report it at:[/dim]")
        console.print("[dim]https://github.com/plato-app/plato-client/issues[/dim]")
        raise typer.Exit(1)

    # Get any additional arguments passed after 'hub'
    args = ctx.args if hasattr(ctx, "args") else []

    try:
        # Launch the Go CLI, passing through all arguments
        # Use execvp to replace the current process so the TUI works properly
        os.execvp(plato_bin, [plato_bin] + args)
    except Exception as e:
        console.print(f"[red]❌ Failed to launch Plato Hub: {e}[/red]")
        raise typer.Exit(1) from e


@app.command()
def clone(
    service: str = typer.Argument(..., help="Service name to clone (e.g., espocrm)"),
):
    """Clone a service repository from Plato Hub (Gitea).

    Clones the simulator source code to your local machine for development or review.

    Arguments:
        service: Service name to clone (e.g., 'espocrm', 'gitea')
    """
    plato_bin = _find_bundled_cli()
    if not plato_bin:
        console.print("[red]❌ Plato CLI binary not found[/red]")
        console.print("[yellow]Cannot clone without the Go CLI binary.[/yellow]")
        raise typer.Exit(1)

    try:
        os.execvp(plato_bin, [plato_bin, "clone", service])
    except Exception as e:
        console.print(f"[red]❌ Failed to clone: {e}[/red]")
        raise typer.Exit(1) from e


@app.command()
def credentials():
    """Display your Plato Hub (Gitea) credentials.

    Shows the username and password needed to access Plato's Gitea repositories
    for cloning and pushing simulator code.
    """
    plato_bin = _find_bundled_cli()
    if not plato_bin:
        console.print("[red]❌ Plato CLI binary not found[/red]")
        console.print("[yellow]Cannot show credentials without the Go CLI binary.[/yellow]")
        raise typer.Exit(1)

    try:
        os.execvp(plato_bin, [plato_bin, "credentials"])
    except Exception as e:
        console.print(f"[red]❌ Failed to get credentials: {e}[/red]")
        raise typer.Exit(1) from e


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    help="Explore simulation APIs (list, info, endpoints, spec)",
)
def sims(ctx: typer.Context):
    """Explore simulation APIs - list sims, view endpoints, get OpenAPI specs."""
    from plato.sims import cli as sims_cli

    # Pass all arguments to the sims CLI
    sims_cli.main(ctx.args)


# =============================================================================
# ENTRY POINT
# =============================================================================

# force bump to v36
# TEST/MOCK: This comment marks test-related code. Used for verification in release workflow.


def main():
    """Main entry point for the Plato CLI."""
    app()


# Backward compatibility
cli = main

if __name__ == "__main__":
    main()
