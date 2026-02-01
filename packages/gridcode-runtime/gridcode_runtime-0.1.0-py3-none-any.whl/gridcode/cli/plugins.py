"""GridCode CLI plugins command - Manage plugins."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

plugins_app = typer.Typer(
    name="plugins",
    help="Manage GridCode plugins",
)

console = Console()


def _get_default_plugin_dirs() -> list[Path]:
    """Get default plugin search directories."""
    dirs = []

    # Current directory plugins
    local_plugins = Path.cwd() / "plugins"
    if local_plugins.exists():
        dirs.append(local_plugins)

    # User plugins directory
    user_plugins = Path.home() / ".gridcode" / "plugins"
    if user_plugins.exists():
        dirs.append(user_plugins)

    return dirs


@plugins_app.command(name="list")
def list_plugins(
    plugin_dirs: Annotated[
        list[str],
        typer.Option(
            "--dir",
            "-d",
            help="Additional plugin directories to search.",
        ),
    ] = [],
    show_all: Annotated[
        bool,
        typer.Option(
            "--all",
            "-a",
            help="Show all plugins including disabled ones.",
        ),
    ] = False,
) -> None:
    """List available plugins.

    Searches for plugins in:
    - ./plugins (current directory)
    - ~/.gridcode/plugins (user directory)
    - Any directories specified with --dir
    """
    from gridcode.plugins.discovery import PluginDiscovery

    # Collect directories to search
    search_dirs = _get_default_plugin_dirs()
    for d in plugin_dirs:
        path = Path(d)
        if path.exists():
            search_dirs.append(path)
        else:
            console.print(f"[yellow]Warning: Directory not found: {d}[/yellow]")

    if not search_dirs:
        console.print("[yellow]No plugin directories found.[/yellow]")
        console.print("\nDefault locations:")
        console.print("  - ./plugins")
        console.print("  - ~/.gridcode/plugins")
        return

    # Discover plugins
    discovery = PluginDiscovery(plugin_dirs=search_dirs)
    result = discovery.discover_from_directories()

    plugins = result.plugins
    if not plugins:
        console.print("[dim]No plugins found.[/dim]")
        return

    # Display in table
    table = Table(title="Available Plugins")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Description")
    table.add_column("Type", style="dim")

    for plugin in plugins:
        table.add_row(
            plugin.name,
            getattr(plugin, "version", "0.0.0"),
            getattr(plugin, "description", "") or "",
            plugin.plugin_type.value if hasattr(plugin, "plugin_type") else "general",
        )

    console.print(table)
    console.print(f"\n[dim]Found {len(plugins)} plugins[/dim]")

    # Show any errors
    if result.errors:
        console.print("\n[yellow]Warnings during discovery:[/yellow]")
        for error in result.errors:
            console.print(f"  - {error}")


@plugins_app.command()
def info(
    plugin_name: Annotated[
        str,
        typer.Argument(help="Name of the plugin to show info for"),
    ],
    plugin_dirs: Annotated[
        list[str],
        typer.Option(
            "--dir",
            "-d",
            help="Additional plugin directories to search.",
        ),
    ] = [],
) -> None:
    """Show detailed information about a plugin."""
    from gridcode.plugins.discovery import PluginDiscovery

    # Collect directories to search
    search_dirs = _get_default_plugin_dirs()
    for d in plugin_dirs:
        path = Path(d)
        if path.exists():
            search_dirs.append(path)

    if not search_dirs:
        console.print(f"[red]Plugin not found: {plugin_name}[/red]")
        console.print("[dim]No plugin directories configured.[/dim]")
        raise typer.Exit(1)

    # Discover plugins
    discovery = PluginDiscovery(plugin_dirs=search_dirs)
    result = discovery.discover_from_directories()

    # Find the requested plugin
    found_plugin = None
    for plugin in result.plugins:
        if plugin.name == plugin_name:
            found_plugin = plugin
            break

    if found_plugin is None:
        console.print(f"[red]Plugin not found: {plugin_name}[/red]")
        raise typer.Exit(1)

    # Display plugin info
    console.print(f"\n[bold cyan]{found_plugin.name}[/bold cyan]")
    console.print(f"[dim]{'=' * len(found_plugin.name)}[/dim]\n")

    console.print(f"[bold]Version:[/bold] {getattr(found_plugin, 'version', '0.0.0')}")
    if hasattr(found_plugin, "description") and found_plugin.description:
        console.print(f"[bold]Description:[/bold] {found_plugin.description}")
    if hasattr(found_plugin, "plugin_type"):
        console.print(f"[bold]Type:[/bold] {found_plugin.plugin_type.value}")

    # Show source if available
    source = result.sources.get(found_plugin.name)
    if source:
        console.print(f"[bold]Source:[/bold] {source}")


@plugins_app.command()
def discover(
    plugin_dirs: Annotated[
        list[str],
        typer.Option(
            "--dir",
            "-d",
            help="Plugin directories to search.",
        ),
    ] = [],
    entry_points: Annotated[
        bool,
        typer.Option(
            "--entry-points",
            "-e",
            help="Also search for entry point plugins.",
        ),
    ] = False,
    output_format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format (table, json, yaml).",
        ),
    ] = "table",
) -> None:
    """Discover all available plugins from all sources."""
    import json

    import yaml as yaml_lib

    from gridcode.plugins.discovery import PluginDiscovery

    # Collect directories
    search_dirs = _get_default_plugin_dirs()
    for d in plugin_dirs:
        path = Path(d)
        if path.exists():
            search_dirs.append(path)

    # Discover from all sources
    all_plugins = []
    all_errors = []

    # From directories
    if search_dirs:
        discovery = PluginDiscovery(plugin_dirs=search_dirs)
        dir_result = discovery.discover_from_directories()
        all_plugins.extend(dir_result.plugins)
        all_errors.extend(dir_result.errors)

    # From entry points
    if entry_points:
        ep_discovery = PluginDiscovery()
        ep_result = ep_discovery.discover_from_entry_points()
        all_plugins.extend(ep_result.plugins)
        all_errors.extend(ep_result.errors)

    if not all_plugins:
        console.print("[dim]No plugins found.[/dim]")
        return

    # Output based on format
    if output_format == "json":
        data = [
            {
                "name": p.name,
                "version": getattr(p, "version", "0.0.0"),
                "description": getattr(p, "description", None),
                "type": p.plugin_type.value if hasattr(p, "plugin_type") else "general",
            }
            for p in all_plugins
        ]
        console.print(json.dumps(data, indent=2))

    elif output_format == "yaml":
        data = [
            {
                "name": p.name,
                "version": getattr(p, "version", "0.0.0"),
                "description": getattr(p, "description", None),
                "type": p.plugin_type.value if hasattr(p, "plugin_type") else "general",
            }
            for p in all_plugins
        ]
        console.print(yaml_lib.dump(data, default_flow_style=False))

    else:  # table
        table = Table(title="Discovered Plugins")
        table.add_column("Name", style="cyan")
        table.add_column("Version", style="green")
        table.add_column("Type")
        table.add_column("Description", style="dim")

        for plugin in all_plugins:
            table.add_row(
                plugin.name,
                getattr(plugin, "version", "0.0.0"),
                plugin.plugin_type.value if hasattr(plugin, "plugin_type") else "general",
                getattr(plugin, "description", "") or "",
            )

        console.print(table)

    console.print(f"\n[dim]Total: {len(all_plugins)} plugins[/dim]")

    # Show errors
    if all_errors:
        console.print("\n[yellow]Warnings:[/yellow]")
        for error in all_errors:
            console.print(f"  - {error}")


@plugins_app.command()
def create(
    name: Annotated[
        str,
        typer.Argument(help="Name for the new plugin"),
    ],
    output_dir: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Directory to create the plugin in.",
        ),
    ] = Path("./plugins"),
    with_hooks: Annotated[
        bool,
        typer.Option(
            "--hooks",
            help="Include hook examples in the plugin.",
        ),
    ] = False,
) -> None:
    """Create a new plugin from template.

    Creates a basic plugin structure with:
    - plugin.yaml configuration
    - Main plugin module
    - Optional hook examples
    """
    import textwrap

    plugin_dir = output_dir / name
    if plugin_dir.exists():
        console.print(f"[red]Directory already exists: {plugin_dir}[/red]")
        raise typer.Exit(1)

    # Create directory
    plugin_dir.mkdir(parents=True)

    # Create plugin.yaml
    plugin_yaml = {
        "name": name,
        "version": "0.1.0",
        "description": f"{name} plugin for GridCode",
        "module": f"{name}.plugin",
        "entry_point": "Plugin",
    }
    if with_hooks:
        plugin_yaml["hooks"] = ["pre_execute", "post_execute"]

    import yaml as yaml_lib

    with open(plugin_dir / "plugin.yaml", "w") as f:
        yaml_lib.dump(plugin_yaml, f, default_flow_style=False)

    # Create plugin module
    module_dir = plugin_dir / name
    module_dir.mkdir()

    # Create __init__.py
    with open(module_dir / "__init__.py", "w") as f:
        f.write(
            f'"""GridCode plugin: {name}."""\n\n'
            f"from {name}.plugin import Plugin\n\n"
            f'__all__ = ["Plugin"]\n'
        )

    # Create plugin.py
    plugin_code = textwrap.dedent(f'''
        """Main plugin implementation."""

        from gridcode.plugins.base import Plugin as BasePlugin


        class Plugin(BasePlugin):
            """Example GridCode plugin."""

            name = "{name}"
            version = "0.1.0"
            description = "{name} plugin for GridCode"

            async def on_load(self) -> None:
                """Called when the plugin is loaded."""
                self.logger.info(f"{{self.name}} plugin loaded")

            async def on_unload(self) -> None:
                """Called when the plugin is unloaded."""
                self.logger.info(f"{{self.name}} plugin unloaded")
    ''').strip()

    with open(module_dir / "plugin.py", "w") as f:
        f.write(plugin_code + "\n")

    console.print(f"[green]Created plugin: {plugin_dir}[/green]")
    console.print("\nFiles created:")
    console.print(f"  - {plugin_dir / 'plugin.yaml'}")
    console.print(f"  - {module_dir / '__init__.py'}")
    console.print(f"  - {module_dir / 'plugin.py'}")
    console.print("\nTo use the plugin:")
    console.print(f"  gridcode run --plugins {output_dir} 'your query'")
