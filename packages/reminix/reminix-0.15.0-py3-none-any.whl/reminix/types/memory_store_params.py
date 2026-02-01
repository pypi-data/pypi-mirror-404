# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Optional
from datetime import datetime
from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["MemoryStoreParams"]


class MemoryStoreParams(TypedDict, total=False):
    identity: Required[Dict[str, Optional[object]]]
    """Identity fields for memory scoping (e.g., user_id, tenant_id)"""

    key: Required[str]
    """Memory key"""

    expires_at: Annotated[Union[str, datetime], PropertyInfo(alias="expiresAt", format="iso8601")]
    """Optional expiration time (ISO 8601)"""

    value: object
    """Value to store"""
