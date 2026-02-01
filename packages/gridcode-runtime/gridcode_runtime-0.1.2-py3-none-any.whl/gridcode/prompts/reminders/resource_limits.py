"""Resource limit reminders.

Reminders about resource usage and limits:
- Token usage warnings
- Output limit exceeded notices
"""

from typing import Any

from gridcode.prompts.reminders.base import SystemReminder


class TokenUsageReminder(SystemReminder):
    """Reminder when token usage approaches or exceeds limits."""

    name: str = "token_usage"
    priority: int = 12  # Important - affects what can be done

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when token usage exceeds threshold.

        Context should contain:
        - tokens_used: Current token count
        - token_limit: Maximum allowed tokens
        - token_threshold: Percentage threshold (default 0.8)
        """
        tokens_used = context.get("tokens_used", 0)
        token_limit = context.get("token_limit", float("inf"))
        threshold = context.get("token_threshold", 0.8)

        if token_limit <= 0:
            return False

        return (tokens_used / token_limit) >= threshold

    def render(self, context: dict[str, Any]) -> str:
        """Render token usage warning."""
        tokens_used = context.get("tokens_used", 0)
        token_limit = context.get("token_limit", 0)
        percentage = (tokens_used / token_limit * 100) if token_limit > 0 else 0
        return f"""<system-reminder>
Token usage warning: {tokens_used:,} / {token_limit:,} tokens used ({percentage:.1f}%).

Consider:
- Completing the current task soon
- Using more concise responses
- Avoiding unnecessary file reads
- Summarizing rather than showing full content
</system-reminder>"""


class OutputLimitExceededReminder(SystemReminder):
    """Reminder when output is truncated due to size limits."""

    name: str = "output_limit_exceeded"
    priority: int = 12

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when output exceeds the limit."""
        return context.get("output_truncated", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render output limit warning."""
        output_size = context.get("output_size", "unknown")
        output_limit = context.get("output_limit", "unknown")
        return f"""<system-reminder>
Output was truncated because it exceeded the limit ({output_size} > {output_limit} characters).

The full content could not be displayed. Consider:
- Requesting specific sections of the content
- Using pagination with offset and limit
- Summarizing instead of showing full output
</system-reminder>"""


class USDBudgetReminder(SystemReminder):
    """Reminder about USD budget usage."""

    name: str = "usd_budget"
    priority: int = 11  # High priority - cost awareness

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when budget tracking is enabled."""
        return context.get("track_budget", False) and context.get("budget_used", 0) > 0

    def render(self, context: dict[str, Any]) -> str:
        """Render USD budget reminder."""
        used = context.get("budget_used", 0)
        total = context.get("budget_total", 0)
        remaining = total - used if total > 0 else 0

        return f"""<system-reminder>
USD budget: ${used:.2f}/${total:.2f}; ${remaining:.2f} remaining
</system-reminder>"""


class BudgetSoftLimitReminder(SystemReminder):
    """Reminder when budget usage reaches soft limit (80% threshold).

    Soft limit warning gives advance notice before hard limit is reached,
    allowing graceful completion of current work.
    """

    name: str = "budget_soft_limit"
    priority: int = 12  # High priority - budget awareness

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when budget usage >= 80% but < 100%.

        Args:
            context: Must contain 'budget_used', 'budget_total'

        Returns:
            True if 80% <= usage < 100%, False otherwise
        """
        used = context.get("budget_used", 0)
        total = context.get("budget_total", float("inf"))

        if total <= 0:
            return False

        percentage = used / total
        return 0.8 <= percentage < 1.0

    def render(self, context: dict[str, Any]) -> str:
        """Render soft limit warning.

        Args:
            context: Execution context with budget_used, budget_total

        Returns:
            Formatted system reminder message
        """
        used = context.get("budget_used", 0)
        total = context.get("budget_total", 0)
        remaining = total - used
        percentage = (used / total * 100) if total > 0 else 0

        return f"""<system-reminder>
⚠️ Budget soft limit warning: ${used:.2f}/${total:.2f} ({percentage:.1f}% used)

Remaining budget: ${remaining:.2f}

The budget is nearing its limit. Consider:
- Completing current tasks efficiently
- Avoiding unnecessary API calls or tool usage
- Prioritizing essential operations
- Preparing to gracefully conclude work

Hard limit will be enforced at 100% budget usage.
</system-reminder>"""


class BudgetHardLimitReminder(SystemReminder):
    """Reminder when budget usage reaches hard limit (100% threshold).

    Hard limit blocks further operations to prevent budget overruns.
    """

    name: str = "budget_hard_limit"
    priority: int = 13  # Very high priority - critical constraint

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when budget usage >= 100%.

        Args:
            context: Must contain 'budget_used', 'budget_total'

        Returns:
            True if usage >= 100%, False otherwise
        """
        used = context.get("budget_used", 0)
        total = context.get("budget_total", float("inf"))

        if total <= 0:
            return False

        return used >= total

    def render(self, context: dict[str, Any]) -> str:
        """Render hard limit error.

        Args:
            context: Execution context with budget_used, budget_total

        Returns:
            Formatted system reminder message
        """
        used = context.get("budget_used", 0)
        total = context.get("budget_total", 0)
        overage = used - total

        return f"""<system-reminder>
🛑 Budget hard limit reached: ${used:.2f}/${total:.2f} (budget exceeded by ${overage:.2f})

CRITICAL: No further operations are allowed until budget is increased.

Actions required:
- Summarize current progress and findings
- Provide user with status update
- Request budget increase if additional work is needed
- Do NOT attempt further API calls or expensive operations

The session will be terminated to prevent cost overruns.
</system-reminder>"""
