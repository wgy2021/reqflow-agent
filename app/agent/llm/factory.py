from app.agent.llm.base import LLMClient
from app.agent.llm.fake import FakeLLMClient
from app.agent.llm.openai_compatible import (
    OpenAICompatibleLLMClient,
)
from app.config import settings


def get_llm_client(
    provider: str | None = None,
) -> LLMClient:
    """根据配置创建对应的大模型客户端。"""

    selected_provider = (
        provider or settings.llm_provider
    ).strip().lower()

    if selected_provider == "fake":
        return FakeLLMClient()

    if selected_provider == "openai_compatible":
        if not settings.llm_api_key:
            raise ValueError(
                "LLM_API_KEY is required for "
                "openai_compatible provider"
            )

        if not settings.llm_base_url:
            raise ValueError(
                "LLM_BASE_URL is required for "
                "openai_compatible provider"
            )

        if not settings.llm_model:
            raise ValueError(
                "LLM_MODEL is required for "
                "openai_compatible provider"
            )

        return OpenAICompatibleLLMClient(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            model=settings.llm_model,
        )

    raise ValueError(
        f"Unsupported LLM provider: {selected_provider}"
    )