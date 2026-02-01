# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional
from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["ClientTokenCreateParams"]


class ClientTokenCreateParams(TypedDict, total=False):
    context: Required[Dict[str, Optional[object]]]
    """
    Public context accessible to the client via /client/context (e.g., { userId:
    "...", sessionId: "..." })
    """

    server_context: Annotated[Dict[str, Optional[object]], PropertyInfo(alias="serverContext")]
    """
    Private context only accessible to agents/handlers, never exposed to client
    (e.g., { internalId: "..." })
    """

    ttl_seconds: Annotated[int, PropertyInfo(alias="ttlSeconds")]
    """Time-to-live in seconds. Default: 3600 (1 hour). Max: 86400 (24 hours)."""
