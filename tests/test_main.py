import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import (
    RequirementAnalysis,
    RequirementAnalysisCache,
)


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

def test_list_requirement_analysis_history_supports_pagination() -> None:
    requirement = create_sample_requirement()
    requirement_id = requirement["id"]

    first_response = client.post(
        f"/requirements/{requirement_id}/analyze"
    )

    second_response = client.post(
        f"/requirements/{requirement_id}/analyze",
        params={"force_refresh": True},
    )

    third_response = client.post(
        f"/requirements/{requirement_id}/analyze",
        params={"force_refresh": True},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert third_response.status_code == 200

    full_history_response = client.get(
        f"/requirements/{requirement_id}/analyses"
    )

    paginated_response = client.get(
        f"/requirements/{requirement_id}/analyses",
        params={
            "limit": 1,
            "offset": 1,
        },
    )

    assert full_history_response.status_code == 200
    assert paginated_response.status_code == 200

    full_history = full_history_response.json()
    paginated_history = paginated_response.json()

    assert len(full_history) == 3
    assert len(paginated_history) == 1

    # 跳过最新一条后，返回第二新的记录。
    assert paginated_history[0]["id"] == (
        full_history[1]["id"]
    )

def test_delete_requirement_removes_analysis_data() -> None:
    requirement = create_sample_requirement()
    requirement_id = requirement["id"]

    analyze_response = client.post(
        f"/requirements/{requirement_id}/analyze"
    )

    assert analyze_response.status_code == 200

    # 先确认分析历史和缓存确实已经创建。
    with TestingSessionLocal() as db:
        analysis_records_before_delete = list(
            db.scalars(
                select(RequirementAnalysis).where(
                    RequirementAnalysis.requirement_id
                    == requirement_id
                )
            ).all()
        )

        cache_before_delete = db.get(
            RequirementAnalysisCache,
            requirement_id,
        )

    assert len(analysis_records_before_delete) == 1
    assert cache_before_delete is not None

    delete_response = client.delete(
        f"/requirements/{requirement_id}"
    )

    assert delete_response.status_code == 204

    # 删除需求后，关联的分析历史和缓存也必须消失。
    with TestingSessionLocal() as db:
        analysis_records_after_delete = list(
            db.scalars(
                select(RequirementAnalysis).where(
                    RequirementAnalysis.requirement_id
                    == requirement_id
                )
            ).all()
        )

        cache_after_delete = db.get(
            RequirementAnalysisCache,
            requirement_id,
        )

    assert analysis_records_after_delete == []
    assert cache_after_delete is None

def test_rag_context_change_invalidates_analysis_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requirement = create_sample_requirement()
    requirement_id = requirement["id"]

    current_context = {
        "value": "知识上下文 A",
    }

    monkeypatch.setattr(
        (
            "app.routers.requirements."
            "rag_service.retrieve_requirement_context"
        ),
        lambda **kwargs: [],
    )

    monkeypatch.setattr(
        (
            "app.routers.requirements."
            "rag_service.format_knowledge_context"
        ),
        lambda results: current_context["value"],
    )

    def fake_analyze_requirement(
        title: str,
        content: str,
        priority: int | None,
        knowledge_context: str = "",
    ) -> dict:
        return {
            "passed": True,
            "planned_tools": [
                "completeness_check",
            ],
            "current_priority": priority,
            "suggested_priority": None,
            "priority_consistent": None,
            "issues": [],
            "tool_results": {},
            "final_report": (
                f"使用知识上下文：{knowledge_context}"
            ),
            "llm_fallback_used": False,
            "llm_error": None,
        }

    monkeypatch.setattr(
        (
            "app.routers.requirements."
            "analyze_requirement"
        ),
        fake_analyze_requirement,
    )

    first_response = client.post(
        f"/requirements/{requirement_id}/analyze"
    )

    second_response = client.post(
        f"/requirements/{requirement_id}/analyze"
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    assert first_response.json()["cache_hit"] is False
    assert second_response.json()["cache_hit"] is True

    assert first_response.json()["final_report"] == (
        "使用知识上下文：知识上下文 A"
    )

    current_context["value"] = "知识上下文 B"

    third_response = client.post(
        f"/requirements/{requirement_id}/analyze"
    )

    assert third_response.status_code == 200
    assert third_response.json()["cache_hit"] is False

    assert third_response.json()["final_report"] == (
        "使用知识上下文：知识上下文 B"
    )

def test_analysis_returns_and_persists_knowledge_references(
) -> None:
    document_response = client.post(
        "/knowledge/documents",
        json={
            "title": "登录安全规范",
            "content": (
                "用户登录必须校验用户名和密码，"
                "密码必须使用哈希算法加盐保存。"
            ),
            "source": "rag-test.md",
        },
    )

    assert document_response.status_code == 201

    requirement_response = client.post(
        "/requirements",
        json={
            "title": "用户登录安全控制",
            "content": (
                "用户登录必须校验用户名和密码，"
                "密码必须使用哈希算法加盐保存。"
            ),
            "priority": 1,
        },
    )

    assert requirement_response.status_code == 201

    requirement_id = requirement_response.json()["id"]

    first_response = client.post(
        (
            f"/requirements/{requirement_id}/analyze"
            "?force_refresh=true"
        )
    )

    assert first_response.status_code == 200

    first_result = first_response.json()
    references = first_result[
        "knowledge_references"
    ]

    assert first_result["cache_hit"] is False
    assert len(references) == 1

    assert references[0]["document_title"] == (
        "登录安全规范"
    )
    assert references[0]["source"] == "rag-test.md"
    assert references[0]["score"] > 0

    cached_response = client.post(
        f"/requirements/{requirement_id}/analyze"
    )

    assert cached_response.status_code == 200
    assert cached_response.json()["cache_hit"] is True

    assert (
        cached_response.json()["knowledge_references"]
        == references
    )

    history_response = client.get(
        f"/requirements/{requirement_id}/analyses"
    )

    assert history_response.status_code == 200

    history = history_response.json()

    assert len(history) == 1
    assert history[0]["knowledge_references"] == (
        references
    )