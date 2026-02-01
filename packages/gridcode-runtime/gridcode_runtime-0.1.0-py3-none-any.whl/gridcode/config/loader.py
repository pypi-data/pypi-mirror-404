"""Configuration loading and management system."""

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import ValidationError

from gridcode.config.models import GridCodeConfig


class EnvFileDiscovery:
    """Discover and load .env files for configuration."""

    ENV_FILE_NAMES = [".env", ".env.local", ".env.production", ".env.development"]

    @staticmethod
    def find_env_files(
        start_dir: Path | None = None,
        check_home: bool = True,
    ) -> list[Path]:
        """Find .env files by searching up directory tree.

        Search order:
        1. Current directory and parents (.env, .env.local, etc.)
        2. User home directory (~/.gridcode/.env, etc.)

        Args:
            start_dir: Directory to start search from (default: current)
            check_home: Whether to check user home directory

        Returns:
            List of found .env files in order of priority
        """
        env_files = []
        search_dir = start_dir or Path.cwd()
        current = search_dir.resolve()

        # Search up directory tree for .env files
        while current != current.parent:
            for env_name in EnvFileDiscovery.ENV_FILE_NAMES:
                env_path = current / env_name
                if env_path.exists() and env_path not in env_files:
                    env_files.append(env_path)
            current = current.parent

        # Check user config directory
        if check_home:
            gridcode_home = Path.home() / ".gridcode"
            for env_name in EnvFileDiscovery.ENV_FILE_NAMES:
                env_path = gridcode_home / env_name
                if env_path.exists() and env_path not in env_files:
                    env_files.append(env_path)

        return env_files

    @staticmethod
    def load_env_files(env_files: list[Path]) -> dict[str, str]:
        """Load environment variables from .env files.

        Args:
            env_files: List of .env file paths to load

        Returns:
            Dictionary of loaded environment variables
        """
        loaded_vars: dict[str, str] = {}
        for env_file in env_files:
            if env_file.exists():
                # Use dotenv to load the file
                vars_dict = load_dotenv(env_file, override=False, verbose=False)
                # dotenv returns True on success, False otherwise
                # Get the actually loaded vars from os.environ
                if vars_dict is not False:
                    loaded_vars.update(os.environ)
        return loaded_vars


