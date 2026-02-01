"""Base Plugin System for GridCode Runtime.

This module defines the core plugin infrastructure including:
- Plugin base class with lifecycle hooks
- PluginManager for loading/unloading plugins
- Plugin type enumeration and status tracking
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from loguru import logger
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from gridcode.core.runtime import GridCodeRuntime


class PluginType(str, Enum):
    """Plugin type enumeration.

    Different plugin types have different capabilities and integration points.
    """

    TOOL = "tool"  # Adds new tools to the registry
    AGENT = "agent"  # Adds new agent types
    REMINDER = "reminder"  # Adds new system reminders
    HOOK = "hook"  # Adds event hooks
    COMPOSITE = "composite"  # Combines multiple plugin types


class PluginStatus(str, Enum):
    """Plugin lifecycle status."""

    UNLOADED = "unloaded"  # Plugin is not loaded
    LOADING = "loading"  # Plugin is being loaded
    LOADED = "loaded"  # Plugin is loaded and active
    UNLOADING = "unloading"  # Plugin is being unloaded
    FAILED = "failed"  # Plugin failed to load/unload


class PluginInfo(BaseModel):
    """Plugin metadata and status information.

    Attributes:
        name: Unique plugin identifier
        version: Plugin version string
        description: Human-readable description
        author: Plugin author
        plugin_type: Type of the plugin
        status: Current lifecycle status
        loaded_at: Timestamp when plugin was loaded
        error: Error message if plugin failed
        dependencies: List of required plugin names
        provides: List of capabilities this plugin provides
    """

    name: str = Field(..., description="Unique plugin identifier")
    version: str = Field(default="1.0.0", description="Plugin version")
    description: str = Field(default="", description="Plugin description")
    author: str = Field(default="", description="Plugin author")
    plugin_type: PluginType = Field(default=PluginType.TOOL, description="Plugin type")
    status: PluginStatus = Field(default=PluginStatus.UNLOADED, description="Current status")
    loaded_at: datetime | None = Field(default=None, description="Load timestamp")
    error: str | None = Field(default=None, description="Error message if failed")
    dependencies: list[str] = Field(default_factory=list, description="Required plugins")
    provides: list[str] = Field(default_factory=list, description="Provided capabilities")


class Plugin(ABC):
    """Abstract base class for all plugins.

    All plugins must implement the on_load and on_unload lifecycle methods.
    The plugin class should define name, version, and description as class attributes.

    Example:
        class MyPlugin(Plugin):
            name = "my-plugin"
            version = "1.0.0"
            description = "A sample plugin"
            plugin_type = PluginType.TOOL

            async def on_load(self, runtime):
                # Initialize plugin resources
                runtime.tool_registry.register_tool(MyTool())

            async def on_unload(self):
                # Cleanup plugin resources
                pass
    """

    # Class-level attributes (should be overridden by subclasses)
    name: str = "base-plugin"
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    plugin_type: PluginType = PluginType.TOOL
    dependencies: list[str] = []
    provides: list[str] = []

    def __init__(self):
        """Initialize the plugin."""
        self._runtime: GridCodeRuntime | None = None
        self._status: PluginStatus = PluginStatus.UNLOADED
        self._loaded_at: datetime | None = None
        self._error: str | None = None

    @property
    def runtime(self) -> "GridCodeRuntime":
        """Get the runtime instance.

        Raises:
            RuntimeError: If plugin is not loaded
        """
        if self._runtime is None:
            raise RuntimeError(f"Plugin '{self.name}' is not loaded")
        return self._runtime

    @property
    def status(self) -> PluginStatus:
        """Get current plugin status."""
        return self._status

    @property
    def info(self) -> PluginInfo:
        """Get plugin info."""
        return PluginInfo(
            name=self.name,
            version=self.version,
            description=self.description,
            author=self.author,
            plugin_type=self.plugin_type,
            status=self._status,
            loaded_at=self._loaded_at,
            error=self._error,
            dependencies=self.dependencies,
            provides=self.provides,
        )

    @abstractmethod
    async def on_load(self, runtime: "GridCodeRuntime") -> None:
        """Called when the plugin is loaded.

        This method should register tools, agents, reminders, or hooks
        with the runtime.

        Args:
            runtime: The GridCodeRuntime instance

        Raises:
            Exception: If plugin fails to load
        """
        pass

    @abstractmethod
    async def on_unload(self) -> None:
        """Called when the plugin is unloaded.

        This method should cleanup any resources and unregister
        any tools, agents, reminders, or hooks.

        Raises:
            Exception: If plugin fails to unload
        """
        pass

    async def on_enable(self) -> None:
        """Called when the plugin is enabled (optional).

        Override this method to perform actions when the plugin
        is enabled after being disabled.
        """
        pass

    async def on_disable(self) -> None:
        """Called when the plugin is disabled (optional).

        Override this method to perform actions when the plugin
        is disabled but not unloaded.
        """
        pass

    def __repr__(self) -> str:
        """String representation of plugin."""
        return (
            f"{self.__class__.__name__}("
            f"name={self.name}, "
            f"version={self.version}, "
            f"status={self._status.value})"
        )


class PluginManager:
    """Manager for loading and unloading plugins.

    The PluginManager handles:
    - Plugin lifecycle (load, unload, enable, disable)
    - Dependency resolution
    - Plugin registry and lookup

    Example:
        runtime = GridCodeRuntime(api_key="...")
        manager = PluginManager(runtime)

        # Load a plugin
        await manager.load_plugin(MyPlugin())

        # Get plugin info
        info = manager.get_plugin_info("my-plugin")

        # Unload a plugin
        await manager.unload_plugin("my-plugin")
    """

    def __init__(self, runtime: "GridCodeRuntime"):
        """Initialize the plugin manager.

        Args:
            runtime: The GridCodeRuntime instance
        """
        self.runtime = runtime
        self._plugins: dict[str, Plugin] = {}
        self._load_order: list[str] = []  # Track load order for unloading

        logger.info("PluginManager initialized")

    @property
    def plugins(self) -> dict[str, Plugin]:
        """Get all loaded plugins."""
        return self._plugins.copy()

    def get_plugin(self, name: str) -> Plugin | None:
        """Get a plugin by name.

        Args:
            name: Plugin name

        Returns:
            Plugin instance or None if not found
        """
        return self._plugins.get(name)

    def get_plugin_info(self, name: str) -> PluginInfo | None:
        """Get plugin info by name.

        Args:
            name: Plugin name

        Returns:
            PluginInfo or None if not found
        """
        plugin = self._plugins.get(name)
        return plugin.info if plugin else None

    def list_plugins(self) -> list[PluginInfo]:
        """List all loaded plugins.

        Returns:
            List of PluginInfo for all plugins
        """
        return [plugin.info for plugin in self._plugins.values()]

    def is_loaded(self, name: str) -> bool:
        """Check if a plugin is loaded.

        Args:
            name: Plugin name

        Returns:
            True if plugin is loaded
        """
        plugin = self._plugins.get(name)
        return plugin is not None and plugin.status == PluginStatus.LOADED

    async def load_plugin(self, plugin: Plugin) -> bool:
        """Load a plugin.

        This method:
        1. Checks for duplicate plugins
        2. Resolves dependencies
        3. Calls the plugin's on_load method
        4. Updates plugin status

        Args:
            plugin: Plugin instance to load

        Returns:
            True if plugin was loaded successfully

        Raises:
            ValueError: If plugin with same name already loaded
            RuntimeError: If dependencies are not met
        """
        name = plugin.name

        # Check for duplicates
        if name in self._plugins:
            existing = self._plugins[name]
            if existing.status == PluginStatus.LOADED:
                logger.warning(f"Plugin '{name}' is already loaded")
                return False

        # Check dependencies
        missing_deps = self._check_dependencies(plugin)
        if missing_deps:
            error_msg = f"Missing dependencies for '{name}': {missing_deps}"
            logger.error(error_msg)
            plugin._status = PluginStatus.FAILED
            plugin._error = error_msg
            raise RuntimeError(error_msg)

        # Load the plugin
        plugin._status = PluginStatus.LOADING
        logger.info(f"Loading plugin: {name} v{plugin.version}")

        try:
            await plugin.on_load(self.runtime)

            # Update plugin state
            plugin._runtime = self.runtime
            plugin._status = PluginStatus.LOADED
            plugin._loaded_at = datetime.now()
            plugin._error = None

            # Register plugin
            self._plugins[name] = plugin
            self._load_order.append(name)

            logger.info(f"Plugin loaded: {name}")
            return True

        except Exception as e:
            plugin._status = PluginStatus.FAILED
            plugin._error = str(e)
            logger.error(f"Failed to load plugin '{name}': {e}")
            raise

    async def unload_plugin(self, name: str) -> bool:
        """Unload a plugin.

        This method:
        1. Checks if plugin exists
        2. Checks for dependent plugins
        3. Calls the plugin's on_unload method
        4. Removes plugin from registry

        Args:
            name: Name of the plugin to unload

        Returns:
            True if plugin was unloaded successfully
        """
        plugin = self._plugins.get(name)
        if plugin is None:
            logger.warning(f"Plugin '{name}' not found")
            return False

        if plugin.status != PluginStatus.LOADED:
            logger.warning(f"Plugin '{name}' is not loaded (status: {plugin.status})")
            return False

        # Check for dependents
        dependents = self._get_dependents(name)
        if dependents:
            logger.warning(
                f"Cannot unload '{name}': required by {dependents}. " f"Unload dependents first."
            )
            return False

        # Unload the plugin
        plugin._status = PluginStatus.UNLOADING
        logger.info(f"Unloading plugin: {name}")

        try:
            await plugin.on_unload()

            # Update plugin state
            plugin._runtime = None
            plugin._status = PluginStatus.UNLOADED

            # Remove from registry
            del self._plugins[name]
            self._load_order.remove(name)

            logger.info(f"Plugin unloaded: {name}")
            return True

        except Exception as e:
            plugin._status = PluginStatus.FAILED
            plugin._error = str(e)
            logger.error(f"Failed to unload plugin '{name}': {e}")
            raise

    async def reload_plugin(self, name: str) -> bool:
        """Reload a plugin.

        This unloads and reloads the plugin, useful for development.

        Args:
            name: Name of the plugin to reload

        Returns:
            True if plugin was reloaded successfully
        """
        plugin = self._plugins.get(name)
        if plugin is None:
            logger.warning(f"Plugin '{name}' not found")
            return False

        # Store reference for reload
        plugin_instance = plugin

        # Unload
        await self.unload_plugin(name)

        # Reset plugin state
        plugin_instance._status = PluginStatus.UNLOADED
        plugin_instance._error = None

        # Reload
        return await self.load_plugin(plugin_instance)

    async def unload_all(self) -> None:
        """Unload all plugins in reverse load order.

        This ensures dependencies are unloaded after their dependents.
        """
        logger.info("Unloading all plugins")

        # Unload in reverse order
        for name in reversed(self._load_order.copy()):
            try:
                await self.unload_plugin(name)
            except Exception as e:
                logger.error(f"Error unloading plugin '{name}': {e}")

    def _check_dependencies(self, plugin: Plugin) -> list[str]:
        """Check if plugin dependencies are satisfied.

        Args:
            plugin: Plugin to check

        Returns:
            List of missing dependency names
        """
        missing = []
        for dep in plugin.dependencies:
            if dep not in self._plugins or self._plugins[dep].status != PluginStatus.LOADED:
                missing.append(dep)
        return missing

    def _get_dependents(self, name: str) -> list[str]:
        """Get plugins that depend on the given plugin.

        Args:
            name: Plugin name

        Returns:
            List of dependent plugin names
        """
        dependents = []
        for plugin_name, plugin in self._plugins.items():
            if name in plugin.dependencies and plugin.status == PluginStatus.LOADED:
                dependents.append(plugin_name)
        return dependents

    def get_plugins_by_type(self, plugin_type: PluginType) -> list[Plugin]:
        """Get all plugins of a specific type.

        Args:
            plugin_type: Type of plugins to get

        Returns:
            List of plugins of the specified type
        """
        return [
            plugin
            for plugin in self._plugins.values()
            if plugin.plugin_type == plugin_type and plugin.status == PluginStatus.LOADED
        ]

    def get_plugins_providing(self, capability: str) -> list[Plugin]:
        """Get all plugins providing a specific capability.

        Args:
            capability: Capability to search for

        Returns:
            List of plugins providing the capability
        """
        return [
            plugin
            for plugin in self._plugins.values()
            if capability in plugin.provides and plugin.status == PluginStatus.LOADED
        ]
