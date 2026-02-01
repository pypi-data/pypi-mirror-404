"""Pydantic models for GridCode configuration validation."""

from pydantic import BaseModel, Field, field_validator


class RuntimeConfig(BaseModel):
    """Runtime configuration settings."""

    # API Provider: openai or anthropic
    api_provider: str = Field(default="openai", description="API provider: 'openai' or 'anthropic'")
    api_key: str = Field(
        default="${OPENAI_API_KEY}",
        description="API key (OpenAI or Anthropic, supports ${VAR} environment variable expansion)",
    )
    api_base_url: str | None = Field(
        default=None, description="Optional custom API base URL (useful for proxies or self-hosted)"
    )
    framework: str = Field(
        default="langgraph", description="Agent framework: 'langgraph' or 'pydantic-ai'"
    )
    model: str = Field(
        default="${OPENAI_MODEL_NAME}",
        description=(
            "Default model to use (OpenAI: gpt-4, gpt-4-turbo, gpt-3.5-turbo, etc.; "
            "Anthropic: claude-sonnet, etc.). Supports ${VAR} environment variable expansion."
        ),
    )
    working_dir: str = Field(default=".", description="Working directory for agent execution")
    template_dir: str | None = Field(
        default=None,
        description=(
            "Directory containing prompt templates. "
            "If None, uses built-in templates from the package."
        ),
    )

    @field_validator("api_provider")
    @classmethod
    def validate_api_provider(cls, v: str) -> str:
        """Validate API provider is one of supported options."""
        valid = ["openai", "anthropic"]
        if v not in valid:
            raise ValueError(f"api_provider must be one of {valid}, got {v}")
        return v

    @field_validator("framework")
    @classmethod
    def validate_framework(cls, v: str) -> str:
        """Validate framework is one of supported options."""
        valid = ["langgraph", "pydantic-ai"]
        if v not in valid:
            raise ValueError(f"framework must be one of {valid}, got {v}")
        return v

    model_config = {"extra": "allow"}


class AnthropicConfig(BaseModel):
    """Anthropic-specific configuration."""

    api_key: str = Field(default="${ANTHROPIC_API_KEY}", description="Anthropic API key")
    base_url: str = Field(default="https://api.anthropic.com", description="Anthropic API base URL")
    model: str = Field(default="claude-sonnet-4-5", description="Default Anthropic model")
    max_tokens: int = Field(default=4000, description="Maximum tokens for completion")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="Temperature (0.0-1.0)")

    model_config = {"extra": "allow"}


class AgentPoolConfig(BaseModel):
    """Agent pool configuration."""

    max_agents: int = Field(default=5, ge=1, description="Maximum number of concurrent agents")
    cache_enabled: bool = Field(default=True, description="Enable agent result caching")
    cache_max_size: int = Field(default=100, ge=1, description="Maximum cache size")
    cache_ttl: int = Field(default=3600, ge=0, description="Cache TTL in seconds")

    model_config = {"extra": "allow"}


