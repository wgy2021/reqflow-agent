from app.agent.llm.base import LLMClient


class FakeLLMClient(LLMClient):
    """根据简单规则模拟大模型选择工具。"""

    def plan_tools(
        self,
        title: str,
        content: str,
        priority: int | None,
        available_tools: list[dict[str, str]],
    ) -> list[str]:
        available_tool_names = {
            tool["name"]
            for tool in available_tools
        }

        planned_tools: list[str] = []

        # 完整性检查始终执行。
        if "completeness_check" in available_tool_names:
            planned_tools.append("completeness_check")

        ambiguous_terms = [
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

        if (
            "ambiguity_check" in available_tool_names
            and any(
                term in content
                for term in ambiguous_terms
            )
        ):
            planned_tools.append("ambiguity_check")

        priority_keywords = [
            "安全",
            "漏洞",
            "攻击",
            "故障",
            "崩溃",
            "宕机",
            "数据丢失",
            "无法登录",
            "性能",
            "延迟",
            "超时",
            "卡顿",
            "错误",
            "异常",
        ]

        full_text = f"{title} {content}"

        if (
            "priority_suggestion" in available_tool_names
            and any(
                keyword in full_text
                for keyword in priority_keywords
            )
        ):
            planned_tools.append("priority_suggestion")

        return planned_tools