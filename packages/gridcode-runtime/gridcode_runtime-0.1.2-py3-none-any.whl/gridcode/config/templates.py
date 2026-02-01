"""Configuration templates management system."""

import os
import re
from pathlib import Path
from typing import Any

import yaml

from gridcode.config.models import GridCodeConfig


class EnvVarTemplate:
    """Represents an environment variable template."""

    def __init__(
        self,
        name: str,
        description: str,
        config_template_syntax: str,
    ):
        """Initialize environment variable template.

        Args:
            name: Variable name (e.g., GRIDCODE_API_KEY)
            description: Description of what this variable does
            config_template_syntax: Template syntax (e.g., ${GRIDCODE_API_KEY:-default})
        """
        self.name = name
        self.description = description
        self.config_template_syntax = config_template_syntax

    def is_set(self) -> bool:
        """Check if environment variable is set.

        Returns:
            True if variable is set in environment
        """
        return self.name in os.environ

    def get_value(self) -> str | None:
        """Get environment variable value.

        Returns:
            Value if set, None otherwise
        """
        return os.environ.get(self.name)


class EnvVarDocumentation:
    """Generate and manage environment variable documentation."""

    # Supported GRIDCODE_* environment variables
    GRIDCODE_ENV_VARS = {
        "GRIDCODE_API_KEY": EnvVarTemplate(
            name="GRIDCODE_API_KEY",
            description="API key for the configured provider (Anthropic or OpenAI)",
            config_template_syntax="runtime.api_key = ${GRIDCODE_API_KEY:-${ANTHROPIC_API_KEY}}",
        ),
        "GRIDCODE_MODEL": EnvVarTemplate(
            name="GRIDCODE_MODEL",
            description="Model to use (e.g., claude-sonnet-4-5, gpt-4)",
            config_template_syntax="runtime.model = ${GRIDCODE_MODEL:-claude-sonnet-4-5}",
        ),
        "GRIDCODE_FRAMEWORK": EnvVarTemplate(
            name="GRIDCODE_FRAMEWORK",
            description="Agent framework: 'langgraph' or 'pydantic-ai'",
            config_template_syntax="runtime.framework = ${GRIDCODE_FRAMEWORK:-langgraph}",
        ),
        "GRIDCODE_API_PROVIDER": EnvVarTemplate(
            name="GRIDCODE_API_PROVIDER",
            description="API provider: 'anthropic' or 'openai'",
            config_template_syntax="runtime.api_provider = ${GRIDCODE_API_PROVIDER:-anthropic}",
        ),
        "GRIDCODE_LOG_LEVEL": EnvVarTemplate(
            name="GRIDCODE_LOG_LEVEL",
            description="Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL",
            config_template_syntax="logging.level = ${GRIDCODE_LOG_LEVEL:-INFO}",
        ),
        "GRIDCODE_LOG_FORMAT": EnvVarTemplate(
            name="GRIDCODE_LOG_FORMAT",
            description="Log format: 'json' or 'text'",
            config_template_syntax="logging.format = ${GRIDCODE_LOG_FORMAT:-text}",
        ),
        "ANTHROPIC_API_KEY": EnvVarTemplate(
            name="ANTHROPIC_API_KEY",
            description="Anthropic API key",
            config_template_syntax="anthropic.api_key = ${ANTHROPIC_API_KEY}",
        ),
        "OPENAI_API_KEY": EnvVarTemplate(
            name="OPENAI_API_KEY",
            description="OpenAI API key",
            config_template_syntax="runtime.api_key = ${OPENAI_API_KEY}",
        ),
    }

    @staticmethod
    def generate_env_doc(template_name: str | None = None) -> str:
        """Generate environment variable documentation.

        Args:
            template_name: Optional specific template name to document

        Returns:
            Documentation string in markdown format
        """
        doc = "# GridCode Environment Variables\n\n"
        doc += "This document describes environment variables supported by GridCode.\n\n"

        doc += "## Configuration via Environment Variables\n\n"
        doc += "You can override configuration using `GRIDCODE_*` environment variables:\n\n"
        doc += "```bash\n"
        doc += "export GRIDCODE_API_KEY=your-api-key\n"
        doc += "export GRIDCODE_MODEL=claude-sonnet-4-5\n"
        doc += "export GRIDCODE_LOG_LEVEL=DEBUG\n"
        doc += 'gridcode run "your query"\n'
        doc += "```\n\n"

        doc += "## Supported Environment Variables\n\n"
        doc += "| Variable | Description | Priority |\n"
        doc += "|----------|-------------|----------|\n"

        for var_name, var_info in EnvVarDocumentation.GRIDCODE_ENV_VARS.items():
            doc += f"| `{var_name}` | {var_info.description} | CLI > Config > Default |\n"

        doc += "\n## .env File Support\n\n"
        doc += (
            "GridCode automatically loads environment variables from `.env` files. "
            "The following files are supported:\n\n"
        )
        doc += "- `.env` - Base environment file\n"
        doc += "- `.env.local` - Local environment overrides (not tracked in git)\n"
        doc += "- `.env.production` - Production environment variables\n"
        doc += "- `.env.development` - Development environment variables\n\n"

        doc += "### Example .env file:\n\n"
        doc += "```bash\n"
        doc += "ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx\n"
        doc += "GRIDCODE_MODEL=claude-opus-4-5\n"
        doc += "GRIDCODE_LOG_LEVEL=DEBUG\n"
        doc += "```\n\n"

        doc += "## Configuration Priority\n\n"
        doc += "Configuration values are loaded in this order (highest to lowest priority):\n\n"
        doc += "1. **CLI parameters** (e.g., `GRIDCODE_API_KEY` environment variable)\n"
        doc += "2. **Environment variables** (e.g., `GRIDCODE_API_KEY`)\n"
        doc += "3. **Configuration file** (e.g., `.env`, `gridcode.yaml`)\n"
        doc += "4. **Default values**\n\n"

        return doc

    @staticmethod
    def extract_env_vars_from_config(config_data: dict[str, Any]) -> list[str]:
        """Extract environment variable references from config data.

        Returns list of environment variable names referenced in config.

        Args:
            config_data: Configuration dictionary

        Returns:
            List of environment variable names (e.g., ['ANTHROPIC_API_KEY', ...])
        """
        env_vars = []
        pattern = r"\$\{([A-Z_][A-Z0-9_]*)"

        def extract_from_value(value: Any) -> None:
            if isinstance(value, str):
                matches = re.findall(pattern, value)
                env_vars.extend(matches)
            elif isinstance(value, dict):
                for v in value.values():
                    extract_from_value(v)
            elif isinstance(value, list):
                for item in value:
                    extract_from_value(item)

        extract_from_value(config_data)
        return sorted(set(env_vars))

    @staticmethod
    def validate_env_vars(
        config_data: dict[str, Any],
        required_only: bool = False,
    ) -> dict[str, bool]:
        """Validate that required environment variables are set.

        Args:
            config_data: Configuration dictionary
            required_only: Only check variables without default values

        Returns:
            Dictionary mapping variable names to availability status
        """
        env_vars = EnvVarDocumentation.extract_env_vars_from_config(config_data)
        result = {}

        for var_name in env_vars:
            is_set = var_name in os.environ
            result[var_name] = is_set

        return result


