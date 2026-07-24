import app.agent.tools  # noqa: F401
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.agent.api_schemas import (
    AgentApprovalRequest,
    AgentRunRequest,
    AgentRunResponse,
)
from app.agent.llm import (
    LLMClient,
    get_llm_client,
)
from app.agent.registry import list_function_tools
from app.agent.run_repository import AgentRunRepository
from app.agent.runtime import AgentRuntime
from app.database import get_db


router = APIRouter(
    prefix="/agent",
    tags=["agent"],
)


def provide_llm_client() -> LLMClient:
    """为 Agent API 提供模型客户端。"""

    return get_llm_client()


def provide_run_repository(
    db: Session = Depends(get_db),
) -> AgentRunRepository:
    """为 Agent API 提供数据库仓储。"""

    return AgentRunRepository(db)


@router.get(
    "/runs",
    response_model=list[AgentRunResponse],
)
def list_agent_runs(
    run_repository: AgentRunRepository = Depends(
        provide_run_repository
    ),
) -> list[AgentRunResponse]:
    states = run_repository.list_all()

    return [
        AgentRunResponse.model_validate(state)
        for state in states
    ]


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
    run_repository: AgentRunRepository = Depends(
        provide_run_repository
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

    run_repository.save(
        state=state,
        max_steps=request.max_steps,
    )

    return AgentRunResponse.model_validate(state)


@router.get(
    "/runs/{run_id}",
    response_model=AgentRunResponse,
)
def get_agent_run(
    run_id: str,
    run_repository: AgentRunRepository = Depends(
        provide_run_repository
    ),
) -> AgentRunResponse:
    state = run_repository.get(run_id)

    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent run not found",
        )

    return AgentRunResponse.model_validate(state)


@router.post(
    "/runs/{run_id}/approval",
    response_model=AgentRunResponse,
)
def resolve_agent_approval(
    run_id: str,
    approval: AgentApprovalRequest,
    llm_client: LLMClient = Depends(
        provide_llm_client
    ),
    run_repository: AgentRunRepository = Depends(
        provide_run_repository
    ),
) -> AgentRunResponse:
    state = run_repository.get(run_id)

    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent run not found",
        )

    if state.status != "waiting_approval":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Agent run is not waiting for approval"
            ),
        )

    max_steps = run_repository.get_max_steps(
        run_id
    )

    if max_steps is None:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail="Agent run configuration not found",
        )

    runtime = AgentRuntime(
        llm_client=llm_client,
        max_steps=max_steps,
    )

    state = runtime.resume_after_approval(
        state=state,
        approved=approval.approved,
        tools=list_function_tools(),
    )

    run_repository.save(
        state=state,
        max_steps=max_steps,
    )

    return AgentRunResponse.model_validate(state)