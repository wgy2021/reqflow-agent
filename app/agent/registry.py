from collections.abc import Callable
from typing import Any


ToolFunction = Callable[..., dict[str, Any]]

_tool_registry: dict[str, dict[str, Any]] = {}


def register_tool(
    name: str,
    description: str,
) -> Callable[[ToolFunction], ToolFunction]:
    """把函数注册为 Agent 可以调用的工具。"""

    def decorator(func: ToolFunction) -> ToolFunction:
        if name in _tool_registry:
            raise ValueError(
                f"Tool already registered: {name}"
            )

        _tool_registry[name] = {
            "name": name,
            "description": description,
            "function": func,
        }

        return func

    return decorator


def list_tools() -> list[dict[str, str]]:
    """返回所有已注册工具的名称和描述。"""

    return [
        {
            "name": tool["name"],
            "description": tool["description"],
        }
        for tool in _tool_registry.values()
    ]


def get_tool(name: str) -> ToolFunction:
    """根据工具名称获取对应函数。"""

    tool = _tool_registry.get(name)

    if tool is None:
        raise KeyError(
            f"Tool not found: {name}"
        )

    return tool["function"]


def execute_tool(
    name: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """根据名称执行工具。"""

    tool_function = get_tool(name)
    result = tool_function(**kwargs)

    if not isinstance(result, dict):
        raise TypeError(
            f"Tool must return a dict: {name}"
        )

    return result