"""Hook execution reminders.

Reminders about hook execution results:
- Success notifications
- Blocking error notifications
"""

from typing import Any

from gridcode.prompts.reminders.base import SystemReminder


class HookSuccessReminder(SystemReminder):
    """Reminder when a hook executed successfully."""

    name: str = "hook_success"
    priority: int = 5  # Lower priority - informational

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when hook_success is True."""
        return context.get("hook_success", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render hook success notification."""
        hook_name = context.get("hook_name", "Hook")
        hook_message = context.get("hook_message", "Success")
        return f"""<system-reminder>
{hook_name} hook success: {hook_message}
</system-reminder>"""


class HookBlockingErrorReminder(SystemReminder):
    """Reminder when a hook blocked an operation."""

    name: str = "hook_blocking_error"
    priority: int = 14  # High priority - operation was blocked

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when hook_blocked is True."""
        return context.get("hook_blocked", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render hook blocking error notification."""
        hook_name = context.get("hook_name", "Hook")
        blocked_operation = context.get("blocked_operation", "the operation")
        error_message = context.get("hook_error_message", "Operation was blocked by a hook")
        return f"""<system-reminder>
{hook_name} hook blocked {blocked_operation}: {error_message}

If you believe this block is incorrect, you may need to:
- Review the hook configuration
- Ask the user to adjust hook settings
- Find an alternative approach that doesn't trigger the hook
</system-reminder>"""


class HookAdditionalContextReminder(SystemReminder):
    """Reminder with additional context from a hook."""

    name: str = "hook_additional_context"
    priority: int = 6  # Medium priority - context information

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when hook_additional_context is True."""
        return context.get("hook_additional_context", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render hook additional context."""
        hook_name = context.get("hook_name", "Hook")
        hook_context = context.get("hook_context_content", [])

        if isinstance(hook_context, list):
            content = "\n".join(str(item) for item in hook_context)
        else:
            content = str(hook_context)

        return f"""<system-reminder>
{hook_name} hook additional context: {content}
</system-reminder>"""


class HookStoppedContinuationReminder(SystemReminder):
    """Reminder when a hook stops the execution chain.

    This indicates that a hook has intercepted and terminated further processing,
    requiring explicit user intervention or alternative action.
    """

    name: str = "hook_stopped_continuation"
    priority: int = 13  # High priority - execution halted

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when hook_stopped_continuation is True."""
        return context.get("hook_stopped_continuation", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render hook stopped continuation notification."""
        hook_name = context.get("hook_name", "A hook")
        reason = context.get("stop_reason", "policy violation or safety concern")
        return f"""<system-reminder>
🛑 {hook_name} has stopped the execution chain.

Reason: {reason}

The execution has been halted and will not continue automatically. This typically indicates:
- A safety or security concern was detected
- A policy violation occurred
- User intervention is required before proceeding

Next steps:
1. Review the reason for the stop
2. Address the underlying issue if needed
3. Request user approval to continue if appropriate
4. Consider alternative approaches that don't trigger the stop condition

Do NOT attempt to bypass or circumvent this stop without explicit user authorization.
</system-reminder>"""
