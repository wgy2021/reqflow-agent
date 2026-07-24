from app.agent.llm import FakeLLMClient
from app.agent.messages import ModelResponse
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