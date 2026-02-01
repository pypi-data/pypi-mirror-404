"""Workflow orchestration module for GridCode Runtime.

This module provides workflow management for different execution modes:
- PlanModeManager: 5-Phase Planning workflow orchestration
- LearningModeManager: Learning mode for observing and improving

Note: This module uses lazy loading - workflow managers are only imported
when first accessed, allowing faster startup for applications that don't
use these advanced modes.
"""

__all__ = [
    "PlanModeManager",
    "PlanPhase",
    "LearningModeManager",
    "FeedbackType",
    "FeedbackCategory",
    "FeedbackRecord",
    "FeedbackPattern",
]

# Lazy loading module map - imports occur on first access
_LAZY_MODULES = {
    "PlanModeManager": ("gridcode.workflows.plan_mode", "PlanModeManager"),
    "PlanPhase": ("gridcode.workflows.plan_mode", "PlanPhase"),
    "LearningModeManager": ("gridcode.workflows.learning_mode", "LearningModeManager"),
    "FeedbackType": ("gridcode.workflows.learning_mode", "FeedbackType"),
    "FeedbackCategory": ("gridcode.workflows.learning_mode", "FeedbackCategory"),
    "FeedbackRecord": ("gridcode.workflows.learning_mode", "FeedbackRecord"),
    "FeedbackPattern": ("gridcode.workflows.learning_mode", "FeedbackPattern"),
}

# Cache for lazy-loaded modules to avoid repeated imports
_LAZY_CACHE = {}


def __getattr__(name: str):
    """Lazy load workflow classes on first access."""
    if name in _LAZY_MODULES:
        if name not in _LAZY_CACHE:
            module_name, class_name = _LAZY_MODULES[name]
            module = __import__(module_name, fromlist=[class_name])
            _LAZY_CACHE[name] = getattr(module, class_name)
        return _LAZY_CACHE[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
