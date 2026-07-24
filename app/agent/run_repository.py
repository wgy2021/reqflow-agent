from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent.state import AgentState
from app.models import AgentRunRecord


class AgentRunRepository:
    """使用数据库持久化 Agent 运行状态。"""

    def __init__(
        self,
        db: Session,
    ) -> None:
        self._db = db

    def save(
        self,
        state: AgentState,
        max_steps: int,
    ) -> None:
        record = self._db.get(
            AgentRunRecord,
            state.run_id,
        )

        now = datetime.now()
        state_json = state.model_dump(
            mode="json",
        )

        if record is None:
            record = AgentRunRecord(
                run_id=state.run_id,
                status=state.status,
                step_count=state.step_count,
                max_steps=max_steps,
                state_json=state_json,
                created_at=now,
                updated_at=now,
            )
            self._db.add(record)
        else:
            record.status = state.status
            record.step_count = state.step_count
            record.max_steps = max_steps
            record.state_json = state_json
            record.updated_at = now

        self._db.commit()

    def get(
        self,
        run_id: str,
    ) -> AgentState | None:
        record = self._db.get(
            AgentRunRecord,
            run_id,
        )

        if record is None:
            return None

        return AgentState.model_validate(
            record.state_json
        )

    def list_all(self) -> list[AgentState]:
        statement = (
            select(AgentRunRecord)
            .order_by(
                AgentRunRecord.created_at.desc()
            )
        )

        records = self._db.scalars(
            statement
        ).all()

        return [
            AgentState.model_validate(
                record.state_json
            )
            for record in records
        ]

    def get_max_steps(
        self,
        run_id: str,
    ) -> int | None:
        record = self._db.get(
            AgentRunRecord,
            run_id,
        )

        if record is None:
            return None

        return record.max_steps