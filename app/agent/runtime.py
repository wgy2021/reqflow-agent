import json
from typing import Any

from app.agent.llm.base import LLMClient
from app.agent.registry import execute_tool, get_tool_spec
from app.agent.state import AgentState
from pydantic import ValidationError

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
        user_message: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        state: AgentState | None = None,
    ) -> AgentState:
        if state is None:
            if user_message is None:
                raise ValueError(
                    "user_message is required for a new run"
                )

            state = AgentState(
                messages=[
                    {
                        "role": "user",
                        "content": user_message,
                    }
                ]
            )
        elif state.status != "running":
            raise ValueError(
                "Agent state must be running"
            )

        available_tools = tools or []
        seen_tool_calls: set[tuple[str, str]] = set()

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

                approval_tools: list[str] = []

                for tool_call in response.message.tool_calls:
                    tool_name = tool_call.function.name

                    try:
                        tool_spec = get_tool_spec(tool_name)
                    except KeyError:
                        state.status = "failed"
                        state.error = f"Unknown tool: {tool_name}"
                        return state

                    if tool_spec.requires_approval:
                        approval_tools.append(tool_name)

                if approval_tools:
                    state.pending_tool_calls.extend(
                        response.message.tool_calls
                    )
                    state.status = "waiting_approval"
                    state.error = (
                            "Approval required for tool: "
                            + ", ".join(approval_tools)
                    )
                    return state

                for tool_call in response.message.tool_calls:
                    try:
                        arguments = json.loads(
                            tool_call.function.arguments
                        )
                    except json.JSONDecodeError:
                        state.status = "failed"
                        state.error = (
                            "Invalid JSON arguments for tool: "
                            f"{tool_call.function.name}"
                        )
                        return state

                    if not isinstance(arguments, dict):
                        state.status = "failed"
                        state.error = (
                            "Tool arguments must be a JSON object"
                        )
                        return state
                    call_signature = (
                        tool_call.function.name,
                        json.dumps(
                            arguments,
                            ensure_ascii=False,
                            sort_keys=True,
                        ),
                    )

                    if call_signature in seen_tool_calls:
                        state.status = "failed"
                        state.error = (
                            "Duplicate tool call detected: "
                            f"{tool_call.function.name}"
                        )
                        return state

                    seen_tool_calls.add(call_signature)

                    try:
                        result = execute_tool(
                            tool_call.function.name,
                            **arguments,
                        )
                    except KeyError:
                        state.status = "failed"
                        state.error = (
                            f"Unknown tool: {tool_call.function.name}"
                        )
                        return state
                    except ValidationError:
                        state.status = "failed"
                        state.error = (
                            "Invalid arguments for tool: "
                            f"{tool_call.function.name}"
                        )
                        return state
                    except Exception as exc:
                        state.status = "failed"
                        state.error = (
                            "Tool execution failed: "
                            f"{tool_call.function.name} "
                            f"({type(exc).__name__})"
                        )
                        return state
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
    def resolve_approval(
        self,
        state: AgentState,
        approved: bool,
    ) -> AgentState:
        """处理待审批工具调用。"""

        if state.status != "waiting_approval":
            raise ValueError(
                "Agent is not waiting for approval"
            )

        if not state.pending_tool_calls:
            raise ValueError(
                "Agent has no pending tool calls"
            )

        if not approved:
            state.pending_tool_calls.clear()
            state.status = "failed"
            state.error = "Tool approval rejected"
            return state

        pending_tool_calls = list(
            state.pending_tool_calls
        )
        state.pending_tool_calls.clear()
        state.status = "running"
        state.error = None

        for tool_call in pending_tool_calls:
            try:
                arguments = json.loads(
                    tool_call.function.arguments
                )
            except json.JSONDecodeError:
                state.status = "failed"
                state.error = (
                    "Invalid JSON arguments for tool: "
                    f"{tool_call.function.name}"
                )
                return state

            if not isinstance(arguments, dict):
                state.status = "failed"
                state.error = (
                    "Tool arguments must be a JSON object"
                )
                return state

            try:
                result = execute_tool(
                    tool_call.function.name,
                    **arguments,
                )
            except KeyError:
                state.status = "failed"
                state.error = (
                    f"Unknown tool: "
                    f"{tool_call.function.name}"
                )
                return state
            except ValidationError:
                state.status = "failed"
                state.error = (
                    "Invalid arguments for tool: "
                    f"{tool_call.function.name}"
                )
                return state
            except Exception as exc:
                state.status = "failed"
                state.error = (
                    "Tool execution failed: "
                    f"{tool_call.function.name} "
                    f"({type(exc).__name__})"
                )
                return state

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

        return state
    def resume_after_approval(
        self,
        state: AgentState,
        approved: bool,
        tools: list[dict[str, Any]] | None = None,
    ) -> AgentState:
        """处理审批并继续原来的 Agent 运行。"""

        state = self.resolve_approval(
            state=state,
            approved=approved,
        )

        if state.status != "running":
            return state

        return self.run(
            tools=tools,
            state=state,
        )