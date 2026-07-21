"""需求分析的知识库检索与上下文构建服务。"""

from sqlalchemy.orm import Session

from app.schemas import KnowledgeSearchResult
from app.services import knowledge as knowledge_service


def retrieve_requirement_context(
    db: Session,
    title: str,
    content: str,
    top_k: int = 3,
    min_score: float = 0.0,
) -> list[KnowledgeSearchResult]:
    """根据需求标题和内容检索相关知识片段。"""

    query = "\n".join(
        part.strip()
        for part in (
            title,
            content,
        )
        if part.strip()
    )

    if not query:
        raise ValueError("需求检索内容不能为空")

    return knowledge_service.search_knowledge_chunks(
        db=db,
        query=query,
        top_k=top_k,
        min_score=min_score,
    )


def format_knowledge_context(
    results: list[KnowledgeSearchResult],
) -> str:
    """把知识检索结果格式化为模型可使用的上下文。"""

    if not results:
        return ""

    sections: list[str] = []

    for index, result in enumerate(
        results,
        start=1,
    ):
        source = result.source or "未标注来源"

        sections.append(
            "\n".join(
                [
                    f"[知识片段 {index}]",
                    f"文档：{result.document_title}",
                    f"来源：{source}",
                    f"相似度：{result.score:.4f}",
                    f"内容：{result.content}",
                ]
            )
        )

    return "\n\n".join(sections)