"""
Debugger Expert Agent Module

Debug specialist for bug localization, root cause analysis, and fix recommendations.
Inspired by Claude Code's debugging capabilities.
"""

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from loguru import logger

from gridcode.agents.base import AgentResult, AgentStatus, AgentType, BaseAgent
from gridcode.core.context import ExecutionContext
from gridcode.prompts.composer import PromptComposer


class DebugMode(str, Enum):
    """Debug mode options"""

    STANDARD = "standard"  # Basic bug analysis
    PERFORMANCE = "performance"  # Include profiling
    MEMORY = "memory"  # Focus on memory issues
    CONCURRENCY = "concurrency"  # Race conditions, deadlocks


class BugSeverity(str, Enum):
    """Bug severity levels"""

    BLOCKER = "blocker"  # System cannot function
    CRITICAL = "critical"  # Major feature broken
    MAJOR = "major"  # Feature partially broken
    MINOR = "minor"  # Inconvenience, workaround exists
    TRIVIAL = "trivial"  # Cosmetic issues


class BugCategory(str, Enum):
    """Bug category classification"""

    RUNTIME_ERROR = "runtime_error"
    LOGIC_ERROR = "logic_error"
    PERFORMANCE = "performance"
    MEMORY_LEAK = "memory_leak"
    RACE_CONDITION = "race_condition"
    TYPE_ERROR = "type_error"
    CONFIGURATION = "configuration"
    DEPENDENCY = "dependency"


@dataclass
class BugDiagnosis:
    """Diagnosis of a single bug"""

    error_type: str
    error_message: str
    file_path: str
    line_number: int | None = None
    root_cause: str = ""
    execution_path: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    severity: BugSeverity = BugSeverity.MAJOR
    category: BugCategory = BugCategory.RUNTIME_ERROR
    fix_recommendation: str = ""
    prevention_tips: list[str] = field(default_factory=list)
    related_files: list[str] = field(default_factory=list)


