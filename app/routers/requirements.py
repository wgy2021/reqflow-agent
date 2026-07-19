from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Requirement
from app.schemas import (
    RequirementCreate,
    RequirementResponse,
    RequirementUpdate,
)
from app.services import requirements as requirement_service
from app.services import analyses as analysis_service
from typing import Any

from app.agent.analyzer import analyze_requirement
from app.agent.schemas import (
    RequirementAnalysisHistoryResponse,
    RequirementAnalysisResponse,
)


router = APIRouter(
    prefix="/requirements",
    tags=["requirements"],
)


@router.post(
    "",
    response_model=RequirementResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_requirement(
    requirement: RequirementCreate,
    db: Session = Depends(get_db),
) -> Requirement:
    return requirement_service.create_requirement(
        db=db,
        requirement=requirement,
    )


@router.get(
    "",
    response_model=list[RequirementResponse],
)
def list_requirements(
    priority: int | None = Query(
        default=None,
        ge=1,
        le=3,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    db: Session = Depends(get_db),
) -> list[Requirement]:
    return requirement_service.list_requirements(
        db=db,
        priority=priority,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{requirement_id}",
    response_model=RequirementResponse,
)
def get_requirement(
    requirement_id: int,
    db: Session = Depends(get_db),
) -> Requirement:
    db_requirement = requirement_service.get_requirement(
        db=db,
        requirement_id=requirement_id,
    )

    if db_requirement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found",
        )

    return db_requirement


@router.patch(
    "/{requirement_id}",
    response_model=RequirementResponse,
)
def update_requirement(
    requirement_id: int,
    requirement_update: RequirementUpdate,
    db: Session = Depends(get_db),
) -> Requirement:
    db_requirement = requirement_service.get_requirement(
        db=db,
        requirement_id=requirement_id,
    )

    if db_requirement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found",
        )

    return requirement_service.update_requirement(
        db=db,
        db_requirement=db_requirement,
        requirement_update=requirement_update,
    )

@router.post(
    "/{requirement_id}/analyze",
    response_model=RequirementAnalysisResponse,
)
def analyze_requirement_endpoint(
    requirement_id: int,
    force_refresh: bool = Query(
        default=False,
        description="是否忽略缓存并重新执行分析",
    ),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    db_requirement = requirement_service.get_requirement(
        db=db,
        requirement_id=requirement_id,
    )

    if db_requirement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found",
        )

    fingerprint = (
        analysis_service.build_requirement_fingerprint(
            title=db_requirement.title,
            content=db_requirement.content,
            priority=db_requirement.priority,
        )
    )

    cached_analysis = None

    if not force_refresh:
        cached_analysis = analysis_service.get_cached_analysis(
            db=db,
            requirement_id=requirement_id,
            fingerprint=fingerprint,
        )

    if cached_analysis is not None:
        return analysis_service.analysis_to_result(
            analysis=cached_analysis,
            cache_hit=True,
        )

    analysis_result = analyze_requirement(
        title=db_requirement.title,
        content=db_requirement.content,
        priority=db_requirement.priority,
    )

    analysis_result["cache_hit"] = False

    analysis_service.create_analysis(
        db=db,
        requirement_id=requirement_id,
        analysis_result=analysis_result,
        fingerprint=fingerprint,
    )

    return analysis_result

@router.get(
    "/{requirement_id}/analyses",
    response_model=list[
        RequirementAnalysisHistoryResponse
    ],
)
def list_requirement_analyses(
    requirement_id: int,
    db: Session = Depends(get_db),
):
    db_requirement = requirement_service.get_requirement(
        db=db,
        requirement_id=requirement_id,
    )

    if db_requirement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found",
        )

    return analysis_service.list_analyses(
        db=db,
        requirement_id=requirement_id,
    )

@router.delete(
    "/{requirement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_requirement(
    requirement_id: int,
    db: Session = Depends(get_db),
) -> Response:
    db_requirement = requirement_service.get_requirement(
        db=db,
        requirement_id=requirement_id,
    )

    if db_requirement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found",
        )

    requirement_service.delete_requirement(
        db=db,
        db_requirement=db_requirement,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )