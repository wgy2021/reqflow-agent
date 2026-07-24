import json

import app.agent.tools  # noqa: F401

from app.agent.llm import (
    OpenAICompatibleLLMClient,
    get_llm_client,
)
from app.agent.registry import list_function_tools
from app.agent.runtime import AgentRuntime


def main() -> None:
    client = get_llm_client()

    if not isinstance(
        client,
        OpenAICompatibleLLMClient,
    ):
        raise RuntimeError(
            "Please set LLM_PROVIDER=openai_compatible"
        )

    runtime = AgentRuntime(
        llm_client=client,
        max_steps=5,
    )

    state = runtime.run(
        user_message=(
            "请必须先调用 completeness_check 工具，"
            "检查下面的需求，然后根据工具结果给出最终结论。"
            "标题：用户登录；"
            "内容：用户可以使用账号密码登录系统；"
            "优先级：1。"
        ),
        tools=list_function_tools(),
    )

    print("status:", state.status)
    print("step_count:", state.step_count)
    print("tool_calls:", len(state.tool_calls))
    print(
        "tool_results:",
        json.dumps(
            state.tool_results,
            ensure_ascii=False,
            indent=2,
        ),
    )
    print("final_answer:", state.final_answer)
    print("error:", state.error)

    if not state.tool_calls:
        raise RuntimeError(
            "The model did not return a tool call"
        )

    if not state.tool_results:
        raise RuntimeError(
            "The requested tool was not executed"
        )

    if state.status != "completed":
        raise RuntimeError(
            f"Agent did not complete: {state.error}"
        )


if __name__ == "__main__":
    main()