@dataclass
class DebugReport:
    """Complete debug report"""

    diagnoses: list[BugDiagnosis] = field(default_factory=list)
    analyzed_files: list[str] = field(default_factory=list)
    logs_analyzed: list[str] = field(default_factory=list)
    profiling_output: str = ""
    summary: str = ""
    debug_mode: DebugMode = DebugMode.STANDARD

    def add_diagnosis(self, diagnosis: BugDiagnosis) -> None:
        """Add a bug diagnosis to the report"""
        self.diagnoses.append(diagnosis)

    @property
    def bug_count(self) -> int:
        return len(self.diagnoses)

    @property
    def blocker_count(self) -> int:
        return len([d for d in self.diagnoses if d.severity == BugSeverity.BLOCKER])

    @property
    def critical_count(self) -> int:
        return len([d for d in self.diagnoses if d.severity == BugSeverity.CRITICAL])

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary"""
        return {
            "summary": self.summary,
            "debug_mode": self.debug_mode.value,
            "bug_count": self.bug_count,
            "blocker_count": self.blocker_count,
            "critical_count": self.critical_count,
            "analyzed_files": self.analyzed_files,
            "logs_analyzed": self.logs_analyzed,
            "profiling_output": self.profiling_output,
            "diagnoses": [
                {
                    "error_type": d.error_type,
                    "error_message": d.error_message,
                    "file_path": d.file_path,
                    "line_number": d.line_number,
                    "root_cause": d.root_cause,
                    "execution_path": d.execution_path,
                    "evidence": d.evidence,
                    "severity": d.severity.value,
                    "category": d.category.value,
                    "fix_recommendation": d.fix_recommendation,
                    "prevention_tips": d.prevention_tips,
                    "related_files": d.related_files,
                }
                for d in self.diagnoses
            ],
        }

    def to_markdown(self) -> str:
        """Convert report to markdown format"""
        lines = ["# Debug Report", ""]

        # Summary
        lines.append("## Summary")
        lines.append(f"- **Debug Mode**: {self.debug_mode.value}")
        lines.append(f"- **Bugs Found**: {self.bug_count}")
        lines.append(f"- **Blockers**: {self.blocker_count}")
        lines.append(f"- **Critical**: {self.critical_count}")
        lines.append(f"- **Files Analyzed**: {len(self.analyzed_files)}")
        lines.append("")

        if self.summary:
            lines.append(self.summary)
            lines.append("")

        # Diagnoses
        for i, diag in enumerate(self.diagnoses, 1):
            lines.append(f"## Bug #{i}: {diag.error_type}")
            lines.append("")
            location = diag.file_path
            if diag.line_number:
                location += f":{diag.line_number}"
            lines.append(f"**Location**: `{location}`")
            lines.append(f"**Severity**: {diag.severity.value}")
            lines.append(f"**Category**: {diag.category.value}")
            lines.append("")

            lines.append("### Error Message")
            lines.append(f"```\n{diag.error_message}\n```")
            lines.append("")

            if diag.root_cause:
                lines.append("### Root Cause")
                lines.append(diag.root_cause)
                lines.append("")

            if diag.execution_path:
                lines.append("### Execution Path")
                for step in diag.execution_path:
                    lines.append(f"1. {step}")
                lines.append("")

            if diag.fix_recommendation:
                lines.append("### Recommended Fix")
                lines.append(diag.fix_recommendation)
                lines.append("")

            if diag.prevention_tips:
                lines.append("### Prevention")
                for tip in diag.prevention_tips:
                    lines.append(f"- {tip}")
                lines.append("")

        # Profiling output if available
        if self.profiling_output:
            lines.append("## Profiling Output")
            lines.append(f"```\n{self.profiling_output}\n```")
            lines.append("")

        return "\n".join(lines)


class DebuggerAgent(BaseAgent):
    """
    Debugger Expert Agent

    Debug specialist with expertise in:
    - Bug localization and root cause analysis
    - Log analysis and pattern recognition
    - Profiling and performance debugging
    - Memory leak detection
    - Concurrency issue diagnosis

    Tool Permissions:
    - Allowed: Read, Glob, Grep, Bash (debug/analysis only)
    - Forbidden: Write, Edit, Task
    """

    # Note: Using CODE_REVIEW type as placeholder since DEBUGGER is not in AgentType enum
    # This should be updated when AgentType is extended
    agent_type = AgentType.CODE_REVIEW

    # Tool permissions
    allowed_tools = ["Read", "Glob", "Grep", "Bash"]
    forbidden_tools = ["Write", "Edit", "Task"]

    # Bash command restrictions - debug tools only
    bash_allowed_commands = [
        "python -m cProfile",
        "python -m memory_profiler",
        "python -m line_profiler",
        "python -m pdb",
        "python -m traceback",
        "grep",
        "cat",
        "head",
        "tail",
        "less",
        "wc",
        "sort",
        "uniq",
        "git diff",
        "git log",
        "git show",
        "git blame",
        "git status",
        "ps aux",
        "top -l 1",
        "lsof",
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
        "kill",
        "pkill",
    ]

    def __init__(
        self,
        agent_id: str | None = None,
        prompt_composer: PromptComposer | None = None,
        debug_mode: DebugMode = DebugMode.STANDARD,
    ):
        """
        Initialize Debugger Agent

        Args:
            agent_id: Optional agent identifier
            prompt_composer: Optional PromptComposer instance
            debug_mode: Debug mode (standard, performance, memory, concurrency)
        """
        super().__init__(agent_id)
        self.prompt_composer = prompt_composer or PromptComposer()
        self.debug_mode = debug_mode

    async def execute(
        self,
        task: str,
        context: ExecutionContext,
        **kwargs,
    ) -> AgentResult:
        """
        Execute debugging task

        Args:
            task: Debug task description (e.g., "Debug test failure in test_auth.py")
            context: Execution context with session info
            **kwargs: Additional arguments:
                - error_message: Error message to analyze
                - stack_trace: Stack trace string
                - affected_files: List of files involved
                - debug_mode: Override default debug mode

        Returns:
            AgentResult with debug report

        Example:
            >>> agent = DebuggerAgent()
            >>> context = ExecutionContext(session_id="debug", working_dir="/path/to/repo")
            >>> result = await agent.execute(
            ...     task="Debug NoneType error in user_service.py",
            ...     context=context,
            ...     error_message="NoneType has no attribute 'id'",
            ...     stack_trace="Traceback...",
            ...     affected_files=["src/user_service.py"]
            ... )
        """
        logger.info(f"DebuggerAgent [{self.agent_id}] starting task: {task}")

        debug_mode = kwargs.get("debug_mode", self.debug_mode)

        result = AgentResult(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            status=AgentStatus.RUNNING,
            metadata={
                "task": task,
                "working_dir": str(context.working_dir),
                "debug_mode": debug_mode.value,
                "error_message": kwargs.get("error_message", ""),
                "affected_files": kwargs.get("affected_files", []),
            },
        )

        try:
            # Step 1: Compose debug prompt
            prompt = await self._compose_debug_prompt(task, context, debug_mode, **kwargs)

            # Step 2: Execute debugging (placeholder)
            report = await self._execute_debug(prompt, context, debug_mode, **kwargs)

            # Step 3: Mark as completed
            result.mark_completed(
                output=report.to_dict(),
                metadata={
                    **result.metadata,
                    "bug_count": report.bug_count,
                    "blocker_count": report.blocker_count,
                    "critical_count": report.critical_count,
                    "markdown_report": report.to_markdown(),
                },
            )

            logger.info(
                f"DebuggerAgent [{self.agent_id}] completed: " f"{report.bug_count} bugs diagnosed"
            )

        except Exception as e:
            logger.error(f"DebuggerAgent [{self.agent_id}] failed: {e}")
            result.mark_failed(
                error=str(e),
                metadata={**result.metadata, "exception_type": type(e).__name__},
            )

        return result

    async def _compose_debug_prompt(
        self,
        task: str,
        context: ExecutionContext,
        debug_mode: DebugMode,
        **kwargs,
    ) -> str:
        """Compose the debug prompt from template"""
        error_message = kwargs.get("error_message", "Not provided")
        stack_trace = kwargs.get("stack_trace", "Not provided")
        affected_files = kwargs.get("affected_files", [])

        try:
            prompt = self.prompt_composer.compose(
                template_names=["agents/experts/debugger"],
                static_vars={
                    "ERROR_MESSAGE": error_message,
                    "STACK_TRACE": stack_trace,
                    "WORKING_DIR": str(context.working_dir),
                    "AFFECTED_FILES": ", ".join(affected_files) if affected_files else "unknown",
                    "DEBUG_MODE": debug_mode.value,
                },
                context=context,
            )
            return prompt
        except Exception as e:
            logger.warning(f"Failed to load template: {e}, using fallback")
            return self._create_fallback_prompt(
                task, context, debug_mode, error_message, stack_trace
            )

    def _create_fallback_prompt(
        self,
        task: str,
        context: ExecutionContext,
        debug_mode: DebugMode,
        error_message: str,
        stack_trace: str,
    ) -> str:
        """Create fallback prompt if template loading fails"""
        return f"""You are a Debugger Expert Agent.

