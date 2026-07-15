import pytest
from fastapi.testclient import TestClient

import app.main as main_module


client = TestClient(main_module.app)


@pytest.fixture(autouse=True)
def reset_in_memory_store() -> None:
    """每个测试开始前清空内存数据，避免测试之间相互影响。"""
    main_module.requirements.clear()
    main_module.next_requirement_id = 1


def create_sample_requirement() -> dict:
    """创建一条供其他测试使用的示例需求。"""
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
        params={"priority": 2},
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
        params={"priority": 10},
    )

    assert response.status_code == 422