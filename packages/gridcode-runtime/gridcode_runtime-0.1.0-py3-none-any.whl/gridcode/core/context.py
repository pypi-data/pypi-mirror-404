"""Execution context for agent runtime."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExecutionContext(BaseModel):
    """Execution context for agent runtime.

    Manages session state, working directory, environment variables,
    and other runtime information.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    session_id: str
    working_dir: Path
    env_vars: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # State flags
    is_plan_mode: bool = False
    is_learning_mode: bool = False
