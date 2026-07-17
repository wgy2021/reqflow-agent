from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Response,
    status,
)
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import Requirement


class RequirementCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=100,
    )
    content: str = Field(
        min_length=1,
        max_length=5000,
    )
    priority: int = Field(
        ge=1,
        le=3,
    )


class RequirementUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    content: str | None = Field(
        default=None,
        min_length=1,
        max_length=5000,
    )
    priority: int | None = Field(
        default=None,
        ge=1,
        le=3,
    )


class RequirementResponse(BaseModel):
    id: int
    title: str
    content: str
    priority: int

    model_config = {
        "from_attributes": True,
    }


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="ReqFlow Agent API",
    version="0.1.0",
)


@app.get(
    "/health",
    tags=["system"],
)
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "reqflow-agent",
        "environment": "development",
    }


@app.post(
    "/requirements",
    response_model=RequirementResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["requirements"],
)
def create_requirement(
    requirement: RequirementCreate,
    db: Session = Depends(get_db),
) -> Requirement:
    db_requirement = Requirement(
        title=requirement.title,
        content=requirement.content,
        priority=requirement.priority,
    )

    db.add(db_requirement)
    db.commit()
    db.refresh(db_requirement)

    return db_requirement


@app.get(
    "/requirements",
    response_model=list[RequirementResponse],
    tags=["requirements"],
)
def list_requirements(
    priority: int | None = Query(
        default=None,
        ge=1,
        le=3,
    ),
    db: Session = Depends(get_db),
) -> list[Requirement]:
    statement = select(Requirement)

    if priority is not None:
        statement = statement.where(
            Requirement.priority == priority
        )

    return list(
        db.scalars(statement).all()
    )


@app.get(
    "/requirements/{requirement_id}",
    response_model=RequirementResponse,
    tags=["requirements"],
)
def get_requirement(
    requirement_id: int,
    db: Session = Depends(get_db),
) -> Requirement:
    db_requirement = db.get(
        Requirement,
        requirement_id,
    )

    if db_requirement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found",
        )

    return db_requirement


@app.patch(
    "/requirements/{requirement_id}",
    response_model=RequirementResponse,
    tags=["requirements"],
)
def update_requirement(
    requirement_id: int,
    requirement_update: RequirementUpdate,
    db: Session = Depends(get_db),
) -> Requirement:
    db_requirement = db.get(
        Requirement,
        requirement_id,
    )

    if db_requirement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found",
        )

    update_data = requirement_update.model_dump(
        exclude_unset=True,
    )

    for field_name, field_value in update_data.items():
        setattr(
            db_requirement,
            field_name,
            field_value,
        )

    db.commit()
    db.refresh(db_requirement)

    return db_requirement


@app.delete(
    "/requirements/{requirement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["requirements"],
)
def delete_requirement(
    requirement_id: int,
    db: Session = Depends(get_db),
) -> Response:
    db_requirement = db.get(
        Requirement,
        requirement_id,
    )

    if db_requirement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found",
        )

    db.delete(db_requirement)
    db.commit()

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )