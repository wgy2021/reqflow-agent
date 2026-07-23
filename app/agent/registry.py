from pydantic import BaseModel
from collections.abc import Callable
from typing import Any
from app.agent.tool_spec import ToolSpec


ToolFunction = Callable[..., dict[str, Any]]

_tool_registry: dict[str, ToolSpec] = {}


def register_tool(
    name: str,
    description: str,
    input_model: type[BaseModel],
    output_model: type[BaseModel],
) -> Callable[[ToolFunction], ToolFunction]:
    """把函数注册为 Agent 可以调用的工具。"""

    def decorator(func: ToolFunction) -> ToolFunction:
        if name in _tool_registry:
            raise ValueError(
                f"Tool already registered: {name}"
            )

        _tool_registry[name] = ToolSpec(
            name=name,
            description=description,
            input_model=input_model,
            output_model=output_model,
            handler=func,
        )

        return func

    return decorator


def list_tools() -> list[dict[str, str]]:
    """返回所有已注册工具的名称和描述。"""

    return [
        {
            "name": tool.name,
            "description": tool.description,
        }
        for tool in _tool_registry.values()
    ]

def get_tool_spec(name: str) -> ToolSpec:
    """根据工具名称获取完整的 ToolSpec。"""

    tool = _tool_registry.get(name)

    if tool is None:
        raise KeyError(
            f"Tool not found: {name}"
        )

    return tool

def get_tool(name: str) -> ToolFunction:
    """根据工具名称获取对应的处理函数。"""

    return get_tool_spec(name).handler

def execute_tool(
    name: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """校验输入参数并执行工具。"""

    tool_spec = get_tool_spec(name)

    validated_input = tool_spec.input_model.model_validate(
        kwargs
    )

    result = tool_spec.handler(
        **validated_input.model_dump()
    )

    if not isinstance(result, dict):
        raise TypeError(
            f"Tool must return a dict: {name}"
        )

    validated_output = tool_spec.output_model.model_validate(
        result
    )

    return validated_output.model_dump()