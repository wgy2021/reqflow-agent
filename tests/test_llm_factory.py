import pytest

from app.agent.llm import (
    FakeLLMClient,
    get_llm_client,
)


def test_factory_creates_fake_llm_client() -> None:
    client = get_llm_client("fake")

    assert isinstance(
        client,
        FakeLLMClient,
    )


def test_factory_rejects_unsupported_provider() -> None:
    with pytest.raises(
        ValueError,
        match="Unsupported LLM provider: unknown",
    ):
        get_llm_client("unknown")