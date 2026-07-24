from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.agent.messages import ToolCall


AgentStatus = Literal[
    "running",
    "completed",
    "failed",
    "waiting_approval",
    "max_steps_exceeded",
]


class AgentState(BaseModel):
    """保存 Agent 一次运行过程中的状态。"""

    model_config = ConfigDict(
        extra="forbid",
    )

    run_id: str = Field(
        default_factory=lambda: str(uuid4())
    )
    status: AgentStatus = "running"
    step_count: int = Field(default=0, ge=0)
    messages: list[dict[str, Any]] = Field(
        default_factory=list,
    )
    tool_calls: list[ToolCall] = Field(
        default_factory=list,
    )
    tool_results: list[dict[str, Any]] = Field(
        default_factory=list,
    )
    final_answer: str | None = None
    error: str | None = None