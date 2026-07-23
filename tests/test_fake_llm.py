from app.agent.llm import FakeLLMClient
from app.agent.messages import ModelResponse


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

def test_fake_llm_returns_scripted_native_tool_call() -> None:
    expected_response = ModelResponse.model_validate(
        {
            "model": "fake-model",
            "finish_reason": "tool_calls",
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_001",
                        "type": "function",
                        "function": {
                            "name": "ambiguity_check",
                            "arguments": (
                                '{"content":"系统应尽快响应"}'
                            ),
                        },
                    }
                ],
            },
        }
    )

    client = FakeLLMClient(
        scripted_responses=[expected_response],
    )

    response = client.generate_response(
        messages=[
            {
                "role": "user",
                "content": "检查这个需求",
            }
        ],
        tools=[],
    )

    assert response == expected_response
    assert (
        response.message.tool_calls[0].function.name
        == "ambiguity_check"
    )

def test_fake_llm_returns_responses_in_order() -> None:
    tool_response = ModelResponse.model_validate(
        {
            "finish_reason": "tool_calls",
            "message": {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "call_001",
                        "type": "function",
                        "function": {
                            "name": "completeness_check",
                            "arguments": (
                                '{"title":"登录","content":"用户登录"}'
                            ),
                        },
                    }
                ],
            },
        }
    )

    final_response = ModelResponse.model_validate(
        {
            "finish_reason": "stop",
            "message": {
                "role": "assistant",
                "content": "需求分析完成。",
            },
        }
    )

    client = FakeLLMClient(
        scripted_responses=[
            tool_response,
            final_response,
        ],
    )

    first_response = client.generate_response(
        messages=[],
        tools=[],
    )
    second_response = client.generate_response(
        messages=[],
        tools=[],
    )

    assert first_response.finish_reason == "tool_calls"
    assert (
        first_response.message.tool_calls[0].function.name
        == "completeness_check"
    )
    assert second_response.finish_reason == "stop"
    assert second_response.message.content == "需求分析完成。"