from typing import Any

from app.agent.registry import register_tool


HIGH_PRIORITY_KEYWORDS = [
    "安全",
    "漏洞",
    "攻击",
    "故障",
    "崩溃",
    "宕机",
    "数据丢失",
    "无法登录",
]

MEDIUM_PRIORITY_KEYWORDS = [
    "性能",
    "延迟",
    "超时",
    "卡顿",
    "错误",
    "异常",
]


@register_tool(
    name="priority_suggestion",
    description="根据需求内容中的关键词建议需求优先级",
)
def suggest_priority(
    title: str,
    content: str,
) -> dict[str, Any]:
    text = f"{title} {content}"

    matched_high_keywords = [
        keyword
        for keyword in HIGH_PRIORITY_KEYWORDS
        if keyword in text
    ]

    matched_medium_keywords = [
        keyword
        for keyword in MEDIUM_PRIORITY_KEYWORDS
        if keyword in text
    ]

    if matched_high_keywords:
        suggested_priority = 1
        reason = "需求包含安全、故障或核心功能不可用相关关键词"
        matched_keywords = matched_high_keywords
    elif matched_medium_keywords:
        suggested_priority = 2
        reason = "需求包含性能、异常或体验问题相关关键词"
        matched_keywords = matched_medium_keywords
    else:
        suggested_priority = 3
        reason = "未发现高风险或紧急问题关键词"
        matched_keywords = []

    return {
        "tool": "priority_suggestion",
        "suggested_priority": suggested_priority,
        "matched_keywords": matched_keywords,
        "reason": reason,
    }