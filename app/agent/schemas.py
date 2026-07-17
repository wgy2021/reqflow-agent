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
    suggested_priority: int = Field(ge=1, le=3)
    matched_keywords: list[str]
    reason: str


class RequirementToolResults(BaseModel):
    completeness: CompletenessToolResult
    ambiguity: AmbiguityToolResult
    priority: PriorityToolResult


class RequirementAnalysisResponse(BaseModel):
    passed: bool
    current_priority: int | None
    suggested_priority: int = Field(ge=1, le=3)
    priority_consistent: bool
    issues: list[str]
    tool_results: RequirementToolResults