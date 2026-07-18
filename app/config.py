import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    llm_provider: str
    llm_api_key: str | None
    llm_base_url: str | None
    llm_model: str | None

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            llm_provider=os.getenv(
                "LLM_PROVIDER",
                "fake",
            ),
            llm_api_key=os.getenv("LLM_API_KEY"),
            llm_base_url=os.getenv("LLM_BASE_URL"),
            llm_model=os.getenv("LLM_MODEL"),
        )


settings = Settings.from_environment()