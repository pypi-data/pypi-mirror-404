"""MCP resource reminders.

Reminders about MCP (Model Context Protocol) resource states:
- No content available
- Resource display issues
"""

from typing import Any

from gridcode.prompts.reminders.base import SystemReminder


class MCPResourceNoContentReminder(SystemReminder):
    """Reminder when MCP resource has no content."""

    name: str = "mcp_resource_no_content"
    priority: int = 7  # Medium priority - informational

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when MCP resource has no content."""
        return context.get("mcp_resource_empty", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render MCP resource no content reminder."""
        server = context.get("mcp_server", "unknown")
        uri = context.get("mcp_uri", "unknown")
        return f"""<system-reminder>
<mcp-resource server="{server}" uri="{uri}">(No content)</mcp-resource>
</system-reminder>"""


class MCPResourceNoDisplayableContentReminder(SystemReminder):
    """Reminder when MCP resource content cannot be displayed.

    This occurs when the resource contains binary data, non-text formats,
    or content that cannot be rendered in the current context.
    """

    name: str = "mcp_resource_no_displayable_content"
    priority: int = 7  # Medium priority - informational

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when MCP resource content is not displayable."""
        return context.get("mcp_resource_not_displayable", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render MCP resource no displayable content reminder."""
        server = context.get("mcp_server", "unknown")
        uri = context.get("mcp_uri", "unknown")
        content_type = context.get("content_type", "binary")
        size = context.get("content_size", "unknown")

        return f"""<system-reminder>
MCP resource from server "{server}" (URI: {uri}) contains non-displayable content.

Content type: {content_type}
Size: {size} bytes

This resource cannot be rendered as text. Possible reasons:
- Binary data (images, executables, archives)
- Proprietary or encoded formats
- Content exceeds display limits

Alternatives:
- Check if the MCP server provides a text summary or metadata
- Request a different resource format if available
- Use specialized tools to process the binary content
</system-reminder>"""
