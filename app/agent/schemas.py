from pydantic import BaseModel, Field


class CompletenessToolResult(BaseModel):
    tool: str
    passed: bool
    missing_fields: list[str]


class AmbiguityToolResult(BaseModel):
    tool: str
    passed: bool
    matched_terms: list[str]


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
    final_report: str
    llm_fallback_used: bool
    llm_error: str | None