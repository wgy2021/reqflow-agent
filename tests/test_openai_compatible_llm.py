import json

import httpx
import pytest

from app.agent.llm import (
    OpenAICompatibleLLMClient,
)


AVAILABLE_TOOLS = [
    {
        "name": "completeness_check",
        "description": "检查需求字段是否完整",
    },
    {
        "name": "ambiguity_check",
        "description": "检测模糊表达",
    },
    {
        "name": "priority_suggestion",
        "description": "建议需求优先级",
    },
]


def test_openai_compatible_client_plans_tools() -> None:
    def handle_request(
        request: httpx.Request,
    ) -> httpx.Response:
        assert str(request.url) == (
            "https://example.com/v1/chat/completions"
        )

        assert request.headers["Authorization"] == (
            "Bearer test-key"
        )

        request_data = json.loads(
            request.content
        )

        assert request_data["model"] == "test-model"
        assert request_data["temperature"] == 0

        return httpx.Response(
            status_code=200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "planned_tools": [
                                        "completeness_check",
                                        "ambiguity_check",
                                    ]
                                }
                            )
                        }
                    }
                ]
            },
        )

    client = OpenAICompatibleLLMClient(
        api_key="test-key",
        base_url="https://example.com/v1/",
        model="test-model",
        transport=httpx.MockTransport(
            handle_request
        ),
    )

    result = client.plan_tools(
        title="优化提示信息",
        content="系统应尽快返回友好的提示信息",
        priority=3,
        available_tools=AVAILABLE_TOOLS,
    )

    assert result == [
        "completeness_check",
        "ambiguity_check",
    ]


def test_openai_compatible_client_removes_duplicates() -> None:
    def handle_request(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "planned_tools": [
                                        "completeness_check",
                                        "completeness_check",
                                    ]
                                }
                            )
                        }
                    }
                ]
            },
        )

    client = OpenAICompatibleLLMClient(
        api_key="test-key",
        base_url="https://example.com/v1",
        model="test-model",
        transport=httpx.MockTransport(
            handle_request
        ),
    )

    result = client.plan_tools(
        title="测试需求",
        content="测试内容",
        priority=3,
        available_tools=AVAILABLE_TOOLS,
    )

    assert result == [
        "completeness_check",
    ]


def test_openai_compatible_client_rejects_invalid_response() -> None:
    def handle_request(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": "不是合法 JSON"
                        }
                    }
                ]
            },
        )

    client = OpenAICompatibleLLMClient(
        api_key="test-key",
        base_url="https://example.com/v1",
        model="test-model",
        transport=httpx.MockTransport(
            handle_request
        ),
    )

    with pytest.raises(
        ValueError,
        match="Invalid LLM response structure or JSON",
    ):
        client.plan_tools(
            title="测试需求",
            content="测试内容",
            priority=3,
            available_tools=AVAILABLE_TOOLS,
        )


def test_openai_compatible_client_requires_api_key() -> None:
    with pytest.raises(
        ValueError,
        match="LLM API key is required",
    ):
        OpenAICompatibleLLMClient(
            api_key="",
            base_url="https://example.com/v1",
            model="test-model",
        )