"""知识库文档处理和数据库服务。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    KnowledgeChunk,
    KnowledgeDocument,
)
from app.schemas import KnowledgeDocumentCreate


DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50


def normalize_text(text: str) -> str:
    """清理文档中的空行和每行首尾空格。"""

    cleaned_lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    return "\n".join(cleaned_lines)


def split_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """按照固定长度将文本切分为带重叠区域的知识片段。"""

    if chunk_size <= 0:
        raise ValueError("chunk_size 必须大于 0")

    if overlap < 0:
        raise ValueError("overlap 不能小于 0")

    if overlap >= chunk_size:
        raise ValueError("overlap 必须小于 chunk_size")

    normalized_text = normalize_text(text)

    if not normalized_text:
        return []

    chunks: list[str] = []
    start = 0
    text_length = len(normalized_text)

    while start < text_length:
        end = min(
            start + chunk_size,
            text_length,
        )

        chunk = normalized_text[start:end]

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = end - overlap

    return chunks


def create_document(
    db: Session,
    document: KnowledgeDocumentCreate,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> KnowledgeDocument:
    """保存知识文档，并自动生成知识片段。"""

    chunks = split_text(
        text=document.content,
        chunk_size=chunk_size,
        overlap=overlap,
    )

    if not chunks:
        raise ValueError("文档内容清理后不能为空")

    db_document = KnowledgeDocument(
        title=document.title,
        content=normalize_text(document.content),
        source=document.source,
    )

    try:
        db.add(db_document)

        # flush 会先取得文档 ID，但不会提交事务。
        db.flush()

        db_chunks = [
            KnowledgeChunk(
                document_id=db_document.id,
                chunk_index=index,
                content=chunk,
                embedding=None,
            )
            for index, chunk in enumerate(chunks)
        ]

        db.add_all(db_chunks)
        db.commit()
        db.refresh(db_document)

        return db_document

    except Exception:
        db.rollback()
        raise


def list_documents(
    db: Session,
    limit: int = 20,
    offset: int = 0,
) -> list[KnowledgeDocument]:
    """分页查询知识文档。"""

    statement = (
        select(KnowledgeDocument)
        .order_by(KnowledgeDocument.id.desc())
        .offset(offset)
        .limit(limit)
    )

    return list(
        db.scalars(statement).all()
    )


def get_document(
    db: Session,
    document_id: int,
) -> KnowledgeDocument | None:
    """按照 ID 查询知识文档。"""

    return db.get(
        KnowledgeDocument,
        document_id,
    )


def list_document_chunks(
    db: Session,
    document_id: int,
) -> list[KnowledgeChunk]:
    """查询指定文档生成的全部片段。"""

    statement = (
        select(KnowledgeChunk)
        .where(
            KnowledgeChunk.document_id == document_id
        )
        .order_by(KnowledgeChunk.chunk_index.asc())
    )

    return list(
        db.scalars(statement).all()
    )