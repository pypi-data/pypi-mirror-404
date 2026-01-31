from __future__ import annotations

import asyncio
import json
import os
from typing import TYPE_CHECKING, Any, TypedDict, cast

from arcadepy import AsyncArcade

from pydantic_ai_arcade._errors import ToolAuthorizationError


if TYPE_CHECKING:
    from collections.abc import Mapping

    import httpx
    from arcadepy import Timeout
    from arcadepy.types import ToolDefinition
    from typing_extensions import Unpack


class ArcadeClientConfig(TypedDict, total=False):
    timeout: float | Timeout
    max_retries: int
    default_headers: Mapping[str, str]
    default_query: Mapping[str, object]
    http_client: httpx.AsyncClient


def get_arcade_client(
    api_key: str | None = os.getenv("ARCADE_API_KEY", None),
    base_url: str = "https://api.arcade.dev",
    **kwargs: Unpack[ArcadeClientConfig],
) -> AsyncArcade:
    if api_key is None:
        msg = "ARCADE_API_KEY is not set"
        raise ValueError(msg)

    return AsyncArcade(base_url=base_url, api_key=api_key, **kwargs)


async def get_arcade_tool_formats(
    client: AsyncArcade,
    tools: list[str] | None = None,
    toolkits: list[str] | None = None,
    *,
    raise_on_empty: bool = True,
) -> list[dict[str, Any]]:
    """Fetch formatted tool definitions from Arcade.

    Args:
        client (AsyncArcade): AsyncArcade client instance.
        tools (list[str], optional):
            List of specific tool names to include. Defaults to None.
        toolkits (list[str], optional):
            List of toolkit names to include all tools from. Defaults to None.
        raise_on_empty (bool, optional):
            Whether to raise an error if no tools or toolkits are provided.
            Defaults to True.

    Raises:
        ValueError: If no tools or toolkits are provided and raise_on_empty is True.

    Returns:
        list[ToolDefinition]: List of Arcade formatted tool definitions.
    """
    if not tools and not toolkits:
        msg = "No tools or toolkits provided to retrieve tool definitions"
        if raise_on_empty:
            raise ValueError(msg)
        return []

    all_tool_formats: list[object] = []

    if tools:
        tool_tasks = [
            client.tools.formatted.get(name=tool_id, format="openai") for tool_id in tools
        ]
        all_tool_formats.extend(await asyncio.gather(*tool_tasks))

    if toolkits:
        toolkit_tasks = [
            client.tools.formatted.list(toolkit=tk, format="openai") for tk in toolkits
        ]
        responses = await asyncio.gather(*toolkit_tasks)
        for response in responses:
            all_tool_formats.extend(response.items)

    return cast("list[dict[str, Any]]", all_tool_formats)


async def get_arcade_tool_auth_requirements(
    client: AsyncArcade,
    tools: list[str] | None = None,
    toolkits: list[str] | None = None,
    *,
    raise_on_empty: bool = True,
) -> dict[str, bool]:
    """Fetch tool definitions from Arcade and determine their authorization requirements.

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
        ValueError: If no tools or toolkits are provided and raise_on_empty is True.

    Returns:
        dict[str, bool]:
            Dictionary mapping tool names to their authorization requirements.
    """
    if not tools and not toolkits:
        msg = "No tools or toolkits provided to retrieve tool definitions"
        if raise_on_empty:
            raise ValueError(msg)
        return {}

    all_tool_definitions: list[ToolDefinition] = []

    if tools:
        tool_tasks = [client.tools.get(name=tool_id) for tool_id in tools]
        all_tool_definitions.extend(await asyncio.gather(*tool_tasks))

    if toolkits:
        toolkit_tasks = [client.tools.list(toolkit=tk) for tk in toolkits]
        responses = await asyncio.gather(*toolkit_tasks)
        for response in responses:
            all_tool_definitions.extend(response.items)

    tool_auth_requirements: dict[str, bool] = {}

    for tool_def in all_tool_definitions:
        tool_name = f"{tool_def.toolkit.name}_{tool_def.name}"
        require_auth = (
            tool_def.requirements is not None
            and tool_def.requirements.authorization is not None
        )
        tool_auth_requirements[tool_name] = require_auth

    return tool_auth_requirements


async def authorize_tool(
    client: AsyncArcade,
    user_id: str | None,
    tool_name: str,
) -> None:
    if not user_id:
        msg = "No user ID and authorization required for tool"
        raise ValueError(msg)

    result = await client.tools.authorize(
        tool_name=tool_name,
        user_id=user_id,
    )

    if result.status != "completed":
        raise ToolAuthorizationError(result)


def convert_output_to_json(output: Any) -> str:  # noqa: ANN401
    if isinstance(output, (dict, list)):
        return json.dumps(output)

    return str(output)
