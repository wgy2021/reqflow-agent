from app.agent.schemas import (
    AmbiguityToolInput,
    AmbiguityToolResult,
)
from typing import Any

from app.agent.registry import register_tool


AMBIGUOUS_TERMS = [
    "尽快",
    "尽量",
    "适当",
    "及时",
    "合理",
    "友好",
    "高效",
    "必要时",
    "相关功能",
]


@register_tool(
    name="ambiguity_check",
    description="检查需求内容中是否包含模糊表达",
    input_model=AmbiguityToolInput,
    output_model=AmbiguityToolResult,
)
def check_ambiguity(
    content: str,
) -> dict[str, Any]:
    matched_terms = [
        term
        for term in AMBIGUOUS_TERMS
        if term in content
    ]

    return {
        "tool": "ambiguity_check",
        "passed": len(matched_terms) == 0,
        "matched_terms": matched_terms,
    }