import pytest
from pydantic import ValidationError

from app.agent.messages import ModelResponse


def test_model_response_parses_tool_call() -> None:
    response = ModelResponse.model_validate(
        {
            "model": "fake-model",
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
                                '{"content":"系统应尽快响应"}'
                            ),
                        },
                    }
                ],
            },
        }
    )

    tool_call = response.message.tool_calls[0]

    assert response.finish_reason == "tool_calls"
    assert tool_call.id == "call_001"
    assert tool_call.function.name == "ambiguity_check"
    assert (
        tool_call.function.arguments
        == '{"content":"系统应尽快响应"}'
    )


def test_model_response_supports_final_answer() -> None:
    response = ModelResponse.model_validate(
        {
            "finish_reason": "stop",
            "message": {
                "role": "assistant",
                "content": "需求分析已经完成。",
            },
        }
    )

    assert response.finish_reason == "stop"
    assert response.message.content == "需求分析已经完成。"
    assert response.message.tool_calls == []


def test_tool_call_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ModelResponse.model_validate(
            {
                "message": {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": "call_001",
                            "type": "function",
                            "function": {
                                "name": "ambiguity_check",
                                "arguments": "{}",
                                "unexpected": True,
                            },
                        }
                    ],
                },
            }
        )