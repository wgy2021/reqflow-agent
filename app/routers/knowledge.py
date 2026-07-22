from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    KnowledgeChunk,
    KnowledgeDocument,
)
from app.schemas import (
    KnowledgeChunkResponse,
    KnowledgeDocumentCreate,
    KnowledgeDocumentResponse,
    KnowledgeDocumentUpdate,
    KnowledgeReindexResponse,
    KnowledgeSearchResult,
)
from app.services import knowledge as knowledge_service


router = APIRouter(
    prefix="/knowledge",
    tags=["knowledge"],
)


@router.post(
    "/documents",
    response_model=KnowledgeDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_knowledge_document(
    document: KnowledgeDocumentCreate,
    db: Session = Depends(get_db),
) -> KnowledgeDocument:
    """创建知识文档，并自动完成文本分块。"""

    try:
        return knowledge_service.create_document(
            db=db,
            document=document,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.post(
    "/reindex",
    response_model=KnowledgeReindexResponse,
)
def reindex_knowledge(
    db: Session = Depends(get_db),
) -> KnowledgeReindexResponse:
    """为旧知识片段补充向量。"""

    try:
        return knowledge_service.reindex_knowledge_chunks(
            db=db,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

@router.get(
    "/search",
    response_model=list[KnowledgeSearchResult],
)
def search_knowledge(
    query: str = Query(
        min_length=1,
        max_length=1000,
    ),
    top_k: int = Query(
        default=5,
        ge=1,
        le=20,
    ),
    min_score: float = Query(
        default=0.0,
        ge=-1.0,
        le=1.0,
    ),
    db: Session = Depends(get_db),
) -> list[KnowledgeSearchResult]:
    """按照语义相似度检索知识片段。"""

    try:
        return knowledge_service.search_knowledge_chunks(
            db=db,
            query=query,
            top_k=top_k,
            min_score=min_score,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

@router.get(
    "/documents",
    response_model=list[KnowledgeDocumentResponse],
)
def list_knowledge_documents(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    db: Session = Depends(get_db),
) -> list[KnowledgeDocument]:
    """分页查询知识文档。"""

    return knowledge_service.list_documents(
        db=db,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/documents/{document_id}",
    response_model=KnowledgeDocumentResponse,
)
def get_knowledge_document(
    document_id: int,
    db: Session = Depends(get_db),
) -> KnowledgeDocument:
    """查询指定知识文档。"""

    document = knowledge_service.get_document(
        db=db,
        document_id=document_id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge document not found",
        )

    return document

@router.put(
    "/documents/{document_id}",
    response_model=KnowledgeDocumentResponse,
)
def update_knowledge_document(
    document_id: int,
    document: KnowledgeDocumentUpdate,
    db: Session = Depends(get_db),
) -> KnowledgeDocument:
    """更新知识文档，并重新生成知识片段和向量。"""

    try:
        updated_document = (
            knowledge_service.update_document(
                db=db,
                document_id=document_id,
                document=document,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_CONTENT
            ),
            detail=str(exc),
        ) from exc

    if updated_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge document not found",
        )

    return updated_document

@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_knowledge_document(
    document_id: int,
    db: Session = Depends(get_db),
) -> None:
    """删除知识文档及其全部知识片段。"""

    deleted = knowledge_service.delete_document(
        db=db,
        document_id=document_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge document not found",
        )


@router.get(
    "/documents/{document_id}/chunks",
    response_model=list[KnowledgeChunkResponse],
)
def list_knowledge_document_chunks(
    document_id: int,
    db: Session = Depends(get_db),
) -> list[KnowledgeChunk]:
    """查询指定文档生成的知识片段。"""

    document = knowledge_service.get_document(
        db=db,
        document_id=document_id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge document not found",
        )

    return knowledge_service.list_document_chunks(
        db=db,
        document_id=document_id,
    )