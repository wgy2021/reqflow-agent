from abc import ABC, abstractmethod
from typing import Any


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