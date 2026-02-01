"""GridCode CLI run command - Execute agent queries."""

import asyncio
import os
import uuid
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

run_app = typer.Typer(
    name="run",
    help="Execute GridCode agent queries",
    invoke_without_command=True,
)

console = Console()


def _get_api_key_from_config(
    config_path: Path | None = None,
) -> tuple[str | None, str, str | None, str | None]:
    """Get API key, provider, model, and template_dir from config or environment.

    Args:
        config_path: Optional path to config file (overrides search)

    Returns:
        Tuple of (api_key, provider, model, template_dir)
    """
    from gridcode.config.loader import ConfigManager

    try:
        config_mgr = ConfigManager()
        config = config_mgr.load_or_create(config_path=config_path, expand_env=True)

        # Get provider, key, model, and template_dir from config
        provider = config.runtime.api_provider
        api_key = config.runtime.api_key
        model = config.runtime.model
        template_dir = config.runtime.template_dir

        # If api_key still has ${...} pattern, try to get from env directly
        if api_key and api_key.startswith("${") and api_key.endswith("}"):
            env_var = api_key[2:-1]
            api_key = os.environ.get(env_var)

        # If model still has ${...} pattern, try to get from env directly
        if model and model.startswith("${") and model.endswith("}"):
            env_var = model[2:-1]
            env_model = os.environ.get(env_var)
            model = env_model if env_model else None

        return api_key, provider, model, template_dir
    except Exception:
        # Fallback: try common environment variables
        model = os.environ.get("OPENAI_MODEL_NAME")
        if openai_key := os.environ.get("OPENAI_API_KEY"):
            return openai_key, "openai", model, None
        if anthropic_key := os.environ.get("ANTHROPIC_API_KEY"):
            return anthropic_key, "anthropic", model, None
        return None, "openai", model, None


async def _run_query(
    query: str,
    api_key: str,
    api_provider: str,
    model: str | None,
    template_dir: Path | None,
    framework: str,
    working_dir: Path,
    plan_mode: bool,
    plugins: list[str],
    mcp_servers: list[str],
    stream: bool,
) -> None:
    """Execute the query with GridCode Runtime."""
    from gridcode import ExecutionContext, GridCodeRuntime
    from gridcode.interaction.console import ConsoleInteractionHandler

    # Initialize runtime
    console.print("[dim]Initializing GridCode Runtime...[/dim]")

    interaction = ConsoleInteractionHandler()
    runtime = await GridCodeRuntime.create(
        api_key=api_key,
        api_provider=api_provider,
        model=model,
        template_dir=template_dir,
        framework=framework,
        interaction=interaction,
    )

    # Create execution context with unique session ID
    context = ExecutionContext(
        session_id=str(uuid.uuid4()),
        working_dir=working_dir,
    )
    if plan_mode:
        context.is_plan_mode = True

    # Load plugins if specified
    if plugins:
        from gridcode.plugins.discovery import AutoPluginLoader, PluginDiscovery

        discovery = PluginDiscovery()
        loader = AutoPluginLoader(runtime.plugin_manager, discovery)

        for plugin_path in plugins:
            plugin_dir = Path(plugin_path)
            if plugin_dir.exists():
                loaded = await loader.load_from_directory(plugin_dir)
                console.print(f"[green]Loaded {len(loaded)} plugins from {plugin_path}[/green]")
            else:
                console.print(
                    f"[yellow]Warning: Plugin directory not found: {plugin_path}[/yellow]"
                )

    # Connect MCP servers if specified
    if mcp_servers:
        from gridcode.mcp.client import MCPServerConfig
        from gridcode.plugins.mcp import MultiMCPPlugin

        configs = []
        for server in mcp_servers:
            # Parse server spec: name or name:command
            if ":" in server:
                name, command = server.split(":", 1)
                configs.append(MCPServerConfig(name=name, command=command))
            else:
                # Default to npx @modelcontextprotocol/server-{name}
                configs.append(
                    MCPServerConfig(
                        name=server,
                        command="npx",
                        args=[f"@modelcontextprotocol/server-{server}"],
                    )
                )

        mcp_plugin = MultiMCPPlugin(configs=configs)
        runtime.plugin_manager.register_plugin(mcp_plugin)
        await runtime.plugin_manager.load_plugin(mcp_plugin.name)
        console.print(f"[green]Connected to {len(configs)} MCP servers[/green]")

    # Display query
    console.print(Panel(query, title="Query", border_style="blue"))

    # Execute query
    console.print("\n[dim]Processing...[/dim]\n")

    try:
        # Use execute_with_agents to enable tool usage and agent system
        # Register default tools: read, write, edit, glob, grep
        tool_names = ["read", "write", "edit", "glob", "grep"]

        if stream:
            # TODO: Implement streaming output with agents
            result = await runtime.execute_with_agents(
                query, context, tools=tool_names, auto_save=False
            )
        else:
            result = await runtime.execute_with_agents(
                query, context, tools=tool_names, auto_save=False
            )

        # Display result
        console.print(
            Panel(
                Markdown(result.output),
                title="Response",
                border_style="green",
            )
        )

        # Display metadata
        if result.metadata:
            usage = result.metadata.get("usage", {})
            console.print(
                f"\n[dim]Tokens: input={usage.get('input_tokens', 'N/A')}, "
                f"output={usage.get('output_tokens', 'N/A')}[/dim]"
            )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@run_app.callback(invoke_without_command=True)
