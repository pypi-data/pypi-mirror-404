"""Learning mode reminders.

Reminders specific to the learning mode workflow:
- Feedback recorded confirmation
- Pattern identified notification
- Improvement suggestion available
"""

from typing import Any

from gridcode.prompts.reminders.base import SystemReminder


class FeedbackRecordedReminder(SystemReminder):
    """Reminder when feedback has been recorded."""

    name: str = "feedback_recorded"
    priority: int = 8  # Medium priority - informational

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when feedback_just_recorded is True."""
        return context.get("feedback_just_recorded", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render feedback recorded confirmation."""
        feedback_type = context.get("feedback_type", "feedback")
        feedback_category = context.get("feedback_category", "general")
        feedback_count = context.get("feedback_count", 1)

        return f"""<system-reminder>
Your {feedback_type} has been recorded for learning.
Category: {feedback_category}
Total feedback recorded this session: {feedback_count}

This feedback will help improve future responses in similar contexts.
</system-reminder>"""


class PatternIdentifiedReminder(SystemReminder):
    """Reminder when a recurring pattern has been identified."""

    name: str = "pattern_identified"
    priority: int = 10  # Higher priority - actionable insight

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when pattern_identified is True."""
        return context.get("pattern_identified", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render pattern identification notification."""
        pattern_description = context.get("pattern_description", "a recurring pattern")
        pattern_frequency = context.get("pattern_frequency", "multiple times")
        suggested_action = context.get("suggested_action", "adjusting behavior")

        return f"""<system-reminder>
Pattern identified: {pattern_description}
Frequency: {pattern_frequency}

Based on this pattern, I am {suggested_action} to better match your preferences.
</system-reminder>"""


class ImprovementSuggestionReminder(SystemReminder):
    """Reminder when improvement suggestions are available."""

    name: str = "improvement_suggestion"
    priority: int = 9  # Medium-high priority - actionable

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when improvement_suggestion_available is True."""
        return context.get("improvement_suggestion_available", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render improvement suggestion notification."""
        suggestion_count = context.get("suggestion_count", 1)
        top_suggestion = context.get("top_suggestion", "Review recent feedback patterns")

        return f"""<system-reminder>
{suggestion_count} improvement suggestion(s) available based on learning feedback.

Top suggestion: {top_suggestion}

Use the learning mode manager to view all suggestions and apply improvements.
</system-reminder>"""


class LearningSessionSummaryReminder(SystemReminder):
    """Reminder providing learning session summary when exiting learning mode."""

    name: str = "learning_session_summary"
    priority: int = 12  # Higher priority - session transition

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when learning_mode_ending is True."""
        return context.get("learning_mode_ending", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render learning session summary."""
        total_feedback = context.get("session_feedback_count", 0)
        patterns_found = context.get("patterns_found", 0)
        corrections_made = context.get("corrections_count", 0)
        preferences_learned = context.get("preferences_count", 0)

        return f"""<system-reminder>
Learning mode session summary:

- Total feedback recorded: {total_feedback}
- Patterns identified: {patterns_found}
- Corrections processed: {corrections_made}
- Preferences learned: {preferences_learned}

These learnings will be applied to future interactions in this session.
</system-reminder>"""


class LearningContextReminder(SystemReminder):
    """Reminder about active learning context and focus areas."""

    name: str = "learning_context"
    priority: int = 7  # Lower priority - background context

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when in learning mode and has active learning context."""
        return context.get("is_learning_mode", False) and context.get("has_learning_context", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render learning context reminder."""
        focus_areas = context.get("learning_focus_areas", [])
        recent_corrections = context.get("recent_corrections_count", 0)

        focus_str = ", ".join(focus_areas) if focus_areas else "general"

        return f"""<system-reminder>
Learning mode is observing and adapting.

Focus areas: {focus_str}
Recent corrections: {recent_corrections}

Corrections and feedback will be used to refine responses.
</system-reminder>"""
