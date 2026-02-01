"""Example Plugin Implementations for GridCode Runtime.

This module provides example plugins to demonstrate the plugin system:
- ToolLoggingPlugin: Logs all tool executions
- MetricsPlugin: Collects execution metrics
- CustomToolPlugin: Adds a custom tool

These examples show best practices for plugin development.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from loguru import logger

from gridcode.plugins.base import Plugin, PluginType
from gridcode.plugins.hooks import (
    HookContext,
    HookEvent,
    HookPriority,
    HookResult,
    PluginHook,
)
from gridcode.tools.base import BaseTool, ToolResult

if TYPE_CHECKING:
    from gridcode.core.runtime import GridCodeRuntime


class ToolLoggingPlugin(Plugin):
    """Plugin that logs all tool executions.

    This plugin demonstrates:
    - Hook-based event handling
    - Before/after execution hooks
    - Accessing tool execution data
    """

    name = "tool-logging"
    version = "1.0.0"
    description = "Logs all tool executions for debugging and auditing"
    author = "GridCode Team"
    plugin_type = PluginType.HOOK
    provides = ["tool-logging", "audit-trail"]

    def __init__(self):
        """Initialize the plugin."""
        super().__init__()
        self._log_entries: list[dict[str, Any]] = []

    async def on_load(self, runtime: "GridCodeRuntime") -> None:
        """Register logging hooks."""
        # Register before hook
        before_hook = PluginHook(
            name=f"{self.name}.before",
            event=HookEvent.TOOL_BEFORE_EXECUTE,
            callback=self._log_before_execute,
            priority=HookPriority.LOW,  # Run after other hooks
            plugin_name=self.name,
        )

        # Register after hook
        after_hook = PluginHook(
            name=f"{self.name}.after",
            event=HookEvent.TOOL_AFTER_EXECUTE,
            callback=self._log_after_execute,
            priority=HookPriority.HIGH,  # Run early to capture result
            plugin_name=self.name,
        )

        runtime.hook_registry.register(before_hook)
        runtime.hook_registry.register(after_hook)

        logger.info("ToolLoggingPlugin: Registered logging hooks")

    async def on_unload(self) -> None:
        """Unregister hooks."""
        self.runtime.hook_registry.unregister_plugin(self.name)
        logger.info("ToolLoggingPlugin: Unregistered hooks")

    async def _log_before_execute(self, context: HookContext) -> HookResult:
        """Log tool execution start."""
        tool_name = context.data.get("tool_name", "unknown")
        args = context.data.get("args", {})

        entry = {
            "event": "before_execute",
            "tool_name": tool_name,
            "args": args,
            "timestamp": datetime.now().isoformat(),
        }
        self._log_entries.append(entry)

        logger.debug(f"Tool execution started: {tool_name}")
        return HookResult.CONTINUE

    async def _log_after_execute(self, context: HookContext) -> HookResult:
        """Log tool execution end."""
        tool_name = context.data.get("tool_name", "unknown")
        result = context.data.get("result")
        duration = context.data.get("duration", 0)

        entry = {
            "event": "after_execute",
            "tool_name": tool_name,
            "success": result.success if result else False,
            "duration_ms": duration,
            "timestamp": datetime.now().isoformat(),
        }
        self._log_entries.append(entry)

        logger.debug(f"Tool execution completed: {tool_name} ({duration}ms)")
        return HookResult.CONTINUE

    def get_log_entries(self) -> list[dict[str, Any]]:
        """Get all log entries."""
        return self._log_entries.copy()

    def clear_log_entries(self) -> int:
        """Clear log entries and return count cleared."""
        count = len(self._log_entries)
        self._log_entries.clear()
        return count


class MetricsPlugin(Plugin):
    """Plugin that collects execution metrics.

    This plugin demonstrates:
    - Composite plugin type (hooks + data collection)
    - Multiple event subscriptions
    - Metric aggregation
    """

    name = "metrics"
    version = "1.0.0"
    description = "Collects execution metrics for monitoring"
    author = "GridCode Team"
    plugin_type = PluginType.COMPOSITE
    provides = ["metrics", "monitoring"]

    def __init__(self):
        """Initialize the plugin."""
        super().__init__()
        self._metrics: dict[str, Any] = {
            "tool_calls": 0,
            "tool_errors": 0,
            "agent_calls": 0,
            "agent_errors": 0,
            "total_duration_ms": 0,
            "tool_durations": {},
        }

    async def on_load(self, runtime: "GridCodeRuntime") -> None:
        """Register metric collection hooks."""
        # Tool execution hook
        tool_hook = PluginHook(
            name=f"{self.name}.tool",
            event=HookEvent.TOOL_AFTER_EXECUTE,
            callback=self._collect_tool_metrics,
            priority=HookPriority.LOWEST,
            plugin_name=self.name,
        )

        # Agent execution hook
        agent_hook = PluginHook(
            name=f"{self.name}.agent",
            event=HookEvent.AGENT_AFTER_EXECUTE,
            callback=self._collect_agent_metrics,
            priority=HookPriority.LOWEST,
            plugin_name=self.name,
        )

        runtime.hook_registry.register(tool_hook)
        runtime.hook_registry.register(agent_hook)

        logger.info("MetricsPlugin: Registered metric hooks")

    async def on_unload(self) -> None:
        """Unregister hooks."""
        self.runtime.hook_registry.unregister_plugin(self.name)
        logger.info("MetricsPlugin: Unregistered hooks")

    async def _collect_tool_metrics(self, context: HookContext) -> HookResult:
        """Collect tool execution metrics."""
        tool_name = context.data.get("tool_name", "unknown")
        result = context.data.get("result")
        duration = context.data.get("duration", 0)

        self._metrics["tool_calls"] += 1
        self._metrics["total_duration_ms"] += duration

        if result and not result.success:
            self._metrics["tool_errors"] += 1

        # Track per-tool durations
        if tool_name not in self._metrics["tool_durations"]:
            self._metrics["tool_durations"][tool_name] = []
        self._metrics["tool_durations"][tool_name].append(duration)

        return HookResult.CONTINUE

    async def _collect_agent_metrics(self, context: HookContext) -> HookResult:
        """Collect agent execution metrics."""
        result = context.data.get("result")

        self._metrics["agent_calls"] += 1

        if result and result.status.value == "failed":
            self._metrics["agent_errors"] += 1

        return HookResult.CONTINUE

    def get_metrics(self) -> dict[str, Any]:
        """Get all metrics."""
        metrics = self._metrics.copy()

        # Calculate averages
        for tool_name, durations in metrics.get("tool_durations", {}).items():
            if durations:
                avg = sum(durations) / len(durations)
                metrics[f"avg_duration_{tool_name}"] = avg

        return metrics

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self._metrics = {
            "tool_calls": 0,
            "tool_errors": 0,
            "agent_calls": 0,
            "agent_errors": 0,
            "total_duration_ms": 0,
            "tool_durations": {},
        }


class TimestampTool(BaseTool):
    """Example custom tool that returns current timestamp."""

    def __init__(self):
        """Initialize the timestamp tool."""
        super().__init__(
            name="timestamp",
            description="Returns the current timestamp in various formats",
        )

    async def execute(
        self,
        format: str = "iso",
        **kwargs: Any,
    ) -> ToolResult:
        """Execute the timestamp tool.

        Args:
            format: Output format ('iso', 'unix', 'human')

        Returns:
            ToolResult with timestamp
        """
        now = datetime.now()

        if format == "iso":
            content = now.isoformat()
        elif format == "unix":
            content = str(int(now.timestamp()))
        elif format == "human":
            content = now.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return ToolResult(
                success=False,
                error=f"Unknown format: {format}. Use 'iso', 'unix', or 'human'",
            )

        return ToolResult(
            success=True,
            content=content,
            metadata={"format": format},
        )


class CustomToolPlugin(Plugin):
    """Plugin that adds a custom tool.

    This plugin demonstrates:
    - Tool plugin type
    - Tool registration/unregistration
    - Custom tool implementation
    """

    name = "custom-tools"
    version = "1.0.0"
    description = "Adds custom utility tools"
    author = "GridCode Team"
    plugin_type = PluginType.TOOL
    provides = ["timestamp-tool"]

    def __init__(self):
        """Initialize the plugin."""
        super().__init__()
        self._tools: list[str] = []

    async def on_load(self, runtime: "GridCodeRuntime") -> None:
        """Register custom tools."""
        # Create and register the timestamp tool
        timestamp_tool = TimestampTool()
        runtime.tool_registry.register_tool(timestamp_tool)
        self._tools.append(timestamp_tool.name)

        logger.info(f"CustomToolPlugin: Registered {len(self._tools)} tools")

    async def on_unload(self) -> None:
        """Unregister custom tools."""
        for tool_name in self._tools:
            self.runtime.tool_registry.unregister_tool(tool_name)

        self._tools.clear()
        logger.info("CustomToolPlugin: Unregistered tools")

    def get_registered_tools(self) -> list[str]:
        """Get list of registered tool names."""
        return self._tools.copy()
