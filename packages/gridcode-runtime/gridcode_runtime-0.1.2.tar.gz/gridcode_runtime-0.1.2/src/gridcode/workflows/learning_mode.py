"""Learning Mode Manager for user feedback collection and improvement.

This module implements Learning Mode, which observes user corrections
and improves agent behavior over time:
1. Captures user feedback (corrections, preferences, approvals, rejections)
2. Identifies patterns in corrections
3. Generates improvement suggestions
4. Persists feedback history for analysis

Learning Mode integrates with:
- GridCodeRuntime for execution and notifications
- System Reminders for context-aware hints
- InteractionHandler for user feedback collection
- Storage backends for persistence (optional)
"""

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

from loguru import logger
from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from gridcode.core.context import ExecutionContext
    from gridcode.core.runtime import GridCodeRuntime


class FeedbackType(Enum):
    """Types of user feedback."""

    CORRECTION = auto()  # User corrects an error
    PREFERENCE = auto()  # User expresses a preference
    APPROVAL = auto()  # User approves a response
    REJECTION = auto()  # User rejects a response


class FeedbackCategory(Enum):
    """Categories of feedback for pattern analysis."""

    CODE_STYLE = auto()  # Code formatting, naming conventions
    ARCHITECTURE = auto()  # Design patterns, structure decisions
    DOCUMENTATION = auto()  # Comments, docstrings, explanations
    TESTING = auto()  # Test coverage, test patterns
    PERFORMANCE = auto()  # Optimization, efficiency
    SECURITY = auto()  # Security practices
    COMMUNICATION = auto()  # Response style, verbosity
    TOOL_USAGE = auto()  # Tool selection, command preferences
    OTHER = auto()  # Uncategorized


