from pydantic import BaseModel, ConfigDict, Field


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
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    title: str
    content: str
    priority: int