def run(
    ctx: typer.Context,
    query: Annotated[
        str | None,
        typer.Argument(
            help="The query to execute. If not provided, enters interactive mode.",
        ),
    ] = None,
    plan: Annotated[
        bool,
        typer.Option(
            "--plan",
            "-p",
            help="Enable plan mode for complex tasks.",
        ),
    ] = False,
    framework: Annotated[
        str,
        typer.Option(
            "--framework",
            "-f",
            help="Agent framework to use.",
        ),
    ] = "langgraph",
    working_dir: Annotated[
        Path,
        typer.Option(
            "--working-dir",
            "-w",
            help="Working directory for file operations.",
        ),
    ] = Path("."),
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-c",
            help="Path to configuration file (default: search for gridcode.yaml).",
        ),
    ] = None,
    plugins: Annotated[
        list[str],
        typer.Option(
            "--plugins",
            help="Plugin directories to load.",
        ),
    ] = [],
    mcp: Annotated[
        list[str],
        typer.Option(
            "--mcp",
            help="MCP servers to connect (e.g., 'github', 'filesystem').",
        ),
    ] = [],
    stream: Annotated[
        bool,
        typer.Option(
            "--stream",
            "-s",
            help="Stream output as it's generated.",
        ),
    ] = False,
    api_key: Annotated[
        str | None,
        typer.Option(
            "--api-key",
            help="API key (overrides config and environment variables).",
        ),
    ] = None,
    provider: Annotated[
        str | None,
        typer.Option(
            "--provider",
            help="API provider: 'openai' or 'anthropic' (overrides config).",
        ),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option(
            "--model",
            "-m",
            help=(
                "Model name to use (e.g., 'gpt-4', 'claude-3-5-sonnet'). "
                "Overrides config and environment."
            ),
        ),
    ] = None,
) -> None:
    """Execute a query with the GridCode agent.

    Examples:

        gridcode run "Analyze this project's code structure"

        gridcode run --plan "Add user authentication"

        gridcode run --config custom.yaml "Use custom config file"

        gridcode run --mcp github "List open issues"

        gridcode run --plugins ./my-plugins "Use custom tools"

        gridcode run --provider openai --model gpt-4 "Use specific model"

        gridcode run --provider anthropic "Use Anthropic API"
    """
    # Handle case where subcommand was invoked without query
    if ctx.invoked_subcommand is not None:
        return

    # Get API key, provider, model, and template_dir from config or CLI
    config_key, config_provider, config_model, config_template_dir = _get_api_key_from_config(
        config_path=config
    )
    effective_api_key = api_key or config_key
    effective_provider = provider or config_provider
    effective_model = model or config_model  # CLI > config > env

    # Resolve template_dir: config > built-in templates
    effective_template_dir = None
    if config_template_dir:
        effective_template_dir = Path(config_template_dir)
    else:
        # Use built-in templates from package
        import gridcode.prompts

        package_path = Path(gridcode.prompts.__file__).parent
        builtin_templates = package_path / "templates"
        if builtin_templates.exists():
            effective_template_dir = builtin_templates

    if not effective_api_key:
        console.print("[red]Error: No API key provided.[/red]")
        console.print(
            "Please set the API key in one of these ways:\n"
            "  1. Set environment variable (OPENAI_API_KEY or ANTHROPIC_API_KEY)\n"
            "  2. Use --api-key option\n"
            "  3. Configure via: gridcode config set runtime.api_key <your-key>"
        )
        raise typer.Exit(1)

    # Show provider info
    console.print(f"[dim]Using API provider: {effective_provider}[/dim]")

    # Interactive mode if no query
    if query is None:
        from gridcode.cli.interactive import InteractiveSession

        # Create query handler that runs queries
        def handle_query(q: str) -> None:
            # Check for plan mode prefix
            is_plan = q.startswith("[PLAN MODE] ")
            if is_plan:
                q = q[12:]  # Remove prefix

            asyncio.run(
                _run_query(
                    query=q,
                    api_key=effective_api_key,
                    api_provider=effective_provider,
                    model=effective_model,
                    template_dir=effective_template_dir,
                    framework=framework,
                    working_dir=working_dir.resolve(),
                    plan_mode=plan or is_plan,
                    plugins=list(plugins),
                    mcp_servers=list(mcp),
                    stream=stream,
                )
            )

        # Run interactive session with enhanced features
        session = InteractiveSession(console=console)
        session.query_handler = handle_query
        session.run()
    else:
        # Single query mode
        asyncio.run(
            _run_query(
                query=query,
                api_key=effective_api_key,
                api_provider=effective_provider,
                model=effective_model,
                template_dir=effective_template_dir,
                framework=framework,
                working_dir=working_dir.resolve(),
                plan_mode=plan,
                plugins=list(plugins),
                mcp_servers=list(mcp),
                stream=stream,
            )
        )


@run_app.command()
def interactive(
    framework: Annotated[
        str,
        typer.Option(
            "--framework",
            "-f",
            help="Agent framework to use.",
        ),
    ] = "langgraph",
    working_dir: Annotated[
        Path,
        typer.Option(
            "--working-dir",
            "-w",
            help="Working directory for file operations.",
        ),
    ] = Path("."),
    api_key: Annotated[
        str | None,
        typer.Option(
            "--api-key",
            envvar="ANTHROPIC_API_KEY",
            help="Anthropic API key.",
        ),
    ] = None,
) -> None:
    """Start an interactive session.

    Enter queries interactively and get responses.
    Type 'exit' or 'quit' to end the session.
    """
    # Delegate to run with no query (interactive mode)
    ctx = typer.Context(run_app)
    run(
        ctx=ctx,
        query=None,
        plan=False,
        framework=framework,
        working_dir=working_dir,
        plugins=[],
        mcp=[],
        stream=False,
        api_key=api_key,
    )
