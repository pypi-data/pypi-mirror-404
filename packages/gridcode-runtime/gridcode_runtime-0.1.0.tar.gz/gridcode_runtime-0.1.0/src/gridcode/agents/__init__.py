"""
GridCode Runtime Agent System

This module provides the agent system for GridCode Runtime, including:
- BaseAgent: Abstract base class for all agents
- ExploreAgent: Read-only codebase exploration agent
- PlanAgent: Implementation design and planning agent
- ReviewAgent: Code review and quality analysis agent
- TestRunnerAgent: Test execution and analysis agent
- Expert Agents: CodeReviewerAgent, DebuggerAgent, ArchitectAgent
- Documentation Agents: DocsArchitectAgent, TutorialEngineerAgent, APIDocumenterAgent
- AgentPool: Agent lifecycle management and parallel execution
- AgentFactory: Factory for creating agent instances
- MessageBus: Inter-agent communication using publish-subscribe pattern
- ResultAggregator: Aggregate results from multiple agents

Note: This module uses lazy loading for non-critical components to improve startup time.
Core classes (BaseAgent, AgentPool) are imported immediately, while specialized agents
are loaded on-demand.
"""

# Import only essential classes that are commonly needed
from gridcode.agents.base import (
    AgentResult,
    AgentStatus,
    AgentType,
    BaseAgent,
)
from gridcode.agents.pool import AgentFactory, AgentPool

__all__ = [
    # Base classes and enums (always imported)
    "BaseAgent",
    "AgentType",
    "AgentStatus",
    "AgentResult",
    "AgentPool",
    "AgentFactory",
    # Lazy-loaded exports
    "ExploreAgent",
    "PlanAgent",
    "PlanPerspective",
    "ReviewAgent",
    "ReviewCategory",
    "ReviewSeverity",
    "ReviewFinding",
    "ReviewReport",
    "TestRunnerAgent",
    "CodeReviewerAgent",
    "CodeReviewReport",
    "CodeIssue",
    "ReviewFocus",
    "IssueSeverity",
    "DebuggerAgent",
    "DebugReport",
    "BugDiagnosis",
    "DebugMode",
    "BugSeverity",
    "BugCategory",
    "ArchitectAgent",
    "ArchitectureReport",
    "ArchitectureConcern",
    "ModuleAnalysis",
    "AnalysisFocus",
    "ArchitecturePattern",
    "HealthStatus",
    "ConcernSeverity",
    "BaseDocumentationAgent",
    "DocsArchitectAgent",
    "DocScope",
    "TutorialEngineerAgent",
    "APIDocumenterAgent",
    "APIScope",
    "DocFormat",
    "TargetAudience",
    "SkillLevel",
    "DocumentSection",
    "DocumentationOutput",
    "MessageBus",
    "Message",
    "MessageType",
    "ResultAggregator",
    "AggregatedResult",
    "AggregationStrategy",
    "BaseAggregator",
    "MergeAggregator",
    "FirstSuccessAggregator",
    "PriorityAggregator",
    "BestScoreAggregator",
]

