# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["ExecutionLog"]


class ExecutionLog(BaseModel):
    id: str
    """Unique execution log ID"""

    created_at: str = FieldInfo(alias="createdAt")
    """When the execution occurred"""

    duration_ms: Optional[float] = FieldInfo(alias="durationMs", default=None)
    """Execution duration in milliseconds"""

    error: Optional[str] = None
    """Error message (null for success)"""

    name: str
    """Agent or tool name"""

    project_id: str = FieldInfo(alias="projectId")
    """Project ID"""

    source: Literal["api", "cli", "dashboard", "widget", "sdk"]
    """Where the request originated"""

    status: Literal["success", "error", "timeout"]
    """Execution result status"""

    type: Literal["agent_invoke", "agent_chat", "tool_call"]
    """Type of execution"""

    input: Optional[object] = None
    """Input parameters"""

    output: Optional[object] = None
    """Output from execution (null for errors)"""
