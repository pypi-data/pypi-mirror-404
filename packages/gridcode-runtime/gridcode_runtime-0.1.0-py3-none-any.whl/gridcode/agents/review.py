"""
Review Agent Module

Code review agent for analyzing code changes and quality.
Inspired by Claude Code's code review capabilities.
"""

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from loguru import logger

from gridcode.agents.base import AgentResult, AgentStatus, AgentType, BaseAgent
from gridcode.core.context import ExecutionContext
from gridcode.prompts.composer import PromptComposer


class ReviewCategory(str, Enum):
    """Code review category enumeration"""

    STYLE = "style"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    TYPE_SAFETY = "type_safety"
    TEST_COVERAGE = "test_coverage"


class ReviewSeverity(str, Enum):
    """Review finding severity levels"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ReviewFinding:
    """A single code review finding"""

    category: ReviewCategory
    severity: ReviewSeverity
    message: str
    file_path: str | None = None
    line_number: int | None = None
    suggestion: str | None = None
    code_snippet: str | None = None


@dataclass
class ReviewReport:
    """Complete code review report"""

    findings: list[ReviewFinding] = field(default_factory=list)
    summary: str = ""
    files_reviewed: list[str] = field(default_factory=list)
    total_issues: int = 0
    critical_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0

    def add_finding(self, finding: ReviewFinding) -> None:
        """Add a finding and update counts"""
        self.findings.append(finding)
        self.total_issues += 1
        if finding.severity == ReviewSeverity.CRITICAL:
            self.critical_count += 1
        elif finding.severity == ReviewSeverity.ERROR:
            self.error_count += 1
        elif finding.severity == ReviewSeverity.WARNING:
            self.warning_count += 1
        else:
            self.info_count += 1

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary"""
        return {
            "summary": self.summary,
            "files_reviewed": self.files_reviewed,
            "total_issues": self.total_issues,
            "critical_count": self.critical_count,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "findings": [
                {
                    "category": f.category.value,
                    "severity": f.severity.value,
                    "message": f.message,
                    "file_path": f.file_path,
                    "line_number": f.line_number,
                    "suggestion": f.suggestion,
                    "code_snippet": f.code_snippet,
                }
                for f in self.findings
            ],
        }

    def to_markdown(self) -> str:
        """Convert report to markdown format"""
        lines = ["# Code Review Report", ""]

        # Summary section
        lines.append("## Summary")
        lines.append(f"- **Files Reviewed**: {len(self.files_reviewed)}")
        lines.append(f"- **Total Issues**: {self.total_issues}")
        if self.critical_count > 0:
            lines.append(f"- **Critical**: {self.critical_count}")
        if self.error_count > 0:
            lines.append(f"- **Errors**: {self.error_count}")
        if self.warning_count > 0:
            lines.append(f"- **Warnings**: {self.warning_count}")
        if self.info_count > 0:
            lines.append(f"- **Info**: {self.info_count}")
        lines.append("")

        if self.summary:
            lines.append(self.summary)
            lines.append("")

        # Findings by severity
        if self.findings:
            lines.append("## Findings")
            lines.append("")

            # Group by severity
            for severity in [
                ReviewSeverity.CRITICAL,
                ReviewSeverity.ERROR,
                ReviewSeverity.WARNING,
                ReviewSeverity.INFO,
            ]:
                severity_findings = [f for f in self.findings if f.severity == severity]
                if severity_findings:
                    lines.append(f"### {severity.value.upper()}")
                    for finding in severity_findings:
                        location = ""
                        if finding.file_path:
                            location = f" ({finding.file_path}"
                            if finding.line_number:
                                location += f":{finding.line_number}"
                            location += ")"
                        lines.append(
                            f"- **[{finding.category.value}]** {finding.message}{location}"
                        )
                        if finding.suggestion:
                            lines.append(f"  - Suggestion: {finding.suggestion}")
                    lines.append("")

        return "\n".join(lines)


