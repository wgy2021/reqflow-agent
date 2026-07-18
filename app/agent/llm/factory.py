from app.agent.llm.base import LLMClient
from app.agent.llm.fake import FakeLLMClient
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

    raise ValueError(
        f"Unsupported LLM provider: {selected_provider}"
    )