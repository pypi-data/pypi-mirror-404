"""Plugin Discovery Mechanism for GridCode Runtime.

This module provides automatic plugin discovery and loading through multiple mechanisms:
1. Directory scanning - Discover plugins from Python files in specified directories
2. Entry Points - Discover plugins registered via pyproject.toml entry points
3. YAML Configuration - Discover plugins defined in configuration files

Usage:
    from gridcode.plugins import PluginDiscovery

    # Create discovery instance
    discovery = PluginDiscovery(
        plugin_dirs=[Path("./plugins")],
        entry_point_group="gridcode.plugins",
    )

    # Discover all plugins
    plugins = discovery.discover_all()

    # Or discover from specific sources
    dir_plugins = discovery.discover_from_directories()
    ep_plugins = discovery.discover_from_entry_points()
    yaml_plugins = discovery.discover_from_yaml(Path("plugins.yaml"))
"""

import importlib
import importlib.util
import inspect
import sys
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any

import yaml
from loguru import logger
from pydantic import BaseModel, Field

from gridcode.plugins.base import Plugin


class PluginSpec(BaseModel):
    """Plugin specification from YAML configuration.

    Attributes:
        name: Plugin name (used for identification)
        module: Python module path (e.g., "mypackage.plugins.my_plugin")
        class_name: Plugin class name within the module
        enabled: Whether the plugin should be loaded
        config: Plugin-specific configuration
    """

    name: str = Field(..., description="Plugin identifier")
    module: str = Field(..., description="Python module path")
    class_name: str = Field(default="Plugin", description="Plugin class name")
    enabled: bool = Field(default=True, description="Whether plugin is enabled")
    config: dict[str, Any] = Field(default_factory=dict, description="Plugin configuration")


class PluginDiscoveryResult(BaseModel):
    """Result of plugin discovery.

    Attributes:
        plugins: List of discovered plugin instances
        errors: List of error messages from failed discoveries
        sources: Mapping of plugin name to discovery source
    """

    plugins: list[Any] = Field(default_factory=list, description="Discovered plugins")
    errors: list[str] = Field(default_factory=list, description="Discovery errors")
    sources: dict[str, str] = Field(default_factory=dict, description="Plugin name -> source")


