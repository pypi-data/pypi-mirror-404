"""
Explore Agent Module

Read-only agent for rapid codebase exploration.
Inspired by Claude Code's Explore Agent design.
"""

import asyncio

from loguru import logger

from gridcode.agents.base import AgentResult, AgentStatus, AgentType, BaseAgent
from gridcode.core.context import ExecutionContext
from gridcode.prompts.composer import PromptComposer


class ExploreAgent(BaseAgent):
    """
    Explore Agent - Read-only codebase exploration

    Capabilities:
    - Fast parallel file search and content reading
    - Pattern matching and code analysis
    - READ-ONLY mode (cannot modify files)

    Tool Permissions (Inspired by Claude Code):
    - Allowed: Read, Glob, Grep, Bash (read-only commands)
    - Forbidden: Write, Edit, Task, AskUserQuestion

    Bash Restrictions:
    - Only read-only commands allowed (ls, find, cat, git log, git diff, etc.)
    - Destructive commands forbidden (rm, mv, git push, git commit, etc.)
    """

    agent_type = AgentType.EXPLORE

    # Tool permissions
    allowed_tools = ["Read", "Glob", "Grep", "Bash"]
    forbidden_tools = ["Write", "Edit", "Task", "AskUserQuestion"]

    # Bash command restrictions
    bash_allowed_commands = [
        "ls",
        "find",
        "cat",
        "head",
        "tail",
        "grep",
        "git log",
        "git diff",
        "git status",
        "git show",
        "tree",
        "file",
        "wc",
        "du",
        "stat",
    ]

    bash_forbidden_commands = [
        "rm",
        "mv",
        "cp",
        "touch",
        "git push",
        "git commit",
        "git add",
        "git reset",
        "git rebase",
        "git merge",
        "chmod",
        "chown",
        "ln",
    ]

    def __init__(
        self,
        agent_id: str | None = None,
        prompt_composer: PromptComposer | None = None,
    ):
        """
        Initialize Explore Agent

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
        Execute exploration task

        Args:
            task: Exploration task description (e.g., "Find all Python test files")
            context: Execution context with session info
            **kwargs: Additional arguments (thoroughness, timeout, etc.)

        Returns:
            AgentResult with exploration findings

        Example:
            >>> agent = ExploreAgent()
            >>> context = ExecutionContext(session_id="test", working_dir="/path/to/repo")
            >>> result = await agent.execute(
            ...     task="Find all configuration files",
            ...     context=context,
            ...     thoroughness="medium"
            ... )
        """
        logger.info(f"ExploreAgent [{self.agent_id}] starting task: {task}")

        # Create result object
        result = AgentResult(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            status=AgentStatus.RUNNING,
            metadata={
                "task": task,
                "thoroughness": kwargs.get("thoroughness", "quick"),
                "working_dir": context.working_dir,
            },
        )

        try:
            # Step 1: Load and compose prompt
            prompt = await self._compose_exploration_prompt(task, context, **kwargs)

            # Step 2: Execute exploration (mock for now, will integrate with Runtime later)
            output = await self._execute_exploration(prompt, context, **kwargs)

            # Step 3: Mark as completed
            result.mark_completed(
                output=output,
                metadata={
                    **result.metadata,
                    "prompt_length": len(prompt),
                    "tools_used": ["Read", "Glob", "Grep"],  # Mock for now
                },
            )

            logger.info(f"ExploreAgent [{self.agent_id}] completed successfully")

        except Exception as e:
            logger.error(f"ExploreAgent [{self.agent_id}] failed: {e}")
            result.mark_failed(
                error=str(e),
                metadata={**result.metadata, "exception_type": type(e).__name__},
            )

        return result

    async def _compose_exploration_prompt(
        self,
        task: str,
        context: ExecutionContext,
        **kwargs,
    ) -> str:
        """
        Compose exploration prompt using PromptComposer

        Args:
            task: Exploration task
            context: Execution context
            **kwargs: Additional arguments

        Returns:
            Composed prompt string
        """
        try:
            # Load explore.md template
            prompt = self.prompt_composer.compose(
                template_names=["agents/explore"],
                static_vars={
                    "TASK": task,
                    "WORKING_DIR": context.working_dir,
                    "THOROUGHNESS": kwargs.get("thoroughness", "quick"),
                },
                context=context,
            )
            return prompt

        except Exception as e:
            logger.warning(f"Failed to load explore.md template: {e}")
            # Fallback to simple prompt
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
            task: Exploration task
            context: Execution context
            **kwargs: Additional arguments

        Returns:
            Fallback prompt string
        """
        thoroughness = kwargs.get("thoroughness", "quick")

        return f"""You are an Explore Agent for GridCode Runtime.

**READ-ONLY MODE**: You CANNOT modify any files. Use only: Read, Glob, Grep, Bash (read-only).

**Task**: {task}

**Working Directory**: {context.working_dir}
**Thoroughness**: {thoroughness}

**Instructions**:
1. Use Glob to find relevant files by pattern
2. Use Grep to search file contents
3. Use Read to examine specific files
4. Return findings in a clear, organized format

**Important**:
- Be fast and efficient
- Make parallel tool calls when possible
- Focus on answering the specific task
"""

    async def _execute_exploration(
        self,
        prompt: str,
        context: ExecutionContext,
        **kwargs,
    ) -> str:
        """
        Execute exploration using the composed prompt

        Note: This is a placeholder implementation. In Phase 2.2, this will:
        1. Call GridCodeRuntime.execute(prompt)
        2. Runtime will use Nexus Engine to route to LangGraph/Pydantic-AI
        3. Return structured exploration results

        Args:
            prompt: Composed prompt
            context: Execution context
            **kwargs: Additional arguments

        Returns:
            Exploration results (mock for now)
        """
        # TODO: Integrate with GridCodeRuntime in Phase 2.2
        # For now, return mock result
        await asyncio.sleep(0.05)  # Simulate work

        return f"""# Exploration Results

**Task**: Completed exploration using read-only tools

**Findings**:
- Used Glob to search files
- Used Grep to analyze content
- Used Read to examine details

**Note**: This is a mock result. Full integration with Runtime/Nexus Engine coming in Phase 2.2.

**Prompt Used** (length: {len(prompt)} chars):
```
{prompt[:200]}...
```
"""

    def can_execute_bash_command(self, command: str) -> bool:
        """
        Check if bash command is allowed (read-only check)

        Args:
            command: Bash command to check

        Returns:
            True if command is allowed, False if forbidden
        """
        command_lower = command.lower().strip()

        # Check forbidden commands first
        for forbidden in self.bash_forbidden_commands:
            if command_lower.startswith(forbidden):
                return False

        # Check allowed commands
        for allowed in self.bash_allowed_commands:
            if command_lower.startswith(allowed):
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
                f"ExploreAgent is not allowed to execute bash command: '{command}'. "
                f"Only read-only commands are permitted. "
                f"Allowed: {', '.join(self.bash_allowed_commands[:5])}..."
            )

    def __repr__(self) -> str:
        """String representation of agent"""
        return (
            f"ExploreAgent(id={self.agent_id}, "
            f"allowed_tools={len(self.allowed_tools)}, "
            f"forbidden_tools={len(self.forbidden_tools)})"
        )
