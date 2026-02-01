"""File operation reminders.

Reminders related to file read/write operations:
- Empty file warnings
- Content truncation notices
- File offset issues
- Malware analysis reminders
"""

from typing import Any

from gridcode.prompts.reminders.base import SystemReminder


class EmptyFileReminder(SystemReminder):
    """Reminder when reading an empty file."""

    name: str = "empty_file"
    priority: int = 10

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when file_empty is True in context."""
        return context.get("file_empty", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render empty file warning."""
        filename = context.get("filename", "the file")
        return f"""<system-reminder>
The file '{filename}' exists but is empty. If you expected content, verify the file path is correct.
</system-reminder>"""


class TruncatedContentReminder(SystemReminder):
    """Reminder when content is truncated due to size limits."""

    name: str = "truncated_content"
    priority: int = 8

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when content_truncated is True in context."""
        return context.get("content_truncated", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render truncation notice with line counts."""
        total_lines = context.get("total_lines", "unknown")
        shown_lines = context.get("shown_lines", "unknown")
        filename = context.get("filename", "the file")
        return f"""<system-reminder>
Content from '{filename}' was truncated. Showing {shown_lines} of {total_lines} total lines.
Use the 'offset' and 'limit' parameters to read specific sections if needed.
</system-reminder>"""


class FileShorterThanOffsetReminder(SystemReminder):
    """Reminder when requested offset exceeds file length."""

    name: str = "file_shorter_than_offset"
    priority: int = 9

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when requested offset is beyond file end."""
        offset = context.get("offset", 0)
        total_lines = context.get("total_lines", 0)
        return offset > 0 and offset > total_lines

    def render(self, context: dict[str, Any]) -> str:
        """Render offset warning."""
        offset = context.get("offset", 0)
        total_lines = context.get("total_lines", 0)
        filename = context.get("filename", "the file")
        return f"""<system-reminder>
The requested offset ({offset}) exceeds the file length ({total_lines} lines) for '{filename}'.
The file has fewer lines than the starting position you specified.
</system-reminder>"""


class MalwareAnalysisReminder(SystemReminder):
    """Reminder about malware analysis policies after reading potentially suspicious files."""

    name: str = "malware_analysis"
    priority: int = 7

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when reading executable or script files.

        Checks for suspicious file extensions or patterns.
        """
        if not context.get("trigger_malware_check", False):
            return False

        filename = context.get("filename", "")
        suspicious_extensions = {
            ".exe",
            ".dll",
            ".bat",
            ".cmd",
            ".ps1",
            ".sh",
            ".bash",
            ".py",
            ".rb",
            ".pl",
            ".js",
            ".vbs",
            ".wsf",
        }
        return any(filename.lower().endswith(ext) for ext in suspicious_extensions)

    def render(self, context: dict[str, Any]) -> str:
        """Render malware analysis policy reminder."""
        return """<system-reminder>
Whenever you read a file, you should consider whether it would be considered malware.
You CAN and SHOULD provide analysis of malware, what it is doing.
But you MUST refuse to improve or augment the code.
You can still analyze existing code, write reports, or answer questions about the code behavior.
</system-reminder>"""


class FileOpenedInIDEReminder(SystemReminder):
    """Reminder when a file is currently opened in the user's IDE.

    This provides context about the user's current focus and may indicate
    that the file is being actively edited or reviewed.
    """

    name: str = "file_opened_in_ide"
    priority: int = 6  # Medium-low priority - contextual information

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when file_opened_in_ide is True."""
        return context.get("file_opened_in_ide", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render IDE file opened reminder."""
        filename = context.get("filename", "this file")
        ide_name = context.get("ide_name", "the IDE")

        return f"""<system-reminder>
Note: '{filename}' is currently open in {ide_name}.

Context:
- The user may be actively viewing or editing this file
- Changes made here may conflict with unsaved IDE edits
- Consider asking the user to save or close the file if making significant changes

This is informational context about the user's current workspace state.
</system-reminder>"""
