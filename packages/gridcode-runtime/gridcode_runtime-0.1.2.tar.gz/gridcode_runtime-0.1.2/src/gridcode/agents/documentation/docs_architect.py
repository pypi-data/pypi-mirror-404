"""
Docs Architect Agent Module

Technical documentation expert for architecture guides and system documentation.
"""

from loguru import logger

from gridcode.agents.base import AgentResult, AgentStatus
from gridcode.agents.documentation.base import (
    BaseDocumentationAgent,
    DocFormat,
    DocumentationOutput,
    TargetAudience,
)
from gridcode.core.context import ExecutionContext
from gridcode.prompts.composer import PromptComposer


class DocScope:
    """Documentation scope constants"""

    ARCHITECTURE = "architecture"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    ALL = "all"


class DocsArchitectAgent(BaseDocumentationAgent):
    """
    Docs Architect Agent

    Technical documentation expert specializing in:
    - Architecture documentation
    - System design guides
    - Technical deep-dives
    - Developer handbooks

    Tool Permissions:
    - Allowed: Read, Glob, Grep, Write
    - Forbidden: Edit, Bash, Task, AskUserQuestion
    """

    def __init__(
        self,
        agent_id: str | None = None,
        prompt_composer: PromptComposer | None = None,
        output_format: DocFormat = DocFormat.MARKDOWN,
        target_audience: TargetAudience = TargetAudience.DEVELOPERS,
    ):
        """
        Initialize Docs Architect Agent

        Args:
            agent_id: Optional agent identifier
            prompt_composer: Optional PromptComposer instance
            output_format: Documentation output format
            target_audience: Primary audience for documentation
        """
        super().__init__(agent_id, prompt_composer, output_format)
        self.target_audience = target_audience

    async def execute(
        self,
        task: str,
        context: ExecutionContext,
        **kwargs,
    ) -> AgentResult:
        """
        Execute documentation task

        Args:
            task: Documentation task description
            context: Execution context
            **kwargs: Additional arguments:
                - doc_scope: "architecture" | "design" | "implementation" | "all"
                - target_audience: Override default target audience
                - output_path: Where to write documentation

        Returns:
            AgentResult with documentation output
        """
        logger.info(f"DocsArchitectAgent [{self.agent_id}] starting task: {task}")

        doc_scope = kwargs.get("doc_scope", DocScope.ALL)
        audience = kwargs.get("target_audience", self.target_audience)

        result = AgentResult(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            status=AgentStatus.RUNNING,
            metadata={
                "task": task,
                "working_dir": str(context.working_dir),
                "doc_scope": doc_scope,
                "target_audience": (
                    audience.value if isinstance(audience, TargetAudience) else audience
                ),
                "output_format": self.output_format.value,
            },
        )

        try:
            # Compose prompt
            prompt = await self._compose_prompt(task, context, doc_scope, audience)

            # Generate documentation (placeholder)
            output = await self._generate_docs(prompt, context, **kwargs)

            result.mark_completed(
                output=output.to_dict(),
                metadata={
                    **result.metadata,
                    "section_count": output.section_count,
                    "markdown_content": output.to_markdown(),
                },
            )

            logger.info(
                f"DocsArchitectAgent [{self.agent_id}] completed: "
                f"{output.section_count} sections"
            )

        except Exception as e:
            logger.error(f"DocsArchitectAgent [{self.agent_id}] failed: {e}")
            result.mark_failed(error=str(e))

        return result

    async def _compose_prompt(
        self,
        task: str,
        context: ExecutionContext,
        doc_scope: str,
        audience: TargetAudience,
    ) -> str:
        """Compose the documentation prompt"""
        try:
            return self.prompt_composer.compose(
                template_names=["agents/documentation/docs_architect"],
                static_vars={
                    "DOC_SCOPE": doc_scope,
                    "TARGET_AUDIENCE": (
                        audience.value if isinstance(audience, TargetAudience) else audience
                    ),
                    "WORKING_DIR": str(context.working_dir),
                    "OUTPUT_FORMAT": self.output_format.value,
                },
                context=context,
            )
        except Exception as e:
            logger.warning(f"Template load failed: {e}")
            return f"Document {doc_scope} for {task}"

    async def _generate_docs(
        self,
        prompt: str,
        context: ExecutionContext,
        **kwargs,
    ) -> DocumentationOutput:
        """Generate documentation (placeholder)"""
        return await self._create_mock_output(
            title="Architecture Documentation",
            summary="This is mock architecture documentation.",
            source_files=["src/", "docs/"],
        )

    def __repr__(self) -> str:
        return f"DocsArchitectAgent(id={self.agent_id}, " f"audience={self.target_audience.value})"
