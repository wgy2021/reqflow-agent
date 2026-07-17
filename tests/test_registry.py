import pytest

from app.agent import registry
from app.agent.tools.completeness import check_completeness
from app.agent.tools.ambiguity import check_ambiguity
from app.agent.tools.priority import suggest_priority


@pytest.fixture(autouse=True)
def isolate_tool_registry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """每个测试使用独立注册表，避免测试互相影响。"""
    monkeypatch.setattr(
        registry,
        "_tool_registry",
        {},
    )


def test_register_list_and_execute_tool() -> None:
    @registry.register_tool(
        name="sample_tool",
        description="测试工具",
    )
    def sample_tool(value: int) -> dict[str, int]:
        return {
            "value": value,
        }

    assert registry.list_tools() == [
        {
            "name": "sample_tool",
            "description": "测试工具",
        }
    ]

    result = registry.execute_tool(
        "sample_tool",
        value=10,
    )

    assert result == {
        "value": 10,
    }


def test_duplicate_tool_name_raises_error() -> None:
    @registry.register_tool(
        name="duplicate_tool",
        description="第一个工具",
    )
    def first_tool() -> dict[str, bool]:
        return {
            "ok": True,
        }

    with pytest.raises(
        ValueError,
        match="Tool already registered: duplicate_tool",
    ):

        @registry.register_tool(
            name="duplicate_tool",
            description="第二个工具",
        )
        def second_tool() -> dict[str, bool]:
            return {
                "ok": False,
            }


def test_get_missing_tool_raises_error() -> None:
    with pytest.raises(
        KeyError,
        match="Tool not found: missing_tool",
    ):
        registry.get_tool("missing_tool")


def test_tool_must_return_dictionary() -> None:
    @registry.register_tool(
        name="invalid_tool",
        description="返回值错误的工具",
    )
    def invalid_tool():
        return "invalid result"

    with pytest.raises(
        TypeError,
        match="Tool must return a dict: invalid_tool",
    ):
        registry.execute_tool("invalid_tool")


def test_completeness_check() -> None:
    incomplete_result = check_completeness(
        title="",
        content="用户可以登录系统",
        priority=1,
    )

    assert incomplete_result == {
        "tool": "completeness_check",
        "passed": False,
        "missing_fields": ["title"],
    }

    complete_result = check_completeness(
        title="用户登录",
        content="用户可以使用账号密码登录系统",
        priority=1,
    )

    assert complete_result == {
        "tool": "completeness_check",
        "passed": True,
        "missing_fields": [],
    }

def test_ambiguity_check_detects_ambiguous_terms() -> None:
    result = check_ambiguity(
        content="系统应尽快向用户返回友好的提示信息",
    )

    assert result == {
        "tool": "ambiguity_check",
        "passed": False,
        "matched_terms": [
            "尽快",
            "友好",
        ],
    }


def test_ambiguity_check_passes_clear_requirement() -> None:
    result = check_ambiguity(
        content="系统必须在2秒内返回错误码和错误信息",
    )

    assert result == {
        "tool": "ambiguity_check",
        "passed": True,
        "matched_terms": [],
    }
def test_priority_suggestion_returns_high_priority() -> None:
    result = suggest_priority(
        title="登录故障",
        content="用户无法登录系统",
    )

    assert result == {
        "tool": "priority_suggestion",
        "suggested_priority": 1,
        "matched_keywords": [
            "故障",
            "无法登录",
        ],
        "reason": "需求包含安全、故障或核心功能不可用相关关键词",
    }


def test_priority_suggestion_returns_medium_priority() -> None:
    result = suggest_priority(
        title="接口性能优化",
        content="接口响应延迟较高",
    )

    assert result == {
        "tool": "priority_suggestion",
        "suggested_priority": 2,
        "matched_keywords": [
            "性能",
            "延迟",
        ],
        "reason": "需求包含性能、异常或体验问题相关关键词",
    }


def test_priority_suggestion_returns_low_priority() -> None:
    result = suggest_priority(
        title="修改页面文案",
        content="调整首页提示语",
    )

    assert result == {
        "tool": "priority_suggestion",
        "suggested_priority": 3,
        "matched_keywords": [],
        "reason": "未发现高风险或紧急问题关键词",
    }