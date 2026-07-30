import json

from app.agent.langgraph_runtime import (
    build_planner_graph,
    execute_langgraph_analysis,
    run_langgraph_analysis,
)
from app.agent.llm import FakeLLMClient


def test_langgraph_plans_tools_with_fake_llm() -> None:
    llm_client = FakeLLMClient()
    graph = build_planner_graph(llm_client)

    result = graph.invoke(
        {
            "title": "用户登录安全需求",
            "content": "系统应尽快完成安全登录检查",
            "priority": 2,
            "planned_tools": [],
            "tool_results": {},
            "execution_order": [],
            "final_report": "",
            "issues": [],
            "passed": False,
            "suggested_priority": None,
            "priority_consistent": None,
        }
    )

    assert result["planned_tools"] == [
        "completeness_check",
        "ambiguity_check",
        "priority_suggestion",
    ]

    assert result["execution_order"] == [
        "planner",
        "tool",
        "final_report",
    ]

    assert result["issues"] == [
        "包含模糊表达：尽快",
        "当前优先级为 2，建议优先级为 1",
    ]

    assert result["passed"] is False
    assert result["suggested_priority"] == 1
    assert result["priority_consistent"] is False

    assert result["final_report"] == (
        "需求《用户登录安全需求》分析未通过。"
        "当前优先级：2。"
        "已执行工具："
        "completeness_check、"
        "ambiguity_check、"
        "priority_suggestion。"
        "分析结论："
        "包含模糊表达：尽快；"
        "当前优先级为 2，建议优先级为 1。"
    )

    assert result["tool_results"][
        "completeness_check"
    ] == {
        "tool": "completeness_check",
        "passed": True,
        "missing_fields": [],
    }

    assert result["tool_results"][
        "ambiguity_check"
    ]["matched_terms"] == [
        "尽快",
    ]

    assert result["tool_results"][
        "priority_suggestion"
    ]["suggested_priority"] == 1

def test_execute_langgraph_analysis_returns_complete_result() -> None:
    execution = execute_langgraph_analysis(
        llm_client=FakeLLMClient(),
        title="用户登录安全需求",
        content="系统应尽快完成安全登录检查",
        priority=2,
    )

    assert execution.passed is False

    assert execution.planned_tools == [
        "completeness_check",
        "ambiguity_check",
        "priority_suggestion",
    ]

    assert execution.current_priority == 2
    assert execution.suggested_priority == 1
    assert execution.priority_consistent is False

    assert execution.issues == [
        "包含模糊表达：尽快",
        "当前优先级为 2，建议优先级为 1",
    ]

    assert execution.raw_tool_results[
        "ambiguity_check"
    ]["matched_terms"] == ["尽快"]

    assert execution.final_report == (
        execution.state.final_answer
    )

    assert execution.state.status == "completed"
    assert execution.state.step_count == 3

    assert execution.llm_fallback_used is False
    assert execution.llm_error is None


def test_run_langgraph_analysis_returns_agent_state() -> None:
    state = run_langgraph_analysis(
        llm_client=FakeLLMClient(),
        title="用户登录安全需求",
        content="系统应尽快完成安全登录检查",
        priority=2,
    )

    assert state.status == "completed"
    assert state.error is None
    assert state.step_count == 3

    assert [
        item["tool_name"]
        for item in state.tool_results
    ] == [
        "completeness_check",
        "ambiguity_check",
        "priority_suggestion",
    ]

    assert len(state.messages) == 2
    assert state.final_answer is not None
    assert "分析未通过" in state.final_answer
    assert "包含模糊表达：尽快" in state.final_answer
    assert "建议优先级为 1" in state.final_answer

    assert [
        call.function.name
        for call in state.tool_calls
    ] == [
        "completeness_check",
        "ambiguity_check",
        "priority_suggestion",
    ]

    assert [
        json.loads(call.function.arguments)
        for call in state.tool_calls
    ] == [
        {
            "title": "用户登录安全需求",
            "content": "系统应尽快完成安全登录检查",
            "priority": 2,
        },
        {
            "content": "系统应尽快完成安全登录检查",
        },
        {
            "title": "用户登录安全需求",
            "content": "系统应尽快完成安全登录检查",
        },
    ]


class NoToolLLMClient(FakeLLMClient):
    """模拟 Planner 不选择任何工具。"""

    def plan_tools(
        self,
        title: str,
        content: str,
        priority: int | None,
        available_tools: list[dict[str, str]],
    ) -> list[str]:
        return []


def test_langgraph_skips_tool_node_when_no_tools() -> None:
    graph = build_planner_graph(
        NoToolLLMClient()
    )

    result = graph.invoke(
        {
            "title": "普通需求",
            "content": "展示欢迎页面",
            "priority": 3,
            "planned_tools": [],
            "tool_results": {},
            "execution_order": [],
            "final_report": "",
            "issues": [],
            "passed": False,
            "suggested_priority": None,
            "priority_consistent": None,
        }
    )

    assert result["planned_tools"] == []
    assert result["tool_results"] == {}

    assert result["execution_order"] == [
        "planner",
        "final_report",
    ]

    assert result["issues"] == [
        "Planner 未选择任何分析工具",
    ]

    assert result["passed"] is False

    assert result["final_report"] == (
        "需求《普通需求》分析未通过。"
        "当前优先级：3。"
        "已执行工具：无。"
        "分析结论："
        "Planner 未选择任何分析工具。"
    )


class UnknownToolLLMClient(FakeLLMClient):
    """模拟 Planner 选择未配置的工具。"""

    def plan_tools(
        self,
        title: str,
        content: str,
        priority: int | None,
        available_tools: list[dict[str, str]],
    ) -> list[str]:
        return ["unknown_tool"]


def test_langgraph_records_tool_error() -> None:
    state = run_langgraph_analysis(
        llm_client=UnknownToolLLMClient(),
        title="异常工具测试",
        content="验证工具失败时仍能生成运行记录",
        priority=2,
    )

    assert state.status == "failed"
    assert state.error == (
        "unknown_tool: "
        "ValueError: No arguments configured "
        "for tool: unknown_tool"
    )
    assert state.step_count == 3

    assert len(state.tool_calls) == 1
    assert (
        state.tool_calls[0].function.name
        == "unknown_tool"
    )
    assert json.loads(
        state.tool_calls[0].function.arguments
    ) == {}

    assert len(state.tool_results) == 1

    result = state.tool_results[0]["result"]

    assert result["tool"] == "unknown_tool"
    assert result["passed"] is False
    assert result["error"] == (
        "ValueError: No arguments configured "
        "for tool: unknown_tool"
    )

    assert (
        "工具 unknown_tool 执行失败"
        in state.final_answer
    )