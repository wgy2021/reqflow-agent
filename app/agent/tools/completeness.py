from typing import Any
from app.agent.schemas import (
    CompletenessToolInput,
    CompletenessToolResult,
)
from app.agent.registry import register_tool


@register_tool(
    name="completeness_check",
    description="检查需求标题、内容和优先级是否完整",
    input_model=CompletenessToolInput,
    output_model=CompletenessToolResult,
)
def check_completeness(
    title: str,
    content: str,
    priority: int | None,
) -> dict[str, Any]:
    missing_fields: list[str] = []

    if not title.strip():
        missing_fields.append("title")

    if not content.strip():
        missing_fields.append("content")

    if priority is None:
        missing_fields.append("priority")

    return {
        "tool": "completeness_check",
        "passed": len(missing_fields) == 0,
        "missing_fields": missing_fields,
    }