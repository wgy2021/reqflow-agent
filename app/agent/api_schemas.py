from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.agent.messages import ToolCall
from app.agent.state import AgentStatus


class AgentRunRequest(BaseModel):
    """创建一次 Agent 运行的请求。"""

    model_config = ConfigDict(
        extra="forbid",
    )

    message: str
    requirement_id: int | None = Field(
        default=None,
        ge=1,
    )
    max_steps: int = Field(
        default=5,
        ge=1,
        le=20,
    )

    @field_validator("message")
    @classmethod
    def validate_message(
        cls,
        value: str,
    ) -> str:
        message = value.strip()

        if not message:
            raise ValueError(
                "message must not be blank"
            )

        return message

class AgentApprovalRequest(BaseModel):
    """批准或拒绝待执行的工具。"""

    model_config = ConfigDict(
        extra="forbid",
    )

    approved: bool

class AgentRunResponse(BaseModel):
    """一次 Agent 运行的对外响应。"""

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )

    run_id: str
    status: AgentStatus
    step_count: int = Field(ge=0)

    tool_calls: list[ToolCall] = Field(
        default_factory=list,
    )
    pending_tool_calls: list[ToolCall] = Field(
        default_factory=list,
    )
    tool_results: list[dict[str, Any]] = Field(
        default_factory=list,
    )

    final_answer: str | None = None
    error: str | None = None