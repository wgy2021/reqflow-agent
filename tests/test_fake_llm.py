import pytest
from app.agent.llm import FakeLLMClient


AVAILABLE_TOOLS = [
    {
        "name": "completeness_check",
        "description": "检查需求字段是否完整",
    },
    {
        "name": "ambiguity_check",
        "description": "检测需求中的模糊表达",
    },
    {
        "name": "priority_suggestion",
        "description": "建议需求优先级",
    },
]


def test_fake_llm_selects_all_relevant_tools() -> None:
    client = FakeLLMClient()

    planned_tools = client.plan_tools(
        title="登录故障",
        content="系统应尽快解决用户无法登录的问题",
        priority=3,
        available_tools=AVAILABLE_TOOLS,
    )

    assert planned_tools == [
        "completeness_check",
        "ambiguity_check",
        "priority_suggestion",
    ]


def test_fake_llm_selects_only_completeness_for_simple_requirement() -> None:
    client = FakeLLMClient()

    planned_tools = client.plan_tools(
        title="修改页面文案",
        content="将首页按钮文字修改为提交",
        priority=3,
        available_tools=AVAILABLE_TOOLS,
    )

    assert planned_tools == [
        "completeness_check",
    ]


def test_fake_llm_only_selects_available_tools() -> None:
    client = FakeLLMClient()

    available_tools = [
        {
            "name": "completeness_check",
            "description": "检查需求字段是否完整",
        },
        {
            "name": "ambiguity_check",
            "description": "检测需求中的模糊表达",
        },
    ]

    planned_tools = client.plan_tools(
        title="登录故障",
        content="系统应尽快解决用户无法登录的问题",
        priority=3,
        available_tools=available_tools,
    )

    assert planned_tools == [
        "completeness_check",
        "ambiguity_check",
    ]

def test_fake_llm_generates_report() -> None:
    client = FakeLLMClient()

    report = client.generate_report(
        title="登录故障",
        content="系统应尽快解决用户无法登录的问题",
        priority=3,
        planned_tools=[
            "completeness_check",
            "ambiguity_check",
        ],
        tool_results={
            "completeness": {
                "passed": True,
                "missing_fields": [],
            },
            "ambiguity": {
                "passed": False,
                "matched_terms": ["尽快"],
            },
        },
        issues=[
            "包含模糊表达：尽快",
        ],
        passed=False,
    )

    assert report == (
        "需求《登录故障》分析未通过。"
        "当前优先级：3。"
        "已执行工具：completeness_check、ambiguity_check。"
        "分析结论：包含模糊表达：尽快。"
    )

def test_fake_llm_native_tool_call_not_implemented_yet() -> None:
    client = FakeLLMClient()

    with pytest.raises(
        NotImplementedError,
        match="native tool calling",
    ):
        client.generate_response(
            messages=[],
            tools=[],
        )