# Lazy loading module map - imports occur on first access
_LAZY_MODULES = {
    # Core agents
    "ExploreAgent": ("gridcode.agents.explore", "ExploreAgent"),
    "PlanAgent": ("gridcode.agents.plan", "PlanAgent"),
    "PlanPerspective": ("gridcode.agents.plan", "PlanPerspective"),
    "ReviewAgent": ("gridcode.agents.review", "ReviewAgent"),
    "ReviewCategory": ("gridcode.agents.review", "ReviewCategory"),
    "ReviewSeverity": ("gridcode.agents.review", "ReviewSeverity"),
    "ReviewFinding": ("gridcode.agents.review", "ReviewFinding"),
    "ReviewReport": ("gridcode.agents.review", "ReviewReport"),
    "TestRunnerAgent": ("gridcode.agents.test_runner", "TestRunnerAgent"),
    # Expert agents
    "CodeReviewerAgent": ("gridcode.agents.experts", "CodeReviewerAgent"),
    "CodeReviewReport": ("gridcode.agents.experts", "CodeReviewReport"),
    "CodeIssue": ("gridcode.agents.experts", "CodeIssue"),
    "ReviewFocus": ("gridcode.agents.experts", "ReviewFocus"),
    "IssueSeverity": ("gridcode.agents.experts", "IssueSeverity"),
    "DebuggerAgent": ("gridcode.agents.experts", "DebuggerAgent"),
    "DebugReport": ("gridcode.agents.experts", "DebugReport"),
    "BugDiagnosis": ("gridcode.agents.experts", "BugDiagnosis"),
    "DebugMode": ("gridcode.agents.experts", "DebugMode"),
    "BugSeverity": ("gridcode.agents.experts", "BugSeverity"),
    "BugCategory": ("gridcode.agents.experts", "BugCategory"),
    "ArchitectAgent": ("gridcode.agents.experts", "ArchitectAgent"),
    "ArchitectureReport": ("gridcode.agents.experts", "ArchitectureReport"),
    "ArchitectureConcern": ("gridcode.agents.experts", "ArchitectureConcern"),
    "ModuleAnalysis": ("gridcode.agents.experts", "ModuleAnalysis"),
    "AnalysisFocus": ("gridcode.agents.experts", "AnalysisFocus"),
    "ArchitecturePattern": ("gridcode.agents.experts", "ArchitecturePattern"),
    "HealthStatus": ("gridcode.agents.experts", "HealthStatus"),
    "ConcernSeverity": ("gridcode.agents.experts", "ConcernSeverity"),
    # Documentation agents
    "BaseDocumentationAgent": ("gridcode.agents.documentation", "BaseDocumentationAgent"),
    "DocsArchitectAgent": ("gridcode.agents.documentation", "DocsArchitectAgent"),
    "DocScope": ("gridcode.agents.documentation", "DocScope"),
    "TutorialEngineerAgent": ("gridcode.agents.documentation", "TutorialEngineerAgent"),
    "APIDocumenterAgent": ("gridcode.agents.documentation", "APIDocumenterAgent"),
    "APIScope": ("gridcode.agents.documentation", "APIScope"),
    "DocFormat": ("gridcode.agents.documentation", "DocFormat"),
    "TargetAudience": ("gridcode.agents.documentation", "TargetAudience"),
    "SkillLevel": ("gridcode.agents.documentation", "SkillLevel"),
    "DocumentSection": ("gridcode.agents.documentation", "DocumentSection"),
    "DocumentationOutput": ("gridcode.agents.documentation", "DocumentationOutput"),
    # Communication
    "MessageBus": ("gridcode.agents.message_bus", "MessageBus"),
    "Message": ("gridcode.agents.message_bus", "Message"),
    "MessageType": ("gridcode.agents.message_bus", "MessageType"),
    # Aggregation
    "ResultAggregator": ("gridcode.agents.aggregator", "ResultAggregator"),
    "AggregatedResult": ("gridcode.agents.aggregator", "AggregatedResult"),
    "AggregationStrategy": ("gridcode.agents.aggregator", "AggregationStrategy"),
    "BaseAggregator": ("gridcode.agents.aggregator", "BaseAggregator"),
    "MergeAggregator": ("gridcode.agents.aggregator", "MergeAggregator"),
    "FirstSuccessAggregator": ("gridcode.agents.aggregator", "FirstSuccessAggregator"),
    "PriorityAggregator": ("gridcode.agents.aggregator", "PriorityAggregator"),
    "BestScoreAggregator": ("gridcode.agents.aggregator", "BestScoreAggregator"),
}

# Cache for lazy-loaded modules to avoid repeated imports
_LAZY_CACHE = {}


def __getattr__(name: str):
    """Lazy load agent modules on first access."""
    if name in _LAZY_MODULES:
        if name not in _LAZY_CACHE:
            module_name, class_name = _LAZY_MODULES[name]
            module = __import__(module_name, fromlist=[class_name])
            _LAZY_CACHE[name] = getattr(module, class_name)
        return _LAZY_CACHE[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
