from datetime import datetime


from pydantic import BaseModel, ConfigDict, Field

from app.schemas import KnowledgeSearchResult

class CompletenessToolInput(BaseModel):
    """完整性检查工具的输入参数。"""

    model_config = ConfigDict(
        extra="forbid",
    )

    title: str
    content: str
    priority: int | None = Field(
        default=None,
        ge=1,
        le=3,
    )


class CompletenessToolResult(BaseModel):
    tool: str
    passed: bool
    missing_fields: list[str]

class AmbiguityToolInput(BaseModel):
    """歧义检查工具的输入参数。"""

    model_config = ConfigDict(
        extra="forbid",
    )

    content: str


class AmbiguityToolResult(BaseModel):
    tool: str
    passed: bool
    matched_terms: list[str]

class PriorityToolInput(BaseModel):
    """优先级建议工具的输入参数。"""

    model_config = ConfigDict(
        extra="forbid",
    )

    title: str
    content: str


class PriorityToolResult(BaseModel):
    tool: str
    suggested_priority: int = Field(
        ge=1,
        le=3,
    )
    matched_keywords: list[str]
    reason: str


class RequirementToolResults(BaseModel):
    completeness: CompletenessToolResult | None = None
    ambiguity: AmbiguityToolResult | None = None
    priority: PriorityToolResult | None = None


class RequirementAnalysisResponse(BaseModel):
    passed: bool
    planned_tools: list[str]
    current_priority: int | None
    suggested_priority: int | None = Field(
        default=None,
        ge=1,
        le=3,
    )
    priority_consistent: bool | None
    issues: list[str]
    tool_results: RequirementToolResults
    knowledge_references: list[
        KnowledgeSearchResult
    ] = Field(
        default_factory=list,
    )
    final_report: str
    llm_fallback_used: bool
    llm_error: str | None
    cache_hit: bool = False

class RequirementAnalysisHistoryResponse(
    RequirementAnalysisResponse
):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    requirement_id: int
    created_at: datetime
