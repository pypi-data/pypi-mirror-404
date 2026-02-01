"""Prompt composer for progressive prompt composition.

This module implements the progressive prompt composition pattern from Claude Code,
where prompts are layered based on task complexity and execution state.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any

from gridcode.prompts.template import PromptTemplate
from gridcode.prompts.variable_resolver import VariableResolver

if TYPE_CHECKING:
    from gridcode.prompts.reminders.base import ReminderRegistry


class PromptComposer:
    """Composes prompts progressively based on context and requirements.

    Features:
    - Template loading and caching
    - Variable resolution (static, context, function, ternary)
    - Multi-template composition
    - System reminder injection

    Example:
        composer = PromptComposer(template_dir=Path("templates"))

        # Basic composition
        prompt = composer.compose(["main_system", "task_execution"], static_vars={"name": "value"})

        # With reminders
        prompt = composer.compose_with_reminders(
            template_names=["main_system"],
            variables={},
            reminder_context={"is_plan_mode": True}
        )
    """

    def __init__(
        self,
        template_dir: Path | None = None,
        reminder_registry: "ReminderRegistry | None" = None,
    ):
        """Initialize the prompt composer.

        Args:
            template_dir: Directory containing prompt template files
            reminder_registry: Optional ReminderRegistry for system reminders.
                             If not provided, a default registry will be created lazily.
        """
        self.template_dir = template_dir
        self._templates: dict[str, PromptTemplate] = {}
        self._reminder_registry = reminder_registry
        self._default_registry_initialized = False

    @property
    def reminder_registry(self) -> "ReminderRegistry":
        """Get the reminder registry, creating a default one if needed."""
        if self._reminder_registry is None:
            from gridcode.prompts.reminders.base import create_default_registry

            self._reminder_registry = create_default_registry()
            self._default_registry_initialized = True
        return self._reminder_registry

    def load_template(self, name: str, file_path: Path | None = None) -> PromptTemplate:
        """Load a prompt template by name or file path.

        Args:
            name: Template name for caching
            file_path: Optional file path (uses template_dir if not provided)

        Returns:
            Loaded PromptTemplate

        Raises:
            FileNotFoundError: If template file not found
        """
        if name in self._templates:
            return self._templates[name]

        if file_path is None:
            if self.template_dir is None:
                raise ValueError("No template_dir configured")
            file_path = self.template_dir / f"{name}.md"

        if not file_path.exists():
            raise FileNotFoundError(f"Template file not found: {file_path}")

        template = PromptTemplate.from_file(file_path)
        self._templates[name] = template
        return template

    def compose(
        self,
        template_names: list[str],
        static_vars: dict[str, Any] | None = None,
        context: Any | None = None,
        functions: dict[str, Any] | None = None,
    ) -> str:
        """Compose multiple templates into a single prompt.

        Args:
            template_names: List of template names to compose
            static_vars: Static variables for resolution
            context: Context object for resolution
            functions: Functions for resolution

        Returns:
            Composed prompt string
        """
        resolver = VariableResolver(static_vars=static_vars, context=context, functions=functions)

        parts = []
        for name in template_names:
            template = self.load_template(name)
            resolved = resolver.resolve(template.content)
            parts.append(resolved)

        return "\n\n".join(parts)

    def compose_with_reminders(
        self,
        template_names: list[str],
        static_vars: dict[str, Any] | None = None,
        context: Any | None = None,
        functions: dict[str, Any] | None = None,
        reminder_context: dict[str, Any] | None = None,
    ) -> str:
        """Compose templates with system reminders injected.

        This method first composes the base prompt from templates,
        then appends any triggered system reminders based on the
        reminder_context.

        Args:
            template_names: List of template names to compose
            static_vars: Static variables for resolution
            context: Context object for resolution
            functions: Functions for resolution
            reminder_context: Context dict for triggering reminders.
                            Keys depend on registered reminders (e.g.,
                            "is_plan_mode", "file_empty", "tokens_used")

        Returns:
            Composed prompt string with reminders appended

        Example:
            prompt = composer.compose_with_reminders(
                template_names=["main_system"],
                static_vars={"project": "MyProject"},
                reminder_context={
                    "is_plan_mode": True,
                    "tokens_used": 8000,
                    "token_limit": 10000
                }
            )
        """
        # Compose base prompt
        base_prompt = self.compose(
            template_names=template_names,
            static_vars=static_vars,
            context=context,
            functions=functions,
        )

        # If no reminder context, return base prompt
        if not reminder_context:
            return base_prompt

        # Get triggered reminders
        reminders = self.reminder_registry.get_triggered_reminders(reminder_context)

        # Append reminders if any triggered
        if reminders:
            return base_prompt + "\n\n" + "\n\n".join(reminders)

        return base_prompt

    def compose_from_string(
        self,
        template_content: str,
        static_vars: dict[str, Any] | None = None,
        context: Any | None = None,
        functions: dict[str, Any] | None = None,
    ) -> str:
        """Compose a prompt from a template string.

        Args:
            template_content: Template content string
            static_vars: Static variables for resolution
            context: Context object for resolution
            functions: Functions for resolution

        Returns:
            Composed prompt string
        """
        template = PromptTemplate.from_string(template_content)
        resolver = VariableResolver(static_vars=static_vars, context=context, functions=functions)
        return resolver.resolve(template.content)

    def compose_from_strings(
        self,
        template_contents: list[str],
        static_vars: dict[str, Any] | None = None,
        context: Any | None = None,
        functions: dict[str, Any] | None = None,
    ) -> str:
        """Compose multiple templates from strings.

        Args:
            template_contents: List of template content strings
            static_vars: Static variables for resolution
            context: Context object for resolution
            functions: Functions for resolution

        Returns:
            Composed prompt string
        """
        resolver = VariableResolver(static_vars=static_vars, context=context, functions=functions)

        parts = []
        for content in template_contents:
            template = PromptTemplate.from_string(content)
            resolved = resolver.resolve(template.content)
            parts.append(resolved)

        return "\n\n".join(parts)

    def compose_from_string_with_reminders(
        self,
        template_content: str,
        static_vars: dict[str, Any] | None = None,
        context: Any | None = None,
        functions: dict[str, Any] | None = None,
        reminder_context: dict[str, Any] | None = None,
    ) -> str:
        """Compose a prompt from a template string with reminders.

        Args:
            template_content: Template content string
            static_vars: Static variables for resolution
            context: Context object for resolution
            functions: Functions for resolution
            reminder_context: Context dict for triggering reminders

        Returns:
            Composed prompt string with reminders appended
        """
        base_prompt = self.compose_from_string(
            template_content=template_content,
            static_vars=static_vars,
            context=context,
            functions=functions,
        )

        if not reminder_context:
            return base_prompt

        reminders = self.reminder_registry.get_triggered_reminders(reminder_context)

        if reminders:
            return base_prompt + "\n\n" + "\n\n".join(reminders)

        return base_prompt
