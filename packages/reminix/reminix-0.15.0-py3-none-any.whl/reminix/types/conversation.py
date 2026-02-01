# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["Conversation"]


class Conversation(BaseModel):
    id: str
    """Unique conversation ID"""

    agent_name: str = FieldInfo(alias="agentName")
    """Agent name"""

    created_at: str = FieldInfo(alias="createdAt")
    """When the conversation was created"""

    identity: Dict[str, Optional[object]]
    """Identity fields for conversation scoping"""

    project_id: str = FieldInfo(alias="projectId")
    """Project ID"""

    updated_at: str = FieldInfo(alias="updatedAt")
    """When the conversation was last updated"""
