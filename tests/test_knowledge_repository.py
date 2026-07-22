import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import (
    Session,
    sessionmaker,
)
from sqlalchemy.pool import StaticPool

from app.agent.embeddings import LocalHashEmbeddingClient
from app.database import Base
from app.models import (
    KnowledgeChunk,
    KnowledgeDocument,
)
from app.schemas import (
    KnowledgeDocumentCreate,
    KnowledgeDocumentUpdate,
)
from app.services.knowledge import (
    create_document,
    delete_document,
    get_document,
    list_document_chunks,
    list_documents,
    reindex_knowledge_chunks,
    update_document,
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


def test_create_document_generates_chunks(
    db: Session,
) -> None:
    document = KnowledgeDocumentCreate(
        title="登录安全规范",
        content="ABCDEFGHIJ",
        source="security-guide.md",
    )

    created_document = create_document(
        db=db,
        document=document,
        chunk_size=6,
        overlap=2,
        embedding_client=LocalHashEmbeddingClient(
            dimension=8,
        ),
    )

    chunks = list_document_chunks(
        db=db,
        document_id=created_document.id,
    )

    assert created_document.id == 1
    assert created_document.title == "登录安全规范"
    assert created_document.source == "security-guide.md"

    assert [
        chunk.chunk_index
        for chunk in chunks
    ] == [
        0,
        1,
    ]

    assert [
        chunk.content
        for chunk in chunks
    ] == [
        "ABCDEF",
        "EFGHIJ",
    ]

    assert all(
        chunk.embedding is not None
        for chunk in chunks
    )

    assert all(
        len(chunk.embedding) == 8
        for chunk in chunks
        if chunk.embedding is not None
    )


def test_list_and_get_documents(
    db: Session,
) -> None:
    first_document = create_document(
        db=db,
        document=KnowledgeDocumentCreate(
            title="第一份规范",
            content="第一份知识内容",
        ),
    )

    second_document = create_document(
        db=db,
        document=KnowledgeDocumentCreate(
            title="第二份规范",
            content="第二份知识内容",
        ),
    )

    documents = list_documents(
        db=db,
        limit=1,
        offset=0,
    )

    assert len(documents) == 1
    assert documents[0].id == second_document.id

    found_document = get_document(
        db=db,
        document_id=first_document.id,
    )

    assert found_document is not None
    assert found_document.title == "第一份规范"

def test_update_document_regenerates_chunks(
    db: Session,
) -> None:
    created_document = create_document(
        db=db,
        document=KnowledgeDocumentCreate(
            title="旧知识文档",
            content="ABCDEFGHIJ",
            source="old.md",
        ),
        chunk_size=6,
        overlap=2,
        embedding_client=LocalHashEmbeddingClient(
            dimension=8,
        ),
    )

    updated_document = update_document(
        db=db,
        document_id=created_document.id,
        document=KnowledgeDocumentUpdate(
            title="新知识文档",
            content="1234567890",
            source="new.md",
        ),
        chunk_size=6,
        overlap=2,
        embedding_client=LocalHashEmbeddingClient(
            dimension=8,
        ),
    )

    assert updated_document is not None
    assert updated_document.id == created_document.id
    assert updated_document.title == "新知识文档"
    assert updated_document.content == "1234567890"
    assert updated_document.source == "new.md"

    chunks = list_document_chunks(
        db=db,
        document_id=created_document.id,
    )

    assert [
        chunk.content
        for chunk in chunks
    ] == [
        "123456",
        "567890",
    ]

    assert all(
        chunk.embedding is not None
        for chunk in chunks
    )

    assert all(
        len(chunk.embedding) == 8
        for chunk in chunks
        if chunk.embedding is not None
    )

    missing_document = update_document(
        db=db,
        document_id=999,
        document=KnowledgeDocumentUpdate(
            title="不存在",
            content="不存在的文档内容",
            source=None,
        ),
    )

    assert missing_document is None


def test_delete_document_removes_document_and_chunks(
    db: Session,
) -> None:
    document = create_document(
        db=db,
        document=KnowledgeDocumentCreate(
            title="待删除知识文档",
            content="用户密码必须进行加密保存",
            source="delete-test.md",
        ),
    )

    chunks_before_delete = list_document_chunks(
        db=db,
        document_id=document.id,
    )

    assert chunks_before_delete != []

    deleted = delete_document(
        db=db,
        document_id=document.id,
    )

    assert deleted is True

    assert get_document(
        db=db,
        document_id=document.id,
    ) is None

    assert list_document_chunks(
        db=db,
        document_id=document.id,
    ) == []

    deleted_again = delete_document(
        db=db,
        document_id=document.id,
    )

    assert deleted_again is False


def test_create_empty_document_rolls_back(
    db: Session,
) -> None:
    document = KnowledgeDocumentCreate(
        title="空文档",
        content="   \n\n   ",
    )

    with pytest.raises(
        ValueError,
        match="不能为空",
    ):
        create_document(
            db=db,
            document=document,
        )

    documents = list(
        db.scalars(
            select(KnowledgeDocument)
        ).all()
    )

    chunks = list(
        db.scalars(
            select(KnowledgeChunk)
        ).all()
    )

    assert documents == []
    assert chunks == []


def test_reindex_fills_missing_embeddings(
    db: Session,
) -> None:
    document = KnowledgeDocument(
        title="旧知识文档",
        content="旧知识片段内容",
        source="legacy.md",
    )

    db.add(document)
    db.flush()

    missing_chunk = KnowledgeChunk(
        document_id=document.id,
        chunk_index=0,
        content="用户登录需要校验密码",
        embedding=None,
    )

    indexed_chunk = KnowledgeChunk(
        document_id=document.id,
        chunk_index=1,
        content="已经完成向量化",
        embedding=[
            1.0,
            0.0,
        ],
    )

    db.add_all([
        missing_chunk,
        indexed_chunk,
    ])
    db.commit()

    result = reindex_knowledge_chunks(
        db=db,
        embedding_client=LocalHashEmbeddingClient(
            dimension=8,
        ),
    )

    db.refresh(missing_chunk)
    db.refresh(indexed_chunk)

    assert result.total_chunks == 2
    assert result.updated_chunks == 1
    assert result.skipped_chunks == 1

    assert missing_chunk.embedding is not None
    assert len(missing_chunk.embedding) == 8

    assert indexed_chunk.embedding == [
        1.0,
        0.0,
    ]