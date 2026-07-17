from typing import Any

import app.agent.tools  # 导入工具模块，触发工具注册
from app.agent.registry import execute_tool


def analyze_requirement(
    title: str,
    content: str,
    priority: int | None,
) -> dict[str, Any]:
    """依次调用需求分析工具，并汇总分析结果。"""

    completeness_result = execute_tool(
        "completeness_check",
        title=title,
        content=content,
        priority=priority,
    )

    ambiguity_result = execute_tool(
        "ambiguity_check",
        content=content,
    )

    priority_result = execute_tool(
        "priority_suggestion",
        title=title,
        content=content,
    )

    issues: list[str] = []

    if not completeness_result["passed"]:
        missing_fields = ", ".join(
            completeness_result["missing_fields"]
        )
        issues.append(
            f"缺少必要字段：{missing_fields}"
        )

    if not ambiguity_result["passed"]:
        matched_terms = "、".join(
            ambiguity_result["matched_terms"]
        )
        issues.append(
            f"包含模糊表达：{matched_terms}"
        )

    suggested_priority = priority_result[
        "suggested_priority"
    ]

    priority_consistent = (
        priority is not None
        and priority == suggested_priority
    )

    if priority is not None and not priority_consistent:
        issues.append(
            f"当前优先级为 {priority}，"
            f"建议优先级为 {suggested_priority}"
        )

    passed = (
        completeness_result["passed"]
        and ambiguity_result["passed"]
        and priority_consistent
    )

    return {
        "passed": passed,
        "current_priority": priority,
        "suggested_priority": suggested_priority,
        "priority_consistent": priority_consistent,
        "issues": issues,
        "tool_results": {
            "completeness": completeness_result,
            "ambiguity": ambiguity_result,
            "priority": priority_result,
        },
    }