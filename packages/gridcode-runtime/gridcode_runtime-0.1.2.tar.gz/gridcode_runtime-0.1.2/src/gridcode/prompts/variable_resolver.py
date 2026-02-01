"""Variable resolution engine for prompt templates.

Supports multiple variable syntax patterns:
- ${VAR} - Static variable substitution
- ${context.property} - Dynamic context property access
- ${COND ? "A" : "B"} - Ternary conditional expressions
- ${FUNCTION()} - Function call expressions
"""

import re
from collections.abc import Callable
from typing import Any


class VariableResolver:
    """Resolves variables in prompt templates with multiple syntax support."""

    # Regex patterns for different variable types
    STATIC_VAR_PATTERN = re.compile(r"\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}")
    CONTEXT_VAR_PATTERN = re.compile(r"\$\{context\.([a-zA-Z_][a-zA-Z0-9_]*)\}")
    TERNARY_PATTERN = re.compile(r"\$\{([^?]+)\s*\?\s*\"([^\"]*)\"\s*:\s*\"([^\"]*)\"\}")
    FUNCTION_PATTERN = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)\(\)\}")

    def __init__(
        self,
        static_vars: dict[str, Any] | None = None,
        context: Any | None = None,
        functions: dict[str, Callable[[], str]] | None = None,
    ):
        """Initialize the variable resolver.

        Args:
            static_vars: Dictionary of static variables (e.g., {"API_KEY": "xxx"})
            context: Context object with properties accessible via ${context.property}
            functions: Dictionary of callable functions (e.g., {"GET_TIME": lambda: "12:00"})
        """
        self.static_vars = static_vars or {}
        self.context = context
        self.functions = functions or {}

    def resolve(self, template: str) -> str:
        """Resolve all variables in the template string.

        Args:
            template: Template string with variable placeholders

        Returns:
            Resolved string with all variables substituted

        Raises:
            ValueError: If a variable cannot be resolved
        """
        result = template

        # 1. Resolve ternary conditionals first (most complex)
        result = self._resolve_ternary(result)

        # 2. Resolve function calls
        result = self._resolve_functions(result)

        # 3. Resolve context properties
        result = self._resolve_context(result)

        # 4. Resolve static variables
        result = self._resolve_static(result)

        return result

    def _resolve_static(self, template: str) -> str:
        """Resolve static variables like ${VAR}."""

        def replacer(match: re.Match[str]) -> str:
            var_name = match.group(1)
            if var_name not in self.static_vars:
                raise ValueError(f"Static variable '{var_name}' not found")
            return str(self.static_vars[var_name])

        return self.STATIC_VAR_PATTERN.sub(replacer, template)

    def _resolve_context(self, template: str) -> str:
        """Resolve context properties like ${context.property}."""
        if self.context is None:
            return template

        def replacer(match: re.Match[str]) -> str:
            prop_name = match.group(1)
            if not hasattr(self.context, prop_name):
                raise ValueError(f"Context property '{prop_name}' not found")
            return str(getattr(self.context, prop_name))

        return self.CONTEXT_VAR_PATTERN.sub(replacer, template)

    def _resolve_functions(self, template: str) -> str:
        """Resolve function calls like ${FUNCTION()}."""

        def replacer(match: re.Match[str]) -> str:
            func_name = match.group(1)
            if func_name not in self.functions:
                raise ValueError(f"Function '{func_name}' not found")
            return str(self.functions[func_name]())

        return self.FUNCTION_PATTERN.sub(replacer, template)

    def _resolve_ternary(self, template: str) -> str:
        """Resolve ternary conditionals like ${COND ? "A" : "B"}."""

        def replacer(match: re.Match[str]) -> str:
            condition = match.group(1).strip()
            true_val = match.group(2)
            false_val = match.group(3)

            # Evaluate condition (simple truthy check)
            is_true = self._evaluate_condition(condition)
            return true_val if is_true else false_val

        return self.TERNARY_PATTERN.sub(replacer, template)

    def _evaluate_condition(self, condition: str) -> bool:
        """Evaluate a simple condition expression."""
        # Check if it's a static variable
        if condition in self.static_vars:
            return bool(self.static_vars[condition])

        # Check if it's a context property
        if condition.startswith("context."):
            prop_name = condition[8:]  # Remove "context."
            if self.context and hasattr(self.context, prop_name):
                return bool(getattr(self.context, prop_name))

        return False
