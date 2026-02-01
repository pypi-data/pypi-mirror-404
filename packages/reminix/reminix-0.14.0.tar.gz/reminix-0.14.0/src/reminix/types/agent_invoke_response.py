# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["AgentInvokeResponse"]


class AgentInvokeResponse(BaseModel):
    """Response with output from the agent and optional execution ID."""

    execution_id: Optional[str] = None
    """Execution ID for tracking"""

    output: Optional[object] = None
    """Output from the agent"""
