"""
Architect Expert Agent Module

Software architecture expert for system design, patterns, and scalability analysis.
Inspired by Claude Code's architecture analysis capabilities.
"""

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from loguru import logger

from gridcode.agents.base import AgentResult, AgentStatus, AgentType, BaseAgent
from gridcode.core.context import ExecutionContext
from gridcode.prompts.composer import PromptComposer


class AnalysisFocus(str, Enum):
    """Architecture analysis focus areas"""

    DESIGN = "design"  # Overall architecture pattern
    SCALABILITY = "scalability"  # Performance and scaling
    MAINTAINABILITY = "maintainability"  # Code quality and testability
    SECURITY = "security"  # Security architecture


class ArchitecturePattern(str, Enum):
    """Common architecture patterns"""

    LAYERED = "layered"
    HEXAGONAL = "hexagonal"
    MICROSERVICES = "microservices"
    MODULAR_MONOLITH = "modular_monolith"
    EVENT_DRIVEN = "event_driven"
    CQRS = "cqrs"
    UNKNOWN = "unknown"


class HealthStatus(str, Enum):
    """Module/component health status"""

    HEALTHY = "healthy"
    NEEDS_ATTENTION = "needs_attention"
    CRITICAL = "critical"


class ConcernSeverity(str, Enum):
    """Architecture concern severity"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ModuleAnalysis:
    """Analysis of a single module"""

    name: str
    responsibility: str
    dependencies: list[str] = field(default_factory=list)
    dependents: list[str] = field(default_factory=list)
    health: HealthStatus = HealthStatus.HEALTHY
    lines_of_code: int | None = None
    complexity_notes: str = ""


@dataclass
class ArchitectureConcern:
    """A single architecture concern"""

    category: str
    description: str
    severity: ConcernSeverity
    impact: str
    recommendation: str
    affected_modules: list[str] = field(default_factory=list)


@dataclass
class ArchitectureReport:
    """Complete architecture analysis report"""

    pattern: ArchitecturePattern = ArchitecturePattern.UNKNOWN
    domain_complexity: str = "moderate"
    overall_health: HealthStatus = HealthStatus.HEALTHY
    strengths: list[str] = field(default_factory=list)
    concerns: list[ArchitectureConcern] = field(default_factory=list)
    modules: list[ModuleAnalysis] = field(default_factory=list)
    dependency_graph: dict[str, list[str]] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    questions_for_stakeholders: list[str] = field(default_factory=list)
    summary: str = ""

    def add_module(self, module: ModuleAnalysis) -> None:
        """Add a module analysis to the report"""
        self.modules.append(module)

    def add_concern(self, concern: ArchitectureConcern) -> None:
        """Add a concern to the report"""
        self.concerns.append(concern)
        # Update overall health based on concern severity
        if concern.severity == ConcernSeverity.HIGH:
            if self.overall_health == HealthStatus.HEALTHY:
                self.overall_health = HealthStatus.NEEDS_ATTENTION
        elif (
            concern.severity == ConcernSeverity.HIGH
            and len([c for c in self.concerns if c.severity == ConcernSeverity.HIGH]) > 2
        ):
            self.overall_health = HealthStatus.CRITICAL

    @property
    def concern_count(self) -> int:
        return len(self.concerns)

    @property
    def high_priority_count(self) -> int:
        return len([c for c in self.concerns if c.severity == ConcernSeverity.HIGH])

    @property
    def module_count(self) -> int:
        return len(self.modules)

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary"""
        return {
            "pattern": self.pattern.value,
            "domain_complexity": self.domain_complexity,
            "overall_health": self.overall_health.value,
            "strengths": self.strengths,
            "concerns": [
                {
                    "category": c.category,
                    "description": c.description,
                    "severity": c.severity.value,
                    "impact": c.impact,
                    "recommendation": c.recommendation,
                    "affected_modules": c.affected_modules,
                }
                for c in self.concerns
            ],
            "modules": [
                {
                    "name": m.name,
                    "responsibility": m.responsibility,
                    "dependencies": m.dependencies,
                    "dependents": m.dependents,
                    "health": m.health.value,
                    "lines_of_code": m.lines_of_code,
                    "complexity_notes": m.complexity_notes,
                }
                for m in self.modules
            ],
            "dependency_graph": self.dependency_graph,
            "recommendations": self.recommendations,
            "questions_for_stakeholders": self.questions_for_stakeholders,
            "summary": self.summary,
        }

    def to_markdown(self) -> str:
        """Convert report to markdown format"""
        lines = ["# Architecture Review", ""]

        # Overview
        lines.append("## Overview")
        lines.append(f"- **Project Structure**: {self.pattern.value}")
        lines.append(f"- **Domain Complexity**: {self.domain_complexity}")
        lines.append(f"- **Architectural Health**: {self.overall_health.value}")
        lines.append(f"- **Modules Analyzed**: {self.module_count}")
        lines.append(
            f"- **Concerns Found**: {self.concern_count} ({self.high_priority_count} high)"
        )
        lines.append("")

        if self.summary:
            lines.append(self.summary)
            lines.append("")

        # Strengths
        if self.strengths:
            lines.append("## Strengths")
            for s in self.strengths:
                lines.append(f"- {s}")
            lines.append("")

        # Concerns
        if self.concerns:
            lines.append("## Concerns")
            for concern in self.concerns:
                lines.append(f"### [{concern.severity.value.upper()}] {concern.category}")
                lines.append(f"{concern.description}")
                lines.append(f"- **Impact**: {concern.impact}")
                lines.append(f"- **Recommendation**: {concern.recommendation}")
                if concern.affected_modules:
                    lines.append(f"- **Affected**: {', '.join(concern.affected_modules)}")
                lines.append("")

        # Module Analysis
        if self.modules:
            lines.append("## Module Analysis")
            lines.append("")
            lines.append("| Module | Responsibility | Dependencies | Health |")
            lines.append("|--------|---------------|--------------|--------|")
            for m in self.modules:
                deps = len(m.dependencies)
                lines.append(
                    f"| {m.name} | {m.responsibility[:30]} | {deps} deps | {m.health.value} |"
                )
            lines.append("")

        # Dependency Graph
        if self.dependency_graph:
            lines.append("## Dependency Graph")
            lines.append("```")
            for module, deps in self.dependency_graph.items():
                if deps:
                    lines.append(f"{module} -> {', '.join(deps)}")
            lines.append("```")
            lines.append("")

        # Recommendations
        if self.recommendations:
            lines.append("## Recommendations")
            for i, rec in enumerate(self.recommendations, 1):
                lines.append(f"{i}. {rec}")
            lines.append("")

        # Questions
        if self.questions_for_stakeholders:
            lines.append("## Questions for Stakeholders")
            for q in self.questions_for_stakeholders:
                lines.append(f"- {q}")
            lines.append("")

        return "\n".join(lines)


