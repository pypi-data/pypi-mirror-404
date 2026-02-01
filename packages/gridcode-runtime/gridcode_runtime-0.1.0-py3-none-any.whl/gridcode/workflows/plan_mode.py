"""Plan Mode Manager for 5-Phase Planning Workflow.

This module orchestrates the 5-Phase Planning workflow:
1. Initial Understanding - Understand requirements and codebase
2. Exploration - Deep dive with ExploreAgent(s)
3. Planning - Design with PlanAgent(s)
4. Review - User review and approval
5. Exit Plan Mode - Transition to implementation

The PlanModeManager integrates with:
- GridCodeRuntime for execution
- System Reminders for context-aware notifications
- InteractionHandler for user confirmation and feedback
- MessageBus for inter-agent communication
"""

from enum import Enum, auto
from typing import TYPE_CHECKING, Any

from loguru import logger
from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from gridcode.core.context import ExecutionContext
    from gridcode.core.runtime import GridCodeRuntime


class PlanPhase(Enum):
    """Phases in the 5-Phase Planning Workflow."""

    INITIAL = auto()
    UNDERSTANDING = auto()
    EXPLORATION = auto()
    PLANNING = auto()
    REVIEW = auto()
    READY = auto()


class PhaseResult(BaseModel):
    """Result from a planning phase."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    phase: PlanPhase
    success: bool
    output: str = ""
    findings: list[str] = []
    metadata: dict[str, Any] = {}


class PlanDocument(BaseModel):
    """The planning document that accumulates through phases."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    task_description: str = ""
    understanding: str = ""
    exploration_findings: list[str] = []
    design_options: list[dict[str, Any]] = []
    selected_approach: str = ""
    implementation_steps: list[str] = []
    risks_and_mitigations: list[dict[str, str]] = []
    test_plan: list[str] = []
    review_notes: str = ""


