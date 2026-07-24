from app.agent.state import AgentState


class AgentRunStore:
    """暂存在内存中的 Agent 运行状态。"""

    def __init__(self) -> None:
        self._runs: dict[str, AgentState] = {}

    def save(
        self,
        state: AgentState,
    ) -> None:
        self._runs[state.run_id] = state

    def get(
        self,
        run_id: str,
    ) -> AgentState | None:
        return self._runs.get(run_id)

    def clear(self) -> None:
        self._runs.clear()


agent_run_store = AgentRunStore()