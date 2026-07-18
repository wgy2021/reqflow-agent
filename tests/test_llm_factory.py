import pytest

import app.agent.llm.factory as factory_module
from app.agent.llm import (
    FakeLLMClient,
    OpenAICompatibleLLMClient,
    get_llm_client,
)
from app.config import Settings


def test_factory_creates_fake_llm_client() -> None:
    client = get_llm_client("fake")

    assert isinstance(
        client,
        FakeLLMClient,
    )


def test_factory_creates_openai_compatible_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    test_settings = Settings(
        llm_provider="openai_compatible",
        llm_api_key="test-key",
        llm_base_url="https://example.com/v1",
        llm_model="test-model",
    )

    monkeypatch.setattr(
        factory_module,
        "settings",
        test_settings,
    )

    client = get_llm_client()

    assert isinstance(
        client,
        OpenAICompatibleLLMClient,
    )
    assert client.api_key == "test-key"
    assert client.base_url == "https://example.com/v1"
    assert client.model == "test-model"


def test_factory_requires_api_key_for_openai_compatible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    test_settings = Settings(
        llm_provider="openai_compatible",
        llm_api_key=None,
        llm_base_url="https://example.com/v1",
        llm_model="test-model",
    )

    monkeypatch.setattr(
        factory_module,
        "settings",
        test_settings,
    )

    with pytest.raises(
        ValueError,
        match=(
            "LLM_API_KEY is required for "
            "openai_compatible provider"
        ),
    ):
        get_llm_client()


def test_factory_requires_base_url_for_openai_compatible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    test_settings = Settings(
        llm_provider="openai_compatible",
        llm_api_key="test-key",
        llm_base_url=None,
        llm_model="test-model",
    )

    monkeypatch.setattr(
        factory_module,
        "settings",
        test_settings,
    )

    with pytest.raises(
        ValueError,
        match=(
            "LLM_BASE_URL is required for "
            "openai_compatible provider"
        ),
    ):
        get_llm_client()


def test_factory_requires_model_for_openai_compatible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    test_settings = Settings(
        llm_provider="openai_compatible",
        llm_api_key="test-key",
        llm_base_url="https://example.com/v1",
        llm_model=None,
    )

    monkeypatch.setattr(
        factory_module,
        "settings",
        test_settings,
    )

    with pytest.raises(
        ValueError,
        match=(
            "LLM_MODEL is required for "
            "openai_compatible provider"
        ),
    ):
        get_llm_client()


def test_factory_rejects_unsupported_provider() -> None:
    with pytest.raises(
        ValueError,
        match="Unsupported LLM provider: unknown",
    ):
        get_llm_client("unknown")