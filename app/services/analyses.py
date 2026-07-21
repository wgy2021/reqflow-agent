import hashlib
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    RequirementAnalysis,
    RequirementAnalysisCache,
)


ANALYSIS_CACHE_VERSION = "v2"


def build_requirement_fingerprint(
    title: str,
    content: str,
    priority: int | None,
    knowledge_context: str = "",
) -> str:
    """根据需求内容生成稳定的 SHA-256 指纹。"""

    fingerprint_data = {
        "cache_version": ANALYSIS_CACHE_VERSION,
        "title": title,
        "content": content,
        "priority": priority,
        "knowledge_context": knowledge_context.strip(),
    }

    normalized_data = json.dumps(
        fingerprint_data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        normalized_data.encode("utf-8")
    ).hexdigest()


def get_cached_analysis(
    db: Session,
    requirement_id: int,
    fingerprint: str,
) -> RequirementAnalysis | None:
    """指纹相同时，返回之前保存的分析记录。"""

    cache_entry = db.get(
        RequirementAnalysisCache,
        requirement_id,
    )

    if cache_entry is None:
        return None

    if cache_entry.fingerprint != fingerprint:
        return None

    return db.get(
        RequirementAnalysis,
        cache_entry.analysis_id,
    )


def create_analysis(
    db: Session,
    requirement_id: int,
    analysis_result: dict[str, Any],
    fingerprint: str,
) -> RequirementAnalysis:
    """保存分析结果，并更新该需求的缓存索引。"""

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
        knowledge_references=analysis_result.get(
            "knowledge_references",
            [],
        ),
        final_report=analysis_result["final_report"],
        llm_fallback_used=analysis_result[
            "llm_fallback_used"
        ],
        llm_error=analysis_result["llm_error"],
    )

    db.add(db_analysis)

    # 先执行 SQL，以便获得新分析记录的 id。
    db.flush()

    cache_entry = db.get(
        RequirementAnalysisCache,
        requirement_id,
    )

    if cache_entry is None:
        cache_entry = RequirementAnalysisCache(
            requirement_id=requirement_id,
            fingerprint=fingerprint,
            analysis_id=db_analysis.id,
        )
        db.add(cache_entry)

    else:
        cache_entry.fingerprint = fingerprint
        cache_entry.analysis_id = db_analysis.id

    db.commit()
    db.refresh(db_analysis)

    return db_analysis


def analysis_to_result(
    analysis: RequirementAnalysis,
    cache_hit: bool,
) -> dict[str, Any]:
    """将数据库分析记录转换为接口响应字典。"""

    return {
        "passed": analysis.passed,
        "planned_tools": analysis.planned_tools,
        "current_priority": analysis.current_priority,
        "suggested_priority": analysis.suggested_priority,
        "priority_consistent": analysis.priority_consistent,
        "issues": analysis.issues,
        "tool_results": analysis.tool_results,
        "knowledge_references": (
            analysis.knowledge_references
        ),
        "final_report": analysis.final_report,
        "llm_fallback_used": analysis.llm_fallback_used,
        "llm_error": analysis.llm_error,
        "cache_hit": cache_hit,
    }


def list_analyses(
    db: Session,
    requirement_id: int,
    limit: int,
    offset: int,
) -> list[RequirementAnalysis]:
    """分页查询某条需求的历史分析记录。"""

    statement = (
        select(RequirementAnalysis)
        .where(
            RequirementAnalysis.requirement_id
            == requirement_id
        )
        .order_by(RequirementAnalysis.id.desc())
        .offset(offset)
        .limit(limit)
    )

    return list(
        db.scalars(statement).all()
    )

    return list(
        db.scalars(statement).all()
    )