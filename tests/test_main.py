import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import RequirementAnalysis


TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
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


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_test_database() -> None:
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)


def create_sample_requirement() -> dict:
    payload = {
        "title": "用户登录需求",
        "content": "用户输入正确账号密码后，系统返回访问令牌",
        "priority": 1,
    }

    response = client.post(
        "/requirements",
        json=payload,
    )

    assert response.status_code == 201
    return response.json()


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "reqflow-agent",
        "environment": "development",
    }


def test_create_and_list_requirement() -> None:
    payload = {
        "title": "用户登录需求",
        "content": "用户输入正确账号密码后，系统返回访问令牌",
        "priority": 1,
    }

    create_response = client.post(
        "/requirements",
        json=payload,
    )

    assert create_response.status_code == 201
    assert create_response.json() == {
        "id": 1,
        **payload,
    }

    list_response = client.get("/requirements")

    assert list_response.status_code == 200
    assert list_response.json() == [
        {
            "id": 1,
            **payload,
        }
    ]


def test_create_requirement_with_invalid_priority() -> None:
    response = client.post(
        "/requirements",
        json={
            "title": "用户登录需求",
            "content": "测试内容",
            "priority": 10,
        },
    )

    assert response.status_code == 422


def test_get_requirement_by_id() -> None:
    created_requirement = create_sample_requirement()

    response = client.get(
        f"/requirements/{created_requirement['id']}"
    )

    assert response.status_code == 200
    assert response.json() == created_requirement


def test_get_missing_requirement_returns_404() -> None:
    response = client.get("/requirements/999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Requirement not found",
    }


def test_update_requirement() -> None:
    create_sample_requirement()

    response = client.patch(
        "/requirements/1",
        json={
            "priority": 2,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "title": "用户登录需求",
        "content": "用户输入正确账号密码后，系统返回访问令牌",
        "priority": 2,
    }


def test_delete_requirement() -> None:
    create_sample_requirement()

    delete_response = client.delete("/requirements/1")

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    get_response = client.get("/requirements/1")

    assert get_response.status_code == 404
    assert get_response.json() == {
        "detail": "Requirement not found",
    }

    list_response = client.get("/requirements")

    assert list_response.status_code == 200
    assert list_response.json() == []


def test_list_requirements_filtered_by_priority() -> None:
    client.post(
        "/requirements",
        json={
            "title": "登录需求",
            "content": "正确账号密码登录",
            "priority": 1,
        },
    )

    client.post(
        "/requirements",
        json={
            "title": "密码锁定需求",
            "content": "连续输错密码后锁定账号",
            "priority": 2,
        },
    )

    response = client.get(
        "/requirements",
        params={
            "priority": 2,
        },
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 2,
            "title": "密码锁定需求",
            "content": "连续输错密码后锁定账号",
            "priority": 2,
        }
    ]


def test_list_requirements_with_invalid_priority() -> None:
    response = client.get(
        "/requirements",
        params={
            "priority": 10,
        },
    )

    assert response.status_code == 422

def test_list_requirements_with_pagination() -> None:
    for index in range(1, 4):
        response = client.post(
            "/requirements",
            json={
                "title": f"需求{index}",
                "content": f"需求内容{index}",
                "priority": 1,
            },
        )

        assert response.status_code == 201

    response = client.get(
        "/requirements",
        params={
            "limit": 1,
            "offset": 1,
        },
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 2,
            "title": "需求2",
            "content": "需求内容2",
            "priority": 1,
        }
    ]


def test_list_requirements_with_invalid_pagination() -> None:
    invalid_limit_response = client.get(
        "/requirements",
        params={
            "limit": 0,
        },
    )

    assert invalid_limit_response.status_code == 422

    invalid_offset_response = client.get(
        "/requirements",
        params={
            "offset": -1,
        },
    )

    assert invalid_offset_response.status_code == 422

def test_analyze_requirement_endpoint() -> None:
    create_response = client.post(
        "/requirements",
        json={
            "title": "登录故障",
            "content": "用户无法登录系统",
            "priority": 3,
        },
    )

    assert create_response.status_code == 201

    requirement_id = create_response.json()["id"]

    analyze_response = client.post(
        f"/requirements/{requirement_id}/analyze"
    )

    assert analyze_response.status_code == 200

    result = analyze_response.json()

    assert result["passed"] is False
    assert result["current_priority"] == 3
    assert result["suggested_priority"] == 1
    assert result["priority_consistent"] is False
    assert (
        "当前优先级为 3，建议优先级为 1"
        in result["issues"]
    )

    assert result["tool_results"]["priority"][
        "matched_keywords"
    ] == [
        "故障",
        "无法登录",
    ]


