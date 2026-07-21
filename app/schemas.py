from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class RequirementCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=100,
    )
    content: str = Field(
        min_length=1,
        max_length=5000,
    )
    priority: int = Field(
        ge=1,
        le=3,
    )


class RequirementUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    content: str | None = Field(
        default=None,
        min_length=1,
        max_length=5000,
    )
    priority: int | None = Field(
        default=None,
        ge=1,
        le=3,
    )


class RequirementResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    title: str
    content: str
    priority: int

class SystemInfoResponse(BaseModel):
    service: str
    version: str
    environment: str

    llm_provider: str
    llm_model: str | None

    database_type: str

    tool_count: int
    tools: list[str]

    cache_version: str

class KnowledgeDocumentCreate(BaseModel):
    """创建知识库文档时接收的数据。"""

    title: str = Field(
        min_length=1,
        max_length=200,
    )

    content: str = Field(
        min_length=1,
        max_length=100_000,
    )

    source: str | None = Field(
        default=None,
        max_length=500,
    )


class KnowledgeDocumentResponse(BaseModel):
    """返回给前端的知识库文档。"""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    title: str
    content: str
    source: str | None
    created_at: datetime


class KnowledgeChunkResponse(BaseModel):
    """返回给前端的知识片段。"""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    document_id: int
    chunk_index: int
    content: str
    created_at: datetime

class KnowledgeSearchResult(BaseModel):
    """知识库语义检索结果。"""

    chunk_id: int
    document_id: int
    document_title: str
    source: str | None
    chunk_index: int
    content: str
    score: float