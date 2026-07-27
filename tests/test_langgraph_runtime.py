from app.agent.langgraph_runtime import (
    build_planner_graph,
)


def test_langgraph_runs_nodes_in_order() -> None:
    graph = build_planner_graph()

    result = graph.invoke(
        {
            "message": "分析登录需求",
            "execution_order": [],
            "final_report": "",
        }
    )

    assert result["message"] == "分析登录需求"

    assert result["execution_order"] == [
        "planner",
        "tool",
        "final_report",
    ]

    assert (
        result["final_report"]
        == "已完成需求分析：分析登录需求"
    )