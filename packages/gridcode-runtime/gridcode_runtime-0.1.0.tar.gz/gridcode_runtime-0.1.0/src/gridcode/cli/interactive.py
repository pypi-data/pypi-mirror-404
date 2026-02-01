"""Interactive CLI session for GridCode Runtime.

Provides an enhanced interactive experience with:
- Command history (persistent across sessions)
- Auto-completion for commands and file paths
- Built-in slash commands (/help, /exit, /clear, etc.)
- Session context management
"""

from collections.abc import Callable
from pathlib import Path

from loguru import logger
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import NestedCompleter, PathCompleter, merge_completers
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel

# GridCode history file location
HISTORY_FILE = Path.home() / ".gridcode" / "history"


class SlashCommand:
    """Represents a slash command."""

    def __init__(
        self,
        name: str,
        description: str,
        handler: Callable[["InteractiveSession", list[str]], bool],
        aliases: list[str] | None = None,
    ):
        self.name = name
        self.description = description
        self.handler = handler
        self.aliases = aliases or []


class InteractiveSession:
    """Manages an interactive CLI session."""

    def __init__(
        self,
        console: Console | None = None,
        history_file: Path | None = None,
    ):
        """Initialize interactive session.

        Args:
            console: Rich console for output
            history_file: Path to history file (default: ~/.gridcode/history)
        """
        self.console = console or Console()
        self.history_file = history_file or HISTORY_FILE
        self.conversation_history: list[dict] = []
        self.running = True

        # Ensure history directory exists
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

        # Register slash commands
        self._commands: dict[str, SlashCommand] = {}
        self._register_default_commands()

        # Build completer
        self._completer = self._build_completer()

        # Create prompt session
        self._session = PromptSession(
            history=FileHistory(str(self.history_file)),
            auto_suggest=AutoSuggestFromHistory(),
            completer=self._completer,
            style=Style.from_dict(
                {
                    "prompt": "bold blue",
                }
            ),
        )

        # Query handler (set by caller)
        self.query_handler: Callable[[str], None] | None = None

    def _register_default_commands(self) -> None:
        """Register default slash commands."""
        self.register_command(
            SlashCommand(
                name="help",
                description="Show available commands",
                handler=self._cmd_help,
                aliases=["h", "?"],
            )
        )

        self.register_command(
            SlashCommand(
                name="exit",
                description="Exit interactive mode",
                handler=self._cmd_exit,
                aliases=["quit", "q"],
            )
        )

        self.register_command(
            SlashCommand(
                name="clear",
                description="Clear conversation history",
                handler=self._cmd_clear,
            )
        )

        self.register_command(
            SlashCommand(
                name="history",
                description="Show recent commands",
                handler=self._cmd_history,
            )
        )

        self.register_command(
            SlashCommand(
                name="plan",
                description="Enter plan mode for complex tasks",
                handler=self._cmd_plan,
            )
        )

        self.register_command(
            SlashCommand(
                name="context",
                description="Show current conversation context",
                handler=self._cmd_context,
            )
        )

    def register_command(self, command: SlashCommand) -> None:
        """Register a slash command."""
        self._commands[command.name] = command
        for alias in command.aliases:
            self._commands[alias] = command

    def _build_completer(self) -> NestedCompleter:
        """Build completer for commands and file paths."""
        # Command completions
        command_dict: dict = {}
        for name, cmd in self._commands.items():
            if name == cmd.name:  # Only add primary names, not aliases
                command_dict[f"/{name}"] = None

        # Add file path completion for certain commands
        path_completer = PathCompleter()

        # Build nested completer
        return merge_completers(
            [
                NestedCompleter.from_nested_dict(command_dict),
                path_completer,
            ]
        )

    def _cmd_help(self, args: list[str]) -> bool:
        """Show help for available commands."""
        self.console.print("\n[bold]Available Commands:[/bold]\n")

        # Group commands (skip aliases)
        seen = set()
        for name, cmd in sorted(self._commands.items()):
            if cmd.name in seen:
                continue
            seen.add(cmd.name)

            aliases = f" (aliases: {', '.join(cmd.aliases)})" if cmd.aliases else ""
            self.console.print(f"  [cyan]/{cmd.name}[/cyan]{aliases}")
            self.console.print(f"    {cmd.description}\n")

        self.console.print("[dim]Type your query and press Enter to execute.[/dim]\n")
        return True

    def _cmd_exit(self, args: list[str]) -> bool:
        """Exit interactive mode."""
        self.console.print("[dim]Goodbye![/dim]")
        self.running = False
        return False

    def _cmd_clear(self, args: list[str]) -> bool:
        """Clear conversation history."""
        self.conversation_history.clear()
        self.console.print("[green]Conversation history cleared.[/green]")
        return True

    def _cmd_history(self, args: list[str]) -> bool:
        """Show recent command history."""
        try:
            count = int(args[0]) if args else 10
        except ValueError:
            count = 10

        self.console.print(f"\n[bold]Recent Commands (last {count}):[/bold]\n")

        # Read history file
        if self.history_file.exists():
            lines = self.history_file.read_text().strip().split("\n")
            recent = lines[-count:] if len(lines) > count else lines
            for i, line in enumerate(recent, 1):
                # Skip comment lines (history file format)
                if not line.startswith("#"):
                    self.console.print(f"  {i}. {line}")
        else:
            self.console.print("  [dim]No history yet.[/dim]")

        self.console.print()
        return True

    def _cmd_plan(self, args: list[str]) -> bool:
        """Enter plan mode."""
        query = " ".join(args) if args else None
        if query:
            self.console.print(f"[bold blue]Entering plan mode for:[/bold blue] {query}")
            # Add plan mode flag to context
            self.conversation_history.append(
                {
                    "role": "system",
                    "content": "User requested plan mode for the following task.",
                }
            )
            # Execute query with plan mode
            if self.query_handler:
                self.query_handler(f"[PLAN MODE] {query}")
        else:
            self.console.print(
                "[yellow]Usage: /plan <task description>[/yellow]\n"
                "Example: /plan Add user authentication to the API"
            )
        return True

    def _cmd_context(self, args: list[str]) -> bool:
        """Show current conversation context."""
        self.console.print("\n[bold]Current Conversation Context:[/bold]\n")

        if not self.conversation_history:
            self.console.print("  [dim]No conversation history yet.[/dim]")
        else:
            for i, msg in enumerate(self.conversation_history[-5:], 1):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")[:100]
                self.console.print(f"  {i}. [{role}] {content}...")

        self.console.print(f"\n[dim]Total messages: {len(self.conversation_history)}[/dim]\n")
        return True

    def handle_input(self, text: str) -> bool:
        """Handle user input.

        Args:
            text: User input text

        Returns:
            True to continue, False to exit
        """
        text = text.strip()

        if not text:
            return True

        # Check for slash commands
        if text.startswith("/"):
            parts = text[1:].split()
            cmd_name = parts[0].lower()
            args = parts[1:]

            if cmd_name in self._commands:
                return self._commands[cmd_name].handler(args)
            else:
                self.console.print(f"[red]Unknown command: /{cmd_name}[/red]")
                self.console.print("[dim]Type /help for available commands.[/dim]")
                return True

        # Regular query - add to history and execute
        self.conversation_history.append(
            {
                "role": "user",
                "content": text,
            }
        )

        if self.query_handler:
            self.query_handler(text)

        return True

    def prompt(self) -> str:
        """Get input from user with prompt.

        Returns:
            User input text
        """
        return self._session.prompt(
            [("class:prompt", "> ")],
        )

    def run(self) -> None:
        """Run the interactive session loop."""
        self.console.print(
            Panel(
                "[bold]GridCode Interactive Mode[/bold]\n\n"
                "Type your query and press Enter to execute.\n"
                "Type [cyan]/help[/cyan] for available commands.\n"
                "Type [cyan]/exit[/cyan] or press Ctrl+D to quit.",
                border_style="blue",
            )
        )

        while self.running:
            try:
                text = self.prompt()
                self.handle_input(text)
            except KeyboardInterrupt:
                self.console.print("\n[dim]Use /exit or Ctrl+D to quit.[/dim]")
            except EOFError:
                self.console.print("\n[dim]Goodbye![/dim]")
                break
            except Exception as e:
                logger.exception("Error in interactive session")
                self.console.print(f"[red]Error: {e}[/red]")

    def add_response(self, content: str) -> None:
        """Add assistant response to conversation history.

        Args:
            content: Response content
        """
        self.conversation_history.append(
            {
                "role": "assistant",
                "content": content,
            }
        )


async def run_interactive_session(
    query_handler: Callable[[str], None],
    console: Console | None = None,
) -> None:
    """Run an interactive session with the given query handler.

    Args:
        query_handler: Function to handle user queries
        console: Rich console for output
    """
    session = InteractiveSession(console=console)
    session.query_handler = query_handler
    session.run()
