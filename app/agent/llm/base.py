from abc import ABC, abstractmethod


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