import pytest

from app.agent.llm import FakeLLMClient


@pytest.fixture(autouse=True)
def use_fake_llm_for_tests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """所有普通测试默认使用 FakeLLM，禁止调用真实 API。"""

    monkeypatch.setattr(
        "app.agent.analyzer.get_llm_client",
        lambda: FakeLLMClient(),
    )