import pytest
from fastapi.testclient import TestClient

import app.main as main_module


client = TestClient(main_module.app)


@pytest.fixture(autouse=True)
def reset_in_memory_store() -> None:
    """每个测试开始前清空内存数据，避免测试互相影响。"""
    main_module.requirements.clear()
    main_module.next_requirement_id = 1


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