from typing import Any

import app.agent.tools  # 触发工具注册
from app.agent.llm import LLMClient, get_llm_client
from app.agent.registry import execute_tool, list_tools


TOOL_RESULT_KEYS = {
    "completeness_check": "completeness",
    "ambiguity_check": "ambiguity",
    "priority_suggestion": "priority",
}


def analyze_requirement(
    title: str,
    content: str,
    priority: int | None,
    llm_client: LLMClient | None = None,
) -> dict[str, Any]:
    """由 Planner 选择工具，再执行并汇总分析结果。"""

    client = llm_client or get_llm_client()

    available_tools = list_tools()
    available_tool_names = {
        tool["name"]
        for tool in available_tools
    }

    planned_tools = client.plan_tools(
        title=title,
        content=content,
        priority=priority,
        available_tools=available_tools,
    )

    # 去除重复工具，同时保留原有顺序。
    planned_tools = list(
        dict.fromkeys(planned_tools)
    )

    for tool_name in planned_tools:
        if tool_name not in available_tool_names:
            raise ValueError(
                f"Planner selected unavailable tool: {tool_name}"
            )

    tool_arguments: dict[str, dict[str, Any]] = {
        "completeness_check": {
            "title": title,
            "content": content,
            "priority": priority,
        },
        "ambiguity_check": {
            "content": content,
        },
        "priority_suggestion": {
            "title": title,
            "content": content,
        },
    }

    tool_results: dict[str, dict[str, Any]] = {}

    for tool_name in planned_tools:
        result_key = TOOL_RESULT_KEYS.get(tool_name)

        if result_key is None:
            raise ValueError(
                f"No result mapping configured for tool: {tool_name}"
            )

        tool_results[result_key] = execute_tool(
            tool_name,
            **tool_arguments[tool_name],
        )

    issues: list[str] = []

    completeness_result = tool_results.get(
        "completeness"
    )

    if (
        completeness_result is not None
        and not completeness_result["passed"]
    ):
        missing_fields = ", ".join(
            completeness_result["missing_fields"]
        )
        issues.append(
            f"缺少必要字段：{missing_fields}"
        )

    ambiguity_result = tool_results.get(
        "ambiguity"
    )

    if (
        ambiguity_result is not None
        and not ambiguity_result["passed"]
    ):
        matched_terms = "、".join(
            ambiguity_result["matched_terms"]
        )
        issues.append(
            f"包含模糊表达：{matched_terms}"
        )

    priority_result = tool_results.get("priority")

    suggested_priority: int | None = None
    priority_consistent: bool | None = None

    if priority_result is not None:
        suggested_priority = priority_result[
            "suggested_priority"
        ]

        if priority is not None:
            priority_consistent = (
                priority == suggested_priority
            )

            if not priority_consistent:
                issues.append(
                    f"当前优先级为 {priority}，"
                    f"建议优先级为 {suggested_priority}"
                )

    passed = bool(planned_tools)

    if not planned_tools:
        issues.append("Planner 未选择任何分析工具")

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

    return {
        "passed": passed,
        "planned_tools": planned_tools,
        "current_priority": priority,
        "suggested_priority": suggested_priority,
        "priority_consistent": priority_consistent,
        "issues": issues,
        "tool_results": tool_results,
    }