class PluginDiscovery:
    """Plugin discovery mechanism for GridCode Runtime.

    Discovers plugins from multiple sources:
    1. Directory scanning - Python files in specified directories
    2. Entry Points - Plugins registered via pyproject.toml
    3. YAML Configuration - Plugins defined in configuration files

    Example:
        discovery = PluginDiscovery(
            plugin_dirs=[Path("./plugins"), Path("~/.gridcode/plugins")],
            entry_point_group="gridcode.plugins",
        )

        # Discover all plugins
        result = discovery.discover_all()
        for plugin in result.plugins:
            print(f"Discovered: {plugin.name}")

        # Load specific plugin from module path
        plugin = discovery.load_plugin_from_module(
            "mypackage.plugins.my_plugin",
            "MyPlugin"
        )
    """

    def __init__(
        self,
        plugin_dirs: list[Path] | None = None,
        entry_point_group: str = "gridcode.plugins",
    ):
        """Initialize the plugin discovery.

        Args:
            plugin_dirs: List of directories to scan for plugins
            entry_point_group: Entry point group name for discovering registered plugins
        """
        self.plugin_dirs = [Path(p).expanduser() for p in (plugin_dirs or [])]
        self.entry_point_group = entry_point_group
        self._discovered_plugins: dict[str, Plugin] = {}

        logger.debug(
            f"PluginDiscovery initialized with dirs={self.plugin_dirs}, "
            f"group={self.entry_point_group}"
        )

    def discover_from_directories(self) -> PluginDiscoveryResult:
        """Discover plugins from configured directories.

        Scans each directory for Python files and attempts to load
        Plugin subclasses from them.

        Returns:
            PluginDiscoveryResult with discovered plugins and any errors
        """
        result = PluginDiscoveryResult()

        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.exists():
                logger.warning(f"Plugin directory does not exist: {plugin_dir}")
                continue

            if not plugin_dir.is_dir():
                logger.warning(f"Plugin path is not a directory: {plugin_dir}")
                continue

            logger.info(f"Scanning plugin directory: {plugin_dir}")

            # Scan for Python files
            for py_file in plugin_dir.glob("*.py"):
                if py_file.name.startswith("_"):
                    continue  # Skip private modules

                try:
                    plugins = self._load_plugins_from_file(py_file)
                    for plugin in plugins:
                        if plugin.name not in self._discovered_plugins:
                            self._discovered_plugins[plugin.name] = plugin
                            result.plugins.append(plugin)
                            result.sources[plugin.name] = f"directory:{plugin_dir}"
                            logger.debug(f"Discovered plugin from file: {plugin.name}")
                        else:
                            logger.warning(
                                f"Duplicate plugin '{plugin.name}' ignored from {py_file}"
                            )

                except Exception as e:
                    error_msg = f"Failed to load plugins from {py_file}: {e}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)

        return result

    def discover_from_entry_points(self) -> PluginDiscoveryResult:
        """Discover plugins from Python entry points.

        Loads plugins registered via the configured entry point group
        (default: "gridcode.plugins") in pyproject.toml or setup.py.

        Entry points should be registered like:
            [project.entry-points."gridcode.plugins"]
            my-plugin = "mypackage.plugins:MyPlugin"

        Returns:
            PluginDiscoveryResult with discovered plugins and any errors
        """
        result = PluginDiscoveryResult()

        try:
            # Get entry points for our group
            eps = entry_points(group=self.entry_point_group)

            for ep in eps:
                try:
                    # Load the plugin class
                    plugin_class = ep.load()

                    # Validate it's a Plugin subclass
                    if not (inspect.isclass(plugin_class) and issubclass(plugin_class, Plugin)):
                        error_msg = (
                            f"Entry point '{ep.name}' does not point to a "
                            f"Plugin subclass: {plugin_class}"
                        )
                        logger.warning(error_msg)
                        result.errors.append(error_msg)
                        continue

                    # Instantiate the plugin
                    plugin = plugin_class()

                    if plugin.name not in self._discovered_plugins:
                        self._discovered_plugins[plugin.name] = plugin
                        result.plugins.append(plugin)
                        result.sources[plugin.name] = f"entry_point:{ep.name}"
                        logger.debug(f"Discovered plugin from entry point: {plugin.name}")
                    else:
                        logger.warning(
                            f"Duplicate plugin '{plugin.name}' ignored from entry point {ep.name}"
                        )

                except Exception as e:
                    error_msg = f"Failed to load entry point '{ep.name}': {e}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)

        except Exception as e:
            error_msg = f"Failed to discover entry points: {e}"
            logger.error(error_msg)
            result.errors.append(error_msg)

        return result

    def discover_from_yaml(self, config_path: Path) -> PluginDiscoveryResult:
        """Discover plugins from a YAML configuration file.

        The YAML file should have the format:
            plugins:
              - name: my-plugin
                module: mypackage.plugins.my_plugin
                class_name: MyPlugin  # optional, defaults to "Plugin"
                enabled: true          # optional, defaults to true
                config:                # optional, plugin-specific config
                  key: value

        Args:
            config_path: Path to the YAML configuration file

        Returns:
            PluginDiscoveryResult with discovered plugins and any errors
        """
        result = PluginDiscoveryResult()
        config_path = Path(config_path).expanduser()

        if not config_path.exists():
            error_msg = f"Plugin configuration file not found: {config_path}"
            logger.warning(error_msg)
            result.errors.append(error_msg)
            return result

        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)

            if config is None:
                logger.warning(f"Empty configuration file: {config_path}")
                return result

            plugins_config = config.get("plugins", [])

            for plugin_data in plugins_config:
                try:
                    spec = PluginSpec(**plugin_data)

                    if not spec.enabled:
                        logger.debug(f"Skipping disabled plugin: {spec.name}")
                        continue

                    plugin = self.load_plugin_from_module(
                        spec.module,
                        spec.class_name,
                        spec.config,
                    )

                    if plugin is None:
                        error_msg = (
                            f"Failed to load plugin '{spec.name}' "
                            f"from {spec.module}:{spec.class_name}"
                        )
                        logger.warning(error_msg)
                        result.errors.append(error_msg)
                    elif plugin.name not in self._discovered_plugins:
                        self._discovered_plugins[plugin.name] = plugin
                        result.plugins.append(plugin)
                        result.sources[plugin.name] = f"yaml:{config_path}"
                        logger.debug(f"Discovered plugin from YAML config: {plugin.name}")
                    else:
                        logger.warning(
                            f"Duplicate plugin '{plugin.name}' ignored from {config_path}"
                        )

                except Exception as e:
                    error_msg = f"Failed to load plugin from spec {plugin_data}: {e}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)

        except yaml.YAMLError as e:
            error_msg = f"Invalid YAML in {config_path}: {e}"
            logger.error(error_msg)
            result.errors.append(error_msg)
        except Exception as e:
            error_msg = f"Failed to read plugin config {config_path}: {e}"
            logger.error(error_msg)
            result.errors.append(error_msg)

        return result

    def discover_all(self, yaml_configs: list[Path] | None = None) -> PluginDiscoveryResult:
        """Discover plugins from all sources.

        Discovers plugins in the following order:
        1. Entry points (highest priority, from installed packages)
        2. Directories (from configured plugin directories)
        3. YAML configurations (from provided config files)

        Later discoveries do not override earlier ones if the plugin
        name is already registered.

        Args:
            yaml_configs: Optional list of YAML configuration files to scan

        Returns:
            Combined PluginDiscoveryResult from all sources
        """
        result = PluginDiscoveryResult()

        # Clear previous discoveries
        self._discovered_plugins.clear()

        # 1. Discover from entry points (highest priority)
        ep_result = self.discover_from_entry_points()
        result.plugins.extend(ep_result.plugins)
        result.errors.extend(ep_result.errors)
        result.sources.update(ep_result.sources)

        # 2. Discover from directories
        dir_result = self.discover_from_directories()
        result.plugins.extend(dir_result.plugins)
        result.errors.extend(dir_result.errors)
        result.sources.update(dir_result.sources)

        # 3. Discover from YAML configs
        if yaml_configs:
            for config_path in yaml_configs:
                yaml_result = self.discover_from_yaml(config_path)
                result.plugins.extend(yaml_result.plugins)
                result.errors.extend(yaml_result.errors)
                result.sources.update(yaml_result.sources)

        logger.info(
            f"Plugin discovery complete: {len(result.plugins)} plugins, "
            f"{len(result.errors)} errors"
        )

        return result

    def load_plugin_from_module(
        self,
        module_path: str,
        class_name: str = "Plugin",
        config: dict[str, Any] | None = None,
    ) -> Plugin | None:
        """Load a specific plugin from a module path.

        Args:
            module_path: Fully qualified module path (e.g., "mypackage.plugins.my_plugin")
            class_name: Name of the Plugin class in the module
            config: Optional configuration to pass to the plugin

        Returns:
            Plugin instance or None if loading failed
        """
        try:
            # Import the module
            module = importlib.import_module(module_path)

            # Get the plugin class
            if not hasattr(module, class_name):
                logger.error(f"Class '{class_name}' not found in module '{module_path}'")
                return None

            plugin_class = getattr(module, class_name)

            # Validate it's a Plugin subclass
            if not (inspect.isclass(plugin_class) and issubclass(plugin_class, Plugin)):
                logger.error(f"Class '{class_name}' is not a Plugin subclass in '{module_path}'")
                return None

            # Instantiate the plugin
            # Check if the plugin accepts config in __init__
            init_sig = inspect.signature(plugin_class.__init__)
            if "config" in init_sig.parameters and config:
                plugin = plugin_class(config=config)
            else:
                plugin = plugin_class()

            logger.debug(f"Loaded plugin '{plugin.name}' from {module_path}:{class_name}")
            return plugin

        except ImportError as e:
            logger.error(f"Failed to import module '{module_path}': {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load plugin from {module_path}:{class_name}: {e}")
            return None

    def _load_plugins_from_file(self, file_path: Path) -> list[Plugin]:
        """Load all Plugin subclasses from a Python file.

        Args:
            file_path: Path to the Python file

        Returns:
            List of Plugin instances found in the file

        Raises:
            Exception: If module loading fails (e.g., syntax errors)
        """
        plugins = []

        # Create a unique module name based on file path
        module_name = f"gridcode_plugin_{file_path.stem}_{id(file_path)}"

        # Load the module from file
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            logger.warning(f"Could not create module spec for {file_path}")
            return plugins

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module

        try:
            spec.loader.exec_module(module)

            # Find all Plugin subclasses in the module
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Skip the base Plugin class itself
                if obj is Plugin:
                    continue

                # Check if it's a subclass of Plugin
                if issubclass(obj, Plugin) and not inspect.isabstract(obj):
                    try:
                        plugin = obj()
                        plugins.append(plugin)
                    except Exception as e:
                        logger.error(
                            f"Failed to instantiate plugin class '{name}' " f"from {file_path}: {e}"
                        )

        except Exception as e:
            # Clean up before re-raising
            sys.modules.pop(module_name, None)
            raise RuntimeError(f"Failed to execute module from {file_path}: {e}") from e
        finally:
            # Clean up the module from sys.modules to avoid pollution
            sys.modules.pop(module_name, None)

        return plugins

    def get_discovered_plugins(self) -> dict[str, Plugin]:
        """Get all discovered plugins.

        Returns:
            Dictionary mapping plugin name to Plugin instance
        """
        return self._discovered_plugins.copy()

    def clear_discoveries(self) -> None:
        """Clear all discovered plugins."""
        self._discovered_plugins.clear()
        logger.debug("Cleared all discovered plugins")


