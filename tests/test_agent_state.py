import pytest
from pydantic import ValidationError

from app.agent.state import AgentState


def test_agent_state_has_safe_defaults() -> None:
    state = AgentState()

    assert state.run_id
    assert state.status == "running"
    assert state.step_count == 0
    assert state.messages == []
    assert state.tool_calls == []
    assert state.tool_results == []
    assert state.final_answer is None
    assert state.error is None


def test_agent_state_can_be_completed() -> None:
    state = AgentState(
        run_id="run_001",
        status="completed",
        step_count=2,
        final_answer="需求分析完成。",
    )

    assert state.run_id == "run_001"
    assert state.status == "completed"
    assert state.step_count == 2
    assert state.final_answer == "需求分析完成。"


def test_agent_state_rejects_negative_step_count() -> None:
    with pytest.raises(ValidationError):
        AgentState(
            step_count=-1,
        )