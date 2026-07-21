import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import (
    Session,
    sessionmaker,
)
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.schemas import KnowledgeDocumentCreate
from app.services.knowledge import (
    create_document,
    search_knowledge_chunks,
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


def test_search_returns_most_related_chunk(
    db: Session,
) -> None:
    create_document(
        db=db,
        document=KnowledgeDocumentCreate(
            title="登录安全规范",
            content="用户登录密码安全校验",
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

    results = search_knowledge_chunks(
        db=db,
        query="用户登录密码安全校验",
        top_k=1,
    )

    assert len(results) == 1
    assert results[0].document_title == (
        "登录安全规范"
    )
    assert results[0].source == "security.md"
    assert results[0].score == pytest.approx(
        1.0
    )


def test_search_results_are_sorted(
    db: Session,
) -> None:
    create_document(
        db=db,
        document=KnowledgeDocumentCreate(
            title="登录规范",
            content="用户登录需要校验密码",
        ),
    )

    create_document(
        db=db,
        document=KnowledgeDocumentCreate(
            title="账户规范",
            content="用户账户需要进行安全校验",
        ),
    )

    create_document(
        db=db,
        document=KnowledgeDocumentCreate(
            title="库存规范",
            content="商品库存需要定期盘点",
        ),
    )

    results = search_knowledge_chunks(
        db=db,
        query="用户登录密码校验",
        top_k=2,
    )

    assert len(results) == 2

    assert results[0].score >= results[1].score

    assert results[0].document_title == (
        "登录规范"
    )


def test_search_rejects_invalid_parameters(
    db: Session,
) -> None:
    with pytest.raises(
        ValueError,
        match="不能为空",
    ):
        search_knowledge_chunks(
            db=db,
            query="   ",
        )

    with pytest.raises(
        ValueError,
        match="top_k",
    ):
        search_knowledge_chunks(
            db=db,
            query="登录",
            top_k=0,
        )

    with pytest.raises(
        ValueError,
        match="min_score",
    ):
        search_knowledge_chunks(
            db=db,
            query="登录",
            min_score=2.0,
        )