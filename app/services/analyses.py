from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import RequirementAnalysis


def create_analysis(
    db: Session,
    requirement_id: int,
    analysis_result: dict[str, Any],
) -> RequirementAnalysis:
    """将一次需求分析结果保存到数据库。"""

    db_analysis = RequirementAnalysis(
        requirement_id=requirement_id,
        passed=analysis_result["passed"],
        planned_tools=analysis_result["planned_tools"],
        current_priority=analysis_result["current_priority"],
        suggested_priority=analysis_result[
            "suggested_priority"
        ],
        priority_consistent=analysis_result[
            "priority_consistent"
        ],
        issues=analysis_result["issues"],
        tool_results=analysis_result["tool_results"],
        final_report=analysis_result["final_report"],
        llm_fallback_used=analysis_result[
            "llm_fallback_used"
        ],
        llm_error=analysis_result["llm_error"],
    )

    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)

    return db_analysis


def list_analyses(
    db: Session,
    requirement_id: int,
) -> list[RequirementAnalysis]:
    """查询某条需求的全部历史分析记录。"""

    statement = (
        select(RequirementAnalysis)
        .where(
            RequirementAnalysis.requirement_id
            == requirement_id
        )
        .order_by(RequirementAnalysis.id.desc())
    )

    return list(
        db.scalars(statement).all()
    )