**READ-ONLY MODE**: Use only Read, Glob, Grep, Bash (debug tools).

**Task**: {task}
**Working Directory**: {context.working_dir}
**Debug Mode**: {debug_mode.value}

**Error Information**:
```
{error_message}
```

**Stack Trace**:
```
{stack_trace}
```

**Debugging Steps**:
1. Analyze the error and stack trace
2. Read relevant source files
3. Trace the execution path
4. Identify root cause
5. Provide fix recommendation

**Output**: Structured debug report with root cause and fix.
"""

    async def _execute_debug(
        self,
        prompt: str,
        context: ExecutionContext,
        debug_mode: DebugMode,
        **kwargs,
    ) -> DebugReport:
        """
        Execute debugging using the composed prompt

        Note: Placeholder for Runtime/Nexus integration.
        """
        await asyncio.sleep(0.05)  # Simulate work

        report = DebugReport(
            summary="Debug analysis completed. This is a mock result.",
            analyzed_files=kwargs.get("affected_files", ["src/example.py"]),
            debug_mode=debug_mode,
        )

        # Add sample diagnosis for demonstration
        report.add_diagnosis(
            BugDiagnosis(
                error_type="AttributeError",
                error_message=kwargs.get("error_message", "Mock error"),
                file_path="src/example.py",
                line_number=42,
                root_cause="Accessing attribute on None object",
                execution_path=[
                    "main() calls process_user()",
                    "process_user() calls get_user() which returns None",
                    "Code attempts to access user.id on None",
                ],
                severity=BugSeverity.MAJOR,
                category=BugCategory.RUNTIME_ERROR,
                fix_recommendation="Add null check: if user is not None: ...",
                prevention_tips=[
                    "Add type hints with Optional[User]",
                    "Add unit test for None case",
                ],
            )
        )

        return report

    def can_execute_bash_command(self, command: str) -> bool:
        """Check if bash command is allowed for debugging"""
        command_lower = command.lower().strip()

        # Check allowed commands first (more specific patterns)
        for allowed in self.bash_allowed_commands:
            if command_lower.startswith(allowed.lower()):
                return True

        # Check forbidden commands (match at start or as standalone)
        for forbidden in self.bash_forbidden_commands:
            forbidden_lower = forbidden.lower()
            # Match at beginning of command
            if command_lower.startswith(forbidden_lower):
                return False
            # Match after a pipe, semicolon, or &&
            if f"| {forbidden_lower}" in command_lower:
                return False
            if f"; {forbidden_lower}" in command_lower:
                return False
            if f"&& {forbidden_lower}" in command_lower:
                return False

        return False

    def validate_bash_command(self, command: str) -> None:
        """Validate bash command and raise if not allowed"""
        if not self.can_execute_bash_command(command):
            raise PermissionError(
                f"DebuggerAgent cannot execute: '{command}'. "
                f"Only debug/analysis tools are permitted."
            )

    def __repr__(self) -> str:
        return f"DebuggerAgent(id={self.agent_id}, mode={self.debug_mode.value})"
