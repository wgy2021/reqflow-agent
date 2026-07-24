from datetime import datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import (
    Session,
    sessionmaker,
)
from sqlalchemy.pool import StaticPool

from app.agent.run_repository import (
    AgentRunRepository,
)
from app.agent.state import AgentState
from app.database import Base
from app.models import AgentRunRecord


test_engine = create_engine(
    "sqlite://",
    connect_args={
        "check_same_thread": False,
    },
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture()
def db() -> Session:
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    with TestingSessionLocal() as session:
        yield session


def test_save_and_get_agent_run(
    db: Session,
) -> None:
    repository = AgentRunRepository(db)

    state = AgentState(
        status="waiting_approval",
        step_count=1,
    )

    repository.save(
        state=state,
        max_steps=5,
    )

    restored_state = repository.get(
        state.run_id
    )

    assert restored_state is not None
    assert restored_state == state
    assert (
        repository.get_max_steps(state.run_id)
        == 5
    )


def test_save_updates_existing_agent_run(
    db: Session,
) -> None:
    repository = AgentRunRepository(db)

    state = AgentState()

    repository.save(
        state=state,
        max_steps=5,
    )

    completed_state = state.model_copy(
        update={
            "status": "completed",
            "step_count": 2,
            "final_answer": "需求分析完成。",
        }
    )

    repository.save(
        state=completed_state,
        max_steps=8,
    )

    records = db.scalars(
        select(AgentRunRecord)
    ).all()

    restored_state = repository.get(
        state.run_id
    )

    assert len(records) == 1
    assert restored_state == completed_state
    assert (
        repository.get_max_steps(state.run_id)
        == 8
    )


def test_list_agent_runs_newest_first(
    db: Session,
) -> None:
    repository = AgentRunRepository(db)

    first_state = AgentState(
        final_answer="第一次运行",
    )
    second_state = AgentState(
        final_answer="第二次运行",
    )

    repository.save(
        state=first_state,
        max_steps=5,
    )

    first_record = db.get(
        AgentRunRecord,
        first_state.run_id,
    )
    assert first_record is not None
    first_record.created_at = datetime(
        2026,
        1,
        1,
    )
    db.commit()

    repository.save(
        state=second_state,
        max_steps=5,
    )

    second_record = db.get(
        AgentRunRecord,
        second_state.run_id,
    )
    assert second_record is not None
    second_record.created_at = datetime(
        2026,
        1,
        2,
    )
    db.commit()

    states = repository.list_all()

    assert [
        state.run_id
        for state in states
    ] == [
        second_state.run_id,
        first_state.run_id,
    ]