# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["Memory"]


class Memory(BaseModel):
    id: str
    """Unique memory ID"""

    created_at: str = FieldInfo(alias="createdAt")
    """When the memory was created"""

    expires_at: Optional[str] = FieldInfo(alias="expiresAt", default=None)
    """When the memory expires"""

    identity: Dict[str, Optional[object]]
    """Identity fields for memory scoping (e.g., user_id, tenant_id)"""

    key: str
    """Memory key"""

    project_id: str = FieldInfo(alias="projectId")
    """Project ID"""

    updated_at: str = FieldInfo(alias="updatedAt")
    """When the memory was last updated"""

    value: Optional[object] = None
    """Memory value"""
