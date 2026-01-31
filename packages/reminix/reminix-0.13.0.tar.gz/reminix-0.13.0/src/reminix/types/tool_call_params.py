# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional
from typing_extensions import Required, TypedDict

__all__ = ["ToolCallParams"]


class ToolCallParams(TypedDict, total=False):
    input: Required[Dict[str, Optional[object]]]
    """Input parameters for the tool. Structure depends on tool definition."""
