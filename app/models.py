from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

class RequirementAnalysis(Base):
    __tablename__ = "requirement_analyses"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    requirement_id: Mapped[int] = mapped_column(
        ForeignKey("requirements.id"),
        nullable=False,
        index=True,
    )

    passed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    planned_tools: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
    )

    current_priority: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    suggested_priority: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    priority_consistent: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    issues: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
    )

    tool_results: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )

    final_report: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    llm_fallback_used: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    llm_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

class RequirementAnalysisCache(Base):
    __tablename__ = "requirement_analysis_cache"

    requirement_id: Mapped[int] = mapped_column(
        ForeignKey("requirements.id"),
        primary_key=True,
    )

    fingerprint: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    analysis_id: Mapped[int] = mapped_column(
        ForeignKey("requirement_analyses.id"),
        nullable=False,
    )

class KnowledgeDocument(Base):
    """知识库中的原始文档。"""

    __tablename__ = "knowledge_documents"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    source: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )


class KnowledgeChunk(Base):
    """文档切分后用于检索的知识片段。"""

    __tablename__ = "knowledge_chunks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_documents.id"),
        nullable=False,
        index=True,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    embedding: Mapped[list[float] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )