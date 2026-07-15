from fastapi import FastAPI, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

class RequirementCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1, max_length=5000)
    priority: int = Field(ge=1, le=3)

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

app = FastAPI(
    title="ReqFlow Agent API",
    version="0.1.0",
)

requirements: dict[int, dict] = {}
next_requirement_id = 1

@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "reqflow-agent",
        "environment": "development",
    }

@app.post(
    "/requirements",
    status_code=status.HTTP_201_CREATED,
    tags=["requirements"],
)
def create_requirement(requirement: RequirementCreate) -> dict:
    global next_requirement_id

    requirement_data = {
        "id": next_requirement_id,
        **requirement.model_dump(),
    }

    requirements[next_requirement_id] = requirement_data
    next_requirement_id += 1

    return requirement_data

@app.get(
    "/requirements",
    tags=["requirements"],
)
def list_requirements(
    priority: int | None = Query(
        default=None,
        ge=1,
        le=3,
    ),
) -> list[dict]:
    all_requirements = list(requirements.values())

    if priority is None:
        return all_requirements

    return [
        requirement
        for requirement in all_requirements
        if requirement["priority"] == priority
    ]

@app.get(
    "/requirements/{requirement_id}",
    tags=["requirements"],
)
def get_requirement(requirement_id: int) -> dict:
    requirement = requirements.get(requirement_id)

    if requirement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found",
        )

    return requirement

@app.patch(
    "/requirements/{requirement_id}",
    tags=["requirements"],
)
def update_requirement(
    requirement_id: int,
    requirement_update: RequirementUpdate,
) -> dict:
    stored_requirement = requirements.get(requirement_id)

    if stored_requirement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found",
        )

    update_data = requirement_update.model_dump(
        exclude_unset=True,
    )

    stored_requirement.update(update_data)

    return stored_requirement

@app.delete(
    "/requirements/{requirement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["requirements"],
)
def delete_requirement(requirement_id: int) -> Response:
    if requirement_id not in requirements:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found",
        )

    del requirements[requirement_id]

    return Response(status_code=status.HTTP_204_NO_CONTENT)