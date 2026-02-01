"""
Plan Agent Module

Agent for designing implementation approaches in the 5-Phase Planning workflow.
Inspired by Claude Code's Plan Agent design.
"""

import asyncio
from enum import Enum

from loguru import logger

from gridcode.agents.base import AgentResult, AgentStatus, AgentType, BaseAgent
from gridcode.core.context import ExecutionContext
from gridcode.prompts.composer import PromptComposer


class PlanPerspective(str, Enum):
    """Planning perspectives for multi-agent design"""

    SIMPLICITY = "simplicity"  # Focus on simple, straightforward implementation
    PERFORMANCE = "performance"  # Focus on performance optimization
    MAINTAINABILITY = "maintainability"  # Focus on long-term maintainability
    SECURITY = "security"  # Focus on security considerations
    TESTABILITY = "testability"  # Focus on testing and verification


class PlanAgent(BaseAgent):
    """
    Plan Agent - Design implementation approaches

    Capabilities:
    - Analyze requirements and design solutions
    - Consider multiple implementation approaches
    - Ask clarifying questions to users
    - READ-ONLY mode (cannot modify files)

    Tool Permissions (Inspired by Claude Code):
    - Allowed: Read, Glob, Grep, AskUserQuestion
    - Forbidden: Write, Edit, Bash, Task

    Usage Scenarios:
    - Phase 2 of 5-Phase Planning workflow
    - Designing implementation strategies
    - Considering trade-offs between approaches
    """

    agent_type = AgentType.PLAN

    # Tool permissions - Plan Agent can ask questions but cannot execute commands
    allowed_tools = ["Read", "Glob", "Grep", "AskUserQuestion"]
    forbidden_tools = ["Write", "Edit", "Bash", "Task"]

    def __init__(
        self,
        agent_id: str | None = None,
        prompt_composer: PromptComposer | None = None,
        perspective: PlanPerspective | None = None,
    ):
        """
        Initialize Plan Agent

        Args:
            agent_id: Optional agent identifier
            prompt_composer: Optional PromptComposer instance (for testing)
            perspective: Optional planning perspective (for multi-agent design)
        """
        super().__init__(agent_id)
        self.prompt_composer = prompt_composer or PromptComposer()
        self.perspective = perspective or PlanPerspective.SIMPLICITY

    async def execute(
        self,
        task: str,
        context: ExecutionContext,
        **kwargs,
    ) -> AgentResult:
        """
        Execute planning task

        Args:
            task: Planning task description (e.g., "Design authentication system")
            context: Execution context with session info
            **kwargs: Additional arguments:
                - perspective: PlanPerspective for this task
                - exploration_results: Results from Phase 1 exploration
                - constraints: List of constraints to consider
                - requirements: List of requirements

        Returns:
            AgentResult with design plan

        Example:
            >>> agent = PlanAgent(perspective=PlanPerspective.PERFORMANCE)
            >>> context = ExecutionContext(session_id="test", working_dir="/path/to/repo")
            >>> result = await agent.execute(
            ...     task="Design caching strategy for API",
            ...     context=context,
            ...     exploration_results="Found Redis client in dependencies...",
            ...     constraints=["Must support distributed deployment"]
            ... )
        """
        logger.info(f"PlanAgent [{self.agent_id}] starting task: {task}")

        # Get perspective from kwargs or use default
        perspective = kwargs.get("perspective", self.perspective)
        if isinstance(perspective, str):
            try:
                perspective = PlanPerspective(perspective)
            except ValueError:
                perspective = PlanPerspective.SIMPLICITY

        # Create result object
        result = AgentResult(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            status=AgentStatus.RUNNING,
            metadata={
                "task": task,
                "perspective": perspective.value,
                "working_dir": context.working_dir,
                "has_exploration_results": "exploration_results" in kwargs,
            },
        )

        try:
            # Step 1: Load and compose prompt
            prompt = await self._compose_planning_prompt(task, context, **kwargs)

            # Step 2: Execute planning (mock for now, will integrate with Runtime later)
            output = await self._execute_planning(prompt, context, **kwargs)

            # Step 3: Mark as completed
            result.mark_completed(
                output=output,
                metadata={
                    **result.metadata,
                    "prompt_length": len(prompt),
                    "perspective_used": perspective.value,
                },
            )

            logger.info(f"PlanAgent [{self.agent_id}] completed successfully")

        except Exception as e:
            logger.error(f"PlanAgent [{self.agent_id}] failed: {e}")
            result.mark_failed(
                error=str(e),
                metadata={**result.metadata, "exception_type": type(e).__name__},
            )

        return result

    async def _compose_planning_prompt(
        self,
        task: str,
        context: ExecutionContext,
        **kwargs,
    ) -> str:
        """
        Compose planning prompt using PromptComposer

        Args:
            task: Planning task
            context: Execution context
            **kwargs: Additional arguments

        Returns:
            Composed prompt string
        """
        perspective = kwargs.get("perspective", self.perspective)
        if isinstance(perspective, str):
            try:
                perspective = PlanPerspective(perspective)
            except ValueError:
                perspective = PlanPerspective.SIMPLICITY

        exploration_results = kwargs.get("exploration_results", "")
        constraints = kwargs.get("constraints", [])
        requirements = kwargs.get("requirements", [])

        try:
            # Load plan mode template
            prompt = self.prompt_composer.compose(
                template_names=["workflows/plan-mode-5-phase"],
                static_vars={
                    "TASK": task,
                    "WORKING_DIR": context.working_dir,
                    "PERSPECTIVE": perspective.value,
                    "EXPLORATION_RESULTS": exploration_results,
                    "CONSTRAINTS": (
                        "\n".join(f"- {c}" for c in constraints) if constraints else "None"
                    ),
                    "REQUIREMENTS": (
                        "\n".join(f"- {r}" for r in requirements) if requirements else "None"
                    ),
                },
                context=context,
            )
            return prompt

        except Exception as e:
            logger.warning(f"Failed to load plan template: {e}")
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
            task: Planning task
            context: Execution context
            **kwargs: Additional arguments

        Returns:
            Fallback prompt string
        """
        perspective = kwargs.get("perspective", self.perspective)
        if isinstance(perspective, str):
            try:
                perspective = PlanPerspective(perspective)
            except ValueError:
                perspective = PlanPerspective.SIMPLICITY

        exploration_results = kwargs.get("exploration_results", "No exploration results provided.")
        constraints = kwargs.get("constraints", [])
        requirements = kwargs.get("requirements", [])

        constraints_str = (
            "\n".join(f"- {c}" for c in constraints) if constraints else "- None specified"
        )
        requirements_str = (
            "\n".join(f"- {r}" for r in requirements) if requirements else "- None specified"
        )

        return f"""You are a Plan Agent for GridCode Runtime.

