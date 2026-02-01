"""Git operation reminders for external file modifications."""

from typing import Any

from gridcode.prompts.reminders.base import SystemReminder


class GitModifiedByUserReminder(SystemReminder):
    """Reminder triggered when files are modified externally by user, IDE, or linter.

    This reminder alerts the agent that files have been changed outside of the agent's
    control, ensuring the agent does not accidentally revert these intentional changes.
    """

    name: str = "git_modified_by_user"
    priority: int = 13  # High priority - just below Hook level

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Check if files were modified externally.

        Args:
            context: Must contain 'file_modified_externally' = True

        Returns:
            True if files were externally modified, False otherwise
        """
        return context.get("file_modified_externally", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render external modification reminder.

        Args:
            context: Execution context with:
                - modified_files: list[str] - List of modified file paths
                - modifier: str - Who modified (e.g., "user", "IDE", "linter")

        Returns:
            Formatted system reminder message
        """
        files = context.get("modified_files", [])
        modifier = context.get("modifier", "user or linter")

        if not files:
            return """<system-reminder>
Files were modified externally, but the specific file list is unavailable.

IMPORTANT: Do NOT revert changes unless explicitly requested by the user.
</system-reminder>"""

        # Show up to 5 files, then "... and N more"
        file_list = "\n".join([f"  - {f}" for f in files[:5]])
        more = f"\n  ... and {len(files) - 5} more" if len(files) > 5 else ""

        return f"""<system-reminder>
Note: The following files were modified externally (by {modifier}):
{file_list}{more}

IMPORTANT: These changes were intentional and should NOT be reverted unless the user explicitly requests it.

Context:
- These modifications may have been made by the user in their IDE
- A linter or formatter (e.g., black, isort, prettier) may have auto-formatted the code
- The user may have manually edited files outside of this session

Best practice: Check the actual changes with 'git diff' before making further modifications to these files.
</system-reminder>"""  # noqa: E501


class GitRepoDirtyReminder(SystemReminder):
    """Reminder triggered when Git working directory has uncommitted changes.

    This reminder alerts the agent to unstaged or uncommitted changes that may
    affect the current operation.
    """

    name: str = "git_repo_dirty"
    priority: int = 10  # Medium priority

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Check if Git repo has uncommitted changes.

        Args:
            context: Must contain 'git_repo_dirty' = True

        Returns:
            True if repo has uncommitted changes, False otherwise
        """
        return context.get("git_repo_dirty", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render Git dirty state reminder.

        Args:
            context: Execution context with:
                - unstaged_files: list[str] - Unstaged file paths
                - staged_files: list[str] - Staged file paths

        Returns:
            Formatted system reminder message
        """
        unstaged = context.get("unstaged_files", [])
        staged = context.get("staged_files", [])

        parts = []
        if staged:
            staged_list = "\n".join([f"  - {f}" for f in staged[:3]])
            more = f"\n  ... and {len(staged) - 3} more" if len(staged) > 3 else ""
            parts.append(f"Staged changes:\n{staged_list}{more}")

        if unstaged:
            unstaged_list = "\n".join([f"  - {f}" for f in unstaged[:3]])
            more = f"\n  ... and {len(unstaged) - 3} more" if len(unstaged) > 3 else ""
            parts.append(f"Unstaged changes:\n{unstaged_list}{more}")

        changes_summary = "\n\n".join(parts) if parts else "Files have been modified"

        return f"""<system-reminder>
Note: Git working directory has uncommitted changes.

{changes_summary}

Consider:
- Review changes with 'git diff' before making further modifications
- Commit or stash changes if starting a new feature
- Be aware that operations may interact with uncommitted work
</system-reminder>"""