def test_analyze_missing_requirement_returns_404() -> None:
    response = client.post(
        "/requirements/999/analyze"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Requirement not found",
    }

def test_analyze_requirement_is_persisted() -> None:
    requirement = create_sample_requirement()
    requirement_id = requirement["id"]

    analyze_response = client.post(
        f"/requirements/{requirement_id}/analyze"
    )

    assert analyze_response.status_code == 200

    response_data = analyze_response.json()

    with TestingSessionLocal() as db:
        analysis_records = list(
            db.scalars(
                select(RequirementAnalysis)
            ).all()
        )

    assert len(analysis_records) == 1

    saved_analysis = analysis_records[0]

    assert saved_analysis.requirement_id == requirement_id
    assert saved_analysis.passed == response_data["passed"]

    assert saved_analysis.planned_tools == (
        response_data["planned_tools"]
    )

    assert saved_analysis.final_report == (
        response_data["final_report"]
    )

    assert saved_analysis.llm_fallback_used == (
        response_data["llm_fallback_used"]
    )

def test_list_requirement_analysis_history() -> None:
    requirement = create_sample_requirement()
    requirement_id = requirement["id"]

    first_response = client.post(
        f"/requirements/{requirement_id}/analyze"
    )

    update_response = client.patch(
        f"/requirements/{requirement_id}",
        json={
            "content": (
                "用户输入正确账号密码后，"
                "系统必须在2秒内返回访问令牌"
            ),
        },
    )

    second_response = client.post(
        f"/requirements/{requirement_id}/analyze"
    )

    assert first_response.status_code == 200
    assert update_response.status_code == 200
    assert second_response.status_code == 200

    assert first_response.json()["cache_hit"] is False
    assert second_response.json()["cache_hit"] is False
    history_response = client.get(
        f"/requirements/{requirement_id}/analyses"
    )

    assert history_response.status_code == 200

    records = history_response.json()

    assert len(records) == 2

    assert records[0]["id"] == 2
    assert records[1]["id"] == 1

    assert records[0]["requirement_id"] == (
        requirement_id
    )

    assert records[0]["final_report"]
    assert records[0]["created_at"]


def test_list_missing_requirement_analyses_returns_404() -> None:
    response = client.get(
        "/requirements/999/analyses"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Requirement not found",
    }

def test_analyze_requirement_uses_cache_when_unchanged() -> None:
    requirement = create_sample_requirement()
    requirement_id = requirement["id"]

    first_response = client.post(
        f"/requirements/{requirement_id}/analyze"
    )

    second_response = client.post(
        f"/requirements/{requirement_id}/analyze"
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_result = first_response.json()
    second_result = second_response.json()

    assert first_result["cache_hit"] is False
    assert second_result["cache_hit"] is True

    assert second_result["final_report"] == (
        first_result["final_report"]
    )

    assert second_result["planned_tools"] == (
        first_result["planned_tools"]
    )

    with TestingSessionLocal() as db:
        analysis_records = list(
            db.scalars(
                select(RequirementAnalysis)
            ).all()
        )

    # 第二次请求使用缓存，不新增历史记录。
    assert len(analysis_records) == 1

def test_analyze_requirement_can_force_refresh() -> None:
    requirement = create_sample_requirement()
    requirement_id = requirement["id"]

    first_response = client.post(
        f"/requirements/{requirement_id}/analyze"
    )

    cached_response = client.post(
        f"/requirements/{requirement_id}/analyze"
    )

    forced_response = client.post(
        f"/requirements/{requirement_id}/analyze",
        params={
            "force_refresh": True,
        },
    )

    cached_again_response = client.post(
        f"/requirements/{requirement_id}/analyze"
    )

    assert first_response.status_code == 200
    assert cached_response.status_code == 200
    assert forced_response.status_code == 200
    assert cached_again_response.status_code == 200

    assert first_response.json()["cache_hit"] is False
    assert cached_response.json()["cache_hit"] is True

    # 强制刷新跳过缓存，重新执行分析。
    assert forced_response.json()["cache_hit"] is False

    # 强制刷新产生的新结果成为最新缓存。
    assert cached_again_response.json()["cache_hit"] is True

    with TestingSessionLocal() as db:
        analysis_records = list(
            db.scalars(
                select(RequirementAnalysis)
            ).all()
        )

    # 第一次分析和强制刷新各保存一条记录。
    assert len(analysis_records) == 2