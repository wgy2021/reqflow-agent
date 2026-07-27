from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.agent.llm import FakeLLMClient
from app.agent.messages import ModelResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.agent.run_repository import AgentRunRepository
from app.database import Base
from app.routers.agent import (
    provide_llm_client,
    provide_run_repository,
)
from app.main import app
from app.models import AgentRunRecord, Requirement

test_engine = create_engine(
    "sqlite://",
    connect_args={
        "check_same_thread": False,
    },
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    expire_on_commit=False,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def override_agent_run_repository():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    def provide_test_repository():
        with TestingSessionLocal() as db:
            yield AgentRunRepository(db)

    app.dependency_overrides[
        provide_run_repository
    ] = provide_test_repository

    yield

    app.dependency_overrides.pop(
        provide_run_repository,
        None,
    )


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

    assert response_data["total"] == 2
    assert response_data["limit"] == 20
    assert response_data["offset"] == 0

    items = response_data["items"]

    assert len(items) == 2
    assert (
        items[0]["run_id"]
        == second_response.json()["run_id"]
    )
    assert (
        items[1]["run_id"]
        == first_response.json()["run_id"]
    )

    paged_response = client.get(
        "/agent/runs",
        params={
            "limit": 1,
            "offset": 1,
        },
    )

    assert paged_response.status_code == 200

    paged_data = paged_response.json()

    assert paged_data["total"] == 2
    assert paged_data["limit"] == 1
    assert paged_data["offset"] == 1

    paged_items = paged_data["items"]

    assert len(paged_items) == 1
    assert (
        paged_items[0]["run_id"]
        == first_response.json()["run_id"]
    )


def test_list_agent_runs_returns_empty_list() -> None:
    response = client.get("/agent/runs")

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "total": 0,
        "limit": 20,
        "offset": 0,
    }


def test_create_agent_run_saves_requirement_id() -> None:
    with TestingSessionLocal() as db:
        requirement = Requirement(
            title="用户登录",
            content="用户可以登录系统",
            priority=1,
        )
        db.add(requirement)
        db.commit()
        db.refresh(requirement)
        requirement_id = requirement.id

    final_response = ModelResponse.model_validate(
        {
            "finish_reason": "stop",
            "message": {
                "role": "assistant",
                "content": "关联测试完成。",
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
                "message": "分析指定需求",
                "requirement_id": requirement_id,
            },
        )
    finally:
        app.dependency_overrides.pop(
            provide_llm_client,
            None,
        )

    assert response.status_code == 201

    run_id = response.json()["run_id"]

    with TestingSessionLocal() as db:
        record = db.get(AgentRunRecord, run_id)

        assert record is not None
        assert record.requirement_id == requirement_id


def test_list_agent_runs_filters_by_requirement_id() -> None:
    with TestingSessionLocal() as db:
        first_requirement = Requirement(
            title="需求一",
            content="需求一的内容",
            priority=1,
        )
        second_requirement = Requirement(
            title="需求二",
            content="需求二的内容",
            priority=2,
        )

        db.add_all(
            [
                first_requirement,
                second_requirement,
            ]
        )
        db.commit()
        db.refresh(first_requirement)
        db.refresh(second_requirement)

        first_requirement_id = first_requirement.id
        second_requirement_id = second_requirement.id

    responses = [
        ModelResponse.model_validate(
            {
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "content": "需求一第一次运行",
                },
            }
        ),
        ModelResponse.model_validate(
            {
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "content": "需求二运行",
                },
            }
        ),
        ModelResponse.model_validate(
            {
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "content": "需求一第二次运行",
                },
            }
        ),
    ]

    app.dependency_overrides[
        provide_llm_client
    ] = lambda: FakeLLMClient(
        scripted_responses=responses,
    )

    try:
        first_response = client.post(
            "/agent/runs",
            json={
                "message": "需求一第一次分析",
                "requirement_id": first_requirement_id,
            },
        )
        other_response = client.post(
            "/agent/runs",
            json={
                "message": "需求二分析",
                "requirement_id": second_requirement_id,
            },
        )
        second_response = client.post(
            "/agent/runs",
            json={
                "message": "需求一第二次分析",
                "requirement_id": first_requirement_id,
            },
        )
    finally:
        app.dependency_overrides.pop(
            provide_llm_client,
            None,
        )

    response = client.get(
        "/agent/runs",
        params={
            "requirement_id": first_requirement_id,
        },
    )

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["total"] == 2
    assert response_data["limit"] == 20
    assert response_data["offset"] == 0

    items = response_data["items"]

    assert [
        item["run_id"]
        for item in items
    ] == [
        second_response.json()["run_id"],
        first_response.json()["run_id"],
    ]

    assert other_response.json()["run_id"] not in {
        item["run_id"]
        for item in items
    }

    paged_response = client.get(
        "/agent/runs",
        params={
            "requirement_id": first_requirement_id,
            "limit": 1,
            "offset": 1,
        },
    )

    assert paged_response.status_code == 200

    paged_data = paged_response.json()

    assert paged_data["total"] == 2
    assert paged_data["limit"] == 1
    assert paged_data["offset"] == 1

    paged_items = paged_data["items"]

    assert [
        item["run_id"]
        for item in paged_items
    ] == [
        first_response.json()["run_id"],
    ]