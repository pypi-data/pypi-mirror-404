from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Protocol

from pydantic_ai import Tool

from pydantic_ai_arcade import _utils
from pydantic_ai_arcade._errors import ToolAuthorizationError, ToolError


if TYPE_CHECKING:
    from arcadepy import AsyncArcade
    from pydantic_ai import RunContext
    from typing_extensions import Unpack


class ToolRunContext(Protocol):
    @abstractmethod
    def get_user_id(self, tool_name: str) -> str | None: ...


async def _invoke_arcade_tool(
    ctx: RunContext[ToolRunContext],
    *args: Any,  # noqa: ANN401
    **kwargs: Any,  # noqa: ANN401
) -> str:
    if args:
        error_msg = "Positional arguments are not allowed"
        raise TypeError(error_msg)

    if ctx.tool_name is None:
        error_msg = "Tool name is not set in the run context"
        raise ValueError(error_msg)

    client = _utils.get_arcade_client()
    tool_name = ctx.tool_name
    user_id = ctx.deps.get_user_id(tool_name)

    if user_id is None:
        error_msg = f"No user integration ID found for tool {tool_name}"
        raise ValueError(error_msg)

    try:
        await _utils.authorize_tool(client, user_id=user_id, tool_name=tool_name)
    except ToolAuthorizationError as e:
        return (
            f"Authorization required for tool {tool_name}, "
            f"please authorize here: {e.result.url} \nThen try again."
        )

    result = await client.tools.execute(
        tool_name=tool_name,
        input=kwargs,
        user_id=user_id,
    )

    if not result.success or result.output is None:
        raise ToolError(ctx.tool_name, result)

    return _utils.convert_output_to_json(result.output.value)


async def get_arcade_tools(
    client: AsyncArcade | None,
    tools: list[str] | None = None,
    toolkits: list[str] | None = None,
    *,
    raise_on_empty: bool = True,
    **kwargs: Unpack[_utils.ArcadeClientConfig],
) -> list[Tool[ToolRunContext]]:
    """Create a Pydantic AI tool proxy for each Arcade tool specified.

    Args:
        client (AsyncArcade):
            AsyncArcade client instance.
        tools (list[str], optional):
            List of specific tool names to include.
            Defaults to None.
        toolkits (list[str], optional):
            List of toolkit names to include all tools from.
            Defaults to None.
        raise_on_empty (bool, optional):
            Whether to raise an error if no tools or toolkits are provided.
            Defaults to True.

    Raises:
        ValueError: If no tools or toolkits are provided.

    Returns:
        list[Tool]: List of Pydantic AI tools that correspond to the Arcade tools.
    """
    if not tools and not toolkits:
        msg = "No tools or toolkits provided to retrieve tool definitions"
        if raise_on_empty:
            raise ValueError(msg)
        return []

    if not client:
        client = _utils.get_arcade_client(**kwargs)

    tool_formats = await _utils.get_arcade_tool_formats(
        client,
        tools=tools,
        toolkits=toolkits,
        raise_on_empty=raise_on_empty,
    )
    tool_auth_requirements = await _utils.get_arcade_tool_auth_requirements(
        client,
        tools=tools,
        toolkits=toolkits,
        raise_on_empty=raise_on_empty,
    )

    pydantic_tools: list[Tool[ToolRunContext]] = []

    for tool in tool_formats:
        tool_name: str = tool["function"]["name"]
        tool_description: str | None = tool["function"]["description"]
        tool_params = tool["function"]["parameters"]
        requires_auth = tool_auth_requirements.get(tool_name, False)
        json_schema = {
            "additionalProperties": tool_params.get("additionalProperties", False),
            "properties": tool_params.get("properties", {}),
            "required": tool_params.get("required", []),
            "type": tool_params.get("type", "object"),
        }

        pydantic_tool = Tool[ToolRunContext].from_schema(
            function=_invoke_arcade_tool,
            name=tool_name,
            description=tool_description,
            json_schema=json_schema,
            takes_ctx=True,
        )
        pydantic_tool.metadata = {"requires_auth": requires_auth}

        pydantic_tools.append(pydantic_tool)

    return pydantic_tools
