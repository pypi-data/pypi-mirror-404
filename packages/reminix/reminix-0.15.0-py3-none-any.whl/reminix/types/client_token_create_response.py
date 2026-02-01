# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["ClientTokenCreateResponse"]


class ClientTokenCreateResponse(BaseModel):
    id: str
    """Token ID for management purposes"""

    token: str
    """The client token. Store this securely - it will not be shown again."""

    expires_at: datetime = FieldInfo(alias="expiresAt")
    """ISO 8601 timestamp when the token expires"""