class AutoPluginLoader:
    """Automatic plugin loader for GridCode Runtime.

    Combines PluginDiscovery with PluginManager to automatically
    discover and load plugins on startup.

    Example:
        from gridcode.plugins import AutoPluginLoader, PluginManager

        manager = PluginManager(runtime)
        loader = AutoPluginLoader(
            manager,
            plugin_dirs=[Path("./plugins")],
            yaml_configs=[Path("plugins.yaml")],
        )

        # Load all discovered plugins
        loaded, failed = await loader.load_all()
        print(f"Loaded: {loaded}, Failed: {failed}")
    """

    def __init__(
        self,
        plugin_manager: Any,  # PluginManager, using Any to avoid circular import
        plugin_dirs: list[Path] | None = None,
        yaml_configs: list[Path] | None = None,
        entry_point_group: str = "gridcode.plugins",
    ):
        """Initialize the auto plugin loader.

        Args:
            plugin_manager: PluginManager instance
            plugin_dirs: Directories to scan for plugins
            yaml_configs: YAML configuration files to load
            entry_point_group: Entry point group for plugin discovery
        """
        self.plugin_manager = plugin_manager
        self.yaml_configs = yaml_configs or []
        self.discovery = PluginDiscovery(
            plugin_dirs=plugin_dirs,
            entry_point_group=entry_point_group,
        )

    async def load_all(
        self,
        skip_errors: bool = True,
    ) -> tuple[int, int]:
        """Discover and load all plugins.

        Args:
            skip_errors: If True, continue loading other plugins when one fails

        Returns:
            Tuple of (loaded_count, failed_count)
        """
        # Discover all plugins
        result = self.discovery.discover_all(self.yaml_configs)

        loaded = 0
        failed = len(result.errors)

        # Load each discovered plugin
        for plugin in result.plugins:
            try:
                success = await self.plugin_manager.load_plugin(plugin)
                if success:
                    loaded += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Failed to load plugin '{plugin.name}': {e}")
                failed += 1
                if not skip_errors:
                    raise

        logger.info(f"Auto-loaded plugins: {loaded} loaded, {failed} failed")
        return loaded, failed

    async def reload_all(self) -> tuple[int, int]:
        """Reload all plugins.

        Unloads all current plugins and rediscovers/reloads them.

        Returns:
            Tuple of (loaded_count, failed_count)
        """
        # Unload all existing plugins
        await self.plugin_manager.unload_all()

        # Clear discovery cache
        self.discovery.clear_discoveries()

        # Load all plugins again
        return await self.load_all()
