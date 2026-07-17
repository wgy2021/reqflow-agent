from app.agent.analyzer import analyze_requirement


def test_analyze_requirement_passes_clear_requirement() -> None:
    result = analyze_requirement(
        title="接口性能优化",
        content="接口必须在2秒内返回响应",
        priority=2,
    )

    assert result["passed"] is True
    assert result["current_priority"] == 2
    assert result["suggested_priority"] == 2
    assert result["priority_consistent"] is True
    assert result["issues"] == []


def test_analyze_requirement_detects_ambiguity() -> None:
    result = analyze_requirement(
        title="优化提示信息",
        content="系统应尽快返回友好的提示信息",
        priority=3,
    )

    assert result["passed"] is False
    assert "尽快" in result[
        "tool_results"
    ]["ambiguity"]["matched_terms"]
    assert "友好" in result[
        "tool_results"
    ]["ambiguity"]["matched_terms"]


def test_analyze_requirement_detects_priority_mismatch() -> None:
    result = analyze_requirement(
        title="登录故障",
        content="用户无法登录系统",
        priority=3,
    )

    assert result["passed"] is False
    assert result["current_priority"] == 3
    assert result["suggested_priority"] == 1
    assert result["priority_consistent"] is False
    assert (
        "当前优先级为 3，建议优先级为 1"
        in result["issues"]
    )