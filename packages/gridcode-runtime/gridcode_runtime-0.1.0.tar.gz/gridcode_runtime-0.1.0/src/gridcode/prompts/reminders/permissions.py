"""Permission control reminders for tool access denial."""

from typing import Any

from gridcode.prompts.reminders.base import SystemReminder


class BashPermissionDeniedReminder(SystemReminder):
    """Reminder triggered when Bash tool access is denied due to permission restrictions."""

    name: str = "bash_permission_denied"
    priority: int = 14  # High priority - Hook level

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Check if Bash tool was denied.

        Args:
            context: Must contain 'tool_denied' = True and 'tool_name' = 'bash'

        Returns:
            True if Bash tool was denied, False otherwise
        """
        return context.get("tool_denied", False) and context.get("tool_name") == "bash"

    def render(self, context: dict[str, Any]) -> str:
        """Render permission denied reminder for Bash tool.

        Args:
            context: Execution context with agent_name, reason (optional)

        Returns:
            Formatted system reminder message
        """
        agent = context.get("agent_name", "Agent")
        reason = context.get("reason", "safety restrictions")

        return f"""<system-reminder>
The {agent} attempted to use the Bash tool but was denied due to {reason}.

Reason: {agent} agents are limited to read-only operations for safety.

Alternative approaches:
- Use Read tool for viewing file contents
- Use Glob tool for finding files by pattern
- Use Grep tool for searching file contents
- If command execution is required, request Main agent to perform the operation

This restriction ensures agents cannot make unintended system modifications.
</system-reminder>"""


class EditPermissionDeniedReminder(SystemReminder):
    """Reminder triggered when Edit tool access is denied due to permission restrictions."""

    name: str = "edit_permission_denied"
    priority: int = 14  # High priority - Hook level

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Check if Edit tool was denied.

        Args:
            context: Must contain 'tool_denied' = True and 'tool_name' = 'edit'

        Returns:
            True if Edit tool was denied, False otherwise
        """
        return context.get("tool_denied", False) and context.get("tool_name") == "edit"

    def render(self, context: dict[str, Any]) -> str:
        """Render permission denied reminder for Edit tool.

        Args:
            context: Execution context with agent_name, reason (optional)

        Returns:
            Formatted system reminder message
        """
        agent = context.get("agent_name", "Agent")
        reason = context.get("reason", "read-only permission restrictions")

        return f"""<system-reminder>
The {agent} attempted to use the Edit tool but was denied due to {reason}.

Reason: {agent} agents are restricted to read-only operations to prevent accidental modifications.

Alternative approaches:
- Use Read tool to view the file contents
- Report findings to Main agent with suggested edits
- Main agent can perform the actual file modifications

If file edits are essential for this agent's task, consider:
1. Requesting permission elevation from Main agent
2. Redesigning the workflow to separate read and write operations
</system-reminder>"""


class WritePermissionDeniedReminder(SystemReminder):
    """Reminder triggered when Write tool access is denied due to permission restrictions."""

    name: str = "write_permission_denied"
    priority: int = 14  # High priority - Hook level

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Check if Write tool was denied.

        Args:
            context: Must contain 'tool_denied' = True and 'tool_name' = 'write'

        Returns:
            True if Write tool was denied, False otherwise
        """
        return context.get("tool_denied", False) and context.get("tool_name") == "write"

    def render(self, context: dict[str, Any]) -> str:
        """Render permission denied reminder for Write tool.

        Args:
            context: Execution context with agent_name, reason (optional)

        Returns:
            Formatted system reminder message
        """
        agent = context.get("agent_name", "Agent")
        reason = context.get("reason", "read-only permission restrictions")
        file_path = context.get("file_path", "file")

        return f"""<system-reminder>
The {agent} attempted to use the Write tool but was denied due to {reason}.

Target file: {file_path}

Reason: {agent} agents are restricted to read-only operations to prevent data loss or corruption.

Alternative approaches:
- Use Read tool to view existing file contents
- Propose file content to Main agent with Write recommendation
- Main agent can perform the actual file creation/modification

Best practice: Separate read-only exploration from write operations for safety.
</system-reminder>"""
