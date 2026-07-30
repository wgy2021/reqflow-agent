import pytest

from app.agent.evaluation import (
    RequirementEvaluationCase,
    evaluate_requirement_case,
    evaluate_requirement_cases,
    evaluate_tool_selection,
)


def test_tool_selection_exact_match() -> None:
    result = evaluate_tool_selection(
        expected_tools=[
            "completeness_check",
            "ambiguity_check",
        ],
        actual_tools=[
            "completeness_check",
            "ambiguity_check",
        ],
    )

    assert result.exact_match is True
    assert result.precision == 1.0
    assert result.recall == 1.0
    assert result.missed_tools == []
    assert result.false_positive_tools == []


def test_tool_selection_reports_missing_and_extra_tools() -> None:
    result = evaluate_tool_selection(
        expected_tools=[
            "completeness_check",
            "ambiguity_check",
        ],
        actual_tools=[
            "completeness_check",
            "priority_suggestion",
        ],
    )

    assert result.exact_match is False
    assert result.precision == 0.5
    assert result.recall == 0.5
    assert result.missed_tools == [
        "ambiguity_check",
    ]
    assert result.false_positive_tools == [
        "priority_suggestion",
    ]


def test_tool_selection_handles_empty_lists() -> None:
    result = evaluate_tool_selection(
        expected_tools=[],
        actual_tools=[],
    )

    assert result.exact_match is True
    assert result.precision == 1.0
    assert result.recall == 1.0


def test_requirement_case_runs_real_langgraph_path() -> None:
    case = RequirementEvaluationCase(
        case_id="security-login-001",
        title="用户登录安全需求",
        content="系统应尽快完成安全登录检查",
        priority=2,
        expected_tools=[
            "completeness_check",
            "ambiguity_check",
            "priority_suggestion",
        ],
    )

    result = evaluate_requirement_case(
        case=case,
    )

    assert result.case_id == "security-login-001"
    assert result.tool_selection.exact_match is True
    assert result.tool_selection.actual_tools == [
        "completeness_check",
        "ambiguity_check",
        "priority_suggestion",
    ]
    assert result.actual_status == "completed"
    assert result.actual_passed is False
    assert result.llm_fallback_used is False
    assert result.llm_error is None


def test_requirement_case_exposes_planner_miss() -> None:
    case = RequirementEvaluationCase(
        case_id="expected-ambiguity-001",
        title="修改按钮文案",
        content="将首页按钮文字修改为提交",
        priority=3,
        expected_tools=[
            "completeness_check",
            "ambiguity_check",
        ],
    )

    result = evaluate_requirement_case(
        case=case,
    )

    assert result.tool_selection.exact_match is False
    assert result.tool_selection.missed_tools == [
        "ambiguity_check",
    ]
    assert (
        result.tool_selection.false_positive_tools
        == []
    )
    assert result.tool_selection.precision == 1.0
    assert result.tool_selection.recall == 0.5


def test_requirement_cases_returns_aggregate_metrics() -> None:
    cases = [
        RequirementEvaluationCase(
            case_id="exact-001",
            title="用户登录安全需求",
            content="系统应尽快完成安全登录检查",
            priority=2,
            expected_tools=[
                "completeness_check",
                "ambiguity_check",
                "priority_suggestion",
            ],
        ),
        RequirementEvaluationCase(
            case_id="miss-001",
            title="修改按钮文案",
            content="将首页按钮文字修改为提交",
            priority=3,
            expected_tools=[
                "completeness_check",
                "ambiguity_check",
            ],
        ),
    ]

    summary = evaluate_requirement_cases(
        cases=cases,
    )

    assert summary.total_cases == 2
    assert summary.exact_match_count == 1
    assert summary.exact_match_rate == 0.5
    assert summary.average_precision == 1.0
    assert summary.average_recall == 0.75
    assert summary.fallback_count == 0
    assert summary.failed_case_ids == [
        "miss-001",
    ]
    assert len(summary.results) == 2


def test_requirement_cases_rejects_duplicate_case_ids() -> None:
    cases = [
        RequirementEvaluationCase(
            case_id="duplicate-001",
            title="需求一",
            content="修改页面标题",
            priority=3,
            expected_tools=[
                "completeness_check",
            ],
        ),
        RequirementEvaluationCase(
            case_id="duplicate-001",
            title="需求二",
            content="修改按钮文字",
            priority=3,
            expected_tools=[
                "completeness_check",
            ],
        ),
    ]

    with pytest.raises(
        ValueError,
        match="case_id values must be unique",
    ):
        evaluate_requirement_cases(
            cases=cases,
        )
