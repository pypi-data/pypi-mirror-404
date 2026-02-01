"""Plugin Hook System for GridCode Runtime.

This module provides an event-driven hook system for plugins to
extend runtime behavior at various lifecycle points.

Hooks can intercept and modify behavior at:
- Tool execution (before/after)
- Agent execution (before/after)
- Prompt composition
- Message handling
- Session lifecycle

Example:
    class MyHookPlugin(Plugin):
        name = "my-hook-plugin"
        plugin_type = PluginType.HOOK

        async def on_load(self, runtime):
            # Register a hook
            hook = PluginHook(
                name="log-tool-calls",
                event=HookEvent.TOOL_BEFORE_EXECUTE,
                callback=self._log_tool_call,
                priority=HookPriority.NORMAL,
            )
            runtime.plugin_manager.hook_registry.register(hook)

        async def _log_tool_call(self, context):
            logger.info(f"Tool called: {context['tool_name']}")
            return HookResult.CONTINUE
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any

from loguru import logger


class HookEvent(str, Enum):
    """Events that hooks can subscribe to."""

    # Runtime lifecycle
    RUNTIME_INIT = "runtime.init"  # After runtime initialization
    RUNTIME_SHUTDOWN = "runtime.shutdown"  # Before runtime shutdown

    # Session lifecycle
    SESSION_START = "session.start"  # When a session starts
    SESSION_END = "session.end"  # When a session ends
    SESSION_SAVE = "session.save"  # Before session is saved
    SESSION_LOAD = "session.load"  # After session is loaded

    # Tool execution
    TOOL_BEFORE_EXECUTE = "tool.before_execute"  # Before tool execution
    TOOL_AFTER_EXECUTE = "tool.after_execute"  # After tool execution
    TOOL_REGISTER = "tool.register"  # When a tool is registered

    # Agent execution
    AGENT_BEFORE_EXECUTE = "agent.before_execute"  # Before agent execution
    AGENT_AFTER_EXECUTE = "agent.after_execute"  # After agent execution
    AGENT_SPAWN = "agent.spawn"  # When a sub-agent is spawned

    # Prompt handling
    PROMPT_BEFORE_COMPOSE = "prompt.before_compose"  # Before prompt composition
    PROMPT_AFTER_COMPOSE = "prompt.after_compose"  # After prompt composition
    REMINDER_INJECT = "reminder.inject"  # When reminders are injected

    # Message handling
    MESSAGE_SEND = "message.send"  # When a message is sent
    MESSAGE_RECEIVE = "message.receive"  # When a message is received

    # User interaction
    USER_INPUT = "user.input"  # When user provides input
    USER_CONFIRM = "user.confirm"  # When user confirms an action

    # Error handling
    ERROR_OCCURRED = "error.occurred"  # When an error occurs


class HookPriority(IntEnum):
    """Hook execution priority (lower runs first)."""

    HIGHEST = 0
    HIGH = 25
    NORMAL = 50
    LOW = 75
    LOWEST = 100


class HookResult(str, Enum):
    """Result of a hook execution."""

    CONTINUE = "continue"  # Continue to next hook and normal execution
    SKIP = "skip"  # Skip remaining hooks but continue normal execution
    ABORT = "abort"  # Abort the operation (hook should set error in context)
    MODIFY = "modify"  # Hook modified the context, continue with changes


@dataclass
class HookContext:
    """Context passed to hook callbacks.

    Attributes:
        event: The event that triggered the hook
        data: Event-specific data
        result: Result to return to caller (can be modified by hooks)
        error: Error message if hook aborts
        modified: Whether the context was modified
    """

    event: HookEvent
    data: dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error: str | None = None
    modified: bool = False

    def set_result(self, result: Any) -> None:
        """Set the result and mark as modified."""
        self.result = result
        self.modified = True

    def set_error(self, error: str) -> None:
        """Set an error message."""
        self.error = error


# Type alias for hook callback functions
HookCallback = Callable[[HookContext], Awaitable[HookResult]]


@dataclass
class PluginHook:
    """A hook registration.

    Attributes:
        name: Unique hook identifier
        event: Event to subscribe to
        callback: Async callback function
        priority: Execution priority
        plugin_name: Name of the plugin that registered this hook
        enabled: Whether the hook is enabled
    """

    name: str
    event: HookEvent
    callback: HookCallback
    priority: HookPriority = HookPriority.NORMAL
    plugin_name: str = ""
    enabled: bool = True

    def __hash__(self) -> int:
        """Hash based on name and event."""
        return hash((self.name, self.event))

    def __eq__(self, other: object) -> bool:
        """Equality based on name and event."""
        if not isinstance(other, PluginHook):
            return False
        return self.name == other.name and self.event == other.event


class HookRegistry:
    """Registry for managing plugin hooks.

    The HookRegistry handles:
    - Hook registration and unregistration
    - Hook execution in priority order
    - Event filtering and dispatching

    Example:
        registry = HookRegistry()

        # Register a hook
        hook = PluginHook(
            name="my-hook",
            event=HookEvent.TOOL_BEFORE_EXECUTE,
            callback=my_callback,
        )
        registry.register(hook)

        # Execute hooks for an event
        context = HookContext(
            event=HookEvent.TOOL_BEFORE_EXECUTE,
            data={"tool_name": "read", "args": {...}},
        )
        result = await registry.execute(context)
    """

    def __init__(self):
        """Initialize the hook registry."""
        # Map from event to list of hooks (sorted by priority)
        self._hooks: dict[HookEvent, list[PluginHook]] = {event: [] for event in HookEvent}
        logger.debug("HookRegistry initialized")

    def register(self, hook: PluginHook) -> bool:
        """Register a hook.

        Args:
            hook: Hook to register

        Returns:
            True if registered successfully
        """
        event_hooks = self._hooks[hook.event]

        # Check for duplicates
        for existing in event_hooks:
            if existing.name == hook.name:
                logger.warning(f"Hook '{hook.name}' already registered for {hook.event}")
                return False

        # Insert in priority order
        inserted = False
        for i, existing in enumerate(event_hooks):
            if hook.priority < existing.priority:
                event_hooks.insert(i, hook)
                inserted = True
                break

        if not inserted:
            event_hooks.append(hook)

        logger.debug(f"Registered hook: {hook.name} for {hook.event}")
        return True

    def unregister(self, name: str, event: HookEvent | None = None) -> int:
        """Unregister a hook by name.

        Args:
            name: Hook name to unregister
            event: Optional specific event (if None, unregister from all events)

        Returns:
            Number of hooks unregistered
        """
        count = 0

        if event is not None:
            # Unregister from specific event
            before = len(self._hooks[event])
            self._hooks[event] = [h for h in self._hooks[event] if h.name != name]
            count = before - len(self._hooks[event])
        else:
            # Unregister from all events
            for evt in HookEvent:
                before = len(self._hooks[evt])
                self._hooks[evt] = [h for h in self._hooks[evt] if h.name != name]
                count += before - len(self._hooks[evt])

        if count > 0:
            logger.debug(f"Unregistered {count} hook(s): {name}")

        return count

    def unregister_plugin(self, plugin_name: str) -> int:
        """Unregister all hooks from a plugin.

        Args:
            plugin_name: Plugin name

        Returns:
            Number of hooks unregistered
        """
        count = 0
        for event in HookEvent:
            before = len(self._hooks[event])
            self._hooks[event] = [h for h in self._hooks[event] if h.plugin_name != plugin_name]
            count += before - len(self._hooks[event])

        if count > 0:
            logger.debug(f"Unregistered {count} hooks from plugin: {plugin_name}")

        return count

    def get_hooks(self, event: HookEvent) -> list[PluginHook]:
        """Get all hooks for an event.

        Args:
            event: Event to get hooks for

        Returns:
            List of hooks in priority order
        """
        return [h for h in self._hooks[event] if h.enabled]

    def list_all_hooks(self) -> list[PluginHook]:
        """List all registered hooks.

        Returns:
            List of all hooks
        """
        all_hooks = []
        for hooks in self._hooks.values():
            all_hooks.extend(hooks)
        return all_hooks

    async def execute(self, context: HookContext) -> HookResult:
        """Execute all hooks for an event.

        Hooks are executed in priority order. A hook can:
        - CONTINUE: Continue to next hook
        - SKIP: Skip remaining hooks
        - ABORT: Abort the operation
        - MODIFY: Continue with modified context

        Args:
            context: Hook context

        Returns:
            Final result (CONTINUE if all hooks passed)
        """
        hooks = self.get_hooks(context.event)

        if not hooks:
            return HookResult.CONTINUE

        logger.debug(f"Executing {len(hooks)} hooks for {context.event}")

        for hook in hooks:
            try:
                result = await hook.callback(context)

                if result == HookResult.SKIP:
                    logger.debug(f"Hook '{hook.name}' returned SKIP")
                    break

                if result == HookResult.ABORT:
                    logger.debug(f"Hook '{hook.name}' returned ABORT: {context.error}")
                    return HookResult.ABORT

                if result == HookResult.MODIFY:
                    logger.debug(f"Hook '{hook.name}' modified context")

            except Exception as e:
                logger.error(f"Hook '{hook.name}' raised exception: {e}")
                # Continue to next hook on error by default
                continue

        return HookResult.CONTINUE

    def enable_hook(self, name: str) -> bool:
        """Enable a hook by name.

        Args:
            name: Hook name

        Returns:
            True if hook was found and enabled
        """
        found = False
        for hooks in self._hooks.values():
            for hook in hooks:
                if hook.name == name:
                    hook.enabled = True
                    found = True

        return found

    def disable_hook(self, name: str) -> bool:
        """Disable a hook by name.

        Args:
            name: Hook name

        Returns:
            True if hook was found and disabled
        """
        found = False
        for hooks in self._hooks.values():
            for hook in hooks:
                if hook.name == name:
                    hook.enabled = False
                    found = True

        return found

    def clear(self) -> None:
        """Clear all hooks."""
        for event in HookEvent:
            self._hooks[event] = []
        logger.debug("Cleared all hooks")
