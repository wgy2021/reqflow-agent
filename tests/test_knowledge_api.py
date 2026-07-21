from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


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


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    previous_override = app.dependency_overrides.get(
        get_db
    )

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    if previous_override is None:
        app.dependency_overrides.pop(
            get_db,
            None,
        )
    else:
        app.dependency_overrides[get_db] = (
            previous_override
        )


def test_create_document_generates_chunks(
    client: TestClient,
) -> None:
    content = "A" * 600

    response = client.post(
        "/knowledge/documents",
        json={
            "title": "登录安全规范",
            "content": content,
            "source": "security-guide.md",
        },
    )

    assert response.status_code == 201

    document = response.json()

    assert document["id"] == 1
    assert document["title"] == "登录安全规范"
    assert document["content"] == content
    assert document["source"] == "security-guide.md"
    assert document["created_at"]

    chunks_response = client.get(
        "/knowledge/documents/1/chunks"
    )

    assert chunks_response.status_code == 200

    chunks = chunks_response.json()

    assert len(chunks) == 2
    assert [
        chunk["chunk_index"]
        for chunk in chunks
    ] == [
        0,
        1,
    ]

    assert len(chunks[0]["content"]) == 500
    assert len(chunks[1]["content"]) == 150


def test_list_and_get_documents(
    client: TestClient,
) -> None:
    client.post(
        "/knowledge/documents",
        json={
            "title": "第一份规范",
            "content": "第一份知识内容",
        },
    )

    client.post(
        "/knowledge/documents",
        json={
            "title": "第二份规范",
            "content": "第二份知识内容",
        },
    )

    list_response = client.get(
        "/knowledge/documents",
        params={
            "limit": 1,
            "offset": 0,
        },
    )

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["title"] == (
        "第二份规范"
    )

    get_response = client.get(
        "/knowledge/documents/1"
    )

    assert get_response.status_code == 200
    assert get_response.json()["title"] == (
        "第一份规范"
    )


def test_create_whitespace_document_returns_422(
    client: TestClient,
) -> None:
    response = client.post(
        "/knowledge/documents",
        json={
            "title": "空文档",
            "content": "   \n\n   ",
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "文档内容清理后不能为空",
    }


def test_missing_document_returns_404(
    client: TestClient,
) -> None:
    document_response = client.get(
        "/knowledge/documents/999"
    )

    chunks_response = client.get(
        "/knowledge/documents/999/chunks"
    )

    assert document_response.status_code == 404
    assert chunks_response.status_code == 404

    assert document_response.json() == {
        "detail": "Knowledge document not found",
    }

    assert chunks_response.json() == {
        "detail": "Knowledge document not found",
    }

def test_search_returns_most_related_document(
    client: TestClient,
) -> None:
    login_response = client.post(
        "/knowledge/documents",
        json={
            "title": "登录安全规范",
            "content": "用户登录密码安全校验",
            "source": "security.md",
        },
    )

    inventory_response = client.post(
        "/knowledge/documents",
        json={
            "title": "库存管理规范",
            "content": "商品库存不足时发送补货提醒",
            "source": "inventory.md",
        },
    )

    assert login_response.status_code == 201
    assert inventory_response.status_code == 201

    response = client.get(
        "/knowledge/search",
        params={
            "query": "用户登录密码安全校验",
            "top_k": 1,
        },
    )

    assert response.status_code == 200

    results = response.json()

    assert len(results) == 1
    assert results[0]["document_title"] == (
        "登录安全规范"
    )
    assert results[0]["source"] == "security.md"
    assert results[0]["content"] == (
        "用户登录密码安全校验"
    )
    assert results[0]["score"] == pytest.approx(
        1.0
    )


def test_search_whitespace_query_returns_422(
    client: TestClient,
) -> None:
    response = client.get(
        "/knowledge/search",
        params={
            "query": "   ",
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "检索内容不能为空",
    }