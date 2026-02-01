# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["KnowledgeSearchParams"]


class KnowledgeSearchParams(TypedDict, total=False):
    collection_ids: Required[Annotated[SequenceNotStr[str], PropertyInfo(alias="collectionIds")]]
    """Collection IDs to search"""

    query: Required[str]
    """Natural language search query"""

    limit: float
    """Maximum number of results"""

    threshold: float
    """Minimum similarity score (0-1)"""
