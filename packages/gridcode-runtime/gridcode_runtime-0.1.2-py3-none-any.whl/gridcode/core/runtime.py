"""GridCode Runtime main entry point."""

from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger
from pydantic import BaseModel

from gridcode.core.context import ExecutionContext

if TYPE_CHECKING:

    from gridcode.agents.aggregator import ResultAggregator
    from gridcode.agents.message_bus import MessageBus
    from gridcode.agents.pool import AgentPool
    from gridcode.interaction.base import InteractionHandler
    from gridcode.plugins.base import PluginManager
    from gridcode.plugins.hooks import HookRegistry
    from gridcode.prompts.composer import PromptComposer
    from gridcode.storage.base import StorageBackend
    from gridcode.tools.registry import ToolRegistry


class RuntimeResult(BaseModel):
    """Result from runtime execution."""

    output: str
    metadata: dict[str, Any] = {}


class GridCodeRuntime:
    """Main runtime for GridCode agent system.

    Features:
    - Multi-framework support (LangGraph, Pydantic-AI)
    - Tool registry and execution
    - Agent pool for parallel execution
    - Session persistence with configurable storage backends
    - System reminder injection
    - Human-in-the-loop interactions
    - Plugin system for extensibility
    - Hook system for lifecycle events
    """

    def __init__(
        self,
        api_key: str,
        framework: str = "langgraph",
        api_provider: str = "openai",
        model: str | None = None,
        template_dir: Path | None = None,
        storage: "StorageBackend | None" = None,
        interaction: "InteractionHandler | None" = None,
        context: ExecutionContext | None = None,
    ):
        """Initialize GridCode Runtime.

        Args:
            api_key: API key (OpenAI or Anthropic)
            framework: Framework to use ("langgraph" or "pydantic-ai")
            api_provider: API provider ("openai" or "anthropic")
            model: Model name (defaults based on provider)
            template_dir: Directory containing prompt templates
            storage: Optional storage backend for session persistence
            interaction: Optional interaction handler for human-in-the-loop.
                        If not provided, a ConsoleInteractionHandler will be used.
            context: Optional execution context. If not provided, a new one will be created.
        """
        self.api_key = api_key
        self.framework = framework
        self.api_provider = api_provider

        # Set default model based on provider
        if model is None:
            self.model = (
                "gpt-3.5-turbo" if api_provider == "openai" else "claude-3-5-sonnet-20241022"
            )
        else:
            self.model = model

        # Lazy initialization of Anthropic client
        # Only imported and instantiated when actually needed
        self._client = None
        self._client_initialized = False

        # Lazy initialization of components
        self._composer: PromptComposer | None = None
        self._template_dir = template_dir
        self.storage = storage

        # Initialize interaction handler (lazy for console handler)
        self._interaction = interaction

        # Lazy initialization of core components
        self._tool_registry: ToolRegistry | None = None
        self._agent_pool: AgentPool | None = None
        self._message_bus: MessageBus | None = None
        self._result_aggregator: ResultAggregator | None = None

        # Lazy initialization of plugin and hook system
        self._hook_registry: HookRegistry | None = None
        self._plugin_manager: PluginManager | None = None

        # Initialize or use provided context
        if context is not None:
            self.context = context
        else:
            # Create default context with required fields
            import uuid

            self.context = ExecutionContext(
                session_id=str(uuid.uuid4()),
                working_dir=Path.cwd(),
            )

        # Nexus Engine (lazy initialization)
        self.nexus_engine = None

        logger.info(f"GridCodeRuntime initialized with framework: {framework}")

    @property
    def client(self):
        """Lazy initialization of Anthropic client."""
        if not self._client_initialized:
            if self.api_provider == "anthropic":
                from anthropic import Anthropic

                self._client = Anthropic(api_key=self.api_key)
            else:
                self._client = None  # OpenAI models accessed through LangChain
            self._client_initialized = True
        return self._client

    @property
    def composer(self) -> "PromptComposer":
        """Lazy initialization of PromptComposer."""
        if self._composer is None:
            from gridcode.prompts.composer import PromptComposer

            self._composer = PromptComposer(template_dir=self._template_dir)
        return self._composer

    @property
    def tool_registry(self) -> "ToolRegistry":
        """Lazy initialization of ToolRegistry."""
        if self._tool_registry is None:
            from gridcode.tools.registry import ToolRegistry

            self._tool_registry = ToolRegistry()
            self._register_default_tools()
        return self._tool_registry

    @property
    def agent_pool(self) -> "AgentPool":
        """Lazy initialization of AgentPool."""
        if self._agent_pool is None:
            from gridcode.agents.pool import AgentPool

            self._agent_pool = AgentPool()
        return self._agent_pool

    @property
    def message_bus(self) -> "MessageBus":
        """Lazy initialization of MessageBus."""
        if self._message_bus is None:
            from gridcode.agents.message_bus import MessageBus

            self._message_bus = MessageBus()
        return self._message_bus

    @property
    def result_aggregator(self) -> "ResultAggregator":
        """Lazy initialization of ResultAggregator."""
        if self._result_aggregator is None:
            from gridcode.agents.aggregator import ResultAggregator

            self._result_aggregator = ResultAggregator()
        return self._result_aggregator

    @property
    def hook_registry(self) -> "HookRegistry":
        """Lazy initialization of HookRegistry."""
        if self._hook_registry is None:
            from gridcode.plugins.hooks import HookRegistry

            self._hook_registry = HookRegistry()
        return self._hook_registry

    def _register_default_tools(self) -> None:
        """Register default tools in the registry."""
        from gridcode.tools.implementations import (
            EditTool,
            GlobTool,
            GrepTool,
            ReadTool,
            WriteTool,
        )

        default_tools = [
            ReadTool(),
            WriteTool(),
            EditTool(),
            GlobTool(),
            GrepTool(),
        ]

        for tool in default_tools:
            self._tool_registry.register_tool(tool)

        logger.info(f"Registered {len(default_tools)} default tools")

    @classmethod
    async def create(
        cls,
        api_key: str,
        framework: str = "langgraph",
        api_provider: str = "openai",
        model: str | None = None,
        template_dir: Path | None = None,
        storage: "StorageBackend | None" = None,
        interaction: "InteractionHandler | None" = None,
        context: ExecutionContext | None = None,
    ) -> "GridCodeRuntime":
        """Create a GridCodeRuntime instance.

        Args:
            api_key: API key (OpenAI or Anthropic)
            framework: Framework to use ("langgraph" or "pydantic-ai")
            template_dir: Directory containing prompt templates
            storage: Optional storage backend for session persistence
            interaction: Optional interaction handler for human-in-the-loop
            context: Optional execution context. If not provided, a new one will be created.

        Returns:
            GridCodeRuntime instance
        """
        runtime = cls(
            api_key=api_key,
            framework=framework,
            api_provider=api_provider,
            model=model,
            template_dir=template_dir,
            storage=storage,
            interaction=interaction,
            context=context,
        )
        await runtime.initialize()
        return runtime

    @property
    def interaction(self) -> "InteractionHandler":
        """Get the interaction handler, creating a console handler if needed."""
        if self._interaction is None:
            from gridcode.interaction.console import ConsoleInteractionHandler

            self._interaction = ConsoleInteractionHandler()
        return self._interaction

    @property
    def plugin_manager(self) -> "PluginManager":
        """Get the plugin manager, creating one if needed."""
        if self._plugin_manager is None:
            from gridcode.plugins.base import PluginManager

            self._plugin_manager = PluginManager(self)
        return self._plugin_manager

    async def initialize(self) -> None:
        """Initialize the Nexus Engine based on selected framework."""
        if self.framework == "langgraph":
            from gridcode.nexus.langgraph import LangGraphAdapter

            self.nexus_engine = LangGraphAdapter(
                api_key=self.api_key,
                api_provider=self.api_provider,
                model_name=self.model,
            )
            logger.info(f"Initialized LangGraph adapter with {self.api_provider} provider")
        elif self.framework == "pydantic-ai":
            from gridcode.nexus.pydantic_ai import PydanticAIAdapter

            # Map api_provider to Pydantic-AI model format
            if self.api_provider == "anthropic":
                model_name = f"anthropic:{self.model}"
            elif self.api_provider == "openai":
                model_name = f"openai:{self.model}"
            else:
                model_name = self.model

            self.nexus_engine = PydanticAIAdapter(model_name=model_name)
            logger.info(f"Initialized Pydantic-AI adapter with model: {model_name}")
        else:
            raise ValueError(f"Unsupported framework: {self.framework}")

    async def resume_session(self, session_id: str) -> ExecutionContext | None:
        """Resume a previous session by loading its context.

        Args:
            session_id: Unique identifier for the session

        Returns:
            The ExecutionContext if found, None otherwise

        Note:
            Requires a storage backend to be configured.
        """
        if self.storage is None:
            logger.warning("No storage backend configured, cannot resume session")
            return None

        context = await self.storage.load_context(session_id)
        if context:
            logger.info(f"Resumed session: {session_id}")
        else:
            logger.info(f"Session not found: {session_id}")
        return context

    async def save_session(
        self,
        context: ExecutionContext,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Save the current session context.

        Args:
            context: The ExecutionContext to save
            metadata: Optional additional metadata to store

        Note:
            Requires a storage backend to be configured.
        """
        if self.storage is None:
            logger.warning("No storage backend configured, cannot save session")
            return

        await self.storage.save_context(context.session_id, context, metadata)
        logger.info(f"Saved session: {context.session_id}")

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session from storage.

        Args:
            session_id: Unique identifier for the session

        Returns:
            True if the session was deleted, False if it didn't exist

        Note:
            Requires a storage backend to be configured.
        """
        if self.storage is None:
            logger.warning("No storage backend configured, cannot delete session")
            return False

        deleted = await self.storage.delete_context(session_id)
        if deleted:
            logger.info(f"Deleted session: {session_id}")
        return deleted

    async def list_sessions(self) -> list:
        """List all stored sessions.

        Returns:
            List of SessionMetadata for all stored sessions

        Note:
            Requires a storage backend to be configured.
            Returns empty list if no storage configured.
        """
        if self.storage is None:
            logger.warning("No storage backend configured, returning empty list")
            return []

        return await self.storage.list_sessions()

    async def run(self, prompt: str, context: ExecutionContext) -> RuntimeResult:
        """Run the agent with a given prompt and context.

        Args:
            prompt: User prompt
            context: Execution context

        Returns:
            RuntimeResult with output and metadata
        """
        # Initialize Nexus Engine if not already done
        if self.nexus_engine is None:
            await self.initialize()

        # Use Nexus Engine for execution (supports both OpenAI and Anthropic)
        from gridcode.nexus.types import NexusAgentState

        initial_state = NexusAgentState(messages=[])
        result = await self.nexus_engine.execute(
            prompt=prompt,
            state=initial_state,
            tools=None,  # No tools for simple run
        )

        # Extract output
        output = result.output

        return RuntimeResult(
            output=output,
            metadata={
                "session_id": context.session_id,
                "model": self.model,
                "provider": self.api_provider,
            },
        )

    async def execute_with_agents(
        self,
        prompt: str,
        context: ExecutionContext | None = None,
        tools: list[str] | None = None,
        auto_save: bool = False,
    ) -> RuntimeResult:
        """Execute prompt with agent system (Nexus Engine + Agent Pool).

        This method orchestrates the full agent execution flow:
        1. Compose prompt with templates
        2. Convert tools to framework format
        3. Execute main agent through Nexus Engine
        4. Handle sub-agent spawning via Agent Pool
        5. Aggregate results from multiple agents
        6. Optionally save session state

        Args:
            prompt: User prompt
            context: Execution context. If None, uses self.context.
            tools: Optional list of tool names to make available
            auto_save: If True and storage is configured, save session after execution

        Returns:
            RuntimeResult with aggregated output and metadata
        """
        if self.nexus_engine is None:
            raise RuntimeError("Nexus Engine not initialized. Call initialize() first.")

        # Use provided context or fall back to self.context
        if context is None:
            context = self.context

        logger.info(f"Executing with agents: session={context.session_id}")

        # Step 1: Compose prompt with templates
        composed_prompt = self._compose_prompt(prompt, context)

        # Step 2: Convert tools to framework format
        framework_tools = None
        if tools:
            framework_tools = self._convert_tools(tools)
            logger.info(f"Converted {len(framework_tools)} tools for execution")

        # Step 3: Execute main agent through Nexus Engine
        from gridcode.nexus.types import NexusAgentState

        initial_state = NexusAgentState(messages=[])
        result = await self.nexus_engine.execute(
            prompt=composed_prompt, state=initial_state, tools=framework_tools
        )

        # Step 4: Extract output
        output = result.output

        # Step 5: Build metadata with usage statistics
        metadata = {
            "session_id": context.session_id,
            "framework": self.framework,
            "agent_count": 1,  # Main agent only for now
            "tools_used": tools or [],
            **result.metadata,
        }

        # Add token usage if available
        if result.usage:
            metadata["usage"] = result.usage

        logger.info(f"Agent execution completed: {len(output)} chars output")

        # Step 6: Auto-save session if configured
        if auto_save and self.storage is not None:
            await self.save_session(context, {"last_prompt": prompt})

        return RuntimeResult(output=output, metadata=metadata)

    def _compose_prompt(self, prompt: str, context: ExecutionContext) -> str:
        """Compose prompt with templates and context.

        Args:
            prompt: User prompt
            context: Execution context

        Returns:
            Composed prompt string
        """
        # Build reminder context for system reminders
        reminder_context = {
            "is_plan_mode": context.is_plan_mode,
            "is_learning_mode": context.is_learning_mode,
        }

        # Try to load main_agent template with reminders
        try:
            composed = self.composer.compose_with_reminders(
                template_names=["main_agent"],
                static_vars={
                    "USER_PROMPT": prompt,
                    "WORKING_DIR": str(context.working_dir),
                    "SESSION_ID": context.session_id,
                    "IS_PLAN_MODE": str(context.is_plan_mode).lower(),
                },
                context=context,
                reminder_context=reminder_context,
            )
            logger.debug("Composed prompt with main_agent template and reminders")
            return composed
        except Exception as e:
            # Fallback to raw prompt if template not found
            logger.warning(f"Failed to compose prompt with template: {e}")
            return prompt

    def _convert_tools(self, tool_names: list[str]) -> list:
        """Convert tool names to framework-specific tools.

        Args:
            tool_names: List of tool names to convert

        Returns:
            List of framework-specific tool objects
        """
        # Lazy import to avoid circular dependencies
        from gridcode.nexus.tool_converter import convert_to_langgraph_tool

        framework_tools = []
        for name in tool_names:
            tool = self.tool_registry.get_tool(name)
            if tool:
                converted = convert_to_langgraph_tool(tool)
                framework_tools.append(converted)
                logger.debug(f"Converted tool: {name}")
            else:
                logger.warning(f"Tool not found: {name}")

        return framework_tools

    # Human-in-the-Loop Methods

    async def ask_user(
        self,
        question: str,
        options: list[str] | None = None,
        allow_free_text: bool = True,
        default: str | None = None,
    ) -> str:
        """Ask the user a question.

        This method provides a simple interface for asking questions.
        For more control, use the interaction handler directly.

        Args:
            question: The question to ask
            options: Optional list of options to choose from
            allow_free_text: Whether to allow free-text input
            default: Default value if no input provided

        Returns:
            The user's answer
        """
        from gridcode.interaction.base import UserQuestion

        q = UserQuestion(
            question=question,
            options=options,
            allow_free_text=allow_free_text,
            default=default,
        )

        response = await self.interaction.ask_question(q)
        return response.answer

    async def request_confirmation(
        self,
        message: str,
        default: bool = False,
    ) -> bool:
        """Request user confirmation for an action.

        Args:
            message: The confirmation message
            default: Default value if user presses Enter

        Returns:
            True if confirmed, False otherwise
        """
        return await self.interaction.request_confirmation(message, default)

    async def notify_user(
        self,
        message: str,
        level: str = "info",
    ) -> None:
        """Send a notification to the user.

        Args:
            message: The message to display
            level: The notification level (info, warning, error, success)
        """
        await self.interaction.notify(message, level)

    async def show_progress(
        self,
        message: str,
        progress: float | None = None,
    ) -> None:
        """Show progress information to the user.

        Args:
            message: The progress message
            progress: Optional progress percentage (0-100)
        """
        await self.interaction.show_progress(message, progress)
