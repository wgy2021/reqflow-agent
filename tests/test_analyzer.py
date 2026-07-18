import pytest

from app.agent.analyzer import analyze_requirement
from app.agent.llm import LLMClient


def test_analyze_requirement_passes_clear_requirement() -> None:
    result = analyze_requirement(
        title="接口性能优化",
        content="接口必须在2秒内返回响应",
        priority=2,
    )

    assert result["passed"] is True
    assert result["current_priority"] == 2
    assert result["suggested_priority"] == 2
    assert result["priority_consistent"] is True
    assert result["issues"] == []


def test_analyze_requirement_detects_ambiguity() -> None:
    result = analyze_requirement(
        title="优化提示信息",
        content="系统应尽快返回友好的提示信息",
        priority=3,
    )

    assert result["passed"] is False
    assert "尽快" in result[
        "tool_results"
    ]["ambiguity"]["matched_terms"]
    assert "友好" in result[
        "tool_results"
    ]["ambiguity"]["matched_terms"]


def test_analyze_requirement_detects_priority_mismatch() -> None:
    result = analyze_requirement(
        title="登录故障",
        content="用户无法登录系统",
        priority=3,
    )

    assert result["passed"] is False
    assert result["current_priority"] == 3
    assert result["suggested_priority"] == 1
    assert result["priority_consistent"] is False
    assert (
        "当前优先级为 3，建议优先级为 1"
        in result["issues"]
    )
class StaticPlanner(LLMClient):
    def __init__(
        self,
        planned_tools: list[str],
    ) -> None:
        self.planned_tools = planned_tools

    def plan_tools(
        self,
        title: str,
        content: str,
        priority: int | None,
        available_tools: list[dict[str, str]],
    ) -> list[str]:
        return self.planned_tools


def test_analyzer_executes_only_planned_tools() -> None:
    planner = StaticPlanner(
        planned_tools=[
            "completeness_check",
        ]
    )

    result = analyze_requirement(
        title="登录故障",
        content="系统应尽快解决用户无法登录的问题",
        priority=3,
        llm_client=planner,
    )

    assert result["planned_tools"] == [
        "completeness_check",
    ]

    assert list(result["tool_results"]) == [
        "completeness",
    ]

    assert "ambiguity" not in result["tool_results"]
    assert "priority" not in result["tool_results"]


def test_analyzer_rejects_unavailable_tool() -> None:
    planner = StaticPlanner(
        planned_tools=[
            "missing_tool",
        ]
    )

    with pytest.raises(
        ValueError,
        match=(
            "Planner selected unavailable tool: "
            "missing_tool"
        ),
    ):
        analyze_requirement(
            title="测试需求",
            content="测试内容",
            priority=3,
            llm_client=planner,
        )