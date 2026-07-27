from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class LangGraphState(TypedDict):
    """LangGraph 节点之间传递的共享状态。"""

    message: str
    execution_order: list[str]
    final_report: str


def planner_node(
    state: LangGraphState,
) -> dict[str, object]:
    """模拟规划节点。"""

    return {
        "execution_order": (
            state["execution_order"]
            + ["planner"]
        ),
    }


def tool_node(
    state: LangGraphState,
) -> dict[str, object]:
    """模拟工具执行节点。"""

    return {
        "execution_order": (
            state["execution_order"]
            + ["tool"]
        ),
    }


def final_report_node(
    state: LangGraphState,
) -> dict[str, object]:
    """模拟生成最终分析报告。"""

    return {
        "execution_order": (
            state["execution_order"]
            + ["final_report"]
        ),
        "final_report": (
            f"已完成需求分析：{state['message']}"
        ),
    }


def build_planner_graph():
    """创建包含三个节点的最小 LangGraph。"""

    builder = StateGraph(LangGraphState)

    builder.add_node(
        "planner",
        planner_node,
    )
    builder.add_node(
        "tool",
        tool_node,
    )
    builder.add_node(
        "final_report",
        final_report_node,
    )

    builder.add_edge(
        START,
        "planner",
    )
    builder.add_edge(
        "planner",
        "tool",
    )
    builder.add_edge(
        "tool",
        "final_report",
    )
    builder.add_edge(
        "final_report",
        END,
    )

    return builder.compile()