import json
from app.agent.langgraph_runtime import (
    build_planner_graph,
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

def test_run_langgraph_analysis_returns_agent_state() -> None:
    state = run_langgraph_analysis(
        llm_client=FakeLLMClient(),
        title="用户登录安全需求",
        content="系统应尽快完成安全登录检查",
        priority=2,
    )

    assert state.status == "completed"
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
    assert state.error is None
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