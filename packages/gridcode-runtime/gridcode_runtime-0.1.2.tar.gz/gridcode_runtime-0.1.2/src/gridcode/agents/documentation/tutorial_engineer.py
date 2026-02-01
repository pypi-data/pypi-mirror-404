"""
Tutorial Engineer Agent Module

Creates step-by-step tutorials and educational content from code.
"""

from loguru import logger

from gridcode.agents.base import AgentResult, AgentStatus
from gridcode.agents.documentation.base import (
    BaseDocumentationAgent,
    DocFormat,
    DocumentationOutput,
    DocumentSection,
    SkillLevel,
)
from gridcode.core.context import ExecutionContext
from gridcode.prompts.composer import PromptComposer


class TutorialEngineerAgent(BaseDocumentationAgent):
    """
    Tutorial Engineer Agent

    Educational content specialist for:
    - Step-by-step learning guides
    - Hands-on coding tutorials
    - Progressive complexity content
    - Example-driven teaching

    Tool Permissions:
    - Allowed: Read, Glob, Grep, Write
    - Forbidden: Edit, Bash, Task, AskUserQuestion
    """

    def __init__(
        self,
        agent_id: str | None = None,
        prompt_composer: PromptComposer | None = None,
        output_format: DocFormat = DocFormat.MARKDOWN,
        skill_level: SkillLevel = SkillLevel.INTERMEDIATE,
    ):
        """
        Initialize Tutorial Engineer Agent

        Args:
            agent_id: Optional agent identifier
            prompt_composer: Optional PromptComposer instance
            output_format: Tutorial output format
            skill_level: Default target skill level
        """
        super().__init__(agent_id, prompt_composer, output_format)
        self.skill_level = skill_level

    async def execute(
        self,
        task: str,
        context: ExecutionContext,
        **kwargs,
    ) -> AgentResult:
        """
        Execute tutorial creation task

        Args:
            task: Tutorial task description
            context: Execution context
            **kwargs: Additional arguments:
                - tutorial_topic: Main topic for the tutorial
                - skill_level: Override default skill level
                - learning_objectives: List of objectives

        Returns:
            AgentResult with tutorial output
        """
        logger.info(f"TutorialEngineerAgent [{self.agent_id}] starting task: {task}")

        topic = kwargs.get("tutorial_topic", task)
        level = kwargs.get("skill_level", self.skill_level)
        objectives = kwargs.get("learning_objectives", [])

        result = AgentResult(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            status=AgentStatus.RUNNING,
            metadata={
                "task": task,
                "working_dir": str(context.working_dir),
                "tutorial_topic": topic,
                "skill_level": level.value if isinstance(level, SkillLevel) else level,
                "learning_objectives": objectives,
            },
        )

        try:
            # Compose prompt
            prompt = await self._compose_prompt(task, context, topic, level, objectives)

            # Generate tutorial (placeholder)
            output = await self._generate_tutorial(prompt, context, **kwargs)

            result.mark_completed(
                output=output.to_dict(),
                metadata={
                    **result.metadata,
                    "section_count": output.section_count,
                    "markdown_content": output.to_markdown(),
                },
            )

            logger.info(
                f"TutorialEngineerAgent [{self.agent_id}] completed: "
                f"{output.section_count} steps"
            )

        except Exception as e:
            logger.error(f"TutorialEngineerAgent [{self.agent_id}] failed: {e}")
            result.mark_failed(error=str(e))

        return result

    async def _compose_prompt(
        self,
        task: str,
        context: ExecutionContext,
        topic: str,
        level: SkillLevel,
        objectives: list[str],
    ) -> str:
        """Compose the tutorial prompt"""
        try:
            return self.prompt_composer.compose(
                template_names=["agents/documentation/tutorial_engineer"],
                static_vars={
                    "TUTORIAL_TOPIC": topic,
                    "SKILL_LEVEL": level.value if isinstance(level, SkillLevel) else level,
                    "WORKING_DIR": str(context.working_dir),
                    "LEARNING_OBJECTIVES": (
                        ", ".join(objectives) if objectives else "understand the topic"
                    ),
                },
                context=context,
            )
        except Exception as e:
            logger.warning(f"Template load failed: {e}")
            return f"Create tutorial for {topic}"

    async def _generate_tutorial(
        self,
        prompt: str,
        context: ExecutionContext,
        **kwargs,
    ) -> DocumentationOutput:
        """Generate tutorial (placeholder)"""
        output = await self._create_mock_output(
            title=f"Tutorial: {kwargs.get('tutorial_topic', 'Getting Started')}",
            summary="This is a mock tutorial.",
            source_files=["examples/"],
        )

        # Add tutorial-specific sections
        output.add_section(
            DocumentSection(
                title="What You Will Learn",
                content="- Objective 1\n- Objective 2\n- Objective 3",
                order=0,
            )
        )

        output.add_section(
            DocumentSection(
                title="Step 1: Setup",
                content="First, set up your environment...",
                order=2,
            )
        )

        return output

    def __repr__(self) -> str:
        return f"TutorialEngineerAgent(id={self.agent_id}, " f"level={self.skill_level.value})"
