# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["ToolCallResponse"]


class ToolCallResponse(BaseModel):
    output: Optional[object] = None
    """Output from the tool execution."""
