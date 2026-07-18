import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(
    dotenv_path=ENV_FILE,
    override=False,
)


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