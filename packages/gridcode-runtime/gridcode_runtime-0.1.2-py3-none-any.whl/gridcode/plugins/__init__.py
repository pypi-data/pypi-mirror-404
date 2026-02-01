"""Plugin System for GridCode Runtime.

This module provides a flexible plugin system that allows extending GridCode
with new tools, agents, reminders, and event hooks.

Plugin Types:
- Tool Plugin: Add new tools to the tool registry
- Agent Plugin: Add new agent types to the agent pool
- Reminder Plugin: Add new system reminders
- Hook Plugin: Add event hooks for lifecycle events

Usage:
    from gridcode.plugins import Plugin, PluginManager, PluginType

    class MyToolPlugin(Plugin):
        name = "my-tool-plugin"
        version = "1.0.0"
        plugin_type = PluginType.TOOL

        async def on_load(self, runtime):
            # Register custom tools
            runtime.tool_registry.register_tool(MyCustomTool())

        async def on_unload(self):
            pass

    # In your runtime code:
    plugin_manager = PluginManager(runtime)
    await plugin_manager.load_plugin(MyToolPlugin())

Plugin Discovery:
    from gridcode.plugins import PluginDiscovery, AutoPluginLoader
    from pathlib import Path

    # Manual discovery
    discovery = PluginDiscovery(
        plugin_dirs=[Path("./plugins")],
        entry_point_group="gridcode.plugins",
    )
    result = discovery.discover_all()
    for plugin in result.plugins:
        await plugin_manager.load_plugin(plugin)

    # Automatic loading
    loader = AutoPluginLoader(
        plugin_manager,
        plugin_dirs=[Path("./plugins")],
        yaml_configs=[Path("plugins.yaml")],
    )
    loaded, failed = await loader.load_all()

MCP Integration:
    from gridcode.plugins import MCPPlugin, MultiMCPPlugin
    from gridcode.mcp import MCPServerConfig

    # Single MCP server
    config = MCPServerConfig(name="my-server", command="uv", args=["run", "server"])
    await plugin_manager.load_plugin(MCPPlugin(config))

    # Multiple MCP servers
    configs = [
        MCPServerConfig(name="server1", command="python", args=["server1.py"]),
        MCPServerConfig(name="server2", url="http://localhost:8000/mcp"),
    ]
    await plugin_manager.load_plugin(MultiMCPPlugin(configs))

Note: This module uses lazy loading to improve startup time. Plugin classes are only
imported when first accessed, allowing faster startup for applications that don't
use the plugin system.
"""

# Import only the base plugin and plugin manager that may be needed
# Other plugin-related classes are lazy-loaded on demand
from gridcode.plugins.base import Plugin, PluginManager

__all__ = [
    # Base classes (always imported)
    "Plugin",
    "PluginManager",
    # Other classes (lazy-loaded)
    "PluginInfo",
    "PluginStatus",
    "PluginType",
    "AutoPluginLoader",
    "PluginDiscovery",
    "PluginDiscoveryResult",
    "PluginSpec",
    "HookEvent",
    "HookPriority",
    "HookResult",
    "PluginHook",
    "MCPPlugin",
    "MultiMCPPlugin",
]

# Lazy loading module map
_LAZY_MODULES = {
    "PluginInfo": ("gridcode.plugins.base", "PluginInfo"),
    "PluginStatus": ("gridcode.plugins.base", "PluginStatus"),
    "PluginType": ("gridcode.plugins.base", "PluginType"),
    "AutoPluginLoader": ("gridcode.plugins.discovery", "AutoPluginLoader"),
    "PluginDiscovery": ("gridcode.plugins.discovery", "PluginDiscovery"),
    "PluginDiscoveryResult": ("gridcode.plugins.discovery", "PluginDiscoveryResult"),
    "PluginSpec": ("gridcode.plugins.discovery", "PluginSpec"),
    "HookEvent": ("gridcode.plugins.hooks", "HookEvent"),
    "HookPriority": ("gridcode.plugins.hooks", "HookPriority"),
    "HookResult": ("gridcode.plugins.hooks", "HookResult"),
    "PluginHook": ("gridcode.plugins.hooks", "PluginHook"),
    "MCPPlugin": ("gridcode.plugins.mcp", "MCPPlugin"),
    "MultiMCPPlugin": ("gridcode.plugins.mcp", "MultiMCPPlugin"),
}

# Cache for lazy-loaded modules
_LAZY_CACHE = {}


def __getattr__(name: str):
    """Lazy load plugin classes on first access."""
    if name in _LAZY_MODULES:
        if name not in _LAZY_CACHE:
            module_name, class_name = _LAZY_MODULES[name]
            module = __import__(module_name, fromlist=[class_name])
            _LAZY_CACHE[name] = getattr(module, class_name)
        return _LAZY_CACHE[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