**READ-ONLY MODE**: You CANNOT modify any files. Use only: Read, Glob, Grep, AskUserQuestion.

**Task**: {task}

**Working Directory**: {context.working_dir}

**Planning Perspective**: {perspective.value}
Focus on {self._get_perspective_description(perspective)}

**Exploration Results from Phase 1**:
{exploration_results}

**Constraints**:
{constraints_str}

**Requirements**:
{requirements_str}

**Instructions**:
1. Analyze the task requirements and exploration results
2. Design an implementation approach focusing on {perspective.value}
3. Consider trade-offs and alternatives
4. Identify critical files and components to modify
5. Use AskUserQuestion if clarification is needed
6. Provide a clear, actionable plan

**Output Format**:
## Summary
Brief overview of the proposed approach

## Implementation Steps
1. Step 1...
2. Step 2...

## Files to Modify
- file1.py: description of changes
- file2.py: description of changes

## Trade-offs
- Pro: ...
- Con: ...

## Verification
How to verify the implementation works correctly
"""

    def _get_perspective_description(self, perspective: PlanPerspective) -> str:
        """
        Get description for a planning perspective

        Args:
            perspective: Planning perspective

        Returns:
            Description string
        """
        descriptions = {
            PlanPerspective.SIMPLICITY: (
                "simple, straightforward implementation with minimal complexity"
            ),
            PlanPerspective.PERFORMANCE: ("performance optimization, efficiency, and scalability"),
            PlanPerspective.MAINTAINABILITY: (
                "long-term maintainability, readability, and code quality"
            ),
            PlanPerspective.SECURITY: (
                "security considerations, input validation, and threat mitigation"
            ),
            PlanPerspective.TESTABILITY: (
                "testing and verification, test coverage, and CI/CD integration"
            ),
        }
        return descriptions.get(perspective, "balanced implementation approach")

    async def _execute_planning(
        self,
        prompt: str,
        context: ExecutionContext,
        **kwargs,
    ) -> str:
        """
        Execute planning using the composed prompt

        Note: This is a placeholder implementation. In Phase 2.2, this will:
        1. Call GridCodeRuntime.execute(prompt)
        2. Runtime will use Nexus Engine to route to LangGraph/Pydantic-AI
        3. Return structured planning results

        Args:
            prompt: Composed prompt
            context: Execution context
            **kwargs: Additional arguments

        Returns:
            Planning results (mock for now)
        """
        # TODO: Integrate with GridCodeRuntime in Phase 2.2
        # For now, return mock result
        await asyncio.sleep(0.05)  # Simulate work

        perspective = kwargs.get("perspective", self.perspective)
        if isinstance(perspective, str):
            try:
                perspective = PlanPerspective(perspective)
            except ValueError:
                perspective = PlanPerspective.SIMPLICITY

        return f"""# Implementation Plan

**Perspective**: {perspective.value}

## Summary
Designed implementation approach based on analysis of requirements and codebase exploration.

## Implementation Steps
1. Analyze existing code structure
2. Identify modification points
3. Implement changes following {perspective.value} principles
4. Add appropriate tests
5. Verify functionality

## Files to Modify
- (Files identified from exploration results)

## Trade-offs
- **Pro**: Follows {perspective.value} principles
- **Con**: May require additional considerations

## Verification
- Run unit tests
- Manual verification of functionality
- Code review

**Note**: This is a mock result. Full integration with Runtime/Nexus Engine coming in Phase 2.2.

**Prompt Used** (length: {len(prompt)} chars):
```
{prompt[:200]}...
```
"""

    def get_perspective(self) -> PlanPerspective:
        """
        Get the current planning perspective

        Returns:
            Current PlanPerspective
        """
        return self.perspective

    def set_perspective(self, perspective: PlanPerspective) -> None:
        """
        Set the planning perspective

        Args:
            perspective: New PlanPerspective to use
        """
        self.perspective = perspective

    def __repr__(self) -> str:
        """String representation of agent"""
        return (
            f"PlanAgent(id={self.agent_id}, "
            f"perspective={self.perspective.value}, "
            f"allowed_tools={len(self.allowed_tools)}, "
            f"forbidden_tools={len(self.forbidden_tools)})"
        )
