# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import TypedDict

__all__ = ["ConversationListParams"]


class ConversationListParams(TypedDict, total=False):
    agent_name: str
    """Filter by agent name"""

    cursor: str
    """Cursor for pagination"""

    limit: float
    """Number of conversations to return"""
