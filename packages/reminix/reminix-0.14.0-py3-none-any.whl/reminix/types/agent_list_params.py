# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, TypedDict

__all__ = ["AgentListParams"]


class AgentListParams(TypedDict, total=False):
    cursor: str
    """Cursor for pagination"""

    limit: float
    """Number of agents to return"""

    status: Literal["active", "inactive"]
    """Filter by agent status"""

    type: str
    """Filter by agent type (managed, python, typescript, python-langchain, etc.)"""
