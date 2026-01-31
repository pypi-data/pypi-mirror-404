# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, TypedDict

__all__ = ["ExecutionLogListParams"]


class ExecutionLogListParams(TypedDict, total=False):
    cursor: str
    """Cursor for pagination"""

    limit: float
    """Number of logs to return"""

    name: str
    """Filter by agent or tool name"""

    source: Literal["api", "cli", "dashboard", "widget", "sdk"]
    """Filter by request source"""

    status: Literal["success", "error", "timeout"]
    """Filter by execution status"""

    type: Literal["agent_invoke", "agent_chat", "tool_call"]
    """Filter by execution type"""