class MCPServerConfig(BaseModel):
    """MCP server configuration."""

    name: str = Field(description="Server name")
    type: str = Field(
        default="stdio", description="Transport type: 'stdio', 'http', 'sse', or 'websocket'"
    )
    command: str | None = Field(
        default=None, description="Command to launch server (for stdio type)"
    )
    args: list[str] = Field(default_factory=list, description="Command arguments (for stdio type)")
    url: str | None = Field(default=None, description="Server URL (for http/sse type)")
    env: dict[str, str] = Field(
        default_factory=dict, description="Environment variables for server"
    )

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate transport type."""
        valid = ["stdio", "http", "sse", "websocket"]
        if v not in valid:
            raise ValueError(f"type must be one of {valid}, got {v}")
        return v

    model_config = {"extra": "allow"}


class MCPConfig(BaseModel):
    """MCP (Model Context Protocol) configuration."""

    enabled: bool = Field(default=True, description="Enable MCP support")
    connection_pool_size: int = Field(default=5, ge=1, description="Connection pool size")
    timeout: int = Field(default=30, ge=1, description="Request timeout in seconds")
    servers: list[MCPServerConfig] = Field(
        default_factory=list, description="List of MCP servers to connect"
    )

    model_config = {"extra": "allow"}


class PluginsConfig(BaseModel):
    """Plugin system configuration."""

    enabled: bool = Field(default=True, description="Enable plugin system")
    auto_discover: bool = Field(
        default=True, description="Auto-discover plugins from plugin directories"
    )
    dirs: list[str] = Field(
        default_factory=lambda: ["~/.gridcode/plugins", "./plugins"],
        description="Directories to search for plugins",
    )
    entry_point_group: str = Field(
        default="gridcode.plugins", description="Entry point group for plugin discovery"
    )

    model_config = {"extra": "allow"}


class AgentConfig(BaseModel):
    """Configuration for individual agent."""

    enabled: bool = Field(default=True, description="Whether this agent is enabled")
    max_depth: int | None = Field(
        default=None, description="Maximum recursion depth (for Explore agent)"
    )
    auto_approve: bool | None = Field(
        default=None, description="Auto-approve decisions (for Plan agent)"
    )

    model_config = {"extra": "allow"}


class AgentsConfig(BaseModel):
    """Configuration for agent pool."""

    explore: AgentConfig = Field(
        default_factory=lambda: AgentConfig(enabled=True, max_depth=3),
        description="Explore agent configuration",
    )
    plan: AgentConfig = Field(
        default_factory=lambda: AgentConfig(enabled=True, auto_approve=False),
        description="Plan agent configuration",
    )
    review: AgentConfig = Field(
        default_factory=lambda: AgentConfig(enabled=True), description="Review agent configuration"
    )

    model_config = {"extra": "allow"}


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(
        default="INFO", description="Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
    format: str = Field(default="text", description="Log format: 'json' or 'text'")
    file: str | None = Field(default=None, description="Log file path (optional)")
    colored: bool = Field(default=True, description="Enable colored output (text format only)")

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate log level."""
        valid = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid:
            raise ValueError(f"level must be one of {valid}, got {v}")
        return v_upper

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate log format."""
        valid = ["json", "text"]
        if v not in valid:
            raise ValueError(f"format must be one of {valid}, got {v}")
        return v

    model_config = {"extra": "allow"}


class PerformanceConfig(BaseModel):
    """Performance tuning configuration."""

    lazy_loading: bool = Field(default=True, description="Enable lazy loading for agent pool")
    connection_pooling: bool = Field(default=True, description="Enable connection pooling for MCP")

    model_config = {"extra": "allow"}


class PlanModeConfig(BaseModel):
    """5-Phase Planning Mode configuration."""

    enabled: bool = Field(default=True, description="Enable 5-Phase Planning Mode")
    auto_save: bool = Field(default=True, description="Auto-save plan to file")
    plan_file: str = Field(default=".gridcode/plan.md", description="Plan file path")

    model_config = {"extra": "allow"}


class LearningModeConfig(BaseModel):
    """Learning Mode configuration."""

    enabled: bool = Field(default=False, description="Enable Learning Mode (feedback collection)")
    feedback_dir: str = Field(
        default=".gridcode/feedback", description="Feedback storage directory"
    )

    model_config = {"extra": "allow"}


class WorkflowsConfig(BaseModel):
    """Workflows configuration."""

    plan_mode: PlanModeConfig = Field(
        default_factory=PlanModeConfig, description="5-Phase Planning Mode configuration"
    )
    learning_mode: LearningModeConfig = Field(
        default_factory=LearningModeConfig, description="Learning Mode configuration"
    )

    model_config = {"extra": "allow"}


class InteractionConfig(BaseModel):
    """Human-in-the-loop interaction configuration."""

    auto_approve: list[str] = Field(
        default_factory=list, description="Auto-approve for specific operations (use with caution)"
    )
    timeout: int = Field(
        default=0, ge=0, description="Timeout for user input (seconds, 0 = no timeout)"
    )

    model_config = {"extra": "allow"}


class GridCodeConfig(BaseModel):
    """Root GridCode configuration model."""

    runtime: RuntimeConfig = Field(
        default_factory=RuntimeConfig, description="Runtime configuration"
    )
    anthropic: AnthropicConfig = Field(
        default_factory=AnthropicConfig, description="Anthropic-specific configuration"
    )
    agent_pool: AgentPoolConfig = Field(
        default_factory=AgentPoolConfig, description="Agent pool configuration"
    )
    agents: AgentsConfig = Field(
        default_factory=AgentsConfig, description="Individual agent configuration"
    )
    mcp: MCPConfig = Field(default_factory=MCPConfig, description="MCP configuration")
    plugins: PluginsConfig = Field(
        default_factory=PluginsConfig, description="Plugin system configuration"
    )
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig, description="Logging configuration"
    )
    performance: PerformanceConfig = Field(
        default_factory=PerformanceConfig, description="Performance tuning configuration"
    )
    workflows: WorkflowsConfig = Field(
        default_factory=WorkflowsConfig, description="Workflows configuration"
    )
    interaction: InteractionConfig = Field(
        default_factory=InteractionConfig, description="Human-in-the-loop interaction configuration"
    )

    model_config = {"extra": "allow"}

    @classmethod
    def default(cls) -> "GridCodeConfig":
        """Create default configuration."""
        return cls()
