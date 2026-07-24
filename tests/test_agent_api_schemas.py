import pytest
from pydantic import ValidationError

from app.agent.api_schemas import (
    AgentRunRequest,
    AgentRunResponse,
)
from app.agent.state import AgentState


def test_agent_run_request_has_defaults() -> None:
    request = AgentRunRequest(
        message="  检查需求完整性  ",
    )

    assert request.message == "检查需求完整性"
    assert request.max_steps == 5


def test_agent_run_request_rejects_blank_message() -> None:
    with pytest.raises(ValidationError):
        AgentRunRequest(
            message="   ",
        )


def test_agent_run_response_accepts_agent_state() -> None:
    state = AgentState(
        status="completed",
        step_count=2,
        final_answer="需求分析完成。",
    )

    response = AgentRunResponse.model_validate(
        state
    )

    assert response.run_id == state.run_id
    assert response.status == "completed"
    assert response.step_count == 2
    assert response.final_answer == "需求分析完成。"
    assert response.tool_calls == []
    assert response.pending_tool_calls == []
    assert response.tool_results == []
    assert response.error is None