# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, TypedDict

__all__ = ["ToolListParams"]


class ToolListParams(TypedDict, total=False):
    cursor: str
    """Cursor for pagination"""

    limit: float
    """Number of tools to return"""

    status: Literal["active", "inactive"]
    """Filter by tool status"""

    type: str
    """Filter by tool type (python, typescript)"""
