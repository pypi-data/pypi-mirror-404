"""Enhanced configuration validation with detailed error reporting."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from gridcode.config.models import GridCodeConfig


class ConfigValidationError(Exception):
    """Detailed configuration validation error with suggestions."""

    def __init__(
        self,
        message: str,
        field_path: str | None = None,
        error_type: str | None = None,
        suggestion: str | None = None,
        original_error: Exception | None = None,
    ):
        """Initialize validation error.

        Args:
            message: Error message
            field_path: Dot-notation field path (e.g., "runtime.api_key")
            error_type: Error type (e.g., "type_error", "value_error")
            suggestion: Suggested fix
            original_error: Original exception if any
        """
        self.message = message
        self.field_path = field_path
        self.error_type = error_type
        self.suggestion = suggestion
        self.original_error = original_error

        # Build full error message
        parts = [message]
        if field_path:
            parts.append(f"Field: {field_path}")
        if error_type:
            parts.append(f"Type: {error_type}")
        if suggestion:
            parts.append(f"Suggestion: {suggestion}")

        super().__init__("\n".join(parts))

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for structured output."""
        return {
            "message": self.message,
            "field": self.field_path,
            "type": self.error_type,
            "suggestion": self.suggestion,
        }


class ConfigValidator:
    """Enhanced configuration validator with detailed error reporting."""

    # Common error messages and suggestions
    SUGGESTIONS = {
        "api_key": (
            "Set your API key:\n"
            "  1. In config file: api_key: 'your-key-here'\n"
            "  2. Environment variable: export ANTHROPIC_API_KEY='your-key'\n"
            "  3. In config with variable: api_key: ${ANTHROPIC_API_KEY}"
        ),
        "api_provider": (
            "Valid API providers:\n"
            "  - openai: For OpenAI API\n"
            "  - anthropic: For Anthropic API (Claude)"
        ),
        "framework": (
            "Valid frameworks:\n"
            "  - langgraph: LangChain's LangGraph\n"
            "  - pydantic-ai: Pydantic AI framework"
        ),
        "log_level": (
            "Valid log levels:\n"
            "  - DEBUG: Most verbose\n"
            "  - INFO: Standard logging\n"
            "  - WARNING: Warnings only\n"
            "  - ERROR: Errors only\n"
            "  - CRITICAL: Critical errors only"
        ),
    }

    @staticmethod
    def validate_yaml_syntax(config_path: Path) -> dict[str, Any] | None:
        """Validate YAML syntax of configuration file.

        Args:
            config_path: Path to configuration file

        Returns:
            Dictionary with error details if syntax error, None if valid

        Raises:
            FileNotFoundError: If config file does not exist
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        try:
            with open(config_path, encoding="utf-8") as f:
                content = f.read()

            # Check for empty file
            if not content.strip():
                return {
                    "message": "Configuration file is empty",
                    "suggestion": ("Create a default configuration:\n" "  gridcode config init"),
                }

            # Try to parse YAML
            yaml.safe_load(content)
            return None

        except yaml.YAMLError as e:
            # Extract line and column information
            line = None
            column = None
            if hasattr(e, "problem_mark"):
                mark = e.problem_mark
                line = mark.line + 1  # Convert to 1-indexed
                column = mark.column + 1

            error_msg = str(e)
            location = f"Line {line}, Column {column}" if line else "Unknown location"

            return {
                "message": f"YAML syntax error at {location}",
                "error": error_msg,
                "suggestion": (
                    "Common YAML syntax issues:\n"
                    "  - Check indentation (use spaces, not tabs)\n"
                    "  - Ensure colons have space after them\n"
                    "  - Quote strings containing special characters\n"
                    "  - Check for unclosed brackets or quotes"
                ),
            }

    @staticmethod
    def validate_config_structure(
        config_data: dict[str, Any],
    ) -> list[ConfigValidationError]:
        """Validate configuration structure and values.

        Args:
            config_data: Configuration dictionary

        Returns:
            List of validation errors (empty if valid)
        """
        errors: list[ConfigValidationError] = []

        try:
            # Try to create GridCodeConfig from data
            GridCodeConfig(**config_data)
            return []

        except ValidationError as e:
            # Convert Pydantic errors to our detailed errors
            for error in e.errors():
                field_path = ".".join(str(loc) for loc in error["loc"])
                error_type = error["type"]
                message = error["msg"]

                # Get suggestion based on field
                suggestion = None
                for key, sug in ConfigValidator.SUGGESTIONS.items():
                    if key in field_path.lower():
                        suggestion = sug
                        break

                # Generate type-specific suggestions
                if error_type == "missing":
                    suggestion = f"Add required field '{field_path}' to your configuration"
                elif error_type in ("type_error.enum", "value_error"):
                    # Extract allowed values from error message if present
                    if "Input should be" in message:
                        suggestion = f"Check the value for '{field_path}'. {message}"

                errors.append(
                    ConfigValidationError(
                        message=message,
                        field_path=field_path,
                        error_type=error_type,
                        suggestion=suggestion,
                        original_error=e,
                    )
                )

            return errors

    @staticmethod
    def validate_config_completeness(config_data: dict[str, Any]) -> list[str]:
        """Check for missing critical configuration values.

        Args:
            config_data: Configuration dictionary

        Returns:
            List of warnings about missing values
        """
        warnings: list[str] = []

        # Check runtime configuration
        if "runtime" in config_data:
            runtime = config_data["runtime"]

            # Check API key
            if "api_key" not in runtime or not runtime.get("api_key"):
                warnings.append(
                    "Missing API key. Set ANTHROPIC_API_KEY environment variable "
                    "or configure runtime.api_key"
                )

            # Check API provider
            if "api_provider" not in runtime:
                warnings.append(
                    "Missing API provider. Set runtime.api_provider to 'openai' or 'anthropic'"
                )

        # Check MCP servers
        if "mcp" in config_data and config_data["mcp"].get("enabled"):
            mcp = config_data["mcp"]
            if "servers" not in mcp or not mcp["servers"]:
                warnings.append(
                    "MCP is enabled but no servers configured. "
                    "Add servers to mcp.servers or disable with mcp.enabled: false"
                )

        # Check plugin directories
        if "plugins" in config_data and config_data["plugins"].get("enabled"):
            plugins = config_data["plugins"]
            if "dirs" in plugins:
                for plugin_dir in plugins["dirs"]:
                    # Expand ~ to home directory
                    expanded_dir = Path(plugin_dir).expanduser()
                    if not expanded_dir.exists():
                        warnings.append(
                            f"Plugin directory does not exist: {plugin_dir}. "
                            f"Create it or remove from plugins.dirs"
                        )

        return warnings

    @staticmethod
    def validate_file(config_path: Path) -> tuple[bool, list[str], list[str]]:
        """Perform comprehensive validation of configuration file.

        Args:
            config_path: Path to configuration file

        Returns:
            Tuple of (is_valid, errors, warnings)
            - is_valid: Whether configuration is valid
            - errors: List of error messages
            - warnings: List of warning messages
        """
        errors: list[str] = []
        warnings: list[str] = []

        # 1. Check file exists
        if not config_path.exists():
            errors.append(f"Configuration file not found: {config_path}")
            return False, errors, warnings

        # 2. Validate YAML syntax
        syntax_error = ConfigValidator.validate_yaml_syntax(config_path)
        if syntax_error:
            errors.append(f"{syntax_error['message']}\n{syntax_error.get('suggestion', '')}")
            return False, errors, warnings

        # 3. Load configuration data
        try:
            with open(config_path, encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            if config_data is None:
                config_data = {}

        except Exception as e:
            errors.append(f"Failed to load configuration: {e}")
            return False, errors, warnings

        # 4. Validate structure and types
        validation_errors = ConfigValidator.validate_config_structure(config_data)
        if validation_errors:
            for err in validation_errors:
                error_msg = f"{err.message}"
                if err.field_path:
                    error_msg = f"[{err.field_path}] {error_msg}"
                if err.suggestion:
                    error_msg += f"\n  Suggestion: {err.suggestion}"
                errors.append(error_msg)

        # 5. Check completeness (warnings only)
        completeness_warnings = ConfigValidator.validate_config_completeness(config_data)
        warnings.extend(completeness_warnings)

        # Configuration is valid if no errors
        is_valid = len(errors) == 0

        return is_valid, errors, warnings
