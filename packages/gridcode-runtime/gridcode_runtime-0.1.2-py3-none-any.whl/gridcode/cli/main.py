"""GridCode CLI main entry point."""

import os
from pathlib import Path

import typer
from dotenv import find_dotenv, load_dotenv
from rich.console import Console

from gridcode import __version__

# Load .env file unless explicitly disabled (for testing)
# Use override=True to handle cases where env vars are set but empty
if not os.environ.get("GRIDCODE_SKIP_DOTENV"):
    env_file = find_dotenv(usecwd=True)
    if env_file:
        load_dotenv(env_file, override=True)
    else:
        # Fallback: try home directory
        load_dotenv(Path.home() / ".env", override=True)

# Create main app
app = typer.Typer(
    name="gridcode",
    help="GridCode Runtime - Modular Agentic Architecture CLI",
    no_args_is_help=True,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)

# Console for rich output
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(
            f"[bold blue]GridCode Runtime[/bold blue] version [green]{__version__}[/green]"
        )
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """GridCode Runtime - Modular Agentic Architecture.

    A production-ready agent runtime supporting LangGraph and Pydantic-AI frameworks.
    """
    pass


# Import subcommands after app creation to avoid circular imports
from gridcode.cli.config import config_app  # noqa: E402
from gridcode.cli.plugins import plugins_app  # noqa: E402

# Import and register subcommands
from gridcode.cli.run import run_app  # noqa: E402

app.add_typer(run_app, name="run", help="Execute agent queries")
app.add_typer(config_app, name="config", help="Manage configuration")
app.add_typer(plugins_app, name="plugins", help="Manage plugins")


if __name__ == "__main__":
    app()
