from typing import Any

from app.agent.llm.base import LLMClient
from app.agent.state import AgentState


class AgentRuntime:
    """驱动 Agent 状态和模型响应。"""

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    def run(
        self,
        user_message: str,
        tools: list[dict[str, Any]] | None = None,
    ) -> AgentState:
        state = AgentState(
            messages=[
                {
                    "role": "user",
                    "content": user_message,
                }
            ]
        )

        response = self.llm_client.generate_response(
            messages=state.messages,
            tools=tools or [],
        )

        state.step_count += 1
        state.messages.append(
            response.message.model_dump(
                exclude_none=True,
            )
        )

        if response.message.tool_calls:
            state.tool_calls.extend(
                response.message.tool_calls
            )
            return state

        if not response.message.content:
            state.status = "failed"
            state.error = (
                "Model returned neither tool calls "
                "nor a final answer"
            )
            return state

        state.status = "completed"
        state.final_answer = response.message.content

        return state