class PlanModeManager:
    """Manager for 5-Phase Planning workflow.

    This class orchestrates plan mode execution, integrating with
    Runtime, System Reminders, and Interaction systems.

    Example:
        runtime = GridCodeRuntime(api_key="...", interaction=handler)
        manager = PlanModeManager(runtime)

        # Enter plan mode
        await manager.enter_plan_mode("Implement user authentication")

        # Execute phases
        await manager.execute_understanding()
        await manager.execute_exploration()
        await manager.execute_planning()

        # Review and exit
        approved = await manager.request_review()
        if approved:
            await manager.exit_plan_mode()
    """

    def __init__(self, runtime: "GridCodeRuntime"):
        """Initialize the PlanModeManager.

        Args:
            runtime: The GridCodeRuntime instance to use
        """
        self.runtime = runtime
        self.current_phase: PlanPhase = PlanPhase.INITIAL
        self.plan_document: PlanDocument = PlanDocument()
        self.phase_results: dict[PlanPhase, PhaseResult] = {}

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

    @property
    def is_active(self) -> bool:
        """Check if plan mode is currently active."""
        return self.context.is_plan_mode

    async def enter_plan_mode(self, task: str = "") -> None:
        """Enter plan mode and notify the user.

        Args:
            task: Description of the task to plan
        """
        if self.is_active:
            logger.warning("Already in plan mode")
            return

        self.context.is_plan_mode = True
        self.current_phase = PlanPhase.UNDERSTANDING
        self.plan_document = PlanDocument(task_description=task)
        self.phase_results = {}

        await self.runtime.notify_user(
            "Entering plan mode. I will explore and plan before implementing.", level="info"
        )

        logger.info(f"Entered plan mode for task: {task}")

    async def exit_plan_mode(self) -> bool:
        """Exit plan mode after getting user approval.

        Returns:
            True if plan mode was exited, False if user declined
        """
        if not self.is_active:
            logger.warning("Not in plan mode")
            return False

        # Check if we've completed necessary phases
        if self.current_phase.value < PlanPhase.REVIEW.value:
            await self.runtime.notify_user(
                "Cannot exit plan mode: planning phases not complete.", level="warning"
            )
            return False

        # Request user confirmation
        confirmed = await self.runtime.request_confirmation(
            "Plan is ready. Proceed with implementation?"
        )

        if confirmed:
            self.context.is_plan_mode = False
            self.current_phase = PlanPhase.READY

            await self.runtime.notify_user(
                "Exited plan mode. Ready for implementation.", level="success"
            )

            logger.info("Exited plan mode")
            return True
        else:
            await self.runtime.notify_user(
                "Plan mode exit declined. Continuing in plan mode.", level="info"
            )
            return False

    async def execute_understanding(self, additional_context: str = "") -> PhaseResult:
        """Execute Phase 1: Initial Understanding.

        Gather and validate requirements, understand the scope.

        Args:
            additional_context: Additional context to consider

        Returns:
            PhaseResult from the understanding phase
        """
        if not self.is_active:
            raise RuntimeError("Cannot execute phase: not in plan mode")

        self.current_phase = PlanPhase.UNDERSTANDING

        await self.runtime.notify_user(
            "Phase 1: Understanding requirements and codebase...", level="info"
        )

        # Compose understanding prompt
        understanding_prompt = f"""
Task: {self.plan_document.task_description}

{additional_context}

Please analyze this task and provide:
1. Key requirements and constraints
2. Relevant files and modules to examine
3. Potential challenges or blockers
4. Questions that need clarification
"""

        try:
            result = await self.runtime.run(understanding_prompt, self.context)

            self.plan_document.understanding = result.output

            phase_result = PhaseResult(
                phase=PlanPhase.UNDERSTANDING,
                success=True,
                output=result.output,
                findings=[],
                metadata=result.metadata,
            )

            self.phase_results[PlanPhase.UNDERSTANDING] = phase_result
            logger.info("Understanding phase completed")

            return phase_result

        except Exception as e:
            logger.error(f"Understanding phase failed: {e}")
            return PhaseResult(
                phase=PlanPhase.UNDERSTANDING,
                success=False,
                output=str(e),
            )

    async def execute_exploration(
        self,
        focus_areas: list[str] | None = None,
        parallel: bool = True,
    ) -> PhaseResult:
        """Execute Phase 2: Exploration.

        Deep dive into codebase with ExploreAgent(s).

        Args:
            focus_areas: Specific areas to explore
            parallel: Whether to run multiple explore agents in parallel

        Returns:
            PhaseResult from the exploration phase
        """
        if not self.is_active:
            raise RuntimeError("Cannot execute phase: not in plan mode")

        self.current_phase = PlanPhase.EXPLORATION

        await self.runtime.notify_user("Phase 2: Exploring codebase...", level="info")

        # Use ExploreAgent(s) through AgentPool
        explore_tasks = focus_areas or [self.plan_document.task_description]

        findings: list[str] = []

        try:
            from gridcode.agents.base import AgentType

            for i, task in enumerate(explore_tasks):
                agent_id = f"explore_{i}"

                await self.runtime.show_progress(
                    f"Exploring: {task[:50]}...", progress=((i + 1) / len(explore_tasks)) * 100
                )

                self.runtime.agent_pool.spawn_agent(
                    agent_type=AgentType.EXPLORE,
                    task=task,
                    context=self.context,
                    agent_id=agent_id,
                )

                result = await self.runtime.agent_pool.wait_for_agent(agent_id)

                if result and result.success:
                    findings.append(result.output)

            self.plan_document.exploration_findings = findings

            phase_result = PhaseResult(
                phase=PlanPhase.EXPLORATION,
                success=True,
                output="\n\n".join(findings),
                findings=findings,
            )

            self.phase_results[PlanPhase.EXPLORATION] = phase_result
            logger.info(f"Exploration phase completed with {len(findings)} findings")

            return phase_result

        except Exception as e:
            logger.error(f"Exploration phase failed: {e}")
            return PhaseResult(
                phase=PlanPhase.EXPLORATION,
                success=False,
                output=str(e),
            )

    async def execute_planning(
        self,
        perspectives: list[str] | None = None,
    ) -> PhaseResult:
        """Execute Phase 3: Planning.

        Design implementation with PlanAgent(s) from multiple perspectives.

        Args:
            perspectives: Planning perspectives to consider
                         (simplicity, performance, maintainability, security, testability)

        Returns:
            PhaseResult from the planning phase
        """
        if not self.is_active:
            raise RuntimeError("Cannot execute phase: not in plan mode")

        self.current_phase = PlanPhase.PLANNING

        await self.runtime.notify_user(
            "Phase 3: Designing implementation approach...", level="info"
        )

        from gridcode.agents.base import AgentType
        from gridcode.agents.plan import PlanPerspective

        # Default perspectives if not specified
        if perspectives is None:
            perspectives = ["simplicity", "maintainability"]

        design_options: list[dict[str, Any]] = []

        try:
            for i, perspective in enumerate(perspectives):
                await self.runtime.show_progress(
                    f"Planning from {perspective} perspective...",
                    progress=((i + 1) / len(perspectives)) * 100,
                )

                agent_id = f"plan_{perspective}"

                agent = self.runtime.agent_pool.spawn_agent(
                    agent_type=AgentType.PLAN,
                    task=self._compose_planning_task(perspective),
                    context=self.context,
                    agent_id=agent_id,
                )

                # Set perspective on the agent
                if hasattr(agent, "set_perspective"):
                    try:
                        agent.set_perspective(PlanPerspective[perspective.upper()])
                    except KeyError:
                        pass

                result = await self.runtime.agent_pool.wait_for_agent(agent_id)

                if result and result.success:
                    design_options.append(
                        {
                            "perspective": perspective,
                            "plan": result.output,
                        }
                    )

            self.plan_document.design_options = design_options

            # Combine design options into output
            combined_output = "\n\n---\n\n".join(
                f"## {opt['perspective'].title()} Perspective\n\n{opt['plan']}"
                for opt in design_options
            )

            phase_result = PhaseResult(
                phase=PlanPhase.PLANNING,
                success=True,
                output=combined_output,
                findings=[opt["plan"] for opt in design_options],
            )

            self.phase_results[PlanPhase.PLANNING] = phase_result
            logger.info(f"Planning phase completed with {len(design_options)} options")

            return phase_result

        except Exception as e:
            logger.error(f"Planning phase failed: {e}")
            return PhaseResult(
                phase=PlanPhase.PLANNING,
                success=False,
                output=str(e),
            )

    async def request_review(self) -> bool:
        """Request user review of the plan.

        Returns:
            True if the user approves, False otherwise
        """
        if not self.is_active:
            raise RuntimeError("Cannot request review: not in plan mode")

        self.current_phase = PlanPhase.REVIEW

        await self.runtime.notify_user("Phase 4: Review your plan...", level="info")

        # Display plan summary
        summary = self._generate_plan_summary()
        await self.runtime.notify_user(summary, level="info")

        # Ask for approval
        approved = await self.runtime.request_confirmation(
            "Do you approve this plan?", default=False
        )

        if approved:
            # Ask for any additional notes
            notes = await self.runtime.ask_user(
                "Any notes or modifications? (press Enter to skip)",
                allow_free_text=True,
                default="",
            )

            if notes:
                self.plan_document.review_notes = notes

            logger.info("Plan approved by user")
        else:
            logger.info("Plan not approved by user")

        return approved

    def _compose_planning_task(self, perspective: str) -> str:
        """Compose a planning task with context.

        Args:
            perspective: The planning perspective

        Returns:
            The composed task string
        """
        return f"""
Task: {self.plan_document.task_description}

Understanding:
{self.plan_document.understanding}

Exploration Findings:
{chr(10).join('- ' + f for f in self.plan_document.exploration_findings[:5])}

Design a solution from the {perspective} perspective. Consider:
- Implementation approach
- Key components and their responsibilities
- Dependencies and interactions
- Potential risks and mitigations
"""

    def _generate_plan_summary(self) -> str:
        """Generate a summary of the current plan.

        Returns:
            The plan summary string
        """
        doc = self.plan_document

        sections = [
            "# Plan Summary",
            f"\n## Task\n{doc.task_description}",
            (
                f"\n## Understanding\n{doc.understanding[:500]}..."
                if len(doc.understanding) > 500
                else f"\n## Understanding\n{doc.understanding}"
            ),
        ]

        if doc.exploration_findings:
            findings_text = "\n".join(f"- {f[:100]}..." for f in doc.exploration_findings[:3])
            sections.append(f"\n## Key Findings\n{findings_text}")

        if doc.design_options:
            options_text = "\n".join(
                f"### {opt['perspective'].title()}\n{opt['plan'][:200]}..."
                for opt in doc.design_options[:2]
            )
            sections.append(f"\n## Design Options\n{options_text}")

        return "\n".join(sections)

    def get_phase_result(self, phase: PlanPhase) -> PhaseResult | None:
        """Get the result from a specific phase.

        Args:
            phase: The phase to get results for

        Returns:
            The PhaseResult if available, None otherwise
        """
        return self.phase_results.get(phase)

    def get_plan_document(self) -> PlanDocument:
        """Get the current plan document.

        Returns:
            The PlanDocument
        """
        return self.plan_document
