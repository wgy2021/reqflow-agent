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

def test_openai_compatible_client_parses_json_code_fence() -> None:
    def handle_request(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": (
                                "```json\n"
                                '{"planned_tools":['
                                '"completeness_check",'
                                '"ambiguity_check"'
                                "]}\n"
                                "```"
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
        title="优化提示信息",
        content="系统应尽快返回提示信息",
        priority=3,
        available_tools=AVAILABLE_TOOLS,
    )

    assert result == [
        "completeness_check",
        "ambiguity_check",
    ]


def test_openai_compatible_client_handles_http_error() -> None:
    def handle_request(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            status_code=401,
            json={
                "error": "Unauthorized",
            },
        )

    client = OpenAICompatibleLLMClient(
        api_key="invalid-key",
        base_url="https://example.com/v1",
        model="test-model",
        transport=httpx.MockTransport(
            handle_request
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="LLM request failed with status 401",
    ):
        client.plan_tools(
            title="测试需求",
            content="测试内容",
            priority=3,
            available_tools=AVAILABLE_TOOLS,
        )


def test_openai_compatible_client_handles_network_error() -> None:
    def handle_request(
        request: httpx.Request,
    ) -> httpx.Response:
        raise httpx.ConnectError(
            "Connection failed",
            request=request,
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
        RuntimeError,
        match="LLM request failed",
    ):
        client.plan_tools(
            title="测试需求",
            content="测试内容",
            priority=3,
            available_tools=AVAILABLE_TOOLS,
        )

def test_openai_compatible_client_generates_report() -> None:
    def handle_request(
        request: httpx.Request,
    ) -> httpx.Response:
        assert str(request.url) == (
            "https://example.com/v1/chat/completions"
        )

        request_data = json.loads(
            request.content
        )

        assert request_data["model"] == "test-model"
        assert request_data["temperature"] == 0

        user_content = json.loads(
            request_data["messages"][1]["content"]
        )

        assert user_content["requirement"]["title"] == (
            "登录故障"
        )

        assert user_content["passed"] is False

        return httpx.Response(
            status_code=200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": (
                                "该需求未通过检查。"
                                "需求中包含“尽快”等模糊表达，"
                                "建议补充明确的处理时限。"
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

    report = client.generate_report(
        title="登录故障",
        content="系统应尽快解决用户无法登录的问题",
        priority=3,
        planned_tools=[
            "completeness_check",
            "ambiguity_check",
        ],
        tool_results={
            "completeness": {
                "passed": True,
                "missing_fields": [],
            },
            "ambiguity": {
                "passed": False,
                "matched_terms": ["尽快"],
            },
        },
        issues=[
            "包含模糊表达：尽快",
        ],
        passed=False,
    )

    assert report == (
        "该需求未通过检查。"
        "需求中包含“尽快”等模糊表达，"
        "建议补充明确的处理时限。"
    )


def test_openai_compatible_client_generates_tool_call() -> None:
    function_tools = [
        {
            "type": "function",
            "function": {
                "name": "ambiguity_check",
                "description": "检测需求中的模糊表达",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                        }
                    },
                    "required": ["content"],
                },
            },
        }
    ]

    def handle_request(
        request: httpx.Request,
    ) -> httpx.Response:
        request_data = json.loads(request.content)

        assert request_data["model"] == "test-model"
        assert request_data["tool_choice"] == "auto"
        assert request_data["tools"] == function_tools
        assert request_data["messages"] == [
            {
                "role": "user",
                "content": "检查需求是否清晰",
            }
        ]

        return httpx.Response(
            status_code=200,
            json={
                "model": "test-model",
                "choices": [
                    {
                        "finish_reason": "tool_calls",
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_001",
                                    "type": "function",
                                    "function": {
                                        "name": "ambiguity_check",
                                        "arguments": (
                                            '{"content":'
                                            '"系统应尽快响应"}'
                                        ),
                                    },
                                }
                            ],
                        },
                    }
                ],
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

    response = client.generate_response(
        messages=[
            {
                "role": "user",
                "content": "检查需求是否清晰",
            }
        ],
        tools=function_tools,
    )

    assert response.finish_reason == "tool_calls"
    assert response.model == "test-model"
    assert response.message.content is None
    assert len(response.message.tool_calls) == 1
    assert (
        response.message.tool_calls[0].function.name
        == "ambiguity_check"
    )

def test_openai_compatible_client_generates_final_answer() -> None:
    def handle_request(
        request: httpx.Request,
    ) -> httpx.Response:
        request_data = json.loads(request.content)

        assert request_data["messages"] == [
            {
                "role": "user",
                "content": "分析这个需求",
            }
        ]
        assert "tools" not in request_data
        assert "tool_choice" not in request_data

        return httpx.Response(
            status_code=200,
            json={
                "model": "test-model",
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant",
                            "content": "需求分析已经完成。",
                        },
                    }
                ],
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

    response = client.generate_response(
        messages=[
            {
                "role": "user",
                "content": "分析这个需求",
            }
        ],
        tools=[],
    )

    assert response.finish_reason == "stop"
    assert response.model == "test-model"
    assert response.message.content == "需求分析已经完成。"
    assert response.message.tool_calls == []