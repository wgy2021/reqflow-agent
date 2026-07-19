from typing import Any

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
    def generate_report(
        self,
        title: str,
        content: str,
        priority: int | None,
        planned_tools: list[str],
        tool_results: dict[str, dict[str, Any]],
        issues: list[str],
        passed: bool,
    ) -> str:
        """使用固定规则生成稳定、可测试的分析报告。"""

        status_text = "通过" if passed else "未通过"

        tool_text = (
            "、".join(planned_tools)
            if planned_tools
            else "无"
        )

        issue_text = (
            "；".join(issues)
            if issues
            else "未发现明显问题"
        )

        priority_text = (
            str(priority)
            if priority is not None
            else "未设置"
        )

        return (
            f"需求《{title}》分析{status_text}。"
            f"当前优先级：{priority_text}。"
            f"已执行工具：{tool_text}。"
            f"分析结论：{issue_text}。"
        )