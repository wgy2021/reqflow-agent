from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.agent.llm import FakeLLMClient
from app.agent.messages import ModelResponse
from app.agent.run_store import agent_run_store
from app.main import app
from app.routers.agent import provide_llm_client


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


def test_approve_agent_run_executes_tool_and_completes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
                "content": "审批工具执行完成。",
            },
        }
    )

    fake_client = FakeLLMClient(
        scripted_responses=[
            tool_response,
            final_response,
        ],
    )

    monkeypatch.setattr(
        "app.agent.runtime.get_tool_spec",
        lambda name: SimpleNamespace(
            requires_approval=True,
        ),
    )

    app.dependency_overrides[
        provide_llm_client
    ] = lambda: fake_client

    try:
        create_response = client.post(
            "/agent/runs",
            json={
                "message": "执行完整性检查",
                "max_steps": 3,
            },
        )

        assert create_response.status_code == 201
        assert (
            create_response.json()["status"]
            == "waiting_approval"
        )

        run_id = create_response.json()["run_id"]

        approval_response = client.post(
            f"/agent/runs/{run_id}/approval",
            json={
                "approved": True,
            },
        )
    finally:
        app.dependency_overrides.pop(
            provide_llm_client,
            None,
        )

    assert approval_response.status_code == 200

    response_data = approval_response.json()

    assert response_data["status"] == "completed"
    assert response_data["step_count"] == 2
    assert response_data["pending_tool_calls"] == []
    assert len(response_data["tool_results"]) == 1
    assert (
        response_data["tool_results"][0]["tool_name"]
        == "completeness_check"
    )
    assert (
        response_data["final_answer"]
        == "审批工具执行完成。"
    )


def test_reject_agent_run_stops_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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

    fake_client = FakeLLMClient(
        scripted_responses=[tool_response],
    )

    monkeypatch.setattr(
        "app.agent.runtime.get_tool_spec",
        lambda name: SimpleNamespace(
            requires_approval=True,
        ),
    )

    app.dependency_overrides[
        provide_llm_client
    ] = lambda: fake_client

    try:
        create_response = client.post(
            "/agent/runs",
            json={
                "message": "执行完整性检查",
                "max_steps": 3,
            },
        )

        run_id = create_response.json()["run_id"]

        rejection_response = client.post(
            f"/agent/runs/{run_id}/approval",
            json={
                "approved": False,
            },
        )
    finally:
        app.dependency_overrides.pop(
            provide_llm_client,
            None,
        )

    assert rejection_response.status_code == 200

    response_data = rejection_response.json()

    assert response_data["status"] == "failed"
    assert response_data["step_count"] == 1
    assert response_data["pending_tool_calls"] == []
    assert response_data["tool_results"] == []
    assert response_data["final_answer"] is None
    assert (
        response_data["error"]
        == "Tool approval rejected"
    )


def test_approval_for_completed_run_returns_409() -> None:
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
        create_response = client.post(
            "/agent/runs",
            json={
                "message": "分析需求",
            },
        )

        run_id = create_response.json()["run_id"]

        approval_response = client.post(
            f"/agent/runs/{run_id}/approval",
            json={
                "approved": True,
            },
        )
    finally:
        app.dependency_overrides.pop(
            provide_llm_client,
            None,
        )

    assert approval_response.status_code == 409
    assert approval_response.json() == {
        "detail": (
            "Agent run is not waiting for approval"
        ),
    }


def test_list_agent_runs_returns_saved_runs() -> None:
    responses = [
        ModelResponse.model_validate(
            {
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "content": "第一次分析完成。",
                },
            }
        ),
        ModelResponse.model_validate(
            {
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "content": "第二次分析完成。",
                },
            }
        ),
    ]

    fake_client = FakeLLMClient(
        scripted_responses=responses,
    )

    app.dependency_overrides[
        provide_llm_client
    ] = lambda: fake_client

    try:
        first_response = client.post(
            "/agent/runs",
            json={
                "message": "第一次分析",
            },
        )

        second_response = client.post(
            "/agent/runs",
            json={
                "message": "第二次分析",
            },
        )
    finally:
        app.dependency_overrides.pop(
            provide_llm_client,
            None,
        )

    response = client.get("/agent/runs")

    assert response.status_code == 200

    response_data = response.json()

    assert len(response_data) == 2
    assert (
        response_data[0]["run_id"]
        == second_response.json()["run_id"]
    )
    assert (
        response_data[1]["run_id"]
        == first_response.json()["run_id"]
    )


def test_list_agent_runs_returns_empty_list() -> None:
    response = client.get("/agent/runs")

    assert response.status_code == 200
    assert response.json() == []