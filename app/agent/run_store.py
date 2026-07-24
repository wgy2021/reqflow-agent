from app.agent.state import AgentState


class AgentRunStore:
    """暂存在内存中的 Agent 运行状态。"""

    def __init__(self) -> None:
        self._runs: dict[str, AgentState] = {}
        self._max_steps: dict[str, int] = {}

    def save(
        self,
        state: AgentState,
        max_steps: int,
    ) -> None:
        self._runs[state.run_id] = state
        self._max_steps[state.run_id] = max_steps

    def get(
        self,
        run_id: str,
    ) -> AgentState | None:
        return self._runs.get(run_id)

    def list_all(self) -> list[AgentState]:
        """返回全部 Agent 运行，最新创建的在前。"""

        return list(
            reversed(
                self._runs.values()
            )
        )

    def get_max_steps(
        self,
        run_id: str,
    ) -> int | None:
        return self._max_steps.get(run_id)

    def clear(self) -> None:
        self._runs.clear()
        self._max_steps.clear()


agent_run_store = AgentRunStore()