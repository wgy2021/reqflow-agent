from fastapi.testclient import TestClient

from app.agent.llm import FakeLLMClient
from app.agent.messages import ModelResponse
from app.main import app
from app.routers.agent import provide_llm_client
import pytest

from app.agent.run_store import agent_run_store

client = TestClient(app)
@pytest.fixture(autouse=True)
def reset_agent_run_store() -> None:
    agent_run_store.clear()

def test_create_agent_run_returns_completed_state() -> None:
    final_response = ModelResponse.model_validate(
        {
            "finish_reason": "stop",
            "message": {
                "role": "assistant",
                "content": "需求分析完成。",
            },
        }
    )

    app.dependency_overrides[
        provide_llm_client
    ] = lambda: FakeLLMClient(
        scripted_responses=[final_response],
    )

    try:
        response = client.post(
            "/agent/runs",
            json={
                "message": "请分析这个需求",
                "max_steps": 3,
            },
        )
    finally:
        app.dependency_overrides.pop(
            provide_llm_client,
            None,
        )

    assert response.status_code == 201

    response_data = response.json()

    assert response_data["run_id"]
    assert response_data["status"] == "completed"
    assert response_data["step_count"] == 1
    assert (
        response_data["final_answer"]
        == "需求分析完成。"
    )
    assert response_data["tool_calls"] == []
    assert response_data["pending_tool_calls"] == []
    assert response_data["tool_results"] == []
    assert response_data["error"] is None
    assert "messages" not in response_data

def test_get_agent_run_returns_saved_state() -> None:
    final_response = ModelResponse.model_validate(
        {
            "finish_reason": "stop",
            "message": {
                "role": "assistant",
                "content": "查询测试完成。",
            },
        }
    )

    app.dependency_overrides[
        provide_llm_client
    ] = lambda: FakeLLMClient(
        scripted_responses=[final_response],
    )

    try:
        create_response = client.post(
            "/agent/runs",
            json={
                "message": "执行查询测试",
            },
        )
    finally:
        app.dependency_overrides.pop(
            provide_llm_client,
            None,
        )

    run_id = create_response.json()["run_id"]

    get_response = client.get(
        f"/agent/runs/{run_id}"
    )

    assert get_response.status_code == 200
    assert get_response.json() == create_response.json()


def test_get_missing_agent_run_returns_404() -> None:
    response = client.get(
        "/agent/runs/missing-run"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Agent run not found",
    }