from pydantic import BaseModel, ConfigDict, Field

from app.agent.langgraph_runtime import (
    execute_langgraph_analysis,
)
from app.agent.llm import FakeLLMClient, LLMClient


class ToolSelectionEvaluation(BaseModel):
    """Planner 工具选择的确定性评测结果。"""

    model_config = ConfigDict(extra="forbid")

    expected_tools: list[str]
    actual_tools: list[str]
    exact_match: bool
    precision: float
    recall: float
    missed_tools: list[str]
    false_positive_tools: list[str]


class RequirementEvaluationCase(BaseModel):
    """一条人工标注的需求分析评测样例。"""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)
    priority: int | None = Field(
        default=None,
        ge=1,
        le=3,
    )
    expected_tools: list[str]


class RequirementEvaluationResult(BaseModel):
    """一条需求样例执行后的评测结果。"""

    model_config = ConfigDict(extra="forbid")

    case_id: str
    tool_selection: ToolSelectionEvaluation
    actual_status: str
    actual_passed: bool
    llm_fallback_used: bool
    llm_error: str | None


class RequirementEvaluationSummary(BaseModel):
    """多条需求样例的聚合评测结果。"""

    model_config = ConfigDict(extra="forbid")

    total_cases: int
    exact_match_count: int
    exact_match_rate: float
    average_precision: float
    average_recall: float
    fallback_count: int
    failed_case_ids: list[str]
    results: list[RequirementEvaluationResult]


def _deduplicate_tools(
    tools: list[str],
) -> list[str]:
    """去重并保留原顺序。"""

    return list(dict.fromkeys(tools))


def evaluate_tool_selection(
    *,
    expected_tools: list[str],
    actual_tools: list[str],
) -> ToolSelectionEvaluation:
    """评估 Planner 工具选择是否符合人工标注。"""

    normalized_expected = _deduplicate_tools(
        expected_tools
    )
    normalized_actual = _deduplicate_tools(
        actual_tools
    )

    expected_set = set(normalized_expected)
    actual_set = set(normalized_actual)

    true_positive_count = len(
        expected_set & actual_set
    )

    if actual_set:
        precision = (
            true_positive_count
            / len(actual_set)
        )
    else:
        precision = (
            1.0
            if not expected_set
            else 0.0
        )

    if expected_set:
        recall = (
            true_positive_count
            / len(expected_set)
        )
    else:
        recall = (
            1.0
            if not actual_set
            else 0.0
        )

    missed_tools = [
        tool_name
        for tool_name in normalized_expected
        if tool_name not in actual_set
    ]

    false_positive_tools = [
        tool_name
        for tool_name in normalized_actual
        if tool_name not in expected_set
    ]

    return ToolSelectionEvaluation(
        expected_tools=normalized_expected,
        actual_tools=normalized_actual,
        exact_match=(
            expected_set == actual_set
        ),
        precision=precision,
        recall=recall,
        missed_tools=missed_tools,
        false_positive_tools=(
            false_positive_tools
        ),
    )


def evaluate_requirement_case(
    *,
    case: RequirementEvaluationCase,
    llm_client: LLMClient | None = None,
) -> RequirementEvaluationResult:
    """运行一条需求样例并评估 Planner 工具选择。"""

    client = llm_client or FakeLLMClient()

    execution = execute_langgraph_analysis(
        llm_client=client,
        title=case.title,
        content=case.content,
        priority=case.priority,
    )

    tool_selection = evaluate_tool_selection(
        expected_tools=case.expected_tools,
        actual_tools=execution.planned_tools,
    )

    return RequirementEvaluationResult(
        case_id=case.case_id,
        tool_selection=tool_selection,
        actual_status=execution.state.status,
        actual_passed=execution.passed,
        llm_fallback_used=(
            execution.llm_fallback_used
        ),
        llm_error=execution.llm_error,
    )


def evaluate_requirement_cases(
    *,
    cases: list[RequirementEvaluationCase],
    llm_client: LLMClient | None = None,
) -> RequirementEvaluationSummary:
    """批量运行评测案例并计算聚合指标。"""

    if not cases:
        raise ValueError(
            "At least one evaluation case is required"
        )

    case_ids = [case.case_id for case in cases]

    if len(case_ids) != len(set(case_ids)):
        raise ValueError(
            "Evaluation case_id values must be unique"
        )

    client = llm_client or FakeLLMClient()

    results = [
        evaluate_requirement_case(
            case=case,
            llm_client=client,
        )
        for case in cases
    ]

    total_cases = len(results)

    exact_match_count = sum(
        result.tool_selection.exact_match
        for result in results
    )

    average_precision = sum(
        result.tool_selection.precision
        for result in results
    ) / total_cases

    average_recall = sum(
        result.tool_selection.recall
        for result in results
    ) / total_cases

    fallback_count = sum(
        result.llm_fallback_used
        for result in results
    )

    failed_case_ids = [
        result.case_id
        for result in results
        if not result.tool_selection.exact_match
    ]

    return RequirementEvaluationSummary(
        total_cases=total_cases,
        exact_match_count=exact_match_count,
        exact_match_rate=(
            exact_match_count / total_cases
        ),
        average_precision=average_precision,
        average_recall=average_recall,
        fallback_count=fallback_count,
        failed_case_ids=failed_case_ids,
        results=results,
    )
