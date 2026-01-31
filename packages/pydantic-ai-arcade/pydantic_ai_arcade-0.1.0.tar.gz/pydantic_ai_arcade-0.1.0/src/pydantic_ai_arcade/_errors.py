from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override


if TYPE_CHECKING:
    from arcadepy.types.execute_tool_response import ExecuteToolResponse
    from arcadepy.types.shared.authorization_response import AuthorizationResponse


class ToolError(RuntimeError):
    def __init__(self, tool_name: str, result: ExecuteToolResponse) -> None:
        self.tool_name = tool_name
        self.result = result

    @property
    def message(self) -> str:
        if self.result.output is not None and self.result.output.error is not None:
            return self.result.output.error.message
        return "Unexpected error occurred."

    @override
    def __str__(self) -> str:
        return f"Tool {self.tool_name} failed with error: {self.message}"


class ToolAuthorizationError(RuntimeError):
    def __init__(self, result: AuthorizationResponse) -> None:
        self.result = result

    @property
    def message(self) -> str:
        return f"Authorization required: {self.result.url}"

    @override
    def __str__(self) -> str:
        return self.message
