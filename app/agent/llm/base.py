from abc import ABC, abstractmethod
from typing import Any
from app.agent.messages import ModelResponse


class LLMClient(ABC):
    """所有大模型客户端都必须遵守的统一接口。"""

    @abstractmethod
    def plan_tools(
        self,
        title: str,
        content: str,
        priority: int | None,
        available_tools: list[dict[str, str]],
    ) -> list[str]:
        """根据需求和可用工具，返回准备调用的工具名称。"""

        raise NotImplementedError

    def generate_response(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> ModelResponse:
        """接收消息和工具定义，返回统一模型响应。"""

        raise NotImplementedError(
            "This LLM client does not support native tool calling"
        )

    def generate_report(
        self,
        title: str,
        content: str,
        priority: int | None,
        planned_tools: list[str],
        tool_results: dict[str, dict[str, Any]],
        issues: list[str],
        passed: bool,
    ) -> str:
        """根据需求和工具结果生成最终自然语言报告。"""

        raise NotImplementedError(
            "This LLM client does not support report generation"
        )