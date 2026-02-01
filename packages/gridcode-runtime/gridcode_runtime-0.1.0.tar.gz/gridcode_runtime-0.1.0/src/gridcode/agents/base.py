"""
Base Agent Module

This module defines the abstract base class for all agents in GridCode Runtime.
Inspired by Claude Code's agent system architecture.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from gridcode.core.context import ExecutionContext


class AgentType(str, Enum):
    """Agent type enumeration"""

    MAIN = "main"
    EXPLORE = "explore"
    PLAN = "plan"
    CODE_REVIEW = "code_review"
    TEST_RUNNER = "test_runner"
    # Expert agents
    CODE_REVIEWER = "code_reviewer"
    DEBUGGER = "debugger"
    ARCHITECT = "architect"
    # Documentation agents
    DOCS_ARCHITECT = "docs_architect"
    TUTORIAL_ENGINEER = "tutorial_engineer"
    API_DOCUMENTER = "api_documenter"


class AgentStatus(str, Enum):
    """Agent execution status"""

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentResult(BaseModel):
    """
    Agent execution result

    Attributes:
        agent_id: Unique agent identifier
        agent_type: Type of the agent
        status: Execution status
        output: Agent output content
        metadata: Additional metadata
        error: Error message if failed
        start_time: Execution start time
        end_time: Execution end time
        duration: Execution duration in seconds
    """

    agent_id: str = Field(..., description="Unique agent identifier")
    agent_type: AgentType = Field(..., description="Type of the agent")
    status: AgentStatus = Field(default=AgentStatus.IDLE, description="Execution status")
    output: Any = Field(
        default="", description="Agent output content (can be str, dict, or any type)"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    error: str | None = Field(default=None, description="Error message if failed")
    start_time: datetime = Field(default_factory=datetime.now, description="Execution start time")
    end_time: datetime | None = Field(default=None, description="Execution end time")
    duration: float | None = Field(default=None, description="Execution duration in seconds")

    def mark_completed(self, output: Any, metadata: dict[str, Any] | None = None):
        """Mark agent as completed successfully"""
        self.status = AgentStatus.COMPLETED
        self.output = output
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
        if metadata:
            self.metadata.update(metadata)

    def mark_failed(self, error: str, metadata: dict[str, Any] | None = None):
        """Mark agent as failed with error"""
        self.status = AgentStatus.FAILED
        self.error = error
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
        if metadata:
            self.metadata.update(metadata)


class BaseAgent(ABC):
    """
    Abstract base class for all agents

    All agent implementations must inherit from this class and implement
    the abstract methods. Inspired by Claude Code's agent permission system.

    Attributes:
        agent_type: Type of this agent
        allowed_tools: List of allowed tool names ("*" means all tools)
        forbidden_tools: List of forbidden tool names (takes precedence)
    """

    agent_type: AgentType = AgentType.MAIN
    allowed_tools: list[str] = ["*"]  # "*" means all tools allowed
    forbidden_tools: list[str] = []

    def __init__(self, agent_id: str | None = None):
        """
        Initialize base agent

        Args:
            agent_id: Optional agent identifier (auto-generated if not provided)
        """
        self.agent_id = agent_id or self._generate_agent_id()

    def _generate_agent_id(self) -> str:
        """Generate unique agent ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        return f"{self.agent_type.value}_{timestamp}"

    @abstractmethod
    async def execute(self, task: str, context: ExecutionContext, **kwargs) -> AgentResult:
        """
        Execute agent task

        Args:
            task: Task description
            context: Execution context
            **kwargs: Additional arguments

        Returns:
            AgentResult: Execution result

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError("Subclass must implement execute() method")

    def get_allowed_tools(self) -> list[str]:
        """
        Get list of allowed tools

        Returns:
            List of allowed tool names
        """
        return self.allowed_tools

    def get_forbidden_tools(self) -> list[str]:
        """
        Get list of forbidden tools

        Returns:
            List of forbidden tool names
        """
        return self.forbidden_tools

    def can_use_tool(self, tool_name: str) -> bool:
        """
        Check if agent can use a specific tool

        Permission logic (inspired by Claude Code):
        1. If tool is in forbidden_tools → False
        2. If "*" is in allowed_tools → True
        3. If tool is in allowed_tools → True
        4. Otherwise → False

        Args:
            tool_name: Name of the tool to check

        Returns:
            True if tool is allowed, False otherwise
        """
        # Forbidden list takes precedence
        if tool_name in self.forbidden_tools:
            return False

        # "*" means all tools allowed
        if "*" in self.allowed_tools:
            return True

        # Check if tool is in allowed list
        if tool_name in self.allowed_tools:
            return True

        # Default deny
        return False

    def validate_tool_usage(self, tool_name: str) -> None:
        """
        Validate tool usage and raise exception if not allowed

        Args:
            tool_name: Name of the tool to validate

        Raises:
            PermissionError: If tool is not allowed
        """
        if not self.can_use_tool(tool_name):
            raise PermissionError(
                f"Agent '{self.agent_type.value}' is not allowed to use tool '{tool_name}'. "
                f"Allowed: {self.allowed_tools}, Forbidden: {self.forbidden_tools}"
            )

    def __repr__(self) -> str:
        """String representation of agent"""
        return f"{self.__class__.__name__}(id={self.agent_id}, " f"type={self.agent_type.value})"