@dataclass
class FeedbackRecord:
    """Record of user feedback.

    Attributes:
        feedback_id: Unique identifier for this feedback
        feedback_type: Type of feedback (correction, preference, etc.)
        category: Category of feedback for analysis
        context: The context that triggered the feedback
        original_response: The agent's original response
        user_feedback: The user's feedback content
        timestamp: When the feedback was recorded
        tags: Optional tags for categorization
        metadata: Additional metadata
    """

    feedback_id: str
    feedback_type: FeedbackType
    category: FeedbackCategory
    context: str
    original_response: str
    user_feedback: str
    timestamp: datetime = field(default_factory=datetime.now)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "feedback_id": self.feedback_id,
            "feedback_type": self.feedback_type.name,
            "category": self.category.name,
            "context": self.context,
            "original_response": self.original_response,
            "user_feedback": self.user_feedback,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FeedbackRecord":
        """Create from dictionary."""
        return cls(
            feedback_id=data["feedback_id"],
            feedback_type=FeedbackType[data["feedback_type"]],
            category=FeedbackCategory[data["category"]],
            context=data["context"],
            original_response=data["original_response"],
            user_feedback=data["user_feedback"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )


class FeedbackPattern(BaseModel):
    """Pattern identified from feedback analysis."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    pattern_id: str
    description: str
    category: FeedbackCategory
    frequency: int = 0
    examples: list[str] = []
    suggestion: str = ""


class LearningModeManager:
    """Manager for Learning Mode workflow.

    Learning mode observes user corrections and improves over time:
    - Captures user feedback during interactions
    - Identifies patterns in corrections
    - Generates improvement suggestions
    - Persists feedback for cross-session learning

    Example:
        runtime = GridCodeRuntime(api_key="...", interaction=handler)
        manager = LearningModeManager(runtime)

        # Enter learning mode
        await manager.enter_learning_mode()

        # Record feedback as it occurs
        await manager.record_feedback(feedback)

        # Analyze patterns
        patterns = await manager.analyze_patterns()

        # Exit learning mode
        await manager.exit_learning_mode()
    """

    def __init__(
        self,
        runtime: "GridCodeRuntime",
        max_history: int = 1000,
    ):
        """Initialize the LearningModeManager.

        Args:
            runtime: The GridCodeRuntime instance to use
            max_history: Maximum number of feedback records to keep in memory
        """
        self.runtime = runtime
        self.max_history = max_history
        self.is_active: bool = False
        self.feedback_history: list[FeedbackRecord] = []
        self._feedback_counter: int = 0
        self._patterns_cache: list[FeedbackPattern] | None = None

    @property
    def context(self) -> "ExecutionContext":
        """Get the runtime's current execution context."""
        if not hasattr(self.runtime, "_context"):
            from gridcode.core.context import ExecutionContext

            self.runtime._context = ExecutionContext()
        return self.runtime._context

    @context.setter
    def context(self, value: "ExecutionContext") -> None:
        """Set the runtime's execution context."""
        self.runtime._context = value

    async def enter_learning_mode(self) -> None:
        """Enter learning mode and notify the user.

        Sets is_learning_mode flag on context and notifies user.
        """
        if self.is_active:
            logger.warning("Already in learning mode")
            return

        self.is_active = True
        self.context.is_learning_mode = True

        await self.runtime.notify_user(
            "Learning mode activated. I will observe and learn from your corrections.",
            level="info",
        )

        logger.info("Entered learning mode")

    async def exit_learning_mode(self) -> None:
        """Exit learning mode and notify the user.

        Clears is_learning_mode flag and provides summary.
        """
        if not self.is_active:
            logger.warning("Not in learning mode")
            return

        self.is_active = False
        self.context.is_learning_mode = False

        # Provide summary
        feedback_count = len(self.feedback_history)
        if feedback_count > 0:
            patterns = await self.analyze_patterns()
            summary = (
                f"Learning mode deactivated. "
                f"Collected {feedback_count} feedback records, "
                f"identified {len(patterns)} patterns."
            )
        else:
            summary = "Learning mode deactivated. No feedback collected."

        await self.runtime.notify_user(summary, level="info")

        logger.info(f"Exited learning mode with {feedback_count} feedback records")

    def _generate_feedback_id(self) -> str:
        """Generate a unique feedback ID."""
        self._feedback_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"fb_{timestamp}_{self._feedback_counter:04d}"

    async def record_feedback(
        self,
        feedback_type: FeedbackType,
        context: str,
        original_response: str,
        user_feedback: str,
        category: FeedbackCategory = FeedbackCategory.OTHER,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> FeedbackRecord:
        """Record user feedback.

        Args:
            feedback_type: Type of feedback
            context: The context that triggered the feedback
            original_response: The agent's original response
            user_feedback: The user's feedback content
            category: Category of feedback
            tags: Optional tags for categorization
            metadata: Additional metadata

        Returns:
            The created FeedbackRecord
        """
        record = FeedbackRecord(
            feedback_id=self._generate_feedback_id(),
            feedback_type=feedback_type,
            category=category,
            context=context,
            original_response=original_response,
            user_feedback=user_feedback,
            tags=tags or [],
            metadata=metadata or {},
        )

        # Add to history (with size limit)
        self.feedback_history.append(record)
        if len(self.feedback_history) > self.max_history:
            self.feedback_history = self.feedback_history[-self.max_history :]

        # Invalidate patterns cache
        self._patterns_cache = None

        logger.debug(f"Recorded feedback: {record.feedback_id} ({feedback_type.name})")

        return record

    async def record_correction(
        self,
        context: str,
        original_response: str,
        corrected_response: str,
        category: FeedbackCategory = FeedbackCategory.OTHER,
    ) -> FeedbackRecord:
        """Convenience method to record a correction.

        Args:
            context: The context that triggered the correction
            original_response: The agent's original response
            corrected_response: The user's corrected version
            category: Category of feedback

        Returns:
            The created FeedbackRecord
        """
        return await self.record_feedback(
            feedback_type=FeedbackType.CORRECTION,
            context=context,
            original_response=original_response,
            user_feedback=corrected_response,
            category=category,
        )

    async def record_preference(
        self,
        context: str,
        preference: str,
        category: FeedbackCategory = FeedbackCategory.OTHER,
    ) -> FeedbackRecord:
        """Convenience method to record a preference.

        Args:
            context: The context for the preference
            preference: The user's stated preference
            category: Category of feedback

        Returns:
            The created FeedbackRecord
        """
        return await self.record_feedback(
            feedback_type=FeedbackType.PREFERENCE,
            context=context,
            original_response="",
            user_feedback=preference,
            category=category,
        )

    async def analyze_patterns(self) -> list[FeedbackPattern]:
        """Analyze feedback patterns from history.

        Identifies common patterns in user corrections and preferences.

        Returns:
            List of identified FeedbackPattern objects
        """
        # Return cached patterns if available
        if self._patterns_cache is not None:
            return self._patterns_cache

        patterns: list[FeedbackPattern] = []

        if not self.feedback_history:
            return patterns

        # Group feedback by category
        by_category: dict[FeedbackCategory, list[FeedbackRecord]] = {}
        for record in self.feedback_history:
            if record.category not in by_category:
                by_category[record.category] = []
            by_category[record.category].append(record)

        # Analyze each category
        for category, records in by_category.items():
            if len(records) >= 2:  # Only report patterns with multiple occurrences
                # Count feedback types within category
                type_counts = Counter(r.feedback_type for r in records)
                dominant_type = type_counts.most_common(1)[0][0]

                pattern = FeedbackPattern(
                    pattern_id=f"pattern_{category.name.lower()}",
                    description=(
                        f"Recurring {dominant_type.name.lower()} feedback "
                        f"in {category.name.lower()}"
                    ),
                    category=category,
                    frequency=len(records),
                    examples=[r.user_feedback[:100] for r in records[:3]],
                    suggestion=self._generate_suggestion(category, records),
                )
                patterns.append(pattern)

        # Cache the patterns
        self._patterns_cache = patterns

        logger.info(f"Analyzed patterns: found {len(patterns)} patterns")

        return patterns

    def _generate_suggestion(
        self,
        category: FeedbackCategory,
        records: list[FeedbackRecord],
    ) -> str:
        """Generate improvement suggestion based on feedback pattern.

        Args:
            category: The feedback category
            records: Feedback records in this category

        Returns:
            Suggestion string
        """
        suggestion_templates = {
            FeedbackCategory.CODE_STYLE: "Consider adjusting code style to match user preferences",
            FeedbackCategory.ARCHITECTURE: "Review architectural decisions based on user feedback",
            FeedbackCategory.DOCUMENTATION: "Improve documentation based on clarity feedback",
            FeedbackCategory.TESTING: "Enhance test coverage per user expectations",
            FeedbackCategory.PERFORMANCE: "Optimize for performance as indicated by feedback",
            FeedbackCategory.SECURITY: "Strengthen security practices based on feedback",
            FeedbackCategory.COMMUNICATION: "Adjust communication style per user preferences",
            FeedbackCategory.TOOL_USAGE: "Refine tool selection based on user guidance",
            FeedbackCategory.OTHER: "Review general feedback for improvement opportunities",
        }

        base_suggestion = suggestion_templates.get(
            category, "Review feedback for improvement opportunities"
        )

        # Count correction vs preference
        corrections = sum(1 for r in records if r.feedback_type == FeedbackType.CORRECTION)
        preferences = sum(1 for r in records if r.feedback_type == FeedbackType.PREFERENCE)

        if corrections > preferences:
            return f"{base_suggestion}. Focus on reducing errors ({corrections} corrections)."
        else:
            return f"{base_suggestion}. Align with user preferences ({preferences} noted)."

    async def suggest_improvements(self) -> list[str]:
        """Generate improvement suggestions based on feedback patterns.

        Returns:
            List of improvement suggestion strings
        """
        patterns = await self.analyze_patterns()

        # Sort by frequency (most common first)
        patterns.sort(key=lambda p: p.frequency, reverse=True)

        suggestions = []
        for pattern in patterns[:5]:  # Top 5 patterns
            suggestion = (
                f"[{pattern.category.name}] {pattern.suggestion} "
                f"(observed {pattern.frequency} times)"
            )
            suggestions.append(suggestion)

        return suggestions

    def get_feedback_by_type(self, feedback_type: FeedbackType) -> list[FeedbackRecord]:
        """Get all feedback records of a specific type.

        Args:
            feedback_type: The type to filter by

        Returns:
            List of matching FeedbackRecord objects
        """
        return [r for r in self.feedback_history if r.feedback_type == feedback_type]

    def get_feedback_by_category(self, category: FeedbackCategory) -> list[FeedbackRecord]:
        """Get all feedback records in a specific category.

        Args:
            category: The category to filter by

        Returns:
            List of matching FeedbackRecord objects
        """
        return [r for r in self.feedback_history if r.category == category]

    def get_recent_feedback(self, count: int = 10) -> list[FeedbackRecord]:
        """Get the most recent feedback records.

        Args:
            count: Number of records to return

        Returns:
            List of most recent FeedbackRecord objects
        """
        return self.feedback_history[-count:]

    def clear_history(self) -> int:
        """Clear all feedback history.

        Returns:
            Number of records cleared
        """
        count = len(self.feedback_history)
        self.feedback_history = []
        self._patterns_cache = None
        logger.info(f"Cleared {count} feedback records")
        return count

    def export_feedback(self) -> list[dict[str, Any]]:
        """Export feedback history as list of dictionaries.

        Returns:
            List of feedback records as dictionaries
        """
        return [record.to_dict() for record in self.feedback_history]

    def import_feedback(self, data: list[dict[str, Any]]) -> int:
        """Import feedback records from list of dictionaries.

        Args:
            data: List of feedback records as dictionaries

        Returns:
            Number of records imported
        """
        imported = 0
        for item in data:
            try:
                record = FeedbackRecord.from_dict(item)
                self.feedback_history.append(record)
                imported += 1
            except (KeyError, ValueError) as e:
                logger.warning(f"Failed to import feedback record: {e}")

        # Invalidate patterns cache
        self._patterns_cache = None

        # Enforce max history limit
        if len(self.feedback_history) > self.max_history:
            self.feedback_history = self.feedback_history[-self.max_history :]

        logger.info(f"Imported {imported} feedback records")
        return imported

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about feedback history.

        Returns:
            Dictionary with feedback statistics
        """
        if not self.feedback_history:
            return {
                "total_records": 0,
                "by_type": {},
                "by_category": {},
                "date_range": None,
            }

        by_type = Counter(r.feedback_type.name for r in self.feedback_history)
        by_category = Counter(r.category.name for r in self.feedback_history)

        timestamps = [r.timestamp for r in self.feedback_history]
        date_range = {
            "earliest": min(timestamps).isoformat(),
            "latest": max(timestamps).isoformat(),
        }

        return {
            "total_records": len(self.feedback_history),
            "by_type": dict(by_type),
            "by_category": dict(by_category),
            "date_range": date_range,
        }
