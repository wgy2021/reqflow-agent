"""知识库文档处理和数据库服务。"""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from app.agent.embeddings import (
    EmbeddingClient,
    LocalHashEmbeddingClient,
    cosine_similarity,
)

from app.models import (
    KnowledgeChunk,
    KnowledgeDocument,
)
from app.schemas import (
    KnowledgeDocumentCreate,
    KnowledgeDocumentUpdate,
    KnowledgeReindexResponse,
    KnowledgeSearchResult,
)


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
    embedding_client: EmbeddingClient | None = None,
) -> KnowledgeDocument:
    """保存知识文档，并自动生成知识片段。"""

    chunks = split_text(
        text=document.content,
        chunk_size=chunk_size,
        overlap=overlap,
    )

    if not chunks:
        raise ValueError("文档内容清理后不能为空")

    if embedding_client is None:
        embedding_client = LocalHashEmbeddingClient()

    embeddings = embedding_client.embed_texts(chunks)

    if len(embeddings) != len(chunks):
        raise ValueError("向量数量与知识片段数量不一致")

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
                embedding=embeddings[index],
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

def update_document(
    db: Session,
    document_id: int,
    document: KnowledgeDocumentUpdate,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
    embedding_client: EmbeddingClient | None = None,
) -> KnowledgeDocument | None:
    """更新知识文档，并重新生成知识片段和向量。"""

    db_document = get_document(
        db=db,
        document_id=document_id,
    )

    if db_document is None:
        return None

    chunks = split_text(
        text=document.content,
        chunk_size=chunk_size,
        overlap=overlap,
    )

    if not chunks:
        raise ValueError("文档内容清理后不能为空")

    if embedding_client is None:
        embedding_client = LocalHashEmbeddingClient()

    embeddings = embedding_client.embed_texts(chunks)

    if len(embeddings) != len(chunks):
        raise ValueError(
            "向量数量与知识片段数量不一致"
        )

    try:
        db.execute(
            delete(KnowledgeChunk).where(
                KnowledgeChunk.document_id
                == document_id
            )
        )

        db_document.title = document.title
        db_document.content = normalize_text(
            document.content
        )
        db_document.source = document.source

        db_chunks = [
            KnowledgeChunk(
                document_id=document_id,
                chunk_index=index,
                content=chunk,
                embedding=embeddings[index],
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


def delete_document(
    db: Session,
    document_id: int,
) -> bool:
    """删除知识文档及其全部知识片段。"""

    document = get_document(
        db=db,
        document_id=document_id,
    )

    if document is None:
        return False

    try:
        db.execute(
            delete(KnowledgeChunk).where(
                KnowledgeChunk.document_id
                == document_id
            )
        )

        db.delete(document)
        db.commit()

        return True

    except Exception:
        db.rollback()
        raise


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

def search_knowledge_chunks(
    db: Session,
    query: str,
    top_k: int = 5,
    min_score: float = 0.0,
    embedding_client: EmbeddingClient | None = None,
) -> list[KnowledgeSearchResult]:
    """按照余弦相似度检索最相关的知识片段。"""

    normalized_query = normalize_text(query)

    if not normalized_query:
        raise ValueError("检索内容不能为空")

    if top_k <= 0:
        raise ValueError("top_k 必须大于 0")

    if not -1.0 <= min_score <= 1.0:
        raise ValueError(
            "min_score 必须在 -1 到 1 之间"
        )

    if embedding_client is None:
        embedding_client = LocalHashEmbeddingClient()

    query_embedding = embedding_client.embed_texts(
        [
            normalized_query,
        ]
    )[0]

    statement = (
        select(
            KnowledgeChunk,
            KnowledgeDocument,
        )
        .join(
            KnowledgeDocument,
            KnowledgeChunk.document_id
            == KnowledgeDocument.id,
        )
    )

    search_results: list[
        KnowledgeSearchResult
    ] = []

    for chunk, document in db.execute(
        statement
    ).all():
        if chunk.embedding is None:
            continue

        if len(chunk.embedding) != len(
            query_embedding
        ):
            continue

        score = cosine_similarity(
            query_embedding,
            chunk.embedding,
        )

        if score < min_score:
            continue

        search_results.append(
            KnowledgeSearchResult(
                chunk_id=chunk.id,
                document_id=document.id,
                document_title=document.title,
                source=document.source,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                score=score,
            )
        )

    search_results.sort(
        key=lambda result: result.score,
        reverse=True,
    )

    return search_results[:top_k]

def reindex_knowledge_chunks(
    db: Session,
    embedding_client: EmbeddingClient | None = None,
) -> KnowledgeReindexResponse:
    """为缺少向量的旧知识片段补充 embedding。"""

    chunks = list(
        db.scalars(
            select(KnowledgeChunk).order_by(
                KnowledgeChunk.id.asc()
            )
        ).all()
    )

    pending_chunks = [
        chunk
        for chunk in chunks
        if chunk.embedding is None
    ]

    if not pending_chunks:
        return KnowledgeReindexResponse(
            total_chunks=len(chunks),
            updated_chunks=0,
            skipped_chunks=len(chunks),
        )

    if embedding_client is None:
        embedding_client = LocalHashEmbeddingClient()

    embeddings = embedding_client.embed_texts(
        [
            chunk.content
            for chunk in pending_chunks
        ]
    )

    if len(embeddings) != len(pending_chunks):
        raise ValueError(
            "向量数量与待索引片段数量不一致"
        )

    try:
        for chunk, embedding in zip(
            pending_chunks,
            embeddings,
            strict=True,
        ):
            chunk.embedding = embedding

        db.commit()

    except Exception:
        db.rollback()
        raise

    return KnowledgeReindexResponse(
        total_chunks=len(chunks),
        updated_chunks=len(pending_chunks),
        skipped_chunks=(
            len(chunks) - len(pending_chunks)
        ),
    )