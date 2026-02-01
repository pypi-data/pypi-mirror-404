"""
Code Reviewer Expert Agent Module

Elite code review expert for quality, security, and best practices analysis.
Inspired by Claude Code's code review capabilities with enhanced security focus.
"""

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from loguru import logger

from gridcode.agents.base import AgentResult, AgentStatus, AgentType, BaseAgent
from gridcode.core.context import ExecutionContext
from gridcode.prompts.composer import PromptComposer


class ReviewFocus(str, Enum):
    """Code review focus areas"""

    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    TYPE_SAFETY = "type_safety"
    STYLE = "style"
    ALL = "all"


class IssueSeverity(str, Enum):
    """Issue severity levels"""

    CRITICAL = "critical"  # Security vulnerabilities, data corruption
    HIGH = "high"  # Performance issues, runtime errors
    MEDIUM = "medium"  # Type safety, maintainability
    LOW = "low"  # Style issues


@dataclass
class CodeIssue:
    """A single code review issue"""

    severity: IssueSeverity
    category: str
    title: str
    file_path: str
    line_number: int | None = None
    description: str = ""
    impact: str = ""
    fix_suggestion: str = ""
    code_snippet: str | None = None


@dataclass
class CodeReviewReport:
    """Complete code review report"""

    issues: list[CodeIssue] = field(default_factory=list)
    files_reviewed: list[str] = field(default_factory=list)
    summary: str = ""
    static_analysis_output: str = ""

    @property
    def total_issues(self) -> int:
        return len(self.issues)

    @property
    def critical_count(self) -> int:
        return len([i for i in self.issues if i.severity == IssueSeverity.CRITICAL])

    @property
    def high_count(self) -> int:
        return len([i for i in self.issues if i.severity == IssueSeverity.HIGH])

    @property
    def medium_count(self) -> int:
        return len([i for i in self.issues if i.severity == IssueSeverity.MEDIUM])

    @property
    def low_count(self) -> int:
        return len([i for i in self.issues if i.severity == IssueSeverity.LOW])

    def add_issue(self, issue: CodeIssue) -> None:
        """Add an issue to the report"""
        self.issues.append(issue)

    def filter_by_severity(self, min_severity: IssueSeverity) -> list[CodeIssue]:
        """Filter issues by minimum severity threshold"""
        severity_order = {
            IssueSeverity.LOW: 0,
            IssueSeverity.MEDIUM: 1,
            IssueSeverity.HIGH: 2,
            IssueSeverity.CRITICAL: 3,
        }
        min_level = severity_order[min_severity]
        return [i for i in self.issues if severity_order[i.severity] >= min_level]

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary"""
        return {
            "summary": self.summary,
            "files_reviewed": self.files_reviewed,
            "total_issues": self.total_issues,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "static_analysis_output": self.static_analysis_output,
            "issues": [
                {
                    "severity": i.severity.value,
                    "category": i.category,
                    "title": i.title,
                    "file_path": i.file_path,
                    "line_number": i.line_number,
                    "description": i.description,
                    "impact": i.impact,
                    "fix_suggestion": i.fix_suggestion,
                    "code_snippet": i.code_snippet,
                }
                for i in self.issues
            ],
        }

    def to_markdown(self) -> str:
        """Convert report to markdown format"""
        lines = ["# Code Review Report", ""]

        # Summary
        lines.append("## Summary")
        lines.append(f"- **Files Reviewed**: {len(self.files_reviewed)}")
        lines.append(f"- **Total Issues**: {self.total_issues}")
        lines.append(
            f"- **Critical**: {self.critical_count} | "
            f"**High**: {self.high_count} | "
            f"**Medium**: {self.medium_count} | "
            f"**Low**: {self.low_count}"
        )
        lines.append("")

        if self.summary:
            lines.append(self.summary)
            lines.append("")

        # Issues by severity
        for severity in [
            IssueSeverity.CRITICAL,
            IssueSeverity.HIGH,
            IssueSeverity.MEDIUM,
            IssueSeverity.LOW,
        ]:
            severity_issues = [i for i in self.issues if i.severity == severity]
            if severity_issues:
                lines.append(f"## {severity.value.upper()} Issues")
                lines.append("")
                for issue in severity_issues:
                    location = issue.file_path
                    if issue.line_number:
                        location += f":{issue.line_number}"
                    lines.append(f"### [{issue.category}] {issue.title}")
                    lines.append(f"- **Location**: `{location}`")
                    if issue.description:
                        lines.append(f"- **Description**: {issue.description}")
                    if issue.impact:
                        lines.append(f"- **Impact**: {issue.impact}")
                    if issue.fix_suggestion:
                        lines.append(f"- **Fix**: {issue.fix_suggestion}")
                    if issue.code_snippet:
                        lines.append("```python")
                        lines.append(issue.code_snippet)
                        lines.append("```")
                    lines.append("")

        return "\n".join(lines)


class CodeReviewerAgent(BaseAgent):
    """
    Code Reviewer Expert Agent

    Elite code review expert specializing in:
    - Modern AI-powered code analysis
    - Security vulnerability detection (OWASP Top 10)
    - Performance optimization
    - Production reliability

    Tool Permissions:
    - Allowed: Read, Glob, Grep, Bash (static analysis only)
    - Forbidden: Write, Edit, Task, AskUserQuestion
    """

    agent_type = AgentType.CODE_REVIEW

    # Tool permissions
    allowed_tools = ["Read", "Glob", "Grep", "Bash"]
    forbidden_tools = ["Write", "Edit", "Task", "AskUserQuestion"]

    # Bash command restrictions - only static analysis tools
    bash_allowed_commands = [
        "ruff",
        "mypy",
        "bandit",
        "pylint",
        "flake8",
        "black --check",
        "isort --check",
        "grep",
        "cat",
        "head",
        "tail",
        "wc",
        "git diff",
        "git log",
        "git status",
        "git show",
    ]

    bash_forbidden_commands = [
        "rm",
        "mv",
        "cp",
        "git push",
        "git commit",
        "git add",
        "git reset",
        "pip install",
        "chmod",
        "chown",
        "python ",  # Prevent arbitrary script execution
    ]

    # Default configuration
    default_focus_areas = [
        ReviewFocus.SECURITY,
        ReviewFocus.PERFORMANCE,
        ReviewFocus.MAINTAINABILITY,
    ]

    def __init__(
        self,
        agent_id: str | None = None,
        prompt_composer: PromptComposer | None = None,
        focus_areas: list[ReviewFocus] | None = None,
        severity_threshold: IssueSeverity = IssueSeverity.MEDIUM,
    ):
        """
        Initialize Code Reviewer Agent

        Args:
            agent_id: Optional agent identifier
            prompt_composer: Optional PromptComposer instance
            focus_areas: Areas to focus review on (default: security, performance, maintainability)
            severity_threshold: Minimum severity to report (default: medium)
        """
        super().__init__(agent_id)
        self.prompt_composer = prompt_composer or PromptComposer()
        self.focus_areas = focus_areas or self.default_focus_areas
        self.severity_threshold = severity_threshold

    async def execute(
        self,
        task: str,
        context: ExecutionContext,
        **kwargs,
    ) -> AgentResult:
        """
        Execute code review task

        Args:
            task: Review task description (e.g., "Review security of authentication module")
            context: Execution context with session info
            **kwargs: Additional arguments:
                - review_scope: "changed_files" | "all" | "specific_files" (default: changed_files)
                - files: List of specific files to review
                - focus_areas: Override default focus areas
                - severity_threshold: Override default severity threshold

        Returns:
            AgentResult with code review report

        Example:
            >>> agent = CodeReviewerAgent()
            >>> context = ExecutionContext(session_id="review", working_dir="/path/to/repo")
            >>> result = await agent.execute(
            ...     task="Review authentication module for security issues",
            ...     context=context,
            ...     focus_areas=[ReviewFocus.SECURITY],
            ...     severity_threshold=IssueSeverity.HIGH
            ... )
        """
        logger.info(f"CodeReviewerAgent [{self.agent_id}] starting task: {task}")

        # Override settings from kwargs if provided
        focus_areas = kwargs.get("focus_areas", self.focus_areas)
        severity_threshold = kwargs.get("severity_threshold", self.severity_threshold)
        review_scope = kwargs.get("review_scope", "changed_files")

        result = AgentResult(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            status=AgentStatus.RUNNING,
            metadata={
                "task": task,
                "working_dir": str(context.working_dir),
                "review_scope": review_scope,
                "focus_areas": [f.value for f in focus_areas],
                "severity_threshold": severity_threshold.value,
            },
        )

        try:
            # Step 1: Compose review prompt
            prompt = await self._compose_review_prompt(
                task, context, review_scope, focus_areas, severity_threshold, **kwargs
            )

            # Step 2: Execute review (placeholder for Runtime integration)
            report = await self._execute_review(prompt, context, **kwargs)

            # Step 3: Mark as completed
            result.mark_completed(
                output=report.to_dict(),
                metadata={
                    **result.metadata,
                    "files_reviewed": len(report.files_reviewed),
                    "total_issues": report.total_issues,
                    "critical_count": report.critical_count,
                    "markdown_report": report.to_markdown(),
                },
            )

            logger.info(
                f"CodeReviewerAgent [{self.agent_id}] completed: "
                f"{report.total_issues} issues found ({report.critical_count} critical)"
            )

        except Exception as e:
            logger.error(f"CodeReviewerAgent [{self.agent_id}] failed: {e}")
            result.mark_failed(
                error=str(e),
                metadata={**result.metadata, "exception_type": type(e).__name__},
            )

        return result

    async def _compose_review_prompt(
        self,
        task: str,
        context: ExecutionContext,
        review_scope: str,
        focus_areas: list[ReviewFocus],
        severity_threshold: IssueSeverity,
        **kwargs,
    ) -> str:
        """Compose the code review prompt from template"""
        focus_str = ", ".join(f.value for f in focus_areas)
        files = kwargs.get("files", [])

        try:
            prompt = self.prompt_composer.compose(
                template_names=["agents/experts/code_reviewer"],
                static_vars={
                    "REVIEW_SCOPE": review_scope,
                    "FOCUS_AREAS": focus_str,
                    "SEVERITY_THRESHOLD": severity_threshold.value,
                    "WORKING_DIR": str(context.working_dir),
                    "CHANGED_FILES": ", ".join(files) if files else "auto-detect",
                },
                context=context,
            )
            return prompt
        except Exception as e:
            logger.warning(f"Failed to load template: {e}, using fallback")
            return self._create_fallback_prompt(
                task, context, review_scope, focus_areas, severity_threshold
            )

    def _create_fallback_prompt(
        self,
        task: str,
        context: ExecutionContext,
        review_scope: str,
        focus_areas: list[ReviewFocus],
        severity_threshold: IssueSeverity,
    ) -> str:
        """Create fallback prompt if template loading fails"""
        focus_str = ", ".join(f.value for f in focus_areas)

        return f"""You are an elite Code Review Expert Agent.

