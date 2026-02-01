# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["MemoryListResponse", "Data"]


class Data(BaseModel):
    expires_at: Optional[str] = FieldInfo(alias="expiresAt", default=None)
    """When the memory expires (if set)"""

    key: str
    """Memory key"""

    updated_at: str = FieldInfo(alias="updatedAt")
    """When the memory was last updated"""


class MemoryListResponse(BaseModel):
    data: List[Data]
