import app.agent.tools  # noqa: F401

from app.agent.llm import FakeLLMClient
from app.agent.messages import ModelResponse
from app.agent.registry import list_function_tools
from app.agent.runtime import AgentRuntime


def test_agent_runtime_completes_with_final_answer() -> None:
    final_response = ModelResponse.model_validate(
        {
            "finish_reason": "stop",
            "message": {
                "role": "assistant",
                "content": "需求分析完成。",
            },
        }
    )

    client = FakeLLMClient(
        scripted_responses=[final_response],
    )
    runtime = AgentRuntime(
        llm_client=client,
    )

    state = runtime.run(
        user_message="请分析这个需求",
        tools=[],
    )

    assert state.status == "completed"
    assert state.step_count == 1
    assert state.final_answer == "需求分析完成。"
    assert state.messages[0]["role"] == "user"
    assert state.messages[1]["role"] == "assistant"
    assert state.tool_calls == []


def test_agent_runtime_executes_tool_and_completes() -> None:
    tool_response = ModelResponse.model_validate(
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
    )

    final_response = ModelResponse.model_validate(
        {
            "finish_reason": "stop",
            "message": {
                "role": "assistant",
                "content": "需求完整性检查已经完成。",
            },
        }
    )

    client = FakeLLMClient(
        scripted_responses=[
            tool_response,
            final_response,
        ],
    )
    runtime = AgentRuntime(
        llm_client=client,
    )

    state = runtime.run(
        user_message="检查需求完整性",
        tools=list_function_tools(),
    )

    assert state.status == "completed"
    assert state.step_count == 2
    assert (
        state.final_answer
        == "需求完整性检查已经完成。"
    )
    assert len(state.tool_calls) == 1

    assert state.tool_results == [
        {
            "tool_call_id": "call_001",
            "tool_name": "completeness_check",
            "result": {
                "tool": "completeness_check",
                "passed": True,
                "missing_fields": [],
            },
        }
    ]

    assert state.messages[2]["role"] == "tool"
    assert state.messages[2]["tool_call_id"] == "call_001"
    assert state.messages[3]["role"] == "assistant"

def test_agent_runtime_stops_at_max_steps() -> None:
    tool_response = ModelResponse.model_validate(
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
    )

    client = FakeLLMClient(
        scripted_responses=[
            tool_response,
            tool_response,
        ],
    )
    runtime = AgentRuntime(
        llm_client=client,
        max_steps=2,
    )

    state = runtime.run(
        user_message="持续检查需求",
        tools=list_function_tools(),
    )

    assert state.status == "max_steps_exceeded"
    assert state.step_count == 2
    assert state.final_answer is None
    assert state.error == "Agent exceeded maximum steps"
    assert len(state.tool_calls) == 2
    assert len(state.tool_results) == 2

def test_agent_runtime_fails_on_invalid_json_arguments() -> None:
    invalid_response = ModelResponse.model_validate(
        {
            "finish_reason": "tool_calls",
            "message": {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "call_invalid",
                        "type": "function",
                        "function": {
                            "name": "completeness_check",
                            "arguments": '{"title":',
                        },
                    }
                ],
            },
        }
    )

    client = FakeLLMClient(
        scripted_responses=[invalid_response],
    )
    runtime = AgentRuntime(
        llm_client=client,
    )

    state = runtime.run(
        user_message="检查这个需求",
        tools=list_function_tools(),
    )

    assert state.status == "failed"
    assert state.step_count == 1
    assert state.tool_results == []
    assert (
        state.error
        == "Invalid JSON arguments for tool: completeness_check"
    )

def test_agent_runtime_fails_on_unknown_tool() -> None:
    response = ModelResponse.model_validate(
        {
            "finish_reason": "tool_calls",
            "message": {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "call_unknown",
                        "type": "function",
                        "function": {
                            "name": "missing_tool",
                            "arguments": "{}",
                        },
                    }
                ],
            },
        }
    )

    client = FakeLLMClient(
        scripted_responses=[response],
    )
    runtime = AgentRuntime(llm_client=client)

    state = runtime.run(
        user_message="调用工具",
        tools=list_function_tools(),
    )

    assert state.status == "failed"
    assert state.error == "Unknown tool: missing_tool"
    assert state.tool_results == []


def test_agent_runtime_fails_on_schema_validation() -> None:
    response = ModelResponse.model_validate(
        {
            "finish_reason": "tool_calls",
            "message": {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "call_invalid_input",
                        "type": "function",
                        "function": {
                            "name": "completeness_check",
                            "arguments": (
                                '{"title":"登录",'
                                '"content":"用户登录",'
                                '"priority":99}'
                            ),
                        },
                    }
                ],
            },
        }
    )

    client = FakeLLMClient(
        scripted_responses=[response],
    )
    runtime = AgentRuntime(llm_client=client)

    state = runtime.run(
        user_message="检查需求",
        tools=list_function_tools(),
    )

    assert state.status == "failed"
    assert (
        state.error
        == "Invalid arguments for tool: completeness_check"
    )
    assert state.tool_results == []