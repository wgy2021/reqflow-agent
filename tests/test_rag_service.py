import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import (
    Session,
    sessionmaker,
)
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.schemas import (
    KnowledgeDocumentCreate,
    KnowledgeSearchResult,
)
from app.services.knowledge import create_document
from app.services.rag import (
    format_knowledge_context,
    retrieve_requirement_context,
)


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


@pytest.fixture()
def db() -> Session:
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    with TestingSessionLocal() as session:
        yield session


def test_retrieve_requirement_context(
    db: Session,
) -> None:
    create_document(
        db=db,
        document=KnowledgeDocumentCreate(
            title="登录安全规范",
            content="用户登录必须校验用户名和密码",
            source="security.md",
        ),
    )

    create_document(
        db=db,
        document=KnowledgeDocumentCreate(
            title="库存管理规范",
            content="商品库存不足时发送补货提醒",
            source="inventory.md",
        ),
    )

    results = retrieve_requirement_context(
        db=db,
        title="用户登录",
        content="必须校验用户名和密码",
        top_k=1,
    )

    assert len(results) == 1
    assert results[0].document_title == (
        "登录安全规范"
    )
    assert results[0].source == "security.md"


def test_format_knowledge_context() -> None:
    results = [
        KnowledgeSearchResult(
            chunk_id=1,
            document_id=2,
            document_title="登录安全规范",
            source="security.md",
            chunk_index=0,
            content="密码必须加密保存",
            score=0.875,
        )
    ]

    context = format_knowledge_context(results)

    assert "[知识片段 1]" in context
    assert "文档：登录安全规范" in context
    assert "来源：security.md" in context
    assert "相似度：0.8750" in context
    assert "内容：密码必须加密保存" in context


def test_format_empty_results_returns_empty_string() -> None:
    assert format_knowledge_context([]) == ""