from collections.abc import Callable
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


ToolHandler = Callable[..., dict[str, Any]]


class ToolSpec(BaseModel):
    """描述一个可由 Agent 调用的工具。"""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    name: str
    version: str = "1.0.0"
    description: str
    input_model: type[BaseModel]
    output_model: type[BaseModel]
    timeout_seconds: float = Field(default=10.0, gt=0)
    max_retries: int = Field(default=0, ge=0)
    risk_level: Literal["low", "medium", "high"] = "low"
    requires_approval: bool = False
    is_idempotent: bool = True
    handler: ToolHandler
    def to_function_tool(self) -> dict[str, Any]:
        """转换为 OpenAI-compatible Function Calling 工具定义。"""

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_model.model_json_schema(),
            },
        }