import json
from typing import Any

import httpx

from app.agent.llm.base import LLMClient


class OpenAICompatibleLLMClient(LLMClient):
    """调用 OpenAI-compatible Chat Completions 接口规划工具。"""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        api_key = api_key.strip()
        base_url = base_url.strip()
        model = model.strip()

        if not api_key:
            raise ValueError(
                "LLM API key is required"
            )

        if not base_url:
            raise ValueError(
                "LLM base URL is required"
            )

        if not model:
            raise ValueError(
                "LLM model is required"
            )

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

        # 测试时传入 MockTransport，避免真实网络请求。
        self.transport = transport

    def plan_tools(
        self,
        title: str,
        content: str,
        priority: int | None,
        available_tools: list[dict[str, str]],
    ) -> list[str]:
        request_payload = self._build_request_payload(
            title=title,
            content=content,
            priority=priority,
            available_tools=available_tools,
        )

        with httpx.Client(
            timeout=self.timeout,
            transport=self.transport,
        ) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": (
                        f"Bearer {self.api_key}"
                    ),
                    "Content-Type": "application/json",
                },
                json=request_payload,
            )

        response.raise_for_status()

        return self._parse_planned_tools(
            response=response,
        )

    def _build_request_payload(
        self,
        title: str,
        content: str,
        priority: int | None,
        available_tools: list[dict[str, str]],
    ) -> dict[str, Any]:
        requirement_data = {
            "title": title,
            "content": content,
            "priority": priority,
            "available_tools": available_tools,
        }

        return {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是需求分析工具规划器。"
                        "请根据需求内容选择必要的工具。"
                        "只能从 available_tools 中选择工具。"
                        "只返回一个 JSON 对象，格式为："
                        '{"planned_tools":["工具名称"]}'
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        requirement_data,
                        ensure_ascii=False,
                    ),
                },
            ],
        }

    @staticmethod
    def _parse_planned_tools(
        response: httpx.Response,
    ) -> list[str]:
        try:
            response_data = response.json()

            message_content = response_data[
                "choices"
            ][0]["message"]["content"]

            parsed_content = json.loads(
                message_content
            )
        except (
            ValueError,
            KeyError,
            IndexError,
            TypeError,
        ) as exc:
            raise ValueError(
                "Invalid LLM response structure or JSON"
            ) from exc

        planned_tools = parsed_content.get(
            "planned_tools"
        )

        if not isinstance(planned_tools, list):
            raise ValueError(
                "LLM response planned_tools must be a list"
            )

        if not all(
            isinstance(tool_name, str)
            and tool_name.strip()
            for tool_name in planned_tools
        ):
            raise ValueError(
                "Every planned tool must be a non-empty string"
            )

        # 去重，同时保留模型给出的原始顺序。
        return list(
            dict.fromkeys(planned_tools)
        )