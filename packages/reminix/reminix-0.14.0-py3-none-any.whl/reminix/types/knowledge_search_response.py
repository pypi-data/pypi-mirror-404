# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["KnowledgeSearchResponse", "Chunk"]


class Chunk(BaseModel):
    chunk_index: float = FieldInfo(alias="chunkIndex")
    """Position in document"""

    content: str
    """Chunk text content"""

    document_id: str = FieldInfo(alias="documentId")
    """Source document ID"""

    score: float
    """Similarity score (0-1)"""


class KnowledgeSearchResponse(BaseModel):
    chunks: List[Chunk]

    count: float
    """Number of results found"""
