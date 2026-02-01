"""
Test Runner Agent Module

Agent for running tests and collecting results.
Inspired by Claude Code's test automation capabilities.
"""

import asyncio

from loguru import logger

from gridcode.agents.base import AgentResult, AgentStatus, AgentType, BaseAgent
from gridcode.core.context import ExecutionContext
from gridcode.prompts.composer import PromptComposer


class TestRunnerAgent(BaseAgent):
    """
    Test Runner Agent - Execute and analyze tests

    Capabilities:
    - Run pytest test suites
    - Collect and analyze test results
    - Report failures with detailed context
    - Suggest fixes for failed tests

    Tool Permissions:
    - Allowed: Read, Glob, Grep, Bash (test commands)
    - Forbidden: Write, Edit, Task (cannot modify code)
    """

    agent_type = AgentType.TEST_RUNNER

    # Tool permissions
    allowed_tools = ["Read", "Glob", "Grep", "Bash"]
    forbidden_tools = ["Write", "Edit", "Task"]

    # Bash command restrictions
    bash_allowed_commands = [
        "pytest",
        "python -m pytest",
        "python -m unittest",
        "coverage",
        "ls",
        "cat",
        "head",
        "tail",
        "grep",
        "git diff",
        "git status",
        "git log",
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
        "uv pip install",
        "chmod",
        "chown",
    ]

    def __init__(
        self,
        agent_id: str | None = None,
        prompt_composer: PromptComposer | None = None,
    ):
        """
        Initialize Test Runner Agent

        Args:
            agent_id: Optional agent identifier
            prompt_composer: Optional PromptComposer instance (for testing)
        """
        super().__init__(agent_id)
        self.prompt_composer = prompt_composer or PromptComposer()

    async def execute(
        self,
        task: str,
        context: ExecutionContext,
        **kwargs,
    ) -> AgentResult:
        """
        Execute test running task

        Args:
            task: Test task description (e.g., "Run unit tests for config module")
            context: Execution context with session info
            **kwargs: Additional arguments:
                - test_path: Specific test file or directory
                - test_pattern: Test pattern to match (e.g., "test_config*")
                - coverage: Whether to collect coverage (default: False)
                - verbose: Verbose output (default: True)
                - fail_fast: Stop on first failure (default: True)

        Returns:
            AgentResult with test results

        Example:
            >>> agent = TestRunnerAgent()
            >>> context = ExecutionContext(session_id="test", working_dir="/path/to/repo")
            >>> result = await agent.execute(
            ...     task="Run all unit tests",
            ...     context=context,
            ...     test_path="tests/unit",
            ...     coverage=True
            ... )
        """
        logger.info(f"TestRunnerAgent [{self.agent_id}] starting task: {task}")

        # Create result object
        result = AgentResult(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            status=AgentStatus.RUNNING,
            metadata={
                "task": task,
                "test_path": kwargs.get("test_path", "tests/"),
                "coverage": kwargs.get("coverage", False),
                "working_dir": str(context.working_dir),
            },
        )

        try:
            # Step 1: Compose test prompt
            prompt = await self._compose_test_prompt(task, context, **kwargs)

            # Step 2: Execute tests
            output = await self._execute_tests(prompt, context, **kwargs)

            # Step 3: Mark as completed
            result.mark_completed(
                output=output,
                metadata={
                    **result.metadata,
                    "prompt_length": len(prompt),
                    "tools_used": ["Bash", "Read"],
                },
            )

            logger.info(f"TestRunnerAgent [{self.agent_id}] completed successfully")

        except Exception as e:
            logger.error(f"TestRunnerAgent [{self.agent_id}] failed: {e}")
            result.mark_failed(
                error=str(e),
                metadata={**result.metadata, "exception_type": type(e).__name__},
            )

        return result

    async def _compose_test_prompt(
        self,
        task: str,
        context: ExecutionContext,
        **kwargs,
    ) -> str:
        """
        Compose test execution prompt

        Args:
            task: Test task
            context: Execution context
            **kwargs: Additional arguments

        Returns:
            Composed prompt string
        """
        test_path = kwargs.get("test_path", "tests/")
        coverage = kwargs.get("coverage", False)
        fail_fast = kwargs.get("fail_fast", True)

        # Build pytest command
        cmd_parts = ["pytest"]
        if fail_fast:
            cmd_parts.append("-x")
        cmd_parts.append("-v")  # verbose
        cmd_parts.append("-s")  # no capture
        if coverage:
            cmd_parts.extend(["--cov=src", "--cov-report=term-missing"])
        cmd_parts.append(test_path)

        pytest_command = " ".join(cmd_parts)

        return f"""You are a Test Runner Agent for GridCode Runtime.

**Task**: {task}

**Working Directory**: {context.working_dir}

**Instructions**:
1. Run the following pytest command:
   ```bash
   {pytest_command}
   ```

2. Analyze the test results:
   - Total tests run
   - Passed tests
   - Failed tests (with details)
   - Skipped tests
   - Coverage percentage (if requested)

3. For any failed tests:
   - Show the failure message
   - Show the relevant test code
   - Suggest potential fixes

4. Return a structured summary of results.

**Tool Permissions**:
- You can use: Read, Glob, Grep, Bash
- You CANNOT use: Write, Edit, Task (read-only mode)

**Important**:
- Do not modify any files
- Focus on analyzing and reporting test results
- Provide actionable feedback for failures
"""

    async def _execute_tests(
        self,
        prompt: str,
        context: ExecutionContext,
        **kwargs,
    ) -> str:
        """
        Execute tests using the composed prompt

        Note: This is a placeholder implementation. In full integration,
        this will call GridCodeRuntime.execute(prompt) to run the tests.

        Args:
            prompt: Composed prompt
            context: Execution context
            **kwargs: Additional arguments

        Returns:
            Test execution results (mock for now)
        """
        # TODO: Integrate with GridCodeRuntime for actual test execution
        await asyncio.sleep(0.05)  # Simulate work

        test_path = kwargs.get("test_path", "tests/")
        coverage = kwargs.get("coverage", False)

        return f"""# Test Execution Results

**Task**: Test execution completed

**Summary**:
- Test Path: {test_path}
- Coverage Enabled: {coverage}
- Status: Ready for execution

**Note**: This is a mock result. Full integration with Runtime/Nexus Engine
will enable actual test execution.

**Prompt Used** (length: {len(prompt)} chars):
```
{prompt[:300]}...
```
"""

    def can_execute_bash_command(self, command: str) -> bool:
        """
        Check if bash command is allowed

        Args:
            command: Bash command to check

        Returns:
            True if command is allowed, False if forbidden
        """
        command_lower = command.lower().strip()

        # Check forbidden commands first
        for forbidden in self.bash_forbidden_commands:
            if forbidden.lower() in command_lower:
                return False

        # Check allowed commands
        for allowed in self.bash_allowed_commands:
            if command_lower.startswith(allowed.lower()):
                return True

        # Default deny for safety
        return False

    def validate_bash_command(self, command: str) -> None:
        """
        Validate bash command and raise exception if not allowed

        Args:
            command: Bash command to validate

        Raises:
            PermissionError: If command is not allowed
        """
        if not self.can_execute_bash_command(command):
            raise PermissionError(
                f"TestRunnerAgent is not allowed to execute bash command: '{command}'. "
                f"Only test-related commands are permitted. "
                f"Allowed: pytest, coverage, git status, etc."
            )

    def __repr__(self) -> str:
        """String representation of agent"""
        return (
            f"TestRunnerAgent(id={self.agent_id}, "
            f"allowed_tools={len(self.allowed_tools)}, "
            f"forbidden_tools={len(self.forbidden_tools)})"
        )
