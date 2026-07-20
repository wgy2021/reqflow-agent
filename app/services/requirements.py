from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import (
    Requirement,
    RequirementAnalysis,
    RequirementAnalysisCache,
)
from app.schemas import (
    RequirementCreate,
    RequirementUpdate,
)


def create_requirement(
    db: Session,
    requirement: RequirementCreate,
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


def list_requirements(
    db: Session,
    priority: int | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[Requirement]:
    statement = (
        select(Requirement)
        .order_by(Requirement.id.asc())
        .offset(offset)
        .limit(limit)
    )

    if priority is not None:
        statement = statement.where(
            Requirement.priority == priority
        )

    return list(
        db.scalars(statement).all()
    )

def get_requirement(
    db: Session,
    requirement_id: int,
) -> Requirement | None:
    return db.get(
        Requirement,
        requirement_id,
    )


def update_requirement(
    db: Session,
    db_requirement: Requirement,
    requirement_update: RequirementUpdate,
) -> Requirement:
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


def delete_requirement(
    db: Session,
    db_requirement: Requirement,
) -> None:
    """删除需求以及关联的分析历史和缓存记录。"""

    requirement_id = db_requirement.id

    # 缓存同时关联需求和分析记录，因此必须先删除。
    db.execute(
        delete(RequirementAnalysisCache).where(
            RequirementAnalysisCache.requirement_id
            == requirement_id
        )
    )

    # 再删除该需求的全部分析历史。
    db.execute(
        delete(RequirementAnalysis).where(
            RequirementAnalysis.requirement_id
            == requirement_id
        )
    )

    # 最后删除需求本身。
    db.delete(db_requirement)
    db.commit()