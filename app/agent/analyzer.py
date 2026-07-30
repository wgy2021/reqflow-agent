from typing import Any

from app.agent.langgraph_runtime import (
    LangGraphAnalysisExecution,
    execute_langgraph_analysis,
)
from app.agent.llm import (
    LLMClient,
    get_llm_client,
)
from app.agent.registry import list_tools
from app.agent.schemas import (
    RequirementAnalysisResponse,
)


TOOL_RESULT_KEYS = {
    "completeness_check": "completeness",
    "ambiguity_check": "ambiguity",
    "priority_suggestion": "priority",
}


def _raise_for_failed_execution(
    execution: LangGraphAnalysisExecution,
) -> None:
    """将 LangGraph 执行失败转换为旧接口可理解的异常。"""

    available_tool_names = {
        tool["name"]
        for tool in list_tools()
    }

    for tool_name in execution.planned_tools:
        if tool_name not in available_tool_names:
            raise ValueError(
                "Planner selected unavailable tool: "
                f"{tool_name}"
            )

    if execution.state.status == "failed":
        raise RuntimeError(
            execution.state.error
            or "LangGraph requirement analysis failed"
        )


def to_requirement_analysis_result(
    execution: LangGraphAnalysisExecution,
) -> dict[str, Any]:
    """将 LangGraph 完整结果转换为旧接口响应结构。"""

    _raise_for_failed_execution(execution)

    tool_results: dict[str, dict[str, Any]] = {}

    for tool_name in execution.planned_tools:
        result_key = TOOL_RESULT_KEYS.get(tool_name)

        if result_key is None:
            raise ValueError(
                f"No result mapping configured for tool: "
                f"{tool_name}"
            )

        raw_result = execution.raw_tool_results.get(
            tool_name
        )

        if raw_result is not None:
            tool_results[result_key] = raw_result

    response = RequirementAnalysisResponse(
        passed=execution.passed,
        planned_tools=execution.planned_tools,
        current_priority=execution.current_priority,
        suggested_priority=execution.suggested_priority,
        priority_consistent=(
            execution.priority_consistent
        ),
        issues=execution.issues,
        tool_results=tool_results,
        final_report=execution.final_report,
        llm_fallback_used=(
            execution.llm_fallback_used
        ),
        llm_error=execution.llm_error,
    )

    result = response.model_dump(
        exclude={
            "knowledge_references",
            "cache_hit",
        },
        exclude_none=False,
    )

    result["tool_results"] = {
        key: value
        for key, value
        in result["tool_results"].items()
        if value is not None
    }

    return result


def analyze_requirement(
    title: str,
    content: str,
    priority: int | None,
    llm_client: LLMClient | None = None,
    knowledge_context: str = "",
) -> dict[str, Any]:
    """通过需求专用 LangGraph 执行分析并返回旧响应结构。"""

    client = llm_client or get_llm_client()

    execution = execute_langgraph_analysis(
        llm_client=client,
        title=title,
        content=content,
        priority=priority,
        knowledge_context=knowledge_context,
    )

    return to_requirement_analysis_result(
        execution
    )
