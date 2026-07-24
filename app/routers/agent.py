import app.agent.tools  # noqa: F401
from fastapi import (
    APIRouter,
    Depends,
    status,
)

from app.agent.api_schemas import (
    AgentRunRequest,
    AgentRunResponse,
)
from app.agent.llm import (
    LLMClient,
    get_llm_client,
)
from app.agent.registry import list_function_tools
from app.agent.runtime import AgentRuntime


router = APIRouter(
    prefix="/agent",
    tags=["agent"],
)


def provide_llm_client() -> LLMClient:
    """为 Agent API 提供模型客户端。"""

    return get_llm_client()


@router.post(
    "/runs",
    response_model=AgentRunResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_agent_run(
    request: AgentRunRequest,
    llm_client: LLMClient = Depends(
        provide_llm_client
    ),
) -> AgentRunResponse:
    runtime = AgentRuntime(
        llm_client=llm_client,
        max_steps=request.max_steps,
    )

    state = runtime.run(
        user_message=request.message,
        tools=list_function_tools(),
    )

    return AgentRunResponse.model_validate(state)