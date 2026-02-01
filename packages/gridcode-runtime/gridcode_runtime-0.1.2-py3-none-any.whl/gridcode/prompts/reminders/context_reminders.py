"""Context-aware reminders.

Reminders about the current execution context:
- Git status information
- Working directory reminders
"""

from typing import Any

from gridcode.prompts.reminders.base import SystemReminder


class GitStatusReminder(SystemReminder):
    """Reminder about current git status."""

    name: str = "git_status"
    priority: int = 3  # Low priority - informational

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when git status information is available and noteworthy."""
        # Trigger if there are uncommitted changes or we're on a non-main branch
        has_changes = context.get("git_has_uncommitted_changes", False)
        branch = context.get("git_branch", "")
        is_non_main = branch and branch not in ("main", "master")
        return context.get("show_git_status", False) and (has_changes or is_non_main)

    def render(self, context: dict[str, Any]) -> str:
        """Render git status reminder."""
        branch = context.get("git_branch", "unknown")
        has_changes = context.get("git_has_uncommitted_changes", False)
        modified_files = context.get("git_modified_files", [])

        parts = [f"Current git branch: {branch}"]

        if has_changes:
            parts.append("You have uncommitted changes.")
            if modified_files:
                files_str = ", ".join(modified_files[:5])
                if len(modified_files) > 5:
                    files_str += f" (+{len(modified_files) - 5} more)"
                parts.append(f"Modified files: {files_str}")

        return f"""<system-reminder>
{" ".join(parts)}
</system-reminder>"""


class WorkingDirectoryReminder(SystemReminder):
    """Reminder about the current working directory."""

    name: str = "working_directory"
    priority: int = 3  # Low priority - informational

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when working directory info should be shown.

        This is typically shown at the start of a session or when
        the working directory changes.
        """
        return context.get("show_working_directory", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render working directory reminder."""
        working_dir = context.get("working_directory", "unknown")
        project_name = context.get("project_name", "")

        if project_name:
            return f"""<system-reminder>
Working directory: {working_dir}
Project: {project_name}
</system-reminder>"""
        else:
            return f"""<system-reminder>
Working directory: {working_dir}
</system-reminder>"""


class SecurityWarningReminder(SystemReminder):
    """Reminder about security-sensitive operations."""

    name: str = "security_warning"
    priority: int = 16  # Highest priority - security matters

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when a security-sensitive operation is detected."""
        return context.get("security_warning", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render security warning."""
        warning_type = context.get("security_warning_type", "general")
        details = context.get("security_warning_details", "")

        warnings = {
            "credentials": """<system-reminder>
SECURITY WARNING: The operation involves credentials or secrets.
- Never expose API keys, passwords, or tokens in output
- Do not commit sensitive files (.env, credentials.json, etc.)
- Suggest using environment variables instead of hardcoded secrets
</system-reminder>""",
            "network": """<system-reminder>
SECURITY WARNING: Network operation detected.
- Verify URLs before making requests
- Be cautious with external APIs
- Don't send sensitive data to unknown endpoints
</system-reminder>""",
            "file_permission": """<system-reminder>
SECURITY WARNING: File permission change detected.
- Avoid making files world-writable
- Be cautious with executable permissions
- Review the security implications
</system-reminder>""",
            "general": f"""<system-reminder>
SECURITY WARNING: {details or "A security-sensitive operation was detected."}
Please proceed with caution and verify the operation is safe.
</system-reminder>""",
        }

        return warnings.get(warning_type, warnings["general"])
