from app.agent.analyzer import (
    to_requirement_analysis_result,
)
from app.agent.langgraph_runtime import (
    LangGraphAnalysisExecution,
)
from app.agent.state import AgentState


def test_to_requirement_analysis_result_maps_fields() -> None:
    execution = LangGraphAnalysisExecution(
        state=AgentState(
            status="completed",
            step_count=3,
            final_answer="固定分析报告",
        ),
        passed=False,
        planned_tools=[
            "completeness_check",
            "ambiguity_check",
            "priority_suggestion",
        ],
        current_priority=2,
        suggested_priority=1,
        priority_consistent=False,
        issues=[
            "包含模糊表达：尽快",
            "当前优先级为 2，建议优先级为 1",
        ],
        raw_tool_results={
            "completeness_check": {
                "tool": "completeness_check",
                "passed": True,
                "missing_fields": [],
            },
            "ambiguity_check": {
                "tool": "ambiguity_check",
                "passed": False,
                "matched_terms": ["尽快"],
            },
            "priority_suggestion": {
                "tool": "priority_suggestion",
                "suggested_priority": 1,
                "matched_keywords": ["安全"],
                "reason": "涉及登录安全",
            },
        },
        final_report="固定分析报告",
        llm_fallback_used=False,
        llm_error=None,
    )

    result = to_requirement_analysis_result(execution)

    assert result["passed"] is False
    assert result["planned_tools"] == [
        "completeness_check",
        "ambiguity_check",
        "priority_suggestion",
    ]
    assert result["current_priority"] == 2
    assert result["suggested_priority"] == 1
    assert result["priority_consistent"] is False
    assert result["issues"] == [
        "包含模糊表达：尽快",
        "当前优先级为 2，建议优先级为 1",
    ]

    assert result["tool_results"]["completeness"][
        "passed"
    ] is True

    assert result["tool_results"]["ambiguity"][
        "matched_terms"
    ] == ["尽快"]

    assert result["tool_results"]["priority"][
        "suggested_priority"
    ] == 1

    assert result["final_report"] == "固定分析报告"
    assert result["llm_fallback_used"] is False
    assert result["llm_error"] is None