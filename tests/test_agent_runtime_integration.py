import json

import httpx
import app.agent.tools  # noqa: F401

from app.agent.llm import OpenAICompatibleLLMClient
from app.agent.registry import list_function_tools
from app.agent.runtime import AgentRuntime


def test_runtime_completes_with_openai_compatible_client() -> None:
    request_count = 0

    def handle_request(
        request: httpx.Request,
    ) -> httpx.Response:
        nonlocal request_count
        request_count += 1

        request_data = json.loads(request.content)

        assert request_data["model"] == "test-model"
        assert request_data["tools"] == list_function_tools()

        if request_count == 1:
            assert request_data["messages"] == [
                {
                    "role": "user",
                    "content": "检查需求完整性",
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
                                            "name": "completeness_check",
                                            "arguments": (
                                                '{"title":"用户登录",'
                                                '"content":"用户可以登录系统",'
                                                '"priority":1}'
                                            ),
                                        },
                                    }
                                ],
                            },
                        }
                    ],
                },
            )

        assert request_count == 2
        assert request_data["messages"][-1]["role"] == "tool"
        assert (
            request_data["messages"][-1]["tool_call_id"]
            == "call_001"
        )

        return httpx.Response(
            status_code=200,
            json={
                "model": "test-model",
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant",
                            "content": "需求完整性检查通过。",
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

    runtime = AgentRuntime(
        llm_client=client,
    )

    state = runtime.run(
        user_message="检查需求完整性",
        tools=list_function_tools(),
    )

    assert request_count == 2
    assert state.status == "completed"
    assert state.step_count == 2
    assert state.final_answer == "需求完整性检查通过。"
    assert len(state.tool_calls) == 1
    assert len(state.tool_results) == 1
    assert (
        state.tool_results[0]["tool_name"]
        == "completeness_check"
    )