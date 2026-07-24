import app.agent.tools  # noqa: F401
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
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
from app.agent.run_store import (
    AgentRunStore,
    agent_run_store,
)
from app.agent.runtime import AgentRuntime


router = APIRouter(
    prefix="/agent",
    tags=["agent"],
)


def provide_llm_client() -> LLMClient:
    """为 Agent API 提供模型客户端。"""

    return get_llm_client()


def provide_run_store() -> AgentRunStore:
    """为 Agent API 提供运行状态存储。"""

    return agent_run_store


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
    run_store: AgentRunStore = Depends(
        provide_run_store
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

    run_store.save(state)

    return AgentRunResponse.model_validate(state)


@router.get(
    "/runs/{run_id}",
    response_model=AgentRunResponse,
)
def get_agent_run(
    run_id: str,
    run_store: AgentRunStore = Depends(
        provide_run_store
    ),
) -> AgentRunResponse:
    state = run_store.get(run_id)

    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent run not found",
        )

    return AgentRunResponse.model_validate(state)