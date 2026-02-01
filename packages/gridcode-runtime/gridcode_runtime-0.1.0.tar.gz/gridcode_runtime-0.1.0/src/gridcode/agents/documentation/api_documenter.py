"""
API Documenter Agent Module

API documentation specialist for comprehensive reference guides.
"""

from loguru import logger

from gridcode.agents.base import AgentResult, AgentStatus
from gridcode.agents.documentation.base import (
    BaseDocumentationAgent,
    DocFormat,
    DocumentationOutput,
    DocumentSection,
)
from gridcode.core.context import ExecutionContext
from gridcode.prompts.composer import PromptComposer


class APIScope:
    """API documentation scope constants"""

    PUBLIC = "public"
    INTERNAL = "internal"
    ALL = "all"


class APIDocumenterAgent(BaseDocumentationAgent):
    """
    API Documenter Agent

    API documentation specialist for:
    - Comprehensive API references
    - OpenAPI/Swagger specifications
    - SDK documentation
    - Parameter and type documentation

    Tool Permissions:
    - Allowed: Read, Glob, Grep, Write
    - Forbidden: Edit, Bash, Task, AskUserQuestion
    """

    def __init__(
        self,
        agent_id: str | None = None,
        prompt_composer: PromptComposer | None = None,
        output_format: DocFormat = DocFormat.MARKDOWN,
        include_examples: bool = True,
    ):
        """
        Initialize API Documenter Agent

        Args:
            agent_id: Optional agent identifier
            prompt_composer: Optional PromptComposer instance
            output_format: Documentation output format
            include_examples: Whether to include usage examples
        """
        super().__init__(agent_id, prompt_composer, output_format)
        self.include_examples = include_examples

    async def execute(
        self,
        task: str,
        context: ExecutionContext,
        **kwargs,
    ) -> AgentResult:
        """
        Execute API documentation task

        Args:
            task: Documentation task description
            context: Execution context
            **kwargs: Additional arguments:
                - api_scope: "public" | "internal" | "all"
                - include_examples: Override default
                - target_modules: Specific modules to document

        Returns:
            AgentResult with API documentation output
        """
        logger.info(f"APIDocumenterAgent [{self.agent_id}] starting task: {task}")

        api_scope = kwargs.get("api_scope", APIScope.PUBLIC)
        include_examples = kwargs.get("include_examples", self.include_examples)
        target_modules = kwargs.get("target_modules", [])

        result = AgentResult(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            status=AgentStatus.RUNNING,
            metadata={
                "task": task,
                "working_dir": str(context.working_dir),
                "api_scope": api_scope,
                "include_examples": include_examples,
                "target_modules": target_modules,
                "output_format": self.output_format.value,
            },
        )

        try:
            # Compose prompt
            prompt = await self._compose_prompt(task, context, api_scope, include_examples)

            # Generate API docs (placeholder)
            output = await self._generate_api_docs(prompt, context, **kwargs)

            result.mark_completed(
                output=output.to_dict(),
                metadata={
                    **result.metadata,
                    "section_count": output.section_count,
                    "markdown_content": output.to_markdown(),
                },
            )

            logger.info(
                f"APIDocumenterAgent [{self.agent_id}] completed: "
                f"{output.section_count} sections"
            )

        except Exception as e:
            logger.error(f"APIDocumenterAgent [{self.agent_id}] failed: {e}")
            result.mark_failed(error=str(e))

        return result

    async def _compose_prompt(
        self,
        task: str,
        context: ExecutionContext,
        api_scope: str,
        include_examples: bool,
    ) -> str:
        """Compose the API documentation prompt"""
        try:
            return self.prompt_composer.compose(
                template_names=["agents/documentation/api_documenter"],
                static_vars={
                    "API_SCOPE": api_scope,
                    "DOC_FORMAT": self.output_format.value,
                    "WORKING_DIR": str(context.working_dir),
                    "INCLUDE_EXAMPLES": "yes" if include_examples else "minimal",
                },
                context=context,
            )
        except Exception as e:
            logger.warning(f"Template load failed: {e}")
            return f"Document API for {task}"

    async def _generate_api_docs(
        self,
        prompt: str,
        context: ExecutionContext,
        **kwargs,
    ) -> DocumentationOutput:
        """Generate API documentation (placeholder)"""
        output = await self._create_mock_output(
            title="API Reference",
            summary="This is mock API documentation.",
            source_files=["src/"],
        )

        # Add API-specific sections
        output.add_section(
            DocumentSection(
                title="Module: gridcode.core",
                content="""### `GridCodeRuntime`

Main runtime class for executing agent tasks.

**Constructor**:
```python
GridCodeRuntime(api_key: str, framework: str = "langgraph")
```

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| api_key | str | Yes | API key for LLM |
| framework | str | No | Framework adapter |
""",
                order=2,
            )
        )

        return output

    def __repr__(self) -> str:
        return (
            f"APIDocumenterAgent(id={self.agent_id}, "
            f"format={self.output_format.value}, "
            f"examples={self.include_examples})"
        )
