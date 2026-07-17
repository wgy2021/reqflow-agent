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
    description="检测需求内容中缺乏明确标准的模糊表达",
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