class ConfigTemplate:
    """Represents a configuration template."""

    def __init__(
        self,
        name: str,
        description: str,
        config_data: dict[str, Any],
    ):
        """Initialize template.

        Args:
            name: Template name (e.g., "production", "development")
            description: Template description
            config_data: Configuration dictionary
        """
        self.name = name
        self.description = description
        self.config_data = config_data

    def to_yaml(self) -> str:
        """Convert template to YAML string.

        Returns:
            YAML representation of template
        """
        result = yaml.dump(self.config_data, default_flow_style=False, sort_keys=False)
        return result if isinstance(result, str) else ""

    def validate(self) -> bool:
        """Validate template configuration.

        Returns:
            True if valid, False otherwise
        """
        try:
            GridCodeConfig(**self.config_data)
            return True
        except Exception:
            return False


class ConfigTemplateManager:
    """Manage configuration templates."""

    # Built-in templates
    BUILT_IN_TEMPLATES = {
        "default": {
            "description": "Default configuration with all features",
            "data": {
                "runtime": {
                    "api_provider": "anthropic",
                    "api_key": "${ANTHROPIC_API_KEY}",
                    "model": "claude-sonnet-4-5",
                    "framework": "langgraph",
                    "working_dir": ".",
                },
                "anthropic": {
                    "api_key": "${ANTHROPIC_API_KEY}",
                    "model": "claude-sonnet-4-5",
                    "max_tokens": 4000,
                    "temperature": 0.7,
                },
                "agent_pool": {
                    "max_agents": 5,
                    "cache_enabled": True,
                },
                "mcp": {
                    "enabled": True,
                    "servers": [],
                },
                "plugins": {
                    "enabled": True,
                    "dirs": ["~/.gridcode/plugins", "./plugins"],
                },
                "logging": {
                    "level": "INFO",
                    "format": "text",
                    "colored": True,
                },
                "workflows": {
                    "plan_mode": {"enabled": True},
                    "learning_mode": {"enabled": False},
                },
            },
        },
        "development": {
            "description": "Development configuration with verbose logging",
            "data": {
                "runtime": {
                    "api_provider": "anthropic",
                    "api_key": "${ANTHROPIC_API_KEY}",
                    "model": "claude-sonnet-4-5",
                    "framework": "langgraph",
                    "working_dir": ".",
                },
                "logging": {
                    "level": "DEBUG",
                    "format": "text",
                    "colored": True,
                },
                "agent_pool": {
                    "max_agents": 3,
                    "cache_enabled": False,
                },
                "workflows": {
                    "plan_mode": {"enabled": True},
                    "learning_mode": {"enabled": True},
                },
            },
        },
        "production": {
            "description": "Production configuration with optimized settings",
            "data": {
                "runtime": {
                    "api_provider": "anthropic",
                    "api_key": "${ANTHROPIC_API_KEY}",
                    "model": "claude-opus-4-5",
                    "framework": "langgraph",
                    "working_dir": ".",
                },
                "logging": {
                    "level": "WARNING",
                    "format": "json",
                    "file": "/var/log/gridcode/runtime.log",
                    "colored": False,
                },
                "agent_pool": {
                    "max_agents": 10,
                    "cache_enabled": True,
                    "cache_ttl": 7200,
                },
                "performance": {
                    "lazy_loading": True,
                    "connection_pooling": True,
                },
                "workflows": {
                    "plan_mode": {"enabled": True},
                    "learning_mode": {"enabled": False},
                },
            },
        },
        "testing": {
            "description": "Testing configuration with minimal overhead",
            "data": {
                "runtime": {
                    "api_provider": "anthropic",
                    "api_key": "${ANTHROPIC_API_KEY}",
                    "model": "claude-sonnet-4-5",
                    "framework": "langgraph",
                },
                "logging": {
                    "level": "ERROR",
                    "format": "text",
                },
                "agent_pool": {
                    "max_agents": 1,
                    "cache_enabled": False,
                },
                "mcp": {
                    "enabled": False,
                },
                "plugins": {
                    "enabled": False,
                },
                "workflows": {
                    "plan_mode": {"enabled": False},
                    "learning_mode": {"enabled": False},
                },
            },
        },
        "minimal": {
            "description": "Minimal configuration with only required settings",
            "data": {
                "runtime": {
                    "api_provider": "anthropic",
                    "api_key": "${ANTHROPIC_API_KEY}",
                    "model": "claude-sonnet-4-5",
                    "framework": "langgraph",
                },
            },
        },
        "openai": {
            "description": "OpenAI API configuration",
            "data": {
                "runtime": {
                    "api_provider": "openai",
                    "api_key": "${OPENAI_API_KEY}",
                    "model": "gpt-4",
                    "framework": "langgraph",
                },
                "logging": {
                    "level": "INFO",
                    "format": "text",
                },
            },
        },
    }

    def __init__(self, custom_template_dir: Path | None = None):
        """Initialize template manager.

        Args:
            custom_template_dir: Directory for custom templates
        """
        self.custom_template_dir = custom_template_dir or (Path.home() / ".gridcode" / "templates")
        self.templates: dict[str, ConfigTemplate] = {}
        self._load_built_in_templates()

    def _load_built_in_templates(self) -> None:
        """Load built-in templates."""
        import copy

        for name, info in self.BUILT_IN_TEMPLATES.items():
            template = ConfigTemplate(
                name=name,
                description=info["description"],
                config_data=copy.deepcopy(info["data"]),
            )
            self.templates[name] = template

    def load_custom_templates(self) -> None:
        """Load custom templates from custom template directory."""
        if not self.custom_template_dir.exists():
            return

        for template_file in self.custom_template_dir.glob("*.yaml"):
            name = template_file.stem
            if name in self.templates:
                continue  # Skip if name conflicts with built-in

            try:
                with open(template_file, encoding="utf-8") as f:
                    config_data = yaml.safe_load(f)

                if config_data is None:
                    continue

                # Extract description from file if available
                description = f"Custom template from {template_file.name}"

                template = ConfigTemplate(
                    name=name,
                    description=description,
                    config_data=config_data,
                )

                if template.validate():
                    self.templates[name] = template

            except Exception:
                # Skip invalid template files
                continue

    def get_template(self, name: str) -> ConfigTemplate | None:
        """Get a template by name.

        Args:
            name: Template name

        Returns:
            Template if found, None otherwise
        """
        return self.templates.get(name)

    def list_templates(self) -> dict[str, tuple[str, bool]]:
        """List all available templates.

        Returns:
            Dictionary mapping template name to (description, is_built_in)
        """
        result = {}
        for name, template in self.templates.items():
            is_built_in = name in self.BUILT_IN_TEMPLATES
            result[name] = (template.description, is_built_in)
        return result

    def create_config_from_template(
        self,
        template_name: str,
        output_path: Path,
        merge_data: dict[str, Any] | None = None,
    ) -> bool:
        """Create a configuration file from a template.

        Args:
            template_name: Name of the template to use
            output_path: Path where to save the configuration
            merge_data: Additional data to merge into template

        Returns:
            True if successful, False otherwise
        """
        template = self.get_template(template_name)
        if template is None:
            return False

        # Prepare config data
        config_data = template.config_data.copy()

        # Merge additional data if provided
        if merge_data:
            self._deep_merge(config_data, merge_data)

        # Create parent directories if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

        return True

    def export_template(
        self,
        name: str,
        output_path: Path,
    ) -> bool:
        """Export a template to a file.

        Args:
            name: Template name
            output_path: Path where to save the template

        Returns:
            True if successful, False otherwise
        """
        return self.create_config_from_template(name, output_path)

    @staticmethod
    def _deep_merge(
        base: dict[str, Any],
        updates: dict[str, Any],
    ) -> None:
        """Deep merge updates into base dictionary.

        Args:
            base: Base dictionary (modified in place)
            updates: Dictionary to merge
        """
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                ConfigTemplateManager._deep_merge(base[key], value)
            else:
                base[key] = value

    def generate_env_doc_for_template(self, template_name: str) -> str | None:
        """Generate environment variable documentation for a template.

        Args:
            template_name: Name of the template

        Returns:
            Environment variable documentation or None if template not found
        """
        template = self.get_template(template_name)
        if template is None:
            return None

        env_vars = EnvVarDocumentation.extract_env_vars_from_config(template.config_data)
        if not env_vars:
            return "No environment variables needed for this template."

        doc = f"# Environment Variables for '{template_name}' Template\n\n"
        doc += f"Template: {template.description}\n\n"
        doc += "## Required Environment Variables\n\n"
        doc += "| Variable | Description | Currently Set |\n"
        doc += "|----------|-------------|----------------|\n"

        for var_name in env_vars:
            var_info = EnvVarDocumentation.GRIDCODE_ENV_VARS.get(var_name)
            if var_info:
                description = var_info.description
            else:
                description = "Custom environment variable"

            is_set = var_name in os.environ
            status = "✓ Yes" if is_set else "✗ No"

            doc += f"| `{var_name}` | {description} | {status} |\n"

        doc += "\n## Setup Instructions\n\n"
        doc += "Create a `.env` file with the required variables:\n\n"
        doc += "```bash\n"
        for var_name in env_vars:
            var_info = EnvVarDocumentation.GRIDCODE_ENV_VARS.get(var_name)
            if var_info:
                doc += f"{var_name}=your-value  # {var_info.description}\n"
            else:
                doc += f"{var_name}=your-value\n"
        doc += "```\n"

        return doc