class ConfigLoader:
    """Load and validate configuration from YAML files."""

    DEFAULT_CONFIG_NAME = "gridcode.yaml"

    @staticmethod
    def load_yaml(config_path: Path) -> dict[str, Any]:
        """Load raw YAML configuration from file.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            Dictionary containing raw YAML data

        Raises:
            FileNotFoundError: If config file does not exist
            yaml.YAMLError: If YAML is malformed
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, encoding="utf-8") as f:
            content = f.read()

        # Handle empty files
        if not content.strip():
            return {}

        return yaml.safe_load(content) or {}

    @staticmethod
    def save_yaml(config_path: Path, data: dict[str, Any]) -> None:
        """Save configuration to YAML file.

        Args:
            config_path: Path to YAML configuration file
            data: Dictionary to save as YAML

        Raises:
            IOError: If file cannot be written
        """
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    @staticmethod
    def expand_env_vars(obj: Any) -> Any:
        """Recursively expand environment variables in configuration.

        Supports both ${VAR_NAME} and ${VAR_NAME:-default} syntax.

        Args:
            obj: Object to expand (dict, list, str, or other)

        Returns:
            Object with environment variables expanded
        """
        if isinstance(obj, str):
            if obj.startswith("${") and obj.endswith("}"):
                var_expr = obj[2:-1]

                # Check for default value syntax: ${VAR:-default}
                if ":-" in var_expr:
                    var_name, default_value = var_expr.split(":-", 1)
                    return os.environ.get(var_name, default_value)
                else:
                    # Simple ${VAR} syntax - return as-is if not found
                    return os.environ.get(var_expr, obj)
            return obj
        elif isinstance(obj, dict):
            return {k: ConfigLoader.expand_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [ConfigLoader.expand_env_vars(item) for item in obj]
        return obj

    @staticmethod
    def load(config_path: Path, expand_env: bool = True) -> GridCodeConfig:
        """Load and validate configuration from YAML file.

        Args:
            config_path: Path to configuration file
            expand_env: Whether to expand environment variables

        Returns:
            Validated GridCodeConfig object

        Raises:
            FileNotFoundError: If config file does not exist
            yaml.YAMLError: If YAML is malformed
            ValidationError: If configuration is invalid
        """
        raw_config = ConfigLoader.load_yaml(config_path)

        # Expand environment variables if requested
        if expand_env:
            raw_config = ConfigLoader.expand_env_vars(raw_config)

        # Validate with Pydantic
        try:
            return GridCodeConfig(**raw_config)
        except ValidationError as e:
            # Re-raise with context
            raise ValidationError.from_exception_data(
                title="GridCodeConfig",
                line_errors=e.errors(),
            ) from e

    @staticmethod
    def extract_gridcode_env_vars() -> dict[str, Any]:
        """Extract GRIDCODE_* environment variables for config override.

        Supports mapping like:
        - GRIDCODE_API_KEY -> runtime.api_key
        - GRIDCODE_MODEL -> runtime.model
        - GRIDCODE_LOG_LEVEL -> logging.level
        - GRIDCODE_FRAMEWORK -> runtime.framework

        Returns:
            Dictionary with nested config structure for overrides
        """
        env_config: dict[str, Any] = {}
        prefix = "GRIDCODE_"

        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove prefix and convert to lowercase
                config_key = key[len(prefix) :].lower()

                # Map specific environment variables to config paths
                if config_key == "api_key":
                    if "runtime" not in env_config:
                        env_config["runtime"] = {}
                    env_config["runtime"]["api_key"] = value
                elif config_key == "model":
                    if "runtime" not in env_config:
                        env_config["runtime"] = {}
                    env_config["runtime"]["model"] = value
                elif config_key == "framework":
                    if "runtime" not in env_config:
                        env_config["runtime"] = {}
                    env_config["runtime"]["framework"] = value
                elif config_key == "api_provider":
                    if "runtime" not in env_config:
                        env_config["runtime"] = {}
                    env_config["runtime"]["api_provider"] = value
                elif config_key == "log_level":
                    if "logging" not in env_config:
                        env_config["logging"] = {}
                    env_config["logging"]["level"] = value
                elif config_key == "log_format":
                    if "logging" not in env_config:
                        env_config["logging"] = {}
                    env_config["logging"]["format"] = value
                elif config_key.startswith("anthropic_"):
                    section_key = config_key[len("anthropic_") :]
                    if "anthropic" not in env_config:
                        env_config["anthropic"] = {}
                    env_config["anthropic"][section_key] = value

        return env_config

    @staticmethod
    def merge_configs(
        base_config: dict[str, Any],
        override_config: dict[str, Any],
    ) -> dict[str, Any]:
        """Deep merge override_config into base_config.

        Args:
            base_config: Base configuration dictionary
            override_config: Configuration to merge (takes priority)

        Returns:
            Merged configuration dictionary
        """
        result = base_config.copy()

        for key, value in override_config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ConfigLoader.merge_configs(result[key], value)
            else:
                result[key] = value

        return result


class ConfigManager:
    """Manage configuration with search paths and defaults."""

    DEFAULT_CONFIG_NAME = "gridcode.yaml"

    def __init__(self):
        """Initialize configuration manager."""
        self._config: GridCodeConfig | None = None
        self._config_path: Path | None = None
        self._env_files_loaded: list[Path] = []
        self._config_sources: dict[str, str] = {}

    @property
    def config(self) -> GridCodeConfig:
        """Get current configuration (lazy load)."""
        if self._config is None:
            raise RuntimeError("Configuration not loaded. Call load() or load_or_create() first.")
        return self._config

    @property
    def config_path(self) -> Path | None:
        """Get path to loaded configuration file."""
        return self._config_path

    @property
    def env_files_loaded(self) -> list[Path]:
        """Get list of .env files that were loaded."""
        return self._env_files_loaded

    def get_config_source(self, key: str) -> str:
        """Get source of a configuration value.

        Args:
            key: Configuration key

        Returns:
            Source of the value (e.g., "config_file", "environment", "default")
        """
        return self._config_sources.get(key, "unknown")

    def find_config_file(
        self,
        start_dir: Path | None = None,
        check_home: bool = True,
    ) -> Path | None:
        """Find configuration file by searching up directory tree.

        Search order:
        1. Current directory and parents
        2. User home directory (~/.config/gridcode/gridcode.yaml)

        Args:
            start_dir: Directory to start search from (default: current)
            check_home: Whether to check user home directory

        Returns:
            Path to configuration file if found, None otherwise
        """
        search_dir = start_dir or Path.cwd()
        current = search_dir.resolve()

        # Search up directory tree
        while current != current.parent:
            config_path = current / self.DEFAULT_CONFIG_NAME
            if config_path.exists():
                return config_path
            current = current.parent

        # Check user config directory
        if check_home:
            user_config = Path.home() / ".config" / "gridcode" / self.DEFAULT_CONFIG_NAME
            if user_config.exists():
                return user_config

        return None

    def load(
        self,
        config_path: Path | None = None,
        expand_env: bool = True,
        load_env_files: bool = True,
        apply_env_overrides: bool = True,
    ) -> GridCodeConfig:
        """Load configuration from file.

        Priority order (highest to lowest):
        1. GRIDCODE_* environment variables (if apply_env_overrides=True)
        2. Configuration file values
        3. Default values

        Args:
            config_path: Path to configuration file. If None, searches for it.
            expand_env: Whether to expand environment variables in config
            load_env_files: Whether to auto-load .env files
            apply_env_overrides: Whether to apply GRIDCODE_* env var overrides

        Returns:
            Loaded and validated configuration

        Raises:
            FileNotFoundError: If no configuration file found
            yaml.YAMLError: If YAML is malformed
            ValidationError: If configuration is invalid
        """
        # Load .env files first if requested
        if load_env_files:
            env_search_dir = None
            if config_path:
                env_search_dir = config_path.parent
            self._env_files_loaded = EnvFileDiscovery.find_env_files(start_dir=env_search_dir)
            for env_file in self._env_files_loaded:
                load_dotenv(env_file, override=False, verbose=False)

        # Determine config path
        if config_path is None:
            config_path = self.find_config_file()
            if config_path is None:
                raise FileNotFoundError(
                    "No configuration file found. Searched locations:\n"
                    f"  - {Path.cwd() / self.DEFAULT_CONFIG_NAME}\n"
                    f"  - {Path.home() / '.config' / 'gridcode' / self.DEFAULT_CONFIG_NAME}"
                )

        # Load base configuration from file
        raw_config = ConfigLoader.load_yaml(config_path)

        # Expand environment variables if requested
        if expand_env:
            raw_config = ConfigLoader.expand_env_vars(raw_config)

        # Apply GRIDCODE_* environment variable overrides
        if apply_env_overrides:
            env_overrides = ConfigLoader.extract_gridcode_env_vars()
            if env_overrides:
                raw_config = ConfigLoader.merge_configs(raw_config, env_overrides)

        # Validate with Pydantic
        self._config = GridCodeConfig(**raw_config)
        self._config_path = config_path
        return self._config

    def load_config(
        self,
        config_path: str | Path | None = None,
        search_path: str | Path | None = None,
        expand_env: bool = True,
        load_env_files: bool = True,
        apply_env_overrides: bool = True,
    ) -> GridCodeConfig:
        """Load configuration from file with search support.

        This is an alias for load() with additional search_path parameter
        for test compatibility.

        Args:
            config_path: Path to configuration file. If None, searches for it.
            search_path: Directory to start search from (if config_path is None)
            expand_env: Whether to expand environment variables
            load_env_files: Whether to auto-load .env files
            apply_env_overrides: Whether to apply GRIDCODE_* env var overrides

        Returns:
            Loaded and validated configuration

        Raises:
            FileNotFoundError: If no configuration file found
            yaml.YAMLError: If YAML is malformed
            ValidationError: If configuration is invalid
        """
        # Convert string paths to Path objects
        if config_path is not None:
            config_path = Path(config_path) if isinstance(config_path, str) else config_path

        if search_path is not None:
            search_path = Path(search_path) if isinstance(search_path, str) else search_path

        # Load .env files first if requested
        if load_env_files:
            self._env_files_loaded = EnvFileDiscovery.find_env_files(start_dir=search_path)
            for env_file in self._env_files_loaded:
                load_dotenv(env_file, override=False, verbose=False)

        # If no config_path specified, search from search_path or current dir
        if config_path is None:
            config_path = self.find_config_file(start_dir=search_path)
            if config_path is None:
                # Use default configuration instead of raising error
                # This matches test expectations
                self._config = GridCodeConfig.default()
                self._config_path = None
                return self._config

        # Load base configuration
        raw_config = ConfigLoader.load_yaml(config_path)

        # Expand environment variables if requested
        if expand_env:
            raw_config = ConfigLoader.expand_env_vars(raw_config)

        # Apply GRIDCODE_* environment variable overrides
        if apply_env_overrides:
            env_overrides = ConfigLoader.extract_gridcode_env_vars()
            if env_overrides:
                raw_config = ConfigLoader.merge_configs(raw_config, env_overrides)

        # Validate with Pydantic
        self._config = GridCodeConfig(**raw_config)
        self._config_path = config_path
        return self._config

    def load_or_create(
        self,
        config_path: Path | None = None,
        expand_env: bool = True,
        load_env_files: bool = True,
        apply_env_overrides: bool = True,
    ) -> GridCodeConfig:
        """Load configuration or create default if not found.

        Args:
            config_path: Path to configuration file
            expand_env: Whether to expand environment variables
            load_env_files: Whether to auto-load .env files
            apply_env_overrides: Whether to apply GRIDCODE_* env var overrides

        Returns:
            Loaded configuration or default configuration
        """
        try:
            return self.load(
                config_path=config_path,
                expand_env=expand_env,
                load_env_files=load_env_files,
                apply_env_overrides=apply_env_overrides,
            )
        except FileNotFoundError:
            # Use default configuration
            self._config = GridCodeConfig.default()
            self._config_path = None
            return self._config

    def create_default_config(
        self,
        config_path: Path | None = None,
        force: bool = False,
    ) -> Path:
        """Create default configuration file.

        Args:
            config_path: Path where to create config file.
                         If None, uses ~/.config/gridcode/gridcode.yaml
            force: Whether to overwrite existing file

        Returns:
            Path to created configuration file

        Raises:
            FileExistsError: If file exists and force=False
        """
        if config_path is None:
            config_path = Path.home() / ".config" / "gridcode" / self.DEFAULT_CONFIG_NAME

        if config_path.exists() and not force:
            raise FileExistsError(
                f"Configuration file already exists: {config_path}. " "Use force=True to overwrite."
            )

        # Create default config
        default_config = GridCodeConfig.default()

        # Convert to dict for YAML serialization
        config_dict = default_config.model_dump(exclude_none=False)

        # Save to file
        ConfigLoader.save_yaml(config_path, config_dict)

        self._config = default_config
        self._config_path = config_path
        return config_path

    def get_config_locations(self) -> dict[str, Path | None]:
        """Get all possible configuration locations.

        Returns:
            Dictionary with location types and their paths
        """
        return {
            "project": Path.cwd() / self.DEFAULT_CONFIG_NAME,
            "user": Path.home() / ".config" / "gridcode" / self.DEFAULT_CONFIG_NAME,
            "active": self._config_path,
        }

    def get_config_info(self) -> dict[str, Any]:
        """Get configuration information including sources and .env files.

        Returns:
            Dictionary with configuration details and metadata
        """
        return {
            "config_path": str(self._config_path) if self._config_path else None,
            "env_files_loaded": [str(f) for f in self._env_files_loaded],
            "locations": {k: str(v) if v else None for k, v in self.get_config_locations().items()},
        }

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key.

        Args:
            key: Configuration key (e.g., "runtime.framework")
            default: Default value if key not found

        Returns:
            Configuration value or default

        Raises:
            RuntimeError: If configuration not loaded
        """
        if self._config is None:
            raise RuntimeError("Configuration not loaded")

        # Navigate through nested structure
        keys = key.split(".")
        value = self._config.model_dump()

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set_value(self, key: str, value: Any) -> None:
        """Set configuration value by dot-notation key.

        Note: This modifies the in-memory configuration only.
        Use save() to persist changes.

        Args:
            key: Configuration key (e.g., "runtime.framework")
            value: Value to set

        Raises:
            RuntimeError: If configuration not loaded
        """
        if self._config is None:
            raise RuntimeError("Configuration not loaded")

        # Convert to dict for modification
        config_dict = self._config.model_dump()

        # Navigate and set value
        keys = key.split(".")
        current = config_dict

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

        # Recreate config object with validation
        self._config = GridCodeConfig(**config_dict)

    def save(self, config_path: Path | None = None) -> None:
        """Save current configuration to file.

        Args:
            config_path: Path to save to. If None, uses loaded path.

        Raises:
            RuntimeError: If no path specified and config not loaded from file
        """
        if config_path is None:
            if self._config_path is None:
                raise RuntimeError(
                    "No configuration path. Specify config_path or load from file first."
                )
            config_path = self._config_path

        if self._config is None:
            raise RuntimeError("No configuration to save")

        config_dict = self._config.model_dump()
        ConfigLoader.save_yaml(config_path, config_dict)
