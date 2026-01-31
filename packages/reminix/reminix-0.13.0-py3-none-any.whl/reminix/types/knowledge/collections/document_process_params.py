# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ...._utils import PropertyInfo

__all__ = ["DocumentProcessParams"]


class DocumentProcessParams(TypedDict, total=False):
    collection_id: Required[Annotated[str, PropertyInfo(alias="collectionId")]]

    prefer_unstructured: Annotated[bool, PropertyInfo(alias="preferUnstructured")]
    """Use Unstructured.io for extraction if available"""
