from typing import Any, TypedDict

import app.agent.tools  # 触发三个分析工具注册
from langgraph.graph import END, START, StateGraph

from app.agent.llm.base import LLMClient
from app.agent.registry import execute_tool, list_tools


class LangGraphState(TypedDict):
    """LangGraph 节点之间传递的共享状态。"""

    title: str
    content: str
    priority: int | None

    planned_tools: list[str]
    tool_results: dict[str, dict[str, Any]]

    issues: list[str]
    passed: bool
    suggested_priority: int | None
    priority_consistent: bool | None

    execution_order: list[str]
    final_report: str


def build_planner_graph(
    llm_client: LLMClient,
):
    """创建 LangGraph 需求分析流程。"""

    def planner_node(
        state: LangGraphState,
    ) -> dict[str, Any]:
        """使用现有 LLM Client 选择分析工具。"""

        planned_tools = llm_client.plan_tools(
            title=state["title"],
            content=state["content"],
            priority=state["priority"],
            available_tools=list_tools(),
        )

        return {
            "planned_tools": list(
                dict.fromkeys(planned_tools)
            ),
            "execution_order": (
                state["execution_order"]
                + ["planner"]
            ),
        }

    def tool_node(
        state: LangGraphState,
    ) -> dict[str, Any]:
        """执行 Planner 选择的分析工具。"""

        tool_arguments: dict[
            str,
            dict[str, Any],
        ] = {
            "completeness_check": {
                "title": state["title"],
                "content": state["content"],
                "priority": state["priority"],
            },
            "ambiguity_check": {
                "content": state["content"],
            },
            "priority_suggestion": {
                "title": state["title"],
                "content": state["content"],
            },
        }

        tool_results: dict[
            str,
            dict[str, Any],
        ] = {}

        for tool_name in state["planned_tools"]:
            arguments = tool_arguments.get(tool_name)

            if arguments is None:
                raise ValueError(
                    "No arguments configured for tool: "
                    f"{tool_name}"
                )

            tool_results[tool_name] = execute_tool(
                tool_name,
                **arguments,
            )

        return {
            "tool_results": tool_results,
            "execution_order": (
                state["execution_order"]
                + ["tool"]
            ),
        }
    def final_report_node(
        state: LangGraphState,
    ) -> dict[str, Any]:
        """汇总工具结果并生成最终报告。"""

        issues: list[str] = []

        completeness_result = (
            state["tool_results"].get(
                "completeness_check"
            )
        )

        if (
            completeness_result is not None
            and not completeness_result["passed"]
        ):
            missing_fields = ", ".join(
                completeness_result[
                    "missing_fields"
                ]
            )
            issues.append(
                f"缺少必要字段：{missing_fields}"
            )

        ambiguity_result = (
            state["tool_results"].get(
                "ambiguity_check"
            )
        )

        if (
            ambiguity_result is not None
            and not ambiguity_result["passed"]
        ):
            matched_terms = "、".join(
                ambiguity_result[
                    "matched_terms"
                ]
            )
            issues.append(
                f"包含模糊表达：{matched_terms}"
            )

        priority_result = (
            state["tool_results"].get(
                "priority_suggestion"
            )
        )

        suggested_priority: int | None = None
        priority_consistent: bool | None = None

        if priority_result is not None:
            suggested_priority = priority_result[
                "suggested_priority"
            ]

            if state["priority"] is not None:
                priority_consistent = (
                    state["priority"]
                    == suggested_priority
                )

                if not priority_consistent:
                    issues.append(
                        f"当前优先级为 "
                        f"{state['priority']}，"
                        f"建议优先级为 "
                        f"{suggested_priority}"
                    )

        passed = bool(state["planned_tools"])

        if not state["planned_tools"]:
            issues.append(
                "Planner 未选择任何分析工具"
            )

        if (
            completeness_result is not None
            and not completeness_result["passed"]
        ):
            passed = False

        if (
            ambiguity_result is not None
            and not ambiguity_result["passed"]
        ):
            passed = False

        if priority_consistent is False:
            passed = False

        final_report = llm_client.generate_report(
            title=state["title"],
            content=state["content"],
            priority=state["priority"],
            planned_tools=state["planned_tools"],
            tool_results=state["tool_results"],
            issues=issues,
            passed=passed,
        )

        return {
            "issues": issues,
            "passed": passed,
            "suggested_priority": (
                suggested_priority
            ),
            "priority_consistent": (
                priority_consistent
            ),
            "execution_order": (
                state["execution_order"]
                + ["final_report"]
            ),
            "final_report": final_report,
        }

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