class ReviewAgent(BaseAgent):
    """
    Review Agent - Code review and quality analysis

    Capabilities:
    - Code style and consistency checking
    - Security vulnerability detection
    - Performance issue identification
    - Type safety analysis
    - Test coverage suggestions

    Tool Permissions (Read-only):
    - Allowed: Read, Glob, Grep
    - Forbidden: Write, Edit, Bash, Task, AskUserQuestion
    """

    agent_type = AgentType.CODE_REVIEW

    # Tool permissions - strictly read-only
    allowed_tools = ["Read", "Glob", "Grep"]
    forbidden_tools = ["Write", "Edit", "Bash", "Task", "AskUserQuestion"]

    # Review categories to check
    default_categories = [
        ReviewCategory.STYLE,
        ReviewCategory.SECURITY,
        ReviewCategory.PERFORMANCE,
        ReviewCategory.MAINTAINABILITY,
        ReviewCategory.TYPE_SAFETY,
    ]

    def __init__(
        self,
        agent_id: str | None = None,
        prompt_composer: PromptComposer | None = None,
        categories: list[ReviewCategory] | None = None,
    ):
        """
        Initialize Review Agent

        Args:
            agent_id: Optional agent identifier
            prompt_composer: Optional PromptComposer instance
            categories: Review categories to check (defaults to all)
        """
        super().__init__(agent_id)
        self.prompt_composer = prompt_composer or PromptComposer()
        self.categories = categories or self.default_categories

    async def execute(
        self,
        task: str,
        context: ExecutionContext,
        **kwargs,
    ) -> AgentResult:
        """
        Execute code review task

        Args:
            task: Review task description (e.g., "Review recent changes")
            context: Execution context with session info
            **kwargs: Additional arguments:
                - files: List of specific files to review
                - categories: Override default review categories
                - focus: Specific focus area (security, performance, etc.)

        Returns:
            AgentResult with review report
        """
        logger.info(f"ReviewAgent [{self.agent_id}] starting task: {task}")

        # Create result object
        result = AgentResult(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            status=AgentStatus.RUNNING,
            metadata={
                "task": task,
                "working_dir": context.working_dir,
                "categories": [c.value for c in self.categories],
            },
        )

        try:
            # Step 1: Compose review prompt
            prompt = await self._compose_review_prompt(task, context, **kwargs)

            # Step 2: Execute review
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
                f"ReviewAgent [{self.agent_id}] completed: " f"{report.total_issues} issues found"
            )

        except Exception as e:
            logger.error(f"ReviewAgent [{self.agent_id}] failed: {e}")
            result.mark_failed(
                error=str(e),
                metadata={**result.metadata, "exception_type": type(e).__name__},
            )

        return result

    async def _compose_review_prompt(
        self,
        task: str,
        context: ExecutionContext,
        **kwargs,
    ) -> str:
        """
        Compose code review prompt

        Args:
            task: Review task
            context: Execution context
            **kwargs: Additional arguments

        Returns:
            Composed prompt string
        """
        categories_str = ", ".join(c.value for c in self.categories)
        files = kwargs.get("files", [])
        focus = kwargs.get("focus", "general")

        try:
            prompt = self.prompt_composer.compose(
                template_names=["agents/review"],
                static_vars={
                    "TASK": task,
                    "WORKING_DIR": context.working_dir,
                    "CATEGORIES": categories_str,
                    "FOCUS": focus,
                    "FILES": ", ".join(files) if files else "all changed files",
                },
                context=context,
            )
            return prompt

        except Exception as e:
            logger.warning(f"Failed to load review template: {e}")
            return self._create_fallback_prompt(task, context, **kwargs)

    def _create_fallback_prompt(
        self,
        task: str,
        context: ExecutionContext,
        **kwargs,
    ) -> str:
        """
        Create fallback prompt if template loading fails

        Args:
            task: Review task
            context: Execution context
            **kwargs: Additional arguments

        Returns:
            Fallback prompt string
        """
        categories_str = ", ".join(c.value for c in self.categories)
        focus = kwargs.get("focus", "general")

        return f"""You are a Code Review Agent for GridCode Runtime.

**READ-ONLY MODE**: You CANNOT modify any files. Use only: Read, Glob, Grep.

**Task**: {task}

**Working Directory**: {context.working_dir}
**Review Categories**: {categories_str}
**Focus Area**: {focus}

**Review Checklist**:

1. **Style & Consistency**
   - Code formatting and naming conventions
   - Import organization
   - Comment quality and documentation

2. **Security**
   - Input validation
   - SQL injection, XSS, command injection risks
   - Sensitive data exposure
   - Authentication/authorization issues

3. **Performance**
   - Inefficient algorithms or data structures
   - Unnecessary database queries
   - Memory leaks or resource management

4. **Maintainability**
   - Code complexity and readability
   - DRY principle violations
   - Proper error handling

5. **Type Safety**
   - Missing type annotations
   - Type inconsistencies
   - Potential runtime type errors

**Output Format**:
For each finding, provide:
- Category: [style|security|performance|maintainability|type_safety]
- Severity: [info|warning|error|critical]
- File: path/to/file.py:line_number
- Issue: Description of the problem
- Suggestion: How to fix it

**Important**:
- Be thorough but concise
- Prioritize security and critical issues
- Provide actionable suggestions
"""

    async def _execute_review(
        self,
        prompt: str,
        context: ExecutionContext,
        **kwargs,
    ) -> ReviewReport:
        """
        Execute code review using the composed prompt

        Note: This is a placeholder implementation. Full integration with
        Runtime/Nexus Engine will be added later.

        Args:
            prompt: Composed prompt
            context: Execution context
            **kwargs: Additional arguments

        Returns:
            ReviewReport with findings
        """
        # TODO: Integrate with GridCodeRuntime
        await asyncio.sleep(0.05)  # Simulate work

        # Create mock report
        report = ReviewReport(
            summary="Code review completed. This is a mock result.",
            files_reviewed=kwargs.get("files", ["src/example.py"]),
        )

        # Add sample findings for demonstration
        report.add_finding(
            ReviewFinding(
                category=ReviewCategory.STYLE,
                severity=ReviewSeverity.INFO,
                message="Consider adding docstrings to public functions",
                file_path="src/example.py",
                line_number=10,
                suggestion="Add a docstring describing the function's purpose",
            )
        )

        return report

    def get_review_categories(self) -> list[ReviewCategory]:
        """Get list of review categories"""
        return self.categories

    def set_review_categories(self, categories: list[ReviewCategory]) -> None:
        """Set review categories"""
        self.categories = categories

    def __repr__(self) -> str:
        """String representation of agent"""
        return (
            f"ReviewAgent(id={self.agent_id}, "
            f"categories={len(self.categories)}, "
            f"allowed_tools={len(self.allowed_tools)})"
        )
