from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ToolCallFunction(BaseModel):
    """模型请求调用的函数信息。"""

    model_config = ConfigDict(
        extra="forbid",
    )

    name: str = Field(min_length=1)
    arguments: str


class ToolCall(BaseModel):
    """模型返回的一次工具调用。"""

    model_config = ConfigDict(
        extra="forbid",
    )

    id: str = Field(min_length=1)
    type: Literal["function"] = "function"
    function: ToolCallFunction


class AssistantMessage(BaseModel):
    """模型返回的 assistant 消息。"""

    model_config = ConfigDict(
        extra="forbid",
    )

    role: Literal["assistant"] = "assistant"
    content: str | None = None
    tool_calls: list[ToolCall] = Field(
        default_factory=list,
    )


class ModelResponse(BaseModel):
    """统一表示模型的一次响应。"""

    model_config = ConfigDict(
        extra="forbid",
    )

    message: AssistantMessage
    finish_reason: str | None = None
    model: str | None = None