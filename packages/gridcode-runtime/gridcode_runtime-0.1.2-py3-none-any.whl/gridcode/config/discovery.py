"""Configuration file discovery and merging with layered support."""

from pathlib import Path
from typing import Any

import yaml

from gridcode.config.models import GridCodeConfig


class ConfigSource:
    """Represents a configuration source with metadata."""

    def __init__(
        self,
        path: Path,
        level: str,
        priority: int,
    ):
        """Initialize config source.

        Args:
            path: Path to configuration file
            level: Configuration level (project, user, default)
            priority: Priority level (higher = higher priority)
        """
        self.path = path
        self.level = level
        self.priority = priority
        self.data: dict[str, Any] | None = None
        self.valid = False

    def load(self) -> bool:
        """Load configuration from file.

        Returns:
            True if successful, False otherwise
        """
        if not self.path.exists():
            return False

        try:
            with open(self.path, encoding="utf-8") as f:
                content = f.read()

            if not content.strip():
                self.data = {}
                self.valid = True
                return True

            self.data = yaml.safe_load(content) or {}
            self.valid = True
            return True

        except Exception:
            return False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for display."""
        return {
            "path": str(self.path),
            "level": self.level,
            "priority": self.priority,
            "exists": self.path.exists(),
            "valid": self.valid,
        }


class ConfigDiscovery:
    """Discover and load configuration files from multiple sources."""

    # Configuration search paths in priority order (highest first)
    SEARCH_PATHS = [
        ("project", Path.cwd() / "gridcode.yaml", 100),
        ("user", Path.home() / ".config" / "gridcode" / "gridcode.yaml", 50),
    ]

    @staticmethod
    def discover_sources(
        start_dir: Path | None = None,
        include_parents: bool = True,
        include_home: bool = True,
    ) -> list[ConfigSource]:
        """Discover all available configuration sources.

        Args:
            start_dir: Directory to start search from
            include_parents: Whether to search parent directories
            include_home: Whether to include home directory config

        Returns:
            List of ConfigSource objects sorted by priority
        """
        sources: list[ConfigSource] = []
        found_paths = set()

        # Search current and parent directories
        if include_parents:
            current = (start_dir or Path.cwd()).resolve()

            while current != current.parent:
                config_path = current / "gridcode.yaml"
                if config_path not in found_paths:
                    source = ConfigSource(
                        path=config_path,
                        level="project",
                        priority=100 - (len(found_paths) if current == Path.cwd() else 0),
                    )
                    sources.append(source)
                    found_paths.add(config_path)

                current = current.parent

        # Add user config
        if include_home:
            user_config = Path.home() / ".config" / "gridcode" / "gridcode.yaml"
            if user_config not in found_paths:
                source = ConfigSource(
                    path=user_config,
                    level="user",
                    priority=50,
                )
                sources.append(source)
                found_paths.add(user_config)

        # Sort by priority (highest first)
        sources.sort(key=lambda s: s.priority, reverse=True)

        return sources

    @staticmethod
    def find_active_config(
        sources: list[ConfigSource] | None = None,
    ) -> ConfigSource | None:
        """Find the active configuration source (highest priority existing file).

        Args:
            sources: List of sources to search (uses discover_sources if None)

        Returns:
            Active ConfigSource if found, None otherwise
        """
        if sources is None:
            sources = ConfigDiscovery.discover_sources()

        for source in sources:
            if source.path.exists():
                return source

        return None

    @staticmethod
    def load_all_sources(
        sources: list[ConfigSource] | None = None,
    ) -> tuple[list[ConfigSource], dict[str, Any]]:
        """Load all available configuration sources.

        Args:
            sources: List of sources (uses discover_sources if None)

        Returns:
            Tuple of (loaded_sources, merged_data)
        """
        if sources is None:
            sources = ConfigDiscovery.discover_sources()

        loaded_sources: list[ConfigSource] = []
        merged_data: dict[str, Any] = {}

        # Sort by priority (lowest first, so highest priority overwrites)
        sorted_sources = sorted(sources, key=lambda s: s.priority)

        # Load and merge sources in priority order
        for source in sorted_sources:
            if source.load():
                loaded_sources.append(source)
                # Merge data
                if source.data:
                    ConfigDiscovery._deep_merge(merged_data, source.data)

        return loaded_sources, merged_data

    @staticmethod
    def _deep_merge(base: dict[str, Any], updates: dict[str, Any]) -> None:
        """Deep merge updates into base dictionary.

        Args:
            base: Base dictionary (modified in place)
            updates: Dictionary to merge
        """
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                ConfigDiscovery._deep_merge(base[key], value)
            else:
                base[key] = value


class LayeredConfigManager:
    """Manage configuration with multiple layers and source tracking."""

    def __init__(self):
        """Initialize layered config manager."""
        self.sources: list[ConfigSource] = []
        self.merged_data: dict[str, Any] = {}
        self.active_source: ConfigSource | None = None
        self.config: GridCodeConfig | None = None

    def discover(
        self,
        start_dir: Path | None = None,
        include_parents: bool = True,
        include_home: bool = True,
    ) -> None:
        """Discover configuration sources.

        Args:
            start_dir: Directory to start search from
            include_parents: Whether to search parent directories
            include_home: Whether to include home directory config
        """
        self.sources = ConfigDiscovery.discover_sources(
            start_dir=start_dir,
            include_parents=include_parents,
            include_home=include_home,
        )

    def load(
        self,
        sources: list[ConfigSource] | None = None,
        expand_env: bool = True,
    ) -> GridCodeConfig:
        """Load configuration from sources.

        Args:
            sources: Specific sources to load (uses discovered if None)
            expand_env: Whether to expand environment variables

        Returns:
            Loaded GridCodeConfig
        """
        if sources is None:
            if not self.sources:
                self.discover()
            sources = self.sources

        # Load sources
        self.sources, self.merged_data = ConfigDiscovery.load_all_sources(sources)

        # Find active source
        self.active_source = ConfigDiscovery.find_active_config(self.sources)

        # Expand environment variables if requested
        if expand_env:
            from gridcode.config.loader import ConfigLoader

            self.merged_data = ConfigLoader.expand_env_vars(self.merged_data)

        # Validate and create config
        try:
            self.config = GridCodeConfig(**self.merged_data)
        except Exception as e:
            raise ValueError(f"Invalid configuration: {e}") from e

        return self.config

    def get_source_info(self) -> dict[str, Any]:
        """Get information about configuration sources.

        Returns:
            Dictionary with source information
        """
        return {
            "discovered": [s.to_dict() for s in self.sources],
            "active": self.active_source.to_dict() if self.active_source else None,
            "source_count": len([s for s in self.sources if s.path.exists()]),
        }

    def get_source_chain(self) -> list[dict[str, Any]]:
        """Get the configuration source chain (what was merged).

        Returns:
            List of loaded sources in merge order
        """
        return [s.to_dict() for s in self.sources if s.valid]
