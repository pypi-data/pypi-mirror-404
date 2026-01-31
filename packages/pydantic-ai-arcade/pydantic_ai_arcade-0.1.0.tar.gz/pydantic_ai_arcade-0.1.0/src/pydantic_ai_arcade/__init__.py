from __future__ import annotations

from importlib.metadata import version as _metadata_version

from pydantic_ai_arcade._errors import ToolAuthorizationError, ToolError
from pydantic_ai_arcade._tools import ToolRunContext, get_arcade_tools
from pydantic_ai_arcade._utils import get_arcade_client


__version__ = _metadata_version("pydantic_ai_arcade")

__all__ = [
    "ToolAuthorizationError",
    "ToolError",
    "ToolRunContext",
    "__version__",
    "get_arcade_client",
    "get_arcade_tools",
]
