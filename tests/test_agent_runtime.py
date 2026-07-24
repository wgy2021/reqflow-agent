from app.agent.llm import FakeLLMClient
from app.agent.messages import ModelResponse
from app.agent.runtime import AgentRuntime
import app.agent.tools  # noqa: F401
from app.agent.registry import list_function_tools

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

def test_agent_runtime_executes_tool_call() -> None:
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
        scripted_responses=[tool_response],
    )
    runtime = AgentRuntime(
        llm_client=client,
    )

    state = runtime.run(
        user_message="检查需求完整性",
        tools=list_function_tools(),
    )

    assert state.status == "running"
    assert state.step_count == 1
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