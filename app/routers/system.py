import os

import app.agent.tools  # 触发 Agent 工具注册
from fastapi import APIRouter

from app.agent.registry import list_tools
from app.config import settings
from app.schemas import SystemInfoResponse


router = APIRouter(
    prefix="/system",
    tags=["system"],
)


@router.get(
    "/info",
    response_model=SystemInfoResponse,
)
def get_system_info() -> SystemInfoResponse:
    registered_tools = list_tools()

    database_url = os.getenv(
        "DATABASE_URL",
        "sqlite:///./reqflow.db",
    )
    database_type = database_url.split(
        ":",
        maxsplit=1,
    )[0].split(
        "+",
        maxsplit=1,
    )[0]

    tool_names = [
        tool["name"]
        for tool in registered_tools
    ]

    return SystemInfoResponse(
        service="reqflow-agent",
        version="0.1.0",
        environment=os.getenv(
            "APP_ENV",
            "development",
        ),
        llm_provider=settings.llm_provider,
        llm_model=settings.llm_model,
        database_type=database_type,
        tool_count=len(tool_names),
        tools=tool_names,
        cache_version="v1",
    )