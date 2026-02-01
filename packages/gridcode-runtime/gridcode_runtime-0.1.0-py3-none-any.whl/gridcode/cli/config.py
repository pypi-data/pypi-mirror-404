"""GridCode CLI config command - Manage configuration."""

from pathlib import Path
from typing import Annotated

import typer
import yaml
from pydantic import ValidationError
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

from gridcode.config import (
    ConfigLoader,
    ConfigManager,
    ConfigTemplateManager,
    ConfigValidator,
    LayeredConfigManager,
)

config_app = typer.Typer(
    name="config",
    help="Manage GridCode configuration",
)

console = Console()

# Global config manager instance
_config_manager = None


def _get_config_manager() -> ConfigManager:
    """Get or create global config manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


@config_app.command()
def show(
    config_file: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-c",
            help="Path to configuration file.",
        ),
    ] = None,
    raw: Annotated[
        bool,
        typer.Option(
            "--raw",
            help="Show raw config without expanding environment variables.",
        ),
    ] = False,
) -> None:
    """Show current configuration.

    Searches for gridcode.yaml in current directory and parent directories,
    then falls back to ~/.config/gridcode/gridcode.yaml.
    """
    manager = _get_config_manager()

    # Find or load config
    if config_file:
        if not config_file.exists():
            console.print(f"[red]Config file not found: {config_file}[/red]")
            raise typer.Exit(1)
        config_path = config_file
    else:
        config_path = manager.find_config_file()

    if config_path is None:
        console.print("[yellow]No configuration file found.[/yellow]")
        console.print("Run [bold]gridcode config init[/bold] to create one.")
        console.print("\nSearched locations:")
        locations = manager.get_config_locations()
        for loc_type, loc_path in locations.items():
            if loc_path:
                console.print(f"  - {loc_path}")
        raise typer.Exit(1)

    console.print(f"[dim]Config file: {config_path}[/dim]\n")

    # Load and display config
    if raw:
        with open(config_path, encoding="utf-8") as f:
            content = f.read()
        syntax = Syntax(content, "yaml", theme="monokai", line_numbers=True)
        console.print(syntax)
    else:
        try:
            config = ConfigLoader.load(config_path, expand_env=True)
            yaml_str = yaml.dump(
                config.model_dump(),
                default_flow_style=False,
                sort_keys=False,
            )
            syntax = Syntax(yaml_str, "yaml", theme="monokai", line_numbers=True)
            console.print(syntax)
        except (ValidationError, Exception) as e:
            console.print(f"[red]Error loading configuration: {e}[/red]")
            console.print(
                "\nRun [bold]gridcode config validate[/bold] for detailed error information."
            )
            raise typer.Exit(1)


@config_app.command()
def init(
    global_config: Annotated[
        bool,
        typer.Option(
            "--global",
            "-g",
            help="Create global config in ~/.config/gridcode/",
        ),
    ] = False,
    template: Annotated[
        str | None,
        typer.Option(
            "--template",
            "-t",
            help=(
                "Configuration template to use "
                "(default, development, production, testing, minimal, openai)"
            ),
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Overwrite existing config file.",
        ),
    ] = False,
) -> None:
    """Initialize a new configuration file.

    By default, creates gridcode.yaml in the current directory.
    Use --global to create in ~/.config/gridcode/ instead.
    Use --template to choose a configuration template.
    """
    manager = _get_config_manager()

    if global_config:
        config_path = Path.home() / ".config" / "gridcode" / "gridcode.yaml"
    else:
        config_path = Path.cwd() / "gridcode.yaml"

    # Check if file exists
    if config_path.exists() and not force:
        console.print(f"[yellow]Config file already exists: {config_path}[/yellow]")
        console.print("Use --force to overwrite.")
        raise typer.Exit(1)

    # Use template if specified
    if template:
        template_manager = ConfigTemplateManager()
        if not template_manager.create_config_from_template(template, config_path):
            console.print(f"[red]Unknown template: {template}[/red]")
            console.print("\nAvailable templates:")
            for name, (desc, is_built_in) in template_manager.list_templates().items():
                marker = "✓" if is_built_in else "◇"
                console.print(f"  {marker} {name}: {desc}")
            raise typer.Exit(1)
        console.print(
            f"[green]Created config file from '{template}' template: {config_path}[/green]"
        )
    else:
        # Create default config
        try:
            manager.create_default_config(config_path, force=force)
            console.print(f"[green]Created config file: {config_path}[/green]")
        except FileExistsError:
            console.print(f"[yellow]Config file already exists: {config_path}[/yellow]")
            console.print("Use --force to overwrite.")
            raise typer.Exit(1)

    console.print("\nEdit this file to customize your GridCode settings.")
    console.print("Key settings:")
    console.print("  - runtime.api_key: Your Anthropic API key")
    console.print("  - runtime.framework: 'langgraph' or 'pydantic-ai'")
    console.print("  - plugins.dirs: Directories to search for plugins")
    console.print("  - mcp.servers: MCP servers to connect")

    if not template:
        console.print("\nAvailable templates:")
        template_manager = ConfigTemplateManager()
        for name, (desc, is_built_in) in template_manager.list_templates().items():
            marker = "✓" if is_built_in else "◇"
            console.print(f"  {marker} {name}: {desc}")
        console.print("\nUse 'gridcode config init --template <name>' to use a template.")


@config_app.command()
def get(
    key: Annotated[
        str,
        typer.Argument(help="Configuration key (e.g., 'runtime.framework')"),
    ],
    config_file: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-c",
            help="Path to configuration file.",
        ),
    ] = None,
) -> None:
    """Get a specific configuration value."""
    manager = _get_config_manager()

    # Load config
    if config_file:
        if not config_file.exists():
            console.print(f"[red]Config file not found: {config_file}[/red]")
            raise typer.Exit(1)
        try:
            manager.load(config_file)
        except (ValidationError, Exception) as e:
            console.print(f"[red]Error loading configuration: {e}[/red]")
            raise typer.Exit(1)
    else:
        try:
            manager.load_or_create()
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)

    # Get value
    value = manager.get_value(key)
    if value is None:
        console.print(f"[red]Key not found: {key}[/red]")
        raise typer.Exit(1)

    if isinstance(value, dict | list):
        console.print(yaml.dump(value, default_flow_style=False))
    else:
        console.print(value)


@config_app.command()
def set(
    key: Annotated[
        str,
        typer.Argument(help="Configuration key (e.g., 'runtime.framework')"),
    ],
    value: Annotated[
        str,
        typer.Argument(help="Value to set"),
    ],
    config_file: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-c",
            help="Path to configuration file.",
        ),
    ] = None,
) -> None:
    """Set a configuration value."""
    manager = _get_config_manager()

    # Load config
    if config_file:
        if not config_file.exists():
            console.print(f"[red]Config file not found: {config_file}[/red]")
            raise typer.Exit(1)
        try:
            manager.load(config_file)
        except (ValidationError, Exception) as e:
            console.print(f"[red]Error loading configuration: {e}[/red]")
            raise typer.Exit(1)
    else:
        try:
            manager.load_or_create()
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)

    # Set value (parse as YAML if possible)
    try:
        parsed_value = yaml.safe_load(value)
    except yaml.YAMLError:
        parsed_value = value

    manager.set_value(key, parsed_value)

    # Save config
    try:
        manager.save()
        console.print(f"[green]Set {key} = {parsed_value}[/green]")
    except Exception as e:
        console.print(f"[red]Error saving configuration: {e}[/red]")
        raise typer.Exit(1)


@config_app.command()
def path() -> None:
    """Show the path to the active configuration file."""
    manager = _get_config_manager()
    config_path = manager.find_config_file()
    if config_path:
        console.print(str(config_path))
    else:
        console.print("[yellow]No configuration file found.[/yellow]")
        raise typer.Exit(1)


@config_app.command()
def locations() -> None:
    """Show all configuration file search locations."""
    manager = _get_config_manager()

    table = Table(title="Configuration Search Locations")
    table.add_column("Location", style="cyan")
    table.add_column("Exists", style="green")
    table.add_column("Type")

    manager.get_config_locations()

    # Project config
    project_config = Path.cwd() / "gridcode.yaml"
    table.add_row(
        str(project_config),
        "✓" if project_config.exists() else "",
        "Project",
    )

    # User config
    user_config = Path.home() / ".config" / "gridcode" / "gridcode.yaml"
    table.add_row(
        str(user_config),
        "✓" if user_config.exists() else "",
        "User",
    )

    console.print(table)

    # Show which one is active
    active = manager.find_config_file()
    if active:
        console.print(f"\n[bold]Active config:[/bold] {active}")


@config_app.command()
def templates(
    template_name: Annotated[
        str | None,
        typer.Argument(
            help="Name of template to show details (optional)",
        ),
    ] = None,
) -> None:
    """List available configuration templates."""
    template_manager = ConfigTemplateManager()

    if template_name:
        # Show details for specific template
        template = template_manager.get_template(template_name)
        if template is None:
            console.print(f"[red]Template not found: {template_name}[/red]")
            raise typer.Exit(1)

        console.print(f"[bold cyan]{template.name}[/bold cyan]")
        console.print(f"Description: {template.description}\n")
        console.print("[bold]Configuration:[/bold]")
        syntax = Syntax(template.to_yaml(), "yaml", theme="monokai", line_numbers=True)
        console.print(syntax)
    else:
        # List all templates
        console.print("[bold cyan]Available Configuration Templates[/bold cyan]\n")

        table = Table()
        table.add_column("Template", style="cyan")
        table.add_column("Description")
        table.add_column("Type")

        for name, (desc, is_built_in) in template_manager.list_templates().items():
            template_type = "Built-in" if is_built_in else "Custom"
            table.add_row(name, desc, template_type)

        console.print(table)

        console.print("\nUse 'gridcode config templates <name>' to see template details.")
        console.print(
            "Use 'gridcode config init --template <name>' to create config from template."
        )


@config_app.command()
def validate(
    config_file: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-c",
            help="Path to configuration file. If not specified, searches for it.",
        ),
    ] = None,
) -> None:
    """Validate a configuration file and show detailed errors/warnings."""
    # Determine config path
    if config_file:
        config_path = config_file
    else:
        manager = _get_config_manager()
        config_path = manager.find_config_file()

        if config_path is None:
            console.print("[yellow]No configuration file found.[/yellow]")
            console.print("Searched locations:")
            console.print(f"  - {Path.cwd() / 'gridcode.yaml'}")
            console.print(f"  - {Path.home() / '.config' / 'gridcode' / 'gridcode.yaml'}")
            console.print("\nCreate a configuration file with: [bold]gridcode config init[/bold]")
            raise typer.Exit(1)

    console.print(f"Validating: [cyan]{config_path}[/cyan]\n")

    # Perform validation
    is_valid, errors, warnings = ConfigValidator.validate_file(config_path)

    # Show errors
    if errors:
        console.print("[red bold]Errors:[/red bold]")
        for i, error in enumerate(errors, 1):
            console.print(f"\n  {i}. {error}")
        console.print()

    # Show warnings
    if warnings:
        console.print("[yellow bold]Warnings:[/yellow bold]")
        for i, warning in enumerate(warnings, 1):
            console.print(f"\n  {i}. {warning}")
        console.print()

    # Show result
    if is_valid:
        console.print("[green bold]✓ Configuration is valid![/green bold]")
        raise typer.Exit(0)
    else:
        console.print("[red bold]✗ Configuration has errors.[/red bold]")
        console.print("\nFix the errors above and try again.")
        raise typer.Exit(1)


@config_app.command()
def debug() -> None:
    """Show configuration loading sources and debug information."""
    manager = LayeredConfigManager()
    manager.discover()

    console.print("[bold cyan]Configuration Source Debug Information[/bold cyan]\n")

    # Show discovered sources
    console.print("[bold]Discovered Sources:[/bold]")
    table = Table()
    table.add_column("Level", style="cyan")
    table.add_column("Path")
    table.add_column("Exists", style="green")
    table.add_column("Priority")

    for source in sorted(manager.sources, key=lambda s: s.priority, reverse=True):
        table.add_row(
            source.level,
            str(source.path),
            "✓" if source.path.exists() else "",
            str(source.priority),
        )

    console.print(table)

    # Try to load
    try:
        manager.load()
        console.print("\n[bold]Configuration Loading:[/bold]")
        console.print("[green]✓ Successfully loaded configuration[/green]")

        # Show source chain
        chain = manager.get_source_chain()
        if chain:
            console.print("\n[bold]Source Merge Order:[/bold]")
            for i, source_info in enumerate(chain, 1):
                console.print(f"  {i}. {source_info['level']}: {source_info['path']}")

        # Show active source
        if manager.active_source:
            console.print("\n[bold]Active Configuration:[/bold]")
            console.print(f"  Path: {manager.active_source.path}")
            console.print(f"  Level: {manager.active_source.level}")

    except Exception as e:
        console.print(f"[red]✗ Error loading configuration: {e}[/red]")
        console.print("\nRun 'gridcode config validate' for detailed error information.")
        raise typer.Exit(1)