**READ-ONLY MODE**: Use only Read, Glob, Grep, Bash (static analysis tools).

**Task**: {task}
**Working Directory**: {context.working_dir}
**Review Scope**: {review_scope}
**Focus Areas**: {focus_str}
**Severity Threshold**: {severity_threshold.value}

**Static Analysis Commands**:
```bash
ruff check {context.working_dir} --output-format=text
mypy {context.working_dir} --ignore-missing-imports
bandit -r {context.working_dir} -f json
```

**Review Checklist**:
1. Security: SQL injection, XSS, command injection, hardcoded credentials
2. Performance: N+1 queries, memory leaks, inefficient algorithms
3. Type Safety: Missing annotations, inconsistent types
4. Maintainability: Long functions, deep nesting, DRY violations

**Output**: Structured report with issues by severity (critical/high/medium/low).
"""

    async def _execute_review(
        self,
        prompt: str,
        context: ExecutionContext,
        **kwargs,
    ) -> CodeReviewReport:
        """
        Execute code review using the composed prompt

        Note: Placeholder for Runtime/Nexus integration.
        """
        await asyncio.sleep(0.05)  # Simulate work

        report = CodeReviewReport(
            summary="Code review completed. This is a mock result.",
            files_reviewed=kwargs.get("files", ["src/example.py"]),
        )

        # Add sample issue for demonstration
        report.add_issue(
            CodeIssue(
                severity=IssueSeverity.MEDIUM,
                category="type_safety",
                title="Missing type annotations",
                file_path="src/example.py",
                line_number=42,
                description="Function parameters lack type hints",
                impact="Reduced code maintainability and IDE support",
                fix_suggestion="Add type hints: def func(name: str, count: int) -> None:",
            )
        )

        return report

    def can_execute_bash_command(self, command: str) -> bool:
        """Check if bash command is allowed for code review"""
        command_lower = command.lower().strip()

        # Check forbidden commands first
        for forbidden in self.bash_forbidden_commands:
            if forbidden.lower() in command_lower:
                return False

        # Check allowed commands
        for allowed in self.bash_allowed_commands:
            if command_lower.startswith(allowed.lower()):
                return True

        return False

    def validate_bash_command(self, command: str) -> None:
        """Validate bash command and raise if not allowed"""
        if not self.can_execute_bash_command(command):
            raise PermissionError(
                f"CodeReviewerAgent cannot execute: '{command}'. "
                f"Only static analysis tools are permitted."
            )

    def __repr__(self) -> str:
        return (
            f"CodeReviewerAgent(id={self.agent_id}, "
            f"focus={[f.value for f in self.focus_areas]}, "
            f"threshold={self.severity_threshold.value})"
        )
