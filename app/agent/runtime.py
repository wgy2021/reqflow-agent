import json
from typing import Any

from app.agent.llm.base import LLMClient
from app.agent.registry import execute_tool
from app.agent.state import AgentState


class AgentRuntime:
    """驱动 Agent 状态和模型响应。"""

    def __init__(
        self,
        llm_client: LLMClient,
        max_steps: int = 5,
    ) -> None:
        if max_steps <= 0:
            raise ValueError(
                "max_steps must be greater than zero"
            )

        self.llm_client = llm_client
        self.max_steps = max_steps

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

        available_tools = tools or []

        while state.step_count < self.max_steps:
            response = self.llm_client.generate_response(
                messages=state.messages,
                tools=available_tools,
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

                for tool_call in response.message.tool_calls:
                    arguments = json.loads(
                        tool_call.function.arguments
                    )

                    if not isinstance(arguments, dict):
                        raise ValueError(
                            "Tool arguments must be a JSON object"
                        )

                    result = execute_tool(
                        tool_call.function.name,
                        **arguments,
                    )

                    state.tool_results.append(
                        {
                            "tool_call_id": tool_call.id,
                            "tool_name": (
                                tool_call.function.name
                            ),
                            "result": result,
                        }
                    )

                    state.messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_call.function.name,
                            "content": json.dumps(
                                result,
                                ensure_ascii=False,
                            ),
                        }
                    )

                continue

            if not response.message.content:
                state.status = "failed"
                state.error = (
                    "Model returned neither tool calls "
                    "nor a final answer"
                )
                return state

            state.status = "completed"
            state.final_answer = (
                response.message.content
            )
            return state

        state.status = "max_steps_exceeded"
        state.error = "Agent exceeded maximum steps"

        return state