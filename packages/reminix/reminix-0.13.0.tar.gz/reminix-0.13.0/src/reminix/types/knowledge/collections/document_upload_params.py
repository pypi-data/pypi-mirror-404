# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ...._utils import PropertyInfo

__all__ = ["DocumentUploadParams"]


class DocumentUploadParams(TypedDict, total=False):
    mime_type: Required[Annotated[str, PropertyInfo(alias="mimeType")]]
    """MIME type of the document"""

    name: Required[str]
    """Document name (filename)"""

    size: float
    """File size in bytes"""