class ArchitectAgent(BaseAgent):
    """
    Architect Expert Agent

    Software architecture expert specializing in:
    - System design and architecture patterns
    - Microservices and monolith trade-offs
    - Scalability and performance architecture
    - Clean architecture and DDD principles
    - Technical debt assessment

    Tool Permissions:
    - Allowed: Read, Glob, Grep, AskUserQuestion
    - Forbidden: Write, Edit, Bash, Task
    """

    # Using PLAN type as closest match for architecture work
    agent_type = AgentType.PLAN

    # Tool permissions - read-only with user interaction
    allowed_tools = ["Read", "Glob", "Grep", "AskUserQuestion"]
    forbidden_tools = ["Write", "Edit", "Bash", "Task"]

    def __init__(
        self,
        agent_id: str | None = None,
        prompt_composer: PromptComposer | None = None,
        analysis_focus: AnalysisFocus = AnalysisFocus.DESIGN,
    ):
        """
        Initialize Architect Agent

        Args:
            agent_id: Optional agent identifier
            prompt_composer: Optional PromptComposer instance
            analysis_focus: Primary focus area for analysis
        """
        super().__init__(agent_id)
        self.prompt_composer = prompt_composer or PromptComposer()
        self.analysis_focus = analysis_focus

    async def execute(
        self,
        task: str,
        context: ExecutionContext,
        **kwargs,
    ) -> AgentResult:
        """
        Execute architecture analysis task

        Args:
            task: Analysis task description
            context: Execution context with session info
            **kwargs: Additional arguments:
                - analysis_focus: Override default focus
                - target_modules: Specific modules to analyze
                - architecture_scope: "full" | "module" | "component"

        Returns:
            AgentResult with architecture report

        Example:
            >>> agent = ArchitectAgent()
            >>> context = ExecutionContext(session_id="arch", working_dir="/repo")
            >>> result = await agent.execute(
            ...     task="Analyze system architecture for scalability",
            ...     context=context,
            ...     analysis_focus=AnalysisFocus.SCALABILITY
            ... )
        """
        logger.info(f"ArchitectAgent [{self.agent_id}] starting task: {task}")

        focus = kwargs.get("analysis_focus", self.analysis_focus)
        scope = kwargs.get("architecture_scope", "full")
        target_modules = kwargs.get("target_modules", [])

        result = AgentResult(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            status=AgentStatus.RUNNING,
            metadata={
                "task": task,
                "working_dir": str(context.working_dir),
                "analysis_focus": focus.value,
                "architecture_scope": scope,
                "target_modules": target_modules,
            },
        )

        try:
            # Step 1: Compose analysis prompt
            prompt = await self._compose_analysis_prompt(
                task, context, focus, scope, target_modules
            )

            # Step 2: Execute analysis (placeholder)
            report = await self._execute_analysis(prompt, context, focus, **kwargs)

            # Step 3: Mark as completed
            result.mark_completed(
                output=report.to_dict(),
                metadata={
                    **result.metadata,
                    "pattern": report.pattern.value,
                    "overall_health": report.overall_health.value,
                    "module_count": report.module_count,
                    "concern_count": report.concern_count,
                    "markdown_report": report.to_markdown(),
                },
            )

            logger.info(
                f"ArchitectAgent [{self.agent_id}] completed: "
                f"{report.module_count} modules, {report.concern_count} concerns"
            )

        except Exception as e:
            logger.error(f"ArchitectAgent [{self.agent_id}] failed: {e}")
            result.mark_failed(
                error=str(e),
                metadata={**result.metadata, "exception_type": type(e).__name__},
            )

        return result

    async def _compose_analysis_prompt(
        self,
        task: str,
        context: ExecutionContext,
        focus: AnalysisFocus,
        scope: str,
        target_modules: list[str],
    ) -> str:
        """Compose the architecture analysis prompt"""
        try:
            prompt = self.prompt_composer.compose(
                template_names=["agents/experts/architect"],
                static_vars={
                    "ARCHITECTURE_SCOPE": scope,
                    "ANALYSIS_FOCUS": focus.value,
                    "WORKING_DIR": str(context.working_dir),
                    "TARGET_MODULES": ", ".join(target_modules) if target_modules else "all",
                },
                context=context,
            )
            return prompt
        except Exception as e:
            logger.warning(f"Failed to load template: {e}, using fallback")
            return self._create_fallback_prompt(task, context, focus, scope)

    def _create_fallback_prompt(
        self,
        task: str,
        context: ExecutionContext,
        focus: AnalysisFocus,
        scope: str,
    ) -> str:
        """Create fallback prompt if template loading fails"""
        return f"""You are an Architecture Expert Agent.

**READ-ONLY MODE**: Use Read, Glob, Grep. Use AskUserQuestion for clarifications.

**Task**: {task}
**Working Directory**: {context.working_dir}
**Analysis Focus**: {focus.value}
**Scope**: {scope}

**Analysis Steps**:
1. Analyze project structure and organization
2. Map module dependencies
3. Identify architecture patterns
4. Flag anti-patterns and concerns
5. Provide recommendations

**Output**: Structured architecture report with patterns, concerns, and recommendations.
"""

    async def _execute_analysis(
        self,
        prompt: str,
        context: ExecutionContext,
        focus: AnalysisFocus,
        **kwargs,
    ) -> ArchitectureReport:
        """
        Execute architecture analysis

        Note: Placeholder for Runtime/Nexus integration.
        """
        await asyncio.sleep(0.05)  # Simulate work

        report = ArchitectureReport(
            pattern=ArchitecturePattern.LAYERED,
            domain_complexity="moderate",
            summary="Architecture analysis completed. This is a mock result.",
            strengths=[
                "Clear separation of concerns",
                "Dependency injection used consistently",
            ],
            recommendations=[
                "Consider extracting shared utilities to a core module",
                "Add integration tests for critical paths",
            ],
        )

        # Add sample module
        report.add_module(
            ModuleAnalysis(
                name="src/core",
                responsibility="Core domain logic",
                dependencies=["utils"],
                health=HealthStatus.HEALTHY,
            )
        )

        # Add sample concern
        report.add_concern(
            ArchitectureConcern(
                category="Coupling",
                description="High coupling between service and API layers",
                severity=ConcernSeverity.MEDIUM,
                impact="Changes to services require API changes",
                recommendation="Introduce interface layer between services and API",
                affected_modules=["services", "api"],
            )
        )

        return report

    def __repr__(self) -> str:
        return f"ArchitectAgent(id={self.agent_id}, focus={self.analysis_focus.value})"
